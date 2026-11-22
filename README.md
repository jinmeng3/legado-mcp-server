# Legado MCP Server

将 Legado 阅读器的 Web HTTP/WebSocket 接口和书源开发辅助能力接入 MCP 客户端。项目由社区维护，非 Legado 官方项目。

## 功能

- 管理书源、RSS 源、替换规则、书架、阅读进度和 Web 阅读配置。
- 调试 Legado 书源、搜索图书，并查看 WebSocket 调试日志。
- 搜索书源知识库，读取 CSS 规则、模板和真实书源案例。
- 获取网站 HTML，分析搜索页、详情页、目录页和正文页。
- 校验书源 JSON、解析规则、运行本地调试并生成修复建议。

MCP 工具的完整参数见 [MCP 工具说明](./mcp-tool-reference.md)；接口背景见 [Legado Web 接口文档](./legado-web-api.md)。

## 环境要求

- Python 3.11 或更高版本。
- 已开启 Web 服务的 Legado 阅读器；使用 HTTP/WebSocket API 工具时需要连接它。
- 推荐使用 [uv](https://docs.astral.sh/uv/) 安装和管理环境。

## 安装

从源码安装：

```bash
git clone https://github.com/jinmeng3/legado-mcp-server.git
cd legado-mcp-server
uv tool install .
```

也可以直接安装远程仓库：

```bash
uv tool install git+https://github.com/jinmeng3/legado-mcp-server.git
```

## 配置

Legado 默认 HTTP 地址为 `http://127.0.0.1:1122`。可通过命令行参数或环境变量配置：

| 参数 | 环境变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--legado-base-url` | `LEGADO_BASE_URL` | `http://127.0.0.1:1122` | Legado HTTP 地址 |
| `--legado-ws-url` | `LEGADO_WS_URL` | 按 HTTP 端口推导 | WebSocket 地址 |
| `--transport` | — | `stdio` | `stdio` 或 `streamable-http` |
| `--host` | — | `127.0.0.1` | HTTP transport 监听地址 |
| `--port` | — | `8000` | HTTP transport 监听端口 |
| — | `LEGADO_HTTP_TIMEOUT` | `60` | HTTP 请求超时秒数 |
| — | `LEGADO_SESSION_BUFFER_SIZE` | `1000` | WebSocket 会话缓冲区大小 |

启动参数也可以通过 `legado-mcp-server --help` 查看。

### Codex 配置示例

安装后在 Codex 配置中添加：

```toml
[mcp_servers.legado]
command = "legado-mcp-server"
args = ["--legado-base-url", "http://127.0.0.1:1122"]
```

### Claude Desktop 配置示例

```json
{
  "mcpServers": {
    "legado": {
      "command": "legado-mcp-server",
      "args": ["--legado-base-url", "http://127.0.0.1:1122"]
    }
  }
}
```

其他 MCP 客户端也可使用同一命令和参数。

## Skills

仓库的 [`skills/`](./skills/) 目录提供三份工作流程说明：

- `legado-mcp-knowledge`：查询书源知识、规则、模板和案例。
- `legado-mcp-site-analysis`：依据真实网页结构推导书源规则。
- `legado-mcp-debugging`：验证、调试和修复书源。

知识文件和调试引擎随 Python 包分发，无需额外下载资源压缩包。

## 开发

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

新增或修改 MCP 工具时，请同步更新 `mcp-tool-reference.md`，并为可复现的用户行为补充测试。

## 注意事项

- 网站分析、书源调试和自动修复可能会向书源中配置的网址发起网络请求。仅使用可信的书源和目标地址。
- Python 调试引擎是 Legado 行为的近似实现。复杂 CSS、JavaScript、正则和编码问题应以 Legado 官方 Kotlin 源码及阅读器实际运行结果为准。
- 自动修复结果需要人工检查，并重新验证；本地模拟成功不代表已在阅读器中验证。

## 许可证

本项目自有代码使用 MIT 许可证，见 [LICENSE](./LICENSE)。随包引入的上游引擎保留其许可证，见 [第三方声明](./THIRD_PARTY_NOTICES.md) 和 `legado_mcp_server/skill_engine/LICENSE`。

## 参与项目

欢迎提交 Issue 和 Pull Request。开发环境、检查命令和贡献流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)；安全问题请阅读 [SECURITY.md](./SECURITY.md)。
