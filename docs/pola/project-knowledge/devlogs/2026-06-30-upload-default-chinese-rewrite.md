# 开发日志：上传生成默认中文改写

## 背景

用户反馈 `https://aipd.me/PolaZhenjing/admin/articles/software-engineering-in-the-20260629.md` 未默认翻译为中文。线上 HTML 里标题、摘要和正文为英文，但图片 alt 和配图资源已经生成，判断配图链路正常，正文改写语言约束不足。

## 计划

- 补充需求和 SPEC，明确 0% 不翻译、AI 改写启用时默认中文成稿。
- 修改共享 AI 改写 prompt 契约。
- 增加单测覆盖中文输出要求。
- 运行相关 pytest 和语法检查。

## 改动文件

- `app/article_ai.py`
- `app/uploader.py`
- `tests/test_upload_rewrite_rate.py`
- `docs/pola/project-knowledge/requirements/2026-06-30-upload-default-chinese-rewrite.md`
- `docs/pola/project-knowledge/specs/2026-06-30-upload-default-chinese-rewrite-spec.md`
- `docs/pola/project-knowledge/devlogs/2026-06-30-upload-default-chinese-rewrite.md`

## 验证记录

- `python3 -m py_compile app/article_ai.py app/uploader.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_upload_rewrite_rate.py tests/test_article_edit_rich_editor.py -q`：23 passed。
- `python3 /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-30-upload-default-chinese-rewrite.md --spec docs/pola/project-knowledge/specs/2026-06-30-upload-default-chinese-rewrite-spec.md --cases docs/pola/project-knowledge/delivery/upload-default-chinese-rewrite/function_test_cases.json`：PASS，覆盖 5 个验收项、2 个 feature、5 个 case。
- 线上现象复核：`software-engineering-in-the-20260629.md` 的 HTML 标题、摘要和正文仍为英文，而中文配图 alt 已生成，确认问题集中在正文改写语言契约，不是图片生成链路。

## 风险

- 历史已生成英文文章不会自动重翻译，需要单独编辑或重新生成。
- 过强的中文约束可能把不应翻译的英文术语翻译掉，因此文案保留代码、命令、API、产品名、链接和专有名词例外。

## 结论

已在共享改写率契约和上传通用 prompt 中补齐简体中文输出要求。后续非 0% AI 改写会默认把英文/外文素材转成中文成稿。
