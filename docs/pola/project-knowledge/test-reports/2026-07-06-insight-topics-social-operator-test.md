# 2026-07-06 洞察选题社媒运营生成机制测试报告

## 本地验证

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`12 passed in 0.84s`。
- `.venv/bin/python -m pytest tests -q`：`105 passed in 1.90s`。
- `validate_function_test_cases.py`：PASS，覆盖 9 个验收 ID / 6 个 feature / 9 个 case。
- `validate_pola_skills.py`：PASS。

## 数据源 Live Smoke

- 命令：`collect_rss_signals(days=30, limit_per_feed=4)`，只读执行，不写 `data/insight_topics.json`。
- 结果：`signal_count=30`。
- 来源计数：`openai_blog=4`、`huggingface_blog=3`、`google_ai_blog=4`、`deepmind_blog=1`、`microsoft_official_blog=5`、`aws_ml_blog=8`、`github_ai_ml_blog=4`、`sequoia_stories=1`。
- 结论：新增 RSS/Atom 源可被既有采集器解析；真实刷新仍由现有分源失败隔离兜底。

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
- A8：数据源覆盖官方模型/产品、企业采用、工程实践、商业模式等来源层。
- A9：新增源均有 HTTPS feed、label、tags 和 `SOURCE_LABELS`。

## 未执行项

- 本报告为本地验证。生产上线需要另行执行发布门禁：备份云端 `data/insight_topics.json`、fast-forward 更新代码、重启 `polazj.service`、运行云端测试和 HTTPS smoke。
