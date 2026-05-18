# 智能排会助手 — PRD v1.0

> **Skill ID**: `wukong-meeting-assistant`
> **作者**: 王畅（福锤）
> **日期**: 2026-04-11
> **状态**: 待评审

---

## 一、产品概述

### 1.1 一句话定义

输入会议主题和参会人（支持 @人/@群/@部门），自动查询所有人闲忙状态，推荐最优时间段，一键创建日程并发送邀请；支持自然语言如"帮我找下周产品部和设计部都有空的1小时"。

### 1.2 目标用户

- 跨部门项目经理、团队 Leader、EA/行政助理
- 核心痛点：5人以上跨部门会议协调时间，平均耗时 15-30 分钟反复沟通

### 1.3 价值主张

| 维度 | 当前方式 | 使用本技能后 |
|------|----------|-------------|
| 协调耗时 | 15-30 分钟群里反复问 | **< 30 秒**一句话完成 |
| 会议室冲突 | 手动查空闲会议室 | 自动匹配推荐 |
| 信息遗漏 | 忘加参会人、忘发邀请 | 全自动闭环 |
| 改期成本 | 重复以上所有步骤 | "往后挪一天"即可 |

---

## 二、dws CLI 能力分析（核心依据）

### 2.1 能力矩阵

基于对 dws CLI 的逐一 `--help` 验证，以下是本技能所需全部命令及其覆盖状态：

| 能力需求 | dws 命令 | 关键参数 | 覆盖状态 |
|----------|----------|----------|----------|
| **闲忙查询** | `dws calendar busy search` | `--users userId1,userId2 --start ISO --end ISO` | ✅ 完全覆盖 |
| **创建日程** | `dws calendar event create` | `--title --start ISO --end ISO --desc` | ✅ 完全覆盖 |
| **添加参会人** | `dws calendar participant add` | `--event EVENT_ID --users userId1,userId2` | ✅ 完全覆盖 |
| **搜索空闲会议室** | `dws calendar room search` | `--start ISO --end ISO --available --group-id` | ✅ 完全覆盖 |
| **预订会议室** | `dws calendar room add` | `--event EVENT_ID --rooms roomId1,roomId2` | ✅ 完全覆盖 |
| **会议室分组** | `dws calendar room list-groups` | 无额外参数 | ✅ 完全覆盖 |
| **按名搜人** | `dws contact user search` | `--query "姓名"` → 返回 userId | ✅ 完全覆盖 |
| **按部门展开成员** | `dws contact dept search` + `dept list-members` | `--query "部门名"` → deptId → `--ids deptId` | ✅ 两步组合 |
| **按群展开成员** | `dws chat search` + `chat group members` | `--query "群名"` → conversationId → `--id convId` | ✅ 两步组合 |
| **预约视频会议** | `dws conference meeting create` | `--title --start ISO --end ISO` | ✅ 覆盖（不关联日历） |
| **查询已有日程** | `dws calendar event list` | `--start ISO --end ISO` | ✅ 完全覆盖 |

### 2.2 能力 Gap 分析

| Gap 项 | 影响 | 解决方案 |
|--------|------|----------|
| `calendar event create` 不支持直接指定参会人 | 需两步：先创建日程 → 再 `participant add` | **可接受**，脚本串联即可 |
| `conference meeting create` 不关联日历日程 | 视频会议和日程是两个独立实体 | 分别创建后在日程描述中附带会议链接 |
| 闲忙查询需传 userId 列表，不支持传部门/群 | 需先展开成员再查闲忙 | 前置步骤：部门/群 → userId 列表 → 闲忙查询 |
| 闲忙查询返回的是"忙碌时段"，非"空闲时段" | 需要自行计算空闲窗口 | **技能核心算法**：反转忙碌时段得到空闲窗口 |
| 无法获取他人日历的详细事件（仅闲忙） | 无法展示冲突事件名称 | 可接受，隐私合理；只展示"忙碌/空闲" |

### 2.3 结论

> **dws CLI 完全能支撑本技能的全部核心功能。** 无需额外 OpenAPI 调用，所有能力均可通过 CLI 命令组合实现。唯一需要技能层自行实现的是"空闲窗口计算算法"和"自然语言时间解析"，这两块由悟空 LLM 推理层承担。

---

## 三、核心流程设计

### 3.1 主流程（Mermaid）

```mermaid
graph TD
    A[用户输入自然语言请求] --> B{解析意图}
    B --> C[提取: 主题 / 参会人 / 时长 / 时间范围 / 偏好]
    C --> D{参会人类型判断}
    D -->|@人名| E1[dws contact user search → userId]
    D -->|@群名| E2[dws chat search → convId → dws chat group members → userId列表]
    D -->|@部门| E3[dws contact dept search → deptId → dws contact dept list-members → userId列表]
    E1 --> F[合并去重所有 userId]
    E2 --> F
    E3 --> F
    F --> G[dws calendar busy search 批量查闲忙]
    G --> H[空闲窗口计算算法]
    H --> I{是否找到合适时段?}
    I -->|是| J[展示 Top-3 推荐时段]
    I -->|否| K[提示无共同空闲 + 建议放宽条件]
    J --> L{用户确认选择}
    L --> M[dws calendar event create 创建日程]
    M --> N[dws calendar participant add 添加参会人]
    N --> O{是否需要会议室?}
    O -->|是| P[dws calendar room search --available]
    P --> Q[dws calendar room add 预订会议室]
    O -->|否| R{是否需要视频会议?}
    Q --> R
    R -->|是| S[dws conference meeting create]
    R -->|否| T[完成 ✅ 输出确认摘要]
    S --> T
```

### 3.2 子流程：参会人解析与展开

```
输入示例: "帮我约 @福锤 @枫华 @开放平台 @悟空核心群 下周二下午的1小时会议"

解析结果:
├── 人名: ["福锤", "枫华"]           → dws contact user search
├── 部门: ["开放平台"]               → dws contact dept search → dept list-members
├── 群名: ["悟空核心群"]             → dws chat search → chat group members
├── 时间范围: 2026-04-14 12:00 ~ 18:00 (下周二下午)
├── 时长: 60 分钟
└── 主题: (由 LLM 根据上下文生成或用户补充)
```

### 3.3 子流程：空闲窗口计算

**输入**：每个 userId 的忙碌时段列表 + 目标时间范围 + 所需时长

**算法**：
1. 将目标时间范围按 **30 分钟粒度** 切分为 slot 数组
2. 遍历所有人的忙碌时段，标记被占用的 slot
3. 在剩余空闲 slot 中，找到 **连续 N 个 slot**（N = 所需时长 / 30）的窗口
4. 按以下优先级排序推荐：
   - **全员可参加** > 部分人可参加
   - **工作时间（9:00-18:00）** > 非工作时间
   - **上午 > 下午**（可配置）
   - **离当前时间越近越优先**

**输出**：Top-3 推荐时段，每个时段附带：
- 开始/结束时间
- 可参加人数 / 总人数
- 不可参加的人员名单（如有）

---

## 四、功能规格

### 4.1 输入格式

技能支持以下自然语言模式：

| 用户说法示例 | 解析目标 |
|-------------|----------|
| "帮我找下周 福锤 和 枫华 都有空的1小时" | 人名 + 时间范围 + 时长 |
| "约一个产品评审会，参会人是 @开放平台 全部门" | 主题 + 部门展开 |
| "帮我在悟空核心群里约个30分钟的站会" | 群展开 + 时长 |
| "下周三下午2-5点之间，找个大家都有空的时间开会" | 精确时间范围 |
| "帮我约会议室，6人，下周一上午" | 含会议室需求 + 人数 |
| "帮我约个视频会议，主题是Q2复盘" | 含视频会议需求 |

### 4.2 输出格式

#### 推荐阶段输出：

```
🗓 智能排会助手 — 推荐结果

📋 会议主题：Q2 产品复盘
👥 参会人（共6人）：福锤、枫华、先雄、毅珩、乐云、高安
⏱ 所需时长：60 分钟

推荐时段：
┌─────┬──────────────────────────┬──────────┬─────────────┐
│ 排名 │ 时段                      │ 可参加    │ 冲突人员     │
├─────┼──────────────────────────┼──────────┼─────────────┤
│ ⭐ 1 │ 周二 04/15 14:00 - 15:00 │ 6/6 全员 │ 无           │
│  2  │ 周三 04/16 10:00 - 11:00 │ 5/6      │ 枫华         │
│  3  │ 周四 04/17 15:00 - 16:00 │ 5/6      │ 毅珩         │
└─────┴──────────────────────────┴──────────┴─────────────┘

请选择时段（输入 1/2/3），或说"换个时间"重新查找。
```

#### 创建完成输出：

```
✅ 会议已创建！

📋 Q2 产品复盘
🕐 2026-04-15 周二 14:00 - 15:00
👥 参会人：福锤、枫华、先雄、毅珩、乐云、高安（已发送邀请）
🏢 会议室：杭州-西溪园区-6F-春风（8人间）
🔗 视频会议：已创建（会议号附在日程描述中）
```

### 4.3 交互模式

| 场景 | 行为 |
|------|------|
| 信息完整 | 直接查询闲忙 → 推荐 → 等待确认 |
| 缺少主题 | 追问"会议主题是什么？" |
| 缺少时间范围 | 默认查询"未来5个工作日 9:00-18:00" |
| 缺少时长 | 默认 60 分钟 |
| 无共同空闲 | 提示"6人在未来5个工作日无共同空闲"，建议放宽时间范围或减少必须参加人员 |
| 用户说"就第1个" | 执行创建流程 |
| 用户说"换个时间" | 重新提供时间范围约束 |
| 用户说"加个会议室" | 追加会议室搜索和预订 |
| 用户说"也约个视频会议" | 追加视频会议创建 |

---

## 五、数据模型

### 5.1 内部数据结构

```typescript
interface MeetingRequest {
  topic?: string;              // 会议主题
  participants: Participant[]; // 参会人列表
  duration: number;            // 时长（分钟），默认 60
  timeRange: {                 // 搜索时间范围
    start: string;             // ISO-8601
    end: string;               // ISO-8601
  };
  preferences: {
    needRoom: boolean;         // 是否需要会议室
    needVideo: boolean;        // 是否需要视频会议
    roomCapacity?: number;     // 会议室容量要求
    preferMorning?: boolean;   // 偏好上午
  };
}

interface Participant {
  source: 'user' | 'group' | 'department';
  rawInput: string;            // 原始输入，如 "@开放平台"
  resolvedUsers: {             // 展开后的用户列表
    userId: string;
    name: string;
  }[];
}

interface TimeSlot {
  start: string;               // ISO-8601
  end: string;                 // ISO-8601
  availableCount: number;      // 可参加人数
  totalCount: number;          // 总人数
  conflicts: string[];         // 不可参加的人员姓名
  score: number;               // 综合评分（排序用）
}

interface MeetingResult {
  eventId: string;             // 创建的日程 ID
  roomId?: string;             // 预订的会议室 ID
  roomName?: string;           // 会议室名称
  conferenceId?: string;       // 视频会议 ID
  participantIds: string[];    // 已添加的参会人
}
```

---

## 六、技术方案

### 6.1 执行链路（全部基于 dws CLI）

整个技能的执行链路由悟空 LLM 编排，所有钉钉操作通过 dws CLI 完成，无需额外 SDK 或 API 调用。

#### Step 1：参会人解析与展开

```bash
# @人名 → userId
dws contact user search --query "福锤" -f json
# 返回: { "userId": "026828", "name": "王畅" }

# @部门 → deptId → 成员列表
dws contact dept search --query "开放平台" -f json
# 返回: { "deptId": "12345", "name": "大客户&战略终端合作" }
dws contact dept list-members --ids 12345 -f json
# 返回: [{ "userId": "026828", "name": "王畅" }, ...]

# @群 → conversationId → 成员列表
dws chat search --query "悟空核心群" -f json
# 返回: { "openConversationId": "cidXXX" }
dws chat group members --id cidXXX -f json
# 返回: [{ "userId": "026828", "name": "王畅" }, ...]
```

#### Step 2：闲忙查询

```bash
# 批量查询所有参会人的闲忙状态
dws calendar busy search \
  --users "026828,userId2,userId3,userId4,userId5,userId6" \
  --start "2026-04-14T09:00:00+08:00" \
  --end "2026-04-18T18:00:00+08:00" \
  -f json
# 返回: 每个用户的忙碌时段列表
```

#### Step 3：空闲窗口计算（LLM 推理层）

由悟空 LLM 执行以下逻辑：
1. 解析每个用户的忙碌时段
2. 按 30 分钟粒度生成 slot 矩阵
3. 计算全员/多数人的连续空闲窗口
4. 按评分规则排序，输出 Top-3

#### Step 4：创建日程 + 添加参会人

```bash
# 创建日程
dws calendar event create \
  --title "Q2 产品复盘" \
  --start "2026-04-15T14:00:00+08:00" \
  --end "2026-04-15T15:00:00+08:00" \
  --desc "由智能排会助手自动创建" \
  -f json -y
# 返回: { "eventId": "evt_xxx" }

# 添加参会人
dws calendar participant add \
  --event evt_xxx \
  --users "026828,userId2,userId3,userId4,userId5,userId6" \
  -y
```

#### Step 5（可选）：预订会议室

```bash
# 搜索空闲会议室
dws calendar room search \
  --start "2026-04-15T14:00:00+08:00" \
  --end "2026-04-15T15:00:00+08:00" \
  --available \
  -f json
# 返回: 空闲会议室列表（含 roomId、名称、容量）

# 预订会议室
dws calendar room add --event evt_xxx --rooms room_xxx -y
```

#### Step 6（可选）：创建视频会议

```bash
dws conference meeting create \
  --title "Q2 产品复盘" \
  --start "2026-04-15T14:00:00+08:00" \
  --end "2026-04-15T15:00:00+08:00" \
  -f json -y
# 返回: 会议链接信息

# 注意：视频会议不自动关联日程
# 解决方案：将会议链接写入日程描述，或更新日程描述追加会议链接
```

### 6.2 技能文件结构

```
wukong-meeting-assistant/
├── PRD.md                    # 本文档
├── SKILL.md                  # 技能描述文件（悟空标准格式）
├── scripts/
│   └── free_slot_calc.py     # 空闲窗口计算脚本（可选，复杂场景用）
└── examples/
    ├── basic_meeting.md      # 基础排会示例
    ├── cross_dept.md         # 跨部门排会示例
    └── with_room.md          # 含会议室预订示例
```

### 6.3 SKILL.md 核心触发词

```
每当用户说「排会」「约会议」「找时间开会」「帮我约个会」「大家什么时候有空」
「安排会议」「协调会议时间」「查一下闲忙」「找个共同空闲」时应使用本技能。
```

---

## 七、边界 Case 与异常处理

### 7.1 参会人解析边界

| Case | 处理策略 |
|------|----------|
| 同名用户（如"张伟"返回多个结果） | 展示列表让用户选择，附带部门信息辅助区分 |
| 搜索不到用户 | 提示"未找到'xxx'，请确认姓名或花名" |
| 部门搜索返回多个匹配 | 展示列表让用户选择 |
| 群成员过多（>50人） | 提示"该群有 N 人，闲忙查询可能较慢，是否继续？" |
| 混合输入（人名+部门+群） | 分别解析，合并去重 userId |
| 参会人包含自己 | 自动包含当前用户（`dws contact user get-self`） |

### 7.2 时间解析边界

| Case | 处理策略 |
|------|----------|
| "下周" | 下周一 09:00 至 下周五 18:00 |
| "明天下午" | 明天 13:00 至 18:00 |
| "这周内" | 今天当前时间 至 本周五 18:00 |
| "尽快" | 今天剩余时间 + 未来 3 个工作日 |
| "下周二下午2-5点" | 精确范围：下周二 14:00-17:00 |
| 跨时区（暂不支持） | V1 默认 UTC+8，后续迭代支持 |

### 7.3 闲忙查询边界

| Case | 处理策略 |
|------|----------|
| 某用户未开启日历/无权限 | 将该用户标记为"无法查询闲忙"，不阻塞其他人 |
| 全员无共同空闲 | 退化为"最多人可参加"的推荐模式 |
| 查询范围过大（>2周） | 提示建议缩小范围，避免 API 超时 |
| 忙碌时段数据为空 | 视为全天空闲 |

### 7.4 创建日程边界

| Case | 处理策略 |
|------|----------|
| 日程创建失败 | 重试 1 次，仍失败则提示用户手动创建 |
| 参会人添加部分失败 | 报告成功/失败列表，不回滚已创建的日程 |
| 会议室被抢占（创建时已被占） | 提示"会议室已被占用"，推荐其他空闲会议室 |
| 用户取消操作 | 在确认前可随时取消，已创建的日程提供删除选项 |

---

## 八、安全与权限

| 维度 | 策略 |
|------|------|
| 闲忙数据 | 仅查询忙碌/空闲状态，不暴露具体事件内容（API 层已保证） |
| 通讯录权限 | 依赖 dws CLI 已配置的企业应用权限，无额外越权 |
| 日程创建 | 以当前用户身份创建，参会人会收到钉钉日程邀请通知 |
| 操作确认 | 创建日程前**必须**经用户确认，不自动执行（`--yes` 仅在用户确认后使用） |

---

## 九、迭代规划

### V1.0（本期）
- [x] 自然语言解析会议需求
- [x] @人名 → userId 解析
- [x] @部门 → 展开成员
- [x] @群 → 展开成员
- [x] 闲忙查询 + 空闲窗口计算
- [x] Top-3 推荐 + 用户确认
- [x] 创建日程 + 添加参会人
- [x] 会议室搜索 + 预订
- [x] 视频会议创建（可选）

### V1.1（后续）
- [ ] 周期性会议支持（每周例会）
- [ ] 会议改期（"往后挪一天"）
- [ ] 会议取消 + 通知
- [ ] 参会人偏好学习（某人偏好上午开会）
- [ ] 跨时区支持
- [ ] 与钉钉听记（闪记）联动——会后自动生成纪要

---

## 十、验收标准

### 10.1 功能验收

| # | 测试场景 | 预期结果 | 优先级 |
|---|---------|----------|--------|
| 1 | "帮我约福锤和枫华下周的1小时会议" | 正确解析人名、查询闲忙、推荐时段 | P0 |
| 2 | "约开放平台全部门下周二下午开会" | 正确展开部门成员、查询闲忙 | P0 |
| 3 | "在悟空核心群约个30分钟站会" | 正确展开群成员、查询闲忙 | P0 |
| 4 | 选择推荐时段后确认创建 | 日程创建成功、参会人收到邀请 | P0 |
| 5 | "加个会议室，6人" | 搜索空闲会议室并预订 | P1 |
| 6 | "也约个视频会议" | 创建视频会议并附在日程描述 | P1 |
| 7 | 同名用户消歧 | 展示列表让用户选择 | P1 |
| 8 | 全员无共同空闲 | 退化推荐 + 提示放宽条件 | P1 |
| 9 | 混合输入（@人+@部门+@群） | 正确合并去重 | P0 |
| 10 | 用户说"取消" | 不执行创建操作 | P0 |

### 10.2 性能要求

| 指标 | 目标 |
|------|------|
| 参会人解析 | < 5 秒（10人以内） |
| 闲忙查询 | < 10 秒（20人 × 5天） |
| 端到端（输入到推荐） | < 30 秒 |
| 日程创建到完成 | < 10 秒 |

---

## 附录 A：dws CLI 命令速查

```
# 通讯录
dws contact user search --query "姓名" -f json
dws contact user get-self -f json
dws contact dept search --query "部门名" -f json
dws contact dept list-members --ids deptId1,deptId2 -f json

# 群聊
dws chat search --query "群名" -f json
dws chat group members --id openConversationId -f json

# 日程
dws calendar busy search --users uid1,uid2 --start ISO --end ISO -f json
dws calendar event create --title "标题" --start ISO --end ISO --desc "描述" -f json -y
dws calendar event list --start ISO --end ISO -f json
dws calendar participant add --event eventId --users uid1,uid2 -y

# 会议室
dws calendar room list-groups -f json
dws calendar room search --start ISO --end ISO --available -f json
dws calendar room add --event eventId --rooms roomId1 -y

# 视频会议
dws conference meeting create --title "标题" --start ISO --end ISO -f json -y
```

---

> **文档结束。请评审后告知，我将进入 SKILL.md 和脚本实现阶段。**
