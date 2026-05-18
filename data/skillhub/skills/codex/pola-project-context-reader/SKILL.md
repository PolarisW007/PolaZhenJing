---
name: pola-project-context-reader
description: Pola 项目上下文读取 skill。用于在开发前自动阅读项目目录、README、配置文件、包管理器、测试脚本、部署脚本、现有规范和 git 状态，形成可供需求分析、架构设计、编码和测试使用的项目画像。触发词包括读取项目上下文、项目画像、分析项目结构、识别技术栈、找测试命令、找部署方式、开发前扫项目。
---

# Pola Project Context Reader

## 目标

在任何需求开发前，先读项目，而不是凭经验猜。输出一份简短但可执行的项目画像，供后续需求、架构、编码、测试和部署阶段复用。

## 读取范围

按优先级读取，不要一次性把大文件全部塞进上下文：

1. 顶层清单：`rg --files`、`find . -maxdepth 2`。
2. 项目说明：`README*`、`AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`ARCHITECTURE.md`、`docs/`。
3. 技术栈：`package.json`、`pyproject.toml`、`requirements.txt`、`go.mod`、`Cargo.toml`、`pom.xml`、`build.gradle`。
4. 工程命令：`Makefile`、`Taskfile.yml`、`justfile`、`.github/workflows/`、`scripts/`。
5. 部署：`Dockerfile`、`docker-compose.yml`、`deploy/`、`helm/`、`vercel.json`、`netlify.toml`、`render.yaml`、`fly.toml`。
6. 测试：`tests/`、`spec/`、`e2e/`、`playwright.config.*`、`pytest.ini`、`vitest.config.*`、`jest.config.*`。
7. 质量：`.eslintrc*`、`eslint.config.*`、`ruff.toml`、`mypy.ini`、`tsconfig.json`、`biome.json`。

跳过目录：`node_modules`、`.git`、`dist`、`build`、`coverage`、`.venv`、`__pycache__`、大型二进制和生成产物。

## 默认流程

1. 列出顶层目录和关键文件。
2. 读取 README、AGENTS、CLAUDE、package、pyproject、go.mod、Cargo.toml、Dockerfile、compose、CI 配置和部署脚本。
3. 识别技术栈、包管理器、启动命令、测试命令、lint/typecheck 命令、构建命令。
4. 读取项目已有规范、开发日志、架构文档和 release 文档。
5. 检查 git 状态；如果不是 git 仓库，明确说明。
6. 输出项目画像，不修改文件。

## 推荐脚本

- `scripts/detect_project.sh`：快速识别项目技术栈和候选命令。
- `scripts/collect_context.sh`：输出关键文件清单和摘要入口。

## 命令发现规则

- Node 项目优先读取 `package.json.scripts`，不要猜 `npm run dev` 一定存在。
- Python 项目优先看 `pyproject.toml`、`pytest.ini`、`Makefile`、`scripts/`。
- Go 项目默认候选 `go test ./...`，但仍要读取 README 确认。
- Rust 项目默认候选 `cargo test`、`cargo clippy`，有 workspace 时注意成员。
- Docker 项目记录镜像构建、compose 服务名和端口。
- 有 CI 时把 CI 命令作为权威参考。

## 项目画像字段

- **仓库状态**：是否 git 仓库、当前分支、脏文件、最近提交。
- **产品形态**：前端 app、后端 API、CLI、库、移动端、数据任务、skill 仓库等。
- **技术栈**：语言、框架、数据库、缓存、队列、云服务。
- **入口点**：主程序、路由、页面、命令行入口、后台任务入口。
- **测试面**：单测、集成、E2E、快照、lint、类型检查。
- **部署面**：静态站、容器、服务器、函数、应用平台、手工部署。
- **文档面**：需求、架构、开发日志、release、ADR。
- **风险点**：密钥、生产配置、迁移、权限、外部 API、计费。

## 输出格式

```markdown
**项目画像**
- 技术栈：
- 包管理器：
- 启动命令：
- 测试命令：
- Lint/类型检查：
- 构建命令：
- 部署方式：
- 关键目录：
- 规范文档：
- git 状态：
- 风险点：

**后续建议**
- 需求分析应重点关注：
- 架构设计应重点关注：
- 测试应优先跑：
```

## 注意事项

- 优先使用 `rg --files` 和项目脚本。
- 不读取或输出密钥值。
- 不把缺失命令编造成事实，只标记为“未发现”。
- 如果项目是多语言或 monorepo，按子项目分别列画像。
- 如果文件很多，先给索引和判断依据，再按后续阶段需要继续读取。
