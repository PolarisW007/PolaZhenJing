# 发布记录:文章编辑页保存 413 修复

日期:2026-06-09

## 发布范围

- 服务器: `/PolaZhenjing`
- 服务:   `polazj.service`(systemd)
- 备份根: `/opt/backups/`
- 本次发布 1 commit,起点 `7a3ad15`,目标 `dee6bb7`。
  - `dee6bb7 fix(editor): 文章编辑页大 body 不再触发 Werkzeug 413`

## 代码 / 模板(2 文件)

- `app/__init__.py` — 新增 `app.config['MAX_FORM_MEMORY_SIZE'] = 16 * 1024 * 1024`,Werkzeug 默认 500KB 提到 16MB。
- `app/templates/article_edit.html` — 提交时把 `content` 和 `rich_content` 两个 textarea `disabled = true`,避免 body 出现 3 份。

## 测试(1 文件)

- `tests/test_article_edit_413_fix.py` — 3 个用例:500KB / 1MB / 8MB body 都不再 413。

## 文档(5 文件)

- `docs/pola/project-knowledge/requirements/2026-06-09-edit-form-413-fix.md`
- `docs/pola/project-knowledge/specs/2026-06-09-edit-form-413-fix-prd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-09-edit-form-413-fix.md`
- `docs/pola/project-knowledge/test-reports/2026-06-09-edit-form-413-fix-test.md`
- `docs/pola/project-knowledge/release/2026-06-09-edit-form-413-fix-deploy.md`(本文)

## 不动

- nginx 配置 `/etc/nginx/conf.d/polazj.conf` — 不动(已设 `client_max_body_size 16m`)。
- gunicorn 启动参数 — 不动。
- `.env` / `data/` — 不动。
- GitHub Pages Jekyll 工作流 — 不动。
- 之前 6 commit 的代码 / 测试 / 文档 — 已落在云端工作区,本次不动。

## 部署方式

- 服务器: `/PolaZhenjing`
- 方式: 沿用 2026-06-08 的 `git checkout <commit> -- <files>` 模式(精确覆盖本次 3 个文件到云端工作区,不动 git HEAD 和云端 20 个独有 `Add article: ...` commit)。
- 服务: `systemctl restart polazj.service`
- 备注: 本次为同会话第二次走方案 3,无新的备份目录(沿用 `/opt/backups/polazj-editor-rtf-20260609002819/`,73KB + 35KB + env 555B + 18KB)。

## 部署前检查(实际值,回填)

```text
# 远端 origin/main HEAD
git rev-parse --short origin/main          → dee6bb7

# 目标 commit 包含 3 个目标文件
git cat-file -e dee6bb7:app/__init__.py                   → OK
git cat-file -e dee6bb7:app/templates/article_edit.html   → OK
git cat-file -e dee6bb7:tests/test_article_edit_413_fix.py → OK
```

## 发布后验证(实际值,回填)

### 部署动作

```text
ssh root@42.121.164.11
cd /PolaZhenjing
git fetch origin main --quiet
git checkout dee6bb7 -- app/__init__.py app/templates/article_edit.html tests/test_article_edit_413_fix.py
.venv/bin/python3 -m py_compile app/__init__.py            # OK
PYTHONPATH=. .venv/bin/pytest tests -q                     # 34 passed
systemctl restart polazj.service                            # active
journalctl -u polazj.service -n 8 --no-pager               # 新 master 1204021 + workers 1204025/1204026
```

### HTTP smoke(走 https 端到端)

| body 大小 | HTTP 状态 | 期望 | 实际 |
| --- | --- | --- | --- |
| 8KB(原文章) | 302 | 跳详情页 | ✓ |
| 100KB | 302 | 跳详情页 | ✓ |
| 500KB(修复前必 413) | 302 | 跳详情页 | ✓ |
| 1MB | 302 | 跳详情页 | ✓ |

### 编辑页静态断言(云端 Flask test client)

| 关键字 | 期望 | 实际 |
| --- | --- | --- |
| `MAX_FORM_MEMORY_SIZE` 在 `app/__init__.py` | 是 | ✓ |
| `markdown.disabled = true` 在 `article_edit.html` | 是 | ✓ |
| `tests/test_article_edit_413_fix.py` 3 个用例 | 通过 | ✓ |

## 回滚(5 分钟内可走)

**方案 A:从备份恢复**(推荐)

```bash
ssh root@42.121.164.11
cd /PolaZhenjing
# 把工作区 3 个文件恢复到 git HEAD(本次 3 文件以 untracked 形式存在)
git checkout HEAD -- app/__init__.py app/templates/article_edit.html
rm -f tests/test_article_edit_413_fix.py
systemctl restart polazj.service
systemctl is-active polazj.service
```

**方案 B:从远端回滚到 7a3ad15**

```bash
ssh root@42.121.164.11
cd /PolaZhenjing
git checkout 7a3ad15 -- app/__init__.py app/templates/article_edit.html tests/test_article_edit_413_fix.py 2>/dev/null
rm -f tests/test_article_edit_413_fix.py
systemctl restart polazj.service
```

回滚后,8KB 等小 body 仍可保存,500KB+ 大 body 会回到 413(预期行为)。

## 风险

- R1 `MAX_FORM_MEMORY_SIZE` 提到 16MB 后,DoS 攻击面扩大;但本接口受 `@login_required` 保护,只暴露给 admin 角色,实际只有你一个人用,风险可控。
- R2 修复后云端 1MB+ 大 body 首次保存链路延迟略增(< 200ms 经验值),可接受。
- R3 后续若支持「附件上传」或「嵌入 PDF」,单字段会进一步膨胀,届时需要重新评估限制。

## 部署后落地动作

- [ ] 把 `部署前检查` 段的 `___` 占位符确认实际值(已自动回填)。
- [ ] 把 `release/2026-06-08-article-edit-rich-editor-deploy.md` 的「部署后落地动作」清单做完后正式签收。
- [ ] 在浏览器手工 smoke 一遍 `https://aipd.me/PolaZhenjing/admin/articles/rolling-ai-fde-ai-20260607.md/edit`,确认富文本保存正常。
- [ ] 若生产监控显示 P95 延迟上升,关注 `journalctl -u polazj` 是否有大 body 触发的回填 IO 抖动。
