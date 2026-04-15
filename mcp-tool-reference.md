# MCP 工具说明

本文档说明 `legado-mcp-server` 暴露给 MCP 客户端的工具、参数和返回结构。上游 Legado HTTP / WebSocket 细节见 [Legado Web 接口文档](./legado-web-api.md)。

## 统一返回结构

除 resources 外，所有工具都返回统一对象：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ok` | `boolean` | 归一化后的成功标记 |
| `upstream_endpoint` | `string` | 对应的上游 HTTP 路径或会话类型 |
| `normalized_data` | `any` | 归一化后的主要结果 |
| `raw_upstream` | `any` | 上游原始响应或调试上下文 |
| `warnings` | `string[]` | 兼容处理、超时、异常等提醒 |
| `session_id` | `string \| null` | 会话类工具返回的会话 ID |

## 基础工具

### `legado_ping()`

- 作用：检查 Legado Web 服务是否可达
- 参数：无

### `legado_get_api_summary()`

- 作用：返回当前支持的 HTTP / WebSocket 概要
- 参数：无

## 书源工具

### `book_source_get(url)`

- `url: string`
- 返回单个 `BookSource`

### `book_source_list()`

- 返回全部书源列表

### `book_source_save(source)`

- `source: BookSource | object`
- 保存单个书源

### `book_source_save_many(sources)`

- `sources: Array<BookSource | object>`
- 批量保存书源

### `book_source_delete_many(sources)`

- `sources: Array<BookSource | object>`
- 批量删除书源

## RSS 工具

### `rss_source_get(url)`

- `url: string`
- 返回单个 `RssSource`

### `rss_source_list()`

- 返回全部 RSS 源

### `rss_source_save(source)`

- `source: RssSource | object`

### `rss_source_save_many(sources)`

- `sources: Array<RssSource | object>`

### `rss_source_delete_many(sources)`

- `sources: Array<RssSource | object>`

## 替换规则工具

### `replace_rule_list()`

- 返回全部 `ReplaceRule`
- 已自动处理上游“字符串化 JSON 数组”问题

### `replace_rule_save(rule)`

- `rule: ReplaceRule | object`
- 已兼容上游旧式成功包络

### `replace_rule_delete(rule)`

- `rule: ReplaceRule | object`
- 已兼容上游旧式成功包络

### `replace_rule_test(rule, text)`

- `rule: ReplaceRule | object`
- `text: string`
- 返回替换后的文本

## 图书工具

### `book_save(book)`

- `book: Book | object`

### `book_delete(book)`

- `book: Book | object`

### `bookshelf_list()`

- 返回书架图书列表

### `book_refresh_toc(url)`

- `url: string`
- 强制刷新目录

### `book_get_chapters(url)`

- `url: string`
- 获取目录

### `book_get_content(url, index)`

- `url: string`
- `index: int`
- 获取指定章节正文

### `book_save_progress(progress)`

- `progress: BookProgress | object`

### `book_add_local(file_path, file_name=None)`

- `file_path: string`
- `file_name?: string`
- 上传本地文件到 Legado

## 图片与配置工具

### `web_read_config_get()`

- 获取当前 Web 阅读配置

### `web_read_config_save(config_json)`

- `config_json: any | null`
- 保存 Web 阅读配置

### `book_get_cover(path)`

- `path: string`
- 返回封面图片的临时文件信息

### `book_get_image(book_url, path, width=640)`

- `book_url: string`
- `path: string`
- `width: int = 640`
- 返回正文图片的临时文件信息

## 调试与搜索工具

这些工具用于书源和 RSS 源的调试，以及跨源图书搜索。接口会自动处理 WebSocket 连接、解析并聚合最终结果。

### `book_source_debug(tag, key, mode="auto", timeout_seconds=30.0)`

- `tag: string` - 书源 URL
- `key: string` - 调试关键字或 URL
- `mode: string` - 调试模式 (auto, search, detail, explore, toc, content)
- `timeout_seconds: float` - 最大等待时间
- **返回**：归一化后的 `logs` 列表

### `book_search(key, timeout_seconds=30.0)`

- `key: string` - 搜索书名或作者
- `timeout_seconds: float` - 最大等待时间
- **返回**：归一化后的 `books` 列表

### `rss_source_debug(tag, timeout_seconds=30.0)`

- `tag: string` - RSS 源 URL
- **返回**：归一化后的 `logs` 列表

## Resource 列表

### `legado://api/http`

- 返回 HTTP 接口概要与附带说明

### `legado://api/websocket`

- 返回 WebSocket 接口概要与附带说明

### `legado://schema/book-source`

- 返回 `BookSource` 的 JSON Schema

### `legado://schema/rss-source`

- 返回 `RssSource` 的 JSON Schema

### `legado://session/{session_id}`

- 返回指定调试或搜索会话的最新快照
