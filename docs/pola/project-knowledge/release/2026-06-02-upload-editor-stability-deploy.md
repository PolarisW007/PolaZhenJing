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

## 回滚

- 回滚本次提交并重启 `polazj.service`。
- 如仅需快速回滚上传页，可恢复 `app/templates/base.html` 和 `app/templates/upload.html` 到上一版本；`assets/vendor/tinymce/` 可暂留。
