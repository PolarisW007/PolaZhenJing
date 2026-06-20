# SPEC：每日选题全网抓取

日期：2026-06-20

## 路由规格

- `GET /admin/insights/topics`
  - 展示选题列表、状态筛选、刷新表单和最近刷新元数据。
- `POST /admin/insights/topics/refresh`
  - 表单字段：`days`，允许 `1,3,7,14,30`，默认 `7`。
  - 权限：仅 admin。
  - 行为：采集信号、生成选题、保存 JSON、flash 成功/失败摘要、重定向回选题页。

## 数据结构

`data/insight_topics.json`

```json
{
  "source_url": "https://alidocs...",
  "updated_at": "2026-06-20T13:00:00",
  "last_refresh": {
    "refreshed_at": "2026-06-20T13:00:00",
    "days": 7,
    "signal_count": 42,
    "topic_count": 18,
    "sources": {"polanews": 20, "hackernews": 8},
    "errors": ["rss:openai timeout"]
  },
  "topics": []
}
```

单条 topic 扩展字段：

- `source_type`: `polanews` / `hackernews` / `github` / `rss` / `manual_seed` / `mixed`
- `source_count`: 证据数量。
- `evidence_links`: `[{ "title": "...", "url": "...", "source": "..." }]`
- `score`: 0-100。
- `generated_at`: 生成时间。
- `cluster_key`: 去重聚类键。

## 采集边界

- 单次刷新最多生成 24 条选题。
- 单来源最多读取 60 条信号。
- HTTP 请求默认 8 秒超时。
- 不保存全文正文，不保存 secret/cookie。

## 选题生成规则

- 去重键：URL 优先，其次标题规范化。
- 标签：基于标题/摘要关键词生成 2-5 个标签。
- 评分：来源权重 + 近期权重 + 互动指标 + AI/产品/工程相关性。
- 标题：保留真实信号标题，避免伪造夸张标题。
- 角度：用来源与标签生成一句可写作切口。

## 测试要求

- 单元测试不得真实依赖外网，使用 monkeypatch 假源。
- 本地可手动运行一次真实刷新 smoke，但不能作为单测必需条件。
