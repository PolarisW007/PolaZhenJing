---
name: pola-deploy-release-gate
description: Pola 发布与部署门禁 skill。用于发布前检查、生成发布清单、确认部署面、执行或指导部署、规划回滚、发布后健康检查和回归验证。触发词包括部署、发布、release、上线、发布清单、回滚方案、生产验证、部署后回归、发版门禁。
---

# Pola Deploy Release Gate

## 目标

确保发布前后代码、文档、需求、测试、部署面、回滚点和验证证据一致。

## 输入

- 需求和验收标准。
- 架构文档。
- review 结论。
- 单测、集成和回归证据。
- commit 范围或 diff。
- 目标环境和部署方式。

如果用户只要求“准备发布”，生成 release runbook，不执行命令。

## 默认流程

1. 读取当前 diff、commit、需求、架构文档和测试证据。
2. 判断发布面：前端、后端、数据库、函数、容器、静态资源、配置、第三方服务。
3. 生成或更新发布清单。
4. 写明部署步骤和每一步风险。
5. 写明回滚方案。
6. 部署后执行健康检查和最小真实链路回归。

## 发布面判断

| 改动 | 发布面 |
| --- | --- |
| 前端源码、静态资源 | 前端 build/CDN/静态托管 |
| 后端 API、服务逻辑 | 应用服务、容器、进程 reload |
| 数据库 schema | migration、备份、回滚脚本 |
| 环境变量 | secret/config reload、进程重启 |
| 函数代码 | function publish、alias/version |
| 队列/任务 | worker restart、任务兼容性 |
| 依赖版本 | build、lockfile、镜像或虚拟环境 |

## 发布前 checklist

- diff 已 review。
- 测试门禁通过或 blocker 已被接受。
- 集成/回归有核心路径证据。
- 需求、架构、测试产物已更新。
- 目标环境和分支明确。
- 回滚点明确：commit、tag、image、function version、DB backup。
- 涉及配置时 dev/prod key 已核对。
- 涉及数据迁移时已写 rollback 或补偿策略。

## 发布清单模板

```markdown
# Release Manifest: YYYY-MM-DD

## 变更摘要

## 待发布 commit

## 部署面

## 发布前验证

## 发布步骤

| 步骤 | 命令/动作 | 风险 | 是否需确认 |
| --- | --- | --- | --- |

## 发布后验证

## 回滚方案

## 观察项
```

## 高危操作规则

- 生产写操作、重启、迁移、切流、覆盖配置前必须单独确认。
- 不串联执行高危命令。
- 不在没有回滚点时声称可发布。
- 如果只是生成计划，不执行部署命令。
- 如果生产与远端 commit 不一致，不报告发布完成。

## 部署执行规则

- 只读命令可以用于确认状态。
- 写操作前说明“将执行什么、影响什么、如何回滚”。
- 每执行一步，立即记录结果。
- 任一步失败，停止后续高危步骤，进入排查或回滚。
- 部署后必须跑健康检查和核心路径回归。

## 回滚方案要求

至少写清：

- 回滚触发条件。
- 回滚命令或操作入口。
- 回滚后验证命令。
- 数据是否需要补偿。
- 谁需要被通知。

## 输出

```markdown
artifact: release-plan

**发布结论**
- Ready / Not ready / Deployed / Blocked

**发布面**
-

**已验证**
-

**待确认**
-

**回滚**
-
```

## Ready 判定

只有同时满足下面条件才能说 Ready：

- 代码和目标分支明确。
- review 无阻塞问题。
- 核心测试通过。
- 发布步骤和回滚步骤可执行。
- 发布后验证项明确。

## Artifact 字段

```markdown
artifact: release-plan
fields:
  status:
  commits:
  surfaces:
  pre_checks:
  deploy_steps:
  post_checks:
  rollback:
```
