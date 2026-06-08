# 开发日志：上传页富文本编辑器稳定性修复

日期：2026-06-02

## 目标

修复 `/PolaZhenjing/admin/upload` 粘贴内容页富文本编辑器加载慢或加载不出来的问题。

## 排查记录

- 本地访问 jsDelivr TinyMCE 6.8.5 主脚本：`tinymce.min.js` 约 20.6 秒。
- 本地访问 jsDelivr TinyMCE 皮肤：`oxide` / `oxide-dark` CSS 约 8 秒。
- 浏览器 smoke 发现 `base.html` 的 Google Fonts stylesheet 会阻塞后续脚本执行，网络卡住时 `window.tinymce` 长时间不可用。
- 浏览器 smoke 发现 TinyMCE `autoresize` 插件会把空编辑器撑到约 1900px 高。

## 改动记录

- `app/templates/base.html`
  - Google Fonts 改为 `rel="preload" as="style"`，加载完成后再切为 stylesheet，并保留 noscript fallback。
- `app/templates/upload.html`
  - TinyMCE 主脚本改为 `/assets/vendor/tinymce/tinymce.min.js`。
  - `base_url` 改为 `/assets/vendor/tinymce`。
  - 移除 `autoresize` 插件，固定初始高度 480px，允许手动 resize，最大 720px。
  - TinyMCE 初始化失败时展示兜底提示并保留基础文本框。
- `assets/vendor/tinymce/`
  - 新增 TinyMCE 6.8.5 上传页必需运行资源。
- `assets/vendor/tinymce/tinymce-manifest.json`
  - 新增 TinyMCE vendor manifest，记录 `version`、`asset_version` 和当前启用插件集合。
- `tests/test_social_publish.py`
  - 增加上传页本地 TinyMCE 资源回归测试。

## 验证记录

- `python3 -m py_compile app/uploader.py app/__init__.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py`：10 passed。
- `PYTHONPATH=. .venv/bin/pytest tests`：20 passed。
- `git diff --check`：通过。
- 已跑浏览器 smoke：本地 `/admin/upload` 使用临时 admin session 打开，`.tox-tinymce` 221ms 出现；无 jsDelivr 请求；本地 TinyMCE 资源 14 个；失败请求 0；编辑器初始高度 480px。
- 云端部署：已精确同步本次相关文件到 `/PolaZhenjing`，云端 `tests/test_social_publish.py` 10 passed，`polazj.service` 为 `active`。
- 线上验证：`/PolaZhenjing/admin/upload` 未登录 302 到登录页；`/PolaZhenjing/assets/vendor/tinymce/tinymce.min.js` 返回 200；云端 Flask test client 验证上传页包含本地 TinyMCE、不包含 jsDelivr TinyMCE、字体链接为非阻塞 preload。
- 2026-06-02 用户反馈第一次修复“比原来更难用”：复查发现体验回归点包括上传页仍被 `.card-wide` 限制为窄卡片、TinyMCE 本地化后缺少中文语言包导致工具栏英文、固定 480px 高度不适合长文编辑。
- 2026-06-02 二次修复：上传页改为 `upload-card` 宽屏工作台，卡片宽度 1280px，表单区 1120px；新增本地 TinyMCE `zh-Hans` 语言包；编辑器初始高度提高到 680px，最小 520px，最大 900px。
- 2026-06-02 二次本地浏览器 smoke：`.tox-tinymce` 161ms 出现；卡片 1280px；编辑器 1120px x 680px；语言包 `/assets/vendor/tinymce/langs/zh-Hans.js` 成功加载；格式下拉显示“段落”；TinyMCE CDN 请求 0；失败请求 0；console error 0。
- 2026-06-02 性能复查：线上原版本 DOMContentLoaded 约 1168ms，TinyMCE 资源 15 个；113KB 真实 paste event 约 1290ms，845KB setContent/save/toggle 约 872ms。
- 2026-06-02 三次性能优化：TinyMCE 改为异步脚本加载，基础 textarea 立即可输入；插件从 9 个减到 5 个，移除 code/fullscreen/media/preview；新增加载状态提示。二次本地性能 smoke：DOMContentLoaded 74ms，编辑器 ready 188ms，TinyMCE 资源 11 个；845KB 长文处理总耗时 872ms。
- 2026-06-02 缓存版本优化：上传页从 TinyMCE manifest 获取 `asset_version`，主脚本 URL 增加 `?v=6.8.5-pzj-20260602`，TinyMCE 初始化增加 `cache_suffix`，语言包 URL 同步带版本参数，避免升级本地 vendor 后浏览器继续使用旧缓存。
- 2026-06-02 缓存版本优化验证：`python3 -m py_compile app/__init__.py app/uploader.py` 通过；`PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` 10 passed；`PYTHONPATH=. .venv/bin/pytest tests -q` 23 passed；`.venv/bin/python` Flask test client 确认上传页包含主脚本版本参数、`cache_suffix` 和语言包版本后缀，manifest 返回 200；`git diff --check` 通过。
- 2026-06-02 用户继续反馈线上等待 5 秒仍不能粘贴：本地 Playwright 复现发现 `.tox-tinymce` 外壳高度 680px，但 TinyMCE 内联 `display:block` 覆盖皮肤 flex 布局，导致 `.tox-edit-area` 和 iframe 高度均为 0px，状态栏贴到工具栏下方，用户看到的是不可点击的空区域。
- 2026-06-02 编辑区塌陷修复：上传页 CSS 强制 `.tox-tinymce` 为纵向 flex，`.tox-editor-container` 撑满剩余空间，`.tox-edit-area` 最小高度 360px，iframe 高度 100%；同时语言包版本参数改由 TinyMCE `cache_suffix` 统一追加，避免双重版本参数。
- 2026-06-02 编辑区塌陷验证：本地 Playwright smoke 中 `.tox-tinymce` 1120px x 680px，`.tox-edit-area` 1116px x 604px，iframe 1116px x 604px，statusbar 位于底部，编辑器 API 写入 `hello from fixed probe` 成功，TinyMCE 资源无失败请求。
- 2026-06-02 编辑区塌陷云端发布：部署前备份 `/opt/backups/polazj-upload-editor-layout-20260602115124`；精确同步上传页、manifest、测试和交付记录后重启 `polazj.service`；云端 `py_compile` 通过，`tests/test_social_publish.py` 10 passed，服务 `active`，线上 manifest 200；用户 Chrome 可访问树已显示富文本 iframe 输入区。

## 风险

- TinyMCE 插件列表和 `assets/vendor/tinymce/plugins/` 需要保持同步。
- 更新 TinyMCE vendor 文件时必须同步更新 `tinymce-manifest.json` 的 `asset_version`。
- 文章编辑页 `article_edit.html` 仍有 EasyMDE CDN，本次未处理，因为用户反馈范围是上传页富文本编辑器。

## Commit 状态

待提交：上传页编辑器稳定性修复、TinyMCE 本地资源、测试和交付文档。
