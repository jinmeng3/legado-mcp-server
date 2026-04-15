from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from legado_mcp_server.client import LegadoHttpClient, LegadoWebSocketSessionManager
from legado_mcp_server.config import Settings, load_settings
from legado_mcp_server.tools.http_tools import register_http_tools
from legado_mcp_server.tools.resources import register_resources
from legado_mcp_server.tools.ws_tools import register_ws_tools


@dataclass
class AppContext:
    settings: Settings
    http_client: LegadoHttpClient
    ws_manager: LegadoWebSocketSessionManager


def build_server(settings: Settings) -> FastMCP:
    http_client = LegadoHttpClient(settings)
    ws_manager = LegadoWebSocketSessionManager(settings)

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[AppContext]:
        try:
            yield AppContext(
                settings=settings,
                http_client=http_client,
                ws_manager=ws_manager,
            )
        finally:
            await http_client.aclose()

    mcp = FastMCP(
        "Legado Web MCP",
        lifespan=lifespan,
        host=settings.host,
        port=settings.port,
        json_response=True,
        stateless_http=True,
    )
    register_http_tools(mcp, http_client)
    register_ws_tools(mcp, ws_manager)
    register_resources(mcp, settings, http_client, ws_manager)
    return mcp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Legado Web MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP transport to run.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host.")
    parser.add_argument("--port", type=int, default=8000, help="HTTP bind port.")
    parser.add_argument(
        "--legado-base-url",
        default=None,
        help="Legado HTTP base URL, e.g. http://192.168.1.10:1122",
    )
    parser.add_argument(
        "--legado-ws-url",
        default=None,
        help="Optional Legado WebSocket base URL, e.g. ws://192.168.1.10:1123",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings(
        transport=args.transport,
        host=args.host,
        port=args.port,
        legado_base_url=args.legado_base_url,
        legado_ws_url=args.legado_ws_url,
    )
    mcp = build_server(settings)
    if settings.transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
