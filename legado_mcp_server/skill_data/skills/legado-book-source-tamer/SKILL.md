---
name: legado-book-source-tamer
description: 使用 Legado MCP 工具查询知识、分析公开站点、验证和调试书源，并审查候选修复。
---

# Legado 书源开发

按用户请求选择知识查询、站点分析、规则验证或书源调试流程。不要假设仓库包含 Legado 源码、旧版 Agent 工具或本地文件整理模块。

## 先判断“测试链接”的类型

- 后端/API 地址：按提供的接口定义直接发 HTTP 请求或调用已有后端工具，核对方法、参数、状态码和响应内容；不要把 API 请求解释为浏览器页面操作。
- 本机或内网 API：使用当前环境可访问该地址的 HTTP 客户端或后端连接。本站点抓取工具只允许公网地址，不能用来测试回环或私有地址。
- 公开网页：只有需要检查网页 HTML/结构时才使用 `skill_*` 网站工具；页面渲染或交互验证才使用浏览器。
- 文件路径：直接读取和解析文件本身，不要当成网页链接打开。

## Legado 后端连接诊断

- `legado_connection_info()`：查看当前 HTTP / WebSocket 地址和配置提示；只读配置，不测试连接或修改配置。
- `legado_ping()`：检查 Legado Web HTTP 服务是否可达。
- 用户明确提供新地址并要求切换时，可调用 `legado_connection_configure(http_base_url, websocket_url=None)`；省略 WebSocket 地址时按 HTTP 端口加 1 推导。此修改只作用于当前进程，重启后恢复启动配置。
- `book_source_debug(tag, key, mode="auto", timeout_seconds=30)`：通过已配置的 WebSocket 后端调试书源；`tag` 是书源 URL，目标站点地址来自书源配置。
- 用户提供新地址并要求测试时，先调用 `legado_connection_configure` 切换，再用 `legado_ping` 检查 HTTP，最后运行指定测试；`legado_ping` 不验证 WebSocket，`book_source_debug` 才会实际连接该 WebSocket。

## 可用工具

### 知识库

- `skill_search_knowledge(query, max_results=8)`：搜索随包知识和书源案例。
- `skill_get_css_rules(page=1, page_size=200)`：分页读取 CSS 和提取规则。
- `skill_get_source_examples(query="", limit=5)`：查找随包书源案例。
- `skill_get_templates(limit=5)`：读取书源模板片段。
- `skill_read_document(path, page=1, page_size=200)`：分页读取 `assets/`、`docs/` 或随包书源 skill 文档。
- `skill_list_knowledge(prefix="assets/", limit=200)`：列出允许的知识资源目录。

按需查询。知识库和案例只能提供线索；必须结合用户给出的真实页面或实际调试结果判断规则。

### 网站分析

- `skill_detect_charset(url, timeout_seconds=20)`：读取页面并检测编码。
- `skill_fetch_html(url, charset="", timeout_seconds=20, max_chars=30000, headers=None)`：获取并解码 HTML。
- `skill_analyze_search(url, charset="", timeout_seconds=20)`：分析搜索页结构。
- `skill_analyze_book_info(url, charset="", timeout_seconds=20)`：分析详情页结构。
- `skill_analyze_toc(url, charset="", timeout_seconds=20)`：分析目录页和章节链接。
- `skill_analyze_content(url, charset="", timeout_seconds=20)`：分析正文容器和分页链接。

抓取只允许目标主机解析到公网 IP，并验证实际连接对端；回环、私有地址及重定向到非公网地址会被拒绝。每次抓取最多跟随 5 次重定向，响应体不超过 10 MiB；`skill_fetch_html` 返回的 HTML 最多 100000 字符。不要尝试用代理、替代地址或重定向绕过限制。除非用户明确授权且确有必要，不要发送 Cookie、Authorization 或其他敏感请求头。

### 规则验证与调试

- `skill_validate_source(source)`：检查一个书源对象的 JSON 结构和规则字段。
- `skill_parse_rule(rule, html, base_url="", js_lib="")`：对给定 HTML 验证单条规则。
- `skill_debug_local(source, stage="search", keyword="斗破苍穹", url="")`：请求书源配置的公开网址并运行 Python 调试引擎。`stage` 可选 `search`、`book_info`、`toc`、`content`、`full`。
- `skill_analyze_error(test_result)`：分类调试结果中的错误。
- `skill_suggest_fix(source, error_type, error_message, html_preview="")`：生成候选规则修改。
- `skill_auto_fix(source, keyword="斗破苍穹", max_attempts=3)`：运行在线修复循环；实际尝试次数限制为 1–5。

## 工作流程

1. 确认用户要解决的阶段和已提供的书源、页面 HTML、URL。缺少真实 HTML 时，可在目标地址符合抓取限制的前提下使用网站分析工具；不要编造页面结构。
   - 编写发现地址（`exploreUrl`）的动态 URL 时，统一以 `sourceUrl` 为基址拼接路径；不要使用当前详情页或目录页 URL 作为基址。
2. 遇到语法或字段问题时，先调用 `skill_validate_source`。需要规则知识时，只查询对应的 CSS 规则、模板或案例，不要求无关工具全部调用。
3. 用真实 HTML 调用 `skill_parse_rule` 验证候选规则。保留页面 URL 和相关 HTML 片段，说明验证范围。
4. 需要联调时，调用 `skill_debug_local` 对应阶段；根据结果选择 `skill_analyze_error` 和 `skill_suggest_fix`。
5. 只有用户明确需要自动迭代时才调用 `skill_auto_fix`。检查候选书源和修复记录，再运行 `skill_validate_source` 与适用阶段的 `skill_debug_local`。
6. 清楚说明结果来自知识库参考、静态校验、Python 模拟或 Legado App 实测。Python 模拟成功不代表 App 实测成功。

## JavaScript 边界

书源 JavaScript 默认关闭。`skill_parse_rule` 遇到 JS 规则时会报告禁用；本地调试对 JS 规则的结果也不能视为有效执行结果。不要把这种情况报告为规则已通过。

操作者可以设置 `LEGADO_ENABLE_UNSAFE_JS=1` 启用 JS，但脚本会以服务进程的权限运行。只有在书源完全可信且操作者明确接受该风险时才启用；不要为来自用户、网站或知识库的未知代码自动启用。

## 写入与保存

验证、分析和自动修复工具返回结果，不会替用户保存书源。检查并说明候选变更；只有用户明确要求写入 Legado 时，才调用对应的书源保存工具。不要假设可用 `Write`、`RunCommand`、`file_organizer` 或其他本地文件工具。