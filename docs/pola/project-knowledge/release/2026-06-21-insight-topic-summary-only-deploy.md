# 发布记录：洞察选题摘要-only 展示与导入

日期：2026-06-21

## 目标

- `/PolaZhenjing/admin/insights/topics` 选题卡片正文区只展示文章摘要。
- 移除卡片正文区的来源、证据、评分、标签和底稿字数等非编辑信息。
- “一键导入上传”进入 `/admin/upload` 后，Markdown 正文只预填摘要内容，不写入来源、证据、状态、评分或底稿章节。

## 发布范围

- `app/insight_topics.py`
- `app/templates/insight_topics.html`
- `tests/test_admin_workbench_insight_topics.py`
- `docs/pola/arch-reference.md`
- `docs/pola/project-knowledge/requirements/2026-06-20-daily-insight-topic-drafts.md`
- `docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-drafts-prd.md`
- `docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-drafts-spec.md`
- `docs/pola/project-knowledge/architecture/2026-06-20-daily-insight-topic-drafts-sdd.md`
- `docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json`
- `docs/pola/project-knowledge/delivery/daily-insight-topic-drafts/function_test_cases.json`
- `docs/pola/project-knowledge/devlogs/2026-06-20-daily-insight-topic-drafts.md`

## 不发布范围

- 不覆盖 `_posts/`。
- 不覆盖 `.env`。
- 不覆盖上传图片、数据库、用户会话或其他运行时缓存。
- 不修改 Nginx、systemd 配置或云资源。

## 风险等级

- P2：影响后台选题列表和上传预填主流程。
- 护栏：
  - 发布前备份应用文件和 `data/insight_topics.json`。
  - 不改变选题 JSON 字段结构，不删除已有底稿数据。
  - 导入动作仍只更新选题状态，正文内容变为摘要-only。

## 本机验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q`：`12 passed in 0.69s`。
- Function test cases harness：
  - 每日选题底稿：通过，覆盖 10 个验收点、4 个 feature、6 个 case。
  - Admin 工作台与洞察选题：通过，覆盖 6 个验收点、6 个 feature、12 个 case。
- Flask test-client smoke：
  - 列表页 200，包含摘要。
  - 列表页不包含来源、评分和底稿字数。
  - 导入上传页 200，textarea 与 `topic.summary` 完全一致。
  - textarea 不包含 `## 证据链接`、`来源类型`、`状态：` 或 `## 核心判断`。

## 云端发布

- 服务器：`pola-server`
- 应用目录：`/PolaZhenjing`
- 备份目录：`/opt/backups/polazj-insight-summary-only-20260621232152`
- 发布方式：精确 `rsync -avR` 同步发布范围文件。
- 服务重启：`systemctl restart polazj.service` 成功，`systemctl is-active polazj.service` 为 `active`。

## 云端验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q`：`12 passed in 1.21s`。
- 云端认证态 Flask smoke：
  - 选题页 200，包含当前选题摘要。
  - 选题页不包含来源、评分和底稿字数。
  - 上传页 200。
  - Markdown textarea 与 `topic.summary` 完全一致，长度 211。
  - textarea 不包含 `## 证据链接`、`来源类型`、`状态：`、`选题评分`、`主来源` 或 `## 核心判断`。
- 公网匿名 smoke：
  - `https://aipd.me/PolaZhenjing/admin/insights/topics` 跳转登录页，登录页 200。
- `journalctl -u polazj.service --since "3 minutes ago"`：只看到正常 stop/start 和 gunicorn worker boot，无异常堆栈。

## 回滚

```bash
ssh pola-server
cd /PolaZhenjing
BACKUP_DIR=/opt/backups/polazj-insight-summary-only-20260621232152
tar -xzf "$BACKUP_DIR/app-docs-existing.tgz" -C /PolaZhenjing
cp "$BACKUP_DIR/insight_topics.json" data/insight_topics.json
systemctl restart polazj.service
systemctl is-active polazj.service
```
