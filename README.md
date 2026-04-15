# legado-mcp-server

`legado-mcp-server` 是一个把Legado Web API封装成MCP服务的项目，主要是为了方便通过AI编写书源时调试

## 适用场景
- 把 Legado 接入 Codex、Claude Desktop、Cherry Studio 等 MCP 客户端

## 文档

- [Legado Web 接口文档](./legado-web-api.md)
- [MCP 工具说明](./mcp-tool-reference.md)

## 环境要求

- Python 3.11+
- 已开启 Legado Web 服务的设备
- 推荐使用 `uv`

## 快速开始

### 安装

1. 下载源码到本地
2. 在项目根目录下执行：
   ```powershell
   uv tool install .
   ```
   *或者直接从 GitHub 安装：*
   ```powershell
   uv tool install git+https://github.com/joestar817/legado-mcp-server.git
   ```

### 配置

命令行参数：

- `--transport`: `stdio` 或 `streamable-http` (默认为 `stdio`)
- `--host`: `streamable-http` 的监听地址 (默认 `127.0.0.1`)
- `--port`: `streamable-http` 的监听端口 (默认 `8000`)
- `--legado-base-url`: Legado HTTP 地址 (如 `http://192.168.1.10:1122`)
- `--legado-ws-url`: Legado WebSocket 地址，可选 (如果不指定，默认按 HTTP 端口 + 1 推导)

### 环境变量：

- `LEGADO_BASE_URL`
- `LEGADO_WS_URL`
- `LEGADO_HTTP_TIMEOUT`: HTTP 请求超时时间 (默认 60s)
- `LEGADO_SESSION_BUFFER_SIZE`: WebSocket 消息缓冲区大小 (默认 1000)

## MCP 客户端接入示例

### Codex


```toml
[mcp_servers.legado]
command = "legado-mcp-server"
args = ["--legado-base-url", "http://192.168.1.10:1122"]
enabled = true
```

### LM studio

```json
{
  "mcpServers": {
    "legado-mcp-server": {
      "command": "legado-mcp-server",
      "args": [
        "--legado-base-url",
        "http://192.168.1.10:1122"
      ]
    }
  }
}
```



## 工具概览

完整参数和返回结构见 [MCP 工具说明](./mcp-tool-reference.md)。

按类别概览：

- 书源：
  - `book_source_get`
  - `book_source_list`
  - `book_source_save`
  - `book_source_save_many`
  - `book_source_delete_many`
- RSS：
  - `rss_source_get`
  - `rss_source_list`
  - `rss_source_save`
  - `rss_source_save_many`
  - `rss_source_delete_many`
- 替换规则：
  - `replace_rule_list`
  - `replace_rule_save`
  - `replace_rule_delete`
  - `replace_rule_test`
- 图书：
  - `book_save`
  - `book_delete`
  - `bookshelf_list`
  - `book_refresh_toc`
  - `book_get_chapters`
  - `book_get_content`
  - `book_save_progress`
  - `book_add_local`
- 图片与配置：
  - `book_get_cover`
  - `book_get_image`
  - `web_read_config_get`
  - `web_read_config_save`
- 调试与搜索：
  - `book_source_debug`
  - `rss_source_debug`
  - `book_search`

## 许可证
[MIT](./LICENSE)
