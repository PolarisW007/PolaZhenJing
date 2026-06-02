# 测试报告：文章生成流程 git 安全治理

日期：2026-06-02

## 验证命令

```bash
python3 -m py_compile git_safety.py app/uploader.py wiki.py
PYTHONPATH=. .venv/bin/pytest tests/test_git_safety.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_git_safety.py tests/test_social_publish.py -q
python3 wiki.py deploy --dry-run
```

## 结果

- `py_compile`：通过。
- `tests/test_git_safety.py`：3 passed。
- `tests/test_git_safety.py tests/test_social_publish.py`：13 passed。
- `wiki.py deploy --dry-run`：按预期阻止当前工作区同步，拒绝路径包含 `.qa-artifacts/`、`app/uploader.py`、`git_safety.py`、`tests/test_git_safety.py`、`wiki.py`。

## 覆盖验收

| 验收 | 结果 |
| --- | --- |
| A1 定位自动 git add/commit 路径 | 覆盖 `wiki.py deploy`、后台生成 worker、`/admin/sync` |
| A2 白名单文件或 dry-run diff | `guarded_commit_and_push` 精确 `git add -- allowed`，`wiki.py deploy --dry-run` 可预览 |
| A3 密钥/临时文件扫描 | 路径拒绝规则 + 1MB 以下文本内容 secret 扫描 |
| A4 证明不会提交 `.env`、备份和无关 diff | 单测覆盖 `.env`、`debug-backup.txt`；当前仓库 dry-run 阻止非白名单改动 |

## 未覆盖

- 未执行真实 push，避免在当前存在非白名单改动时触发文章发布提交。
- 未部署到生产；上线后仍需在后台同步按钮路径观察一次安全提示/成功提示。
