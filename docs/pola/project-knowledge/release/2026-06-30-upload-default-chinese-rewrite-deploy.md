# 发布记录：上传生成默认中文改写

## 发布范围

- `app/article_ai.py`
- `app/uploader.py`
- `tests/test_upload_rewrite_rate.py`

## 发布目标

修复英文素材在非 0% AI 改写时可能默认保留英文正文的问题。后续上传、URL、PDF/文档等生成入口在启用 AI 改写时必须输出简体中文成稿。

## 发布方式

1. 本地提交 `67cdc26 fix: 强制上传改写默认输出中文`。
2. 推送 `origin/main`。
3. 云服务器 `/PolaZhenjing` 执行 `git fetch origin main`。
4. 仅 checkout 本次运行文件：
   - `app/article_ai.py`
   - `app/uploader.py`
   - `tests/test_upload_rewrite_rate.py`
5. 重启 `polazj.service`。

未执行 `git reset`，未覆盖线上文章、图片、历史文档和其它工作区改动。

## 备份

服务器备份目录：

```text
/opt/backups/polazj-default-chinese-rewrite-67cdc26-20260630/
```

## 发布前验证

- `python3 -m py_compile app/article_ai.py app/uploader.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_upload_rewrite_rate.py tests/test_article_edit_rich_editor.py -q`：23 passed。
- `validate_function_test_cases.py`：PASS，覆盖 5 个验收项。
- `git diff --check`：通过。
- 本次 diff 密钥关键词扫描：未命中。

## 发布后验证

- `.venv/bin/python3 -m py_compile app/article_ai.py app/uploader.py app/__init__.py`：通过。
- `PYTHONPATH=. .venv/bin/pytest tests/test_upload_rewrite_rate.py tests/test_article_edit_rich_editor.py -q`：23 passed。
- `systemctl is-active polazj.service`：active。
- `curl -I https://aipd.me/PolaZhenjing/admin/articles/software-engineering-in-the-20260629.md`：200 OK。
- `curl -I https://aipd.me/PolaZhenjing/admin/upload`：302 到登录页，符合未登录保护。
- 服务器文件确认包含：
  - `输出语言必须是简体中文`
  - `最终输出必须是简体中文 Markdown 成稿`
  - `先忠实翻译成中文`

## 回滚

如新 prompt 导致术语被过度翻译，可从备份恢复：

```bash
cp -a /opt/backups/polazj-default-chinese-rewrite-67cdc26-20260630/article_ai.py /PolaZhenjing/app/article_ai.py
cp -a /opt/backups/polazj-default-chinese-rewrite-67cdc26-20260630/uploader.py /PolaZhenjing/app/uploader.py
systemctl restart polazj.service
```

## 备注

历史已生成的英文文章不会自动重翻译。需要通过编辑页启用 AI 修改建议，或重新上传/重新生成该文章。
