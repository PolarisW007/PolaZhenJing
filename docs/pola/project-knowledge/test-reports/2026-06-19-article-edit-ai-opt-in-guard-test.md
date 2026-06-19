# 测试报告：文章编辑 AI 修改显式开关

## 测试时间

2026-06-19 17:35 CST

## 自动化测试

```bash
.venv/bin/python -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py
.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py -q
.venv/bin/python -m pytest tests/test_article_content.py tests/test_article_edit_rich_editor.py tests/test_upload_rewrite_rate.py tests/test_public_article_homepage.py tests/test_article_reader_roles.py tests/test_article_reader_sidebar_like.py -q
.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019
```

结果：

- 语法检查通过。
- 编辑模块 13 个测试全部通过。
- 文章内容/编辑/上传改写率/前台列表/阅读角色/侧栏点赞相关 32 个测试全部通过。
- Playwright 上传/编辑 harness 通过。

## 覆盖点

- 编辑页使用本地 TinyMCE 资源。
- 编辑页默认展示 Markdown 模式和预览。
- 编辑页默认存在 AI 修改开关，AI 面板隐藏。
- 未启用 AI 修改时，后端不会调用 AI 修订函数。
- 启用 AI 修改时，仍使用 canonical Markdown 给模型。
- 模型返回 `<think>` 时会清理。
- 模型遗漏图片/媒体时会补回原引用。

## 待补

- 线上部署后编辑页 smoke、受影响文章图片/正文回归。
