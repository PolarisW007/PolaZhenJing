# AIPD 根入口首页架构方案

文件注释：
- 模块名称：AIPD 根入口首页架构方案
- 功能描述：描述根入口静态页面的模块划分、部署面、测试策略与回滚方式
- 创建日期：2026-05-17
- 作者：Codex
- 主要变更：2026-05-17 初始创建
- 依赖模块：Nginx、静态 HTML/CSS/JS、PolaZhenjing 资源目录

## 模块影响

- 新增 `portal/index.html`：根入口页面结构与内容。
- 新增 `portal/assets/portal.css`：黑金视觉系统、响应式布局和交互状态。
- 新增 `portal/assets/portal.js`：年份、平滑滚动、可见性动画。
- 新增 `docs/pola/**`：A2A 阶段产物记录。

现有 `index.html` 是 Jekyll 文章首页，不改动，避免影响 GitHub Pages 和 PolaZhenjing 内容站。

## 页面结构

```text
Hero
├── 固定导航
├── 品牌主张与 CTA
├── 四模块入口卡片
└── 系统状态条

AI文章
├── 最近文章卡片
└── 管理后台入口

Skills
├── Skill Hub 定位
└── 精选 skill 能力卡片

项目
├── PolaNews
├── PolaRead
├── 须弥山
└── PolaZhenjing

AI分身
├── Agent 定位
└── 下一阶段能力路线
```

## 数据流

- 页面为纯静态，不读取后端 API。
- 文章与项目链接为已知线上路径。
- 视觉图片优先复用 PolaZhenjing 已有文章配图，避免新增大二进制资源。

## 部署面

推荐部署方式：

```bash
rsync -av portal/ root@pola-server:/var/www/html/
```

当前 `https://aipd.me/` 返回 `/var/www/html/index.nginx-debian.html` 默认页。将 `portal/index.html` 部署为 `/var/www/html/index.html` 后，Nginx 默认静态根会优先展示新首页。

## 回滚

```bash
ssh pola-server 'rm -f /var/www/html/index.html /var/www/html/assets/portal.css /var/www/html/assets/portal.js'
```

回滚后根目录会恢复显示默认 Nginx 欢迎页；子路径应用不受影响。

## 测试策略

- 本地静态服务打开 `portal/index.html`。
- 检查桌面和移动端视口截图。
- 检查关键链接响应。
- 部署后 `curl -I https://aipd.me/` 和浏览器截图验证。
