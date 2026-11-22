from __future__ import annotations

import io
import json
import os
import re
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

from legado_mcp_server.safe_http import fetch_public_url

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_DATA_ROOT = _PACKAGE_ROOT / "skill_data"
_ASSETS_ROOT = _DATA_ROOT / "assets"
_SOURCE_SKILL_PREFIX = ".trae/skills/legado-book-source-tamer/"


def _resource_path(path: str) -> Path:
    clean = PurePosixPath(path)
    if not clean.parts or clean.is_absolute() or ".." in clean.parts:
        raise ValueError("path must be a relative knowledge file path")
    normalized = clean.as_posix()
    if clean.parts[0] == "assets":
        return _DATA_ROOT.joinpath(*clean.parts)
    if clean.parts[0] == "docs":
        return _PACKAGE_ROOT.parent.joinpath(*clean.parts)
    if normalized.startswith(_SOURCE_SKILL_PREFIX):
        relative = normalized[len(_SOURCE_SKILL_PREFIX) :]
        return _DATA_ROOT / "skills" / "legado-book-source-tamer" / relative
    raise ValueError("path must be under assets/, docs/, or the bundled source skill")


def _members(prefix: str = "assets/") -> list[str]:
    if prefix == "assets/" or prefix.startswith("assets/"):
        root = _ASSETS_ROOT / prefix.removeprefix("assets/")
        output_prefix = prefix
    elif prefix == _SOURCE_SKILL_PREFIX:
        root = _DATA_ROOT / "skills" / "legado-book-source-tamer"
        output_prefix = prefix
    else:
        raise ValueError("unsupported knowledge prefix")
    if not root.is_dir():
        return []
    return sorted(output_prefix + path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _read_asset(path: str) -> str:
    file_path = _resource_path(path)
    try:
        return file_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        raise FileNotFoundError(f"Knowledge file not found: {path}") from exc


def _engine() -> tuple[Any, Any, Any, Any]:
    from legado_mcp_server.skill_engine.debugger.engine import AnalyzeRule, AutoFixer, BookSource, DebugEngine
    from legado_mcp_server.skill_engine.debugger.engine.auto_fixer import ErrorAnalysis, ErrorType

    return AnalyzeRule, AutoFixer, BookSource, (DebugEngine, ErrorAnalysis, ErrorType)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _fetch(
    url: str,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, str, int, dict[str, str]]:
    return fetch_public_url(
        url,
        headers=headers,
        timeout_seconds=timeout_seconds,
    )


def _decode_html(data: bytes, headers: dict[str, str], charset: str = "") -> tuple[str, str]:
    declared = charset
    if not declared:
        content_type = headers.get("content-type", "")
        match = re.search(r"charset\s*=\s*['\"]?([^;\s'\"]+)", content_type, re.I)
        if match:
            declared = match.group(1)
    if not declared:
        match = re.search(rb"<meta[^>]+charset\s*=\s*['\"]?([^\s'\"/>;]+)", data[:8192], re.I)
        if match:
            declared = match.group(1).decode("ascii", errors="ignore")
    candidates = [declared, "utf-8", "gb18030", "big5"]
    for candidate in candidates:
        if candidate:
            try:
                return data.decode(candidate), candidate
            except (LookupError, UnicodeDecodeError):
                continue
    return data.decode("utf-8", errors="replace"), "utf-8 (replacement)"


def _analyze_html(html: str, url: str, page_type: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    candidates: list[dict[str, Any]] = []
    selectors = [".book-item", ".result-item", ".book", ".list li", "#list li", "#list dd", ".chapter-list li", ".content", "#content", "#chaptercontent", "article"]
    for selector in selectors:
        found = soup.select(selector)
        if found:
            candidates.append({"selector": selector, "count": len(found), "sample": found[0].get_text(" ", strip=True)[:180]})
    links = []
    for anchor in soup.select("a[href]")[:30]:
        label = anchor.get_text(" ", strip=True)
        href = urljoin(url, anchor.get("href", ""))
        if label or href:
            links.append({"text": label[:100], "url": href})
    text = soup.get_text(" ", strip=True)
    pagination_links = []
    for anchor in soup.select("a[href]"):
        label = anchor.get_text(" ", strip=True)
        rel = " ".join(anchor.get("rel", [])) if isinstance(anchor.get("rel"), list) else str(anchor.get("rel", ""))
        if re.search(r"下一页|下一章|下页|下一|末页|next", label + " " + rel, re.I):
            pagination_links.append({"text": label[:100], "url": urljoin(url, anchor.get("href", ""))})
    return {
        "page_type": page_type,
        "url": url,
        "title": title,
        "html_length": len(html),
        "text_preview": text[:1000],
        "selector_candidates": candidates,
        "links": links,
        "pagination_links": pagination_links[:20],
        "forms": [
            {"action": urljoin(url, form.get("action", "")), "method": form.get("method", "GET").upper(), "inputs": [{"name": item.get("name", ""), "type": item.get("type", "text")} for item in form.select("input[name]")[:20]]}
            for form in soup.select("form")[:10]
        ],
    }


def register_skill_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def skill_search_knowledge(query: str, max_results: int = 8) -> dict[str, Any]:
        """Search Legado source development knowledge files bundled from assets/ and SKILL.md."""
        terms = [term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", query) if term]
        results = []
        for prefix in ("assets/", _SOURCE_SKILL_PREFIX):
            for path in _members(prefix):
                if Path(path).suffix.lower() not in {".md", ".txt", ".json"}:
                    continue
                file_path = _resource_path(path)
                if file_path.stat().st_size > 2_000_000:
                    continue
                text = _read_asset(path)
                lower = text.lower()
                score = sum(lower.count(term) for term in terms)
                if score:
                    positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
                    pos = min(positions, default=0)
                    start = max(0, pos - 200)
                    results.append((score, path, text[start : start + 900]))
        results.sort(key=lambda item: (-item[0], item[1]))
        return {"query": query, "results": [{"path": path, "score": score, "excerpt": excerpt} for score, path, excerpt in results[: max(1, min(max_results, 20))]]}

    @mcp.tool()
    def skill_get_css_rules(page: int = 1, page_size: int = 200) -> dict[str, Any]:
        """Read a page of the CSS selector and extraction rule reference."""
        path = "assets/css选择器规则.txt"
        lines = _read_asset(path).splitlines()
        page_size = max(1, min(page_size, 500))
        page = max(1, page)
        start = (page - 1) * page_size
        return {"path": path, "page": page, "page_size": page_size, "total_lines": len(lines), "total_pages": (len(lines) + page_size - 1) // page_size, "content": "\n".join(lines[start : start + page_size])}

    @mcp.tool()
    def skill_get_source_examples(query: str = "", limit: int = 5) -> dict[str, Any]:
        """Find real book source examples by filename or content."""
        limit = max(1, min(limit, 10))
        paths = _members("assets/knowledge_base/book_sources/")
        words = [word.lower() for word in re.findall(r"[\w\u4e00-\u9fff]+", query) if word]
        ranked = []
        for path in paths:
            file_path = _resource_path(path)
            name = Path(path).name
            score = sum(name.lower().count(word) * 3 for word in words)
            if words and not score and file_path.stat().st_size > 500_000:
                continue
            text = _read_asset(path) if file_path.stat().st_size <= 500_000 else ""
            if words and not score:
                score = sum(text.lower().count(word) for word in words)
            if not words or score:
                ranked.append((score, path, text[:6000]))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return {"query": query, "examples": [{"path": path, "excerpt": excerpt} for _, path, excerpt in ranked[:limit]]}

    @mcp.tool()
    def skill_get_templates(limit: int = 5) -> dict[str, Any]:
        """Return template sections from the real source template library."""
        text = _read_asset("assets/真实书源模板库.txt")
        sections = re.split(r"(?=^#{1,3}\s|^【[^】]+】|^\s*书源名称)", text, flags=re.M)
        nonempty = [section.strip() for section in sections if section.strip()]
        return {"path": "assets/真实书源模板库.txt", "templates": nonempty[: max(1, min(limit, 10))]}

    @mcp.tool()
    def skill_read_document(path: str, page: int = 1, page_size: int = 200) -> dict[str, Any]:
        """Read a paginated text document from assets/ or docs/."""
        text = _read_asset(path)
        lines = text.splitlines()
        page_size = max(1, min(page_size, 500))
        page = max(1, page)
        start = (page - 1) * page_size
        return {"path": path, "page": page, "page_size": page_size, "total_lines": len(lines), "total_pages": (len(lines) + page_size - 1) // page_size, "content": "\n".join(lines[start : start + page_size])}

    @mcp.tool()
    def skill_list_knowledge(prefix: str = "assets/", limit: int = 200) -> dict[str, Any]:
        """List files in the bundled knowledge base."""
        allowed_prefixes = {"assets/", "assets/knowledge_base/", "assets/knowledge_base/book_sources/", ".trae/skills/legado-book-source-tamer/"}
        if prefix not in allowed_prefixes:
            raise ValueError("unsupported knowledge prefix")
        paths = _members(prefix)
        return {"prefix": prefix, "total": len(paths), "files": paths[: max(1, min(limit, 500))], "truncated": len(paths) > limit}

    @mcp.tool()
    def skill_detect_charset(url: str, timeout_seconds: float = 20.0) -> dict[str, Any]:
        """Fetch a page and detect its response charset from HTTP headers or HTML metadata."""
        data, final_url, status, headers = _fetch(url, timeout_seconds)
        _, charset = _decode_html(data, headers)
        return {"url": final_url, "status_code": status, "charset": charset, "content_type": headers.get("content-type", ""), "sample_bytes": data[:120].hex()}

    @mcp.tool()
    def skill_fetch_html(url: str, charset: str = "", timeout_seconds: float = 20.0, max_chars: int = 30000, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Fetch real page HTML and decode it using an explicit, HTTP, or meta charset."""
        data, final_url, status, response_headers = _fetch(url, timeout_seconds, headers)
        html, detected = _decode_html(data, response_headers, charset)
        return {"url": final_url, "status_code": status, "charset": detected, "headers": response_headers, "html_length": len(html), "html": html[: max(1, min(max_chars, 100000))], "truncated": len(html) > max_chars}

    @mcp.tool()
    def skill_analyze_search(url: str, charset: str = "", timeout_seconds: float = 20.0) -> dict[str, Any]:
        """Fetch and summarize a search page structure, forms, links, and likely result containers."""
        data, final_url, status, headers = _fetch(url, timeout_seconds)
        html, detected = _decode_html(data, headers, charset)
        result = _analyze_html(html, final_url, "search")
        result.update({"status_code": status, "charset": detected})
        return result

    @mcp.tool()
    def skill_analyze_book_info(url: str, charset: str = "", timeout_seconds: float = 20.0) -> dict[str, Any]:
        """Fetch and summarize a book detail page and likely metadata fields."""
        data, final_url, status, headers = _fetch(url, timeout_seconds)
        html, detected = _decode_html(data, headers, charset)
        result = _analyze_html(html, final_url, "book_info")
        result.update({"status_code": status, "charset": detected})
        return result

    @mcp.tool()
    def skill_analyze_toc(url: str, charset: str = "", timeout_seconds: float = 20.0) -> dict[str, Any]:
        """Fetch and summarize a table of contents page and chapter link candidates."""
        data, final_url, status, headers = _fetch(url, timeout_seconds)
        html, detected = _decode_html(data, headers, charset)
        result = _analyze_html(html, final_url, "toc")
        result.update({"status_code": status, "charset": detected})
        return result

    @mcp.tool()
    def skill_analyze_content(url: str, charset: str = "", timeout_seconds: float = 20.0) -> dict[str, Any]:
        """Fetch and summarize a chapter page, content containers, and pagination links."""
        data, final_url, status, headers = _fetch(url, timeout_seconds)
        html, detected = _decode_html(data, headers, charset)
        result = _analyze_html(html, final_url, "content")
        result.update({"status_code": status, "charset": detected})
        return result

    @mcp.tool()
    def skill_validate_source(source: dict[str, Any] | str) -> dict[str, Any]:
        """Validate book source JSON shape, known fields, rule sections, and required values."""
        try:
            payload = json.loads(source) if isinstance(source, str) else source
        except json.JSONDecodeError as exc:
            return {"valid": False, "errors": [f"Invalid JSON: {exc}"]}
        if isinstance(payload, list):
            if len(payload) != 1:
                return {"valid": False, "errors": ["Provide one source object per call"]}
            payload = payload[0]
        if not isinstance(payload, dict):
            return {"valid": False, "errors": ["Source must be a JSON object"]}
        _, _, BookSource, _ = _engine()
        from legado_mcp_server.skill_engine.debugger.engine.book_source import BookInfoRule, ContentRule, ExploreRule, SearchRule, TocRule

        section_models = {"ruleSearch": SearchRule, "ruleBookInfo": BookInfoRule, "ruleToc": TocRule, "ruleContent": ContentRule, "ruleExplore": ExploreRule}
        fields = set(BookSource.__dataclass_fields__)
        errors = []
        warnings = []
        unknown = sorted(set(payload) - fields)
        if unknown:
            errors.append("Unknown source fields: " + ", ".join(unknown))
        for key in ("bookSourceUrl", "bookSourceName"):
            if not payload.get(key):
                errors.append(f"Missing required field: {key}")
        for section, model_type in section_models.items():
            value = payload.get(section)
            if value is not None and not isinstance(value, dict):
                errors.append(f"{section} must be an object")
            elif isinstance(value, dict):
                unknown_rules = sorted(set(value) - set(model_type.__dataclass_fields__))
                if unknown_rules:
                    errors.append(f"Unknown {section} fields: " + ", ".join(unknown_rules))
        content_rules = payload.get("ruleContent")
        if isinstance(content_rules, dict) and "prevContentUrl" in content_rules:
            errors.append("ruleContent.prevContentUrl is unsupported; use nextContentUrl")
        serialized = json.dumps(payload, ensure_ascii=False)
        forbidden = re.findall(r":(?:contains|first-child|last-child)\b", serialized)
        if forbidden:
            errors.append("Unsupported selector pseudo-class found: " + ", ".join(sorted(set(forbidden))))
        try:
            normalized = BookSource.from_dict(payload).to_dict()
        except Exception as exc:
            errors.append(f"BookSource model conversion failed: {exc}")
            normalized = None
        return {"valid": not errors, "errors": errors, "warnings": warnings, "normalized_source": normalized}

    @mcp.tool()
    def skill_parse_rule(rule: str, html: str, base_url: str = "", js_lib: str = "") -> dict[str, Any]:
        """Run an AnalyzeRule expression against supplied HTML and return extracted values."""
        if ("@js:" in rule or "<js>" in rule) and os.environ.get(
            "LEGADO_ENABLE_UNSAFE_JS", ""
        ).lower() not in {"1", "true", "yes", "on"}:
            return {"rule": rule, "error": "JavaScript rules are disabled by default."}
        AnalyzeRule, _, _, _ = _engine()
        analyzer = AnalyzeRule(html, base_url, js_lib or None)
        try:
            elements = analyzer.get_elements(rule)
            values = [str(element)[:2000] for element in elements]
            result = analyzer.get_string_list(rule)
            return {"rule": rule, "values": result, "element_count": len(elements), "element_previews": values[:30]}
        except Exception as exc:
            return {"rule": rule, "error": str(exc)}

    @mcp.tool()
    def skill_debug_local(source: dict[str, Any] | str, stage: str = "search", keyword: str = "斗破苍穹", url: str = "") -> dict[str, Any]:
        """Run the upstream local DebugEngine against the selected book source stage."""
        try:
            payload = json.loads(source) if isinstance(source, str) else source
            if isinstance(payload, list):
                payload = payload[0]
            _, _, BookSource, engine_types = _engine()
            DebugEngine = engine_types[0]
            engine = DebugEngine(BookSource.from_dict(payload))
            methods = {"search": lambda: engine.test_search(keyword), "book_info": lambda: engine.test_book_info(url or None, keyword), "toc": lambda: engine.test_toc(url or None, keyword), "content": lambda: engine.test_content(url or None, keyword), "full": lambda: engine.run_full_test(keyword)}
            if stage not in methods:
                raise ValueError("stage must be search, book_info, toc, content, or full")
            return _jsonable(methods[stage]())
        except Exception as exc:
            return {"success": False, "error": str(exc), "stage": stage}

    @mcp.tool()
    def skill_analyze_error(test_result: dict[str, Any]) -> dict[str, Any]:
        """Classify a DebugEngine failure using the upstream AutoFixer analyzer."""
        _, AutoFixer, _, _ = _engine()
        analysis = AutoFixer({}).analyze_error(test_result)
        return _jsonable(analysis)

    @mcp.tool()
    def skill_suggest_fix(source: dict[str, Any] | str, error_type: str, error_message: str, html_preview: str = "") -> dict[str, Any]:
        """Generate a candidate source patch from an upstream AutoFixer error classification."""
        payload = json.loads(source) if isinstance(source, str) else source
        if isinstance(payload, list) and len(payload) == 1:
            payload = payload[0]
        _, AutoFixer, _, internals = _engine()
        ErrorAnalysis, ErrorType = internals[1], internals[2]
        try:
            kind = ErrorType(error_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported error_type: {error_type}") from exc
        result = AutoFixer(payload).generate_fix(ErrorAnalysis(kind, error_message, html_preview=html_preview), html_preview)
        return _jsonable(result)

    @mcp.tool()
    def skill_auto_fix(source: dict[str, Any] | str, keyword: str = "斗破苍穹", max_attempts: int = 3) -> dict[str, Any]:
        """Run the upstream AutoFixer test-and-repair loop against live source pages."""
        import contextlib

        payload = json.loads(source) if isinstance(source, str) else source
        if isinstance(payload, list) and len(payload) == 1:
            payload = payload[0]
        _, AutoFixer, BookSource, internals = _engine()
        DebugEngine = internals[0]
        engine = DebugEngine(BookSource.from_dict(payload))
        fixer = AutoFixer(payload, engine)

        def run_test(requested_keyword: str) -> dict[str, Any]:
            engine.book_source = BookSource.from_dict(fixer.book_source)
            return _jsonable(engine.test_content(None, search_keyword=requested_keyword))

        fixer._run_test = run_test
        with contextlib.redirect_stdout(io.StringIO()):
            result = fixer.auto_fix_and_test(keyword, max_attempts=max(1, min(max_attempts, 5)))
        return _jsonable(result)
