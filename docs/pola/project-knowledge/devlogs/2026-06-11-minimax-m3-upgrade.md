# Devlog：MiniMax M3 默认模型升级

## 改动

- `app/agent.py` 默认 `POLA_AGENT_MODEL` fallback 改为 `MiniMax-M3`。
- `app/uploader.py` 默认 `MINIMAX_MODEL` 改为 `MiniMax-M3`。

## 稳定性与安全门禁

- 风险等级：P2，涉及外部 AI provider 默认模型。
- 未修改 endpoint、secret、数据库或用户主流程。

## 验证

- MiniMax M3 在线烟测：`/v1/text/chatcompletion_v2` 返回 200，模型为 `MiniMax-M3`。
- MiniMax M3 兼容烟测：`/v1/chat/completions` 对 `max_tokens` 与 `max_completion_tokens` 均返回 200。
- `python3 -m py_compile app/agent.py app/uploader.py` 通过。
- 静态默认值断言：`app/agent.py` 与 `app/uploader.py` 均包含 `MiniMax-M3`。
- `git diff --check -- <本次改动文件>` 通过。
