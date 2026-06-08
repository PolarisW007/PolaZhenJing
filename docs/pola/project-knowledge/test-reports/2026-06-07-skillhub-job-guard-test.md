# Test Report: SkillHub and Job Guard - 2026-06-07

## Scope

- SkillHub zip safety limits.
- Bounded background job executor.
- Syntax validation.

## Commands

```bash
python3 -m py_compile app/skillhub.py app/jobs.py tests/test_skillhub_guard.py tests/test_jobs_guard.py
PYTHONPATH=. .venv/bin/pytest tests/test_skillhub_guard.py tests/test_jobs_guard.py -q
git diff --check
```

## Results

- PASS: `python3 -m py_compile app/skillhub.py app/jobs.py tests/test_skillhub_guard.py tests/test_jobs_guard.py`
- PASS: `PYTHONPATH=. .venv/bin/pytest tests/test_skillhub_guard.py tests/test_jobs_guard.py -q`，3 passed。
- PASS: `git diff --check`

## Notes

- 直接运行系统 `python3 -m pytest` 时本机没有安装 pytest；改用仓库 `.venv/bin/pytest` 并设置 `PYTHONPATH=.` 后通过。
