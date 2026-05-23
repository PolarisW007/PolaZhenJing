# 悟空分身 Agent 对话页架构

## 现状

- 根站 `/` 是 `/var/www/html` 下的静态 Portal。
- PolaZhenjing Flask 服务部署在 `/PolaZhenjing`，已有登录、文章、Skill API。
- 线上服务器无法直接读取用户 Mac 本地 Obsidian vault。

## 方案

### 前端

- 新增 `portal/agent.html`。
- 新增 `portal/assets/portal-agent.css` 和 `portal/assets/agent.js`。
- 复用根站导航、登录态展示和黑金视觉系统。
- 会话历史存在浏览器 `localStorage`，不写服务器数据库。

### 后端

- 新增 `app/agent.py` Blueprint。
- API：
  - `GET /admin/api/agent/memory/status`
  - `GET /admin/api/agent/memory/search?q=...`
  - `POST /admin/api/agent/chat`
- 使用 MiniMax chat completions 作为大模型桥接。

### 记忆

- 新增 `scripts/build_agent_memory.py`。
- 本地读取 Obsidian CLI `files vault=PolaMemory` 的文件列表，再读取 vault markdown/canvas 文本，生成 `data/agent_memory.json`。
- 线上只读取同步后的 JSON，不访问本地 vault。
- 检索为轻量关键词召回，返回 top chunks 给大模型。

### 部署

- 静态文件同步到 `/var/www/html`。
- Flask 文件和 `data/agent_memory.json` 同步到 `/PolaZhenjing`。
- 重启 `polazj.service`。

## 风险与后续

- 当前检索是关键词召回，后续可升级为 embedding 向量检索。
- 当前会话存在浏览器本地，后续可做登录用户级会话存档。
- Obsidian 记忆更新需要重新运行脚本并同步。
