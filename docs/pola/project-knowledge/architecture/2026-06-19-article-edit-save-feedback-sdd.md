# SDD：文章编辑页保存反馈与 Harness 覆盖

日期：2026-06-19

## 影响模块

- `app/templates/article_edit.html`
  - 前端提交监听器。
  - 保存状态 UI。
- `scripts/upload_edit_playwright_harness.py`
  - 新增临时文章创建、真实点击保存、文件写回验证和清理。
- `tests/test_article_edit_rich_editor.py`
  - 增加模板级提交反馈与保存模式保护断言。

## 根因分析

- 后端保存接口本身可以处理 POST 并写回文章。
- 旧 Harness 只验证了编辑器切换、预览和修改建议字段可填写，没有点击真实保存按钮。
- 填写修改建议后后端会同步等待 AI 改写，前端没有提交中状态，用户看到的是“按钮没反应”。

## 设计

- 在表单末尾增加 `#save-status`，使用 `role=status` 和 `aria-live=polite`。
- 提交时：
  - 读取 `event.submitter`，将点击的 `save_mode` 写入隐藏字段。
  - 将当前正文镜像到隐藏 `body` 字段。
  - 禁用提交按钮并显示保存状态。
  - 不 `preventDefault`，保持原生表单提交。
- Harness：
  - 运行前创建 `_posts/2026-06-19-upload-edit-harness.md`。
  - 用临时管理员登录本机服务。
  - 真实点击保存，等待跳转到详情页。
  - 读取临时文章文件确认正文写回。
  - finally 清理临时用户和临时文章。

## 回滚

- 回滚 `app/templates/article_edit.html` 的保存状态和提交保护变更。
- 回滚 Harness 的临时文章保存覆盖。
- 后端保存逻辑不变，无数据迁移。
