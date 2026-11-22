# 贡献指南

感谢你为 Legado MCP Server 提交问题或改进。

## 开发环境

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)。克隆仓库后运行：

```bash
uv sync --extra dev
```

## 提交改动

- Bug 报告请包含复现步骤、预期行为和实际结果；提交日志前移除访问令牌、Cookie、私人书源地址和其他敏感信息。
- 新增或修改 MCP 工具时，同步更新 `docs/mcp-tool-reference.md` 和相关 `skills/` 文档。
- 修改打包资源时，确认资源可以从已安装的 Python 包读取，不依赖仓库外的绝对路径。
- 保持改动聚焦；避免提交构建产物、虚拟环境、缓存或个人配置。

## 本地检查

提交 Pull Request 前运行：

```bash
uv run pytest
uv run ruff check .
```

Pull Request 请说明问题背景、实现方式和验证结果。行为变化应附上可复现的测试或步骤。
