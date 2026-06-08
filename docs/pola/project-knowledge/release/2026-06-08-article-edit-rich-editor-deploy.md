# 发布记录:文章编辑页 TinyMCE + 上传页稳定性 + skillhub 守卫

日期:2026-06-08(部署执行时回填真实时间)

## 部署前快照

- 本次发布 5 commit,起点 `ee4c10b`,目标 `360deb3`。
  - `296e6f9` feat(editor): 文章编辑页接入 TinyMCE 富文本编辑器
  - `de68133` feat(editor): 上传页 TinyMCE 编辑器稳定性收尾
  - `258ed24` feat(skillhub): skillhub 与 jobs 后台任务守卫
  - `683ad52` docs(ops): 补录后台无前缀 URL 404 兼容修复交付记录
  - `360deb3` chore(docs): 去掉 3 个 skillhub 守卫文档的多余末尾换行
- 本地 `git push -u origin main` 已完成,远端 `origin/main` HEAD = `360deb3`。
- 服务器: `/PolaZhenjing`。
- 服务:   `polazj.service`(systemd)。
- 备份根: `/opt/backups/`。

## 发布范围

### 代码 / 模板(2 文件)

- `app/templates/article_edit.html` — 全文替换为 TinyMCE 双模式编辑器,539 行变更。
- `app/templates/upload.html` — 补 .tox-tinymce flex / 高度 360px 兜底、TinyMCE 缓存版本参数。
- `app/uploader.py` — `preview_article_markdown` 接受 `content_format`,`rich_html` 直出。

### 静态资源(1 文件)

- `assets/vendor/tinymce/tinymce-manifest.json` — 新增。

### 测试(2 文件)

- `tests/test_article_edit_rich_editor.py` — 新增 4 用例。
- `tests/test_social_publish.py` — 增强本地 TinyMCE 断言 + 新增 `test_admin_links_respect_script_name_prefix`。

### 文档(7 文件)

- `docs/pola/project-knowledge/requirements/2026-06-08-article-edit-rich-editor.md`
- `docs/pola/project-knowledge/specs/2026-06-08-article-edit-rich-editor-prd.md`
- `docs/pola/project-knowledge/devlogs/2026-06-08-article-edit-rich-editor.md`
- `docs/pola/project-knowledge/test-reports/2026-06-08-article-edit-rich-editor-test.md`
- 其它 3 个补充/收尾文档来自前置 4 个 commit。

### 不动

- `app/__init__.py` / `app/jobs.py` / `app/skillhub.py` — 本次已合入前置 commit,本次部署自然包含。
- nginx 配置 `/etc/nginx/conf.d/polazj.conf` — 不动。
- `.env` / `data/` — 不动。
- GitHub Pages Jekyll 工作流 `.github/workflows/deploy.yml` — 不动,本次只更新 Flask 后端。

## 部署方式

- 服务器: `/PolaZhenjing`
- 方式: 自动化脚本 `scripts/deploy_editor_rtf_to_cloud.sh`(本地仓库根,scp 到云端后 sudo bash 执行)
- 同步路径: 仓库 `git pull --ff-only origin main`(脚本里加了 HEAD 校验,防错拉)
- 服务: `systemctl restart polazj.service`

## 部署前检查(在云端跑出的实际值,部署时回填)

```text
# step 0 pre-release
systemctl is-active polazj.service             → ___
git rev-parse --short HEAD                     → ___(部署前是 ___)
git log --oneline -3                           → ___ / ___ / ___
git merge-base --is-ancestor 360deb3 origin/main  → true

# step 1 备份
BACKUP_DIR=/opt/backups/polazj-editor-rtf-20260608____
ls -lh $BACKUP_DIR                             → ___

# step 3 门禁
.venv/bin/python3 -m py_compile ...            → 无输出(通过)
PYTHONPATH=. .venv/bin/pytest tests -q         → 34 passed
```

## 发布后验证(部署时回填实际值)

### 服务与日志

```text
systemctl is-active polazj.service             → active
journalctl -u polazj.service -n 30 --no-pager  → 启动无 traceback,见末尾
```

### 关键 HTTP smoke

| URL | 期望 | 实际 |
| --- | --- | --- |
| `/PolaZhenjing/assets/vendor/tinymce/tinymce-manifest.json` | 200 | ___ |
| `/PolaZhenjing/assets/vendor/tinymce/tinymce.min.js` | 200 | ___ |
| `/PolaZhenjing/assets/vendor/tinymce/langs/zh-Hans.js` | 200 | ___ |
| `/PolaZhenjing/admin/login`(未登录) | 200 | ___ |
| `/PolaZhenjing/admin/upload`(未登录) | 302 → login | ___ |
| `/PolaZhenjing/admin/articles/2026-04-11-test-article.md/edit`(临时 admin session) | 200 | ___ |

### Flask test client 编辑页断言(脚本 step 5 末尾那段)

| 关键字 | 期望 | 实际 |
| --- | --- | --- |
| `easymde` | 不在 body | ___ |
| `tinymce.min.js?v=6.8.5-pzj-20260602` | 在 body | ___ |
| `cache_suffix: TINYMCE_CACHE_SUFFIX` | 在 body | ___ |
| `editor_mode` | 在 body | ___ |
| `rich-content` | 在 body | ___ |
| `content-format` | 在 body | ___ |

### 浏览器手工 smoke(可选,推荐)

打开 `https://aipd.me/PolaZhenjing/admin/articles/<任意文章>/edit`:

- 顶部出现「富文本编辑 / Markdown 源码」单选。
- 默认进 Markdown 源码(因 body 是 Markdown);切到富文本后 TinyMCE 工具栏出现,中文,粘贴文本/图片可用。
- 底部「渲染预览」随模式实时刷新。
- 保存 → 跳回 `/PolaZhenjing/admin/articles/<file>.md`,成功 flash 提示「文章已保存。」

## 回滚(单段命令,5 分钟内)

```bash
ssh <user>@aipd.me
cd /PolaZhenjing
git reset --hard ee4c10b
systemctl restart polazj.service
systemctl is-active polazj.service   # 期望 active
```

或仅回滚代码(保留新 docs,从备份恢复 templates / uploader.py / tests):

```bash
BACKUP=$(cat /tmp/polazj_editor_rtf_last_backup)
cd /PolaZhenjing
tar -xzf "$BACKUP/app-templates.tgz" -C .
tar -xzf "$BACKUP/tests.tgz"         -C .
systemctl restart polazj.service
```

回滚后再跑一次 smoke 确认:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://aipd.me/PolaZhenjing/admin/login  # 200
curl -sS -o /dev/null -w "%{http_code}\n" https://aipd.me/PolaZhenjing/admin/upload  # 302
```

## 风险

- R1 `article_edit.html` 全文 539 行替换,任何 tiny 模板语法问题都会让编辑页白屏;烟囱测试有断言,但 502/500 仍可能在某些 front matter / 字符边界触发。回滚命令已备好。
- R2 `preview_article_markdown` 行为变更(增加 `content_format`),可能影响其它调用方(目前只在 article_edit 调用,无其它调用)。
- R3 本地 `git push` 与云端 `git pull` 之间的窗口期内,如果有新 commit 进来会导致 ff 失败;脚本里有 `git merge-base --is-ancestor` 守卫。
- R4 skillhub 守卫 5 个新环境变量是 **可选**(都有默认值),本次部署不主动写 `.env`,但要让运维知道:
  - `SKILLHUB_CACHE_TTL_SECONDS`(默认 300)
  - `SKILLHUB_MAX_ZIP_BYTES`(默认 25MB)
  - `SKILLHUB_MAX_ZIP_FILES`(默认 500)
  - `SKILLHUB_MAX_EXTRACTED_BYTES`(默认 50MB)
  - `SKILLHUB_MAX_DOWNLOAD_BYTES`(默认 25MB)
  - `SKILLHUB_MAX_DOWNLOAD_FILES`(默认 500)
  - `POLAZJ_JOB_MAX_WORKERS`(默认 2)

## 部署后落地动作

- [ ] 把本文件 `发布后验证` 段、`发布前检查` 段的 `___` 占位符回填实际值。
- [ ] 把 `BACKUP_DIR=/opt/backups/polazj-editor-rtf-20260608____` 替换为真实路径。
- [ ] 截取 `journalctl -u polazj.service -n 30 --no-pager` 输出贴到本文档底部或附图。
- [ ] 浏览器手工 smoke 截图后,补到 `docs/pola/project-knowledge/release/` 同目录或 commit 一次 `test-reports/2026-06-08-...-smoke.md`。
- [ ] 如果走 rsync 精确同步而不是 git pull(云端 /PolaZhenjing 有未提交改动),把哪些文件覆盖了记到本文档。
