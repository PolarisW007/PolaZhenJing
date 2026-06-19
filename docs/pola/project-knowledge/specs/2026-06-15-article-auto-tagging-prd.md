# PRD: 文章自动归类打标与快速筛选完善

日期: 2026-06-15

## 用户流程

### 普通用户浏览

1. 用户进入 `/articles` 或未登录访问 `/PolaZhenjing/admin/articles`。
2. 在快速 Wiki 区看到业务主题,例如 `agent-systems`、`ai-engineering`、`product-design`、`data-infrastructure`。
3. 点击主题 chip 后,文章时间线只展示对应主分类文章。
4. 点击关键词 chip 后,文章时间线按关键词进一步过滤。
5. 搜索框和排序继续无刷新工作。

### 管理员上传

1. 管理员在 `/PolaZhenjing/admin/upload` 上传文件、粘贴内容或输入 URL。
2. 标题:
   - 用户填写标题: 使用用户标题。
   - 用户留空: 继续使用 `extract_title()` 自动识别。
3. 标签:
   - 用户填写标签: 使用用户标签。
   - 用户留空: 系统根据最终标题和正文自动生成标签。
4. 进入风格选择并生成文章。
5. 生成文章 front matter 中 `tags` 非空,且首标签为业务分类。

## 标签体系

主分类候选:

- `agent-systems`
- `ai-engineering`
- `model-research`
- `product-design`
- `data-infrastructure`
- `coding-tools`
- `media-generation`
- `industry-analysis`
- `personal-knowledge`
- `testing-harness`

补充标签:

- 平台/公司: `openai`, `anthropic`, `claude`, `codex`, `deepseek`, `langchain`, `palantir`, `databricks`, `snowflake`。
- 技术主题: `llm`, `rag`, `context-engineering`, `workflow`, `developer-tools`, `multimodal`, `video-generation`, `typescript`。
- 内容形态: `case-study`, `guide`, `research`, `opinion`。

## 异常与边界

- 内容太短或测试文章: 保底标签为 `testing-harness`, `test` 或 `personal-knowledge`。
- 已有用户标签: 不覆盖用户显式输入,但批量脚本可重排/补充历史文章标签。
- 标签数量: 默认 3-6 个,避免首页出现过碎标签。
- 标签格式: 使用英文小写 kebab-case,降低 URL/DOM/JSON-LD 风险。

## 验收 UI

- 快速 Wiki 第一行主题不再由文章写作风格主导。
- 关键词筛选点击后有 active 状态,再次点击可取消。
- 移动端 chip 自动换行,无横向溢出。
