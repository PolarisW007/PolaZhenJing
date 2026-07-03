# 2026-07-04 云端测试与标签修复测试报告

## 本地测试

- `validate_pola_skills.py`：PASS。
- `py_compile app/insight_topics.py scripts/backfill_insight_topics.py app/__init__.py app/agent.py scripts/build_agent_memory.py`：通过。
- `.venv/bin/python -m pytest tests -q`：103 passed。
- `validate_function_test_cases.py`：PASS。
- `git diff --check`：通过。

## 云端测试

- 云端首次 `tests/`：102 passed / 1 failed，失败原因为生产文章首个 tag `ai-lab` 不在业务主标签集合。
- 修复文章：`_posts/2026-06-21-new-usage-analytics-and-20260621.md`。
- 修复后 `.venv/bin/python -m pytest tests -q`：103 passed。
- 修复后单测 `test_local_posts_have_business_primary_tags_after_batch_tagging`：1 passed。
- HTTPS smoke：`admin/login=200`，`admin/workbench=302`，`admin/insights/topics=302`，`articles=200`。
- 服务状态：active。

## 结论

本地和云端项目测试均通过；线上已是最新代码，生产内容标签已修复，未重启服务。
