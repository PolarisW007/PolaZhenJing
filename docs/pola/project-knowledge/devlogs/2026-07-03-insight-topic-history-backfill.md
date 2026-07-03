# 2026-07-03 历史每日选题回填与云端安全合并开发日志

## 目标

完成历史日期补全生成能力，并安全处理云端 PolaZhenJing 与 GitHub 最新代码的分叉合并，最终让每日选题覆盖 2026-06-01 到 2026-07-03。

## 本次改动

- 新增 `app/insight_topics.py` 历史回填函数和 `manual_backfill` 来源类型。
- 新增 `scripts/backfill_insight_topics.py` 运维 CLI。
- 新增单测覆盖缺失日期回填、状态保留、dry-run 不写入。
- 新增需求、PRD、SPEC、SDD、release runbook 和 A2A Harness 文件。

## 稳定性与安全门禁

- 风险等级：P1。
- 不新增后台任务、cron、队列、本地模型或网络抓取。
- 回填范围和每天数量有上限。
- 云端发布必须先备份生产目录和 `data/insight_topics.json`。
- 不打印、不提交 secret。

## 本地验证

- `.venv/bin/python -m py_compile app/insight_topics.py scripts/backfill_insight_topics.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：10 passed。
- `.venv/bin/python scripts/backfill_insight_topics.py --start 2026-06-01 --end 2026-07-03 --dry-run --json`：本地 seed 数据预计补 32 天，`missing_days_after=[]`。
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py ...`：PASS，覆盖 8 个验收 ID / 3 个 feature / 7 个 case。
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py`：PASS。
- `git diff --check`：通过。

## 云端验证

- 备份分支：`backup/pre-history-backfill-20260703231809`。
- 备份目录：`/root/polazj-backups/history-backfill-20260703231809`。
- 旧生产目录：`/PolaZhenjing.pre-history-backfill-20260703231809`。
- 合并策略：直接 cherry-pick 云端 21 个 ahead 提交会带入旧 app 代码并导致 `/admin/*` 路由测试 404；最终采用 GitHub 最新代码 + 生产文章/图片/data 资产保留的目录切换发布。
- 发布后 HEAD：`3be6d82cded0f102fc18f61ee37d3ab1803c895e`。
- 回填结果：`added_count=29`，`total_topics=57`，`covered_count=33`，`missing_count=0`，`manual_backfill_min_words=5026`。
- 云端 `.venv/bin/python -m py_compile app/insight_topics.py scripts/backfill_insight_topics.py`：通过。
- 云端 `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：10 passed。
- 云端 function test cases Harness：PASS，覆盖 8 个验收 ID / 3 个 feature / 7 个 case。
- 线上 smoke：`https://aipd.me/PolaZhenjing/admin/login` 200；受保护 `admin/workbench` 和 `admin/insights/topics` 302 到登录；`/PolaZhenjing/articles` 200。
- `polazj.service`：active；gunicorn worker RSS 约 59 MB，服务重启后无 swap。

## Git 状态

- 代码提交：`3be6d82 feat: backfill historical insight topics`，已推送 GitHub。
- 云端 `/PolaZhenjing` HEAD 对齐 GitHub main。文章、图片、`data/insight_topics.json` 和 `data/theme.json` 作为生产运行数据保留在工作区，未做破坏性 hard reset。
- 本地工作区另有 `.qoder/skills/` 和 `tmp/` 未跟踪目录，本次不纳入提交。

## 钉钉同步

- 钉钉开发日志文档：`https://alidocs.dingtalk.com/i/nodes/7QG4Yx2JpLwEz4m6hQMomb11J9dEq3XD`。
- AI 表格 `开发日志` 表记录：`recordId=7gqqGXH6H4`。
- 同步批次：`polazj-history-backfill-20260703`。
- 回填字段：`来源文件` 指向钉钉开发日志文档，`更新内容` 已写入本次变更摘要。
