# 2026-07-06 洞察选题社媒运营生成机制测试报告

## 本地验证

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`14 passed in 0.83s`。
- `.venv/bin/python -m pytest tests -q`：`107 passed in 2.24s`。
- `validate_function_test_cases.py`：PASS，覆盖 10 个验收 ID / 6 个 feature / 11 个 case。
- `validate_pola_skills.py`：PASS。

## 数据源 Live Smoke

- 命令：`collect_rss_signals(days=30, limit_per_feed=4)`，只读执行，不写 `data/insight_topics.json`。
- 结果：`signal_count=30`。
- 来源计数：`openai_blog=4`、`huggingface_blog=3`、`google_ai_blog=4`、`deepmind_blog=1`、`microsoft_official_blog=5`、`aws_ml_blog=8`、`github_ai_ml_blog=4`、`sequoia_stories=1`。
- 结论：新增 RSS/Atom 源可被既有采集器解析；真实刷新仍由现有分源失败隔离兜底。

## 查询包 Live Smoke

- 命令：`collect_polanews_signals(days=30, limit=20)`，只读执行，不写 `data/insight_topics.json`。
- 结果：`polanews_count=5`，样例包含 AI 行业采用、AI 运营企业指数、组织采用 AI 的方式等场景/业务信号。
- 命令：`collect_topic_signals(days=30)`，只读执行。
- 结果：`topic_signal_count=135`，`source_counts={'industry_context': 7, 'polanews': 5, 'hackernews': 55, 'github': 30, 'rss': 38}`，`errors=[]`。
- 单测：`test_industry_context_sources_feed_social_operator_topics` 验证行业实践源能生成 best_practice、scenario_use_case、business_model 等运营选题，且标题不等于原始来源标题。

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
- A10：测试覆盖 PolaNews 查询词是否面向 workflow/use case/business model/best practice/adoption 以及中文场景、产品能力、商业模式、最佳实践、企业采用。

## 未执行项

- 初版报告为本地验证；2026-07-06 晚已按 release 记录完成生产发布。查询包 follow-up 需要再次执行云端 fast-forward、测试、服务重启和 HTTPS smoke。
