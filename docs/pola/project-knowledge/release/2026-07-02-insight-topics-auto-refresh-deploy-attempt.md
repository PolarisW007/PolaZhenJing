# Release Attempt: 洞察选题自动刷新与质量聚焦

## 状态

Blocked：代码已提交并推送到 GitHub main，但本次未能进入云服务器执行部署。

## 待发布版本

- 本地 HEAD：`5e1db04d3a8786901100991deb46830f545c252e`
- GitHub `origin/main`：`5e1db04d3a8786901100991deb46830f545c252e`
- 提交标题：`fix: auto refresh insight topics`

## 发布面

- Flask 后端：`app/insight_topics.py`, `app/admin_workbench.py`
- 管理后台模板：`app/templates/insight_topics.html`
- 测试和工程记录：`tests/test_admin_workbench_insight_topics.py`, `docs/pola/project-knowledge/...`
- 生产目录：`/PolaZhenjing`
- 生产服务：`polazj.service`

## 发布前验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`8 passed`。
- `validate_function_test_cases.py`：PASS。
- 真实线上信号 smoke：近 10 天可采集 127 条信号，生成 24 个候选选题。

## 本次连接证据

- 当前 Codex 出口 IP：`162.251.62.70`。
- `nc -vz -w 5 42.121.164.11 22`：TCP connected。
- `nc -vz -w 5 42.121.164.11 80`：TCP connected。
- `nc -vz -w 5 42.121.164.11 443`：TCP connected。
- `ssh -o BatchMode=yes -o ConnectTimeout=60 pola-server ...`：`Connection timed out during banner exchange`。
- `curl -I https://aipd.me/PolaZhenjing/admin/login`：SSL connection timeout。
- `nc` 发送 HTTP 明文请求到 80 端口：30 秒无响应体。

## 判断

当前不是代码、密码或 SSH key 阶段的问题。TCP 可以建连，但 22/80/443 均不返回应用层协议数据，优先怀疑：

- 云服务器重启后 `sshd` / nginx / systemd 服务仍未恢复正常；
- 阿里云安全组、服务器防火墙、fail2ban 或白名单对当前出口 IP 做了连接延迟/丢弃；
- 服务器负载或网络链路异常导致 accept 后无法响应。

## 待执行部署步骤

服务器连接恢复后执行：

```bash
ssh pola-server
cd /PolaZhenjing
git fetch origin main
git rev-parse --short HEAD
git rev-parse --short origin/main
git pull --ff-only origin main
.venv/bin/python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py
PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py -q
systemctl restart polazj.service
systemctl is-active polazj.service
journalctl -u polazj.service -n 50 --no-pager
```

## 发布后验证

```bash
curl -I https://aipd.me/PolaZhenjing/admin/login
curl -I https://aipd.me/PolaZhenjing/admin/insights/topics
curl -I https://aipd.me/PolaZhenjing/admin/upload
cd /PolaZhenjing && .venv/bin/python3 - <<'PY'
from app.insight_topics import collect_topic_signals, signals_to_topics
signals, counts, errors = collect_topic_signals(10)
topics = signals_to_topics(signals)
print(len(signals), counts, errors[:3], len(topics))
PY
```

## 回滚方案

如部署后异常：

```bash
cd /PolaZhenjing
git reset --hard <previous_known_good_commit>
systemctl restart polazj.service
systemctl is-active polazj.service
```

本次不涉及数据库 schema、secret 或运行时数据迁移。
