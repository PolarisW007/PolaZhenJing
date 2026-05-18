---
name: pola-agent-delivery-framework
description: Pola 通用需求交付总控 skill。用于把一个软件需求从项目读取、需求分析、架构文档、编码、代码 review、单元测试、集成测试、部署、回归测试、开发日志到 git 提交串成闭环。触发词包括 pola 交付框架、自动化需求到发布、完整开发流水线、从需求到部署、全链路 agent skill、开发总控、需求实现并测试部署提交。
---

# Pola Agent Delivery Framework

## 目标

把一个需求交付到“有文档、有代码、有 review、有测试证据、有部署计划、有回归结论、有开发日志、有 git 收尾”的状态。

本 skill 是总控入口，只做编排和门禁判断。具体阶段优先交给同套 `pola-` skill：

- `pola-project-context-reader`
- `pola-requirement-analyzer`
- `pola-architecture-doc-writer`
- `pola-implementation-runner`
- `pola-code-review-gate`
- `pola-test-gate`
- `pola-integration-regression-gate`
- `pola-deploy-release-gate`
- `pola-devlog-git-finalizer`

如果项目中已有更具体的 skill，例如需求池、发布、部署、HTML app 验证、开发日志或 git 提交 skill，优先复用具体 skill，不重复实现。

## 输入形态

接受以下任一输入：

- 一段自然语言需求。
- 手写图、白板图、截图、会议纪要。
- 现有 PRD、issue、需求池记录或任务链接。
- “修复这个 bug”“把这个需求做完”“开发并部署”这类目标型指令。
- 已经存在的代码 diff，需要补 review、测试、发布和日志闭环。

如果输入只包含模糊目标，例如“优化一下”“做个自动化”，先进入需求分析，不直接编码。

## 产物目录约定

优先使用项目已有文档目录；没有约定时使用下面路径：

```text
docs/
├── pola/
│   ├── requirements/YYYY-MM-DD-需求短名.md
│   ├── architecture/YYYY-MM-DD-需求短名.md
│   ├── test-reports/YYYY-MM-DD-需求短名.md
│   └── release/YYYY-MM-DD-需求短名.md
└── requirement_delivery_logs/YYYY-MM/YYYY-MM-DD-需求短名.md
```

如果项目不适合写入 `docs/`，例如当前目录是 skill 仓库或用户只要规划，则把产物保留在本轮回复或当前 skill 对应目录。

跨阶段产物字段见 `references/artifact-contract.md`。总控应尽量让每个阶段输出符合该契约，方便后续阶段直接接续。

阶段门禁细则见 `references/workflow-gates.md`。当某阶段状态不清楚时，优先按该文件判断是否能进入下一阶段。

## 执行模式

- **Plan only**：只生成需求、架构、测试和发布计划，不改代码。
- **Implement**：完成代码和最小测试，但不部署。
- **Ship ready**：完成代码、review、测试、发布清单和 git 收尾。
- **Deploy**：在用户明确要求并确认风险后执行部署和回归。

默认根据用户话术判断：说“规划”则 Plan only；说“开发完成”则 Implement 或 Ship ready；说“部署上线”才进入 Deploy。

## 总控流程

1. **读取项目上下文**
   - 使用 `pola-project-context-reader` 识别技术栈、目录、文档、测试命令、部署方式和现有约束。
   - 输出项目画像和可执行命令候选。
   - 如果不是 git 仓库，后续 git 收尾只生成建议，不执行 commit。

2. **需求分析**
   - 使用 `pola-requirement-analyzer` 处理用户描述、图片、文件、会议记录或已有 issue。
   - 输出需求口径、用户目标、非目标、验收标准、风险和待澄清项。
   - 若验收标准不明确，不进入编码。
   - 若需求涉及外部文档、法律、价格、模型规格或 API 最新行为，先查官方来源。

3. **架构开发文档**
   - 使用 `pola-architecture-doc-writer` 生成架构计划。
   - 必须覆盖模块影响、数据流、接口、文件改动、测试策略、部署面、回滚点。
   - 小修小补可以写轻量方案；跨模块、数据、部署、计费、权限变更必须写完整方案。

4. **编码实现**
   - 使用 `pola-implementation-runner`。
   - 先读现有代码模式，再小步修改。
   - 不做无关重构，不覆盖用户未提交改动。
   - 每次修改后维护“验收项 -> 文件 -> 验证方式”的映射。

5. **代码 review**
   - 使用 `pola-code-review-gate`。
   - 先列 bug、回归风险、测试缺口和安全问题，再决定是否修复。
   - P0/P1 未解决时不能进入发布准备，除非用户明确接受风险。

6. **测试门禁**
   - 使用 `pola-test-gate`。
   - 至少运行最小相关测试；无法运行时记录 blocker 和原因。
   - 测试失败时优先修复本次引入的问题；历史失败需说明与本次改动的关系。

7. **集成与回归**
   - 使用 `pola-integration-regression-gate`。
   - 覆盖真实用户路径、UI、API、历史记录、下载、计费或日志等项目相关链路。
   - bugfix 必须包含原始失败 case 的回归验证。

8. **发布与部署**
   - 使用 `pola-deploy-release-gate`。
   - 生成或更新发布清单，明确部署命令、环境、回滚和发布后验证。
   - 生产改动必须逐步确认，不把高危命令串联执行。
   - 如果没有部署权限或环境不可用，输出可执行部署 runbook。

9. **日志与 git 收尾**
   - 使用 `pola-devlog-git-finalizer`。
   - 更新开发日志、CHANGELOG 或需求状态，审阅 diff，执行 commit/push 前检查。
   - commit/push 只有在用户要求时执行；否则保留为建议。

## 门禁规则

- 没有验收标准，不编码。
- 没有架构计划，不做跨模块改动。
- 没有 review 结论，不进入发布准备。
- 没有测试证据，不声称完成。
- 没有部署和回滚说明，不声称可上线。
- 没有回归证据，不把需求标记为已上线。
- 有未解决 P0/P1 review 问题，不进入 release。
- 生产环境命令没有用户确认，不执行。

## 失败处理

- **需求不清**：输出最少必要澄清问题，并给出当前可确认部分。
- **项目不可识别**：列出已发现文件和需要用户提供的启动/测试命令。
- **测试失败**：区分本次引入、环境问题、历史失败；能修就修，不能修就记录 blocker。
- **部署受阻**：输出 runbook、所需权限、预期命令、回滚命令和验证项。
- **git 不可用**：生成变更摘要和建议 commit message，不声称已提交。

## 阶段状态记录

总控执行时维护一个简短状态表：

```markdown
| 阶段 | 状态 | 产物 | 备注 |
| --- | --- | --- | --- |
| 项目画像 | Done | docs/pola/... |  |
| 需求分析 | Blocked |  | 缺少验收标准 |
```

总控最终应汇总一个 `delivery-summary` 产物，其中引用各阶段 artifact：

```markdown
artifact: delivery-summary
fields:
  project_context:
  requirement:
  architecture_plan:
  implementation:
  review:
  test_evidence:
  regression_evidence:
  release_plan:
  finalization:
```

## Harness 回归

当本框架自身被修改时，使用本地 harness 做回归：

```bash
./pola-agent-delivery-framework/scripts/validate_pola_skills.py
```

该 harness 检查：

- 每个 `pola-` skill 的必要章节。
- reference 文件是否存在并包含关键内容。
- 各阶段是否显式输出 artifact。
- scripts 是否可执行且语法正确。
- 开发计划是否覆盖全部 skill。

如果 harness 失败，先修复失败项，再运行 `quick_validate.py` 做 frontmatter 基础校验。

## 最终汇报

最终回复使用以下结构：

```markdown
**交付结论**
- 完成 / 未完成 / 阻塞

**产物**
- 需求分析
- 架构文档
- 代码变更
- Review 结论
- 测试证据
- 发布和回归结论
- 开发日志和 git 状态

**阻塞或风险**
- 明确未完成项、原因和下一步
```
