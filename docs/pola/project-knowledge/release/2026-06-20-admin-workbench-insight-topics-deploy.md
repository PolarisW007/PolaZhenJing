# 发布记录：Admin 工作台与洞察选题池上线

日期：2026-06-20

## 发布目标

- 将 PolaZhenjing Admin 工作台入口发布到云服务器。
- 将洞察文章选题池、状态打标、一键导入上传页的能力发布到云服务器。
- 保持既有上传、文章编辑、公开文章页、登录保护和运行时数据不被破坏。

## 发布范围

- 后端：
  - `app/admin_workbench.py`
  - `app/insight_topics.py`
  - `app/__init__.py`
  - `app/uploader.py`
- 模板：
  - `app/templates/admin_workbench.html`
  - `app/templates/insight_topics.html`
  - `app/templates/base.html`
  - `app/templates/upload.html`
- 初始数据：
  - `data/insight_topics.json`
- 测试：
  - `tests/test_admin_workbench_insight_topics.py`
- 文档和 A2A 证据：
  - `docs/pola/project-knowledge/requirements/2026-06-20-admin-workbench-insight-topics.md`
  - `docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-prd.md`
  - `docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-spec.md`
  - `docs/pola/project-knowledge/architecture/2026-06-20-admin-workbench-insight-topics-sdd.md`
  - `docs/pola/project-knowledge/devlogs/2026-06-20-admin-workbench-insight-topics.md`
  - `docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/`

## 不发布范围

- 不覆盖 `_posts/` 文章内容。
- 不覆盖服务器 `.env`、运行时数据库、上传/生成图片、临时文件和缓存。
- 不调整 nginx、systemd、云资源、密钥和第三方平台配置。
- 不导入或抓取钉钉文档正文；当前只保留来源链接和本地选题池。

## 发布前本机验证

```bash
python3 -m py_compile app/admin_workbench.py app/insight_topics.py app/__init__.py app/uploader.py
.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py tests/test_public_article_homepage.py tests/test_social_publish.py::test_admin_links_respect_script_name_prefix -q
.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-20-admin-workbench-insight-topics.md --prd docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-prd.md --sdd docs/pola/project-knowledge/architecture/2026-06-20-admin-workbench-insight-topics-sdd.md --spec docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-spec.md --cases docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json
/Users/wangchang/.agents/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py
git diff --check
```

本机 Playwright smoke：

- 管理员测试会话进入 `/admin/workbench`。
- 打开 `/admin/insights/topics`。
- 点击一键导入，跳转 `/admin/upload?insight_topic=...`。
- 验证 Markdown 编辑框可见并包含 `## 洞察选题`、`状态：已导入`、`content-production`。

结果：

- `py_compile`：Pass。
- 相关 pytest：`15 passed in 0.69s`。
- 完整 pytest：`89 passed in 1.64s`。
- Function test cases harness：Pass，覆盖 6 个验收项、6 个功能、12 个用例。
- Pola skill harness：Pass。
- Playwright 本机 smoke：Pass，console clean，无 failed request。
- `git diff --check`：Pass。
- 敏感信息扫描：只命中既有环境变量名引用，未发现密钥值、cookie、private key 或明文 `.env`。

## 云端发布计划

1. 本地提交并推送本次相关文件到 `origin/main`。
2. SSH 到 `root@42.121.164.11`，在 `/PolaZhenjing` 备份本次覆盖文件。
3. 精确 rsync 本次范围文件到 `/PolaZhenjing`，排除 `_posts`、`.env`、运行时数据和临时目录。
4. 云端运行 py_compile 和相关 pytest。
5. 重启 `polazj.service`。
6. 线上 smoke：
   - `https://aipd.me/PolaZhenjing/admin/login`
   - `https://aipd.me/PolaZhenjing/admin/workbench`
   - `https://aipd.me/PolaZhenjing/admin/insights/topics`
   - `https://aipd.me/PolaZhenjing/admin/upload`
   - `https://aipd.me/PolaZhenjing/articles/fde-databricks-snowflake-20260610.md`

## 回滚方案

```bash
ssh root@42.121.164.11
cd /PolaZhenjing
BACKUP_DIR=/opt/backups/polazj-admin-workbench-insights-<timestamp>
tar -xzf "$BACKUP_DIR/app.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/templates.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/tests-docs.tgz" -C /PolaZhenjing
tar -xzf "$BACKUP_DIR/data-insight-topics.tgz" -C /PolaZhenjing
systemctl restart polazj.service
systemctl is-active polazj.service
```

## 执行记录

待发布后继续回填 commit、备份目录、云端验证和线上 smoke。

## 风险

- 选题状态目前为 JSON 文件存储，适合轻量后台管理；后续多人并发编辑时建议迁入 SQLite 或数据库表。
- 钉钉文档 URL 服务端未授权访问会跳 OAuth，当前不是自动同步实现。
- `/admin/` 默认入口从上传页改为工作台；上传页仍可通过导航和 `/admin/upload` 直接访问。
