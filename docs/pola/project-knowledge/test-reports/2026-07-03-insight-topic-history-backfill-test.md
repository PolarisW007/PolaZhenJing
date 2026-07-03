# 2026-07-03 历史每日选题回填测试报告

## 本地测试

- `.venv/bin/python -m py_compile app/insight_topics.py scripts/backfill_insight_topics.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：10 passed。
- `.venv/bin/python scripts/backfill_insight_topics.py --start 2026-06-01 --end 2026-07-03 --dry-run --json`：通过，dry-run 不写入。
- `validate_function_test_cases.py`：PASS，覆盖 8 个验收 ID / 3 个 feature / 7 个 case。
- `validate_pola_skills.py`：PASS。
- `git diff --check`：通过。

## 覆盖点

- A1：日期覆盖统计。
- A2：已存在日期不重复生成，已有状态不覆盖。
- A3：CLI JSON 输出和 dry-run。
- A4：回填 topic 生成长底稿。
- A6：本地测试与 Harness。
- A7：无网络抓取、无后台任务、范围有上限。

## 待补充

无。

## 云端测试

- 合并演练：直接 cherry-pick 云端 21 个 ahead 提交可自动合成，但会带入旧 app 代码并导致 6 个 `/admin/*` 路由相关测试 404；因此未采用该路径。
- 安全发布：使用 GitHub 最新代码，保留生产文章/图片/data 资产，目录切换后启动服务。
- 云端 `.venv/bin/python -m py_compile app/insight_topics.py scripts/backfill_insight_topics.py`：通过。
- 云端 `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：10 passed。
- 云端 function test cases Harness：PASS。
- 回填结果：`topic_count=57`，`covered_count=33`，`missing_count=0`，`manual_backfill=29`，`manual_backfill_min_words=5026`。
- HTTPS smoke：`/PolaZhenjing/admin/login` 200，受保护后台和选题入口 302，`/PolaZhenjing/articles` 200。
