# AIPD 根入口首页需求分析

文件注释：
- 模块名称：AIPD 根入口首页需求分析
- 功能描述：记录 aipd.me 根目录入口页的需求、范围、验收标准和风险
- 创建日期：2026-05-17
- 作者：Codex
- 主要变更：2026-05-17 初始创建
- 依赖模块：pola-agent-delivery-framework、pola-a2a-usage、pola-wukong-ui

## 需求口径

在 `aipd.me/` 根目录新增一个云服务总入口首页，替换当前 Nginx 默认欢迎页。首页采用悟空黑金风格，承载四个核心模块入口：

- AI文章：展示 PolaZhenjing 最近文章，并入口到 `/PolaZhenjing/admin/articles`。
- Skills：作为个人 skill hub 的预览入口，展示高价值技能方向。
- 项目：展示 PolaNews、PolaRead、须弥山、PolaZhenjing 等项目入口。
- AI分身：预留在线 Agent 产品位，表达“蒸馏我的在线 Agent”的方向。

## 用户目标

用户访问 `https://aipd.me/` 时，不再看到默认 Nginx 页，而是看到一个个人 AI 云服务入口，可快速进入已有服务并理解后续建设方向。

## 非目标

- 不重构 PolaZhenjing Flask/Jekyll 代码。
- 不实现完整 Skills 后台管理系统。
- 不实现 AI 分身在线对话后端。
- 不改动 PolaNews、PolaRead、须弥山既有服务代码。

## 参考

- 悟空官网：暗色、金色点缀、AI Agent 执行感、Skill Center 表达。
- `wwenj.com`：个人空间式入口，项目与内容模块聚合。
- 当前 `aipd.me/`：Nginx 默认页，可替换为静态入口。

## 验收标准

- `portal/index.html` 可独立作为静态页面打开。
- 首屏包含 AIPD 品牌、主 CTA、四个模块入口。
- 页面包含 AI文章、Skills、项目、AI分身四个明确分区。
- 项目入口链接覆盖 `/polanews`、`/PolaRead/`、`/xumishan/`、`/PolaZhenjing/`。
- 视觉风格符合黑金、玻璃、深色高端 AI 官网方向。
- 桌面与移动端不出现明显文本溢出或布局重叠。
- 部署后 `https://aipd.me/` 返回新首页，原子路径服务不受影响。

## 风险

- 根目录部署会替换 Nginx 默认页，需要确认不会影响已有 `location` 子路径。
- 静态首页引用 `/PolaZhenjing/assets/...` 图片，需在线验证资源可访问。
- 当前本地存在 `.qoder` 未提交改动，本需求不应覆盖。
