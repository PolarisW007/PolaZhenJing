# 悟空分身 Agent 对话页需求

## 目标

在 AIPD 根站新增独立页面 `/agent.html`，把首页 AI 分身从展示型区块升级为可对话的在线 Agent。

## 用户路径

1. 用户从首页导航或 AI 分身区块进入 `/agent.html`。
2. 页面展示小悟空头像、记忆状态和对话面板。
3. 用户输入问题。
4. 后端检索 Obsidian 长期记忆，拼入大模型上下文。
5. Agent 返回中文回答，并展示本次引用的记忆来源。

## 功能范围

- 独立黑金风格聊天页。
- 从用户提供图片裁切小悟空头像。
- 本地脚本通过 Obsidian CLI/vault 生成长期记忆索引。
- Flask API 提供记忆状态、记忆检索和聊天接口。
- 前端支持本地会话历史、新会话、加载态、错误态。

## 验收标准

- `/agent.html` 可访问并在桌面/移动端可用。
- `/PolaZhenjing/admin/api/agent/memory/status` 返回记忆统计。
- `/PolaZhenjing/admin/api/agent/chat` 可调用大模型并返回回答。
- 回答包含与问题相关的记忆检索证据。
- 没有 API key 或模型异常时，前端显示明确错误。
