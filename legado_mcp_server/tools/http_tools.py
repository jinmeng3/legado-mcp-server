from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from legado_mcp_server.client.http import LegadoHttpClient
from legado_mcp_server.config import DEFAULT_BASE_URL
from legado_mcp_server.models.legado import (
    Book,
    BookProgress,
    BookSource,
    ReplaceRule,
    RssSource,
)
from legado_mcp_server.models.protocol import ToolResult


def prepare_local_book_upload(
    file_path: str, file_name: str | None = None
) -> tuple[str, bytes] | ToolResult:
    path = Path(file_path)
    try:
        content = path.read_bytes()
    except OSError as exc:
        return ToolResult(
            ok=False,
            upstream_endpoint="/addLocalBook",
            normalized_data=None,
            raw_upstream=str(exc),
            warnings=[f"Failed to read local file: {path}"],
        )
    return file_name or path.name, content


def _connection_info(client: LegadoHttpClient) -> dict[str, Any]:
    base_url = client.settings.legado_base_url
    return {
        "http_base_url": base_url,
        "websocket_url": client.settings.resolved_ws_url,
        "default_http_base_url": DEFAULT_BASE_URL,
        "using_default_http_base_url": base_url.rstrip("/") == DEFAULT_BASE_URL,
        "environment_variables": {
            "http": "LEGADO_BASE_URL",
            "websocket": "LEGADO_WS_URL",
        },
        "configuration_example": (
            '$env:LEGADO_BASE_URL = "http://<Legado-LAN-IP>:1122"'
        ),
        "notes": [
            "127.0.0.1 points to the machine running this MCP server.",
            "Use legado_connection_configure for a temporary runtime change.",
            "Set environment variables before startup for persistent configuration.",
            (
                "The default WebSocket URL uses the HTTP host with its port "
                "increased by 1."
            ),
            (
                "book_source_debug uses the configured Legado WebSocket endpoint; "
                "tag selects a configured book source."
            ),
        ],
    }


def register_http_tools(mcp: FastMCP, client: LegadoHttpClient) -> None:
    @mcp.tool()
    async def legado_ping() -> dict[str, Any]:
        """Check whether the Legado Web service is reachable."""
        return (await client.ping()).model_dump()

    @mcp.tool()
    def legado_connection_info() -> dict[str, Any]:
        """Show the current Legado endpoints and configuration guidance.

        This reports settings only; it does not test connectivity or change them.
        """
        return _connection_info(client)

    @mcp.tool()
    def legado_connection_configure(
        http_base_url: str, websocket_url: str | None = None
    ) -> dict[str, Any]:
        """Change active endpoints for this process after the user requests it.

        The change is temporary and does not persist across a server restart.
        """
        try:
            client.configure_connection(http_base_url, websocket_url)
        except ValueError as exc:
            return {"configured": False, "error": str(exc)}
        return {
            **_connection_info(client),
            "configured": True,
            "persistent": False,
            "message": (
                "The new endpoints apply to subsequent requests in this process. "
                "They are not saved and will revert after the MCP server restarts."
            ),
        }

    @mcp.tool()
    async def legado_get_api_summary() -> dict[str, Any]:
        """Return the normalized summary of supported Legado HTTP and WS endpoints."""
        return client.get_api_summary().model_dump()

    @mcp.tool()
    async def book_source_get(url: str) -> dict[str, Any]:
        return (await client.get("/getBookSource", params={"url": url})).model_dump()

    @mcp.tool()
    async def book_source_list() -> dict[str, Any]:
        return (await client.get("/getBookSources")).model_dump()

    @mcp.tool()
    async def book_source_save(source: BookSource | dict[str, Any]) -> dict[str, Any]:
        payload = source.model_dump() if isinstance(source, BookSource) else source
        return (await client.post_json("/saveBookSource", payload)).model_dump()

    @mcp.tool()
    async def book_source_save_many(
        sources: list[BookSource | dict[str, Any]],
    ) -> dict[str, Any]:
        payload = [
            item.model_dump() if isinstance(item, BookSource) else item
            for item in sources
        ]
        return (await client.post_json("/saveBookSources", payload)).model_dump()

    @mcp.tool()
    async def book_source_delete_many(
        sources: list[BookSource | dict[str, Any]],
    ) -> dict[str, Any]:
        payload = [
            item.model_dump() if isinstance(item, BookSource) else item
            for item in sources
        ]
        return (await client.post_json("/deleteBookSources", payload)).model_dump()

    @mcp.tool()
    async def rss_source_get(url: str) -> dict[str, Any]:
        return (await client.get("/getRssSource", params={"url": url})).model_dump()

    @mcp.tool()
    async def rss_source_list() -> dict[str, Any]:
        return (await client.get("/getRssSources")).model_dump()

    @mcp.tool()
    async def rss_source_save(source: RssSource | dict[str, Any]) -> dict[str, Any]:
        payload = source.model_dump() if isinstance(source, RssSource) else source
        return (await client.post_json("/saveRssSource", payload)).model_dump()

    @mcp.tool()
    async def rss_source_save_many(
        sources: list[RssSource | dict[str, Any]],
    ) -> dict[str, Any]:
        payload = [
            item.model_dump() if isinstance(item, RssSource) else item
            for item in sources
        ]
        return (await client.post_json("/saveRssSources", payload)).model_dump()

    @mcp.tool()
    async def rss_source_delete_many(
        sources: list[RssSource | dict[str, Any]],
    ) -> dict[str, Any]:
        payload = [
            item.model_dump() if isinstance(item, RssSource) else item
            for item in sources
        ]
        return (await client.post_json("/deleteRssSources", payload)).model_dump()

    @mcp.tool()
    async def replace_rule_list() -> dict[str, Any]:
        return (await client.get("/getReplaceRules")).model_dump()

    @mcp.tool()
    async def replace_rule_save(rule: ReplaceRule | dict[str, Any]) -> dict[str, Any]:
        payload = rule.model_dump() if isinstance(rule, ReplaceRule) else rule
        return (await client.post_json("/saveReplaceRule", payload)).model_dump()

    @mcp.tool()
    async def replace_rule_delete(rule: ReplaceRule | dict[str, Any]) -> dict[str, Any]:
        payload = rule.model_dump() if isinstance(rule, ReplaceRule) else rule
        return (await client.post_json("/deleteReplaceRule", payload)).model_dump()

    @mcp.tool()
    async def replace_rule_test(
        rule: ReplaceRule | dict[str, Any], text: str
    ) -> dict[str, Any]:
        payload = rule.model_dump() if isinstance(rule, ReplaceRule) else rule
        return (
            await client.post_json("/testReplaceRule", {"rule": payload, "text": text})
        ).model_dump()

    @mcp.tool()
    async def book_save(book: Book | dict[str, Any]) -> dict[str, Any]:
        payload = book.model_dump() if isinstance(book, Book) else book
        return (await client.post_json("/saveBook", payload)).model_dump()

    @mcp.tool()
    async def book_delete(book: Book | dict[str, Any]) -> dict[str, Any]:
        payload = book.model_dump() if isinstance(book, Book) else book
        return (await client.post_json("/deleteBook", payload)).model_dump()

    @mcp.tool()
    async def bookshelf_list() -> dict[str, Any]:
        return (await client.get("/getBookshelf")).model_dump()

    @mcp.tool()
    async def book_refresh_toc(url: str) -> dict[str, Any]:
        return (await client.get("/refreshToc", params={"url": url})).model_dump()

    @mcp.tool()
    async def book_get_chapters(url: str) -> dict[str, Any]:
        return (await client.get("/getChapterList", params={"url": url})).model_dump()

    @mcp.tool()
    async def book_get_content(url: str, index: int) -> dict[str, Any]:
        return (
            await client.get("/getBookContent", params={"url": url, "index": index})
        ).model_dump()

    @mcp.tool()
    async def book_save_progress(
        progress: BookProgress | dict[str, Any],
    ) -> dict[str, Any]:
        payload = (
            progress.model_dump() if isinstance(progress, BookProgress) else progress
        )
        return (await client.post_json("/saveBookProgress", payload)).model_dump()

    @mcp.tool()
    async def book_add_local(
        file_path: str, file_name: str | None = None
    ) -> dict[str, Any]:
        prepared = prepare_local_book_upload(file_path, file_name)
        if isinstance(prepared, ToolResult):
            return prepared.model_dump()
        upload_name, content = prepared
        return (
            await client.post_multipart(
                "/addLocalBook",
                data={"fileName": upload_name},
                files={"fileData": (upload_name, content, "application/octet-stream")},
            )
        ).model_dump()

    @mcp.tool()
    async def web_read_config_save(config_json: Any | None) -> dict[str, Any]:
        return (await client.post_json("/saveReadConfig", config_json)).model_dump()

    @mcp.tool()
    async def web_read_config_get() -> dict[str, Any]:
        return (await client.get("/getReadConfig")).model_dump()

    @mcp.tool()
    async def book_get_cover(path: str) -> dict[str, Any]:
        return (await client.get_image("/cover", params={"path": path})).model_dump()

    @mcp.tool()
    async def book_get_image(
        book_url: str, path: str, width: int = 640
    ) -> dict[str, Any]:
        return (
            await client.get_image(
                "/image",
                params={"url": book_url, "path": path, "width": width},
            )
        ).model_dump()
