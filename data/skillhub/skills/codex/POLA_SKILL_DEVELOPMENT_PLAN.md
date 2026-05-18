# Pola Agent Skill Framework 开发计划

## 目标

构建一套以 `pola-` 为前缀的通用 Agent skill 框架，把一个软件需求从输入、分析、架构设计、编码、review、测试、部署、回归、开发日志到 git 提交串成可重复的工程流水线。

## 设计原则

- 总控只编排，不把所有细节塞进一个大 skill。
- 阶段 skill 只负责一个质量门禁，输出可被下一阶段复用的证据。
- 优先读取项目已有文件和命令，不凭空假设技术栈。
- 每个阶段都要能写清：输入、动作、输出、阻塞条件。
- 部署和生产改动必须有发布清单、回滚点和回归证据。

## Skill 清单

| Skill | 职责 |
| --- | --- |
| `pola-agent-delivery-framework` | 总控编排，从需求到提交的主入口 |
| `pola-project-context-reader` | 读取项目目录、技术栈、命令、文档和约束 |
| `pola-requirement-analyzer` | 把文字、图片、文件和现有上下文转成需求与验收标准 |
| `pola-architecture-doc-writer` | 生成架构开发文档、数据流、接口、风险和测试策略 |
| `pola-implementation-runner` | 按计划编码，保持改动范围和项目风格一致 |
| `pola-code-review-gate` | 对 diff 做工程 review、安全检查和规范检查 |
| `pola-test-gate` | 发现并运行单测、类型检查、lint 和最小相关测试 |
| `pola-integration-regression-gate` | 做集成、UI、真实链路和回归验证 |
| `pola-deploy-release-gate` | 发布就绪检查、部署计划、回滚和线上验证 |
| `pola-devlog-git-finalizer` | 更新开发日志、变更记录、commit 和 push 前检查 |

## 推荐执行顺序

1. `pola-project-context-reader`
2. `pola-requirement-analyzer`
3. `pola-architecture-doc-writer`
4. `pola-implementation-runner`
5. `pola-code-review-gate`
6. `pola-test-gate`
7. `pola-integration-regression-gate`
8. `pola-deploy-release-gate`
9. `pola-devlog-git-finalizer`

## 交付标准

- 每个 skill 有独立 `SKILL.md`。
- 关键通用动作有脚本或 reference 支撑。
- 所有 skill 通过 `quick_validate.py` 基础校验。
- 总控 skill 能指挥其它阶段 skill，并给出缺口和 blocker。
- 使用 `pola-agent-delivery-framework/scripts/validate_pola_skills.py` 作为 harness，检查章节完整度、reference 存在性、artifact 契约、脚本权限和脚本语法。

## 第二轮补全重点

- 总控补充输入形态、执行模式、产物目录、失败处理和阶段状态表。
- 项目画像补充读取范围、命令发现规则、风险字段和 monorepo 处理。
- 需求分析补充需求质量标准、分类、澄清问题规则和验收标准写法。
- 架构文档补充完整设计步骤、方案取舍、文件改动表、测试策略和存放规则。
- 编码执行补充代码阅读方法、改动粒度、脏文件处理、测试同步和验收映射。
- Review 门禁补充专项矩阵、review 方法、严重程度处理和 pass 条件。
- 测试门禁补充测试选择规则、失败分类、证据记录和进入下一阶段条件。
- 集成回归补充真实链路设计、前端浏览器验证、API 验证、bugfix 回归和部署后回归。
- 发布部署补充发布面判断、发布前 checklist、部署执行规则、回滚要求和 Ready 判定。
- 收尾补充文档更新规则、diff 卫生检查、commit 准备和 commit message 模板。

## Harness 校对流程

每次改动 skill 后按顺序执行：

```bash
./pola-agent-delivery-framework/scripts/validate_pola_skills.py

for d in pola-agent-delivery-framework pola-project-context-reader pola-requirement-analyzer pola-architecture-doc-writer pola-implementation-runner pola-code-review-gate pola-test-gate pola-integration-regression-gate pola-deploy-release-gate pola-devlog-git-finalizer pola-devlog-writer; do
  /tmp/pola-skill-validate-venv/bin/python yun-skills/skill-creator/scripts/quick_validate.py "$d"
done

bash -n pola-project-context-reader/scripts/detect_project.sh
bash -n pola-project-context-reader/scripts/collect_context.sh
bash -n pola-test-gate/scripts/run_quality_gates.sh
```

Harness 必须无失败、无警告；`quick_validate.py` 必须全部通过；脚本语法检查必须通过。
