# 2026-07-03 历史每日选题回填 PRD

## 用户流程

1. 管理员或运维在部署前运行 dry-run：
   `scripts/backfill_insight_topics.py --start 2026-06-01 --end 2026-07-03 --dry-run --json`
2. 系统读取现有 `data/insight_topics.json`，统计目标区间已覆盖日期和缺失日期。
3. 管理员确认输出后运行持久化回填。
4. 系统只为缺失日期生成 `manual_backfill` topic，写入长底稿和 `last_backfill` 元数据。
5. 当历史日期已有旧新闻式 topic 且需要重刷质量时，管理员可增加 `--replace`，系统删除目标日期内 `new` 状态旧 topic，保留 `selected`、`imported`、`archived`。
6. `--replace` 使用行业实践源生成社媒运营选题，并写入 `last_range_regeneration` 元数据。
7. 管理员进入洞察选题列表，继续使用选中、导入、归档等既有功能。

## 功能行为

- 回填日期格式固定为 `YYYY-MM-DD`。
- 默认每个缺失日期生成 1 条 topic，最多支持 3 条，防止误操作无界扩张。
- 一次回填最多 366 天。
- topic 来源类型为 `manual_backfill`，来源显示为“历史回填”。
- topic 证据链接使用现有钉钉底料 URL，不新增外部抓取。
- 保存时保留已有 `last_refresh`，并新增或更新 `last_backfill`。
- `--replace` 模式不使用 `manual_backfill` 模板，而使用 `industry_context` 选题蓝图；每个目标日期生成 `topics-per-day` 条。
- `--replace` 模式只移除 `new` 状态旧 topic，避免覆盖用户已选中或已导入的运营结果。

## 异常分支

- 日期格式错误：CLI 直接失败并提示 `YYYY-MM-DD`。
- 开始日期晚于结束日期：失败，不写文件。
- 超过最大天数或每天数量越界：失败，不写文件。
- dry-run：不写 `data/insight_topics.json`。
- 无新增日期：不写文件，输出 `added_count = 0`。
- replace dry-run：输出预计移除和新增数量，不写文件。

## 兼容要求

- A1：选题池覆盖完整历史日期。
- A2：不覆盖已有日期和已有运营状态。
- A3：CLI 输出机器可读摘要。
- A4：回填 topic 可被现有导入上传流程消费。
- A8：旧入口、旧 API、旧数据结构继续可用。
- A9：`--replace` 可重生成日期段内 `new` 选题，并保留已选中/已导入/已归档 topic。
