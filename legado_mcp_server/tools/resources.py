from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from legado_mcp_server.client.http import LegadoHttpClient
from legado_mcp_server.client.ws import LegadoWebSocketSessionManager
from legado_mcp_server.config import Settings
from legado_mcp_server.models.legado import BookSource, RssSource


def register_resources(
    mcp: FastMCP,
    settings: Settings,
    client: LegadoHttpClient,
    manager: LegadoWebSocketSessionManager,
) -> None:
    @mcp.resource("legado://api/http")
    def legado_http_api() -> str:
        """Read the HTTP API summary and implementation notes."""
        summary = client.get_api_summary().model_dump()
        doc_tail = settings.read_api_doc_text()
        return (
            "# HTTP API Summary\n\n"
            + json.dumps(summary, ensure_ascii=False, indent=2)
            + "\n\n"
            + doc_tail
        )

    @mcp.resource("legado://api/websocket")
    def legado_ws_api() -> str:
        """Read the WebSocket API summary and implementation notes."""
        summary = {
            "ws_url": settings.resolved_ws_url,
            "endpoints": ["/bookSourceDebug", "/rssSourceDebug", "/searchBook"],
        }
        doc_tail = settings.read_api_doc_text()
        return (
            "# WebSocket API Summary\n\n"
            + json.dumps(summary, ensure_ascii=False, indent=2)
            + "\n\n"
            + doc_tail
        )

    @mcp.resource("legado://schema/book-source")
    def legado_book_source_schema() -> str:
        """Read the normalized JSON schema for the BookSource model."""
        return json.dumps(BookSource.model_json_schema(), ensure_ascii=False, indent=2)

    @mcp.resource("legado://schema/rss-source")
    def legado_rss_source_schema() -> str:
        """Read the normalized JSON schema for the RssSource model."""
        return json.dumps(RssSource.model_json_schema(), ensure_ascii=False, indent=2)

    @mcp.resource("legado://session/{session_id}")
    def legado_session_snapshot(session_id: str) -> str:
        """Read the latest in-memory session snapshot for a debug/search session."""
        record = manager.get_session(session_id)
        if record is None:
            return json.dumps(
                {"error": "unknown session_id"}, ensure_ascii=False, indent=2
            )
        return json.dumps(record.snapshot(0).model_dump(), ensure_ascii=False, indent=2)
