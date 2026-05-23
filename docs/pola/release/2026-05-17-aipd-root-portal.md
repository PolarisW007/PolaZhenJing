# AIPD 根入口首页发布清单

文件注释：
- 模块名称：AIPD 根入口首页发布清单
- 功能描述：记录部署步骤、验证项和回滚命令
- 创建日期：2026-05-17
- 作者：Codex
- 主要变更：2026-05-17 初始创建
- 依赖模块：Nginx、/var/www/html、portal 静态文件

## 发布范围

- 新增根入口静态文件：
  - `/var/www/html/index.html`
  - `/var/www/html/assets/portal.css`
  - `/var/www/html/assets/portal-sections.css`
  - `/var/www/html/assets/portal.js`
- 更新 Nginx `aipd.me` server 块：
  - `location = /` 指向 `/var/www/html/index.html`
  - `location /assets/` 指向 `/var/www/html/assets/`

## 发布命令

```bash
rsync -av portal/ pola-server:/var/www/html/
```

Nginx 配置已备份到：

```text
/etc/nginx/conf.d/polazj.conf.bak.20260517221445
```

配置变更验证：

```bash
nginx -t
systemctl reload nginx
```

## 发布后验证

```bash
curl -k -I https://aipd.me/
curl -k -L https://aipd.me/ | head
```

浏览器验证：

- 打开 `https://aipd.me/`
- 检查导航与四个模块区块。
- 检查 `/PolaZhenjing/`、`/PolaRead/`、`/polanews`、`/xumishan/` 子路径不受影响。

## 回滚命令

```bash
ssh pola-server 'rm -f /var/www/html/index.html /var/www/html/assets/portal.css /var/www/html/assets/portal.js'
ssh pola-server 'cp /etc/nginx/conf.d/polazj.conf.bak.20260517221445 /etc/nginx/conf.d/polazj.conf && nginx -t && systemctl reload nginx'
```

## 风险等级

低到中。新增根目录静态文件，并为 `aipd.me` 增加精确根路径和资源路径映射；未改 systemd 服务。2026-05-17 二次主题优化只同步静态文件，未再次改 Nginx 配置。
