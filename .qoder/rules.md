** 第一性原理思考： **
```
---
description: CRITICAL -  First Principles Thinking
alwaysApply: true
---
# MANDATORY:  First Principles Thinking
Don't be evil.
运用第一性原理 思考，拒绝经验主义和路径盲从，不要假设我完全清楚目标，保持审慎，从原始需求和问题出发，若目标模糊请停下和我讨论，若目标清晰但路径非最优，请直接建议更短、更低成本的办法。

所有回答必须分为两个部分： 
• ​直接执行：按照我当前的要求和逻辑，直接给出任务结果。
• ​深度交互：基于底层逻辑对我的原始需求进行“审慎挑战”。包括但不限于：质疑我的动机是否偏离目标（XY问题）、分析当前路径的弊端、并给出更优雅的替代方案。

```

**详细版（强烈推荐，防止 Opus 等模型偷偷调用）：**

```
---
description: CRITICAL - 完全禁止 subagent 使用，避免 Composer 模型降级和额外计费
alwaysApply: true
---
# MANDATORY: DO NOT SPAWN SUBAGENTS
你**绝对不能**使用 Task 工具或任何方式启动 subagent。
无论任务多复杂，都必须自己在主上下文中直接处理：
- 代码搜索 → 直接用 Glob / Grep / SemanticSearch / Read
- 运行命令 → 直接用 Shell
- 浏览器操作 → 直接用 MCP 工具
- 其他复杂任务 → 自己搞定，不要委托
- 此规则**无任何例外**。永不启动 subagent，永不使用 Task 工具。
```

```
---
description: CRITICAL - 完全遵循最小化和单一原则，降低coding复杂度
alwaysApply: true
---
# MANDATORY: One File, One Job, Clear Name.

- 实现高内聚低耦合的代码
- 一个源文件尽量不超过300行，最多不超过400行
- 加新功能时，如果发现要改的那个文件已经很长，就新建一个文件（
- 一个文件只做一类事
- 一个页面组件文件里，只放「这个页面的壳子」和少量状态
- 具体一块UI（比如播放器、侧边栏、分享弹窗）放到单独组件文件。
- 一个后端路由文件里，只放「一类接口」（例如只做「文档上传与导入」或只做「文档CRUDJ）
- 命名和文件夹能看出「是什么功能」
- 同一功能的前端东西尽量放在同一目录（例如 document-study/ 下有页面、子组件、hooks）。
- 整体架构设计支持DDD架构完整有分层且合理
- 模块化端点可拆分	
- 统一异常处理
- 启动模块清晰完整
- 健康检查及测试套件完整
- 相应业务的扩展性和前端钩子留好
```

```
---
description: CRITICAL - 让人类能看懂代码
alwaysApply: true
---
# MANDATORY: Coding 让人类友好

- 每个文件头增加文件注释，需要包含：模块名称、功能描述、创建日期、作者、主要变更（日期和内容）、依赖模块
- 核心功能需要注释清楚：功能的业务规则说明、算法逻辑、参数和返回值说明、边界条件和特殊情况、外部依赖和 API 说明、性能考量说明（时间、空间复杂度）
```
