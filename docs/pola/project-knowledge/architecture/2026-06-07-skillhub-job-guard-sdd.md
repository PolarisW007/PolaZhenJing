# SDD: SkillHub and Job Guard - 2026-06-07

## Architecture Impact

本次不改变 Flask blueprint、SQLite jobs 表或模板结构，只在现有模块内增加边界：

- `app/skillhub.py`
  - `_all_skills()` 增加进程内 TTL cache。
  - `_save_registry()` 后清空 cache。
  - `_safe_extract_zip()` 增加压缩包大小、文件数量、解压总量检查。
  - GitHub zip 下载改为分块读取并累计限制。
  - Skill zip 下载在写入内存 buffer 前限制文件数量和总大小。
- `app/jobs.py`
  - `submit()` 改为使用 `ThreadPoolExecutor(max_workers=POLAZJ_JOB_MAX_WORKERS)`。

## Configuration

- `SKILLHUB_CACHE_TTL_SECONDS`: 默认 `300`。
- `SKILLHUB_MAX_ZIP_BYTES`: 默认 `25MB`。
- `SKILLHUB_MAX_ZIP_FILES`: 默认 `500`。
- `SKILLHUB_MAX_EXTRACTED_BYTES`: 默认 `50MB`。
- `SKILLHUB_MAX_DOWNLOAD_BYTES`: 默认 `25MB`。
- `SKILLHUB_MAX_DOWNLOAD_FILES`: 默认 `500`。
- `POLAZJ_JOB_MAX_WORKERS`: 默认 `2`。

## No-Function-Impact Strategy

- 默认上限覆盖正常 skill 包。
- 用户入口和权限判断保持不变。
- 超限行为使用现有错误提示或 HTTP 413。

## Verification

- `py_compile` 覆盖 `app/skillhub.py`、`app/jobs.py` 和新增测试。
- pytest 覆盖 zip guard 和 executor guard。
- `git diff --check` 确认 diff 卫生。
