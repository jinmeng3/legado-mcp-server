import httpx

from legado_mcp_server.client.http import LegadoHttpClient
from legado_mcp_server.config import load_settings
from legado_mcp_server.tools.http_tools import prepare_local_book_upload


def make_response(path: str, payload: object) -> httpx.Response:
    request = httpx.Request("GET", f"http://127.0.0.1:1122{path}")
    return httpx.Response(200, json=payload, request=request)


def test_success_envelope_is_normalized() -> None:
    client = LegadoHttpClient(load_settings())
    response = make_response(
        "/getBookSources",
        {"isSuccess": True, "errorMsg": "", "data": [{"bookSourceUrl": "a"}]},
    )
    result = client._normalize_response("/getBookSources", response)
    assert result.ok is True
    assert result.normalized_data == [{"bookSourceUrl": "a"}]


def test_replace_rules_embedded_json_is_parsed() -> None:
    client = LegadoHttpClient(load_settings())
    response = make_response(
        "/getReplaceRules",
        {
            "isSuccess": True,
            "errorMsg": "",
            "data": '[{"id":1,"name":"demo","pattern":"a","replacement":"b"}]',
        },
    )
    result = client._normalize_response("/getReplaceRules", response)
    assert result.ok is True
    assert result.normalized_data == [
        {"id": 1, "name": "demo", "pattern": "a", "replacement": "b"}
    ]


def test_legacy_replace_rule_success_is_inferred() -> None:
    client = LegadoHttpClient(load_settings())
    response = make_response(
        "/saveReplaceRule",
        {"isSuccess": False, "errorMsg": "未知错误,请联系开发者!", "data": None},
    )
    result = client._normalize_response("/saveReplaceRule", response)
    assert result.ok is True
    assert result.normalized_data == {
        "message": "success inferred from legacy endpoint behavior"
    }
    assert result.warnings


def test_plain_text_response_is_reported() -> None:
    client = LegadoHttpClient(load_settings())
    request = httpx.Request("GET", "http://127.0.0.1:1122/getBookSources")
    response = httpx.Response(200, text="boom", request=request)
    result = client._normalize_response("/getBookSources", response)
    assert result.ok is False
    assert "not JSON" in result.warnings[0]


def test_prepare_local_book_upload_reports_missing_file() -> None:
    result = prepare_local_book_upload("Z:/missing/demo.txt")
    assert result.ok is False
    assert result.upstream_endpoint == "/addLocalBook"
    assert "Failed to read local file" in result.warnings[0]
