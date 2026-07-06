# 需求记录：洞察选题从新闻流升级为社媒运营选题蓝图

## 背景

用户反馈 `/PolaZhenjing/admin/insights/topics` 生成内容更多像 AI 新闻列表，不适合直接用于运营自己的社媒账号。目标不是搬运新闻，而是持续提炼 AI 行业中值得写、值得讨论、能形成账号观点的选题。

本轮设计输入来自近期行业共识：

- AI 价值从单点工具走向工作流和组织采用，选题应关注真实场景、流程变化和价值捕获。
- Agent 与自动化实践正在从 demo 进入工程化，选题应关注方法、边界、失败恢复和评估。
- 企业和个人账号的内容竞争不在速度，而在能否把公开信号转译成可复用判断、业务启发和实践复盘。

参考来源：

- McKinsey: The state of AI
- Microsoft WorkLab: Work Trend Index / Frontier Firm
- Anthropic: Building effective agents
- OpenAI Business: enterprise AI use cases

## 用户原始需求

> insights 的内容现在更多是新闻，我需要的不是新闻，而是整个行业对于 AI 的各种最新的场景使用、产品能力更新、好的业务模式、商业的思考、使用的最佳实践和实践过程的总结等，需要你整体全局思考，然后更新 topics 的生成机制，使得生成的 topics 适合我用于运营自己的社媒账号。Harness。

## 目标

- 将线上信号从“新闻标题来源”降级为“证据切口”。
- 生成的 topic 必须服务社媒运营，而不是复述事件。
- 每个 topic 输出明确内容赛道：
  - 场景使用；
  - 产品能力更新；
  - 业务模式；
  - 商业思考；
  - 最佳实践；
  - 实践复盘。
- 每个 topic 同时给出：
  - 社媒开场钩子；
  - 目标读者；
  - 核心问题；
  - 内容结构；
  - 来源信号标题和证据角色。
- 保持现有状态打标、一键导入上传、自动刷新和旧 JSON 数据兼容。

## 范围

- 修改 `app/insight_topics.py` 中信号到选题的生成、归类、排序、草稿生成逻辑。
- 修改 `app/templates/insight_topics.html`，让页面展示社媒运营蓝图字段。
- 更新 `tests/test_admin_workbench_insight_topics.py` 覆盖新生成机制。
- 补齐 A2A Harness 交付证据。

## 非目标

- 本次不接入新的大模型生成服务。
- 本次不改变外部信号采集源和请求频率。
- 本次不改 PolaNews 上游新闻数据结构。
- 本次不部署新的队列、cron 或 worker。
- 本次不发布到生产服务器，除非后续明确要求。

## 验收标准

- A1 选题定位：刷新生成的 topic 标题不能简单等于原始新闻/链接标题，应转译成社媒可写的洞察选题。
- A2 内容赛道：每个 topic 有 `content_lane` 和 `content_lane_label`，覆盖六类运营赛道之一。
- A3 社媒蓝图：每个 topic 有 `social_hook`、`target_audience`、`core_question`、`content_structure`。
- A4 证据角色：topic 保留原始信号标题和证据链接，但页面和底稿应把它作为证据，不作为新闻搬运主题。
- A5 导入成稿：一键导入上传生成的长稿应围绕运营蓝图展开，不暴露管理态来源、评分、状态等元信息。
- A6 兼容回归：旧种子数据、手动刷新、状态保留、历史回填、自动刷新锁不回归。
- A7 Harness：功能用例、测试矩阵、回归证据和 delivery state 覆盖 A1-A6。

## 风险等级

P2。改动影响后台选题生成和导入底稿，但不新增外部服务、不新增后台进程、不改变生产采集频率。通过兼容字段默认值、单测和 Harness 降低风险。
