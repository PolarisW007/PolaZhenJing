# 开发日志：Admin 工作台与洞察选题池

## 时间

2026-06-20 09:39-11:08 CST

## 本次目标

- 新增 PolaZhenjing Admin 工作台入口，聚合文章管理、洞察选题、小王记忆、Skills、项目管理。
- 新增洞察文章选题池，支持查看每日选题、状态打标、一键导入上传页。
- 保持上传/编辑主流程不被破坏。

## 主要改动

- 新增 `app/admin_workbench.py`：后台工作台和洞察选题路由。
- 新增 `app/insight_topics.py`：选题 JSON 存储、状态更新、上传预填生成。
- 新增模板：
  - `app/templates/admin_workbench.html`
  - `app/templates/insight_topics.html`
- 更新：
  - `app/__init__.py` 注册新蓝图，管理员 `/admin/` 默认进入工作台。
  - `app/templates/base.html` 增加工作台和选题导航。
  - `app/uploader.py` / `upload.html` 支持 `insight_topic` 预填 Markdown。
- 新增初始数据：`data/insight_topics.json`。
- 新增测试：`tests/test_admin_workbench_insight_topics.py`。
- 新增 A2A 交付证据：
  - `docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json`
  - `docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/test_matrix.json`
  - `docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/regression_evidence.json`
  - `docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/delivery_state.json`
- 新增实现规格：`docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-spec.md`。

## 钉钉底料处理

服务端访问用户提供的钉钉文档 URL 会跳转到钉钉 OAuth 登录，当前不能直接读取正文。因此本轮实现为：

- 保存钉钉文档作为来源链接。
- 使用本地选题池承载每日选题和状态。
- 为后续接入钉钉开放接口预留 `source_url` 和 JSON 状态结构。

## 验证

- `python3 -m py_compile app/admin_workbench.py app/insight_topics.py app/__init__.py app/uploader.py`
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py tests/test_public_article_homepage.py tests/test_social_publish.py::test_admin_links_respect_script_name_prefix -q`
  - 15 passed
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-20-admin-workbench-insight-topics.md --prd docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-prd.md --sdd docs/pola/project-knowledge/architecture/2026-06-20-admin-workbench-insight-topics-sdd.md --spec docs/pola/project-knowledge/specs/2026-06-20-admin-workbench-insight-topics-spec.md --cases docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json`
  - PASS：覆盖 6 个验收项、6 个功能、12 个用例。
- `/Users/wangchang/.agents/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py`
  - PASS：Pola skill harness found no issues。
- Playwright 本地烟测：
  - 登录测试会话进入 `/admin/workbench`。
  - 打开 `/admin/insights/topics`。
  - 点击一键导入，跳转 `/admin/upload?insight_topic=...`。
  - 验证 Markdown 编辑框可见并包含 `## 洞察选题` 和 `状态：已导入`。
  - 烟测使用临时 `insight_topics.json`，避免污染正式种子数据。
- `git diff --check`
  - 通过
- 敏感信息扫描：
  - 未发现新增 token、cookie、private key、明文 `.env`。

## 风险与回滚

- 选题状态存储在 `data/insight_topics.json`，没有数据库迁移风险。
- 上传页仅新增 GET 预填逻辑，POST 解析优先级不变。
- 若线上不希望 `/admin/` 默认进工作台，可回滚 `app/__init__.py` 的 index 跳转和 `base.html` 导航改动。

## Commit 状态

已提交并发布：

- Commit：`83d58a1 feat(admin): add workbench insight topic workflow`。
- Push：`origin/main` 已更新。
- 云端发布：采用精确 rsync 同步到 `/PolaZhenjing`，备份目录 `/opt/backups/polazj-admin-workbench-insights-20260620122554`。
- 云端验证：py_compile、相关 pytest、function cases harness、服务重启、公网 smoke、认证态 Flask smoke 均通过。
- 备注：云端仓库存在既有 `_posts` 和 `.gitignore` 脏改动，未执行 `git pull`；发布范围文件已同步为本次 commit 内容。
