# SPEC：Admin 工作台与洞察选题池

## 路由规格

| 路由 | 方法 | 权限 | 行为 |
| --- | --- | --- | --- |
| `/admin/` | GET | 登录 | 管理员跳转 `/admin/workbench`，普通用户跳转 `/admin/account` |
| `/admin/workbench` | GET | 管理员 | 展示文章、选题、记忆、Skills、项目管理入口与统计 |
| `/admin/insights/topics` | GET | 管理员 | 展示选题池，支持 `status` 查询参数筛选 |
| `/admin/insights/topics/<topic_id>/status` | POST | 管理员 | 更新选题状态 |
| `/admin/insights/topics/<topic_id>/import` | POST | 管理员 | 标记选题为已导入，跳转上传页预填 Markdown |
| `/admin/upload?insight_topic=<topic_id>` | GET | 登录 | 若选题存在，预填标题、标签、描述、Markdown 正文 |

## 状态枚举

| 状态 | 文案 | 含义 |
| --- | --- | --- |
| `new` | 待处理 | 新进入选题池，尚未选择 |
| `selected` | 已选中 | 管理员认为值得写 |
| `imported` | 已导入 | 已导入上传页进入生成链路 |
| `archived` | 已归档 | 暂不处理或历史留存 |

## 数据结构

`data/insight_topics.json`：

```json
{
  "source_url": "https://alidocs.dingtalk.com/...",
  "updated_at": "2026-06-20T09:55:00",
  "topics": [
    {
      "id": "724e49daee3e",
      "date": "2026-06-20",
      "title": "内容生产 v2：从上传工具走向作者型写作系统",
      "angle": "写作角度",
      "summary": "摘要",
      "tags": ["content-production"],
      "status": "new",
      "source_url": "https://alidocs.dingtalk.com/...",
      "created_at": "2026-06-20T09:55:00",
      "updated_at": "2026-06-20T09:55:00"
    }
  ]
}
```

## 导入 Markdown 模板

```markdown
# 选题标题

## 洞察选题
- 日期：YYYY-MM-DD
- 状态：已导入
- 标签：tag-a, tag-b
- 来源：https://alidocs.dingtalk.com/...

## 写作角度
...

## 关键摘要
...

## 待展开问题
- 这个趋势为什么现在发生？
- 对创业者、产品经理或工程团队有什么直接影响？
- 哪些证据、案例或反例能支撑这个判断？
```

## 兼容规格

- 上传页 POST 字段和解析优先级不变。
- 未带 `insight_topic` 的上传页保持富文本默认模式。
- 非管理员不能进入工作台和选题池。

## 验收标准

- A1 管理员访问 `/admin/workbench` 能看到核心功能模块入口。
- A2 管理员访问 `/admin/insights/topics` 能看到每日选题列表和状态筛选。
- A3 点击选题导入后跳转 `/admin/upload?insight_topic=<id>`，上传页以 Markdown 模式预填洞察消息。
- A4 状态打标能持久化到本地 JSON。
- A5 普通未登录用户不能进入后台工作台和选题池。
- A6 钉钉文档无法服务端直读时，页面和文档需要明确来源链接、登录限制和后续接入边界。
