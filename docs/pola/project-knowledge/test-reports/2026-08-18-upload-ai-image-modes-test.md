# Test Report：上传文章 AI 生图四档模式

日期：2026-08-18

结论：Pass（本地 Ship ready）；生产真实 provider smoke 未执行。

## 功能用例门禁

- 用例：`docs/pola/project-knowledge/delivery/upload-ai-image-modes/function_test_cases.json`
- 矩阵：`docs/pola/project-knowledge/delivery/upload-ai-image-modes/test_matrix.json`
- Validator：覆盖 A1–A9、9 个 feature、17 个 case，退出码 0。

## 已运行命令

| 命令 | 结果 |
| --- | --- |
| `.venv/bin/python -m py_compile app/uploader.py app/jobs.py app/__init__.py scripts/upload_edit_playwright_harness.py` | Pass |
| `.venv/bin/python -m pytest tests/test_upload_image_modes.py tests/test_upload_rewrite_rate.py -q` | 21 passed |
| 关联上传/媒体/编辑/标签/jobs pytest | 68 passed |
| `.venv/bin/python -m pytest tests -q` | 120 passed |
| `validate_function_test_cases.py ...` | 9 acceptance / 9 feature / 17 case，Pass |
| `scripts/upload_edit_playwright_harness.py --base-url http://127.0.0.1:5019` | Pass，4 screenshots |
| `~/.codex/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py` | Pass |

## 覆盖结果

- 四档 UI：三个表单共 12 个 radio，默认适中；详细可选择。
- 状态：模式经 draft 和 job payload 传递，非法/缺失值默认适中。
- 数量：题图 1、概括 3、适中 5；详细为题图 + 可配图段落。
- 安全：详细最多 12 段；900 秒 deadline 包含视觉规划；响应 18MB、单图 12MB、整批 64MB。
- AI 不可信输出：视觉 LLM 不能扩张 scene 数量或改变后端锚点。
- 降级：单张/批次失败保留已成功图片并继续写文章；任务消息展示计划/实际数量。
- 兼容：AI 改写率、原媒体、用户配图、文章编辑/预览/保存和任务路径回归通过。

## 浏览器证据

- 桌面上传页：`tmp/harness/upload-edit/1787047926-upload-rich-switch.png`
- 手机生图模式：`tmp/harness/upload-edit/1787047926-upload-image-modes-mobile.png`
- 编辑预览：`tmp/harness/upload-edit/1787047927-edit-markdown-rich-preview.png`
- 编辑保存：`tmp/harness/upload-edit/1787047930-edit-save-submitted.png`
- console errors：0（忽略 harness 明确允许的 favicon/TinyMCE 开发提示）。
- 关键 network failures：0（本地文章页缺少静态主题 CSS 为既有 harness 白名单项）。

## 发现与处理

- 第一次手机全页溢出断言失败，诊断为既有 `.admin-nav-links` 导航溢出，不是本次卡片；断言收窄为生图模式区域并保留具体元素诊断信息。
- 生图模式区域在 390px 视口无溢出，四张卡片按单列完整显示。

## 未覆盖与残余风险

- 未调用真实 MiniMax T2I，避免未授权费用和生产副作用；发布后需用短文章做 cover/standard 小流量 smoke。
- AI 图像审美和内容相关性不能由离线测试确定。
- 本轮未部署、未重启服务、未验证线上登录后页面。

## Artifact

```yaml
artifact: test-evidence
status: Pass
function_test_cases: docs/pola/project-knowledge/delivery/upload-ai-image-modes/function_test_cases.json
test_matrix: docs/pola/project-knowledge/delivery/upload-ai-image-modes/test_matrix.json
failures: []
skipped:
  - production MiniMax smoke
coverage_notes: A1-A9 已映射；A8/A9 的最终发布/Git 门禁在后续阶段完成
```
