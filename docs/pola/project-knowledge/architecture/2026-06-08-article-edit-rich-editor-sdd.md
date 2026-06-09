# SDD:文章编辑页 TinyMCE 富文本编辑器接入

日期:2026-06-08

## 当前系统理解

- 文章编辑页由 `app/templates/article_edit.html` 渲染,路由 `/admin/articles/<filename>/edit`,对应 `app/uploader.py` 的 `edit_article()`。
- 历史实现:EasyMDE(通过 `cdn.jsdelivr.net/npm/easymde`)提供基础 Markdown 工具栏(B/I/H/quote/list/link/image/table/code/fullscreen/help),仅支持 Markdown 源码,无法粘贴富文本、不支持所见即所得。
- 上传页(`/admin/upload`)的「粘贴内容」tab 已在用本地 TinyMCE 6.8.5(见 `2026-06-02-upload-editor-stability-sdd.md`),体验和编辑页分裂。
- 文章文件存放在 `_posts/*.md`,Jekyll front matter + Markdown body,Jekyll 原生支持 HTML 段混排。
- 后端 `preview_article_markdown` 路由仅做 Markdown 渲染,渲染管线为 `python-markdown + extra/codehilite/toc/tables` 扩展。

## 项目 Arch Reference 摘要

- arch-reference 路径:`docs/pola/arch-reference.md`
- 相关事实:
  - Flask app factory 注册后台 blueprint,模板经 Jinja 渲染。
  - 静态资源经 `/assets/<path:filename>` 从项目根 `assets/` 提供,带 7 天缓存头。
  - 富文本粘贴图片上传走 `upload_richtext_media()`,返回 `{"location": "/assets/images/richtext/..."}`。
  - 现有 `tinymce-manifest.json` 已记录 vendor 版本和插件集合,模板通过 `tinymce_asset_manifest()` 上下文处理器读取 `asset_version`。
  - 后端 `MAX_CONTENT_LENGTH = 16 * 1024 * 1024`,Werkzeug 3.x 默认 `max_form_memory_size = 500KB`(详见 2026-06-09 修复 SDD)。

## 架构选型

| 方案 | 一致性 | 复用 | 风险 | 结论 |
| --- | --- | --- | --- | --- |
| 沿用 EasyMDE,只换 CSS 主题 | 高 | 高 | 用户体验分裂(粘贴富文本仍丢样式) | 不选 |
| 复用上传页 TinyMCE,加 Markdown 源码切换 | 高 | 高 | 需为同一组件维护两套渲染输入 | 采用 |
| 替换为另一编辑器(Tiptap / Quill / CKEditor) | 低 | 低 | 引入新依赖、迁移成本 | 不选 |

结论:沿用本地 TinyMCE 6.8.5,与上传页共享 vendor / cache_suffix / 皮肤 / 中文语言包 / 图片上传 handler,新增「富文本 / Markdown 源码」双模式切换,提交时把当前模式内容写入隐藏 `body` 字段,后端零改动。

## 资源清单

(与上传页完全共享,本节列出以便核对一致性)

- `assets/vendor/tinymce/tinymce.min.js`
- `assets/vendor/tinymce/tinymce-manifest.json`
- `assets/vendor/tinymce/langs/zh-Hans.js`
- `assets/vendor/tinymce/icons/default/icons.min.js`
- `assets/vendor/tinymce/themes/silver/theme.min.js`
- `assets/vendor/tinymce/models/dom/model.min.js`
- `assets/vendor/tinymce/plugins/{image,link,lists,table,wordcount}/plugin.min.js`
- `assets/vendor/tinymce/skins/ui/{oxide,oxide-dark}/{skin.min.css,content.min.css}`
- `assets/vendor/tinymce/skins/content/{default,dark}/content.min.css`
- `assets/vendor/tinymce/license.txt`

## 模块影响

| 模块 | 改动 | 原因 | 风险 |
| --- | --- | --- | --- |
| `app/templates/article_edit.html` | 移除 EasyMDE CDN 与 CSS;新增 `editor_mode` 单选 / `content_format` 隐藏字段 / `#rich-content` 与 `#content` 双 textarea;接本地 TinyMCE;提交时 JS 把当前模式内容写入隐藏 `body` 字段 | 提供富文本编辑能力,和上传页体验一致 | 模式切换首次 Markdown → 富文本会按当前源码原样写回,不会自动转 HTML |
| `app/templates/article_edit.html` | TinyMCE 配置与上传页同款:`paste_data_images: true` + `images_upload_handler` 走 `/admin/upload/media` | 复用现有图片上传链路 | 编辑页和上传页共用上传接口,后续调整上传限制需同步两边 |
| `app/templates/article_edit.html` | 自动探测已有 body 形态决定初始模式:HTML → 富文本,否则 → Markdown | 已有 markdown 文章不被「强行渲染成 HTML」 | 探测规则只在首屏运行一次,后续用户可手动切换 |
| `app/templates/article_edit.html` | 渲染预览面板改为单列在编辑器下方(原为左右分栏) | 富文本编辑器本身已较宽,左分栏挤压编辑区 | 失去同时编辑+预览能力,改为手动刷新预览按钮 |
| `app/uploader.py` | `preview_article_markdown` 新增 `content_format` 入参,`rich_html` 直出,`markdown` 走原有 `python-markdown` 流程 | 支持富文本和 Markdown 两种模式预览 | `rich_html` 路径不做 HTML 清洗,依赖 TinyMCE 的 `paste_preprocess` 保证输入可信 |
| `app/uploader.py` | 路由 URL 仍 `/articles/<filename>/preview`(函数名 `preview_article_markdown` 沿用),函数 docstring 更新 | 不破坏其它调用方,目前仅编辑页调用 | 函数名与 markdown 略有歧义,后续若需可改名 |
| `app/uploader.py` | `_build_post_markdown` / `edit_article` 零改动 | 后端只读 `form.get('body')`,HTML 与 Markdown 同样能写回 .md 文件 | .md 文件中可能混入大量 HTML 段,Jekyll 仍可渲染但 git diff 可读性下降 |
| `tests/test_article_edit_rich_editor.py` | 新增 4 个用例:编辑页无 EasyMDE / 引用本地 TinyMCE / 预览 HTML 直出 / 预览 Markdown 渲染 / 缺省回落 | 防止 CDN 重新引入、防止 `preview_article_markdown` 行为回归 | 测试位置后续可拆分 |
| `scripts/deploy_editor_rtf_to_cloud.sh` | 新增端到端部署脚本(step 0-5 + 回滚模板) | 复用同一套发布模式 | 脚本是模板,实际部署走「精确 checkout 27 个文件」方案 3 |

## 测试策略

- 单测:`tests/test_article_edit_rich_editor.py` 4 个用例 + `tests/test_social_publish.py` 已有上传页断言(本次加强)。
- 语法检查:`python3 -m py_compile app/uploader.py app/__init__.py`。
- 浏览器 smoke:用临时 admin session 打开本地 `/admin/articles/2026-04-11-test-article.md/edit`,确认:
  - 工具栏中文,`.tox-tinymce` 高度 ≥ 360px,`.tox-edit-area` 不塌陷。
  - 模式切换实时同步。
  - 渲染预览随模式变化刷新。
  - 保存后跳详情页,新文件可被 Jekyll 渲染。
- 线上回归:部署后访问 `https://aipd.me/PolaZhenjing/admin/articles/<file>.md/edit`,未登录 302 跳登录,登录态可见 TinyMCE 工具栏且无 jsDelivr 请求。

## 回滚方案

- 方案 A(推荐):从 `/opt/backups/polazj-editor-rtf-<ts>/` 恢复 `app-templates.tgz` + `tests.tgz` 到 `/PolaZhenjing`。
- 方案 B:`git reset --hard ee4c10b`(回到本次 5 commit 之前)+ `systemctl restart polazj.service`。
- 文章文件(`_posts/*.md`)不受影响,Jekyll 发布页(`https://aipd.me/articles/...`)继续渲染。
