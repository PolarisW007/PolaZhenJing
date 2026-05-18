---
name: pola-test-gate
description: Pola 测试门禁 skill。用于自动发现并运行项目相关的单元测试、类型检查、lint、构建、最小回归测试和质量命令，生成测试证据和 blocker。触发词包括单元测试、跑测试、测试门禁、lint、typecheck、构建验证、最小相关测试、质量检查。
---

# Pola Test Gate

## 目标

用项目真实命令验证代码，而不是只看 diff。输出清楚的测试命令、结果、失败原因和未覆盖风险。

## 输入

- 项目画像中的候选命令。
- 本次改动文件列表。
- 需求验收标准。
- review 发现项。
- 项目已有 CI 配置。

## 默认流程

1. 读取项目画像和 package/pyproject/Makefile/CI。
2. 根据改动范围选择最小相关测试。
3. 先跑快速静态检查，再跑单测和构建。
4. 如果失败，定位到最小原因并修复可控问题。
5. 无法运行时记录 blocker，例如缺依赖、缺密钥、服务不可用。

## 推荐脚本

- `scripts/run_quality_gates.sh`：根据常见项目文件自动尝试候选命令。

## 常见命令选择

- Node：`npm test`、`npm run lint`、`npm run typecheck`、`npm run build`
- pnpm：`pnpm test`、`pnpm lint`、`pnpm typecheck`、`pnpm build`
- Python：`pytest`、`python -m pytest`、`python -m compileall`
- Go：`go test ./...`
- Rust：`cargo test`

## 测试选择规则

- 改文档或 skill：跑 markdown/skill 校验、脚本语法检查。
- 改纯工具脚本：跑脚本 `--help`、语法检查和一个安全样例。
- 改前端组件：跑 lint/typecheck/build，必要时浏览器验证。
- 改后端服务：跑单测、接口相关测试、语法/类型检查。
- 改共享库：跑全量相关单测，必要时跑消费者测试。
- 改配置/部署：跑配置解析、构建或 dry-run，记录需要人工验证项。

## 失败分类

| 类型 | 处理 |
| --- | --- |
| 本次引入失败 | 修复后重跑 |
| 环境缺依赖 | 说明缺什么，能安装则安装，不能则 blocker |
| 外部服务不可用 | 记录服务、命令、错误和替代验证 |
| 历史失败 | 给出证据说明与本次无关，避免宣称全量通过 |
| 测试不稳定 | 重跑一次确认，记录 flake 迹象 |

## 证据记录

每条命令记录：

- 工作目录。
- 命令。
- 退出码。
- 关键输出摘要。
- 如果失败，保留首个有用错误，不粘贴海量日志。

## 输出

```markdown
artifact: test-evidence

**测试结论**
- Pass / Fail / Blocked

**已运行**
- 命令：
- 结果：

**未覆盖**
- 项：
- 原因：

**下一步**
-
```

## 进入下一阶段条件

- 核心逻辑至少有一个自动化验证或明确人工验证计划。
- 所有本次引入的测试失败已修复。
- 未运行项有具体原因，不用“未测试”一句带过。

## Artifact 字段

```markdown
artifact: test-evidence
fields:
  status:
  commands:
  results:
  failures:
  skipped:
  coverage_notes:
```
