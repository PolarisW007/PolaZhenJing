# 开发日志：洞察选题自动刷新与质量聚焦

## 目标

修复洞察选题近十天没有新生成的问题，并让选题更聚焦 AI 场景应用、方法论、最佳实践、行业观察、Skill 和场景解决方案。

## 根因

- `/admin/insights/topics` 只有手动刷新入口，缺少每日自动刷新或新鲜度守护。
- `data/insight_topics.json` 当前仅有 2026-06-20 的本地种子选题。
- 真实网络采集近 10 天可以获得信号和候选选题，说明源采集可用，断更原因主要是触发机制缺失。
- 原排序过度依赖来源热度，弱相关高热度信号存在进入前排的风险。

## 改动

- `app/insight_topics.py`
  - 默认刷新周期调整为 10 天，并加入 10 天选项。
  - 新增 AI 主题聚焦评分，优先 AI 场景、方法论、实践、行业、Skill/解决方案。
  - 新增后台自动刷新、新鲜度判断、文件锁和锁 TTL。
  - 自动刷新阈值环境变量增加容错读取，避免配置异常导致选题模块加载失败。
- `app/admin_workbench.py`
  - 管理员进入工作台或选题页时触发过期后台刷新。
- `app/templates/insight_topics.html`
  - 展示后台刷新已开始/进行中的状态提示。
- `tests/test_admin_workbench_insight_topics.py`
  - 增加后台刷新锁和质量过滤测试。

## 验证

- `python3 -m py_compile app/insight_topics.py app/admin_workbench.py app/__init__.py`：通过。
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`：8 passed。
- `validate_function_test_cases.py`：PASS，覆盖 6 条验收、2 个 feature、4 个 case。
- 真实网络 smoke：近 10 天采集到 127 条信号，生成 24 个候选选题；榜单已过滤弱相关高热度内容，保留 AI 工作流、智能体、产业应用、工程实践等方向。
- `curl -I -L https://aipd.me/PolaZhenjing/admin/insights/topics`：线上后台入口可访问但会跳登录，未携带管理员会话时只能验证登录跳转。
- `ssh -o BatchMode=yes root@42.121.164.11 ...`：非交互 SSH key 不可用，返回 `Permission denied`；未把服务器密码写入命令或文档。

## 风险和回滚

- 风险：外部源慢或失败。控制：后台线程、不阻塞首屏、请求超时、旧数据保留。
- 风险：多 worker 并发刷新。控制：文件锁和 TTL。
- 回滚：回滚本次代码，或生产设置 `POLAZJ_INSIGHT_AUTO_REFRESH=0`。

## 钉钉同步

待收尾阶段同步；如 dws 上传仍受三步流程限制，将记录 blocker。

## 部署状态

本地修复和 Harness 已完成。云服务器部署暂未执行，原因是当前 Codex 运行环境没有可用 SSH key，非交互 SSH 连接失败。需要用户在本机 shell 完成 SSH key 授权，或允许通过安全的交互方式登录后再同步部署。
