# 发布记录：每日选题本周数据初始化刷新

日期：2026-06-20

## 目标

- 按用户要求在线上重跑本周 2026-06-15 到 2026-06-20 的每日选题抓取任务。
- 为 Admin 洞察选题池初始化一批可校验的线上数据。
- 本次只刷新生产 `data/insight_topics.json`，不发布新代码、不覆盖 `.env`、不重启服务。

## 风险等级

- P2：生产数据写入，涉及外部网络抓取和后台管理数据池。
- 护栏：刷新前备份正式 JSON；刷新 API 保留人工状态；外部源错误隔离；刷新后做云端 test-client 和公网未登录保护 smoke。

## 执行环境

- 服务器：`pola-server`
- 应用目录：`/PolaZhenjing`
- 服务：`polazj.service`
- 刷新窗口：`days=7`

说明：当前线上实现支持 `1/3/7/14/30` 天窗口，未提供精确 `date_from/date_to` 参数。本次使用 `days=7` 覆盖本周 2026-06-15 到 2026-06-20 的校验需求。

## 备份

- 备份目录：`/opt/backups/polazj-insight-topics-refresh-20260620203232`
- 备份文件：`insight_topics.json`

## 刷新结果

```json
{
  "refreshed_at": "2026-06-20T20:33:04",
  "days": 7,
  "signal_count": 131,
  "topic_count": 24,
  "source_counts": {
    "polanews": 60,
    "hackernews": 43,
    "github": 20,
    "rss": 8
  },
  "errors": []
}
```

刷新后正式选题池：

- 总数：27
- 状态：`new=26`、`imported=1`
- 来源：`polanews=16`、`hackernews=3`、`github=4`、`manual_seed=3`、`openai_blog=1`

## 验证

- `systemctl is-active polazj.service`：`active`
- 云端 Flask test-client：
  - `/admin/workbench`：200，包含 `PolaNews`
  - `/admin/insights/topics`：200，包含 `洞察文章选题`、`刷新线上选题`、`PolaNews`
- 公网匿名访问：
  - `https://aipd.me/PolaZhenjing/admin/login`：200
  - `https://aipd.me/PolaZhenjing/admin/workbench`：跳转到登录页
  - `https://aipd.me/PolaZhenjing/admin/insights/topics`：跳转到登录页

## 回滚

如刷新数据需要回退：

```bash
ssh pola-server
cd /PolaZhenjing
cp /opt/backups/polazj-insight-topics-refresh-20260620203232/insight_topics.json data/insight_topics.json
systemctl is-active polazj.service
```

## 观察项

- 后台选题页是否显示 27 条选题及最近刷新时间。
- 已导入的 1 条选题状态是否保持为 `imported`。
- 若需要严格从自然周起点 2026-06-15 抓取，后续应新增 `date_from/date_to` 精确窗口参数。
