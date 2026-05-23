# AIPD 根入口首页测试报告

文件注释：
- 模块名称：AIPD 根入口首页测试报告
- 功能描述：记录本地、线上、响应式和回归验证结果
- 创建日期：2026-05-17
- 作者：Codex
- 主要变更：2026-05-17 初始创建
- 依赖模块：portal、Nginx、Playwright、curl

## 本地验证

```bash
python3 -m http.server 8088
curl -I http://127.0.0.1:8088/
curl -I http://127.0.0.1:8088/assets/portal.css
```

结果：

- `http://127.0.0.1:8088/` 返回 `200`。
- `http://127.0.0.1:8088/assets/portal.css` 返回 `200`。
- 线上 hero 图片返回 `200 image/png`。

## 浏览器验证

使用 Playwright 检查桌面和移动端：

- 桌面：`1440x1000`
- 移动：`390x844`

结果：

- 页面标题：`AIPD | AI 云服务入口`
- H1：`把文章、技能、项目和分身收束到一个入口。`
- 四个模块入口存在。
- 四个项目卡片存在。
- console error：无。
- request failed：无。
- 修复过一次导航偏移问题，复验通过。

## 主题优化复验

2026-05-17 根据 `http://aipd.me/OneCLubZhenjingList/index.html` 的黑金风格进行二次优化：

- 将首屏背景改为沉浸式视频背景，并叠加深色遮罩和金色径向光。
- 将 H1 改为金色渐变宋体大标题。
- 将模块卡片改为金色描边、玻璃拟态、内高光和 hover 抬升。
- 将样式拆分为 `portal.css` 与 `portal-sections.css`，单文件职责更清晰。

复验结果：

- 本地 `portal.css` 返回 `200`。
- 本地 `portal-sections.css` 返回 `200`。
- Playwright 桌面与移动端检查通过。
- 线上 `https://aipd.me/assets/portal-sections.css` 返回 `200 text/css`。
- 线上桌面与移动端无 console error、无 failed request。

## 移动端响应式复验

2026-05-18 针对手机浏览体验继续优化：

- 手机端导航改为居中品牌 + 胶囊导航，降低视觉压迫。
- 手机端 H1 降低字号和行高，避免首屏文字过重。
- 首屏模块入口从单列改为 2x2，缩短首屏滚动距离。
- 手机端模块卡片、项目卡片、文章卡片间距和高度收紧。

复验视口：

- `375x667`
- `393x852`
- `430x932`
- `1440x1000`

结果：

- 本地与线上 `https://aipd.me/` 均返回 `200`。
- 手机端 `scrollWidth == clientWidth`，无横向溢出。
- 手机端 `.module-radar` 为两列布局。
- 线上手机与桌面均无 console error、无 failed request。

## 线上验证

```bash
curl -k -I -L https://aipd.me/
curl -k -L https://aipd.me/ | head
```

结果：

- `https://aipd.me/` 返回 `200 text/html`。
- 页面内容为 AIPD 根入口首页，不再是 Nginx 默认页。
- `https://aipd.me/assets/portal.css` 返回 `200 text/css`。
- `https://aipd.me/assets/portal.js` 返回 `200 application/javascript`。

## 子路径回归

| URL | 结果 |
| --- | --- |
| `https://aipd.me/PolaZhenjing/` | `200`，跳转登录页 |
| `https://aipd.me/PolaRead/` | `200` |
| `https://aipd.me/polanews` | `200` |
| `https://aipd.me/xumishan/` | `200` |

## 未通过项

`bundle exec jekyll build` 未能在本地执行，原因是当前本地 Ruby 环境缺少 `jekyll` 可执行 gem。该问题与本次新增 `portal/` 静态首页无直接关系。
