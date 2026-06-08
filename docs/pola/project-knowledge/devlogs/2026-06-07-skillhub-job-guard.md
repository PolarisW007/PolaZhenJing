# Devlog: SkillHub and Job Guard - 2026-06-07

## Goal

降低 PolaZhenJing SkillHub 高频访问、zip 包处理和后台任务并发线程带来的 I/O/内存/线程风险。

## Changes

- `app/skillhub.py`
  - Skill 列表增加 TTL cache，registry 变更后清空。
  - zip 上传/导入检查压缩包大小、文件数和解压总量。
  - GitHub zip 下载改为分块读取并限制累计大小。
  - Skill zip 下载前限制文件数量和总大小。
- `app/jobs.py`
  - 每任务新线程改为固定线程池。
- `tests/test_skillhub_guard.py`
  - 覆盖 zip 文件数量和解压大小限制。
- `tests/test_jobs_guard.py`
  - 覆盖 executor bounded 配置。

## Verification

- PASS: `python3 -m py_compile app/skillhub.py app/jobs.py tests/test_skillhub_guard.py tests/test_jobs_guard.py`
- PASS: `PYTHONPATH=. .venv/bin/pytest tests/test_skillhub_guard.py tests/test_jobs_guard.py -q`，3 passed。
- PASS: `git diff --check`
