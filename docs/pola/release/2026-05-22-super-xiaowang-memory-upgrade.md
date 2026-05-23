# 发布清单：超级小王记忆系统升级

日期：2026-05-22

## 发布范围

- Flask Agent API 和记忆服务模块。
- 管理后台记忆工作台。
- PostgreSQL migration 与导入脚本。
- Harness 与测试。
- 文档产物。

## 部署步骤

```bash
cd /PolaZhenjing
cp data/wiki.db data/wiki.db.bak.super-xiaowang-$(date +%Y%m%d%H%M%S)
git pull --ff-only
./.venv/bin/python -m pip install -r requirements.txt

# 如果已配置 PostgreSQL：
export POLA_MEMORY_DB_ENABLED=true
export POLA_MEMORY_WRITE_ENABLED=true
./.venv/bin/python - <<'PY'
from app.memory_service import init_memory_store_if_enabled
print(init_memory_store_if_enabled())
PY

systemctl restart polazj.service
systemctl is-active polazj.service
curl -k -L https://aipd.me/PolaZhenjing/admin/api/agent/memory/status
curl -k -L 'https://aipd.me/PolaZhenjing/admin/api/agent/memory/search?q=Agent'
```

## 安全部署策略

- PostgreSQL 使用服务器本机 socket DSN：`postgresql:///polazj_memory`，未引入明文数据库密码。
- `data/agent_memory.json` 继续保留为 fallback，PostgreSQL 是正式记忆账本。
- 旧记忆以 candidate 状态导入，避免一次性污染 active/pinned 人格记忆。
- Meilisearch 服务当前未启用，搜索投影脚本保留，后续可重建。

## 回滚

```bash
cd /PolaZhenjing
git revert <commit>
systemctl restart polazj.service
curl -k -L https://aipd.me/PolaZhenjing/admin/api/agent/memory/status
```

紧急降级：

```bash
unset POLA_MEMORY_DB_ENABLED
unset POLA_MEMORY_WRITE_ENABLED
systemctl restart polazj.service
```

## 发布后验收

- `polazj.service` active。
- `/memory/status` 返回 200。
- `/memory/search` 返回 200。
- `/release/status` 返回 200，并能展示当前运行 commit 与最近更新摘要。
- `/agent.html` 页面可加载并正常调用 chat。
- 未登录 `/admin/agent/memory` 进入登录页。

## 实际发布记录

- 本地提交：`73d46f9 feat: 升级超级小王记忆系统`。
- 本地提交：`586edca docs: 记录超级小王部署验证`。
- GitHub push 因远端 main 有更新被拒绝；为避免在脏工作区 rebase 影响用户未提交内容，本次采用 rsync 精确同步发布。
- 远端备份目录：`/opt/backups/polazj-super-xiaowang-20260522232806`。
- 远端依赖：通过清华 PyPI 镜像安装 `psycopg[binary]==3.3.4` 和 `pytest==8.3.4`。
- 远端 PostgreSQL：
  - `polazj_memory` 数据库已创建。
  - `/PolaZhenjing/.env` 已启用 `POLA_MEMORY_DB_ENABLED=true`、`POLA_MEMORY_WRITE_ENABLED=true`、`POLA_MEMORY_FALLBACK_JSON=true`。
  - 旧记忆导入 `4387` 条 candidate memory。
  - 文章导入 `33` 条 article memory。
- 远端补丁：
  - `app/memory_store.py` 增加 PostgreSQL 文本/JSONB NUL 字节清洗。
  - `tests/test_memory_store.py` 覆盖历史脏数据导入回归。
- 远端服务：`polazj.service` 已重启并保持 active。
- 线上验证：
  - `https://aipd.me/PolaZhenjing/admin/api/agent/memory/status` -> 200，`backend=postgres`、`enabled=true`。
  - `https://aipd.me/PolaZhenjing/admin/api/agent/memory/search?q=Agent` -> 200。
  - `https://aipd.me/PolaZhenjing/admin/agent/memory` 未登录 -> 302 到登录页。
  - `https://aipd.me/agent.html` -> 200。
  - `POST /PolaZhenjing/admin/api/agent/chat` -> 200，`ok=true`。

## 2026-05-23 追加发布项：更新感知

- 新增 `app/release_awareness.py`。
- 新增 `GET /PolaZhenjing/admin/api/agent/release/status`。
- Chat prompt 注入运行版本自我感知上下文。
- 新增 Harness 项 `H36-release-awareness`。
- 回滚方式：`git revert <release-awareness-commit>` 后重启 `polazj.service`。
- 实际发布提交：`884c2cf feat: 增加超级小王更新感知`。
- 线上验证：
  - `/admin/api/agent/release/status` -> 200，`commit=884c2cf`。
  - `/admin/api/agent/chat` 询问“你刚刚被更新了吗” -> 200，小王能说明自己新增了更新感知能力。
