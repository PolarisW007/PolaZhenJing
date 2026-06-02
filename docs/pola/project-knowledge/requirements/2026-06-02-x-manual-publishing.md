# X 手动发布模式需求

- 日期：2026-06-02
- 来源：用户要求去除 X API 对接，改成 X 内容生成后人工发布
- 关联需求池：`XhcYwKVYha`

## 原始需求

去除 X 的 API 对接部分，不再申请和配置 X API，不再依赖 `X_USER_ACCESS_TOKEN`。发布中心应生成适合 X 的内容，用户复制后到 X 后台手动发布，并回填发布链接。

## 目标

- X 平台从官方 API 自动发帖切换为手动发布包模式。
- 页面直接展示 X 文案、来源链接、封面提示和发布步骤。
- 生成 X 发布包时写入 `social_publications`，状态为 `package_created`。
- 手动发布完成后沿用现有链接回填能力记录 `external_url`。
- 移除 X token 配置 blocker，让需求可以进入待验收。

## 边界

- 保留微信公众号官方草稿/发布能力。
- 保留小红书、今日头条手动发布包模式。
- 保留 X 文案 280 字限制。
- 不再调用 X API、不上传 X 媒体、不创建 X post id。

## 非目标

- 不实现 X OAuth。
- 不申请 X API 账号或购买 credits。
- 不自动打开或操控 X 网页后台发帖。

## 验收标准

- A1：发布中心 X 卡片不再展示 token 缺失提示或“发布到 X”自动发帖按钮。
- A2：X 卡片展示可复制的 X 文案，长度不超过 280 字。
- A3：点击“生成发布包”后写入 X `package_created` 记录。
- A4：发布后可回填 X 链接，记录状态更新为 `published_manual`。
- A5：测试证明不会触发 X API 或依赖 `X_USER_ACCESS_TOKEN`。
