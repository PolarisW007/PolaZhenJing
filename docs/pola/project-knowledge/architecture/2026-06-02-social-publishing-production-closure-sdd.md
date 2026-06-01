# 架构开发文档：发布中心生产收口

## 1. 背景

发布中心已经通过 `app/social_publish.py` 支撑微信公众号草稿、X 官方 API 发帖和人工发布包。当前需求重点不是新增平台，而是核查生产闭环和清理待提交状态。

## 2. 当前系统理解

| 维度 | 当前事实 | 影响 |
| --- | --- | --- |
| 本地代码 | `origin/main` 已包含微信批量草稿、X adapter、上传页稳定性修复 | 不需要重复实现。 |
| 线上服务 | `/PolaZhenjing` + `polazj.service`，当前 active | 可做生产 smoke。 |
| X 配置 | 线上 `_x_config_status()` 显示未配置 | 真实 X 发帖被环境变量阻塞。 |
| 服务器 git | HEAD 停在文章提交 `edd2d4a`，工作树有 rsync 文件和文章/auth 改动 | 不能直接 reset 到 `origin/main`。 |

## 3. 方案

- 保持发布中心代码不变，先完成收口核查和阻塞记录。
- 线上只读检查配置状态，不输出 token 值。
- 对服务器清理只允许非破坏性步骤：
  - 创建 backup branch。
  - 尝试 `git reset --mixed origin/main` 前后核查状态。
  - 如果发现文章/SEO/auth 差异扩大，立即 reset 回 backup。

## 4. 数据和安全

- 第三方凭据只从环境变量读取。
- `social_publications` 只记录状态、外部 ID、URL 和错误，不记录 token。
- 生产工作树中的文章和 auth 改动视为用户/生产改动，不能由本需求覆盖。

## 5. 验证策略

- 本地：`py_compile`、`tests/test_social_publish.py`。
- 线上：`systemctl is-active polazj.service`、发布中心/上传页未登录跳转、配置状态只读脚本。
- Git：本地 clean；服务器 dirty 状态明确并保留 backup branch。

## 6. 当前阻塞

- X 真实发帖需要在生产环境配置 `X_USER_ACCESS_TOKEN` 后重新验证。
- 服务器 git 收口需要单独决定文章发布线与 GitHub main 的合并策略。
