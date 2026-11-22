# Legado MCP Server

把 Legado 阅读器的 Web API 接入 MCP 客户端，并提供书源知识查询、网站结构分析和规则调试工具。社区项目，非 Legado 官方产品。

[MCP 工具参考](./docs/mcp-tool-reference.md) · [Legado Web API 文档](./docs/legado-web-api.md) · [贡献指南](./CONTRIBUTING.md)

## 功能

- **阅读器管理**：书源、RSS 源、替换规则、书架、章节、阅读进度和 Web 阅读配置。
- **搜索与调试**：跨源搜书、书源和 RSS 调试、WebSocket 日志。
- **书源开发**：搜索知识库、读取 CSS 规则和模板、查询真实案例；分析搜索页、详情页、目录页和正文页。
- **规则辅助**：验证书源 JSON、解析规则、运行本地调试、分析错误并生成修复建议。

完整工具名称、参数和返回值见 [MCP 工具参考](./docs/mcp-tool-reference.md)。

## 环境要求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- 使用阅读器管理工具时，需要已开启 Web 服务的 Legado 阅读器

## 安装

```bash
uv tool install git+https://github.com/jinmeng3/legado-mcp-server.git
```

或克隆仓库后本地安装：

```bash
git clone https://github.com/jinmeng3/legado-mcp-server.git
cd legado-mcp-server
uv tool install .
```

安装完成后可运行 `legado-mcp-server --help` 查看启动参数。

## 配置

默认连接 `http://127.0.0.1:1122`。配置可通过命令行参数或环境变量提供：

| 命令行参数 | 环境变量 | 默认值 | 用途 |
| --- | --- | --- | --- |
| `--legado-base-url` | `LEGADO_BASE_URL` | `http://127.0.0.1:1122` | Legado HTTP 地址 |
| `--legado-ws-url` | `LEGADO_WS_URL` | HTTP 端口加 1 | Legado WebSocket 地址 |
| `--transport` | — | `stdio` | `stdio` 或 `streamable-http` |
| `--host` | — | `127.0.0.1` | HTTP transport 仅允许绑定回环地址 |
| `--port` | — | `8000` | HTTP transport 监听端口 |
| — | `LEGADO_HTTP_TIMEOUT` | `60` 秒 | HTTP 请求超时 |
| — | `LEGADO_SESSION_BUFFER_SIZE` | `1000` | WebSocket 会话缓冲区大小 |
| — | `LEGADO_ENABLE_UNSAFE_JS` | 未设置 | 显式启用可信书源中的 JavaScript 规则；代码以服务进程权限执行 |

调用 `legado_connection_info()` 可查看当前连接地址和配置提示。

- 若 Legado Web 服务不在运行 MCP 服务的同一台机器上，在 MCP 服务进程设置 `LEGADO_BASE_URL`。
- 局域网设备地址会变化时，建议在路由器中为设备保留 DHCP 地址。
- 修改配置后重启 MCP 服务。

运行期间可让 AI 调用 `legado_connection_configure(http_base_url, websocket_url=None)` 切换地址；新地址仅在当前 MCP 进程生效，重启后恢复启动配置。需要持久使用时，在 MCP 启动配置中设置 `LEGADO_BASE_URL` 和可选的 `LEGADO_WS_URL`。

### Codex

将下面配置加入 Codex 的 MCP 配置：

```toml
[mcp_servers.legado]
command = "legado-mcp-server"
args = ["--legado-base-url", "http://127.0.0.1:1122"]
```

### Claude Desktop

将下面配置加入 Claude Desktop 的 MCP 配置：

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

其他 MCP 客户端也可使用已安装的 `legado-mcp-server` 命令。

## Skills

[`skills/`](./skills/) 中包含可供 AI Agent 使用的工作流程说明：

- `legado-mcp-knowledge`：查书源知识、规则、模板和案例。
- `legado-mcp-site-analysis`：依据目标网站的真实 HTML 推导选择器。
- `legado-mcp-debugging`：验证和调试书源，分析错误并检查修复结果。

知识库、技能参考文档和调试引擎随 Python 包分发，不需要单独下载压缩包。

## 开发

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

贡献方式见 [CONTRIBUTING.md](./CONTRIBUTING.md)。GitHub Actions 会在 push 和 pull request 时运行测试与代码检查。

## 使用说明

- 网站分析、书源调试和自动修复会请求书源中配置的网址。只使用可信的书源和目标地址。
- `streamable-http` 仅绑定回环地址；远程访问请放在带认证的反向代理之后。
- JavaScript 规则默认关闭。仅在信任书源且接受其以当前用户权限执行时设置 `LEGADO_ENABLE_UNSAFE_JS=1`。
- 网站抓取只允许目标主机解析到公网 IP，最多跟随 5 次重定向，并将响应限制为 10 MiB。
- Python 调试引擎是 Legado 行为的近似实现；复杂 CSS、JavaScript、正则和编码行为，以 Legado Kotlin 源码及阅读器实测为准。
- 自动修复返回候选结果，需要检查并重新验证；本地模拟成功不代表已在阅读器中验证。

## 许可证

项目自有代码使用 MIT 许可证，见 [LICENSE](./LICENSE)。随包引入的上游资源保留原许可证，见 [第三方声明](./THIRD_PARTY_NOTICES.md) 和 `legado_mcp_server/skill_engine/LICENSE`。安全问题请阅读 [SECURITY.md](./SECURITY.md)。
