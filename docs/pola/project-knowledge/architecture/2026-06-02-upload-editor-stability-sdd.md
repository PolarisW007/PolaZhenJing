# SDD：上传页富文本编辑器稳定性修复

日期：2026-06-02

## 当前系统理解

- 上传页由 `app/templates/upload.html` 渲染，路由位于 `app/uploader.py` 的 `/admin/upload`。
- 上传页继承 `app/templates/base.html`，因此会受到后台基础字体和脚本加载顺序影响。
- 富文本粘贴图片上传接口为 `/admin/upload/media`，对应 `upload_richtext_media()`。
- 静态资源由 `app/__init__.py` 中 `/assets/<path:filename>` 从项目根目录 `assets/` 提供。

## 项目 Arch Reference 摘要

- arch-reference 路径：`docs/pola/arch-reference.md`
- 相关事实：
  - Flask app factory 注册后台 blueprint。
  - 管理后台使用 Jinja 模板和内联样式体系。
  - 静态资源通过 `/assets/` 从项目根 `assets/` 目录服务。
  - 上传页依赖前端编辑器，但提交仍由后端表单处理。

## 架构选型

| 方案 | 一致性 | 复用 | 风险 | 结论 |
| --- | --- | --- | --- | --- |
| 继续使用 CDN，加超时重试 | 中 | 高 | 网络慢时仍不稳定 | 不选 |
| 本地 vendor TinyMCE 必需资源 | 高 | 高 | 需维护插件文件列表 | 采用 |
| 替换为新编辑器 | 低 | 低 | 交互和转换链路风险大 | 不选 |

结论：保留 TinyMCE 6.8.5，但将上传页需要的 minified 运行文件放入 `assets/vendor/tinymce/`，并调整后台字体 CSS 为非阻塞加载。

## 资源清单

- `assets/vendor/tinymce/tinymce.min.js`
- `assets/vendor/tinymce/icons/default/icons.min.js`
- `assets/vendor/tinymce/models/dom/model.min.js`
- `assets/vendor/tinymce/themes/silver/theme.min.js`
- `assets/vendor/tinymce/plugins/{code,fullscreen,image,link,lists,media,preview,table,wordcount}/plugin.min.js`
- `assets/vendor/tinymce/skins/ui/{oxide,oxide-dark}/{skin.min.css,content.min.css}`
- `assets/vendor/tinymce/skins/content/{default,dark}/content.min.css`
- `assets/vendor/tinymce/license.txt`

## 模块影响

| 模块 | 改动 | 原因 | 风险 |
| --- | --- | --- | --- |
| `app/templates/base.html` | Google Fonts 改为 preload + onload stylesheet，保留 noscript | 避免样式表阻塞脚本执行 | 首屏可能先用系统字体 |
| `app/templates/upload.html` | TinyMCE 改用本地资源，移除 autoresize，加入兜底提示 | 修复加载慢和高度异常 | 插件列表需和 vendor 文件一致 |
| `assets/vendor/tinymce/` | 新增 TinyMCE 运行资源 | 消除上传页编辑器 CDN 依赖 | 增加约 1.4MB 静态资源 |
| `tests/test_social_publish.py` | 增加上传页资源回归测试 | 防止重新引入 CDN | 测试位置后续可拆分 |

## 测试策略

- 单测：上传页 HTML 不包含 jsDelivr TinyMCE，包含本地 TinyMCE 资源，本地资源路由返回 200。
- 语法检查：`python3 -m py_compile app/uploader.py app/__init__.py`。
- 浏览器 smoke：使用临时 admin session 打开本地 `/admin/upload`，等待 `.tox-tinymce` 出现，检查无 jsDelivr 请求、无失败请求、编辑器高度稳定。
- 线上回归：部署后访问线上 `/PolaZhenjing/admin/upload`，验证未登录 302 和本地资源 200；登录态可由用户在浏览器确认。

## 回滚方案

- 回滚 `base.html`、`upload.html`、测试和文档。
- 删除或保留 `assets/vendor/tinymce/` 均不影响后端上传和文章数据；若保留，只是未使用静态资源。
