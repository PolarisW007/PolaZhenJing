# TencentDB Agent Memory 代码阅读笔记

更新时间：2026-05-22

## 1. 本地位置

- GitHub: https://github.com/Tencent/TencentDB-Agent-Memory
- 本地路径：`referene/TencentDB-Agent-Memory`
- 当前 commit：`bfddda6`
- package：`@tencentdb-agent-memory/memory-tencentdb@0.3.5`
- 技术栈：TypeScript、Node >= 22.16、SQLite、sqlite-vec、FTS5、OpenClaw plugin、Hermes Gateway adapter

## 2. 核心判断

TencentDB Agent Memory 的价值不在于“再接一个插件”，而在于它把 Agent memory 工程化成两条清晰链路：

1. 长期记忆链路：L0 Conversation -> L1 Atom -> L2 Scenario -> L3 Persona。
2. 短期压缩链路：tool logs / raw refs -> jsonl step summaries -> Mermaid canvas -> `node_id` drill-down。

这与超级小王的目标高度一致：低层保留证据，高层保留结构；平时少注入，必要时可下钻；模型可以提炼，但不能丢失来源。

## 3. 关键实现

| 文件 | 关键实现 | 说明 |
| --- | --- | --- |
| `src/core/tdai-core.ts` | `TdaiCore` | host-neutral facade，统一 recall、capture、search、pipeline、session end。 |
| `src/core/types.ts` | `HostAdapter` / `RuntimeContext` / `LLMRunnerFactory` | 解耦 OpenClaw、Hermes、Gateway 与核心记忆算法。 |
| `src/utils/pipeline-manager.ts` | L0/L1/L2/L3 scheduler | 支持 warm-up、轮数阈值、idle timeout、L2 min/max interval、串行队列、checkpoint。 |
| `src/core/hooks/auto-capture.ts` | L0 capture | 每轮结束先写 L0；checkpoint 原子游标避免重复捕获；embedding 可后台写入。 |
| `src/core/hooks/auto-recall.ts` | auto recall | L1 相关记忆动态 prepend；L3 persona 和 L2 scene navigation 作为稳定 system context。 |
| `src/core/record/l1-extractor.ts` | L1 extraction | 一次 LLM 调用同时完成 scene segmentation 与 persona/episodic/instruction 抽取。 |
| `src/core/record/l1-dedup.ts` | dedup/conflict | 先用 vector/FTS 找候选，再让 LLM 批量判断 store/update/merge/skip。 |
| `src/core/store/sqlite.ts` | local store | L1/L0 metadata 表、FTS5 表、sqlite-vec 表；支持 embedding 失败时 metadata/FTS 降级。 |
| `src/core/tools/memory-search.ts` | memory search tool | FTS + vector 并行，RRF 融合，支持 type/scene filters。 |
| `src/offload/*` | context offload | 长任务日志外置，MMD/Mermaid 注入上下文，按 `node_id` 恢复原文。 |

## 4. 对超级小王的采用方案

### 4.1 直接借鉴

- L0/L1/L2/L3 分层，但小王命名为 raw_events、memory_items、scene_blocks、persona_versions。
- RRF 混合召回，先支持 SQLite FTS5 + LIKE fallback，后续加 embedding。
- `node_id` 可下钻链路，用于 session canvas 和后台调试。
- HostAdapter 思路，用 `MemoryHostContext` 表达 actor、session、source、trust、owner_status。
- 召回超时和 embedding 失败不阻塞主对话，只降级并记录 trace。

### 4.2 改造后借鉴

- L1 prompt 只抽 persona/episodic/instruction，对小王不够；应扩展为 9 类记忆，并增加 Owner/visitor/source/risk。
- L2 scene block 很适合小王，但要保留 Owner 审核和编辑入口。
- L3 persona 自动写 `persona.md` 不适合核心人格；小王应生成 persona draft，并绑定 Harness run 后由 Owner 激活。

### 4.3 不直接采用

- 不引入 OpenClaw plugin/postinstall patch 作为 PolaZhenJing 主运行时依赖。
- 不要求 Node 22 runtime 成为小王记忆系统的核心依赖。
- 不把匿名访客对话直接沉淀进全局 Persona。
- 不把短期 Mermaid canvas 当作长期事实或人格依据。

## 5. 后续代码复用建议

优先复刻而不是直接调用：

1. Python 实现 `rrf_merge(results_a, results_b, k=60)`。
2. Python 实现 `session_canvas`：生成 Mermaid、保存 `node_map_json`、支持后台下钻。
3. Python 实现 `MemoryHostContext`，统一 chat/admin/importer/harness 调用。
4. SQLite schema 借鉴 metadata + FTS + optional embedding 的三层索引。
5. L1 extraction prompt 借鉴 scene segmentation，但输出 schema 改为小王 9 类记忆。

可直接参考的代码片段位置：

- RRF：`src/core/tools/memory-search.ts`
- auto recall context split：`src/core/hooks/auto-recall.ts`
- pipeline timing：`src/utils/pipeline-manager.ts`
- SQLite metadata/FTS schema：`src/core/store/sqlite.ts`
- Mermaid node trace：`src/offload/pipelines/l2-mermaid.ts`

## 6. Harness 增补

新增测试必须验证：

- L0 raw_event 永远可追溯。
- L1 抽取不会把访客建议写入 Owner 全局人格。
- L2 scene block 可以合并但不能删除证据。
- L3 persona draft 不能绕过 Harness 和 Owner 审核。
- session_canvas 中每个 `node_id` 都能下钻到 raw_event/tool_result。
- RRF 排序优于单路 FTS 或单路 embedding。
