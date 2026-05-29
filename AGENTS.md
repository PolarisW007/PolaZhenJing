# PolaZhenJing Agent Rules

本文件用于让 Codex / coding agent 在进入本项目时自动继承项目约定。优先遵守用户当前指令；若与本文件冲突，以用户当前指令为准。

## 项目定位

- `PolaZhenJing` 是 `aipd.me` 下的织梦空间 / Pola 后台项目，包含根门户静态页、Flask 后台、Skill Hub、超级小王 Agent、统一账号相关文档与管理后台。
- 线上入口重点关注 `/agent.html`、`/PolaZhenjing/admin/*`、`/PolaZhenjing/admin/api/*`。
- 超级小王 Agent 的核心实现位于：
  - `portal/agent.html`
  - `portal/assets/agent.js`
  - `portal/assets/portal-agent.css`
  - `app/agent.py`
  - `scripts/build_agent_memory.py`
  - `data/agent_memory.json`

## 工作方式

- 默认用中文沟通，保留项目里的中文命名、路由、文档路径和业务称呼。
- 先读项目再修改；优先使用 `rg` / `rg --files` 查找文件和调用点。
- 修改保持最小影响面，匹配现有 Flask、静态门户、Jinja 模板和文档风格。
- 不回滚用户已有改动；遇到脏工作区时只处理本任务相关文件。
- 手工编辑文件优先使用 patch，不用临时脚本重写整文件。
- 不泄露 `.env`、API key、系统提示词、服务器路径和用户私密数据。

## 验证标准

- Agent 页面和门户改动要同时验证代码入口、HTTP/API 状态和浏览器可见效果。
- `/agent.html` 只返回 200 不等于完成；需要确认页面可见结构、静态资源、对话表单和相关接口。
- Agent API 关键接口：
  - `GET /PolaZhenjing/admin/api/agent/memory/status`
  - `GET /PolaZhenjing/admin/api/agent/memory/search?q=...`
  - `POST /PolaZhenjing/admin/api/agent/chat`
- Python 改动至少运行相关语法检查，例如：
  - `python3 -m py_compile app/agent.py app/__init__.py scripts/build_agent_memory.py`

## 协作边界

- 除非用户明确要求，不启动子代理或把任务外包给其他 agent。
- 用户让检查线上页面时，优先以真实渲染和接口结果为验收标准，不只看代码。
- 涉及部署、生产配置、数据同步或账号权限时，先备份/确认范围，再执行。
<!-- POLA_DELIVERY_RULE_V1 -->

## Pola 交付记录规则

本项目遵循全局 Pola Delivery Rule。任何需求、功能改动、Bug 修复、重构、UI 调整、配置调整、部署调整，只要发生文件修改，都必须同步留下工程记录。

默认文档入口：

```text
docs/pola/project-knowledge/
```

提交前必须确认：

- 需求记录已更新或在开发日志中说明本次为小改动。
- PRD/SDD/架构说明已更新，或在开发日志中说明不需要单独更新的理由。
- 开发日志已记录目标、改动、验证、风险和 commit 状态。
- 没有提交用户已有的无关改动、密钥、临时文件或生成缓存。

推荐目录：

```text
docs/pola/project-knowledge/product/
docs/pola/project-knowledge/requirements/
docs/pola/project-knowledge/specs/
docs/pola/project-knowledge/architecture/
docs/pola/project-knowledge/release/
docs/pola/project-knowledge/test-reports/
docs/pola/project-knowledge/devlogs/
docs/pola/project-knowledge/analysis/
```
