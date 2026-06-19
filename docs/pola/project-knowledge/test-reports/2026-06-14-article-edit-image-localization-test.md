# Test Report: 文章编辑图片本地化与保存清洗

日期: 2026-06-14

## 测试矩阵

| 验收项 | 类型 | 方式 | 状态 |
| --- | --- | --- | --- |
| A2 富文本属性清理 | 单测 | 保存富文本后读取 `_posts` 内容 | 通过 |
| A3 外部图片本地化 | 单测 | monkeypatch 下载 helper,断言本地 URL 写入 | 通过 |
| A4 Markdown 模式兼容 | 单测 | 保存 Markdown 图片并断言不丢失 | 通过 |
| A5 线上文章图片恢复 | 集成 | curl 图片响应 + 浏览器截图 | 通过 |
| A7 发布备份 | 发布 | 记录备份路径和回滚命令 | 通过 |

## 命令记录

- 本地 `python3 -m py_compile app/uploader.py`: 通过。
- 本地 `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q`: 9 passed。
- 本地 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`: 18 passed。
- 服务器 `.venv/bin/python -m py_compile app/uploader.py`: 通过。
- 服务器 `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q`: 9 passed。
- 服务器 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`: 18 passed。
- 服务器 `systemctl restart polazj.service && systemctl is-active polazj.service`: active。
- 线上图片检查:
  - 文章 URL: `https://aipd.me/articles/rolling-ai-fde-ai-20260607.md`
  - 图片数量: 9。
  - 图片状态: 9/9 返回 `200 image/png`。
  - 页面 HTML: 不含 `alidocs`、`data-clipboard`。
- 浏览器回归:
  - Chrome/Playwright 渲染文章页。
  - `broken=[]`。
  - console error 为空。
  - 截图: `/var/folders/n5/qgp982f52plfm1c3x4vvydm80000gp/T/rolling-ai-image-regression.png`。

## 残余风险

- 若用户粘贴的第三方图片已经需要登录态且服务端无法公开访问,自动本地化无法恢复原始图片内容;保存会保留原链接并记录脱敏日志。本次故障文章已通过历史本地配图路径完成内容修复。
- 远程图片下载在保存时发生,已设置 8 秒超时和 8MB 上限;极慢外部图片不会阻塞超过单图超时。
- 服务器工作区存在历史未提交改动,本次仅同步相关文件并记录备份路径,未执行 git reset 或回滚用户改动。
