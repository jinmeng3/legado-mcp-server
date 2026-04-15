import json

from legado_mcp_server.client.ws import LegadoWebSocketSessionManager
from legado_mcp_server.config import load_settings


class FakeWebSocket:
    def __init__(self, messages: list[str]) -> None:
        self.messages = list(messages)
        self.sent_payloads: list[str] = []

    async def send(self, payload: str) -> None:
        self.sent_payloads.append(payload)

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        if self.messages:
            return self.messages.pop(0)
        raise StopAsyncIteration


class FakeConnector:
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        self.websocket = FakeWebSocket(messages)

    def __call__(self, _: str):
        return self

    async def __aenter__(self) -> FakeWebSocket:
        return self.websocket

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


async def test_book_source_debug_session_collects_transcript() -> None:
    manager = LegadoWebSocketSessionManager(
        load_settings(), connector=FakeConnector(["line1", "line2"])
    )
    start = manager.start_book_source_debug(tag="source-url", key="keyword")
    session_id = start.session_id
    assert session_id
    result = await manager.wait(session_id, timeout_seconds=1)
    assert result.ok is True
    snapshot = result.normalized_data
    assert snapshot["done"] is True
    assert [event["text"] for event in snapshot["events"][:2]] == ["line1", "line2"]


async def test_book_search_session_parses_search_batches() -> None:
    payload = json.dumps(
        [
            {
                "bookUrl": "u1",
                "origin": "o1",
                "originName": "n1",
                "type": 0,
                "name": "Book",
                "author": "Author",
                "tocUrl": "toc",
            }
        ]
    )
    manager = LegadoWebSocketSessionManager(
        load_settings(), connector=FakeConnector([payload])
    )
    start = manager.start_book_search(key="book")
    result = await manager.wait(start.session_id or "", timeout_seconds=1)
    assert result.ok is True
    snapshot = result.normalized_data
    assert snapshot["events"][0]["kind"] == "search_batch"
    assert snapshot["events"][0]["search_books"][0]["name"] == "Book"
