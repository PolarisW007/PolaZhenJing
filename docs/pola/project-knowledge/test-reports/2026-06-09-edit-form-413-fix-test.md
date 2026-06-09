# 测试报告:文章编辑页保存 413 修复

日期:2026-06-09

## 自动化

- 本地 `python3 -m py_compile app/__init__.py`:通过。
- 本地 `PYTHONPATH=. .venv/bin/pytest tests -q`:**37 passed**(原 34 + 本次 3)。
- 本地 `git diff --check`:通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests -q`:**34 passed**(云端少 3 个新测试是工作区未提交的存量差异,跑在云端 checkout 后的代码上时,3 个新测试也通过,见下面"云端 checkout 验证")。

## 新增单测

`tests/test_article_edit_413_fix.py`

3 个用例,都用 `tmp_path` 隔离 `_posts/`,避免污染云端真实文章。

- `test_500kb_body_should_not_413`
  - 提交 500KB `<p>x</p>` body,Werkzeug 旧默认 500KB 必 413,修复后 302 跳详情页。
- `test_1mb_body_should_not_413`
  - 提交 1MB body,继续 302。
- `test_8mb_body_should_not_413`
  - 提交 8MB body,继续 302(还没到 MAX_FORM_MEMORY_SIZE 16MB 上限)。

## 云端 checkout 验证

- `git checkout dee6bb7 -- app/__init__.py app/templates/article_edit.html tests/test_article_edit_413_fix.py`:3 文件落位。
- 云端 `python3 -m py_compile app/__init__.py`:通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_413_fix.py -q`:3 passed。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests -q`:34 passed(已包含 3 个新测试,因为它们在云端已 checkout)。

## 云端端到端 smoke(走 nginx https,gunicorn 真实进程)

`tests/test_article_edit_413_fix.py` 之外,再用 `requests` 走 `https://aipd.me/PolaZhenjing/...`:

| body 大小 | HTTP 状态 | 期望 | 实际 |
| --- | --- | --- | --- |
| 8KB(原文章) | 302 | 跳详情页 | ✓ |
| 100KB | 302 | 跳详情页 | ✓ |
| 500KB(修复前必 413) | 302 | 跳详情页 | ✓ |
| 1MB | 302 | 跳详情页 | ✓ |

修复前 500KB 必 413,修复后所有 body 大小 302 跳详情页。

## 回归检查(本次改动范围)

| 项 | 状态 |
| --- | --- |
| 上传页 TinyMCE 加载 | 不动,仍走 `/assets/vendor/tinymce/tinymce.min.js?v=6.8.5-pzj-20260602` |
| 文章编辑页模式切换 | 不动,`editor_mode` 单选仍工作 |
| 渲染预览(refresh preview) | 不动 |
| revision_instruction LLM 重写 | 不动 |
| 保存并同步 GitHub | 不动 |
| 其它管理路由(/admin/upload、/admin/social/*、/admin/skillhub) | 不动 |

## 未做的事(留给后续)

- 边界 17MB 严格 enforce 没单独测:Flask test client 不严格 enforce `MAX_CONTENT_LENGTH`,要测需在 gunicorn 端用真实请求测,本轮跳过(用户场景下不会到 16MB+)。
- 富文本 HTML 清洗(sanitize `<script>` / 危险属性):本轮不动。
- `assets/images/richtext/` 已上传图片的回收策略:本轮不动。
