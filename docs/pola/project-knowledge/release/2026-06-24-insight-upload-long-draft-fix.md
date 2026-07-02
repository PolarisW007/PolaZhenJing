# 发布记录：洞察选题导入上传长稿修复

日期：2026-06-24

## 目标

修复 `/PolaZhenjing/admin/upload?insight_topic=724e49daee3e` 只预填一句摘要的问题。预期行为是：

- 洞察选题列表仍只展示摘要，方便扫描。
- 一键导入上传时，Markdown 编辑器预填 5000-30000 可见字符的正文型长稿。
- 上传正文不包含状态、来源类型、评分、证据链接列表等选题池管理元信息。

## 本地发布前验证

- `python3 -m json.tool docs/pola/project-knowledge/delivery/daily-insight-topic-drafts/function_test_cases.json`
- `python3 -m json.tool docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json`
- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py`
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q`
  - 结果：`12 passed in 0.71s`
- `validate_function_test_cases.py` 每日选题底稿：通过，覆盖 10 个验收点、4 个 feature、6 个 case。
- `validate_function_test_cases.py` Admin 工作台：通过，覆盖 6 个验收点、6 个 feature、12 个 case。
- Flask test-client smoke：
  - `/admin/upload?insight_topic=724e49daee3e` 返回 200。
  - textarea `visible_chars=5010`。
  - 包含标题和 `## 核心判断`。
  - 不包含 `## 洞察选题`、`来源类型：`、`选题评分：`、`状态：`。

## 浏览器验证状态

本地 Codex 沙箱阻塞了浏览器级验证：

- 本地 Flask 服务绑定端口失败：`Operation not permitted`。
- Playwright Chromium headless 启动失败：`bootstrap_check_in ... Permission denied (1100)`。

本轮以 Flask test-client HTML smoke 作为替代证据。线上同步后仍需在真实浏览器打开目标 URL 复测。

## 云端执行状态

已完成云端备份：

```text
/opt/backups/polazj-insight-upload-long-draft-20260624205512
```

备份后，当前 Codex 网络沙箱对数据同步会话报错。已尝试 `rsync`、`tar | ssh`、stdin 写入、逐文件 base64 内联分块写入，均无法稳定完成文件传输：

```text
ssh: connect to host 42.121.164.11 port 22: Operation not permitted
```

因此本轮尚未完成云端文件同步、服务重启和线上回归。远端只新增了备份目录，没有替换业务文件。

## 待执行发布命令

网络恢复后，从仓库根目录执行：

```bash
tar -cf - \
  app/insight_topics.py \
  tests/test_admin_workbench_insight_topics.py \
  docs/pola/arch-reference.md \
  docs/pola/project-knowledge/requirements/2026-06-20-daily-insight-topic-drafts.md \
  docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-drafts-prd.md \
  docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-drafts-spec.md \
  docs/pola/project-knowledge/architecture/2026-06-20-daily-insight-topic-drafts-sdd.md \
  docs/pola/project-knowledge/delivery/daily-insight-topic-drafts/function_test_cases.json \
  docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json \
  docs/pola/project-knowledge/devlogs/2026-06-20-daily-insight-topic-drafts.md \
  docs/pola/project-knowledge/release/2026-06-24-insight-upload-long-draft-fix.md \
| ssh pola-server 'cd /PolaZhenjing && tar -xf -'
```

云端验证：

```bash
ssh pola-server 'cd /PolaZhenjing && python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py'
ssh pola-server 'cd /PolaZhenjing && PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q'
ssh pola-server 'sudo systemctl restart polazj.service && sudo systemctl is-active polazj.service'
```

线上 smoke：

```bash
ssh pola-server 'cd /PolaZhenjing && PYTHONPATH=. .venv/bin/python - <<PY
import html
from app import create_app
from app import insight_topics

app = create_app()
app.config["TESTING"] = True
client = app.test_client()
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["role"] = "admin"
response = client.get("/admin/upload?insight_topic=724e49daee3e")
body = response.get_data(as_text=True)
value = html.unescape(body.split("id=\\\"content\\\"", 1)[1].split(">", 1)[1].split("</textarea>", 1)[0])
print(response.status_code)
print(insight_topics._draft_word_count(value))
print("## 核心判断" in value)
print(any(x in value for x in ["## 洞察选题", "来源类型：", "选题评分：", "状态："]))
PY'
```

## 回滚

如上线后发现上传页异常，可从备份恢复：

```bash
ssh pola-server 'cd /PolaZhenjing && backup=/opt/backups/polazj-insight-upload-long-draft-20260624205512 && cp -a "$backup/app/insight_topics.py" app/insight_topics.py && sudo systemctl restart polazj.service'
```
