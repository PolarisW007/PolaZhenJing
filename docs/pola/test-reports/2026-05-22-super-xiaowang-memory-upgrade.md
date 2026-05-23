# 测试报告：超级小王记忆系统升级

日期：2026-05-22

## 本地测试

| 命令 | 结果 |
| --- | --- |
| `./.venv/bin/python -m pip install -r requirements.txt` | Pass；`psycopg[binary]` 调整为 `3.3.4` 以兼容当前 Python 3.14 环境 |
| `./.venv/bin/python -m py_compile app/agent.py app/__init__.py app/owner_identity.py app/memory_guard.py app/memory_store.py app/memory_service.py app/search_projection.py scripts/import_agent_memory_legacy.py scripts/import_article_memories.py scripts/rebuild_meilisearch_index.py scripts/run_memory_harness.py scripts/build_agent_memory.py` | Pass |
| `./.venv/bin/python -m pytest tests/test_owner_identity.py tests/test_memory_guard.py tests/test_search_projection.py tests/test_memory_store.py` | 9 passed |
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
- H36 release awareness：小王能读取当前运行提交和更新摘要，且不暴露敏感配置。

## 存储层异常数据回归

- 线上导入旧记忆时发现历史文本包含 NUL 字节，PostgreSQL 拒绝写入。
- 已在 `app/memory_store.py` 增加递归清洗，覆盖普通文本、JSONB、tuple/list/dict。
- 新增 `tests/test_memory_store.py`，验证 NUL 字节会在入库前递归移除。

## 未覆盖

- 本地未连接真实 PostgreSQL 实例做端到端写入，因为本地环境未配置 `DATABASE_URL`。
- 未连接真实 Meilisearch 实例，因为 projection 是可选层，生产是否启用需先确认服务状态。

## 线上回归

部署时间：2026-05-22 23:32 Asia/Shanghai

| 路径/命令 | 结果 |
| --- | --- |
| 远端 `./.venv/bin/python -m pytest tests/test_owner_identity.py tests/test_memory_guard.py tests/test_search_projection.py tests/test_memory_store.py` | 9 passed |
| 远端 `scripts/run_memory_harness.py` | Pass |
| 远端 `scripts/import_agent_memory_legacy.py` | Pass，导入 `events=4387`、`memories=4387` |
| 远端 `scripts/import_article_memories.py` | Pass，导入 `articles=33` |
| `systemctl is-active polazj.service` | active |
| `GET https://aipd.me/PolaZhenjing/admin/api/agent/memory/status` | 200，`store.enabled=true`，`backend=postgres` |
| `GET https://aipd.me/PolaZhenjing/admin/api/agent/memory/search?q=Agent` | 200，返回旧记忆结果 |
| `GET https://aipd.me/PolaZhenjing/admin/agent/memory` 未登录 | 302 -> `/admin/login` |
| `GET https://aipd.me/agent.html` | 200 |
| `POST https://aipd.me/PolaZhenjing/admin/api/agent/chat` | 200，`ok=true`，`model=MiniMax-M2.7` |

## 2026-05-23 小能力回归：更新感知

新增能力：

- `app/release_awareness.py` 从服务器当前 git commit、最新发布文档和交付日志生成“运行版本自我感知上下文”。
- `/admin/api/agent/release/status` 返回当前 commit、分支、最近提交标题、提交时间和发布/交付文档引用。
- `/admin/api/agent/chat` 的 system context 注入短版本感知信息；仅在用户询问更新、版本、部署或新能力时使用。

验证项：

| 路径/命令 | 结果 |
| --- | --- |
| `pytest tests/test_release_awareness.py` | 待远端部署后记录 |
| `scripts/run_memory_harness.py` | 新增 H36，待远端部署后记录 |
| `GET /admin/api/agent/release/status` | 待远端部署后记录 |

生产状态：

- 服务器 PostgreSQL 服务 active。
- 已创建本机 socket 连接的 `polazj_memory` 数据库和 `root` role。
- `/PolaZhenjing/.env` 已启用：
  - `DATABASE_URL=postgresql:///polazj_memory`
  - `POLA_MEMORY_DB_ENABLED=true`
  - `POLA_MEMORY_WRITE_ENABLED=true`
  - `POLA_MEMORY_FALLBACK_JSON=true`
- 最新线上状态：
  - `memory_items=4420`
  - `raw_events=4422`
  - `search_index_jobs=8369`
  - `visitor_suggestions=0`
  - `active_memories=0`
  - `candidates=4411`
