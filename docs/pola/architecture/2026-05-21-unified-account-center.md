# SDD：AIPD 统一账号中心

日期：2026-05-21

## 1. 背景和目标

当前 `aipd.me` 已有根门户、PolaZhenjing、Skill Hub、超级小王 Agent、PolaRead、PolaNews、须弥山等入口。已有登录注册与用户资料主要在 PolaZhenjing 中，根门户通过 `/PolaZhenjing/admin/api/me` 读取登录态。下一步需要将账号、权限和基础偏好上升为全站统一能力。

目标是在不破坏现有应用的前提下，建立统一账号服务和统一用户组件，让各应用复用同一套登录、注册、用户中心、角色权限、主题和字体设置。

## 2. 当前系统理解

| 维度 | 项目事实 | 证据文件 | 对本需求的影响 |
| --- | --- | --- | --- |
| Flask 后台 | `create_app()` 注册 `auth_bp`、`uploader_bp`、`skillhub_bp`、`agent_bp` | `app/__init__.py` | 统一账号服务可先扩展 `auth_bp` |
| 用户表 | 已有 `users` 表，含昵称、头像、角色字段 | `app/__init__.py` | 可增量扩展偏好和权限表 |
| 统一状态 API | `api/me` 返回用户资料和权限 | `app/auth.py` | 应成为跨应用账号服务基础 API |
| 根门户组件 | `portal.js` 调用 `api/me` 渲染登录态 | `portal/assets/portal.js` | 可抽象为可复用 auth widget |
| 部署 | Flask 在 `/PolaZhenjing`，根门户在 `/var/www/html` | systemd/nginx 现状 | 新 API 不应破坏子路径部署 |

## 3. 项目 Arch Reference 摘要

- arch-reference 路径：[docs/pola/arch-reference.md](/Users/wangchang/Desktop/WSYCursorCode/PolaZhenJing/docs/pola/arch-reference.md)
- 本次选型使用的项目事实：
  - PolaZhenjing 已有账号系统和用户资料 API。
  - 根门户和静态页已能通过 `api/me` 获取登录态。
  - PolaRead/PolaNews 已有 SSO 桥接方向，适合作为 client 接入统一账号服务。
- 必须复用的现有模式：
  - Flask Blueprint、SQLite 增量迁移、Jinja 管理页、根门户静态 JS auth entry。
- 不可破坏的架构约束：
  - 现有 `/PolaZhenjing/admin/login`、`/register`、`/account` 继续可用。
  - 子应用现有 token/session 需兼容，不做一次性硬切。

## 4. 架构选型分析

| 候选方案 | 一致性 | 复用 | 耦合 | 扩展 | 验证 | 部署风险 | 回滚 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A 扩展 PolaZhenjing auth 为统一账号服务 | 高 | 高 | 中 | 中 | 高 | 低 | 高 | 推荐一期采用 |
| B 新建独立 `/account` Flask 服务 | 中 | 中 | 低 | 高 | 中 | 中 | 中 | 二期可演进 |
| C 各应用复制同一套登录组件 | 低 | 低 | 高 | 低 | 低 | 中 | 低 | 拒绝 |

### 架构选型结论

推荐：候选 A，先扩展现有 PolaZhenjing auth 为统一账号服务。

理由：
- 现有用户表、登录注册、头像、角色和 `api/me` 已经存在，改动最小。
- 根门户已依赖该服务，天然可作为统一入口。
- 可以渐进接入 PolaRead/PolaNews，降低迁移风险。

拒绝方案：
- 候选 C：各应用复制登录组件。拒绝原因是会造成账号状态、权限、偏好和 UI 不一致。

决策约束：
- 不新建平行用户主数据。
- 不把 PolaRead/PolaNews 的业务偏好塞进统一用户表。
- 所有权限在服务端校验。

## 5. 推荐方案概览

### 一期：统一账号服务内聚到 PolaZhenjing

- 扩展 `users` 表或新增资料/偏好/权限表。
- 增强 `auth_bp` API：
  - 获取当前用户。
  - 更新资料和头像。
  - 更新全站主题/字体偏好。
  - 查询角色/权限。
  - 子应用 session 校验/交换。
- 抽象根门户 auth widget，应用到首页、About、Agent、后续静态页面。
- 子应用调用统一账号服务，完成登录状态同步和权限判断。

### 二期：拆出 Account Center

如果用户量、权限复杂度或接入应用数量继续增加，可将统一账号服务拆为 `/account` 或 `/auth` 独立 Flask/FastAPI 服务，但 API 契约保持兼容。

## 6. 数据模型设计

### 现有表：users

继续保留：

- `id`
- `username`
- `email`
- `password_hash`
- `email_verified`
- `created_at`
- `nickname`
- `avatar_url`
- `role`

### 新增表：user_preferences

```sql
CREATE TABLE IF NOT EXISTS user_preferences (
  user_id INTEGER PRIMARY KEY,
  theme TEXT DEFAULT 'dream-gold',
  font_family TEXT DEFAULT 'system',
  font_scale TEXT DEFAULT 'normal',
  density TEXT DEFAULT 'comfortable',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### 新增表：user_permissions

```sql
CREATE TABLE IF NOT EXISTS user_permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  permission TEXT NOT NULL,
  source TEXT DEFAULT 'manual',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, permission),
  FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### 新增表：app_user_links

用于子应用本地账号映射。

```sql
CREATE TABLE IF NOT EXISTS app_user_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  app_id TEXT NOT NULL,
  external_user_id TEXT,
  linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, app_id),
  FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### 应用偏好边界

- 全站偏好放 `user_preferences`。
- PolaRead 个性偏好放 PolaRead 自己的表，例如 `polaread_user_preferences`。
- PolaNews 个性偏好放 PolaNews 自己的表，例如 `polanews_user_preferences`。

## 7. API 设计

### 当前用户

`GET /PolaZhenjing/admin/api/me`

响应扩展：

```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "wsyxjer",
    "email": "wsyxjer@gmail.com",
    "nickname": "炽驹",
    "avatar_url": "/PolaZhenjing/assets/avatars/user-1.png",
    "role": "admin",
    "permissions": ["articles.manage", "skills.manage"],
    "preferences": {
      "theme": "dream-gold",
      "font_family": "MFYaYun",
      "font_scale": "normal",
      "density": "comfortable"
    }
  }
}
```

### 资料更新

`POST /PolaZhenjing/admin/api/profile`

- 入参：`nickname`、`avatar_data` 或 multipart avatar。
- 行为：保存昵称与圆形头像。
- 权限：登录用户本人。

### 全站偏好更新

`POST /PolaZhenjing/admin/api/preferences`

- 入参：`theme`、`font_family`、`font_scale`、`density`。
- 行为：保存全站基础偏好，返回更新后的 user payload。

### 权限查询

`GET /PolaZhenjing/admin/api/permissions`

- 普通用户返回自身权限。
- 管理员可附带 `user_id` 查询其他用户。

### 子应用会话校验

`POST /PolaZhenjing/admin/api/sso/check`

- 入参：子应用标识、可选目标权限。
- 凭据：浏览器同源 Cookie。
- 响应：用户 payload、权限判断、建议跳转。

### 子应用会话交换

`POST /PolaZhenjing/admin/api/sso/exchange`

- 用于 PolaRead/PolaNews 将统一会话换成本地 token。
- 响应：`app_token` 或标准 user payload，由子应用自行签发本地 token。

## 8. 前端组件设计

### Auth Widget

建议新增：

- `portal/assets/auth-widget.js`
- `portal/assets/auth-widget.css`

能力：

- 自动读取 `/PolaZhenjing/admin/api/me`。
- 渲染未登录/加载/已登录/无权限状态。
- 输出一致的头像、昵称、登录/注册链接。
- 支持读取用户主题和字体偏好，并写入 `document.documentElement.dataset` 或 CSS variables。

### Account Center UI

建议将 `app/templates/account.html` 从单一表单扩展为分区页面：

- 个人资料：昵称、头像、邮箱、密码入口。
- 外观偏好：主题、字体、字号、显示密度。
- 权限与应用：角色、权限、已开通应用。
- 应用设置入口：PolaRead、PolaNews、PolaZhenjing、Skill Hub。
- 管理员入口：用户管理、权限授予。

## 9. 子应用接入策略

### PolaZhenjing / Skill Hub / Agent

- 继续使用 Flask session。
- 所有后台页面使用统一 `login_required`。
- 管理能力改为权限点判断，例如 `skills.manage`。

### PolaRead

- 未登录时跳转 `/PolaZhenjing/admin/login?next=/PolaRead/`。
- 前端启动时调用本地 SSO endpoint。
- 后端通过统一账号 `sso/check` 校验 AIPD 会话，映射/创建本地用户。
- PolaRead 语音、语速、播放偏好保留在 PolaRead。

### PolaNews

- 未登录时跳转统一登录。
- 后端通过统一账号 `sso/check` 校验会话。
- PolaNews 关注分类、推送时间保留在 PolaNews。

## 10. 文件改动计划

| 文件 | 操作 | 内容 | 对应验收 |
| --- | --- | --- | --- |
| `app/__init__.py` | 修改 | 增量创建 preferences/permissions/app links 表 | A4/A6 |
| `app/auth.py` | 修改 | 扩展 user payload、preferences/profile/sso API、权限 helper | A4/A5 |
| `app/templates/account.html` | 修改 | 统一账号中心分区 UI | A3 |
| `app/templates/base.html` | 修改 | 用户入口组件和主题/字体变量 | A3 |
| `portal/assets/auth-widget.js` | 新增 | 根门户统一登录态组件 | A3/A4 |
| `portal/assets/auth-widget.css` | 新增 | 黑金用户组件样式 | A3 |
| `portal/index.html/about.html/agent.html` | 修改 | 接入统一 auth widget | A3 |
| PolaRead auth endpoint | 修改 | 接入统一 SSO check/exchange | A5 |
| PolaNews auth endpoint | 修改 | 接入统一 SSO check/exchange | A5 |
| `docs/pola/*` | 修改 | 开发、测试、发布记录 | A1/A8 |

## 11. 测试策略

| 测试类型 | 命令或方式 | 覆盖验收 |
| --- | --- | --- |
| 单元测试 | user payload、权限合并、preferences 默认值、头像保存 | A4/A6 |
| API 测试 | `api/me`、profile、preferences、sso/check | A4/A5 |
| UI 测试 | 登录/未登录账号中心、头像上传、主题字体切换 | A2/A3 |
| 集成测试 | 首页、Agent、PolaZhenjing、Skill Hub 登录状态一致 | A5/A7 |
| 子应用回归 | PolaRead/PolaNews 登录跳转、token 交换、应用偏好不丢失 | A5/A7 |
| 部署验证 | 备份 DB、迁移后服务 active、关键 URL 200/302 正常 | A8 |

## 12. 部署和回滚

### 部署步骤

1. 备份 `/PolaZhenjing/data/wiki.db`。
2. 部署后端代码和模板。
3. 重启 `polazj.service`。
4. 部署根门户 auth widget 静态资源。
5. 灰度接入 PolaRead/PolaNews。
6. 验证登录、注册、账户中心、子应用跳转。

### 回滚策略

- 代码回滚：恢复上一个 `app/auth.py`、模板和静态资源。
- 数据回滚：新增表可保留不影响旧逻辑；如需完全回退，恢复 DB 备份。
- 子应用回滚：保留原本本地登录/token 流程开关，关闭 SSO exchange。

## 13. 验收映射

| 验收项 | 实现点 | 验证方式 |
| --- | --- | --- |
| A1 | PRD/SDD/arch-reference | 文档审阅 |
| A2 | 用户流程和页面状态 | UI 测试 |
| A3 | account center + auth widget | 浏览器截图/交互 |
| A4 | 统一账号 API | curl/API 测试 |
| A5 | 服务端权限和子应用接入 | 集成测试 |
| A6 | 数据表和迁移兼容 | DB 检查 |
| A7 | 旧路径回归 | 回归清单 |
| A8 | 备份部署回滚 | 发布记录 |

## 14. 未决问题

- Q1 管理员授权 UI 是否一期完成，还是先通过数据库/配置维护权限。结论：一期完成管理员授权 UI。
- Q2 主题/字体是否需要立即覆盖 PolaRead/PolaNews，还是先只在根门户和 PolaZhenjing 生效。结论：立即覆盖 PolaRead/PolaNews。
- Q3 是否需要“应用权限申请”工作流，还是无权限只显示提示。结论：需要权限申请工作流。
- Q4 PolaRead/PolaNews 当前生产数据结构需在编码前重新读取确认。结论：需要并已开始复查，实施时继续以生产结构为准，保证安全统一过渡。

## 15. 生产结构复查补充

- PolaRead 位于 `/opt/PolaRead`，后端是 FastAPI，进程为 `/opt/PolaRead/backend/.conda/polaread/bin/uvicorn app.main:app --port 8766`。已有 `/api/auth/sso/aipd`，读取 AIPD Cookie 后换取 PolaRead JWT。数据库 `backend/data/polaread.db` 包含：
  - `users`：本地用户、邮箱、头像、last_login。
  - `user_settings`：`tts_voice`、`tts_speed`、`theme`、`auto_play_next`、`show_translation`、`font_family`。实施策略：TTS/播放/翻译保留本地，`theme/font_family` 由 AIPD 统一偏好覆盖。
- PolaNews 位于 `/opt/polanews`，Next app，有 `/api/auth/sso/aipd`，读取 AIPD Cookie 后生成本地 JWT。设置接口 `/api/settings` 将 `theme`、`digest_time`、`categories` 存在用户 `preferences` JSON。实施策略：`digest_time/categories/language` 保留本地，`theme/font_family` 由 AIPD 统一偏好覆盖。
