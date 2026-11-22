---
name: legado-mcp-site-analysis
description: Use the Legado MCP website tools to inspect live pages and derive book source selectors from real HTML.
---

# Legado MCP 网站结构分析

书源选择器必须由目标站点真实页面推导。使用项目 `skill_*` 网站工具获取编码、HTML 和页面结构。

## 先判断“测试链接”的类型

- 后端/API 地址：直接调用用户提供的 HTTP API 或项目已有后端工具，按接口定义检查方法、参数、状态码、响应头和响应体。不要把 API 请求转成浏览器页面操作。
- 本机或内网 API：使用可访问该网络的 HTTP 客户端或项目后端连接。本站点抓取工具只允许公网目标；不要用 `skill_fetch_html` 测本机或私有地址，也不要尝试绕过限制。
- 公开网页：只有需要分析网页内容时才用 `skill_detect_charset`、`skill_fetch_html` 和 `skill_analyze_*`。只有用户明确要验证页面渲染或交互时，才使用浏览器。
- 文件路径：直接读取并解析文件本身；检查 JSON 时可用 `skill_validate_source`。不要把文件路径当作网页链接打开。
- “测试链接”没有说明目标类型时，先结合用户提供的 API、代码和文件判断；只在缺少必要的接口参数或预期结果时再询问。

## Legado 后端连接诊断

- `legado_connection_info()` 只显示 MCP 当前配置的 Legado HTTP / WebSocket 地址和配置提示，不测试或修改连接。
- 用户明确提供新地址并要求切换时，可调用 `legado_connection_configure(http_base_url, websocket_url=None)`；只作用于当前 MCP 进程，重启后恢复启动配置。
- `legado_ping()` 检查 Legado Web HTTP 服务是否可达。`book_source_debug` 使用配置好的 WebSocket 后端；`tag` 选择书源，目标站点地址来自书源配置。
- 用户提供新地址并要求测试时，先调用 `legado_connection_configure` 切换，再用 `legado_ping` 检查 HTTP，最后运行指定测试；`legado_ping` 不验证 WebSocket，`book_source_debug` 才会实际连接该 WebSocket。

## 分析流程

1. 从站点可访问入口开始，先调用 `skill_detect_charset(url)`。
2. 调用 `skill_fetch_html(url, charset=...)` 检查原始 HTML；优先分析表单 action、输入字段、链接和页面中的 API 线索。
3. 按页面类型调用 `skill_analyze_search`、`skill_analyze_book_info`、`skill_analyze_toc` 或 `skill_analyze_content`。
4. 从返回的真实结构推导候选选择器，并用 `skill_parse_rule(rule, html, base_url)` 对原始 HTML 验证。
5. 给出依据：页面 URL、命中的结构、提取结果和仍需人工确认的项。

## 约束

- 不猜搜索接口；先检查 HTML 表单和内嵌脚本线索。需要访问 API 时再直接测试发现的地址。
- 网站抓取仅允许目标主机解析到公网 IP，并校验实际连接地址；回环、私有网段和重定向到非公网地址会被拒绝。不要尝试绕过此限制。
- 抓取最多跟随 5 次重定向，响应体上限为 10 MiB；`skill_fetch_html` 返回的 HTML 最多 100000 字符。超限时说明截断或请求被拒绝。
- 编写或修复发现地址（`exploreUrl`）的动态 URL 时，统一以 `sourceUrl` 为基址拼接路径；不要改用当前详情页或目录页 URL。
- HTML 可能动态加载、需要 Cookie、特定请求头或受反爬保护。工具返回空页面时，明确报告证据，不把空结果当成页面不存在。
- 编码优先以 HTTP `Content-Type` 和 HTML meta 为准；遇到乱码时显式传入候选 charset 再比较。
- 分析工具只返回有限长度的 HTML/文本预览。需要完整内容时用 `skill_fetch_html` 调高 `max_chars`，上限 100000 字符。
