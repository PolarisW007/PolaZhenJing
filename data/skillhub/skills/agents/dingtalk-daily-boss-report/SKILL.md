---
name: dingtalk-daily-boss-report
description: 通过 DingTalk CLI (dws) 自动汇总当天 08:00-22:00 的钉钉AI听记、钉钉文档、钉钉AI表格，生成一份结构化老板日报并自动创建钉钉文档。Use when the user asks to generate a daily boss report, dingtalk summary, 老板日报, daily dingtalk report, or mentions dws/dingtalk CLI data collection.
---

# 钉钉老板日报自动生成

通过 `dws` CLI 收集当天钉钉数据，AI 提炼汇总，自动写入钉钉文档。

## 前置条件

- 已安装并登录 `dws`（`dws auth login`）
- 有权访问 `minutes`、`doc`、`aitable` 服务

## 工作流

### Step 1：确定时间范围

```bash
TODAY=$(date +%Y-%m-%d)
START_TIME="${TODAY} 08:00:00"
END_TIME="${TODAY} 22:00:00"
```

### Step 2：采集 AI 听记列表

```bash
dws minutes list \
  --start-time "${START_TIME}" \
  --end-time   "${END_TIME}" \
  -f json 2>/dev/null
```

对每条听记，获取 AI 纪要摘要：

```bash
# MINUTES_ID 来自上一步输出
dws minutes get --minutes-id "${MINUTES_ID}" -f json 2>/dev/null
```

> 若 `minutes` 服务尚未开放，直接跳过，在日报中注明"AI听记暂无数据"。

### Step 3：采集钉钉文档

```bash
dws doc list -f json 2>/dev/null
```

按修改时间过滤今日更新的文档，逐条读取内容摘要：

```bash
dws doc get --doc-id "${DOC_ID}" -f json 2>/dev/null
```

> 若 `doc` 服务尚未开放，在日报中注明"文档暂无数据"。

### Step 4：采集钉钉 AI 表格

```bash
dws aitable list -f json 2>/dev/null
```

读取今日有变更的表格关键数据：

```bash
dws aitable record list --table-id "${TABLE_ID}" -f json 2>/dev/null
```

### Step 5：获取当前用户名（用于日报称呼）

```bash
dws auth status -f json 2>/dev/null
# 取 .name 字段
```

### Step 6：AI 汇总生成日报正文

将上述所有原始 JSON 数据合并，严格按照以下模板顺序生成日报 Markdown。

**⚠️ 格式强制要求：**
- 第一行必须以"亲爱的{老板姓名}老板"开头（姓名取自 Step 5 `auth status` 的 `.name` 字段）
- 各章节顺序固定，不得调换
- 数据概览（来源统计）必须放在**最末尾**，因为它不是核心内容
- 所有关键数字（金额、百分比、数量）使用 `**加粗**`
- 总长度控制在 600 字以内

```markdown
## 亲爱的{老板姓名}老板，以下是你的今日钉钉重要总结

从今日的AI听记的AI纪要，钉钉文档，钉钉AI表格中提取并汇总

### 今日最核心事项TOP3
1. {从日报内容中提炼第1条最重要事项}
2. {从日报内容中提炼第2条最重要事项}
3. {从日报内容中提炼第3条最重要事项}

### 年度目标进度
- 营收达成率：{数据}，距目标差额{数据}
- 关键项目里程碑：{数据}
- 战略投入回报：{数据}
- 财务健康度：{数据}

### 市场与客户动态
- 客户增长：{新增客户数、流失率}
- 竞品动态：{关键对手动作简报}
- 品牌声量：{社交媒体提及量、舆情风险}

### 团队动态
- 核心业务进展（产品、运营、市场进度）
- 生产/交付效率：{订单处理时效、产能利用率}
- 供应链稳定性：{关键物料库存、供应商交货准时率}

### 风险与机会
- 风险预警
    - 合规风险：{政策变动影响}
    - 技术风险：{系统故障、数据安全事件}
    - 市场风险：{汇率波动、原材料涨价}
- 机会捕捉
    - 新市场机会：{潜在合作方/客户线索}
    - 创新突破：{研发/技术进展}

### 行动建议
- 关键决策：{需审批的事项}
- 资源调配建议：{跨部门协作需求}

---

### 数据概览（来源统计）
| 数据类型 | 数量 | 状态 |
|----------|------|------|
| AI 听记  | {N} 条 | {已获取/暂无数据} |
| 钉钉文档 | {N} 个 | {今日更新N个/暂无更新} |
| AI 表格  | {N} 个 | {已获取/暂无数据} |

数据来源：自动同步钉钉AI听记、钉钉文档、钉钉AI表格
生成时间：{YYYY-MM-DD HH:mm}
```

汇总规则：
- 若某类数据为空，相关章节写"今日暂无此类数据"，不要省略章节
- 数据概览始终放最末尾

### Step 7：写入钉钉文档（必须创建真实钉钉文档）

**⚠️ 严禁将日报保存为本地 `.md` 文件。必须调用 `dws doc create` 创建钉钉云文档。**

```bash
# 创建钉钉文档（返回 JSON 含 docUrl 字段）
dws doc create \
  --title   "老板日报-${TODAY}" \
  --content "${REPORT_MARKDOWN}" \
  -f json 2>/dev/null
```

执行后：
1. 从返回 JSON 中提取 `.docUrl`（或 `.url` / `.webUrl`）字段
2. 将文档链接直接输出给用户，格式为：
   > ✅ 日报已创建：[老板日报-{TODAY}]({docUrl})
3. 若 `doc create` 命令返回"即将推出"错误，则尝试备用方案：
   ```bash
   dws doc space list -f json   # 先获取文档空间ID
   dws doc create --space-id "{SPACE_ID}" --title "老板日报-${TODAY}" --content "${REPORT_MARKDOWN}" -f json
   ```
4. 所有备用方案均失败时，才将日报 Markdown 输出到对话中，并告知用户原因

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| `dws` 未登录 | 提示执行 `dws auth login` 后重试，不继续执行 |
| 服务"即将推出"（🔜） | 跳过该数据源，在日报对应章节注明"暂无数据" |
| 无今日数据 | 章节写"今日暂无此类数据"，不省略章节 |
| 文档创建失败（所有方式） | 将日报 Markdown 输出到对话中，说明原因，提醒用户手动建文档 |
| **输出为本地 .md 文件** | **严禁此行为**，必须创建钉钉云文档 |

## 执行示例

```bash
# 完整执行序列（由 AI 逐步调用）
dws auth status -f json                          # → 取 .name 作为老板姓名
dws minutes list --start-time "2026-04-03 08:00:00" --end-time "2026-04-03 22:00:00" -f json
dws minutes get --minutes-id "xxx" -f json
dws doc list -f json
dws doc get --doc-id "xxx" -f json
dws aitable list -f json
dws aitable record list --table-id "xxx" -f json
# AI 汇总生成日报 Markdown（严格按模板，数据概览在末尾）
dws doc create --title "老板日报-2026-04-03" --content "..." -f json
# → 输出: ✅ 日报已创建：[老板日报-2026-04-03](https://...)
```

**最终输出给用户的格式（不是文件路径，是可点击的钉钉文档链接）：**
```
✅ 老板日报已生成并写入钉钉文档：
👉 老板日报-2026-04-03：https://doc.dingtalk.com/xxx
```

## 注意事项

- `minutes`、`doc` 在 dws v1.0.0 标注为"🔜 即将推出"，若命令不存在则跳过
- `aitable` 已标注为 ✅ 可用
- 所有命令统一使用 `-f json` 以便 AI 解析
- 时间参数格式：`YYYY-MM-DD HH:mm:ss`

## 参考文档

- DWS CLI 分析报告：`/Users/wangchang/Desktop/Sirius/Draft/DingTalk_CLI_Analysis_Report.md`
- 日报模版：`/Users/wangchang/Desktop/WSYCursorCode/skills/PolaWukong/pola-daily-info-summery/module.md`
