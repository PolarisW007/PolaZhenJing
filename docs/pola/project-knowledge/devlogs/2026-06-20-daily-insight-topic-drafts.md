# 开发日志：每日选题 5000 字底稿

## 背景

用户指出每日选题需要每篇自带约 5000 字底稿，列表只显示摘要；一键导入上传时，完整底稿必须预输入到上传页 Markdown 编辑器。当前实现只导入标题、角度、摘要和证据链接。

2026-06-21 补充：用户反馈选题列表红框区域和一键导入上传正文只需要具体摘要内容，来源、证据、评分、标签、状态、底稿字数等信息对编辑不重要，进入 upload 时也不应把这些元信息放入正文。

## 计划

- 扩展选题数据字段：`draft_markdown`、`draft_word_count`。
- 在读取/保存/刷新时自动补齐底稿。
- 列表页只展示摘要，不展示来源、证据、评分、标签和底稿字数。
- 导入上传页只预填摘要正文，长底稿保留在数据层。
- 补测试和 harness 证据。

## 改动

- `app/insight_topics.py`
  - 新增确定性 Markdown 底稿生成器，目标约 5000 字，最低 4500 可见字符。
  - `_normalize_topic()` 自动补齐 `draft_markdown` 和 `draft_word_count`，兼容旧 JSON。
  - `build_upload_prefill()` 按 2026-06-21 反馈改为只预填摘要正文，不再写入来源、证据、状态、评分或底稿章节。
  - 2026-06-24 修正：`build_upload_prefill()` 改为从 `draft_markdown` 派生 upload 专用正文型长稿，保留标题和 `## 导语` 之后的正文章节，剔除来源、状态、评分、证据链接等选题池管理元信息；剔除后不足 5000 可见字符时追加正文延展段。
- `app/templates/insight_topics.html`
  - 选题卡片正文区只展示摘要，不展示来源、证据、评分、标签和底稿字数。
- `app/templates/admin_workbench.html`
  - 工作台今日选题继续展示底稿字数，用于管理概览。
  - 去除钉钉底料入口和旧说明，改为线上信号与 Markdown 草稿导入说明。
- `app/templates/upload.html`
  - 修复导入选题后空富文本编辑器抢占可见区域的问题。
  - 当 `insight_prefill` 存在时默认只展示 Markdown textarea，不主动初始化 TinyMCE；用户切换到富文本时再加载转换。
- `tests/test_admin_workbench_insight_topics.py`
  - 增加底稿字段、长度、列表不泄露全文断言。
  - 增加工作台不再展示钉钉底料入口、导入页出现 Markdown 就绪提示的断言。
  - 补充摘要-only 断言：列表不展示来源/评分/底稿字数，上传预填不包含证据链接和底稿章节。
  - 2026-06-24 修正断言：列表仍摘要-only；导入上传页 textarea 必须包含 5000-30000 可见字符长稿、`## 核心判断`，且不包含来源、状态、评分等元信息。
- `docs/pola/arch-reference.md`
  - 记录选题池新增长底稿字段和导入语义。

## 验证

- 2026-06-24 upload 长稿导入修正验证：
  - 目标生产选题 `724e49daee3e` 本地 smoke：`build_upload_prefill()` 生成 `visible_chars=5010`、包含 `## 核心判断` 和 `## 延展观察`，不包含 `## 洞察选题`、`来源类型：`、`选题评分：`、`状态：`。
  - `python3 -m json.tool docs/pola/project-knowledge/delivery/daily-insight-topic-drafts/function_test_cases.json` 通过。
  - `python3 -m json.tool docs/pola/project-knowledge/delivery/admin-workbench-insight-topics/function_test_cases.json` 通过。
  - `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py` 通过。
  - `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q` 通过，`12 passed in 0.71s`。
  - `validate_function_test_cases.py` 对每日选题底稿文档通过，覆盖 10 个验收点、4 个 feature、6 个 case。
  - `validate_function_test_cases.py` 对 Admin 工作台文档通过，覆盖 6 个验收点、6 个 feature、12 个 case。
  - Flask test-client smoke：`/admin/upload?insight_topic=724e49daee3e` 返回 200，Markdown textarea `visible_chars=5010`、包含标题和 `## 核心判断`、不包含 `## 洞察选题`、`来源类型：`、`选题评分：`、`状态：`。
  - Playwright 本地浏览器验证阻塞：当前 Codex 沙箱不允许本地 Flask 绑定端口，且 Chromium headless 启动时被 macOS MachPort 权限拒绝（`bootstrap_check_in ... Permission denied (1100)`）；本轮以 Flask test-client HTML/DOM smoke 替代记录，线上发布后仍需在真实浏览器复测。
  - 云端备份完成：`/opt/backups/polazj-insight-upload-long-draft-20260624205512`。
  - 云端同步阻塞：备份后 rsync、tar 管道和逐文件 SSH 写入均被当前网络沙箱拒绝，报 `ssh: connect to host 42.121.164.11 port 22: Operation not permitted`；发布 runbook 已记录在 `docs/pola/project-knowledge/release/2026-06-24-insight-upload-long-draft-fix.md`。

- 2026-06-21 摘要-only 修正验证：
  - `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py` 通过。
  - `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q` 通过，`12 passed in 0.69s`。
  - `validate_function_test_cases.py` 对每日选题底稿文档通过，覆盖 10 个验收点、4 个 feature、6 个 case。
  - `validate_function_test_cases.py` 对 Admin 工作台文档通过，覆盖 6 个验收点、6 个 feature、12 个 case。
  - Flask test-client smoke：`/admin/insights/topics` 仅展示摘要，不包含来源、评分、底稿字数；导入上传页 textarea 与 `topic.summary` 完全一致，不包含 `## 证据链接`、`来源类型`、`状态：` 或 `## 核心判断`。
- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`
  - 通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`
  - 通过，`6 passed in 0.61s`。
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/requirements/2026-06-20-daily-insight-topic-drafts.md --prd docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-drafts-prd.md --sdd docs/pola/project-knowledge/architecture/2026-06-20-daily-insight-topic-drafts-sdd.md --spec docs/pola/project-knowledge/specs/2026-06-20-daily-insight-topic-drafts-spec.md --cases docs/pola/project-knowledge/delivery/daily-insight-topic-drafts/function_test_cases.json`
  - 通过，覆盖 8 个验收点、3 个 feature、4 个 case。
- Flask test-client smoke：
  - 样例 `draft_word_count=5048`。
  - `/admin/insights/topics` 展示底稿字数，未泄露底稿结尾句。
  - `/admin/insights/topics/<id>/import` 跳转上传页后包含 `## 核心判断`、底稿结尾句和 `状态：已导入`。
- Playwright 本地烟测：
  - 导入选题后上传页 `#content` 可见、`#rich-content` 隐藏。
  - Markdown textarea 长度 5806，包含 `## 核心判断`。
  - `window.tinymce=false`，说明导入模式不再主动加载空富文本编辑器。
  - 页面不包含 `钉钉底料`。

## 风险与护栏

- 风险等级：P2。
- 不新增外部 LLM 调用，不新增定时任务，不修改生产配置。
- 底稿控制在约 5000 字，避免 JSON 和页面体积无界增长。
- TinyMCE 延迟加载只影响带 `insight_topic` 的上传页；普通粘贴上传页仍按原逻辑默认富文本模式。

## 云端发布补充

- 备份目录：`/opt/backups/polazj-insight-import-prefill-20260620232418`。
- 发布方式：精确同步 `app/insight_topics.py`、上传页/选题页/工作台模板、相关测试与文档，不覆盖 `_posts/`、`.env`、上传图片或运行时缓存。
- 云端验证：
  - `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py` 通过。
  - `PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q` 通过，`12 passed in 1.49s`。
  - 认证态 Flask smoke 确认导入真实选题后上传页 200，Markdown textarea 长度 6127，包含 `## 核心判断` 和 `Markdown 源码模式已就绪`，不包含旧的无条件 `initRichEditor()` 逻辑。
  - `/admin/workbench` 和 `/admin/insights/topics` 云端页面不再包含 `钉钉底料`。
  - `polazj.service` 重启后为 `active`，近 5 分钟 journal 只有正常 stop/start 和 gunicorn worker boot。
- 验证用生产选题 `ab0a9d1435d9` 的状态已恢复为 `new`，避免测试污染选题池。
- 云端 function test cases harness 未执行，原因是服务器没有本机 `/Users/wangchang/.agents/skills/...` 技能脚本路径；本机 harness 已通过。

## 云端发布补充 2026-06-21

- 备份目录：`/opt/backups/polazj-insight-summary-only-20260621232152`。
- 发布方式：精确同步摘要-only 相关代码、测试和文档，不覆盖 `_posts/`、`.env`、上传图片或运行时缓存。
- 云端验证：
  - `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/uploader.py app/__init__.py` 通过。
  - `PYTHONPATH=. .venv/bin/pytest tests/test_admin_workbench_insight_topics.py tests/test_upload_rewrite_rate.py -q` 通过，`12 passed in 1.21s`。
  - 认证态 Flask smoke 确认选题页 200，包含摘要，不包含来源、评分、底稿字数；上传页 200，Markdown textarea 与 `topic.summary` 完全一致，长度 211，不包含证据链接、来源、状态、评分或底稿章节。
  - 公网匿名访问 `/PolaZhenjing/admin/insights/topics` 按预期跳转登录页，登录页 200。
  - `polazj.service` 重启后为 `active`，journal 只有正常 stop/start 和 gunicorn worker boot。

## Commit 状态

- 尚未提交。
