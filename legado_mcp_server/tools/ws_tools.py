from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from legado_mcp_server.client.ws import LegadoWebSocketSessionManager


def build_book_source_debug_key(
    key: str,
    mode: Literal["auto", "search", "detail", "explore", "toc", "content"],
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if mode in {"auto", "search", "detail"}:
        return key, warnings
    if mode == "explore":
        # Legado only needs a "label::url" shape here. The label itself is not used.
        return f"explore::{key}", warnings
    if mode == "toc":
        return f"++{key}", warnings
    if mode == "content":
        return f"--{key}", warnings
    warnings.append(f"Unsupported mode {mode}; using key as-is.")
    return key, warnings


def register_ws_tools(mcp: FastMCP, manager: LegadoWebSocketSessionManager) -> None:

    @mcp.tool()
    async def book_source_debug(
        tag: str,
        key: str,
        mode: Literal["auto", "search", "detail", "explore", "toc", "content"] = "auto",
        timeout_seconds: float = 30.0,
    ) -> dict[str, Any]:
        """
        Debug a book source and return all logs in one go.
        This is the recommended tool for book source debugging.

        Args:
            tag: The book source URL (NOT the name).
            key: The keyword or URL to debug.
            mode: Debug mode (auto, search, detail, explore, toc, content).
            timeout_seconds: Maximum time to wait for the debug session to finish.
        """
        transformed_key, warnings = build_book_source_debug_key(key, mode)
        start_res = manager.start_book_source_debug(tag=tag, key=transformed_key)
        if not start_res.ok:
            return start_res.model_dump()

        wait_res = await manager.wait(start_res.session_id, timeout_seconds)
        wait_res.warnings.extend(warnings)

        # Post-process: flatten logs
        if wait_res.ok and wait_res.normalized_data:
            snapshot = wait_res.normalized_data
            logs = [
                e.get("text")
                for e in snapshot.get("events", [])
                if e.get("kind") == "log"
            ]
            wait_res.normalized_data = {
                "logs": logs,
                "done": snapshot.get("done", False),
                "error_message": snapshot.get("error_message"),
            }

        return wait_res.model_dump()

    @mcp.tool()
    async def book_search(key: str, timeout_seconds: float = 30.0) -> dict[str, Any]:
        """
        Search for books across all enabled sources and return sorted results.
        This tool waits for the search to complete or timeout.

        Args:
            key: The search keyword (title or author).
            timeout_seconds: Maximum time to wait (multi-source search can be slow).
        """
        start_res = manager.start_book_search(key=key)
        if not start_res.ok:
            return start_res.model_dump()

        wait_res = await manager.wait(start_res.session_id, timeout_seconds)

        # Post-process: extract and flatten books if successful
        if wait_res.ok and wait_res.normalized_data:
            snapshot = wait_res.normalized_data
            all_books = []
            for event in snapshot.get("events", []):
                if event.get("kind") == "search_batch" and event.get("search_books"):
                    all_books.extend(event["search_books"])
            # Replace normalized_data with the flat list for easier consumption
            wait_res.normalized_data = {
                "books": all_books,
                "done": snapshot.get("done", False),
                "error_message": snapshot.get("error_message"),
            }

        return wait_res.model_dump()

    @mcp.tool()
    async def rss_source_debug(tag: str, timeout_seconds: float = 30.0) -> dict[str, Any]:
        """Debug an RSS source and return logs in one go."""
        start_res = manager.start_rss_source_debug(tag=tag)
        if not start_res.ok:
            return start_res.model_dump()

        wait_res = await manager.wait(start_res.session_id, timeout_seconds)

        # Post-process: flatten logs
        if wait_res.ok and wait_res.normalized_data:
            snapshot = wait_res.normalized_data
            logs = [
                e.get("text")
                for e in snapshot.get("events", [])
                if e.get("kind") == "log"
            ]
            wait_res.normalized_data = {
                "logs": logs,
                "done": snapshot.get("done", False),
                "error_message": snapshot.get("error_message"),
            }

        return wait_res.model_dump()

