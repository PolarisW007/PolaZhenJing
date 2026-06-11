# 需求：MiniMax M3 默认模型升级

## 用户原始需求

用户要求测试 MiniMax M3，并将 Pola 项目中 MiniMax M2.5、M2.7 的文字生成能力升级到 M3。

## 目标

- 将 PolaZhenJing 后台 Agent 与上传处理中的 MiniMax 默认文字模型升级为 `MiniMax-M3`。
- 保持现有环境变量覆盖能力。
- 不影响 SkillHub、登录、上传和已有内容生成流程。

## 边界

- 只调整默认模型名。
- 不改 API key、endpoint、数据库和路由。

## 验收标准

- `POLA_AGENT_MODEL` 未配置时后台 Agent 使用 `MiniMax-M3`。
- 上传处理默认使用 `MiniMax-M3`。
- Python 语法检查通过。
