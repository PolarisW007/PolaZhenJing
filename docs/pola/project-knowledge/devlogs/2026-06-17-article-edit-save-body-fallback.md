# Devlog: 文章编辑保存未生效兜底修复

## 目标

用户反馈 `https://aipd.me/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md` 进入编辑后保存，页面内容没有生效。

本次目标是修复编辑页保存正文时对前端隐藏字段 `body` 的单点依赖，确保富文本编辑和 Markdown 源码编辑都能可靠写回文章文件。

## 根因判断

- 线上文件 `_posts/2026-06-07-rolling-ai-fde-ai-20260607.md` 在用户反馈前后确实被写入，说明 POST 保存链路能到达服务器。
- 当前后端 `_build_post_markdown()` 只读取 `form.get('body')` 作为正文。
- 编辑页真实表单字段是 `rich_content` 和 `content`，提交时依赖前端 JS 动态创建隐藏 `body` 字段。
- 一旦 TinyMCE `triggerSave()`、隐藏字段创建、浏览器提交事件或编辑器初始化出现任何异常，后端会拿不到当前正文，造成“保存成功但内容没变化/不是当前编辑内容”的体验。
- 2026-06-17 追加复查：用户截图显示 Markdown 源码 textarea 与 TinyMCE 同时可见。原因是页面初始化阶段无条件执行 `initRichEditor()`，即使当前文章是 Markdown 模式也会启动富文本编辑器；用户在下方 Markdown textarea 修改时，提交脚本仍可能优先读取上方 TinyMCE 旧内容。
- 2026-06-17 再次复查：富文本编辑与 Markdown 源码切换按钮状态会改变，但页面可见编辑区不随之切换。浏览器 harness 复现到切回 Markdown 后 `visibleSources=3`，`#content`、`#rich-content` 和 `.tox-tinymce` 同时可见。进一步定位到两个叠加原因：TinyMCE `editor.hide()` 会把原始 textarea 重新显示出来；同时模板中 `.tox-tinymce { display: flex !important; }` 会覆盖普通 JS `display:none`。

## 改动

- `app/uploader.py`
  - `_build_post_markdown()` 按 `content_format` 从 `body`、`rich_content`、`content` 三个来源兜底取正文。
  - 富文本模式优先 `body -> rich_content -> content`。
  - Markdown 模式优先 `body -> content -> rich_content`。
- `app/templates/article_edit.html`
  - 保存提交时富文本模式优先调用 `tinymce.get('rich-content').getContent()`，再回落到 textarea 值，避免 textarea 未及时同步导致提交旧内容。
  - 取消页面底部无条件 `initRichEditor()`；初始为 Markdown 时只显示 Markdown 源码 textarea，不加载 TinyMCE，只有用户切换到富文本模式时才初始化 TinyMCE。
  - TinyMCE 加载失败 fallback 直接切回 Markdown 模式，不再先把富文本 textarea 强制显示，避免两个正文区域同时出现。
  - 新增 `hideRichEditorSurface()` / `showRichEditorSurface()`，切换模式时显式同步内容并控制 TinyMCE 容器。
  - 新增 `.editor-mode-hidden` 显隐 class，避免 `.tox-tinymce display:flex!important` 覆盖 Markdown 模式下的隐藏动作。
  - 切换到 Markdown 时不再调用 `editor.hide()`，避免 TinyMCE API 自动恢复原始富文本 textarea。
- `tests/test_article_edit_rich_editor.py`
  - 增加富文本缺失 `body` 时使用 `rich_content` 保存的回归测试。
  - 增加 Markdown 缺失 `body` 时使用 `content` 保存的回归测试。
  - 增加模板级断言，防止恢复“先 initRichEditor 再 setEditorMode”的无条件初始化顺序。
  - 增加模板级断言，确保保留 `.editor-mode-hidden` 与富文本显隐 helper。

## 验证

- `.venv/bin/python -m py_compile app/uploader.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q`：11 passed。
- 本地扩展回归：`.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py tests/test_article_reader_roles.py tests/test_article_reader_sidebar_like.py -q`：17 passed。
- 云端：`.venv/bin/python -m py_compile app/uploader.py app/__init__.py`：通过。
- 云端：`PYTHONPATH=. .venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q`：11 passed。
- 云端 harness：对 `rolling-ai-fde-ai-20260607.md` 用 Flask test client 临时 POST `rich_content` 标记，确认 `post_status=302`、`marker_in_file=True`、`marker_in_page=True`，随后恢复原文件并确认 `restored=True`、`marker_remaining=False`。
- 线上 HTTP：`https://aipd.me/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md?v=save-fallback-20260617` 返回 `200 OK`，测试标记不存在，标题正常。
- 追加本地浏览器 DOM harness：Markdown 编辑页 `content_format=markdown`，选中模式 `markdown`，`#content` 可见，`#rich-content` 隐藏，`.tox-tinymce` 数量为 0，`visibleTextSources=1`，`tinymceLoaded=false`。
- 追加云端渲染检查：`rolling-ai-fde-ai-20260607.md/edit` 管理员态 HTML 包含编辑表单，`no_unconditional_init=True`，`has_order=True`。
- 追加云端服务检查：`polazj.service` 为 `active`；`app/templates/article_edit.html` 更新时间 `2026-06-17 22:48:29 +0800`。
- 追加本地浏览器点击 harness（重启本地 Flask 后验证最新模板）：初始 Markdown、切到富文本、切回 Markdown、再次切到富文本四个状态均 `visibleSources=1`；切回 Markdown 后 `#content` 可见、`.tox-tinymce` 为 `display:none` 且 class 为 `editor-mode-hidden`。
- 追加本地最小测试：`.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q && .venv/bin/python -m py_compile app/uploader.py app/__init__.py`：11 passed，语法检查通过。
- 追加云端最小测试：`.venv/bin/python -m py_compile app/uploader.py app/__init__.py && PYTHONPATH=. .venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q`：11 passed。
- 追加线上浏览器 harness：打开 `https://aipd.me/PolaZhenjing/admin/articles/yi-ge-ren-you-zheng-zhi-you-jia-20260524.md/edit?v=mode-switch-20260617`，初始 Markdown、切到富文本、切回 Markdown、再次切到富文本四个状态均 `visibleSources=1`；切回 Markdown 后 `.tox-tinymce` 为 `display:none`，切回富文本后 `.tox-tinymce` 为 `display:flex`；console errors 为空。

## 影响面

- 仅影响文章编辑保存正文的取值兜底逻辑。
- 不改变文章详情渲染、上传生成、图片本地化规则、分享卡片、点赞和用户权限。
- 兼容旧表单：旧的 `body` 字段仍是第一优先级。

## 风险与回滚

- 风险等级：P3，小范围编辑保存可靠性修复。
- 风险：若浏览器同时提交多个正文来源且内容不同，仍以隐藏 `body` 为准；这是当前设计，避免改变正常 JS 路径。
- 风险：富文本与 Markdown 之间仍是 HTML/Markdown 原文级切换，不做语义级转换；本次只保证可见编辑源唯一、提交取值稳定。
- 回滚：恢复 `app/uploader.py` `_build_post_markdown()` 和 `app/templates/article_edit.html` 提交脚本本次改动。

## 状态

- 本地修复与测试完成。
- 已同步到云端 `/PolaZhenjing`，`polazj.service` 已重启且 `active`。
- 云端备份：`/opt/backups/polazj-edit-save-body-fallback-20260617-222047/files.tgz`。
- 追加重复编辑器修复已同步云端并重启服务。
- 追加云端备份：`/opt/backups/polazj-edit-duplicate-editor-20260617-225442/files.tgz`。
- 追加模式切换显隐修复已同步云端并重启服务，`polazj.service` 为 `active`。
- 追加云端备份：`/opt/backups/polazj-edit-mode-switch-20260617-232320/files.tgz`。
- Commit：未提交。
