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

待执行。

## Git 状态

待提交；本地工作区另有 `.qoder/skills/` 和 `tmp/` 未跟踪目录，本次不纳入提交。

## 钉钉同步

待同步；如 dws/网络/权限失败，将在最终回复中记录 blocker。
