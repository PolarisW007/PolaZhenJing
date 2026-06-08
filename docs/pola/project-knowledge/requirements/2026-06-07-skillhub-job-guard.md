# Requirement: SkillHub and Job Guard - 2026-06-07

## Source

服务器 Critical I/O 诊断后的性能与安全升级批次。PolaZhenJing 的 SkillHub 递归扫描、zip 上传/下载和后台 job 线程模型可能在高频访问或批量任务时放大 I/O、内存和线程压力。

## Goals

- SkillHub 列表扫描增加短 TTL 缓存，减少每次请求全量 `rglob`。
- zip 上传、GitHub 导入和下载增加文件数与大小上限。
- 后台 job 从每任务新线程改为固定大小线程池。
- 管理后台、发布中心和 SkillHub 页面入口保持不变。

## Non-Goals

- 不改发布中心业务流程。
- 不改数据库 schema。
- 不执行生产重启或部署。

## Acceptance

- A1: SkillHub `_all_skills()` 具备 in-process TTL cache。
- A2: zip 解压前检查压缩包大小、文件数量和解压总量。
- A3: Skill 包下载前检查文件数量和总大小。
- A4: job submit 使用 bounded executor。
- A5: 新增最小单测覆盖 zip guard 和 executor guard。

