# 2026-07-03 历史每日选题回填 SPEC

## CLI

命令：

```bash
.venv/bin/python scripts/backfill_insight_topics.py --start 2026-06-01 --end 2026-07-03 --json
```

参数：

- `--start`：必填，开始日期。
- `--end`：必填，结束日期。
- `--topics-per-day`：默认 1，范围 1 到 3。
- `--dry-run`：只计算不写入。
- `--json`：输出 JSON 摘要。

## 输出字段

- `start_date`
- `end_date`
- `target_days`
- `topics_per_day`
- `covered_days_before`
- `missing_days_before`
- `added_count`
- `added_dates`
- `missing_days_after`
- `total_topics`
- `persisted`

## 数据写入规则

1. 读取 `data/insight_topics.json`。
2. 以 topic 的 `date` 字段判断日期覆盖。
3. 已覆盖日期不生成新 topic。
4. 缺失日期生成 `manual_backfill` topic。
5. 每条 topic 进入 `_normalize_topic`，保证 id、draft、word count、evidence links 一致。
6. `save_topics` 保留既有 metadata，并写入 `last_backfill`。

## 不影响功能使用的验证路径

- A4：`tests/test_admin_workbench_insight_topics.py::test_import_topic_prefills_upload_markdown`
- A8：`/admin/workbench`、`/admin/insights/topics`、`/admin/upload`、文章公共页面和登录跳转 smoke。

## 验收映射

- A1：统计区间日期覆盖。
- A2：重复执行和保留已有 topic。
- A3：CLI dry-run 与 JSON 输出。
- A4：长底稿和上传导入。
- A5：云端安全合并发布方案。
- A6：测试与 Harness。
- A7：性能和安全边界。
- A8：生产回归。
