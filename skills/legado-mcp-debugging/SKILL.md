---
name: legado-mcp-debugging
description: Validate, parse, debug, and repair Legado book source JSON with the project's skill MCP tools.
---

# Legado MCP 规则验证与调试

使用以下流程定位并修复书源规则问题：

1. `skill_validate_source(source)` 检查 JSON 结构、书源字段和规则区块。
2. 先用真实页面 HTML 调用 `skill_parse_rule(rule, html, base_url)` 验证单条规则；保留输入 HTML 与页面 URL 以便复现。
3. 页面联调调用 `skill_debug_local(source, stage, keyword, url)`。`stage` 可选 `search`、`book_info`、`toc`、`content`、`full`。
4. 对失败结果调用 `skill_analyze_error(test_result)`，然后按需调用 `skill_suggest_fix(source, error_type, error_message, html_preview)`。
5. 只有明确需要迭代时运行 `skill_auto_fix(source, keyword, max_attempts)`。检查返回的 `fixed_source` 和 `fix_history`，再通过 `skill_validate_source` 与 `skill_debug_local` 复核。

## Legado 后端连接

- `legado_connection_info()`：查看当前 HTTP / WebSocket 地址和配置提示；只读配置，不测试连接，也不修改配置。
- 用户明确提供新地址并要求切换时，调用 `legado_connection_configure(http_base_url, websocket_url=None)` 更新当前进程；省略 WebSocket 地址时按 HTTP 端口加 1 推导。此修改不持久，重启后恢复启动配置。
- `legado_ping()`：检查 Legado Web HTTP 服务是否可达。
- `book_source_debug` 通过已配置的 WebSocket 后端调试 `tag` 指定的书源；连接地址由 MCP 服务配置决定，不是目标书源地址参数。
- 用户提供新地址并要求测试时，先调用 `legado_connection_configure` 切换，再用 `legado_ping` 检查 HTTP，最后运行指定测试；`legado_ping` 不验证 WebSocket，`book_source_debug` 才会实际连接该 WebSocket。

## 安全和正确性

- `skill_debug_local` 与 `skill_auto_fix` 会对书源中的目标网址发起网络请求；只提供可信书源。
- `skill_parse_rule`、`skill_debug_local` 和 `skill_auto_fix` 默认不执行书源 JavaScript；JS 规则结果不完整时应明确报告这一限制。
- 只有操作者明确接受以服务进程权限执行可信书源代码时，才设置 `LEGADO_ENABLE_UNSAFE_JS=1`。不要为不可信来源启用。
- 编写或修复发现地址（`exploreUrl`）的动态 URL 时，统一以 `sourceUrl` 为基址拼接路径；不要改用当前详情页或目录页 URL。
- 自动修复结果是候选书源，必须检查变更并重新验证，不能直接覆盖用户数据。
- 本地 Python 引擎是近似实现。CSS 细节、Rhino JavaScript、正则和编码行为可能与 Legado 有差异；冲突时查看 Legado Kotlin 实现，并以阅读 App 实测为最终判断。
- 不因模拟成功宣称阅读 App 中已验证成功；清楚区分静态验证、Python 调试和 App 实测。
