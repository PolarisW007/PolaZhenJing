# Devlog：上传文章 AI 生图四档模式

日期：2026-08-18

状态：开发完成（本地验证通过，钉钉同步被登录态阻塞）

## 目标

在文章上传生成流程增加题图、概括 3 张、适中 5 张、详细逐段四档 AI 生图模式，并为详细模式补齐数量、时间和失败降级护栏。

## A2A 阶段记录

- `pola-a2a-usage` / `pola-agent-delivery-framework`：按 Ship ready 模式执行，生产部署不在授权范围。
- project-context：已确认 Flask/Jinja 上传页、draft JSON、SQLite 有界后台任务、MiniMax 文本/图片生成、图片合并注入和 Jekyll 写入链路。
- requirement：`docs/pola/project-knowledge/requirements/2026-08-18-upload-ai-image-modes.md`。
- PRD/SPEC：`docs/pola/project-knowledge/specs/2026-08-18-upload-ai-image-modes-prd.md`。
- architecture：`docs/pola/project-knowledge/architecture/2026-08-18-upload-ai-image-modes-sdd.md`。
- release：`docs/pola/project-knowledge/release/2026-08-18-upload-ai-image-modes-release.md`。

## 既有脏工作区隔离

- `app/uploader.py` 已有 MiniMax 文本 API 官方端点改动，与生图代码同文件；保留且不回滚，本次最终 diff 会单独说明其归属。
- `app/agent.py` 和 2026-08-15 MiniMax M3 文档属于用户既有改动，本次不修改、不纳入建议提交范围。
- `.qoder/skills/`、`tmp/` 属于既有未跟踪内容；本次浏览器截图如写入 `tmp/` 仅作为本地证据，不建议提交。

## 计划改动

- `app/templates/upload.html`：三种输入表单增加四档生图 radio 卡片。
- `app/uploader.py`：模式解析/传递、精确数量、详细逐段、批次预算和任务消息。
- `tests/test_upload_image_modes.py`：新增模式与安全护栏测试。
- `tests/test_upload_rewrite_rate.py`：调整既有替身签名，证明改写率路径仍兼容。
- `scripts/upload_edit_playwright_harness.py`：增加四档 UI 与默认状态的真实浏览器断言和截图。
- `docs/pola/project-knowledge/delivery/upload-ai-image-modes/`：维护状态、用例、测试和回归证据。

## 稳定性与安全门禁

- 风险等级：P2。
- 并发：复用 `app/jobs.py` 最大 2 worker。
- 数量：详细正文图最大 12；其它模式固定数量。
- 超时：整批 900 秒，单请求受剩余预算约束。
- 容量：单图 12MB、单篇 AI 图片批次 64MB，API 响应和 URL 下载均有累计字节上限。
- 失败：不做无界重试；逐张失败继续文章。
- secret：不输出/记录 key、cookie、token 或 `.env` 内容。
- 不影响功能路径：旧入口、AI 改写率、原媒体、用户图、旧 draft、风格选择、文章写入、登录态保持不变。

## 验证记录

- 最小语法检查：`.venv/bin/python -m py_compile app/uploader.py app/jobs.py app/__init__.py scripts/upload_edit_playwright_harness.py`，通过。
- 最小实现测试：`.venv/bin/python -m pytest tests/test_upload_image_modes.py tests/test_upload_rewrite_rate.py -q`，初次 19 passed。
- Review 修复后测试：同一命令，21 passed。
- `git diff --check`：Review 修复后通过。
- 关联回归：`.venv/bin/python -m pytest tests/test_upload_image_modes.py tests/test_upload_rewrite_rate.py tests/test_social_publish.py tests/test_article_auto_tagging.py tests/test_article_edit_rich_editor.py tests/test_article_edit_413_fix.py tests/test_article_content.py tests/test_jobs_guard.py -q`，68 passed。
- 全量回归：`.venv/bin/python -m pytest tests -q`，120 passed。
- 功能用例门禁：`validate_function_test_cases.py`，9 个验收项、9 个 feature、17 个 case 全部覆盖。
- 本地真实浏览器：Playwright 桌面端 1440x1100、手机端 390x844 及旧编辑/保存路径共 4 张截图，断言通过。
- Pola A2A Harness：`validate_pola_skills.py`，`PASS: Pola skill harness found no issues.`
- 真实 MiniMax T2I：未调用，避免未授权的付费请求；provider 成功率和美学质量作为上线后小流量观察项。

## Code Review

- 结论：Pass，无 P0/P1。
- 已修复 P2：整批 900 秒预算改为包含视觉规划时间。
- 已修复 P2：题图插入不再导致原始正文段落锚点整体偏移。
- 已修复 P2：MiniMax 图片响应、单图和整批二进制增加上限，下载日志不再记录可能带签名参数的完整 URL。
- 残余风险：真实 provider 成功率、耗时和审美质量需上线后小流量验证；本轮不具备生产授权。

## Git 与发布状态

- commit：用户已于 2026-08-18 明确要求执行，待形成本需求独立 commit。
- push：作为生产从 `origin/main` 发布的必要步骤，已包含在本次授权中。
- deploy/restart：用户已明确授权生产部署与 `polazj.service` 重启；执行后回填结果。
- `git diff --check`：通过。
- 本任务新增文件行尾空白扫描：通过。
- 本任务文件常见 secret/private-key 模式扫描：通过（仅输出文件名模式，未读取 `.env`）。

### 发布前生产基线

- 本地、`origin/main`、生产 `main` 均为 `9eb1efee5c7716f59aa98b3c20b8afed809fb2f4`。
- `polazj.service` 为 active；发布前进程内存约 184MB，近 15 分钟 warning 计数为 1，作为发布后对比基线。
- 生产根盘使用率 93%，剩余约 3.3GB；`/opt/backups` 约 3.7GB、journald 约 1.6GB。本次仅增加约 192KB 运行文件备份，不进行未授权的旧备份/日志清理。
- 生产存在 `_posts/` 和 `data/` 的已有跟踪内容改动；部署采用 `git pull --ff-only`，若 Git 判定有重叠则立即停止，不覆盖内容文件。

## 钉钉同步状态

- 目标文件夹：`Pola开发日志记录文件`，原始 node URL 已按 DWS 规范执行类型探测。
- 目标 AI 表格：`开发日志`，计划回填 `来源文件` 并回读 `更新内容` AI 字段。
- 实际结果：阻塞。`dws profile list --format json` 显示当前组织 profile 的访问令牌已于 2026-08-14 过期；`dws doc info --node <folder-url> --format json` 返回 `not_authenticated`，明确要求执行 `dws auth login`。
- 未执行：未创建钉钉文档，未更新 AI 表格，因此不存在部分写入或需要回滚的外部状态。
- 解除 blocker：用户在本机完成 `dws auth login` 后，重试文件夹 probe → 项目目录列表 → `doc create --content-file` → `doc read` 回读 → AI 表字段/记录查询 → 回填 `来源文件` → 记录回读。
