# 开发日志：发布中心生产收口

日期：2026-06-02

## 目标

核查钉钉需求 `XhcYwKVYha`：微信公众号批量草稿、X 真实发帖与服务器待提交清理。

## 本次核查

- 本地仓库：
  - `main...origin/main` 干净。
  - 最新相关提交：`fe67d6f` 微信批量草稿、`56fec1a` X 自动发布、`351df4b` 上传页稳定性。
- 本地验证：
  - `python3 -m py_compile app/social_publish.py app/__init__.py app/uploader.py`：通过。
  - `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：10 passed。
  - 本地配置只读检查：微信 configured，X 未配置。
- 线上只读验证：
  - `systemctl is-active polazj.service`：active。
  - `https://aipd.me/PolaZhenjing/admin/social/`：跳转到登录页。
  - `https://aipd.me/PolaZhenjing/admin/upload`：跳转到登录页。
  - 服务器配置只读检查：微信 configured，X 未配置。
  - 服务器 `PYTHONPATH=. .venv/bin/pytest tests/test_social_publish.py -q`：10 passed。

## 服务器 git 收口尝试

- 发现服务器 `/PolaZhenjing` HEAD 为 `edd2d4a`，工作树有 21 个待提交项，其中包含发布中心 rsync 文件、文章和 `app/auth.py`。
- 已创建 backup branch：`backup/pre-clean-20260602042250`。
- 尝试 `git reset --mixed origin/main` 后发现服务器文章/SEO/auth 差异显著扩大，说明生产文章线与 GitHub main 存在更大分叉。
- 已立即 reset 回 backup，恢复到操作前的 21 项 dirty 状态，未覆盖工作树文件。

## 当前结论

- 微信批量草稿：已实现、已部署、测试通过，生产配置完整。
- X 自动发布：代码已实现并部署，但生产 `X_USER_ACCESS_TOKEN` 未配置，因此真实发帖阻塞。
- 待提交清理：服务器发布中心相关文件已经部署，但生产 git 工作树与 GitHub main/文章线分叉，不能在本轮粗暴清理；需要单独制定服务器文章线合并策略。

## 风险

- 未配置 X token 前强行触发真实发帖会失败并产生无意义错误记录。
- 服务器 reset/checkout 可能覆盖生产文章、auth 或 SEO 改动，必须继续保持文件级同步和备份策略。
