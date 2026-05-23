# 悟空分身 Agent 测试报告

## 验证项

- `scripts/build_agent_memory.py` 成功读取 Obsidian vault `PolaMemory`。
- 生成 `data/agent_memory.json`：606 篇 notes，4386 个 chunks，约 409 万字符。
- `python3 -m py_compile app/agent.py app/__init__.py scripts/build_agent_memory.py` 通过。
- 线上 `/agent.html` 返回 200。
- 线上 `/assets/agent-avatar.png` 返回 200，图片为 320 x 320 PNG。
- 线上 `/PolaZhenjing/admin/api/agent/memory/status` 返回记忆统计。
- 线上 `/PolaZhenjing/admin/api/agent/memory/search?q=企业级 Skill 平台` 返回相关记忆。
- 线上 `/PolaZhenjing/admin/api/agent/chat` 已完成真实模型调用，返回 `MiniMax-M2.7` 回答和记忆来源。

## 发现与处理

- 初次访问 `/agent.html` 404，原因是 Nginx 只显式放行 `/` 和 `/about.html`。已新增 `/agent.html` 与 `/agent` location 并 reload。
- 初次模型调用返回 `invalid chat setting`，原因是 MiniMax 不接受多条 system 消息。已合并系统提示与记忆上下文为一条 system message。
- Computer Use 浏览器权限未完成授权，未做截图级自动化验证；已通过 HTTP、静态资源、API 和真实模型链路完成回归。
