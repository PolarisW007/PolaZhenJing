---
layout: deep-technical
theme: claude
title: "用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些“最佳实践”，但它们无法复用："
date: 2026-05-05
tags: []
summary: "![用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些“最佳实践”，但它们无法复用： — cover]({{ site.baseurl }}/assets/images/generated/yong-ai-xie-dai-ma-yi-duan-shi-jian-hou-wo-fa-xian-yi-ge-hen/cover.png)做了几年开发，用 AI 写代码也算有些时日了。"
---

![用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些“最佳实践”，但它们无法复用： — cover]({{ site.baseurl }}/assets/images/generated/yong-ai-xie-dai-ma-yi-duan-shi-jian-hou-wo-fa-xian-yi-ge-hen/cover.png)

# 用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些"最佳实践"，但它们无法复用

---

做了几年开发，用 AI 写代码也算有些时日了。从最初的新鲜尝试，到现在几乎离不开它，这个过程让我积累了不少经验。

我发现自己在不同项目里反复做着同样的事情：调教 AI、设定规则、优化 prompt。每次换一个新项目，或者换一个新的 AI 工具，一切都要从头开始。就像打游戏，每次都从第一关重新开始，之前的"攻略"没法带进新游戏。

这种感觉说不上多痛苦，但总觉得哪里不对。

直到有一天，我突然想明白了一个问题：为什么代码可以用 Git 管理、可以用 NPM 分发，而我的 AI 规范还停留在"复制粘贴"的阶段？

---

## 问题的本质：我们把规则当成了"文本"

回想一下我们平时的做法：

- 在 A 项目里精心调教 Prompt，让 AI 学会了某种代码风格
- 把这个 Prompt 复制到 B 项目
- 发现 AI 完全不记得之前学到的"规矩"
- 重新开始调教……

周而复始。

这不是工具的问题，也不是 AI 的问题。这是我们对待"AI 规则"的方式本身出了问题——我们一直把规则当作"文本"，而不是"代码"。

代码之所以能成为工程资产，是因为它具备三个核心能力：

**可组合**（Composable） → 不同规则可以拆分、复用  
**可分发**（Distributable） → 像 npm 包一样安装  
**可演进**（Versioned） → 有版本、有变更记录

如果 AI 规则也具备这三个能力，它就能从"碎片化经验"变成"可管理的工程资产"。否则，一个规范如果不能被 install，那它本质上就只是不成体系的经验。

---

## Skill 的最小抽象模型

那问题来了：一个"可安装的 AI 规范"，在工程上到底长什么样？

我探索出来的最小结构其实非常简单：

```
my-skill/
├── SKILL.md
├── rules/
├── package.json
```

但真正的关键不是结构，而是它解决的问题。

### 1️⃣ rules 目录：让 AI"分块理解"

我们传统的做法是把所有规则写在一个巨大的 prompt 里。但这会带来三个问题：

- **上下文污染**：规则太多，AI 记不住重点
- **规则冲突**：不同规则之间互相矛盾
- **记忆漂移**：AI 在长对话中逐渐"忘记"规则

![用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些“最佳实践”，但它们无法复用： — scene]({{ site.baseurl }}/assets/images/generated/yong-ai-xie-dai-ma-yi-duan-shi-jian-hou-wo-fa-xian-yi-ge-hen/scene-1.png)


拆分之后，结构就清晰了：

- behavior rules：开发行为约束
- optimization rules：代码质量优化规则

AI 不再"理解一坨规则"，而是按职责加载对应的规则上下文。就像微服务架构一样，每个规则模块各司其职。

### 2️⃣ SKILL.md：让 AI 知道"自己在哪个体系里"

这是我自己趟过的坑：AI 最大的问题不是不会写代码，而是不知道"当前的约束体系是什么"。

SKILL.md 本质上是一个"运行时契约"：

```yaml
name: project-core-standards
description: 项目的核心代码规范、行为准则与架构要求
version: 1.0.0
author: Admin
```

它定义的不是规则内容，而是规则系统的身份边界。就像每个 npm 包都有自己的 name 一样，这个文件告诉 AI：这个规则的"名字"是什么，它属于哪个体系。

### 3️⃣ package.json：从"规则文件"升级为"能力模块"

一旦进入 npm 体系，一切都变了。

从"文档"变成"可安装能力"——这个描述可能有点抽象，但实际效果非常直接：

**同一套规则，可以适配所有主流 AI 编程环境。**

这意味着不再是"适配工具"，而是"统一规则源"。你定义一次规则，然后可以选择要为哪些工具生成对应的配置文件。

---

## 真实使用方式：一行命令安装自定义 skills

这套自定义的 skills 最终是这样被使用的：

```bash
npx project-core-standards init
```

执行后，会进入一个交互式初始化流程：

```less
Welcome to Project Core Standards Setup

Please select the IDEs you want to generate rules for:
[1] Cursor (.cursorrules)
[2] Windsurf (.windsurfrules)
[3] Antigravity / Gemini (GEMINI.md)
[4] GitHub Copilot (.github/copilot-instructions.md)
[5] Cline / Roo Code (.clinerules)
[6] Codex (.codexrules)
[A] All of the above

![用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些“最佳实践”，但它们无法复用： — scene]({{ site.baseurl }}/assets/images/generated/yong-ai-xie-dai-ma-yi-duan-shi-jian-hou-wo-fa-xian-yi-ge-hen/scene-2.png)


Enter your choices (e.g., 1,3 or A):
```

这一步的意义非常关键——同一套规则，可以无缝适配所有主流 AI 编程环境。规则定义一次，自动适配多个工具。

---

## 最终 Skill 的形态

最终，我把这套系统封装成了一个 npm 包：project-core-standards。它的核心结构非常轻量：

```yaml
name: project-core-standards
description: 项目的核心代码规范、行为准则与架构要求。适用于所有需要编写代码、重构或进行代码审查的场景。
version: "1.0.0"
author: "Admin"
```

### 两个核心规则

Skill 的真正价值，不是结构，而是规则本身。

**规则一：Agent 行为与全局开发规范**

涵盖核心开发底线：

- commit 规范化（Conventional Commits）
- pnpm 作为唯一包管理方式
- Vue 项目结构约束
- TypeScript 强制类型约束
- 数据库变更必须可追踪
- 组件必须可复用、不可重复造轮子

这个规则解决的是：AI 写代码"失控"的问题。它就像一道"护栏"，确保 AI 的输出始终在项目允许的范围内。

**规则二：代码简化与优化专家原则**

核心目标：在保持功能不变的前提下优化代码质量。

原则包括：

- 优先简化逻辑，而不是增加抽象
- 删除重复代码，而不是复制模式
- 提升可读性优先于"设计模式正确性"
- 避免过度工程化
- 保持结构一致性

这个规则解决的是：AI 过度设计或复杂化代码的问题。AI 很喜欢"炫技"，这个规则就是给它设一个边界——简洁比花哨更重要。

---

## 真正的难点：无损同步机制

分发不是问题，问题是：**如何更新规则，而不破坏项目已有的定制？**

![用 AI 写代码一段时间后，我发现一个很反直觉的问题：我们其实已经有一些“最佳实践”，但它们无法复用： — scene]({{ site.baseurl }}/assets/images/generated/yong-ai-xie-dai-ma-yi-duan-shi-jian-hou-wo-fa-xian-yi-ge-hen/scene-3.png)


这是我自己设计系统时，花了最多时间思考的部分。

核心设计是 **Marker**：

```xml
<!-- BEGIN: project-core-standards -->
<!-- END: project-core-standards -->
```

同步逻辑：

- **有 marker → 精准替换区块**，只更新你定义的内容
- **无 marker → 自动安全注入**，不影响项目原有配置

本质是：局部 patch，而不是文件 overwrite。

工程实现有几个关键点：

- 使用 INIT_CWD 定位真实项目路径
- install 阶段自动触发同步
- 基于 AST + regex 做安全替换

核心思想是：**把 Git 的 diff 能力，搬进 AI 规则系统**。

每次更新规则，不会覆盖你项目的自定义配置，而是像 git merge 一样，精准地合并变更。

---

## 结语：当规则变成基础设施

引入 project-core-standards 后，开发流程变成了：

**以前**：

```
新项目 → prompt 调教 → 规则迁移 → 人工同步
```

**现在**：

```
npx init → 自动生成规则体系
```

当 AI 成为开发流程的一部分，一个新的层级出现了：

- **应用代码层**——你的业务代码
- **工程工具层**——构建、测试、部署
- **AI 规则层（Skill）**——AI 行为的"配置"

而 Skill 的意义是：**让 AI 行为本身，变成可工程化管理的资产**。

这不是在讲概念。这是在解决一个我们每天都在经历的、真实的痛点。

如果你也在为 AI 规则无法复用而困扰，不妨试试这个思路：把规则当代码看，给它结构、给它版本、给它分发能力。

也许很快，"调教 AI"这件事，就会变得和 npm install 一个包一样简单。