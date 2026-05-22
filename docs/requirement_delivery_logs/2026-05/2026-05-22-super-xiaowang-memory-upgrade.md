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

## 决策记录

- PostgreSQL 是正式记忆事实源。
- pgvector/Meilisearch 只作为索引和投影，不作为事实源。
- 未配置生产 PostgreSQL 时，线上继续使用 JSON fallback，避免影响现有 Agent。
- 写入开关默认关闭，需要显式启用。

## 验证摘要

- `py_compile` Pass。
- `pytest` 8 passed。
- `scripts/run_memory_harness.py` Pass。
- 本地 `/memory/status` 和 `/memory/search` HTTP 200。

## 后续

- 生产确认 `DATABASE_URL` 后执行 migration。
- 导入 `data/agent_memory.json` 和 `_posts/*.md`。
- 启用 `POLA_MEMORY_WRITE_ENABLED` 后再开放 Owner 确认式写入。
