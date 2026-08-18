# Release Plan：上传文章 AI 生图四档模式

日期：2026-08-18

状态：Deployed（产品 commit `ed3d89fa58796ffdb4a12ecc20e69ffdf15e2170` 已于 2026-08-19 部署并通过生产验证）

## 发布输入审计

| 项 | 内容 | 证据 | 缺口 |
| --- | --- | --- | --- |
| 本地版本 | 运行时产品 commit `ed3d89fa58796ffdb4a12ecc20e69ffdf15e2170` + 本发布记录所在 docs commit | `git rev-parse HEAD` | 无 |
| 远端版本 | `origin/main` 包含产品 commit 与本发布记录 | `git push origin main` | 无 |
| 生产版本 | 运行文件来自 `ed3d89f`；仓库 HEAD 在收尾时同步至本发布记录 commit；`polazj.service=active` | SSH HEAD/blob/systemd 验证 | 无 |
| Requirement/PRD/SDD | 已完成 | 2026-08-18 三份文档 | 无 |
| Review | Pass，3 个 P2 已修复，无 P0/P1 | `analysis/2026-08-18-upload-ai-image-modes-review.md` | 无 |
| 测试 | 21 core / 68 related / 120 full；用例 validator/Harness Pass | `test-reports/2026-08-18-upload-ai-image-modes-test.md` | 真实 provider 未测 |
| 回归 | 本地桌面/手机 Playwright Pass | `delivery/upload-ai-image-modes/regression_evidence.json` | 线上未测 |

## 发布结论

- 本地代码、review、测试、浏览器回归和回滚 runbook 已达到 Ship ready；用户已授权提交、push、生产文件更新与 `polazj.service` 重启。
- 发布前全量回归再次通过：120 passed；`git diff --check` 和常见 secret 特征扫描通过。
- 生产根盘使用率 93%，剩余约 3.3GB；本次仅备份约 192KB 运行文件且不生成构建产物，可继续，但不在本次授权中清理旧备份或 journald。
- 产品 commit 已推送、生产 fast-forward 成功，生产全量测试 120 passed，服务重启后 active；发布结论为 **Deployed**。

## 发布面

- `app/uploader.py`
- `app/templates/upload.html`
- 与本需求直接相关的测试和本地 harness
- `docs/pola/arch-reference.md` 与本次项目知识库记录
- 无数据库 schema、secret、必需环境变量和历史内容迁移

## 发布前检查

1. 确认 review 无 P0/P1。
2. 运行 `python -m py_compile`、相关 pytest、功能用例 validator、Playwright harness。
3. 运行 `git diff --check` 与本次 diff secret 扫描。
4. `git fetch` 后核对本地待发布 commit、`origin/main` 和生产实际 commit 三方一致。
5. 核对生产 `polazj.service` 状态、CPU/内存、磁盘可用空间、近 15 分钟 warning/error 日志；项目未提供 `server_runtime_monitor.py`，需以 systemd/进程/磁盘命令记录同等基线证据。
6. 确认本次文件清单不包含 `app/agent.py`、2026-08-15 文档、`.qoder/skills/` 或 `tmp/` 等用户既有无关改动。
7. 备份生产目标文件，记录可恢复路径；不备份/输出 `.env` 内容。

## 建议发布步骤（每个生产写步骤都需用户另行明确确认）

| 步骤 | 动作 | 风险 | 需确认 |
| --- | --- | --- | --- |
| 1 | 记录生产 commit、服务、CPU/内存、磁盘与错误日志基线 | 只读 | 否 |
| 2 | 备份 `app/uploader.py`、`app/templates/upload.html` | 产生约 192KB 备份文件/磁盘占用 | 用户已授权 |
| 3 | `git pull --ff-only origin main`，保留生产 `_posts/` 和 `data/` 已有修改；如 Git 检测到冲突立即停止 | 修改生产代码与文档 | 用户已授权 |
| 4 | 在生产虚拟环境运行语法检查和本次相关 pytest | 读取代码/可能写 pytest 临时缓存 | 用户已授权 |
| 5 | 确认没有 pending/running 生成任务后重启 `polazj.service` | 短暂中断后台请求；有运行任务则停止不重启 | 用户已授权 |
| 6 | 检查服务 active、进程内存和启动日志 | 只读 | 否 |
| 7 | 登录线上上传页，检查三 Tab 的四档模式、默认适中和响应式布局 | 读取页面 | 需要管理员账号 |
| 8 | 使用短样例分别执行“只生成题图”和“适中” | 写入文章、调用付费/限额第三方 API、可能触发安全 Git 同步 | 是 |
| 9 | 观察 15 分钟 CPU、内存、磁盘增长、任务失败率和 MiniMax warning | 只读 | 否 |

## 发布后验证

- `/PolaZhenjing/admin/upload` 登录后 200，三个表单均有 4 个模式。
- 旧文章列表/查看、富文本媒体上传、AI 改写率、风格选择可用。
- 生成任务状态从 pending/running 到 done；图片失败时文章仍完成。
- `polazj.service` active，近 15 分钟无新增 traceback/OOM/磁盘告警。
- 对比发布前后 CPU、RSS、磁盘可用量和 `jobs` pending/running/failed 数；详细模式不得造成持续增长或任务堆积。
- 日志只核对异常类型、模式和计数，不打印 `.env`、Authorization、key、cookie 或带签名参数的完整 URL。

## 回滚

触发条件：服务无法启动、上传页 5xx/关键布局不可用、旧上传/编辑路径回归、任务持续失败、CPU/内存/磁盘异常增长，或图片调用数量不符合 1/3/5/详细上限。

1. 恢复本次发布前备份的 `app/uploader.py` 和 `app/templates/upload.html`。
2. 重启 `polazj.service` 并检查 active。
3. 复测旧上传 → 风格 → 生成路径。
4. 新 draft 的 `image_generation_mode` 字段可保留；旧实现会忽略额外 JSON 字段。
5. 已生成文章和图片属于用户内容，不自动删除；如需删除必须另行确认具体目标。

回滚后验证：服务 active、上传页登录后 200、旧上传 → 风格 → 生成路径完成、近 15 分钟无新增 traceback。通知对象为本项目管理员/内容发布者；若真实生图产生异常费用，暂停新任务并记录受影响 job ID，不擅自删除文章。

## 发布边界

- 产品 commit 只包含本需求，已排除 `app/agent.py`、`app/uploader.py` 中既有 MiniMax 端点 hunk、2026-08-15 文档、`.qoder/skills/` 与 `tmp/`。
- 生产 fast-forward 保留了 `_posts/` 和 `data/` 中的已有运行内容改动，未 reset、stash 或覆盖。
- 线上仅执行无付费副作用的页面/代码探针；不自动发起真实 MiniMax T2I 请求或生成正式文章。

## 2026-08-19 部署执行记录

- Git：产品 commit `ed3d89fa58796ffdb4a12ecc20e69ffdf15e2170` 已推送至 `origin/main`。
- 部署前：生产 HEAD 与远端均为 `9eb1efee5c7716f59aa98b3c20b8afed809fb2f4`；`polazj.service=active`，pending/running jobs 为 0。
- 备份：已备份 `app/uploader.py` 与 `app/templates/upload.html`，备份大小 208KB，记录了回滚 HEAD。
- 更新：`git pull --ff-only origin main` 成功，生产 HEAD 到达 `ed3d89f`；运行文件 blob 与 commit tree 一致。
- 生产测试：`py_compile` 通过；本次核心测试 21 passed；项目正常命令的全量测试 120 passed。首次额外注入 `PYTHONPATH=.` 时出现 1 个既有 CLI 导入失败，去掉该非项目标准环境变量后全量通过。
- 重启：重启前再次确认 active jobs 为 0；`polazj.service` 重启后 active，PID 已更新。
- HTTP：公网 `/admin/login` 为 200，`/admin/upload` 未登录为 302 到登录页。生产应用内登录态探针为 200，检出 12 个模式 radio、3 个默认“适中”且四个标签齐全。
- 运行时：完成 15 分钟发布后观察；内存稳定在约 93MB，`journalctl -q` 复核 warning/error 均为 0，active jobs 为 0，根盘仍为 93%。
- 观察结束时公网 login/upload 仍为 200/302，产品运行文件 blob 仍与 `ed3d89f` 一致。
- 未执行：未发起真实 MiniMax T2I，未写入正式文章，未清理旧备份/日志。

## Artifact

```yaml
artifact: release-plan
status: Deployed / production checks passed
version_source: runtime files@ed3d89fa58796ffdb4a12ecc20e69ffdf15e2170 + release record@this document commit
commits: [ed3d89fa58796ffdb4a12ecc20e69ffdf15e2170]
surfaces:
  - Flask backend
  - Jinja upload UI
  - bounded background image generation
pre_checks: documented
deploy_steps: documented, require explicit approval
post_checks: documented
rollback: documented
```
