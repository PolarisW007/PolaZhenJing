# 开发日志：文章生成流程 git 安全治理

日期：2026-06-02
需求池记录：`x3OmSzOadF`

## 目标

治理 PolaZhenJing 文章生成和后台同步流程中的 `git add -A` 风险，防止无关改动、密钥备份或运行产物被文章发布流程误提交。

## 改动文件

- 新增：`git_safety.py`
- 新增：`tests/test_git_safety.py`
- 修改：`wiki.py`
- 修改：`app/uploader.py`
- 新增：`docs/pola/project-knowledge/requirements/2026-06-02-article-git-safety.md`
- 新增：`docs/pola/project-knowledge/specs/2026-06-02-article-git-safety-prd.md`
- 新增：`docs/pola/project-knowledge/architecture/2026-06-02-article-git-safety-sdd.md`
- 新增：`docs/pola/project-knowledge/test-reports/2026-06-02-article-git-safety-test.md`

## 实现

- `wiki.py deploy` 改为输出 allowed/denied 路径，并支持 `--dry-run`。
- 后台生成文章 worker 和 `/admin/sync` 改为调用 `guarded_commit_and_push`。
- 新增路径拒绝清单：`.env`、密钥文件、token/cookie/secret/backup 命名、数据库、缓存、`.qa-artifacts`。
- 新增内容扫描：阻断疑似 API key、access token、secret、password、cookie 和私钥文本。
- 只有 `_posts/*.md` 与 `assets/images/**` 可被文章同步流程 stage。

## 验证

```bash
python3 -m py_compile git_safety.py app/uploader.py wiki.py
PYTHONPATH=. .venv/bin/pytest tests/test_git_safety.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_git_safety.py tests/test_social_publish.py -q
python3 wiki.py deploy --dry-run
```

## 结果

- `py_compile` 通过。
- git 安全单测 3 passed。
- git 安全 + social publish 回归 13 passed。
- `deploy --dry-run` 在当前存在本轮代码和 `.qa-artifacts` 时按预期阻止同步，证明不会把非文章文件混入文章发布提交。

## 风险

- 当前未执行真实文章 push；上线后需要在后台同步按钮路径做一次可见提示验证。
- 如果后续文章同步需要提交新目录，必须先显式扩展白名单并补测试。
