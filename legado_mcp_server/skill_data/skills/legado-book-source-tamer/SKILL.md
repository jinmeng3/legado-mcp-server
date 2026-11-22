---
name: legado-book-source-tamer
description: 使用 Legado MCP 工具查询知识、分析公开站点、验证和调试书源，并审查候选修复。
---

# Legado 书源开发

按用户请求选择知识查询、站点分析、规则验证或书源调试流程。不要假设仓库包含 Legado 源码、旧版 Agent 工具或本地文件整理模块。

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