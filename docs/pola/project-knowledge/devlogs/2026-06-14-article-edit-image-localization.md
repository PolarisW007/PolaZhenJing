# Devlog: 文章编辑后图片失效修复

日期: 2026-06-14

## 目标

修复 `rolling-ai-fde-ai-20260607.md` 编辑后正文图片全部失效的问题,并防止后续富文本编辑保存再次写入第三方临时图片和钉钉剪贴板元数据。

## 根因

- 编辑保存路径 `_build_post_markdown()` 未根据 `content_format` 清洗 body,直接写入 TinyMCE 富文本 HTML。
- 钉钉文档复制内容中的图片为 `alidocs.dingtalk.com` 临时 URL,浏览器访问会跳转 noAuth/403。
- 同一段富文本还包含大体积 `data-clipboard-cangjie` 属性,导致文章文件异常膨胀并拖慢编辑/渲染。

## 计划改动

- `app/uploader.py`: 在保存文章时按 `content_format` 转换正文;富文本路径清理属性并本地化外部图片。
- `tests/test_article_edit_rich_editor.py`: 增加富文本保存清洗和图片本地化回归测试。
- 线上 `_posts/2026-06-07-rolling-ai-fde-ai-20260607.md`: 备份后替换失效图片为稳定本地图片路径。

## 实际变更

- `app/uploader.py`
  - 新增远程图片本地化 helper,限制 public http/https、8MB、8 秒超时、image content type,拒绝私网/localhost/noAuth。
  - `_rich_html_to_markdown()` 在转 Markdown 前清理 `data-*`、`style`、事件属性和无关属性。
  - `_build_post_markdown()` 按 `content_format` 选择富文本转换或 Markdown 兼容保存。
- `tests/test_article_edit_rich_editor.py`
  - 新增富文本保存清洗和图片本地化测试。
  - 新增 Markdown 模式保留图片测试。
- 线上文章
  - 备份: `/PolaZhenjing/backups/2026-06-14-rolling-ai-fde-ai-before-image-repair-153522.md`
  - 修复后文件从约 762KB 降到约 37KB。
  - 9 个 `alidocs.dingtalk.com` 临时图替换为本地 `/PolaZhenjing/assets/...` 图片。

## 验证记录

- 本地: `python3 -m py_compile app/uploader.py` 通过。
- 本地: `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q` 通过,9 passed。
- 本地: `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` 通过,18 passed。
- 服务器: `.venv/bin/python -m py_compile app/uploader.py` 通过。
- 服务器: `PYTHONPATH=. .venv/bin/pytest tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py -q` 通过,9 passed。
- 服务器: `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q` 通过,18 passed。
- 服务器: `systemctl restart polazj.service && systemctl is-active polazj.service` 返回 `active`。
- 线上: `https://aipd.me/articles/rolling-ai-fde-ai-20260607.md` 返回 200,不含 `alidocs` / `data-clipboard`。
- 线上: 页面 9 张图片均返回 `200 image/png`,失败数 0。
- 浏览器: Playwright/Chrome 渲染该文章,`document.images.length=9`,`broken=[]`,console error 为空。

## 风险与回滚

- 风险等级: P2。
- 风险: 保存时下载远程图片可能增加延迟;通过超时、大小限制和失败不中断处理。
- 回滚: 恢复部署前 `app/uploader.py`;线上文章可从本次备份文件恢复。
- 代码部署备份: `/PolaZhenjing/backups/deploy-20260614-155116/`。
