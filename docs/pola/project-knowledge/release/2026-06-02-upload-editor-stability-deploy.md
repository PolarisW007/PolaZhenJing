# 发布记录：上传页富文本编辑器稳定性修复

日期：2026-06-02

## 发布范围

- `app/templates/base.html`
- `app/templates/upload.html`
- `assets/vendor/tinymce/`
- `tests/test_social_publish.py`
- `docs/pola/arch-reference.md`
- `docs/pola/project-knowledge/requirements/2026-06-02-upload-editor-stability.md`
- `docs/pola/project-knowledge/specs/2026-06-02-upload-editor-stability-prd.md`
- `docs/pola/project-knowledge/architecture/2026-06-02-upload-editor-stability-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-02-upload-editor-stability.md`

## 部署方式

- 服务器：`/PolaZhenjing`
- 方式：精确 `rsync` 本次相关模板、测试、文档和 TinyMCE vendor 静态资源。
- 服务：重启 `polazj.service`。

## 发布后验证

- 云端 `python3 -m py_compile app/uploader.py app/__init__.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py`：10 passed。
- 云端 `systemctl is-active polazj.service`：`active`。
- 线上 `/PolaZhenjing/admin/upload` 未登录返回 302 到 `/PolaZhenjing/admin/login`。
- 线上 `/PolaZhenjing/assets/vendor/tinymce/tinymce.min.js` 返回 200，大小 446827 bytes。
- 云端 Flask test client 带临时 admin session 验证：
  - 上传页状态 200。
  - 页面包含 `/assets/vendor/tinymce/tinymce.min.js`。
  - 页面不包含 `cdn.jsdelivr.net/npm/tinymce`。
  - Google Fonts 链接为非阻塞 preload。
- 二次体验修复后线上 Playwright smoke：
  - `.upload-card` 宽度 1280px。
  - `.tox-tinymce` 宽度 1120px，高度 680px。
  - 本地 TinyMCE 资源 15 个。
  - 语言包 `/assets/vendor/tinymce/langs/zh-Hans.js` 已加载。
  - 格式下拉显示“段落”。
  - TinyMCE CDN 请求 0，失败请求 0，console error 0。
  - 富文本写入和 Markdown 模式切换均通过。
- 三次性能优化后线上 Playwright smoke：
  - DOMContentLoaded 约 498ms。
  - TinyMCE ready 约 813ms。
  - TinyMCE 本地资源从 15 个降为 11 个。
  - CDN 请求 0，失败请求 0，console error 0。
  - 845KB 长文处理：setContent 147ms，triggerSave 265ms，富文本/Markdown 切换 448ms，总计 861ms。
- 四次编辑区塌陷修复后本地 Playwright smoke：
  - 原始复现：`.tox-tinymce` 外壳高度 680px，但 `.tox-edit-area` 和 iframe 均为 0px，状态栏贴在工具栏下方。
  - 修复后：`.tox-edit-area` 1116px x 604px，iframe 1116px x 604px，statusbar 位于底部。
  - 真实交互：点击 iframe 后键盘输入 `keyboard input probe` 成功，TinyMCE 资源 11 个，失败请求 0。
  - 自动化：`python3 -m py_compile app/__init__.py app/uploader.py` 通过；`PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` 10 passed；`PYTHONPATH=. .venv/bin/pytest tests -q` 23 passed；`git diff --check` 通过。
- 四次编辑区塌陷修复后云端发布：
  - 备份：`/opt/backups/polazj-upload-editor-layout-20260602115124`。
  - 云端验证：`python3 -m py_compile app/__init__.py app/uploader.py` 通过；`PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` 10 passed。
  - 线上状态：`polazj.service` 为 `active`；`/PolaZhenjing/assets/vendor/tinymce/tinymce-manifest.json` 返回 200；`/PolaZhenjing/admin/upload` 未登录返回 302 到登录页。
  - 用户 Chrome 可访问树已显示 `富文本区域` iframe 和 `文本输入区`，不再只有工具栏和状态栏。

## 回滚

- 回滚本次提交并重启 `polazj.service`。
- 如仅需快速回滚上传页，可恢复 `app/templates/base.html` 和 `app/templates/upload.html` 到上一版本；`assets/vendor/tinymce/` 可暂留。
