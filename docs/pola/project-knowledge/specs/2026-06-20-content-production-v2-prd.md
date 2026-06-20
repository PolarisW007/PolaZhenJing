# PRD：PolaZhenJing 内容生产升级 v2

## 1. 产品目标

把 PolaZhenJing 从“上传素材后直接风格改写”推进到“研究先行的作者型写作系统”。

本轮只交付 v2.1 的工程底座：

- 参考项目能力地图。
- 实时信号摘要标准结构。
- 去 AI 味审稿报告生成器。
- 本地项目知识记录与交付 ledger。

## 2. 用户流程

1. 作者输入主题与草稿。
2. 系统从近 30 天研究结果归一化出信号摘要。
3. 审稿模块对草稿做启发式检查。
4. 作者看到“中文腔调 / 结构套路 / 证据缺口 / 作者感缺口 / 可删句”。
5. 作者根据报告继续人工修稿或调用后续 LLM 流程。

## 3. 页面与交互范围

- 本轮不新增前端页面。
- 工具以 CLI 和文档工件交付：
  - `scripts/content_production_v2.py capability-map`
  - `scripts/content_production_v2.py signal-summary`
  - `scripts/content_production_v2.py review`

## 4. 核心行为

### 4.1 能力地图

- 输出 11 个上游项目到业务阶段的映射。
- 需覆盖：实时信号研究、去 AI 味规则库、风格品味、作者蒸馏、检测辅助、提示词增强、全链路写作。

### 4.2 实时信号摘要

- 输入：source JSON 数组。
- 输出字段：
  - `topic`
  - `sources`
  - `clusters`
  - `controversies`
  - `links`
  - `missing_sources`
  - `status`
- 当来源不可用或没有链接时，必须进入 `missing_sources`。

### 4.3 去 AI 味审稿报告

- 至少检查：
  - 中文套话和 filler phrases。
  - `首先/其次/最后` 模板结构。
  - 是否缺具体场景切口。
  - 是否缺链接、数字、时间点等证据锚点。
  - 是否缺第一人称判断。
- 报告输出 Markdown，供后续贴进项目文档或发布复盘。

## 5. 兼容要求

- 不改变既有上传页、风格选择页、图片生成和 Git 同步行为。
- 不读写 `.env`、token、cookie 到生成产物。
- 不自动修改现有 `_posts` 内容。

## 6. 验收

- 命令可运行并生成确定性输出。
- 单测覆盖 signal summary、review heuristics 和 CLI。
- 项目文档与需求池记录保持一致。
