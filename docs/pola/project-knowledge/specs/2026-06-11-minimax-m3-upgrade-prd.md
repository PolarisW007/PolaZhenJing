# PRD：MiniMax M3 默认模型升级

## 用户流程

- 管理员进入后台 Agent 或触发上传内容处理。
- 系统沿用现有 MiniMax endpoint 和 key。
- 未显式配置模型时，默认使用 `MiniMax-M3`。

## 兼容要求

- `POLA_AGENT_MODEL` 继续可以覆盖默认模型。
- 既有上传、内容缓存、SkillHub 数据不迁移。
- 用户登录与后台权限不变化。

## 异常分支

- MiniMax 调用失败时，沿用现有错误提示和日志。

## 非目标

- 不变更账号、权限、发布链路。
