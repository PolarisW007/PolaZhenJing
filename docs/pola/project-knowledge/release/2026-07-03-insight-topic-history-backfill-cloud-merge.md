# 2026-07-03 历史每日选题回填云端发布方案

## 发布对象

- 项目：PolaZhenJing
- 云端目录：`/PolaZhenjing`
- 服务：`polazj.service`
- 数据文件：`data/insight_topics.json`

## 发布前检查

1. 本地测试通过。
2. 本地 commit 已推送到 GitHub。
3. 云端记录当前 HEAD、`git status`、服务状态。
4. 云端创建备份分支和备份文件。
5. 云端演练合并 GitHub 最新代码与服务器文章提交。

## 发布命令草案

```bash
git -C /PolaZhenjing rev-parse HEAD
git -C /PolaZhenjing fetch origin main
git -C /PolaZhenjing branch backup/pre-history-backfill-YYYYMMDDHHMMSS HEAD
cp /PolaZhenjing/data/insight_topics.json /root/polazj-backups/insight_topics.pre-history-backfill-YYYYMMDDHHMMSS.json
```

回填命令：

```bash
cd /PolaZhenjing
.venv/bin/python scripts/backfill_insight_topics.py --start 2026-06-01 --end 2026-07-03 --json
```

## 发布后验证

- `systemctl is-active polazj.service`
- `.venv/bin/python -m py_compile app/insight_topics.py scripts/backfill_insight_topics.py`
- `.venv/bin/python -m pytest tests/test_admin_workbench_insight_topics.py -q`
- 统计 `2026-06-01` 到 `2026-07-03` 覆盖日期。
- HTTP smoke：登录页、管理工作台跳转、选题入口、公共文章页面。

## 回滚

```bash
cp /root/polazj-backups/insight_topics.pre-history-backfill-YYYYMMDDHHMMSS.json /PolaZhenjing/data/insight_topics.json
systemctl restart polazj.service
systemctl status polazj.service --no-pager
```

如采用目录切换发布，则恢复 `/PolaZhenjing.pre-YYYYMMDDHHMMSS` 为 `/PolaZhenjing` 后重启服务。

## 门禁

- A5：没有备份和回滚路径不得执行生产写入。
- A6：测试和 Harness 未通过不得推送/部署。
- A7：不得输出 secret。
- A8：发布后必须验证线上服务。
