# 测试报告：超级小王记忆系统升级

日期：2026-05-22

## 本地测试

| 命令 | 结果 |
| --- | --- |
| `./.venv/bin/python -m pip install -r requirements.txt` | Pass；`psycopg[binary]` 调整为 `3.3.4` 以兼容当前 Python 3.14 环境 |
| `./.venv/bin/python -m py_compile app/agent.py app/__init__.py app/owner_identity.py app/memory_guard.py app/memory_store.py app/memory_service.py app/search_projection.py scripts/import_agent_memory_legacy.py scripts/import_article_memories.py scripts/rebuild_meilisearch_index.py scripts/run_memory_harness.py scripts/build_agent_memory.py` | Pass |
| `./.venv/bin/python -m pytest tests/test_owner_identity.py tests/test_memory_guard.py tests/test_search_projection.py` | 8 passed |
| `./.venv/bin/python scripts/run_memory_harness.py` | Pass |

## 本地 HTTP 回归

本地服务：

```bash
./.venv/bin/flask --app app run --host 127.0.0.1 --port 5001
```

| 路径 | 结果 |
| --- | --- |
| `GET /admin/api/agent/memory/status` | 200，返回 `legacy_json` 和 `store.enabled=false` |
| `GET /admin/api/agent/memory/search?q=PostgreSQL` | 200，返回 JSON fallback 结果 |
| `GET /admin/agent/memory` 未登录 | 302，跳转登录，符合权限预期 |

## Harness 检查

通过项：

- H32 Owner alias。
- H33 反投毒隔离。
- H34 boundary 分类。
- H35 Meilisearch projection 使用可回查 `target_id`。

## 未覆盖

- 未连接真实 PostgreSQL 实例做端到端写入，因为本地环境未配置 `DATABASE_URL`。
- 未连接真实 Meilisearch 实例，因为 projection 是可选层，生产是否启用需先确认服务状态。
