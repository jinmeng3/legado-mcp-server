---
name: legado-mcp-site-analysis
description: Use the Legado MCP website tools to inspect live pages and derive book source selectors from real HTML.
---

# Legado MCP 网站结构分析

书源选择器必须由目标站点真实页面推导。使用项目 `skill_*` 网站工具获取编码、HTML 和页面结构。

## 分析流程

1. 从站点可访问入口开始，先调用 `skill_detect_charset(url)`。
2. 调用 `skill_fetch_html(url, charset=...)` 检查原始 HTML；优先分析表单 action、输入字段、链接和页面中的 API 线索。
3. 按页面类型调用 `skill_analyze_search`、`skill_analyze_book_info`、`skill_analyze_toc` 或 `skill_analyze_content`。
4. 从返回的真实结构推导候选选择器，并用 `skill_parse_rule(rule, html, base_url)` 对原始 HTML 验证。
5. 给出依据：页面 URL、命中的结构、提取结果和仍需人工确认的项。

## 约束

- 不猜搜索接口；先检查 HTML 表单和内嵌脚本线索。需要访问 API 时再直接测试发现的地址。
- HTML 可能动态加载、需要 Cookie、特定请求头或受反爬保护。工具返回空页面时，明确报告证据，不把空结果当成页面不存在。
- 编码优先以 HTTP `Content-Type` 和 HTML meta 为准；遇到乱码时显式传入候选 charset 再比较。
- 分析工具只返回有限长度的 HTML/文本预览。需要完整内容时用 `skill_fetch_html` 调高 `max_chars`，上限 100000 字符。
