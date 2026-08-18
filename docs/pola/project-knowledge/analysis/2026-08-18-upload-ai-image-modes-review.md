# Code Review：上传文章 AI 生图四档模式

日期：2026-08-18

## Review 结论

Pass。未发现未处理的 P0/P1；发现的 3 个 P2 已在本轮修复并增加回归测试。

## 上游与实现证据

- Requirement：`docs/pola/project-knowledge/requirements/2026-08-18-upload-ai-image-modes.md`
- PRD：`docs/pola/project-knowledge/specs/2026-08-18-upload-ai-image-modes-prd.md`
- SDD：`docs/pola/project-knowledge/architecture/2026-08-18-upload-ai-image-modes-sdd.md`
- 实现：`app/uploader.py`、`app/templates/upload.html`
- 测试：`tests/test_upload_image_modes.py`、`tests/test_upload_rewrite_rate.py`

## 发现与修复

| 严重度 | 发现 | 影响 | 修复 | 回归证据 |
| --- | --- | --- | --- | --- |
| P2 | 整批 deadline 原先在视觉规划 LLM 完成后才创建 | 最坏总时长可能超过文档约定 900 秒 | deadline 提前到视觉规划之前，T2I 单请求使用剩余预算 | `test_image_batch_budget_stops_before_new_api_calls` |
| P2 | 注入题图后仍把题图计入 source block index | 场景图可能插在目标正文段落之前 | 有题图时 source index 从 `-2` 开始，只排除生成题图，不排除原文媒体 | `test_cover_does_not_shift_original_scene_anchor` |
| P2 | T2I base64/URL 下载和整批二进制缺容量上限，错误日志含完整签名 URL | 详细模式可能放大内存/磁盘风险，日志可能泄露临时签名参数 | 响应 18MB、单图 12MB、批次 64MB；URL 分块读取并只记录 host | `test_image_batch_byte_budget_stops_before_writing_oversized_batch` |

## 验收覆盖

| 验收 | 代码 | 当前验证 | 结论 |
| --- | --- | --- | --- |
| A1 | upload 模板四档卡片与响应式 CSS | Flask 页面测试；Playwright 待运行 | 实现通过，UI 待回归 |
| A2 | parser/draft/payload/job | pytest | Pass |
| A3 | 固定模式和详细模式 jobs spec | fake T2I pytest | Pass |
| A4 | 数量、deadline、请求/容量限制 | pytest + diff review | Pass |
| A5 | 既有改写/媒体/用户图/写入路径 | 最小 rewrite 回归通过；扩大回归待运行 | Partial |
| A6 | job stage/messages | pytest | Pass |
| A7 | test matrix/Playwright/Harness | 待 test gate | Pending |
| A8 | release runbook | release 文档 | Pass（未部署） |
| A9 | diff/secret scan | diff check 已通过；secret scan 待 finalizer | Partial |

## 测试缺口

- 运行上传、文章编辑、媒体、自动标签和任务相关的关联 pytest。
- 启动本地 Flask 并运行真实 Playwright upload/edit harness，保存桌面和手机截图。
- 真实 MiniMax 成功率、成本和耗时只在用户授权生产/测试环境后做小流量验证。

## 残余风险

- 视觉质量属于 AI 非确定性输出，离线测试只验证数量、锚点和失败边界。
- 现有 `app/uploader.py` 包含用户此前的 MiniMax 文本 API 官方端点修改；本次没有回滚，最终 Git 收尾需隔离说明。

## Artifact

```yaml
artifact: review
status: Pass
severity: P2-fixed
findings: 3
fixed: 3
test_gaps:
  - related pytest
  - local Playwright
  - authorized provider smoke
residual_risks:
  - AI output quality and provider latency
```
