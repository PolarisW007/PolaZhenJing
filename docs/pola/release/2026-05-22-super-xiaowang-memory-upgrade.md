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

- 如果生产未配置 `DATABASE_URL`，不强制启用 PostgreSQL；先部署代码和 JSON fallback。
- `POLA_MEMORY_WRITE_ENABLED` 默认关闭，避免上线即自动写入。
- 初始化 PostgreSQL schema 需要 Owner/admin 手动触发或运维命令执行。

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
- `/agent.html` 页面可加载并正常调用 chat。
- 未登录 `/admin/agent/memory` 进入登录页。
