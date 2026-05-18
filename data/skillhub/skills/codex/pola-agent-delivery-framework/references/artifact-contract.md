# Pola 跨阶段产物契约

## 目标

让每个 `pola-` skill 输出能被下一个阶段直接使用的结构化证据，减少重复解释和上下文丢失。

## 统一字段

每个阶段输出尽量包含：

```markdown
**阶段**
- 名称：
- 状态：Done / Partial / Blocked
- 输入：
- 输出：
- 证据：
- 风险：
- 下一步：
```

## 阶段产物

### 项目画像

```markdown
artifact: project-context
fields:
  root:
  git:
  stack:
  commands:
    dev:
    test:
    lint:
    typecheck:
    build:
  docs:
  deploy:
  risks:
```

### 需求分析

```markdown
artifact: requirement
fields:
  title:
  goal:
  users:
  inputs:
  outputs:
  non_goals:
  assumptions:
  acceptance:
  risks:
  open_questions:
```

### 架构文档

```markdown
artifact: architecture-plan
fields:
  title:
  affected_modules:
  data_flow:
  api_changes:
  file_plan:
  test_strategy:
  deploy_plan:
  rollback_plan:
  acceptance_mapping:
```

### 实现摘要

```markdown
artifact: implementation
fields:
  changed_files:
  acceptance_mapping:
  decisions:
  tests_added:
  risks:
```

### Review 结论

```markdown
artifact: review
fields:
  status:
  findings:
  fixed:
  test_gaps:
  residual_risks:
```

### 测试证据

```markdown
artifact: test-evidence
fields:
  status:
  commands:
  results:
  failures:
  skipped:
  coverage_notes:
```

### 集成回归证据

```markdown
artifact: regression-evidence
fields:
  status:
  environment:
  paths:
  ids:
  screenshots:
  logs:
  risks:
```

### 发布清单

```markdown
artifact: release-plan
fields:
  status:
  commits:
  surfaces:
  pre_checks:
  deploy_steps:
  post_checks:
  rollback:
```

### 收尾记录

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

## 状态语义

- `Done`：阶段目标完成，证据可复查。
- `Partial`：完成一部分，但仍有非阻塞缺口。
- `Blocked`：缺口会影响下一阶段，必须先处理或让用户接受风险。

## Blocker 写法

```markdown
**Blocker**
- 阶段：
- 阻塞原因：
- 影响：
- 需要谁做什么：
- 可替代方案：
```
