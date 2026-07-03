# 2026-07-04 云端测试与生产文章主标签修复开发日志

## 目标

按 `pola-a2a-usage` 要求对 PolaZhenJing 执行 A2A/Harness 与项目测试；若测试通过则更新线上。

## 本次处理

- 本地确认 `main` 与 `origin/main` 均为 `ff6261c`，无 tracked 改动。
- 本地运行 Pola A2A skill harness、语法检查、项目测试和 function test cases harness。
- 云端确认 `/PolaZhenjing` 已是 `ff6261c`，无需代码 fast-forward 或重启。
- 云端项目测试首次发现生产文章 `_posts/2026-06-21-new-usage-analytics-and-20260621.md` 的首个 tag 为 `ai-lab`，不属于 `ARTICLE_PRIMARY_TAGS`。
- 线上备份该文章到 `/root/polazj-backups/2026-06-21-new-usage-analytics-and-20260621.md.pre-tagfix-20260704`。
- 将该文章 tags 从 `[ai-lab, openai, ai, enterprise-ai, model]` 调整为 `[industry-analysis, openai, ai, enterprise-ai, model]`，保留其他标签。

## 验证

- 本地 `.venv/bin/python /Users/wangchang/.agents/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py`：PASS。
- 本地 `.venv/bin/python -m py_compile app/insight_topics.py scripts/backfill_insight_topics.py app/__init__.py app/agent.py scripts/build_agent_memory.py`：通过。
- 本地 `.venv/bin/python -m pytest tests -q`：103 passed。
- 本地 function test cases harness：PASS，覆盖 8 个验收 ID / 3 个 feature / 7 个 case。
- 本地 `git diff --check`：通过。
- 云端 `.venv/bin/python -m pytest tests -q`：修复后 103 passed。
- 云端 `tests/test_article_auto_tagging.py::test_local_posts_have_business_primary_tags_after_batch_tagging`：1 passed。
- 线上 smoke：`/PolaZhenjing/admin/login` 200，受保护后台和选题入口 302 到登录，`/PolaZhenjing/articles` 200。
- `polazj.service`：active。

## 风险与回滚

- 风险等级：P3，生产内容 frontmatter 标签修复，不涉及代码、数据库、密钥或服务重启。
- 回滚：将备份文件复制回 `_posts/2026-06-21-new-usage-analytics-and-20260621.md`。

## Git 状态

- 待提交本地记录文档，并 fast-forward 到云端。

## 钉钉同步

- 钉钉开发日志文档：`https://alidocs.dingtalk.com/i/nodes/b9Y4gmKWrPXEL936F4NKgLpMJGXn6lpz`。
- AI 表格 `开发日志` 表记录：`recordId=Bp9uVjiVKS`。
- 同步批次：`polazj-cloud-test-tagfix-20260704`。
