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
