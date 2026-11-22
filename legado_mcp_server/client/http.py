from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import httpx

from legado_mcp_server.config import Settings
from legado_mcp_server.models.protocol import ApiSummary, LegadoEnvelope, ToolResult

REPLACE_RULE_LEGACY_SUCCESS_PATHS = {"/saveReplaceRule", "/deleteReplaceRule"}
DEFAULT_UNKNOWN_ERROR = "未知错误,请联系开发者!"


class LegadoHttpClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.legado_base_url,
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        )

    def configure_connection(
        self, http_base_url: str, websocket_url: str | None = None
    ) -> None:
        try:
            http_url = httpx.URL(http_base_url)
        except httpx.InvalidURL as exc:
            raise ValueError("http_base_url must be a valid URL") from exc
        if (
            http_url.scheme not in {"http", "https"}
            or not http_url.host
            or http_url.username
            or http_url.password
            or http_url.query
            or http_url.fragment
        ):
            raise ValueError(
                "http_base_url must be an http(s) URL without credentials, "
                "query, or fragment"
            )

        ws_url: httpx.URL | None = None
        if websocket_url is not None:
            try:
                ws_url = httpx.URL(websocket_url)
            except httpx.InvalidURL as exc:
                raise ValueError("websocket_url must be a valid URL") from exc
            if (
                ws_url.scheme not in {"ws", "wss"}
                or not ws_url.host
                or ws_url.username
                or ws_url.password
                or ws_url.query
                or ws_url.fragment
            ):
                raise ValueError(
                    "websocket_url must be a ws(s) URL without credentials, "
                    "query, or fragment"
                )

        self._client.base_url = http_url
        self.settings.legado_base_url = str(self._client.base_url)
        self.settings.legado_ws_url = str(ws_url).rstrip("/") if ws_url else ""

    async def aclose(self) -> None:
        await self._client.aclose()

    async def ping(self) -> ToolResult:
        try:
            response = await self._client.get("/")
        except Exception as exc:
            return ToolResult(
                ok=False,
                upstream_endpoint="/",
                normalized_data=None,
                raw_upstream=str(exc),
                warnings=["Failed to reach Legado Web service."],
            )
        return ToolResult(
            ok=response.status_code < 400,
            upstream_endpoint="/",
            normalized_data={
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
            },
            raw_upstream=response.text[:2000],
            warnings=[],
        )

    def get_api_summary(self) -> ApiSummary:
        return ApiSummary(
            base_url=self.settings.legado_base_url,
            ws_url=self.settings.resolved_ws_url,
            http_endpoints=[
                "/saveBookSource",
                "/saveBookSources",
                "/deleteBookSources",
                "/getBookSource",
                "/getBookSources",
                "/saveRssSource",
                "/saveRssSources",
                "/deleteRssSources",
                "/getRssSource",
                "/getRssSources",
                "/getReplaceRules",
                "/saveReplaceRule",
                "/deleteReplaceRule",
                "/testReplaceRule",
                "/saveBook",
                "/deleteBook",
                "/getBookshelf",
                "/refreshToc",
                "/getChapterList",
                "/getBookContent",
                "/saveBookProgress",
                "/addLocalBook",
                "/saveReadConfig",
                "/getReadConfig",
                "/cover",
                "/image",
            ],
            websocket_endpoints=[
                "/bookSourceDebug",
                "/rssSourceDebug",
                "/searchBook",
            ],
            notes=[
                "Most HTTP JSON responses use ReturnData.",
                "cover/image return binary PNG.",
                "getReplaceRules.data is a JSON string.",
                "saveReplaceRule/deleteReplaceRule may return a legacy false envelope on success.",
            ],
        )

    async def get(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> ToolResult:
        return await self._request("GET", path, params=params)

    async def post_json(self, path: str, payload: Any) -> ToolResult:
        body = json.dumps(payload, ensure_ascii=False)
        return await self._request(
            "POST",
            path,
            content=body.encode("utf-8"),
            headers={"content-type": "application/json; charset=utf-8"},
        )

    async def post_multipart(
        self,
        path: str,
        *,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes, str]],
    ) -> ToolResult:
        try:
            response = await self._client.post(path, data=data, files=files)
        except Exception as exc:
            return self._exception_result(path, exc)
        return self._normalize_response(path, response)

    async def get_image(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        suffix: str = ".png",
    ) -> ToolResult:
        try:
            response = await self._client.get(path, params=params)
        except Exception as exc:
            return self._exception_result(path, exc)
        if response.status_code >= 400:
            return ToolResult(
                ok=False,
                upstream_endpoint=path,
                normalized_data=None,
                raw_upstream=response.text,
                warnings=[f"HTTP {response.status_code} while fetching image."],
            )
        temp_dir = self.settings.runtime_tmp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = Path(
            tempfile.mkstemp(prefix="legado_", suffix=suffix, dir=temp_dir)[1]
        )
        temp_file.write_bytes(response.content)
        return ToolResult(
            ok=True,
            upstream_endpoint=path,
            normalized_data={
                "mime_type": response.headers.get("content-type", "image/png"),
                "temp_file": str(temp_file),
                "byte_size": len(response.content),
            },
            raw_upstream={"status_code": response.status_code},
            warnings=[],
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> ToolResult:
        try:
            response = await self._client.request(
                method,
                path,
                params=params,
                content=content,
                headers=headers,
            )
        except Exception as exc:
            return self._exception_result(path, exc)
        return self._normalize_response(path, response)

    @staticmethod
    def _exception_result(path: str, exc: Exception) -> ToolResult:
        return ToolResult(
            ok=False,
            upstream_endpoint=path,
            normalized_data=None,
            raw_upstream=str(exc),
            warnings=[exc.__class__.__name__],
        )

    @staticmethod
    def _normalize_response(path: str, response: httpx.Response) -> ToolResult:
        text = response.text
        warnings: list[str] = []
        if response.status_code >= 400:
            return ToolResult(
                ok=False,
                upstream_endpoint=path,
                normalized_data=None,
                raw_upstream=text,
                warnings=[f"HTTP {response.status_code}"],
            )
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return ToolResult(
                ok=False,
                upstream_endpoint=path,
                normalized_data=None,
                raw_upstream=text,
                warnings=["Upstream response is not JSON ReturnData."],
            )

        if not isinstance(payload, dict):
            return ToolResult(
                ok=False,
                upstream_endpoint=path,
                normalized_data=None,
                raw_upstream=payload,
                warnings=["Unexpected non-object JSON response."],
            )

        envelope = LegadoEnvelope.model_validate(payload)
        normalized_data = envelope.data
        ok = envelope.isSuccess

        if path == "/getReplaceRules" and isinstance(envelope.data, str):
            try:
                normalized_data = json.loads(envelope.data)
            except json.JSONDecodeError:
                warnings.append("getReplaceRules.data was not valid JSON text.")

        if (
            path in REPLACE_RULE_LEGACY_SUCCESS_PATHS
            and not envelope.isSuccess
            and envelope.errorMsg == DEFAULT_UNKNOWN_ERROR
            and envelope.data is None
        ):
            ok = True
            normalized_data = {
                "message": "success inferred from legacy endpoint behavior"
            }
            warnings.append(
                "Upstream endpoint returned the legacy default envelope; treated as success."
            )

        if not ok and envelope.errorMsg:
            warnings.append(envelope.errorMsg)

        return ToolResult(
            ok=ok,
            upstream_endpoint=path,
            normalized_data=normalized_data,
            raw_upstream=payload,
            warnings=warnings,
        )
