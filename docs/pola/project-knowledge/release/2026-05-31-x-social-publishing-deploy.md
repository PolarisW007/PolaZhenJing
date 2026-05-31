# 发布记录：X 自动发布

日期：2026-05-31

## 发布范围

- `app/social_publish.py`
- `app/templates/social_publish_article.html`
- `app/templates/social_publish_index.html`
- `tests/test_social_publish.py`
- `docs/pola/arch-reference.md`
- `docs/pola/project-knowledge/requirements/2026-05-31-x-social-publishing.md`
- `docs/pola/project-knowledge/specs/2026-05-31-x-social-publishing-prd.md`
- `docs/pola/project-knowledge/architecture/2026-05-31-x-social-publishing-sdd.md`
- `docs/pola/project-knowledge/devlogs/2026-05-31-x-social-publishing.md`

## 部署方式

- 服务器：`/PolaZhenjing`
- 方式：精确 `rsync` 本次相关文件，未触碰服务器既有无关改动。
- 服务：重启 `polazj.service`。

## 发布后验证

- 云端 `python3 -m py_compile app/social_publish.py app/__init__.py`：通过。
- 云端 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py`：9 passed。
- 云端 `systemctl is-active polazj.service`：`active`。
- 线上 `https://aipd.me/PolaZhenjing/admin/social/`：未登录返回 302 到 `/PolaZhenjing/admin/login`。
- 云端 X 配置状态：`X_USER_ACCESS_TOKEN` 未配置；当前版本不会误调用 X API。

## 回滚

- 回滚本次代码文件并重启 `polazj.service`。
- 已产生的 `platform=x` 发布记录可保留，不影响微信和人工发布包路径。
