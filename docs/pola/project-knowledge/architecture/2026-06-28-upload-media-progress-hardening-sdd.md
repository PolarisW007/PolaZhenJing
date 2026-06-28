# SDD: 上传媒体与 PDF 进度修复

## 现状与根因

- 富文本转换由 `app/article_content.py` 负责,保存路径最终以 canonical Markdown 入库/落盘。
- 现有 `html2text` 会把 `<img src="">` 转成 `![alt]()`、把 `<img src="blob:...">` 转成 blob 图片语法。这些 URL 不能被服务端或文章页长期访问。
- 富文本图片上传 endpoint 返回 `url_for('serve_assets')` 结果。在反向代理前缀缺失或页面处于 `/PolaZhenjing` 下时,裸 `/assets/...` 可能命中错误静态根。
- 文件/PDF 上传仍使用普通 HTML 表单 POST,浏览器上传和服务端解析期间没有用户反馈。

## 设计

### 富文本图片 URL

- `_save_richtext_image()` 与 `_richtext_image_url_from_bytes()` 返回稳定文章资源 URL:
  - 优先使用 `request.script_root`。
  - 兜底使用 `/PolaZhenjing`。
  - 输出 `/PolaZhenjing/assets/images/richtext/YYYY-MM/file.ext`。

### 富文本转换防御

- `html_to_canonical_markdown()` 在调用 `html2text` 前清理无效图片:
  - 无 `src` 或空 `src`: 删除。
  - `blob:`: 删除,因为服务端无法持久化。
- `_localize_rich_html_images()` 遇到 `blob:` 时删除图片,依赖前端提交前上传流程处理。
- `normalize_markdown()` 清理历史内容里的裸图片占位:
  - 独占一行的 `![alt]`
  - 空链接图片 `![alt]()`
- `_render_article()` 在渲染 `_posts` body 前走 `normalize_markdown()`,让线上旧文章不再暴露坏占位文本。

### 前端提交前图片 flush

- 上传页富文本表单 submit:
  - 如果当前模式是富文本并且 TinyMCE 已初始化,先调用 `editor.uploadImages()`。
  - 成功后 `tinymce.triggerSave()` 再提交。
  - 失败时显示错误并停止提交。

### 文件上传进度

- 仅增强 `#upload-form`。
- 使用 `XMLHttpRequest` 提交 `FormData`。
- `xhr.upload.onprogress` 更新进度条。
- `load` 成功后跳转到 `xhr.responseURL` 或风格选择页。
- 没有 JS 时保留原生表单 fallback。

## 兼容性

- 后端路由、表单字段、draft payload、style select 和 job 生成流程保持不变。
- 已有本地 `/assets/...` 图片仍被 `_is_local_article_image_url()` 识别。
- 历史文章渲染只增加坏图片占位清理,不改动正常图片、短链、分享卡片和管理按钮逻辑。

## 测试策略

- 单测覆盖:
  - 富文本空/缺失/blob 图片不会生成坏 Markdown。
  - 历史裸图片占位会被规范化清理,正常图片保留。
  - 富文本本地图片仍生成 Markdown 图片。
  - 上传页包含进度条与 XHR 上传逻辑。
  - 上传页富文本提交前调用 `uploadImages()`。
- 语法检查:
  - `app/article_content.py`
  - `app/uploader.py`
  - `app/__init__.py`
- Harness:
  - Flask test client 验证上传页 DOM/JS 标记。
  - 如本机浏览器可用,补浏览器可见性验证;否则记录环境阻塞。

## 回滚

- 回滚 `app/article_content.py`、`app/uploader.py`、`app/templates/upload.html` 和测试/文档改动。
- 若已部署云端,按发布前备份恢复对应文件并重启 `polazj.service`。
