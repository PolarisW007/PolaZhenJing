# PolaZhenJing / AIPD 架构参考

更新时间：2026-08-18

## 项目类型和业务形态

AIPD 是 `aipd.me` 根域下的个人 AI 云服务入口，根门户承载全站导航、展示与统一入口；`/PolaZhenjing/` 是 Flask 后台，负责文章生产、Skill Hub、用户登录注册、用户资料和 Agent API。根域还反向代理到 PolaRead、PolaNews、须弥山等独立应用。

## 前端架构

- 根门户：`portal/` 下的静态 HTML/CSS/JS，部署到服务器 `/var/www/html`。
- 管理后台：Flask Jinja 模板，主模板位于 `app/templates/base.html`，页面模板按功能拆分。
- 统一登录态展示：根门户 `portal/assets/portal.js` 调用 `/PolaZhenjing/admin/api/me`，根据返回的昵称和头像渲染登录/注册或用户入口。
- 样式：根门户使用黑金视觉体系，后台页面使用 `app/templates/base.html` 内联 CSS 变量与卡片式表单。
- 后台富文本编辑器：上传页使用本地 vendor 的 TinyMCE 运行资源，路径为 `assets/vendor/tinymce/`，避免核心编辑能力依赖外部 CDN。
- 文章生成表单：`app/templates/upload.html` 的上传文件、粘贴内容、输入 URL 三个表单统一提交文章生成参数；低频参数通过 draft JSON 跨越风格选择页传递。

## 后端架构

- 后端主框架：Flask app factory，入口 `app/__init__.py:create_app()`。
- 反向代理：`ReverseProxied` 根据 `X-Script-Name` 支持 `/PolaZhenjing/` 子路径部署。
- Blueprints：
  - `app/auth.py`：登录、注册、邮箱验证、密码修改、账户管理、`/admin/api/me`。
  - `app/uploader.py`：文章上传、生成、编辑、列表、展示。
  - `app/social_publish.py`：文章多平台发布中心，复用 `_posts` 解析、`jobs` 异步任务和 SQLite 发布记录；微信公众号和 X 使用官方 API，未接官方 API 的平台生成人工发布包。
  - `app/skillhub.py`：Skill 列表、上传、GitHub 导入、下载。
  - `app/agent.py`：超级小王 Agent API、记忆库查询。
- 运行方式：服务器 `/PolaZhenjing/.venv/bin/gunicorn`，systemd 服务 `polazj.service`，监听 `127.0.0.1:5000`。
- 长任务：`app/jobs.py` 使用 SQLite 记录任务状态，并通过有界 `ThreadPoolExecutor` 执行文章生成等后台任务；默认最大并发为 2。
- 文章 AI 链路：`app/uploader.py` 依次执行文本改写、原媒体恢复、用户配图处理、MiniMax 插画规划/生成、Markdown 注入、Jekyll 文件写入和安全 Git 同步；外部图片调用失败时保持文章可生成。

## 通信协议和路由

- 根门户静态路由：`/`、`/agent.html`、`/about.html`。
- 公开文章路由：根域 `/articles`、`/articles/<filename>.md` 由 nginx 代理到 Flask 公开文章 blueprint；短链 `/s/<code>` 也应由 nginx 代理到 Flask，并在应用内解析到同一篇公开文章。
- 公开发现路由：`/sitemap.xml`、`/robots.txt`、`/llms.txt`、`/feed.xml`、`/articles.json` 由 Flask 按服务器当前 `_posts` 动态生成，供搜索引擎、AI agent 和社交抓取器读取。
- 统一账号基础 API：
  - `GET /PolaZhenjing/admin/api/me`：返回 `authenticated`、`user`、`permissions`。
  - 页面路由：`/PolaZhenjing/admin/login`、`/register`、`/account`、`/password`、`/logout`。
- 已有跨应用 SSO 方向：PolaRead/PolaNews 通过读取 AIPD/PolaZhenjing 会话并换取各自本地 token。

## 数据与状态

- 当前主数据库：`data/wiki.db` SQLite，WAL 模式。
- 当前 `users` 表字段：`id`、`username`、`email`、`password_hash`、`email_verified`、`created_at`、`nickname`、`avatar_url`、`role`。
- 发布中心状态表：`social_publications` 和 `social_publication_events`，记录每篇文章在各平台的状态、外部 ID/URL、payload、错误和事件轨迹；第三方 token 不写入表内。
- 洞察选题池：`data/insight_topics.json` 存储 Admin 每日选题、状态、来源证据、社媒运营蓝图字段、约 5000 字 Markdown 底稿和最近刷新元数据；`app/insight_topics.py` 负责从 PolaNews、Hacker News、GitHub Search、公开 RSS 手动刷新线上信号，先按 AI 相关性过滤，再把原始信号转译为“场景使用、产品能力更新、业务模式、商业思考、最佳实践、实践复盘”六类社媒运营选题。RSS 数据源按价值分层，覆盖官方模型/产品更新、企业采用与云端实践、开发者工程实践、商业模式和创业观察，当前包含 OpenAI、Anthropic、Hugging Face、Google AI、Google DeepMind、Microsoft Official Blog、AWS Machine Learning Blog、GitHub AI & ML、Sequoia Stories。列表页展示内容赛道、社媒钩子、目标读者、核心问题、建议结构和来源信号；一键导入上传时 Markdown 编辑器预填 5000-30000 可见字符的正文型长稿，并剔除状态、来源、评分等选题池管理元信息。
- 头像文件：`assets/avatars/`，URL 为 `/PolaZhenjing/assets/avatars/<file>`。
- 当前权限：`user_payload()` 以 role 生成基础权限列表，admin 用户扩展管理权限。
- 文章生成中间态：`data/drafts/<id>.json` 保存正文、标题、标签、媒体策略、改写率和图片模式等临时参数，风格选择后读取并删除；异步进度保存在 SQLite `jobs` 表。
- 文章及媒体文件：成稿写入 `_posts/`，AI 图片写入 `assets/images/generated/<slug>/`，用户配图写入 `assets/images/uploads/<slug>/`。

## 部署方式

- 根门户同步到 `/var/www/html`。
- Flask 应用同步到 `/PolaZhenjing/app`，重启 `polazj.service`。
- 部署前应保留数据库备份，涉及 schema 迁移时需可回滚。

## 复用优先级

1. 优先复用 `app/auth.py` 的会话、用户 payload、登录注册、账户页。
2. 根门户和其他静态页优先复用 `/PolaZhenjing/admin/api/me` 的用户状态。
3. PolaRead、PolaNews 等独立应用优先作为统一账号服务的 client，不再各自定义账号资料主数据。
4. 用户个性化基础设置（昵称、头像、角色、权限、主题、字体）归统一账号中心；应用偏好（语音、语速、分类、推送时间）归各应用设置。
5. 文章生成参数优先复用 `upload()` → `_save_draft()` → `generate()` → `_run_generate_job()` 的传递链路，不新建并行入口或第二套任务系统。
6. 文章插画优先复用 `_extract_visual_blocks()`、`_call_visual_brief_llm()`、`_generate_illustrations()` 和 `_inject_illustrations()`，数量策略通过显式模式配置扩展。

## 架构约束

- 不破坏现有 `/PolaZhenjing/admin/*` 登录注册路径。
- 不一次性强迁移所有应用账号，优先兼容现有本地 token/session。
- 跨应用权限必须由服务端校验，不能只依赖前端隐藏入口。
- 头像、昵称、主题、字体等用户基础资料必须以统一账号服务为准。
- 线上选题抓取必须保持手动触发或过期后台触发、超时受控、分源失败隔离；抓取结果必须带 `evidence_links`，不得生成无来源选题；原始新闻/链接标题只能作为 `source_signal_title` 证据切口，不应直接成为运营选题标题。
- AI 批量生图必须有并发上限、单请求超时、整批数量/时间预算和逐张失败降级；不得在日志、视觉计划或工程文档中写入 provider key。
- 旧 draft 缺少新增字段时必须使用兼容默认值，不能阻断历史/并发中的文章生成任务。
