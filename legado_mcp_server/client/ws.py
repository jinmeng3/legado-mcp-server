from __future__ import annotations

import asyncio
import contextlib
import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

import websockets

from legado_mcp_server.config import Settings
from legado_mcp_server.models.legado import SearchBook
from legado_mcp_server.models.protocol import SessionEvent, SessionSnapshot, ToolResult


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    session_type: str
    warnings: list[str] = field(default_factory=list)
    events: deque[SessionEvent] = field(default_factory=deque)
    done: bool = False
    cancelled: bool = False
    error_message: str | None = None
    completion_event: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task[Any] | None = None
    cursor: int = 0

    def append_event(
        self,
        *,
        kind: Literal["log", "search_batch", "status"],
        text: str | None = None,
        raw_text: str | None = None,
        search_books: list[dict[str, Any]] | None = None,
        done: bool = False,
        error: bool = False,
        max_events: int,
    ) -> None:
        event = SessionEvent(
            index=self.cursor,
            ts=time.time(),
            kind=kind,
            text=text,
            raw_text=raw_text,
            search_books=search_books,
            done=done,
            error=error,
        )
        self.events.append(event)
        self.cursor += 1
        while len(self.events) > max_events:
            self.events.popleft()

    def mark_done(self, *, error_message: str | None = None) -> None:
        self.done = True
        self.error_message = error_message
        self.completion_event.set()

    def snapshot(self, cursor: int | None = None) -> SessionSnapshot:
        resolved_cursor = 0 if cursor is None else cursor
        events = [event for event in self.events if event.index >= resolved_cursor]
        next_cursor = events[-1].index + 1 if events else resolved_cursor
        return SessionSnapshot(
            session_id=self.session_id,
            session_type=self.session_type,
            cursor=next_cursor,
            done=self.done,
            cancelled=self.cancelled,
            error_message=self.error_message,
            warnings=list(self.warnings),
            events=events,
        )


class LegadoWebSocketSessionManager:
    MAX_ACTIVE_SESSIONS = 32
    MAX_RETAINED_SESSIONS = 100

    def __init__(
        self,
        settings: Settings,
        *,
        connector: Callable[..., Any] = websockets.connect,
    ) -> None:
        self.settings = settings
        self.connector = connector
        self._sessions: dict[str, SessionRecord] = {}

    def get_session(self, session_id: str) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def create_session(self, session_type: str) -> SessionRecord | None:
        active_count = sum(not record.done for record in self._sessions.values())
        if active_count >= self.MAX_ACTIVE_SESSIONS:
            return None
        for old_session_id, record in list(self._sessions.items()):
            if len(self._sessions) < self.MAX_RETAINED_SESSIONS:
                break
            if record.done:
                del self._sessions[old_session_id]
        if len(self._sessions) >= self.MAX_RETAINED_SESSIONS:
            return None
        session_id = uuid.uuid4().hex
        record = SessionRecord(session_id=session_id, session_type=session_type)
        self._sessions[session_id] = record
        return record

    def snapshot(self, session_id: str, cursor: int | None = None) -> ToolResult:
        record = self._sessions.get(session_id)
        if record is None:
            return ToolResult(
                ok=False,
                upstream_endpoint=session_id,
                normalized_data=None,
                raw_upstream=None,
                warnings=["Unknown session_id."],
            )
        return ToolResult(
            ok=True,
            upstream_endpoint=record.session_type,
            normalized_data=record.snapshot(cursor).model_dump(),
            raw_upstream=None,
            warnings=list(record.warnings),
            session_id=session_id,
        )

    async def wait(
        self, session_id: str, timeout_seconds: float | None = None
    ) -> ToolResult:
        record = self._sessions.get(session_id)
        if record is None:
            return ToolResult(
                ok=False,
                upstream_endpoint=session_id,
                normalized_data=None,
                raw_upstream=None,
                warnings=["Unknown session_id."],
            )
        try:
            await asyncio.wait_for(record.completion_event.wait(), timeout_seconds)
        except asyncio.TimeoutError:
            record.warnings.append(
                "Wait timed out before the upstream session completed."
            )
            record.cancelled = True
            if record.task is not None and not record.task.done():
                record.task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await record.task
            record.mark_done(error_message=record.error_message)
        return ToolResult(
            ok=record.error_message is None,
            upstream_endpoint=record.session_type,
            normalized_data=record.snapshot(0).model_dump(),
            raw_upstream=None,
            warnings=list(record.warnings),
            session_id=session_id,
        )

    async def cancel(self, session_id: str) -> ToolResult:
        record = self._sessions.get(session_id)
        if record is None:
            return ToolResult(
                ok=False,
                upstream_endpoint=session_id,
                normalized_data=None,
                raw_upstream=None,
                warnings=["Unknown session_id."],
            )
        record.cancelled = True
        if record.task is not None:
            record.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await record.task
        record.mark_done(error_message=record.error_message)
        return ToolResult(
            ok=True,
            upstream_endpoint=record.session_type,
            normalized_data={"cancelled": True},
            raw_upstream=None,
            warnings=list(record.warnings),
            session_id=session_id,
        )

    def start_book_source_debug(self, *, tag: str, key: str) -> ToolResult:
        return self._start_text_session(
            endpoint="/bookSourceDebug",
            session_type="book_source_debug",
            payload={"tag": tag, "key": key},
        )

    def start_rss_source_debug(self, *, tag: str) -> ToolResult:
        return self._start_text_session(
            endpoint="/rssSourceDebug",
            session_type="rss_source_debug",
            payload={"tag": tag},
        )

    def start_book_search(self, *, key: str) -> ToolResult:
        record = self.create_session("book_search")
        if record is None:
            return ToolResult(
                ok=False,
                upstream_endpoint="/searchBook",
                normalized_data=None,
                raw_upstream=None,
                warnings=["WebSocket session capacity reached."],
            )
        record.task = asyncio.create_task(
            self._run_search_session(record, "/searchBook", {"key": key})
        )
        return ToolResult(
            ok=True,
            upstream_endpoint="/searchBook",
            normalized_data={"session_id": record.session_id},
            raw_upstream=None,
            warnings=[],
            session_id=record.session_id,
        )

    def _start_text_session(
        self, *, endpoint: str, session_type: str, payload: dict[str, Any]
    ) -> ToolResult:
        record = self.create_session(session_type)
        if record is None:
            return ToolResult(
                ok=False,
                upstream_endpoint=endpoint,
                normalized_data=None,
                raw_upstream=None,
                warnings=["WebSocket session capacity reached."],
            )
        record.task = asyncio.create_task(
            self._run_text_session(record, endpoint, payload)
        )
        return ToolResult(
            ok=True,
            upstream_endpoint=endpoint,
            normalized_data={"session_id": record.session_id},
            raw_upstream=None,
            warnings=[],
            session_id=record.session_id,
        )

    async def _run_text_session(
        self, record: SessionRecord, endpoint: str, payload: dict[str, Any]
    ) -> None:
        uri = f"{self.settings.resolved_ws_url}{endpoint}"
        try:
            async with self.connector(uri) as websocket:
                await websocket.send(json.dumps(payload, ensure_ascii=False))
                async for message in websocket:
                    record.append_event(
                        kind="log",
                        text=message,
                        raw_text=message,
                        max_events=self.settings.session_buffer_size,
                    )
        except asyncio.CancelledError:
            record.cancelled = True
            raise
        except Exception as exc:
            record.append_event(
                kind="status",
                text=str(exc),
                raw_text=str(exc),
                error=True,
                done=True,
                max_events=self.settings.session_buffer_size,
            )
            record.mark_done(error_message=str(exc))
            return
        record.append_event(
            kind="status",
            text="Upstream WebSocket closed.",
            raw_text="Upstream WebSocket closed.",
            done=True,
            max_events=self.settings.session_buffer_size,
        )
        record.mark_done()

    async def _run_search_session(
        self, record: SessionRecord, endpoint: str, payload: dict[str, Any]
    ) -> None:
        uri = f"{self.settings.resolved_ws_url}{endpoint}"
        try:
            async with self.connector(uri) as websocket:
                await websocket.send(json.dumps(payload, ensure_ascii=False))
                async for message in websocket:
                    search_books = [
                        SearchBook.model_validate(item).model_dump()
                        for item in json.loads(message)
                    ]
                    record.append_event(
                        kind="search_batch",
                        text=f"Received {len(search_books)} search results.",
                        raw_text=message,
                        search_books=search_books,
                        max_events=self.settings.session_buffer_size,
                    )
        except asyncio.CancelledError:
            record.cancelled = True
            raise
        except Exception as exc:
            record.append_event(
                kind="status",
                text=str(exc),
                raw_text=str(exc),
                error=True,
                done=True,
                max_events=self.settings.session_buffer_size,
            )
            record.mark_done(error_message=str(exc))
            return
        record.append_event(
            kind="status",
            text="Upstream search WebSocket closed.",
            raw_text="Upstream search WebSocket closed.",
            done=True,
            max_events=self.settings.session_buffer_size,
        )
        record.mark_done()
