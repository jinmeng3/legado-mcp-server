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

## 安全和正确性

- `skill_debug_local` 与 `skill_auto_fix` 会对书源中的目标网址发起网络请求；只提供可信书源。
- 自动修复结果是候选书源，必须检查变更并重新验证，不能直接覆盖用户数据。
- 本地 Python 引擎是近似实现。CSS 细节、Rhino JavaScript、正则和编码行为可能与 Legado 有差异；冲突时查看 Legado Kotlin 实现，并以阅读 App 实测为最终判断。
- 不因模拟成功宣称阅读 App 中已验证成功；清楚区分静态验证、Python 调试和 App 实测。
