# 交付日志：超级小王记忆系统升级

日期：2026-05-22

## 阶段状态

| 阶段 | 状态 | 产物 |
| --- | --- | --- |
| 项目画像 | Done | `docs/pola/arch-reference.md`、A2A 本轮读取记录 |
| 需求分析 | Done | `docs/pola/requirements/2026-05-22-super-xiaowang-memory-upgrade.md` |
| 架构设计 | Done | `docs/pola/architecture/2026-05-22-super-xiaowang-memory-upgrade.md` |
| 编码实现 | Done | `app/memory_*`、`app/owner_identity.py`、`app/search_projection.py`、`app/agent.py` |
| 测试门禁 | Done | `docs/pola/test-reports/2026-05-22-super-xiaowang-memory-upgrade.md` |
| 发布清单 | Done | `docs/pola/release/2026-05-22-super-xiaowang-memory-upgrade.md` |
| 云端部署 | Done | rsync 到 `/PolaZhenjing`，启用 PostgreSQL 记忆账本，重启 `polazj.service` |
| 产品更新日志 | Done | `docs/pola/agent-memory-persona/CHANGELOG.md` |

## 决策记录

- PostgreSQL 是正式记忆事实源。
- pgvector/Meilisearch 只作为索引和投影，不作为事实源。
- 生产 PostgreSQL 已启用，`data/agent_memory.json` 保留为 fallback。
- 写入开关已启用，但旧记忆默认导入为 candidate，需要 Owner 在后台采纳/编辑/置为 active。
- 历史脏数据可能包含 NUL 字节，统一在存储层清洗，避免导入和后台编辑写库失败。

## 验证摘要

- `py_compile` Pass。
- `pytest` 9 passed。
- `scripts/run_memory_harness.py` Pass。
- 本地 `/memory/status` 和 `/memory/search` HTTP 200。
- 线上 `/memory/status`、`/memory/search`、`/agent.html`、`/agent/chat` 回归通过。
- 远端备份目录：`/opt/backups/polazj-super-xiaowang-20260522232806`。
- 远端导入 `4387` 条旧记忆、`33` 篇文章。
- 最新线上 PostgreSQL 状态：`memory_items=4420`、`raw_events=4422`、`candidates=4411`、`visitor_suggestions=0`。

## 后续

- Owner 登录后台 `/PolaZhenjing/admin/agent/memory` 后，优先审核 candidate 记忆并逐步转 active/pinned。
- 如需更好的后台搜索体验，启动 Meilisearch 后执行 `scripts/rebuild_meilisearch_index.py`。
- Phase 2 再启用 pgvector embedding shadow mode，并用 Harness 对比召回质量。

## 2026-05-23 追加：小王更新感知

- 目标：让超级小王知道自己当前运行的版本、最近一次更新摘要和对应交付文档。
- 实现：
  - `app/release_awareness.py` 读取当前 git commit、commit subject、commit time、最新 release doc 和 delivery log。
  - `app/agent.py` 在 chat system context 中注入短版本感知信息。
  - 新增 `GET /admin/api/agent/release/status` 作为运维/验收入口。
  - `scripts/run_memory_harness.py` 新增 `H36-release-awareness`。
- 安全边界：只暴露 commit、分支、提交标题和文档相对路径；不暴露服务器绝对路径、环境变量值、密钥和系统提示词。
- 发布结果：
  - 提交 `884c2cf feat: 增加超级小王更新感知` 已部署到服务器。
  - 提交 `d07fa70 docs: 记录小王更新感知发布验证` 已同步到本地、GitHub 和服务器。
  - 远端 pytest 10 passed。
  - 远端 Harness 新增 `H36-release-awareness` 并通过。
  - 线上 `/admin/api/agent/release/status` 返回 200，可展示当前运行 commit、分支、提交标题和最近交付文档。
  - 线上 chat 已能回答“我刚刚被更新了，并新增更新感知能力”。
- 产品更新日志：`docs/pola/agent-memory-persona/CHANGELOG.md` 已记录 2026-05-22 记忆系统升级、2026-05-23 代码线同步和更新感知发布。
