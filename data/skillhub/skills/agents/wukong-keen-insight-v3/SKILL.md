---
name: wukong-keen-insight-v3
description: "千里眼 v3：时间段全群检索 + 多轮聊天语义合并 + 群链接跳转 + 多维表列顺序优化。脚本用 dws chat message search 跨全会话时间窗拉取消息，Agent 做语义分簇合并（同一事件只出一条记录），写入 v3 专用多维表并通知用户。Run: /path/to/python .../scripts/run.py --keywords '悟空' --date 今天."
metadata:
  platforms: "claude-code,openclaw,cursor,wukong"
  skill-root-env: "KEEN_INSIGHT_V3_SKILL_ROOT"
  display-name: "悟空千里眼 v3"
  author: 王畅
  created: "2026-04-20"
  updated: "2026-04-20"
---

# 悟空千里眼 v3 —— 时间段全群检索 + 语义合并 + 群链接跳转

脚本批量采集钉钉群消息（**v3 改为跨全会话时间窗搜索**），Agent 对多轮聊天做语义分簇合并（**同一事件只生成一条记录**），写入 v3 专用多维表（**列顺序已优化 + 新增群链接字段**）并通知用户。

零第三方依赖，仅 Python 标准库。脚本只做采集，Agent 做分析。**所有钉钉操作统一走 dws CLI。**

## v3 相对 v2 的升级点

| 升级项 | v2 实现 | v3 实现 |
|---|---|---|
| **检索方式** | 先 `chat search` 搜群 → 逐群 `message list` 拉消息 | 直接 `chat message search --keyword` **跨全会话 + 时间窗**，一次搞定 |
| **多轮合并** | 摘要级语义去重（同一 key 保留最高分） | **同一事件全部消息合并为 1 条记录**，原始内容保留完整证据链 |
| **跳转链接** | 无 | 新增「群链接」字段，点击打开钉钉对应会话（深链 `dingtalk://`，兜底 `https://im.dingtalk.com/?conversationId=xxx`） |
| **列顺序** | 字段写入顺序固定 | **日期（首列索引）→ 排名 → 一句话摘要 → 建议解决方案 → 群名 → 价值维度 → 紧急程度 → 分类 → 综合得分 → 优先级 → 当前状态 → 关键行动 → 发送人 → 消息时间 → 合并消息数 → 群链接 → 原始内容 → 置信度** |
| **多维表** | `TbEXpjZ`（在另一 base） | **v3 专用表：baseId=`nYMoO1rWxmP7olkyFQlOGK76V47Z3je9` / tableId=`z2uCFiw`**（在「悟空千里眼·情报」base 内独立一张表，不污染 v2 历史数据） |

### 关于跳转链接的硬约束（重要）

钉钉 `chat message search` / `chat message list` 的原始返回**没有 messageId 字段**，**无法精确跳转到某条消息**。
v3 的「群链接」只能做到**会话级跳转**（打开群/单聊），用户需根据「消息时间」字段在群里自行定位。
如果以后钉钉开放 messageId，v3 可平滑升级为"跳转到具体消息"。

## 何时使用

- 想按**时间段**（例如近 1 小时 / 今天 / 本周）扫描所有相关群的消息，不想按群枚举。
- 一件事情在多个群里被反复讨论（客户常见诉求、跨群共识），希望**合并为一条情报**。
- 希望在多维表情报中直接点击就能跳回钉钉会话。

## 依赖

- Python 3.9+（仅标准库）
- dws CLI：需先执行 `dws auth login` 完成认证

## Agent 五步执行协议（必遵）

### 步骤一：调用脚本采集消息

```bash
"/path/to/python" "/path/to/wukong-keen-insight-v3/scripts/run.py" \
  --customer "悟空事业部" \
  --user "王畅" \
  --keywords "悟空" \
  --date "今天"
```

脚本 stdout 输出：
- `KEEN_V3_MARKDOWN_FILE:{path}` — 人类可读 Markdown
- `KEEN_V3_JSON_FILE:{path}` — 结构化 JSON，包含每会话的 `deep_link`/`web_link` 和按时间排序的消息列表
- `KEEN_V3_TOTAL_GROUPS:{n}`、`KEEN_V3_TOTAL_MESSAGES:{n}`

Agent 捕获 JSON 路径进入下一步。

### 步骤二：读 JSON + LLM 语义分簇（核心升级点）

Agent 读取 JSON，对**同一 conversation + 相近时间 + 同一话题**的消息做**语义分簇**。

**分簇规则（必遵）：**

1. **会话内多轮合并**：同一 `conversation_id` 内，若连续多条消息围绕**同一事件/同一诉求/同一话题**展开（时间跨度 ≤ 30 分钟、或话题承接明显），合并为 **1 条记录**。
2. **跨会话同主题合并**：若多个会话（例如 5 个单聊）在同一时间段内被本人重复提起**同一问题/同一诉求**（如"企业算粒采购"被问了 5 家），合并为 **1 条跨会话记录**，在「群名」字段标注 `N会话合并（会话名列表）`。
3. **原始内容保全**：所有被合并的原始消息按时间顺序拼接进「原始内容」字段，每条带发言人和时间戳，形成完整证据链。
4. **群链接归属**：合并记录的「群链接」使用**主群**（消息数最多/最具代表性的会话）的 deep_link。

**每条记录输出字段**（与 v3 多维表 18 字段一一对应）：

| 字段 | fieldId | 说明 |
|------|---------|------|
| 日期 | `wcRKHda` | yyyy-MM-dd |
| 排名 | `dkPvjKa` | 从 1 开始递增 |
| 一句话摘要 | `dPZXFuN` | 50 字以内核心摘要 |
| 建议解决方案 | `WsaMm6m` | 高/中优先级必填，给出下一步建议 |
| 群名 | `4y945x1` | 主群名；跨会话合并时写 `N会话合并（xx/yy/zz）` |
| 价值维度 | `BOv2cep` | 市场机会 / 竞争情报 / 决策讨论 / 风险预防 / 知识共享 |
| 紧急程度 | `okjMCwe` | 立即响应 / 关键待办 / 适时跟进 / 信息同步 |
| 分类 | `IgiT3p7` | 8 类之一 |
| 综合得分 | `oi3wQAn` | 价值权重 × 紧急权重 |
| 优先级 | `bm32MbN` | 高(≥12) / 中(4-11) / 低(≤3) |
| 当前状态 | `oWuYRpy` | 被识别（默认） |
| 关键行动 | `1Dh7Xwj` | Action Item，可为空 |
| 发送人 | `M0kuRsa` | 代表性发言人，多人用 `/` 分隔 |
| 消息时间 | `vpbNqjc` | 簇内最早消息时间 `yyyy-MM-dd HH:mm:ss` |
| 合并消息数 | `y5Ijv8W` | 该簇合并了多少条原始消息 |
| 群链接 | `reYB7CZ` | URL 字段：`{"text":"打开会话","link":"dingtalk://..."}` |
| 原始内容 | `Cmg0eb1` | 合并的完整证据链（≤5000 字） |
| 置信度 | `A4p4h7k` | 分簇+分类置信度 0-1 |

**价值权重与紧急权重同 v2**（市场机会=5 / 竞争情报=4 / 决策讨论=3 / 风险预防=3 / 知识共享=1；立即响应=5 / 关键待办=4 / 适时跟进=2 / 信息同步=1）。

### 步骤三：排序与数量控制

1. 综合得分降序
2. 同分按簇内最早消息时间倒序
3. 高优先级全保留；中优先级 ≤ 24 条；低优先级补到总数 36 条为止
4. 总数不足不强凑

### 步骤三点五：差量写入（防重复）

写入多维表前先查询当日已有记录：

```bash
dws aitable record query \
  --base-id "nYMoO1rWxmP7olkyFQlOGK76V47Z3je9" \
  --table-id "z2uCFiw" \
  --filters '{"operator":"and","operands":[{"operator":"date_eq","operands":["wcRKHda","2026-04-20"]}]}' \
  --format json
```

对比「一句话摘要」语义相似度，已存在的跳过、新增的从 `max(已有排名)+1` 开始编号。

### 步骤四：dws 写入 v3 多维表

**v3 专用多维表**（请优先复用，避免重复建表）：

| 配置项 | 值 |
|--------|-----|
| base-id | `nYMoO1rWxmP7olkyFQlOGK76V47Z3je9` |
| table-id | `z2uCFiw` |
| view-id | `2R0fbAy` |
| 访问地址 | `https://docs.dingtalk.com/i/nodes/nYMoO1rWxmP7olkyFQlOGK76V47Z3je9?iframeQuery=sheetId%3Dz2uCFiw` |

**批量写入**（每批 ≤ 20 条）：

```bash
dws aitable record create \
  --base-id "nYMoO1rWxmP7olkyFQlOGK76V47Z3je9" \
  --table-id "z2uCFiw" \
  --records '[{"cells":{"wcRKHda":"2026-04-20","dkPvjKa":1,"dPZXFuN":"...","reYB7CZ":{"text":"打开会话","link":"dingtalk://..."},...}}]' \
  --format json
```

**权限处理**：首次写入若返回 `PAT_MEDIUM_RISK_NO_PERMISSION`，提示用户在悟空客户端点击「允许」授权 AI 表格写入权限（建议选 `permanent`）。

### 步骤五：通知用户

```markdown
📊 千里眼 v3 播报 — {yyyy-MM-dd HH:mm}

时间窗口：{start} ~ {end}
扫描会话：{conv_count} 个
原始消息：{raw_count} 条
语义合并后：{merged_count} 条情报（🔴高 {high} 🟡中 {mid} 🟢低 {low}）

**高优先级 Top 5：**
1. [{分类}] {一句话摘要} — {群名}（合并{N}条）
2. ...

📋 多维表：https://docs.dingtalk.com/i/nodes/nYMoO1rWxmP7olkyFQlOGK76V47Z3je9?iframeQuery=sheetId%3Dz2uCFiw
```

## 技能使用的 dws 命令清单

| 阶段 | dws 命令 | 用途 |
|------|---------|------|
| 采集（脚本） | `dws chat message search --keyword "X" --start ISO --end ISO --limit 100 --cursor 0 -f json` | 跨全会话时间窗关键词搜索 |
| 写表（Agent） | `dws aitable record query --filters '{"operator":"and",...}' -f json` | 查询已有记录做差量 |
| 写表（Agent） | `dws aitable record create --records '[...]' -f json` | 批量写入 |
| 写表（Agent） | `dws aitable record delete --record-ids 'ID1,ID2' --yes -f json` | 删除低质量记录 |

## CLI 参数一览

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--customer` | 客户/主题名 | 环境变量 `DINGTALK_CUSTOMER` 或 `自定义` |
| `--user` | 采集人名字（多维表记录归属） | 环境变量 `KEEN_USER_NAME` |
| `--keywords` | 跨会话搜索关键词（`,` / `/` / `\|` / `、` / `，` 分隔，最多 20 个） | `悟空` |
| `--date` | 单日查询（YYYY-MM-DD / 今天 / 昨天 / 前天） | 今天 |
| `--week` | 周范围查询（本周 / 上周） | 无 |
| `--start-date` / `--end-date` | 自定义时间段（最多 14 天） | 无 |
| `--start-time` | 起始时间 HH:MM:SS | `00:00:00` |
| `--end-time` | 结束时间 HH:MM:SS（今天默认当前时刻，过去日默认 23:59:59） | 自动 |
| `--tz-offset` | 时区偏移 | `+08:00` |
| `--out-dir` | 输出目录 | `{技能根}/out` |

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `DINGTALK_CUSTOMER` | 客户名 | 无 |
| `DWS_EXECUTABLE` | dws 可执行文件路径 | PATH 中自动查找 |
| `KEEN_USER_NAME` | 采集人 | 无 |
| `KEEN_V3_OUT_DIR` | 输出目录覆盖 | `{技能根}/out` |
| `KEEN_LOG_LEVEL` | 日志级别 | INFO |

## 脚本职责

| 文件 | 职责 |
|------|------|
| `scripts/run.py` | 悟空平台入口适配器 |
| `scripts/fetch_and_save.py` | 跨全会话时间窗搜索 + 群链接生成 + Markdown/JSON 双输出 |

## 目录结构

```
wukong-keen-insight-v3/
├── SKILL.md              # 本文件
├── PRD-v2.md             # v2 产品需求文档（保留以供参考）
├── requirements.txt      # Python 依赖（仅标准库）
├── scripts/
│   ├── run.py            # 入口适配器
│   └── fetch_and_save.py # v3 核心采集脚本
└── out/
    └── .gitkeep
```

## v3 首次测试通过记录

- 测试时间：2026-04-20 19:28
- 关键词：悟空
- 时间窗：2026-04-20 00:00 - 19:28
- 原始命中：21 会话 / 39 条消息
- 语义合并后：14 条情报（5 条"企业算粒采购"跨 5 会话合并为 1 条）
- 全部写入 v3 表 `z2uCFiw`，RecordId 正常、群链接可点击
