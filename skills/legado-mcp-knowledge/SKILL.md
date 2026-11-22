---
name: legado-mcp-knowledge
description: Use the Legado knowledge library MCP tools to learn source rules, find templates, and inspect real source examples.
---

# Legado MCP 知识库查询

处理 Legado 书源规则、CSS/XPath/JSONPath、请求配置或字段问题时，先查询项目内知识库，再组织答案或编写规则。

## 工具顺序

1. 用 `skill_search_knowledge(query)` 搜索具体问题。
2. 选择器问题使用 `skill_get_css_rules(page)`；完整文档用 `skill_read_document(path, page)` 分页读取。
3. 需要可复用规则结构时调用 `skill_get_templates()`；需要实际站点写法时调用 `skill_get_source_examples(query, limit)`。
4. 不确定资源文件名或可用案例时调用 `skill_list_knowledge(prefix)`。

## 约束

- 知识库是参考。根据目标页面实际 HTML 选择规则，不能照搬案例中的站点 URL 或选择器。
- 使用 `nextContentUrl` 表示正文页的后续分页；不要生成 `prevContentUrl`。
- Legado 规则不要使用 `:contains()`、`:first-child` 或 `:last-child`；按知识库中的 Legado 语法选择提取方式和索引。
- 需要引用长文档时说明实际读取的路径和页码。
