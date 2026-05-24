# 更新日志：超级小王记忆与人格系统

本文件记录 `超级小王` 记忆、人格、后台、搜索、更新感知和部署验证的用户可见变化。PRD/SDD 记录产品与技术设计，Release/Delivery 文档记录发布与验收，本文件作为持续演进的产品更新日志。

## 2026-05-23

### Added

- 新增微信私域数据补充方案：`WECHAT_PERSONA_PRD.md`、`WECHAT_PERSONA_SDD.md`、`WECHAT_PERSONA_HARNESS.md`。
- 设计 Owner 聊天风格提炼、好友画像数据库、私域证据链、工作台审核、隐私边界和发布回滚流程。
- 新增 Harness 文档门禁项 `H43-H48`，校验微信补充方案是否覆盖文档、Owner 风格门槛、好友画像 schema、隐私边界、PolaAIBrain 复用和无聊天原文泄露。

### Verification

- `scripts/run_memory_harness.py` 本地通过，包含 `H43-H48`。

## 2026-05-23

### Added

- 新增运行版本自我感知：小王在被问到“最近是否更新”“新增了什么能力”“当前版本是什么”时，可以基于运行环境说明当前 commit、最近更新摘要和相关交付文档。
- 新增运维验收接口：`GET /PolaZhenjing/admin/api/agent/release/status`，用于确认当前运行 commit、分支、提交标题、提交时间和最近 release/delivery 文档。
- 新增 `H36-release-awareness` Harness 用例，覆盖小王是否能感知更新、是否避免暴露密钥/系统提示词/服务器绝对路径。
- 新增产品更新日志文件，作为后续每次小王升级的固定记录入口。

### Changed

- Chat system context 增加短版 release awareness，仅在用户询问更新、版本、部署或新增能力时使用，不替代记忆检索和人格规则。
- 发布清单、交付日志、PRD 和 SDD 增加产品更新日志入口，避免功能上线后只散落在测试报告或 commit 里。
- 本地、GitHub、服务器已在更新感知发布后同步到 `d07fa70 docs: 记录小王更新感知发布验证`；后续文档补记会产生新的文档提交。

### Verification

- 本地 `python -m py_compile app/release_awareness.py app/agent.py` 通过。
- 本地 `pytest`：10 passed。
- 本地 `scripts/run_memory_harness.py`：Pass，包含 `H36-release-awareness`。
- 远端 `pytest`：10 passed。
- 远端 `scripts/run_memory_harness.py`：Pass，包含 `H36-release-awareness`。
- 线上 `/PolaZhenjing/admin/api/agent/release/status` 返回 200。
- 线上 `/PolaZhenjing/admin/api/agent/chat` 询问“你刚刚被更新了吗？”返回 200，小王能说明自己新增了更新感知能力。

### Commits

- `884c2cf feat: 增加超级小王更新感知`
- `d07fa70 docs: 记录小王更新感知发布验证`

## 2026-05-23

### Changed

- 将本地、GitHub、服务器代码线重新对齐，服务器 `/PolaZhenjing` 使用 GitHub `main` 作为部署基线。
- 补充项目规则与参考资料同步记录，保留 `AGENTS.md`、`.qoder/rules.md` 与超级小王记忆工程文档之间的约束关系。
- 明确后续实现继续以 PostgreSQL typed ledger 为事实源，pgvector/Meilisearch 作为可重建索引或搜索投影。

### Verification

- GitHub `main`、本地仓库、服务器 `/PolaZhenjing` 均同步到同一代码线。
- `polazj.service` active。

### Commits

- `24fc09f docs: 同步项目规则与参考资料`

## 2026-05-22

### Added

- 新增 PostgreSQL typed memory ledger，作为超级小王记忆事实源。
- 新增 `raw_events`、`memory_items`、`memory_candidates`、`visitor_suggestions`、`audit_logs`、`search_outbox` 等结构，支持来源、版本、状态、可信度、审计和后续索引重建。
- 新增 Owner/visitor 身份区分：Owner 账号可确认式写入和管理记忆，访客建议进入 suggestion/candidate 流程。
- 新增记忆管理后台 `/PolaZhenjing/admin/agent/memory`，支持状态查看、搜索、候选记忆审核、访客建议处理、编辑和状态治理。
- 新增记忆搜索 API、写入治理、投毒扫描、NUL 字节清洗、JSON fallback 和 Meilisearch outbox。
- 新增旧记忆和文章导入能力：`data/agent_memory.json` 作为 bootstrap source，`_posts/*.md` 可导入为文章记忆来源。
- 下载并阅读 `referene/TencentDB-Agent-Memory`，将其 L0/L1/L2/L3 分层、RRF 混合召回、短期任务日志 offload、Mermaid canvas 和 HostAdapter 解耦思想纳入本项目文档。

### Changed

- 记忆系统架构从“静态 JSON + 关键词召回”升级为“PostgreSQL 事实账本 + 可治理写入 + 后续 pgvector/Meilisearch 投影”的渐进式方案。
- 明确向量数据库不是人格事实源；pgvector、Meilisearch、Qdrant、Tencent Cloud VectorDB、Mem0/mem9/EverOS 只能作为索引、搜索体验或评估对照。
- PRD/SDD/Harness 文档更新为 PostgreSQL 优先、pgvector Phase 2、Meilisearch Phase 3 的路线。

### Verification

- 本地 `py_compile` 通过。
- 本地 `pytest`：9 passed。
- 本地 `scripts/run_memory_harness.py`：Pass。
- 线上 `/PolaZhenjing/admin/api/agent/memory/status` 返回 200，`backend=postgres`、`enabled=true`。
- 线上 `/PolaZhenjing/admin/api/agent/memory/search?q=Agent` 返回 200。
- 线上 `/agent.html` 和 `/PolaZhenjing/admin/api/agent/chat` 回归通过。
- 远端导入旧记忆 `4387` 条，文章记忆 `33` 条；线上状态记录为 `memory_items=4420`、`raw_events=4422`、`candidates=4411`、`visitor_suggestions=0`。

### Commits

- `1b14052 docs: 更新超级小王记忆架构方案`
- `ab506e7 feat: 升级超级小王记忆系统`
- `d44943c docs: 记录超级小王部署验证`
- `c98cc15 fix: 启用超级小王 PostgreSQL 记忆账本`
