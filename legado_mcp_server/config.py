from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from urllib.parse import urlparse, urlunparse

DEFAULT_BASE_URL = "http://127.0.0.1:1122"
DEFAULT_HTTP_TIMEOUT_SECONDS = 60.0
DEFAULT_SESSION_BUFFER_SIZE = 1000


def _derive_ws_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    netloc = parsed.hostname or "127.0.0.1"
    ws_port = port + 1
    if ":" in netloc:
        netloc = f"[{netloc}]"
    return urlunparse((ws_scheme, f"{netloc}:{ws_port}", "", "", "", ""))


@dataclass(slots=True)
class Settings:
    legado_base_url: str = DEFAULT_BASE_URL
    legado_ws_url: str = ""
    http_timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS
    session_buffer_size: int = DEFAULT_SESSION_BUFFER_SIZE
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def resolved_ws_url(self) -> str:
        return self.legado_ws_url or _derive_ws_url(self.legado_base_url)

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def api_doc_path(self) -> Path:
        return self.repo_root / "docs" / "legado-web-api.md"

    def read_api_doc_text(self) -> str:
        try:
            return (
                resources.files("legado_mcp_server")
                .joinpath("_docs", "legado-web-api.md")
                .read_text(encoding="utf-8")
            )
        except FileNotFoundError:
            return self.api_doc_path.read_text(encoding="utf-8")

    @property
    def runtime_tmp_dir(self) -> Path:
        return Path(tempfile.gettempdir()) / "legado-mcp-server"


def load_settings(
    *,
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    legado_base_url: str | None = None,
    legado_ws_url: str | None = None,
) -> Settings:
    return Settings(
        legado_base_url=legado_base_url
        or os.environ.get("LEGADO_BASE_URL", DEFAULT_BASE_URL),
        legado_ws_url=legado_ws_url or os.environ.get("LEGADO_WS_URL", ""),
        http_timeout_seconds=float(
            os.environ.get("LEGADO_HTTP_TIMEOUT", DEFAULT_HTTP_TIMEOUT_SECONDS)
        ),
        session_buffer_size=int(
            os.environ.get("LEGADO_SESSION_BUFFER_SIZE", DEFAULT_SESSION_BUFFER_SIZE)
        ),
        transport=transport,
        host=host,
        port=port,
    )
