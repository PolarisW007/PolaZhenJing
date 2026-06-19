# 文章编辑 AI 修改显式开关 SDD

## 架构影响

本次改动限定在文章编辑保存链路：

- `app/templates/article_edit.html`：新增 AI 修改开关和前端显示/禁用控制。
- `app/uploader.py`：新增表单布尔解析、AI 输出清洗、模型结果媒体保留，以及编辑 POST 的显式开关判断。
- `tests/test_article_edit_rich_editor.py`：覆盖默认不开 AI、AI 输出清洗和图片保留。
- `scripts/upload_edit_playwright_harness.py`：浏览器回归默认隐藏 AI 面板、开启后可填写建议、普通保存可提交。

## 数据流

```text
管理员打开编辑页
  -> 默认只显示正文编辑和保存
  -> 未勾选 enable_ai_revision
  -> POST 不触发 _apply_revision_instruction
  -> _canonical_body_from_form 生成正文
  -> _build_post_markdown 写回文章

管理员主动勾选 enable_ai_revision
  -> 显示 rewrite_rate 与 revision_instruction
  -> POST enable_ai_revision=1
  -> _apply_revision_instruction 调用 LLM
  -> _clean_llm_revision_output 清理 think / 自述 / 围栏
  -> _ensure_original_media 补回原文媒体
  -> normalize_markdown 后写回文章
```

## 关键决策

- AI 修改使用 opt-in，不再由“修改建议字段是否有值”单独决定。
- 后端强制判断 `enable_ai_revision`，前端隐藏只是体验，不作为安全边界。
- 模型输出只接受正文 Markdown；明显以英文模型自述开头的内容直接拒绝。
- 媒体保留采用防御式追加：如果模型遗漏原图片/HTML 媒体标签，追加到“原文媒体”区域，优先保证图片不丢。

## 风险和回滚

- 风险：开启 AI 修改时，如果模型重排正文，图片可能被追加到文末而不是原位置；这是保图优先的保守策略。
- 回滚：恢复 `app/uploader.py` 和 `app/templates/article_edit.html` 到上一版本，并保留线上文章备份。
- 线上止血：受影响文章已从 2026-06-17 备份恢复；污染版本另存到服务器备份目录。

## 测试策略

- 单测验证默认不开 AI 不调用模型。
- 单测验证启用 AI 时仍传入 canonical Markdown。
- 单测验证 `<think>` 清理和原媒体补回。
- Playwright 验证编辑页默认隐藏 AI 面板、开启后可填写、默认保存可提交。

