# 发布记录：洞察选题导入上传预填修复

日期：2026-06-20

## 目标

- 修复线上 `/PolaZhenjing/admin/insights/topics` 点击“一键导入上传”后，上传页显示空富文本编辑器、Markdown 底稿不可见的问题。
- 移除当前工作台和选题页中的钉钉底料入口与旧提示。
- 同步每日选题 5000 字底稿逻辑到云端，使生产选题导入上传时可获得完整 Markdown 草稿。

## 发布范围

- `app/insight_topics.py`
- `app/templates/upload.html`
- `app/templates/insight_topics.html`
- `app/templates/admin_workbench.html`
- `tests/test_admin_workbench_insight_topics.py`
- 相关 Pola project-knowledge 文档和 function test cases。

## 不发布范围

- 不覆盖 `_posts/`。
- 不覆盖 `.env`。
- 不覆盖上传图片、数据库或其他运行时缓存。
- 不修改 Nginx、systemd 配置或云资源。

## 风险等级

- P2：涉及后台上传主流程和生产选题 JSON 的读取/导入。
- 护栏：
  - 发布前备份代码文件和正式 `data/insight_topics.json`。
  - 默认导入模式不初始化 TinyMCE，只影响带 `insight_topic` 的上传页。
  - 普通粘贴上传页仍默认富文本模式。

## 本机验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q`：`12 passed`。
- Function test cases harness：
  - Admin 工作台与洞察选题：通过，覆盖 6 个验收项、6 个 feature、12 个 case。
  - 每日选题底稿：通过，覆盖 10 个验收项、4 个 feature、6 个 case。
- Playwright 本地 smoke：
  - 导入选题后 `#content` Markdown textarea 可见。
  - `#rich-content` 隐藏。
  - Markdown 长度 5806，包含 `## 核心判断`。
  - `window.tinymce=false`，导入模式未主动加载 TinyMCE。
  - 页面不包含 `钉钉底料`。

## 云端发布

- 服务器：`pola-server`
- 应用目录：`/PolaZhenjing`
- 备份目录：`/opt/backups/polazj-insight-import-prefill-20260620232418`
- 发布方式：精确 `rsync -avR` 同步发布范围文件。
- 服务重启：`systemctl restart polazj.service` 成功，`systemctl is-active polazj.service` 为 `active`。

## 云端验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q`：`12 passed in 1.49s`。
- 云端认证态 Flask smoke：
  - 生产选题池总数 27。
  - 导入真实生产选题后上传页 200。
  - Markdown textarea 长度 6127。
  - 包含 `## 核心判断`。
  - 包含 `Markdown 源码模式已就绪`。
  - 不包含无条件 `initRichEditor()` 旧逻辑。
  - 不包含 `钉钉底料`。
  - 验证用选题 `ab0a9d1435d9` 的状态已恢复为 `new`，避免污染生产选题池。
- 云端页面 smoke：
  - `/admin/workbench`：200，不包含 `钉钉底料`，包含 `底稿`。
  - `/admin/insights/topics`：200，不包含 `钉钉底料`，包含 `刷新线上选题` 和 `底稿`。
- 公网匿名 smoke：
  - `https://aipd.me/PolaZhenjing/admin/login`：200。
  - `https://aipd.me/PolaZhenjing/admin/insights/topics`：跳转登录页。
  - `https://aipd.me/PolaZhenjing/admin/upload`：跳转登录页。
- `journalctl -u polazj.service --since "5 minutes ago"`：只看到正常 stop/start 和 gunicorn worker boot，无异常堆栈。

## 回滚

```bash
ssh pola-server
cd /PolaZhenjing
BACKUP_DIR=/opt/backups/polazj-insight-import-prefill-20260620232418
tar -xzf "$BACKUP_DIR/app-templates-tests-docs-existing.tgz" -C /PolaZhenjing
cp "$BACKUP_DIR/insight_topics.json" data/insight_topics.json
systemctl restart polazj.service
systemctl is-active polazj.service
```

## 后续观察

- 管理员真实浏览器点击任意选题“一键导入上传”后，应直接看到 Markdown 源码 textarea 中的完整底稿。
- 如果用户手动切回富文本，才加载 TinyMCE 并做 Markdown 到富文本转换。
