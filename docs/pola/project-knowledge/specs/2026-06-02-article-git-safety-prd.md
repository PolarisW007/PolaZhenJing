# PRD：文章生成流程 git 安全治理

日期：2026-06-02

## 背景

PolaZhenJing 的文章生成和后台同步会把文章写入 `_posts/` 并同步到 GitHub。旧实现使用 `git add -A`，当工作区同时存在 `.env`、备份、测试截图或运行产物时，存在误提交风险。

## 用户流程

### CLI 发布

1. 运营或开发运行 `python3 wiki.py deploy`。
2. 系统扫描当前 git 变更。
3. 系统打印允许提交路径和拒绝路径。
4. 如果存在拒绝路径，发布被阻止。
5. 如果只有允许路径，系统执行精确 `git add -- <files>`、`git diff --cached --check`、commit 和 push。

### CLI Dry-run

1. 运营或开发运行 `python3 wiki.py deploy --dry-run`。
2. 系统打印允许/拒绝路径。
3. 若存在拒绝路径，直接阻止。
4. 若无拒绝路径，仅展示预览，不 stage、不 commit、不 push。

### 后台文章生成/同步

1. 后台生成文章或用户点击同步。
2. 系统调用同一套安全 helper。
3. 同步成功时提示成功；无文章/图片变更时提示无需同步。
4. 安全规则阻止时，后台提示“同步被安全规则阻止”并保留文章文件。

## 白名单

- `_posts/*.md`
- `assets/images/**`

## 拒绝规则

- `.env`、`.env.*`。
- `*.pem`、`*.key`、`*.p12`、`*.pfx`。
- 路径包含 `secret`、`token`、`cookie`、`backup`。
- `*.bak`、`*.db`、`__pycache__/**`、`.qa-artifacts/**`。
- 文本内容疑似包含 API key、access token、secret、password、cookie 或私钥。

## 异常分支

- 工作区存在本轮代码改动：文章发布同步被阻止，避免混入非文章文件。
- 允许路径为空：不创建空 commit。
- push 失败：保留本地 commit，错误通过 CLI 或后台 flash/job message 暴露。
