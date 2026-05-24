# Harness 校验：微信私域数据、Owner 风格与好友画像补充方案

更新时间：2026-05-23

本 Harness 用 Agent Harness Engineering 的七层框架检查 `WECHAT_PERSONA_PRD.md` 和 `WECHAT_PERSONA_SDD.md`：

- E: Execution environment，执行环境和本地数据边界。
- T: Tool interface and protocol，导入/API/工作台接口。
- C: Context and memory management，风格、好友画像和上下文注入。
- L: Lifecycle and orchestration，导入、抽取、审核、发布、回滚。
- O: Observability and operations，任务状态、错误、审计。
- V: Verification and evaluation，测试、门禁、Harness。
- G: Governance and security，隐私、权限、反投毒、敏感推断。

## Round 1: 数据源是否被正确边界化

检查：

- 是否识别 `contacts.json`、`contacts_list.txt`、`chats/private`、`chats/groups`。
- 是否明确本轮不导入原文。
- 是否区分通讯录、单聊、群聊、群话题。

结论：Pass。PRD/SDD 只描述结构和规模，不展示聊天原文。

## Round 2: Owner 风格是否和核心人格分开

检查：

- Owner 风格候选不能直接覆盖 `persona_versions`。
- 核心价值观仍以 Owner 审批和 Harness 为门槛。
- 场景风格和全局风格分开。

结论：Pass。SDD 设计 `owner_style_versions` 和 persona diff 发布流程。

## Round 3: 好友画像是否和超级小王人格分开

检查：

- 好友画像不直接进入 active memory。
- 只有 Owner 查询相关好友时召回。
- 访客不能访问，也不透露好友是否存在。

结论：Pass。PRD/SDD 都明确 social profile 是私域知识层。

## Round 4: PolaAIBrain 遗产是否被合理复用

检查：

- 复用 customers/messages/profiles/insights/tags 的结构思想。
- 拒绝重型 FastAPI/Next/Milvus 直接搬迁。
- 与现有 PolaZhenJing Flask/Postgres 工作台一致。

结论：Pass。采用轻量 schema 扩展方案。

## Round 5: 数据模型是否可审计

检查：

- 是否有 import_run、contacts、conversation、message、subject、profile、candidate、evidence、audit。
- 每个候选字段是否有 evidence_refs。
- 是否支持版本和状态。

结论：Pass。SDD 覆盖核心表和状态。

## Round 6: 抽取是否防止误判

检查：

- explicit_self_claim、owner_statement、third_party_statement、behavioral_inference 分层。
- 群聊无法归属时不进入个人画像。
- 玩笑、反讽、转述降置信。

结论：Pass。

## Round 7: 隐私和敏感推断是否有硬边界

检查：

- 原文默认 owner_private。
- 敏感推断默认 pending_sensitive。
- 原文不进入 Meilisearch，不进入普通 prompt。

结论：Pass。

## Round 8: 工作台是否覆盖人工治理

检查：

- 导入、我的风格、好友画像、社交洞察四个 Tab。
- 支持搜索、合并、编辑、删除、证据抽屉。
- 原文展开需要二次确认。

结论：Pass。

## Round 9: 发布和回滚是否完整

检查：

- feature flag 默认关闭。
- 备份、dry-run、小范围导入、Harness、Owner 发布。
- 可回滚 active style version 和 archived social profiles。

结论：Pass。

## Round 10: 可自动校验项是否进入脚本

检查：

- `scripts/run_memory_harness.py` 增加 H43-H48。
- 检查文档存在、关键 schema、隐私边界、PolaAIBrain 复用和无聊天原文泄露。

结论：Pass，脚本校验作为本轮最终门禁。

## 总结评分

| 维度 | 分数 | 说明 |
| --- | --- | --- |
| E | 4 | 明确本地导出目录、dry-run、feature flag |
| T | 4 | API 和工作台入口完整 |
| C | 5 | Owner 风格、好友画像、核心人格三层分离 |
| L | 5 | 导入、抽取、审核、发布、回滚闭环 |
| O | 4 | import_run、parse_status、audit、search jobs |
| V | 4 | 文档 Harness 已落脚本，后续实现需加单测 |
| G | 5 | Owner-only、敏感推断禁区、反投毒和不泄露原文 |

本轮补充方案满足“先方案和文档，必须 Harness 校验”的要求。
