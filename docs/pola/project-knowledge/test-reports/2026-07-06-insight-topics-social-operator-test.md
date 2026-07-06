# 2026-07-06 洞察选题社媒运营生成机制测试报告

## 本地验证

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`11 passed in 0.73s`。
- `.venv/bin/python -m pytest tests -q`：`104 passed in 2.16s`。
- `validate_function_test_cases.py`：PASS，覆盖 7 个验收 ID / 5 个 feature / 7 个 case。
- `validate_pola_skills.py`：PASS。

## UI 渲染验证

- 使用 Flask test client 构造管理员 session，渲染 `/admin/insights/topics`：HTTP 200。
- HTML 检查：包含 `AI 行业社媒运营选题`、`topic-lane`、`topic-hook`、`topic-structure`。
- Playwright 使用系统 Chrome 渲染 `/tmp/polazj-insight-topics-social-operator.html`：通过。
- 截图：`/tmp/polazj-insight-topics-social-operator.png`。
- 可见字段统计：`laneCount=3`，`hookCount=3`，`structureCount=3`，`sourceSignalCount=3`。

## 覆盖验收

- A1：生成 topic 标题不再等于原始新闻/链接标题。
- A2：每个 topic 有 `content_lane` 和 `content_lane_label`。
- A3：每个 topic 有社媒钩子、目标读者、核心问题和结构建议。
- A4：原始信号以 `source_signal_title` 和证据链接保留。
- A5：一键导入上传生成正文型长稿，不暴露后台管理态元信息。
- A6：旧列表、状态更新、刷新、回填、自动刷新锁和相邻流程测试通过。
- A7：Harness JSON 通过校验。

## 未执行项

- 本报告为本地验证。生产上线需要另行执行发布门禁：备份云端 `data/insight_topics.json`、fast-forward 更新代码、重启 `polazj.service`、运行云端测试和 HTTPS smoke。
