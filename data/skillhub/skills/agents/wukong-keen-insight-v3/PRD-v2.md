# 千里眼 v2 —— 群聊知识萃取工具 产品需求文档（PRD）

> 作者：王畅 · 2026-04-08
> 技能标识：wukong-keen-insight-v2
> 版本：v2.0 Draft
> 基于：wukong-keen-insight v1 架构演进

---

## 一、产品概述

### 1.1 背景与演进动机

v1 版千里眼采用三步式执行架构（脚本预处理 → Agent 分类 → 脚本后处理），全流程由 11 个 Python 模块 + LangGraph 编排完成。实际运行中发现两个核心痛点：

| 痛点 | 具体表现 |
|------|---------|
| **沙盒超时** | 悟空沙盒执行上限 300 秒，全流程（642 个群采集 + LLM 分类 + 写表）需 5~10 分钟，必然超时 |
| **架构过重** | 分类、排序、写表、通知全用 Python 实现，但悟空 Agent 本身具备 LLM 推理 + dws 工具调用能力，重复造轮子 |

v2 的设计哲学：**脚本只做 Agent 做不了的事（批量 dws 消息采集），其余全部交给 Agent**。

### 1.2 产品定位

**千里眼 v2** 是一个轻量化的群聊消息采集技能。脚本仅负责通过 dws CLI 批量拉取群消息并写入本地 Markdown 文件；后续的语义分析、智能分类、多维表写入和用户通知全部由悟空 Agent 利用自身 LLM 能力和 dws 工具链完成。

### 1.3 v1 → v2 架构对比

| 维度 | v1 | v2 |
|------|-----|-----|
| 脚本职责 | 采集 + 预处理 + 分类 + 排序 + 写表 + 通知 | **仅采集 + 写文件** |
| LLM 依赖 | 脚本内调用 OpenAI 兼容 API（或 Agent 中转） | **无**（Agent 自有 LLM） |
| 编排引擎 | LangGraph StateGraph（11 个模块） | **无**（单脚本，线性流程） |
| 分类排序 | Python 代码实现双维度模型 | **Agent 按 SKILL.md prompt 模板完成** |
| 多维表写入 | Python subprocess 调用 dws | **Agent 直接调用 dws 工具** |
| 通知 | Python 生成 use_channel payload | **Agent 直接构建通知** |
| Python 依赖 | langgraph, httpx, openai | **仅标准库**（json, subprocess, pathlib） |
| 典型执行时间 | 5~10 分钟（全流程） | **1~3 分钟**（仅采集） |

### 1.4 核心价值

| 价值维度 | 描述 |
|---------|------|
| **极致轻量** | 脚本零第三方依赖，仅用标准库完成采集 |
| **沙盒友好** | 采集脚本可在 300 秒内完成，不再超时 |
| **Agent 原生** | 充分利用悟空 Agent 的 LLM 推理和工具调用能力 |
| **可维护性** | 单文件脚本 < 400 行，逻辑透明 |
| **业务一致** | 延续 v1 的双维度优先级模型和多维表字段规范 |

### 1.5 一句话描述

> 脚本拉群消息写成 Markdown，Agent 读文件做分析写表格发通知。

---

## 二、功能架构

### 2.1 数据流全景

```
钉钉群聊
  │
  │ dws CLI 批量采集
  ▼
[Python 脚本] ── 写入 → chat-group-message-{timestamp}.md
  │
  │ stdout 输出文件路径
  ▼
[悟空 Agent]
  ├── 读取 Markdown 文件
  ├── LLM 语义分析 + 双维度分类 + 排序
  ├── dws 写入钉钉多维表（AI 表格）
  └── 通知用户（AI 表格链接 + 群 Summary）
```

### 2.2 职责边界

| 角色 | 职责 | 不做什么 |
|------|------|---------|
| **Python 脚本** | dws 群搜索、消息拉取、写 Markdown 文件 | 不做分类、不做排序、不写表、不通知 |
| **悟空 Agent** | 读文件、LLM 分析、dws 写表、构建通知 | 不做批量 dws 命令调用（沙盒限制） |

---

## 三、Python 脚本功能定义

### 3.1 输入参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--customer` | 客户名（必选） | 环境变量 `DINGTALK_CUSTOMER` |
| `--user` | 用户名（多维表命名用） | 环境变量 `KEEN_USER_NAME` |
| `--group-keywords` | 群搜索关键词（`,` `/` `\|` 分隔，最多 10 个） | 内置默认关键词 |
| `--date` | 目标日期（YYYY-MM-DD / 今天 / 昨天 / 前天） | 今天 |
| `--week` | 周范围查询（本周 / 上周） | 无 |
| `--start-date` / `--end-date` | 自定义时间段 | 无 |
| `--out-dir` | 输出目录 | `{技能根}/out` |
| `--skip-env-check` | 跳过环境自检 | false |

> 时间范围互斥优先级：`--week` > `--start-date/--end-date` > `--date`
> 最远支持 T-7 天历史数据。

### 3.2 群消息采集逻辑

复用 v1 的 dws 调用模式，但简化为单文件实现：

1. **群搜索**：按关键词逐个调用 `dws chat search --query "{keyword}" -f json`，支持自动分页（hasMore + nextCursor），合并去重（按 openConversationId）
2. **消息拉取**：遍历每个群，调用 `dws chat message list --group "{group_id}" --time "{date} 00:00:00" -f json`，支持自动分页
3. **内置默认关键词**：`["悟空", "开放平台", "FY27", "大客户", "战略", "ATH"]`（与 v1 保持一致）
4. **关键词上限**：最多 10 个，支持 `,` `/` `|` 三种分隔符

### 3.3 Markdown 输出文件

**文件命名**：`chat-group-message-{yyyy-MM-dd-HH-mm-ss}.md`

**文件结构**：

```markdown
# 群聊消息采集报告

- 客户：{customer}
- 采集人：{user}
- 采集时间：{datetime}
- 目标日期：{date_label}
- 搜索关键词：{keywords}
- 群数量：{group_count}
- 消息总数：{message_count}

---

## 群：{group_name_1}

> 群 ID：{group_id_1} | 消息数：{msg_count}

### {sender_1} ({timestamp_1})

{message_content_1}

### {sender_2} ({timestamp_2})

{message_content_2}

---

## 群：{group_name_2}

> 群 ID：{group_id_2} | 消息数：{msg_count}

### {sender_1} ({timestamp_1})

{message_content_1}

...
```

**设计要点**：
- 每个群以二级标题 `## 群：{name}` 分隔，便于 Agent 按群解析
- 每条消息以三级标题 `### {sender} ({timestamp})` 标记，保留发言人和时间
- 群之间用 `---` 分隔线隔开
- 文件头包含采集元信息，Agent 可直接读取上下文
- 纯 Markdown 格式，Agent 原生可读，无需额外解析库

### 3.4 stdout 输出协议

脚本执行完成后，通过 stdout 输出关键信息供 Agent 读取：

```
KEEN_MESSAGE_FILE:{absolute_path_to_md_file}
```

Agent 通过识别 `KEEN_MESSAGE_FILE:` 前缀获取文件路径。

### 3.5 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功，已生成消息文件 |
| 0 | 成功但无消息（文件仍生成，内容标注"无消息"） |
| 1 | 参数错误（缺少 --customer 等） |
| 2 | 环境检查失败（dws 不可用等） |

---

## 四、Agent 处理逻辑（SKILL.md 中定义）

Agent 读取脚本输出的 Markdown 文件后，按以下业务逻辑处理：

### 4.1 消息分析与分类

延续 v1 的双维度优先级模型：

**分类标签**（8 类）：需求讨论 / 问题反馈 / 技术方案 / 项目进展 / 商务沟通 / 行业动态 / 日常沟通 / 待办跟进

**价值维度**（Value）：

| 标签 | 权重 | 判定标准 |
|------|------|---------|
| 市场机会 | 5 | 客户需求、产品机会、潜在商机、新场景发现 |
| 竞争情报 | 4 | 竞争对手被提及、竞品对比讨论 |
| 决策讨论 | 3 | 方案选型、技术决策、资源分配 |
| 风险预防 | 3 | 风险识别、Bug 预警、客户不满信号 |
| 知识共享 | 1 | 行业动态、经验交流、一般信息同步 |

**紧急程度**（Urgency）：

| 标签 | 权重 | 判定标准 |
|------|------|---------|
| 立即响应 | 5 | @指定任务、风险预警、线上故障 |
| 关键待办 | 4 | 明确 Todo、有截止日期、需确认 |
| 适时跟进 | 2 | 机会挖掘、方案推进 |
| 信息同步 | 1 | 日常同步、闲聊 |

**综合得分** = 价值权重 × 紧急权重：高(≥12) / 中(4-11) / 低(≤3)

### 4.2 Top 36 排序规则

1. 综合得分降序
2. 同分按时间倒序（最新优先）
3. 高优先级全部保留
4. 中优先级最多 24 条
5. 低优先级填充到 36 条为止
6. 总数不足 36 则全部输出

### 4.3 多维表写入

Agent 通过 dws 工具创建/写入钉钉多维表（AI 表格）。**所有多维表操作统一走 dws CLI。**

**已有多维表配置**（优先复用）：base-id = `nYMoO1rWxmP7olkyFQExjRR9V47Z3je9`，table-id = `TbEXpjZ`。

**写入命令**：`dws aitable record create --base-id X --table-id Y --records '[...]' --format json`

**分批策略**：每批 20 条，任一批次失败立即中止。

**权限注意**：`aitable.record:create` 为中风险权限，首次调用需用户在悟空客户端手动授权（错误码 `PAT_MEDIUM_RISK_NO_PERMISSION`）。建议写入前先用测试记录验证权限。

**表名规范**：`{用户名}-群消息洞察-{YYYY-MM-DD}`（多日：`{用户名}-群消息洞察-{起始}~{结束}`）

**字段定义**（与 v1 完全一致）：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 日期 | 日期 | 情报日期 yyyy-MM-dd |
| 排名 | 数字 | 1-36 |
| 优先级 | 单选 | 高 / 中 / 低 |
| 综合得分 | 数字 | 价值权重 × 紧急权重 |
| 价值维度 | 单选 | 市场机会 / 竞争情报 / 决策讨论 / 风险预防 / 知识共享 |
| 紧急程度 | 单选 | 立即响应 / 关键待办 / 适时跟进 / 信息同步 |
| 分类 | 单选 | 8 类之一 |
| 群名 | 文本 | 来源群名称 |
| 一句话摘要 | 文本 | 50 字以内的核心摘要 |
| 建议解决方案 | 长文本 | 高/中优先级必填 |
| 关键行动 | 文本 | Action Item（可为空） |
| 当前状态 | 单选 | 被识别 / 解决中 / 已解决 / 已抛弃（默认：被识别） |
| 发送人 | 文本 | 核心发言人 |
| 消息时间 | 日期时间 | 原始消息时间 |
| 原始内容 | 长文本 | 完整消息内容（上限 5000 字） |
| 置信度 | 数字 | 分类置信度 0-1 |

### 4.4 用户通知

Agent 分析完成后，向用户发送通知：

```markdown
亲爱{客户}老板：
📊  千里眼播报 — {yyyy-MM-dd}

目前共萃取 {total} 条情报：
- 🔴 高优先级 {high_count} 条
- 🟡 中优先级 {mid_count} 条
- 🟢 低优先级 {low_count} 条

**高优先级 Top 5：**
1. [{分类}] {一句话摘要} — {群名}
2. [{分类}] {一句话摘要} — {群名}
3. [{分类}] {一句话摘要} — {群名}
4. [{分类}] {一句话摘要} — {群名}
5. [{分类}] {一句话摘要} — {群名}
**高风险 Top 5：**
1. [{分类}] {一句话摘要} — {群名}
2. [{分类}] {一句话摘要} — {群名}
3. [{分类}] {一句话摘要} — {群名}
4. [{分类}] {一句话摘要} — {群名}
5. [{分类}] {一句话摘要} — {群名}
📋 完整情报已更新至多维表：{AI表格链接}
```

---

## 五、技术架构

### 5.1 技术选型

| 组件 | v1 选型 | v2 选型 | 变更理由 |
|------|--------|--------|---------|
| 流程编排 | LangGraph StateGraph | **无（线性脚本）** | 脚本只做采集，无需复杂编排 |
| 群消息采集 | dws CLI + subprocess | **dws CLI + subprocess** | 保持不变 |
| LLM 调用 | OpenAI 兼容协议 | **无** | Agent 自有 LLM 能力 |
| 数据存储 | Python → dws 多维表 | **Agent → dws 多维表** | Agent 直接调用 dws 工具 |
| 通知 | Python use_channel | **Agent 构建通知** | Agent 原生能力 |
| Python 依赖 | langgraph, httpx, openai | **无第三方依赖**（Python 3.9+） | 仅标准库 |

### 5.2 目录结构

```
wukong-keen-insight-v2/
├── SKILL.md              # 技能元数据 + Agent 执行协议 + 分类 prompt
├── PRD-v2.md             # 本文档
├── requirements.txt      # Python 依赖（仅标准库声明）
├── scripts/
│   ├── run.py            # 主入口（兼容悟空调用协议）
│   └── fetch_and_save.py # 群消息采集 + Markdown 写入（单文件实现）
└── out/
    └── .gitkeep
```

> 从 v1 的 11 个 Python 文件精简为 **2 个**（run.py + fetch_and_save.py）。

### 5.3 脚本模块设计

**`fetch_and_save.py`**（~720 行，单文件完整实现，含分批拉取 + 权限预检查 + 连续失败快退）：

```
模块结构：
├── 常量定义
│   ├── _DEFAULT_KEYWORDS: 内置默认搜索关键词
│   └── _MAX_KEYWORDS: 关键词上限 10
├── 环境检查
│   ├── _find_dws(): 定位 dws 可执行文件
│   └── _check_env(): 检查必要环境（dws 可用性）
├── 日期处理
│   ├── _parse_date(): 解析中文日期（今天/昨天/前天）
│   ├── _resolve_date_range(): 解析时间范围参数
│   └── _validate_range(): T-7 天限制校验
├── dws 调用
│   ├── _run_dws(): 通用 dws 命令执行器
│   ├── _search_groups(): 按关键词搜索群（自动分页）
│   └── _fetch_messages(): 拉取单群消息（自动分页）
├── Markdown 生成
│   └── _write_markdown(): 生成结构化 Markdown 文件
├── CLI 参数解析
│   └── _parse_args(): argparse 参数定义
└── 主流程
    └── main(): 入口函数
```

**`run.py`**：悟空平台入口适配器，调用 `fetch_and_save.main()`。

---

## 六、环境变量

### 6.1 必选

| 环境变量 | 用途 |
|---------|------|
| `DINGTALK_CUSTOMER` | 客户名（也可通过 `--customer` 参数指定） |

### 6.2 可选

| 环境变量 | 用途 | 默认值 |
|---------|------|--------|
| `DWS_EXECUTABLE` | dws 可执行文件路径 | PATH 中自动查找 |
| `DWS_CHAT_SEARCH_CMD` | 群搜索命令模板 | `dws chat search --query {query} -f json` |
| `DWS_FETCH_MESSAGES_CMD` | 消息拉取命令模板 | `dws chat message list --group {group_id} --time {time} -f json` |
| `DWS_GROUP_QUERIES` | 群搜索关键词（逗号分隔） | 内置默认关键词 |
| `KEEN_USER_NAME` | 用户名（多维表命名用） | 无 |
| `KEEN_TOP_N` | 情报条数上限 | 36 |

> 相比 v1 减少了 LLM 相关（KEEN_LLM_*）和多维表写入相关（KEEN_SHEET_*）的环境变量，因为这些功能由 Agent 直接完成。

---

## 七、运行协议

### 7.1 Agent 调用脚本

```bash
"/path/to/python" "/path/to/wukong-keen-insight-v2/scripts/run.py" \
  --customer "某集团" \
  --user "张三" \
  --group-keywords "开放平台,大客户,悟空" \
  --date "今天"
```

### 7.2 Agent 处理脚本输出

1. Agent 执行脚本，从 stdout 捕获 `KEEN_MESSAGE_FILE:{path}`
2. Agent 读取该 Markdown 文件
3. Agent 按 SKILL.md 中的分类 prompt 模板进行 LLM 分析
4. Agent 调用 dws 创建多维表并写入 Top 36 情报
5. Agent 向用户发送通知（含 AI 表格链接 + 群 Summary）

### 7.3 执行时序图

```
Agent                        Python 脚本                    dws CLI
  │                              │                             │
  │── 调用 run.py ──────────────▶│                             │
  │                              │── search groups ──────────▶│
  │                              │◀── group list ─────────────│
  │                              │── fetch messages ─────────▶│
  │                              │◀── messages ───────────────│
  │                              │                             │
  │                              │── 写入 Markdown ──▶ 文件系统
  │                              │                             │
  │◀── KEEN_MESSAGE_FILE:path ───│                             │
  │                              │                             │
  │── 读取 Markdown 文件 ──────▶ 文件系统                      │
  │◀── 文件内容 ──────────────── 文件系统                      │
  │                              │                             │
  │── LLM 分析（Agent 自有）     │                             │
  │                              │                             │
  │── dws 写多维表 ────────────────────────────────────────────▶│
  │◀── 表格链接 ──────────────────────────────────────────────│
  │                              │                             │
  │── 通知用户 ──▶ 用户                                        │
```

---

## 八、验收标准

1. 脚本在 300 秒内完成消息采集并生成 Markdown 文件
2. Markdown 文件格式正确，Agent 可直接读取解析
3. 零第三方依赖，仅使用 Python 标准库
4. 脚本代码单文件 ~720 行（含分批拉取、权限预检查、连续失败快退等健壮性逻辑），结构清晰
5. 支持 v1 的全部时间范围参数（单日/周/自定义/T-7 限制）
6. 支持 v1 的全部群搜索能力（关键词/分页/去重）
7. stdout 输出 `KEEN_MESSAGE_FILE:` 信号供 Agent 读取
8. 无消息时仍生成文件（标注"无消息"），退出码 0

---

## 九、后续演进

| 阶段 | 能力 | 价值 |
|------|------|------|
| v2.1 | 增量采集：记录上次采集位置，避免重复拉取 | 提升效率，减少 dws 调用 |
| v2.2 | 消息预过滤：脚本侧过滤系统消息/纯表情/短消息 | 减小 Markdown 文件体积，提升 Agent 分析效率 |
| v2.3 | 多格式输出：支持 JSON 格式（`--format json`） | 适配非 Agent 场景 |
| v2.4 | 与 url-convert-dingtalk-context 联动 | 群内链接自动抓取入库 |
