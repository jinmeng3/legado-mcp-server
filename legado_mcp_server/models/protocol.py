from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class LegadoEnvelope(ProtocolModel):
    isSuccess: bool = False
    errorMsg: str = "未知错误,请联系开发者!"
    data: Any = None


class ToolResult(ProtocolModel):
    ok: bool
    upstream_endpoint: str
    normalized_data: Any = None
    raw_upstream: Any = None
    warnings: list[str] = Field(default_factory=list)
    session_id: str | None = None


class SessionEvent(ProtocolModel):
    index: int
    ts: float
    kind: Literal["log", "search_batch", "status"]
    text: str | None = None
    raw_text: str | None = None
    search_books: list[dict[str, Any]] | None = None
    done: bool = False
    error: bool = False


class SessionSnapshot(ProtocolModel):
    session_id: str
    session_type: str
    cursor: int
    done: bool
    cancelled: bool
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    events: list[SessionEvent]


class ApiSummary(ProtocolModel):
    base_url: str
    ws_url: str
    http_endpoints: list[str]
    websocket_endpoints: list[str]
    notes: list[str]
