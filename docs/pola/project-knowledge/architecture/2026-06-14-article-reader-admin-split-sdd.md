# SDD: 文章浏览页权限分流和文章切换

日期: 2026-06-14

## 当前系统理解

- 文章详情页由 `app/uploader.py::_render_article()` 渲染 `app/templates/article_view.html`。
- 是否管理员由 `_is_admin_session()` 判断,当前模板已有 `can_manage` 和 `show_admin_nav`。
- `base.html` 仅在 `show_admin_nav` 为真时显示管理后台导航,非管理员没有统一用户中心轻导航。
- `article_view.html` 当前存在两个分享/摘要区域:
  - 标题下方 `article-share-panel`。
  - 管理员可见 `summary-box` 中的 summary + share row。
- `_scan_posts()` 已能按日期倒序扫描文章,可复用来计算上一篇/下一篇和快速列表。

## 项目 Arch Reference 摘要

- arch-reference 路径: `docs/pola/arch-reference.md`
- 相关事实:
  - Flask/Jinja 后台与公开文章页共用 `base.html`。
  - 普通用户账户中心位于 `/PolaZhenjing/admin/account`,密码/设置位于 `/PolaZhenjing/admin/password` 和账户偏好表单。
  - 公开文章页 `/articles/<file>` 由 public blueprint 渲染,管理员预览页 `/admin/articles/<file>` 由 uploader blueprint 渲染。

## 架构选型

| 方案 | 一致性 | 风险 | 结论 |
| --- | --- | --- | --- |
| 在前端 JS 中隐藏按钮 | 低 | HTML 仍泄露管理入口 | 不选 |
| Jinja 按 `can_manage` 服务端条件渲染 | 高 | 需补足模板测试 | 采用 |
| 拆分普通/管理员两套文章模板 | 中 | 重复维护 SEO/正文样式 | 不选 |

## 方案

- `base.html`
  - 增加非管理员/普通用户轻导航。
  - 管理员仍保留原后台导航。
  - 轻导航只包含文章列表、统一用户中心、设置/密码、登录/退出。
- `app/uploader.py`
  - 新增文章导航上下文 helper,基于 `_scan_posts()` 计算:
    - `previous_article`
    - `next_article`
    - `quick_articles`
  - `_render_article()` 传入 `article_navigation`。
- `article_view.html`
  - 移除顶部重复分享面板。
  - 保留单一摘要卡片。
  - 管理操作和多平台分享统一放入管理员工具区。
  - 正文后增加上一篇/下一篇和快速 Wiki/文章列表。
  - 普通用户无管理/分享按钮。
- 测试
  - 增加模板级/路由级断言:
    - 公开文章页不含管理和分享文字。
    - 管理员文章页含管理工具区。
    - 公开文章页含上一篇/下一篇或快速文章列表。
    - 普通 base 导航不含管理后台字样。

## 测试策略

- `python3 -m py_compile app/uploader.py`
- `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py tests/test_article_view_permissions.py -q`
- 浏览器打开:
  - `https://aipd.me/articles/fde-databricks-snowflake-20260610.md`
  - 管理员路径 `https://aipd.me/PolaZhenjing/admin/articles/fde-databricks-snowflake-20260610.md`

## 回滚

- 恢复部署前 `app/uploader.py`、`app/templates/base.html`、`app/templates/article_view.html`。
- 服务重启: `systemctl restart polazj.service`。
