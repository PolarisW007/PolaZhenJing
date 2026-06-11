# SDD：MiniMax M3 默认模型升级

## 架构影响

本次只修改 `app/agent.py` 和 `app/uploader.py` 的默认模型常量。现有 `https://api.minimax.chat/v1/chat/completions` endpoint、鉴权头、请求结构、缓存和数据库逻辑不变。

## 安全与性能

- 不新增 secret。
- 不新增后台任务或磁盘 IO。
- M3 已通过兼容烟测；如旧 endpoint 运行异常，可通过环境变量回滚 Agent 模型。

## 回滚

设置 `POLA_AGENT_MODEL=MiniMax-M2.7` 或回滚常量即可。
