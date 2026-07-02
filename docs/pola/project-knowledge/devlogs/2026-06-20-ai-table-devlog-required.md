# 开发日志：AI 表格开发日志同步必选化

## 目标

将“本地开发日志必须同步到钉钉 AI 表格”写入 Pola 项目的强制开发流程，避免后续需求交付只更新本地文档而遗漏线上项目日志。

## 改动

- 更新全局 Pola A2A 收尾规则：`pola-devlog-git-finalizer` 增加 AI 表格同步门禁。
- 更新全局 Pola 总控规则：`pola-agent-delivery-framework` 的 Phase 8 收尾必须包含 devlog AI 表格同步。
- 更新 PolaZhenJing 项目规则和项目知识库 README。
- 同步更新 PolaUUH 项目规则和项目知识库 README。

## 验收

- 后续 Pola 项目只要更新开发日志，就必须同步到钉钉开发日志文件夹：
  `https://alidocs.dingtalk.com/i/nodes/DnRL6jAJMGQ0Xgd6uql3NodwWyMoPYe1`
- AI 表格开发日志视图必须回填具体来源文件：
  `https://alidocs.dingtalk.com/i/nodes/np9zOoBVBYOk2Ew6fPjEja5pW1DK0g6l?iframeQuery=entrance%3Ddata%26sheetId%3DhERWDMS%26viewId%3DqvGDAH2`
- 同步失败必须记录 blocker，不得把需求标记为完整收尾。

## 验证

- `validate_pola_skills.py`：PASS。
- `git diff --check -- AGENTS.md docs/pola/project-knowledge/README.md docs/pola/project-knowledge/devlogs/2026-06-20-ai-table-devlog-required.md`：PASS。
- AI 表格同步：已创建钉钉文档 `https://alidocs.dingtalk.com/i/nodes/Exel2BLV5zqxOrbaCPlmrPDYJgk9rpMq`，并更新 AI 表格 `PolaZhenJing` 记录的 `来源文件` 和 `功能汇总`。
- AI 表格 `更新内容`：已按“基于功能汇总整理”回填准确摘要；当前字段类型为 text，dws CLI 暂不支持通过 `field update` 暴露参数修改 AI 字段配置。

## 风险

- 当前 dws CLI 对部分 AI 字段运行能力暴露不完整；规则要求记录触发状态或 blocker，避免静默遗漏。
- 已尝试通过 `dws doc update --content/--content-file` 更新钉钉文档正文，但当前接口返回缺少 `markdown` 参数；线上文档正文如需补齐最终验证段落，需要等待 dws 文档更新参数映射修复或手动补充。
