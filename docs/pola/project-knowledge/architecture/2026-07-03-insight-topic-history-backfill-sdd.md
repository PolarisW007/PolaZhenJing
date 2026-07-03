# 2026-07-03 历史每日选题回填与云端安全合并 SDD

## 架构影响

本次不新增服务进程、队列、cron 或后台线程。新增能力以同步 CLI 和纯函数形式存在：

- `app/insight_topics.py`
  - 日期解析和范围限制。
  - 历史回填 topic 生成。
  - `backfill_topics_for_date_range` 幂等回填入口。
  - `save_topics` 保留 metadata。
- `scripts/backfill_insight_topics.py`
  - 运维 CLI，支持 dry-run 和 JSON 输出。

## 数据流

```text
CLI args -> backfill_topics_for_date_range
  -> _load_payload
  -> 统计目标日期覆盖
  -> 为缺失日期生成 manual_backfill topic
  -> _normalize_topic 生成长底稿
  -> save_topics 写入 data/insight_topics.json
```

## 幂等和并发

- 幂等依据：`date` 已存在则跳过。
- 本次不提供并发写锁，生产执行为单次运维命令；执行前必须备份 `data/insight_topics.json`。
- dry-run 不写文件。
- 每次最多 366 天，每天最多 3 条，避免无界写入。

## 性能和资源

- 不访问网络。
- 不加载模型。
- 不启动 ASR、本地模型或后台批处理。
- CPU 消耗来自 29 到 32 条长底稿文本生成，规模固定，预期秒级完成。
- 写入单个 JSON 临时文件后原子替换。

## 云端安全合并策略

线上仓库为 `ahead 21, behind 72` 且工作区有未提交运行数据；直接 `git pull` 已在演练中出现多文件冲突。因此采用安全发布路径：

1. 本地完成实现、测试、commit、push。
2. 云端创建当前 HEAD 备份分支。
3. 云端备份生产目录关键数据和 `data/insight_topics.json`。
4. 在临时目录演练 GitHub 最新代码叠加云端文章提交。
5. 只在演练和检查通过后切换生产目录或执行等价的保守同步。
6. 回滚方式：恢复备份目录/备份 JSON，并重启 `polazj.service`。

## 安全边界

- A5：禁止在生产目录执行 `git reset --hard` 覆盖未备份数据。
- A7：不读取、不打印、不提交 `.env`、token、cookie、私钥。
- A8：部署后必须验证服务状态和关键入口。

## 测试策略

- 单元测试覆盖历史日期缺口补全、dry-run 不写入、状态保留。
- 既有导入上传、刷新、工作台测试保持通过。
- Harness 验证 PRD/SPEC/SDD 中所有验收 ID。
