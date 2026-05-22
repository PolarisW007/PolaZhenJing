# 需求分析：超级小王记忆系统升级

日期：2026-05-22

## 目标

按 `docs/pola/agent-memory-persona/PRD.md` 和 `SDD.md`，把现有 `/agent.html` 的 JSON 关键词记忆升级为可持续治理的超级小王记忆系统，并部署到云服务器。

## 范围

- 保持现有 Agent 对话接口兼容。
- 新增 PostgreSQL typed ledger 作为正式记忆主存。
- 保留 `data/agent_memory.json` 作为 fallback。
- 区分 Owner、admin、登录用户、访客。
- Owner 指令走确认式写入。
- 访客建议进入待处理列表，不直接改变人格。
- 后台支持搜索、查看、编辑、采纳、丢弃。
- 补充文章和旧 JSON 导入脚本。
- 补充 Meilisearch search projection 的可重建脚本骨架。
- 补充 Harness、单元测试、部署与回滚记录。

## 非目标

- 不在本轮强制安装生产 PostgreSQL 或 Meilisearch 服务。
- 不把外部向量库作为事实源。
- 不让模型自动改写核心人格并直接发布。

## 验收标准

| ID | 验收项 |
| --- | --- |
| A1 | `/admin/api/agent/memory/status` 在未配置 PostgreSQL 时仍返回 JSON fallback 统计。 |
| A2 | `/admin/api/agent/memory/search` 在未配置 PostgreSQL 时仍可检索旧记忆。 |
| A3 | Owner alias 覆盖 `wsyxjer@gmail.com`、`wsyxjer@qq.com`、`18667107187`。 |
| A4 | 非 Owner 投毒/越权建议不会进入 active memory。 |
| A5 | Owner 可通过确认 API 写入记忆。 |
| A6 | 访客建议进入 `visitor_suggestions`，Owner 可采纳或丢弃。 |
| A7 | 后台 `/admin/agent/memory` 可登录访问，未登录必须跳转登录。 |
| A8 | PostgreSQL migration、导入脚本、Meilisearch rebuild 脚本可语法检查。 |
| A9 | 本地 pytest、Harness、HTTP smoke 全部通过。 |
| A10 | 云服务器部署后线上接口健康，且可回滚到旧 JSON 检索。 |

## 风险

- 当前工作区存在大量历史未提交文件，提交和部署必须只选择超级小王相关文件。
- 生产数据库服务状态未知；若未安装 PostgreSQL，本轮只部署代码和 fallback，不强行改生产基础设施。
- Meilisearch 是可选 projection，不得影响主对话链路。
