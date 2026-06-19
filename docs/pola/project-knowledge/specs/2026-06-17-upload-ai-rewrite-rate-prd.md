# PRD/SPEC: 上传文章 AI 改写率控制

日期: 2026-06-17

## 产品目标

让管理员在文章上传阶段控制 AI 文本改写强度，支持从“不改写原文，只插图”到“完全按所选风格重写”的连续业务心智。

## 用户流程

1. 管理员进入 `/PolaZhenjing/admin/upload`。
2. 在上传文件、粘贴内容或输入 URL 中任一入口提供原文。
3. 管理员选择媒体处理、可选标签/描述/配图/修改建议。
4. 管理员选择 AI 改写率:
   - 0%: 不改写正文，只生成/插入图片。
   - 25%: 轻润色，修正表达和格式。
   - 50%: 结构优化，改善段落和过渡。
   - 75%: 深度改写，保留事实和论点，重塑表达。
   - 100%: 完整按所选风格重写。
5. 提交后进入风格选择页。
6. 选择风格并生成，进度页显示对应阶段消息。
7. 生成结束后进入文章查看/列表链路。

## 页面规格

### 上传页 AI 改写率模块

- 位置: 每个 tab 的「修改建议简述」前或后，保持表单扫描顺序一致。
- 控件类型: radio segment group。
- 字段名: `rewrite_rate`。
- 值: `0`、`25`、`50`、`75`、`100`。
- 默认值: `100`。
- 帮助文案: “0% 不改写正文；100% 完整按选择风格重写。图片生成与插入不受 0% 影响。”
- 桌面: 可横向换行。
- 窄屏: 自动换行，不遮挡其他字段。

### 风格选择页

- 暂不新增改写率编辑，降低状态分叉。
- 后续可在 draft 预览区显示已选改写率，本次非目标。

### 进度页

- 0%: 消息显示“AI 改写率 0%，已跳过文本重写，将继续生成/插入图片。”
- 25/50/75/100: 阶段文案包含改写率。

## 后端规格

- 新增 `_parse_rewrite_rate(value, default=100) -> int`。
- `_save_draft()` 增加 `rewrite_rate` 参数并写入 draft JSON。
- `upload()` 从表单读取 `rewrite_rate`，所有三种输入入口共用。
- `generate()` 从 draft 读取 `rewrite_rate`，旧 draft 缺字段时使用 100。
- `_run_generate_job()`:
  - `rewrite_rate <= 0`: 跳过 `_call_llm_rewrite()`。
  - `rewrite_rate > 0`: 调用 `_call_llm_rewrite(..., rewrite_rate=rewrite_rate)`。
- `_call_llm_rewrite()`:
  - 保持 100% 与旧完整改写行为兼容。
  - 25/50/75 加入强度约束和输出边界。

## 验收映射

| 验收项 | 验证方式 |
| --- | --- |
| A2 UI | Flask test client + Playwright 检查 radio group |
| A3 Draft | 单测 POST `/admin/upload` 后读取 draft JSON |
| A5 0% | monkeypatch `_call_llm_rewrite`，运行 `_run_generate_job` 后断言未调用 |
| A7 中间档 | 单测捕获 LLM payload prompt 中包含强度说明 |
| A9 部署 | 云端 pytest + 线上浏览器 harness |

## 异常处理

- 非法 `rewrite_rate`: 后端使用默认 100。
- LLM 失败: 沿用原降级，使用当前内容继续。
- 无 API key:
  - 0%: 无影响。
  - >0%: 记录 warning，继续原内容。
