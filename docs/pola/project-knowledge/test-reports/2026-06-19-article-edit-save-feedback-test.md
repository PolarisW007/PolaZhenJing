# 测试报告：文章编辑页保存反馈修复

日期：2026-06-19

## 测试结论

Pass。

## 已运行

```bash
.venv/bin/python -m py_compile app/uploader.py scripts/upload_edit_playwright_harness.py
.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py -q
.venv/bin/python scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019
```

## Playwright 覆盖

- 登录后台。
- 上传页 Markdown -> 富文本切换。
- 编辑页 Markdown 预览。
- 编辑页富文本/Markdown 往返。
- 修改建议字段可填写。
- 创建临时文章并真实点击保存。
- 确认临时文章正文写回。
- 清理临时文章。

## 截图

- `tmp/harness/upload-edit/1781859339-upload-rich-switch.png`
- `tmp/harness/upload-edit/1781859340-edit-markdown-rich-preview.png`
- `tmp/harness/upload-edit/1781859341-edit-save-submitted.png`

## 未覆盖

- 没有真实调用线上 MiniMax 长耗时改写；本次使用 `rewrite_rate=0` 验证保存链路，避免污染或等待外部模型。
