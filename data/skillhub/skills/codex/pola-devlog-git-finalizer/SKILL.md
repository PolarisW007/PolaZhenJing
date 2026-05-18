---
name: pola-devlog-git-finalizer
description: Pola 开发日志与 git 收尾 skill。用于需求完成后更新开发日志、CHANGELOG、交付记录、需求状态、审阅 diff、检查密钥和临时代码、生成中文 commit 信息并在用户确认后提交或 push。触发词包括开发日志、devlog、提交 git、commit、push、收尾、更新日志、提交前检查、需求状态回填。
---

# Pola Devlog Git Finalizer

## 目标

把开发结果变成可追踪的工程记录，并在 git 提交前做最后一轮卫生检查。

## 输入

- 需求分析和验收标准。
- 架构文档。
- 实现摘要。
- review 结论。
- 测试和回归证据。
- 发布清单或部署结论。
- 当前 git diff。

## 默认流程

1. 读取本次需求、架构文档、测试证据、发布结论。
2. 更新开发日志或交付记录。
3. 判断是否需要 CHANGELOG 或 release manifest。
4. 审阅 `git status` 和 `git diff`。
5. 检查密钥、个人路径、调试输出、临时文件和无关改动。
6. 生成中文 commit message。
7. 用户要求并确认后执行 commit 或 push。

## 复用建议

如果项目中存在更具体的 skill，优先使用：

- `pola-devlog-writer`：根目录开发日志。
- `local-git-commit-push`：本地提交、env 加密、CHANGELOG 和 push 检查。
- `requirements-management`：需求池状态和备注回填。
- `release-readiness-coordinator`：发布清单和部署前后证据。

## 文档更新规则

| 文档 | 何时更新 |
| --- | --- |
| 开发日志 | 完成一个开发节点、commit、里程碑或用户明确要求 |
| CHANGELOG | 用户可见功能、行为变化、重要 bugfix、发布版本 |
| 交付记录 | 需求有验收、测试证据、发布证据 |
| Release manifest | 即将部署、多 commit、生产 bugfix、配置/计费/环境改动 |
| 需求池 | 有需求记录、PRD、状态流转或上线回填 |

纯内部文档或 skill 修改通常不需要需求池，但需要开发日志或提交说明。

## Diff 卫生检查

提交前必须检查：

- 是否有密钥、token、cookie、私钥、`.env` 明文。
- 是否有个人绝对路径、临时目录、机器名。
- 是否有 `console.log`、`debugger`、`print`、TODO 临时代码。
- 是否有大型二进制、生成产物、缓存文件、`.DS_Store`。
- 是否有无关格式化或误删。
- 是否遗漏新增文件。

## Commit 准备

1. `git status --short` 确认文件范围。
2. `git diff --stat` 看改动规模。
3. `git diff` 抽查关键文件。
4. 运行最终测试或引用已有测试证据。
5. 生成中文 commit message。
6. 用户确认后 `git add`、`git commit`。
7. 用户确认 remote/branch 后 `git push`。

如果当前目录不是 git 仓库，只输出变更清单和建议 commit message。

## 输出

```markdown
artifact: finalization

**收尾结论**
- 开发日志：
- CHANGELOG：
- 需求状态：
- git 状态：
- commit：
- push：

**提交前检查**
- 密钥：
- 临时代码：
- 无关改动：
- 测试证据：
```

## Commit 规则

- 默认中文 commit message。
- 标题简洁说明用户可见变化或工程目的。
- 正文列出核心变更和验证命令。
- 不把未验证项写成已完成。

## Commit message 模板

```text
feat: 完成 Pola 需求交付 skill 框架

- 新增需求分析、架构文档、编码、review、测试、发布、收尾阶段 skill
- 补充项目识别和质量门禁脚本
- 验证：quick_validate.py 全部通过；bash -n 脚本通过
```

## 完成标准

- 文档记录与实际改动一致。
- git diff 已审阅。
- 没有明显不应提交文件。
- commit/push 状态如实说明。

## Artifact 字段

```markdown
artifact: finalization
fields:
  devlog:
  changelog:
  requirement_status:
  git_status:
  commit:
  push:
```
