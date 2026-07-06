# 开发日志：洞察选题社媒运营生成机制

## 时间

2026-07-06 CST

## 本次目标

- 将 `/PolaZhenjing/admin/insights/topics` 从新闻式选题升级为 AI 行业社媒运营选题蓝图。
- 公开信号只作为证据，不再直接变成 topic 标题。
- 每个 topic 提供内容赛道、社媒钩子、目标读者、核心问题和建议结构。

## 计划改动

- `app/insight_topics.py`：升级信号转 topic、归一化字段、草稿模板、排序策略。
- `app/templates/insight_topics.html`：展示社媒运营字段。
- `tests/test_admin_workbench_insight_topics.py`：更新旧断言，增加生成机制测试。
- `docs/pola/project-knowledge/delivery/insight-topics-social-operator/*`：补齐 Harness 交付证据。

## 已完成改动

- `app/insight_topics.py`
  - 新增六类内容赛道：场景使用、产品能力更新、业务模式、商业思考、最佳实践、实践复盘。
  - 新增赛道识别、社媒标题模板、社媒钩子、目标读者、核心问题、建议结构、来源信号和证据角色字段。
  - 将原始线上信号从 topic 标题降级为 `source_signal_title`，用于证据切口，不再直接作为新闻标题搬运。
  - `_normalize_topic()` 兼容旧 JSON，旧 topic 缺字段时补齐运营蓝图字段；旧草稿策略缺失时生成新版底稿。
  - `merge_preserving_status()` 支持用 `source_signal_title` 匹配旧 topic，避免标题转译后丢失 selected/imported/archived 状态。
  - `_upload_article_draft()` 不再因正文长度不足退回管理态完整底稿，而是继续扩写正文型长稿。
- `app/templates/insight_topics.html`
  - 页面标题改为 `AI 行业社媒运营选题`。
  - Topic 卡片展示内容赛道、社媒钩子、读者、核心问题、建议结构和来源信号。
- `tests/test_admin_workbench_insight_topics.py`
  - 新增 `test_signals_to_topics_generates_social_operation_blueprints_not_news_titles`。
  - 回归状态保留、导入上传、质量过滤、页面展示和自动刷新测试。
- `docs/pola/arch-reference.md`
  - 更新洞察选题池架构事实和“不直接搬运新闻标题”的约束。
- `docs/pola/project-knowledge/*`
  - 补齐需求、PRD、SDD、test report、delivery state、test matrix、regression evidence。

## 数据源二阶段更新

- 背景：用户继续指出数据源可能也需要更新。现有源偏官方模型发布和社区热度，虽然能生成蓝图，但对企业采用、云端实践、工程最佳实践和商业模式的覆盖还不够。
- 新增 RSS/Atom 来源：
  - `deepmind_blog`：Google DeepMind，覆盖模型能力和研究产品化。
  - `microsoft_official_blog`：Microsoft Official Blog，覆盖企业采用、组织实践和 Copilot/平台商业化。
  - `aws_ml_blog`：AWS Machine Learning Blog，覆盖 Bedrock/Agent/云端 AI 架构和行业实践。
  - `github_ai_ml_blog`：GitHub AI & ML，覆盖开发者工具、Copilot、AI coding 和工程实践。
  - `sequoia_stories`：Sequoia，覆盖创业观察、AI for verticals 和商业模式。
- 扩展查询词：
  - PolaNews 增加 `AI工作流`、`AI应用`、`企业AI`、`AI商业化`、`AI最佳实践`、`AI产品`。
  - Hacker News 增加 `AI workflow`、`enterprise AI`、`LLM evals`、`RAG`。
  - GitHub Search 增加 `topic:rag`、`topic:llmops`。
- 未接入：
  - Meta AI 未发现稳定官方 RSS。
  - LangChain/LlamaIndex 当前 feed 路径验证不稳定或不可用。
  - Vercel Blog 可解析但全站 Atom 体积过大且主题过宽，暂不加入同步刷新链路。

## 稳定性与安全门禁

- 风险等级：P2。
- 不新增 secret，不新增模型调用，不新增后台进程。
- 采集源、请求超时、自动刷新锁沿用旧逻辑。
- 旧数据通过 `_normalize_topic` 补齐新字段。
- 数据源二阶段只增加 RSS/Atom 配置和查询词，不新增采集类型；真实刷新仍由分源失败隔离兜底。

## 验证记录

- `.venv/bin/python -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：`12 passed in 0.84s`。
- `.venv/bin/python -m pytest tests -q`：`105 passed in 1.90s`。
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-test-gate/scripts/validate_function_test_cases.py --prd docs/pola/project-knowledge/specs/2026-07-06-insight-topics-social-operator-prd.md --sdd docs/pola/project-knowledge/architecture/2026-07-06-insight-topics-social-operator-sdd.md --spec docs/pola/project-knowledge/requirements/2026-07-06-insight-topics-social-operator.md --cases docs/pola/project-knowledge/delivery/insight-topics-social-operator/function_test_cases.json`：PASS，覆盖 9 个验收 ID / 6 个 feature / 9 个 case。
- `.venv/bin/python /Users/wangchang/.agents/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py`：PASS。
- Flask test client 渲染 `/admin/insights/topics` 管理员页面：HTTP 200，包含社媒标题、赛道、钩子和建议结构。
- Playwright system Chrome 渲染：通过，截图 `/tmp/polazj-insight-topics-social-operator.png`。
- RSS live smoke：`collect_rss_signals(days=30, limit_per_feed=4)` 只读执行，采集 30 条信号，新增源中 `deepmind_blog`、`microsoft_official_blog`、`aws_ml_blog`、`github_ai_ml_blog`、`sequoia_stories` 均有返回。

## 影响面

- 用户可见：`/PolaZhenjing/admin/insights/topics` 后台选题页展示从新闻列表升级为运营蓝图。
- 数据：新增兼容字段写入 `data/insight_topics.json` 时向前兼容；本地测试未修改生产数据。
- 性能：不新增外部请求、模型调用、后台进程、队列或定时任务；新增逻辑为本地字符串规则和排序。
- 安全：不新增 secret，不读取或写入 `.env`，不输出 token/cookie。

## 发布状态

- 本地实现与回归通过。
- 已部署生产：2026-07-06 22:30 CST。
- 发布前云端 HEAD：`6cbadb63ea1c5ef4c0142fd3188e12fe0bb6912d`；发布后云端 HEAD：`d1f49b0`。
- 备份分支：`backup/pre-insight-social-operator-20260706222858`。
- 数据备份：`/root/polazj-backups/insight-social-operator-20260706222858/insight_topics.json`。
- 云端验证：`py_compile` 通过；`tests/test_admin_workbench_insight_topics.py` 12 passed；`tests` 全量 105 passed；RSS live smoke 26 条信号；`polazj.service` active。
- HTTPS smoke：`/PolaZhenjing/admin/login` 200，`/PolaZhenjing/admin/insights/topics` 302，`/PolaZhenjing/articles` 200。
- 管理员模板渲染 smoke：包含 `AI 行业社媒运营选题`、`topic-lane`、`topic-hook`、`topic-structure`。
- 服务日志：发布后 5 分钟 warning/error 为空。
- 钉钉开发日志文档：`https://alidocs.dingtalk.com/i/nodes/gpG2NdyVX37kymb5CP2nkzQYWMwvDqPk`。
- AI 表格 `开发日志` 表记录：`recordId=oBx4EtxtmE`。
- 回填字段：`来源文件` 指向钉钉开发日志文档，`更新内容` 已写入本次变更摘要。
- 同步校验：`dws doc read` 回读成功；`dws aitable record query --record-ids oBx4EtxtmE` 回读成功。
- 备注：钉钉文档创建时已包含本次开发日志主体；AI 表格创建后尝试用 `dws doc update --mode append` 将最终同步结果回写到同一钉钉文档，两种 CLI 写法均返回后端缺少 `markdown` 参数。最终同步证据已保留在本地开发日志和 AI 表格记录中。
- 数据源二阶段钉钉开发日志文档：`https://alidocs.dingtalk.com/i/nodes/9E05BDRVQ2pvPkd5tDBwoXoEJ63zgkYA`。
- 数据源二阶段 AI 表格 `开发日志` 表记录：`recordId=kEyHOZRCUj`。
- 数据源二阶段同步校验：`dws doc read --node 9E05BDRVQ2pvPkd5tDBwoXoEJ63zgkYA` 回读成功；`dws aitable record query --record-ids kEyHOZRCUj` 回读成功。
- 线上部署钉钉发布记录文档：`https://alidocs.dingtalk.com/i/nodes/OG9lyrgJPzp47NdBCvpRDjZyWzN67Mw4`。
- 线上部署 AI 表格 `开发日志` 表记录：`recordId=bEFPQt5IGz`。
- 线上部署同步校验：`dws doc read --node OG9lyrgJPzp47NdBCvpRDjZyWzN67Mw4` 回读成功；`dws aitable record query --record-ids bEFPQt5IGz` 回读成功。

## Commit 状态

- 代码改动提交：`c2950d2 feat: 升级洞察选题社媒运营生成机制`。
- 数据源改动提交：`d1f49b0 feat: 补强洞察选题数据源池`。
- 线上部署记录提交：`cc2c91d docs: 记录洞察选题线上部署`。
