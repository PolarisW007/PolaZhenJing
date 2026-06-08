# 需求记录：文章编辑页支持富文本编辑

日期：2026-06-08

## 原始需求

`https://aipd.me/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md/edit`
的编辑页只提供 EasyMDE 的基础 Markdown 工具栏(粗体/斜体/标题/列表/链接/图片/表格/代码/全屏/帮助),粘贴富文本或写公众号长文体验差。用户希望和上传页 `https://aipd.me/PolaZhenjing/admin/upload` 一样可以使用 TinyMCE 富文本编辑器,而不是只有 Markdown 源码。

## 目标

- 文章编辑页 `article_edit.html` 默认使用 TinyMCE 富文本编辑器。
- 保留现有 Markdown 源码模式,作为「Markdown 源码」切换项,让习惯手写 Markdown 的用户继续可用。
- 富文本模式下,粘贴、拖入和插入图片走现有 `/admin/upload/media` 富文本图片上传接口。
- 编辑页底部的「渲染预览」面板按当前模式显示:富文本直出 HTML,Markdown 走 `python-markdown` 渲染。
- 保存时按当前模式把内容写回 `body` 字段,文章文件继续以 `.md` 后缀保存在 `_posts/`,Jekyll 仍然能正常渲染。

## 非目标

- 不替换现有图片上传/媒体库,继续复用 `/admin/upload/media`。
- 不引入新的富文本编辑器(继续用 TinyMCE 6.8.5 本地 vendor)。
- 不重写编辑页其他字段(标题/日期/标签/风格/主题/摘要/front matter),也不动保存并同步 GitHub 流程。
- 不动 TinyMCE 本地 vendor、`tinymce-manifest.json` 或 `app/__init__.py` 的 `tinymce_asset_manifest`。
- 不替换 `_build_post_markdown` 写入逻辑:HTML 形态的 body 直接写回 `.md` 文件,Jekyll 原生支持 HTML 段。

## 验收标准

- A1 文档:需求、PRD/SPEC、开发日志和测试报告覆盖本次改动。
- A2 编辑页 HTML 不再引用 `cdn.jsdelivr.net/npm/easymde`,也不再加载 `easymde.min.js`。
- A3 编辑页 HTML 包含 `editor_mode` 单选(rich / markdown)、`#content-format` 隐藏字段、`#rich-content` 与 `#content` 两个文本区,以及上传页同款的本地 TinyMCE 主脚本 URL + `cache_suffix`。
- A4 编辑页与上传页使用同一份 TinyMCE 工具栏与图片上传 handler,粘贴图片走 `/admin/upload/media`。
- A5 预览接口 `POST /admin/articles/<filename>/preview` 在 `content_format=rich_html` 时直接返回原 HTML,在 `content_format=markdown`(默认值)时继续使用 `python-markdown` 渲染并替换 `{{ site.baseurl }}`。
- A6 打开已有 Markdown 文章时,自动选 Markdown 源码模式;打开已经是 HTML 形态的文章时,自动选富文本模式。
- A7 富文本 / Markdown 切换时,内容互相同步;提交时把当前模式的内容写入 `body` 字段,后端 `_build_post_markdown` 不需修改即可保存。
- A8 富文本编辑器加载失败时,自动切换到基础 textarea 兜底,提示文案沿用上传页「富文本编辑器资源加载失败,已自动切换为基础文本框;内容仍可正常提交」,用户仍可保存文章。
- A9 相关单测、语法检查、`git diff --check` 通过;线上 `/PolaZhenjing/admin/articles/.../edit` 浏览器 smoke 显示 TinyMCE 工具栏且无 jsDelivr 请求。

## 风险

- R1 编辑页 body 现在可能保存为 HTML 段,Jekyll 渲染时若用户混合 Markdown 与 HTML 可能出现解析顺序差异,需要在保存时按用户当前模式原样写回。
- R2 TinyMCE 插件列表与 `assets/vendor/tinymce/plugins/` 必须保持同步;若后续编辑页新增插件,需要同步补充 vendor。
- R3 切换 Markdown -> 富文本不会自动把 Markdown 转 HTML,首次切换是「清空富文本内容并填入 Markdown 原文」,用户保存后会被当 HTML 写回 `.md`;在 UI 提示「切换会按当前源码写入」,避免误用。
- R4 编辑页的 preview 接口把 `rich_html` 直出,要求 TinyMCE 输出的 HTML 是可信的;现有 `paste_preprocess` 已做 `<img>` 重写,但建议后续补一次富文本 HTML 清洗工具函数(本轮不在范围)。
