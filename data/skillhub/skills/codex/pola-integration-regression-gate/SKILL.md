---
name: pola-integration-regression-gate
description: Pola 集成与回归测试 skill。用于在单测后验证真实链路、API、浏览器 UI、历史记录、下载、计费、日志、部署后回归和原始 bug 复现。触发词包括集成测试、回归测试、真实链路验证、UI 测试、浏览器验证、部署后验证、原始 bug 复现、端到端测试。
---

# Pola Integration Regression Gate

## 目标

验证“用户真的能完成目标”，而不是只验证代码能编译。适用于 API、前端、任务系统、后台流程、部署后检查和 bugfix 回归。

## 输入

- 需求验收标准。
- 测试门禁结果。
- 运行环境和账号信息。
- 原始 bug 复现信息。
- 发布环境或本地服务 URL。

缺少账号、密钥、测试素材或服务时，先尝试使用项目已有测试 fixtures；仍不可用则记录 blocker。

## 默认流程

1. 读取验收标准和测试门禁结果。
2. 选择最小真实链路。
3. 对 bugfix，复现原始失败 case，再验证修复后通过。
4. 对前端，使用浏览器验证关键路径、响应式和 console 错误。
5. 对任务或异步流程，记录任务 ID、状态、结果 URL、日志和历史展示。
6. 对计费或权益，记录预估、实扣、退款或补扣。
7. 对部署后回归，记录环境、版本和健康检查。

## 验证类型

- API 集成：请求、响应、错误码、鉴权。
- UI 集成：页面加载、表单、提交、结果展示、console。
- 数据集成：写入、读取、历史、缓存、幂等。
- 任务集成：提交、轮询、下载、日志、失败处理。
- 发布回归：健康检查、核心路径、日志观察。

## 真实链路设计

为每个核心验收项选择一个最小真实路径：

```markdown
| 验收项 | 入口 | 操作 | 期望结果 | 证据 |
| --- | --- | --- | --- | --- |
| A1 | /settings | 修改配置并保存 | toast 成功，刷新后保留 | screenshot/API |
```

## 前端浏览器验证

- 打开真实 URL 或本地服务。
- 覆盖桌面和移动视口。
- 检查加载态、错误态、空态、成功态。
- 检查 console error 和 network 失败。
- 对表单验证输入边界值。
- 对布局检查文本遮挡、按钮溢出、弹窗位置。

## API 验证

- 覆盖成功请求。
- 覆盖缺参、非法参数、无权限或资源不存在。
- 验证响应 schema 和状态码。
- 验证日志中可追踪 request/task/session。

## Bugfix 回归规则

bugfix 必须记录：

- 原始问题描述。
- 原始复现步骤或最小输入。
- 修复前预期失败点。
- 修复后验证命令或操作。
- 是否补了自动化测试。

不能只跑一个相似 happy path 就说 bugfix 已回归。

## 部署后回归

记录：

- 环境：本地、staging、production。
- 版本：commit、image tag、函数 version、部署时间。
- 健康检查：URL/命令/结果。
- 核心路径：操作和证据。
- 日志观察：错误日志、告警或监控。

## 输出

```markdown
artifact: regression-evidence

**集成回归结论**
- Pass / Fail / Blocked

**真实链路证据**
- 环境：
- 命令或操作：
- ID 或 URL：
- 结果：

**原始 bug 回归**
- case：
- 结果：

**残余风险**
-
```

## 注意事项

- 不把单测通过等同于回归通过。
- 浏览器测试要检查 console 错误和布局遮挡。
- 外部服务不可用时，记录 blocker，不伪造结果。
- 真实链路测试若会产生费用、发消息、写生产数据，先确认或使用测试环境。

## Artifact 字段

```markdown
artifact: regression-evidence
fields:
  status:
  environment:
  paths:
  ids:
  screenshots:
  logs:
  risks:
```
