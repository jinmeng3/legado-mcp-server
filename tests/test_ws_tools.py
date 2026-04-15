from pathlib import Path

from legado_mcp_server.config import load_settings
from legado_mcp_server.tools.ws_tools import build_book_source_debug_key


def test_build_book_source_debug_key_for_explore_mode() -> None:
    key, warnings = build_book_source_debug_key("https://example.com/list", "explore")
    assert key == "explore::https://example.com/list"
    assert warnings == []


def test_build_book_source_debug_key_for_content_mode() -> None:
    key, warnings = build_book_source_debug_key(
        "https://example.com/chapter/1", "content"
    )
    assert key == "--https://example.com/chapter/1"
    assert warnings == []


def test_read_api_doc_text_falls_back_to_repo_doc() -> None:
    settings = load_settings()
    text = settings.read_api_doc_text()
    assert text.startswith("# Legado Web 服务接口文档")
    assert Path(settings.api_doc_path).exists()


def test_runtime_tmp_dir_uses_system_temp_root() -> None:
    settings = load_settings()
    assert settings.runtime_tmp_dir.name == "legado-mcp-server"
