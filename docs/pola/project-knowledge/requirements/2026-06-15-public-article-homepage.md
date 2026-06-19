# Requirement: PolaZhenjing 前台文章首页

日期: 2026-06-15

## 用户原始需求

为 `https://aipd.me/PolaZhenjing/admin/articles` 对应的普通用户访问场景提供一个前台文章列表页,作为普通用户的 PolaZhenjing 首页。页面参考:

- Lilian Weng Lil Log: 作者型知识库/技术笔记目录。
- Ben Evans: 简洁的观点文章入口、精选和时间线。
- 掘金: 频道筛选、搜索和信息流浏览。

默认视觉风格参考 `aipd.me`,并执行 Pola A2A/harness。

## 目标

- 普通用户访问 `/PolaZhenjing/admin/articles` 或 `/articles` 时看到干净、可浏览的前台文章首页。
- 首页有 Wiki/知识库式浏览体验: 精选文章、频道/主题、搜索、排序、文章时间线。
- 管理员访问 `/PolaZhenjing/admin/articles` 仍看到后台文章管理列表。
- 保持现有公开文章详情、短链、RSS/JSON feed、SEO/GEO 入口不回退。

## 非目标

- 不重做后台管理列表 `articles.html`。
- 不新增数据库 schema。
- 不引入前端框架或外部 UI 依赖。
- 不改变文章生成、编辑、发布、多平台同步逻辑。

## 验收标准

- A1 文档: 需求、PRD、SDD、测试报告、开发日志记录本次范围、验证和风险。
- A2 普通访问 `/articles` 返回前台文章首页,而不是后台风格列表。
- A3 普通登录用户访问 `/admin/articles` 时仍渲染同一前台文章首页,不出现 `PolaZhenjing 管理后台`、上传、发布、小王记忆等后台导航。
- A4 管理员访问 `/admin/articles` 仍渲染后台管理页。
- A5 前台首页包含: hero/定位、精选文章、主题频道、搜索、排序、文章时间线、RSS/JSON/LLMs 链接。
- A6 前台首页支持无刷新搜索、主题筛选、排序;移动端无横向溢出。
- A7 SEO/GEO 保持: `ItemList` JSON-LD、canonical、RSS/JSON feed、文章 canonical URL。
- A8 Harness: Flask test client + 浏览器 PC/mobile 对公开首页和管理员页做回归。

## 风险等级

P2。影响公开文章列表和普通用户入口,但不涉及数据库、secret、后台任务或生产配置。主要风险是普通用户误看到后台导航、管理员管理入口误被替换、列表页面 SEO 元信息回退。
