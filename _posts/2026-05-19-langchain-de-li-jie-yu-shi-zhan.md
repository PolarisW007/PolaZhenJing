---
layout: deep-technical
theme: wukong
title: "LangChain 的理解与实战"
date: 2026-05-19
tags: []
summary: "很多人跟着教程 npm install 一下，写了个调用 DeepSeek 的 Demo，输出一句「你好，我是 AI」，就发朋友圈说自己入门 AI 开发了。结果产品经理一句「给我做个能查公司内部文档的客服机器人」，直接傻眼：- RAG 检索永远答非所问，上下文驴唇不对马嘴- 多轮对话聊个七八轮就崩，token 直接爆仓- 想换个性价比更高的模型，代码要全量重写- 线上一限流、API 一超时，服务直…"
---

![前端开发者从调包侠成长为AI应用架构师的转变之路]({{ site.baseurl }}/assets/images/generated/langchain-de-li-jie-yu-shi-zhan/cover.png)

# LangChain 的理解与实战：从「调包侠」到 AI 应用架构师的进阶之路

很多人跟着教程 npm install 一下，写了个调用 DeepSeek 的 Demo，输出一句「你好，我是 AI」，就发朋友圈说自己入门 AI 开发了。结果产品经理一句「给我做个能查公司内部文档的客服机器人」，直接傻眼：

![前端新手面对产品经理需求时的困境场景]({{ site.baseurl }}/assets/images/generated/langchain-de-li-jie-yu-shi-zhan/scene-1.png)



- RAG 检索永远答非所问，上下文驴唇不对马嘴
- 多轮对话聊个七八轮就崩，token 直接爆仓
- 想换个性价比更高的模型，代码要全量重写
- 线上一限流、API 一超时，服务直接原地升天

最后只能甩锅「LangChain 不好用」——不是它不好用，是你只解锁了它 10% 的能力！

上一篇我们聊了 LangChain 的核心概念和基础 Demo，这篇咱们直接进阶，用前端 er 听得懂的梗、能直接抄的生产级代码，把 LangChain 扒得明明白白，带你从「调包侠」直接进阶成 AI 应用架构师。

## 一、重新认识 LangChain：你之前对它的理解可能全错了

很多人对 LangChain 的认知还停留在「Lang = 语言模型，Chain = 把步骤串起来」，格局小了家人们！咱们先把底层逻辑掰扯清楚。

### 1.1 它不是胶水代码，是 AI 应用界的「React」

咱们前端 er 都懂：原生 JS 能写页面，但是为什么大家都用 React？因为 React 把 DOM 操作、状态管理、组件复用、生命周期这些脏活累活全给你封装好了，让你能专注写业务逻辑，不用天天跟浏览器兼容性对线。

LangChain 就是干了一模一样的事：

- **原生 LLM 接口 = 原生 JS**：能实现基础功能，但是每加一个需求就要写一堆重复代码，换个环境直接不兼容
- **LangChain = React**：把提示词工程、模型适配、数据流转、工具调用、内存管理、异常处理这些 AI 应用的通用脏活全给你封装了，提供了一套标准化的开发范式，让你不用天天跟不同模型的 API 文档对线

它的核心从来不是「把接口串起来」，而是一套可组合、可扩展、生产级可用的 AI 原生应用开发框架。

### 1.2 JS/TS 生态才是全栈开发的王炸

很多人有个误区：「LangChain 是 Python 的，JS 版本就是个玩具」。大错特错！

现在 LangChain 的 JS/TS 版本已经完全成熟，生产级可用，而且对咱们前端全栈开发者来说，它简直是天选之子：

- 完全基于 Node.js 开发，原生支持 ESM 规范，跟你天天写的 Next.js、NestJS、Express 无缝衔接，不用额外学一门 Python
- 完美兼容前端生态，你熟悉的 npm、yarn、pnpm 直接用，dotenv、axios 这些常用库随便接
- 类型提示拉满！TypeScript 原生支持，写代码的时候 IDE 直接给你提示参数、报错，不用对着文档瞎猜，这一点直接吊打 Python 版本的体验

别再被 Python 教程劝退了，用你最熟悉的 JS/TS，照样能写出顶级的 AI 应用。

### 1.3 适配器模式的终极奥义：不止是换模型，是给应用上了「双保险」

很多人看完适配器模式只记住了「能随便换模型」，但它的价值远不止于此。

咱们用前端最熟悉的 Axios 来类比：Axios 为什么好用？因为它封装了浏览器和 Node.js 的 http 请求差异，不管你在什么环境，都是一套 get/post API，不用管底层是 XMLHttpRequest 还是 http 模块。

LangChain 的适配器就是干了这件事：

- 不管你用的是 DeepSeek、OpenAI、Anthropic，还是本地部署的 Ollama 模型，全都是一套标准的 invoke/stream 接口
- 不用去研究每个模型的请求格式、参数差异、鉴权方式，适配器全给你处理好了
- 你写的业务逻辑完全和底层模型解耦，真正做到了「面向接口编程，而不是面向实现编程」

这带来的生产级价值，可比「换模型方便」大多了：

- **模型 A/B 测试**：同一个业务逻辑，同时测试 DeepSeek 和 GPT-4o 的效果，只需要改一行模型名，业务代码一行不用动
- **灰度发布**：新模型上线，先给 10% 的流量用，出问题一键切回旧模型，零成本
- **降级容灾**：主模型 API 挂了、限流了，自动切换到备用模型，服务完全不中断，用户根本感知不到
- **成本优化**：简单问题用便宜的小模型，复杂问题用强大的大模型，自动切换，把你的 API 账单直接打下来

## 二、LangChain 灵魂核心：LCEL 表达式，告别祖传屎山代码

如果你还在用旧版的 ConversationChain、RetrievalQA 这些类式 API，那你真的错过了 LangChain 最香的部分——LCEL（LangChain Expression Language，LangChain 表达式语言）。

![LCEL表达式语言让复杂的AI流程变得简洁清晰]({{ site.baseurl }}/assets/images/generated/langchain-de-li-jie-yu-shi-zhan/scene-2.png)



LCEL 就是 LangChain 的「React Hooks」，直接告别了旧时代类式 API 的冗余、难复用、难维护的问题，用声明式的管道写法，让你写 AI 应用跟写 Promise 链一样简单。

### 2.1 什么是 LCEL？5 分钟上手，比写 Promise 链还简单

LCEL 的核心就是一个管道符 `|`，把不同的功能模块像管道一样串起来，前一个模块的输出，就是后一个模块的输入。

咱们用前端的概念类比：它就像 RxJS 的 pipe 方法，或者数组的链式调用，把数据处理的每一步拆成独立的函数，可组合、可复用、可测试。

先看个最简单的例子，对比一下旧写法和 LCEL 写法的差距：

**旧版类式 API 写法（又臭又长，难维护）**

```javascript
import 'dotenv/config';
import { ChatDeepSeek } from '@langchain/deepseek';
import { PromptTemplate } from '@langchain/core/prompts';
import { LLMChain } from 'langchain/chains';

// 初始化模型
const model = new ChatDeepSeek({
  model: 'deepseek-reasoner',
  temperature: 0.7,
});

// 创建提示词模板
const prompt = PromptTemplate.fromTemplate(`
  你是一个{role}，请用不超过{limit}个字符回答：{question}
`);

// 创建Chain
const chain = new LLMChain({ llm: model, prompt: prompt });

// 调用Chain
const res = await chain.call({
  role: '前端架构师',
  limit: 50,
  question: '怎么快速学好React？'
});

console.log(res.text);
```

**LCEL 写法（简洁优雅，一行搞定核心逻辑）**

```javascript
import 'dotenv/config';
import { ChatDeepSeek } from '@langchain/deepseek';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';

// 1. 初始化模型和输出解析器
const model = new ChatDeepSeek({
  model: 'deepseek-reasoner',
  temperature: 0.7,
});
// 输出解析器：直接提取模型返回的文本内容，不用再写res.content
const outputParser = new StringOutputParser();

// 2. 创建提示词模板（推荐用ChatPromptTemplate，适配对话模型）
const prompt = ChatPromptTemplate.fromTemplate(`
  你是一个{role}，请用不超过{limit}个字符回答：{question}
`);

// 3. 用LCEL管道符串起整个流程，一行搞定Chain！
const chain = prompt | model | outputParser;

// 4. 调用Chain，就是这么简单
const res = await chain.invoke({
  role: '前端架构师',
  limit: 50,
  question: '怎么快速学好React？'
});

console.log(res);
```

看到差距了吗？LCEL 写法逻辑清晰，每一步做什么一目了然，没有冗余的类实例化，模块之间完全解耦，想改哪一步直接替换就行，比如想换个模型，直接把 model 变量换了，其他代码一行不用动。

### 2.2 LCEL 的黑魔法：生产级能力开箱即用

你以为 LCEL 只是写法简洁？它真正的王炸，是自带了一堆生产级的能力，不用你自己手写一堆胶水代码。

**能力 1：流式输出，一行代码搞定打字机效果**

上一篇的 Demo 里我们只用了 invoke 方法，但是做聊天应用，必须要有流式输出的打字机效果，LCEL 里直接用 stream 方法就行，简单到离谱：

```javascript
// 还是上面那个chain，一行代码实现流式输出
const stream = await chain.stream({
  role: '前端架构师',
  limit: 100,
  question: '怎么快速学好Vue3？'
});

// 遍历流，逐字输出，前端直接对接打字机效果
for await (const chunk of stream) {
  process.stdout.write(chunk);
}
```

**能力 2：自动重试 + 降级容灾，再也不怕 API 崩了**

生产环境最怕什么？模型 API 超时、限流、挂了。LCEL 自带 withRetry 和 withFallbacks 方法，直接给你的服务上双保险：

```javascript
import 'dotenv/config';
import { ChatDeepSeek } from '@langchain/deepseek';
import { ChatOllama } from '@langchain/ollama';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';

// 主模型：DeepSeek在线模型
const primaryModel = new ChatDeepSeek({
  model: 'deepseek-reasoner',
  temperature: 0.7,
}).withRetry({
  stopAfterAttempt: 3, // 失败最多重试3次
});

// 备用模型：本地部署的Ollama模型，完全不依赖外网
const fallbackModel = new ChatOllama({
  model: 'qwen:7b',
  temperature: 0.7,
});

// 带降级的模型：主模型失败，自动切备用模型
const modelWithFallback = primaryModel.withFallbacks({
  fallbacks: [fallbackModel],
});

// 构建Chain
const prompt = ChatPromptTemplate.fromTemplate(`
  你是一个{role}，请用不超过{limit}个字符回答：{question}
`);
const outputParser = new StringOutputParser();
const chain = prompt | modelWithFallback | outputParser;

// 调用的时候，完全不用关心底层的重试和降级，安心用就行
const res = await chain.invoke({
  role: '前端架构师',
  limit: 50,
  question: '怎么学好TypeScript？'
});
console.log(res);
```

就这么几行代码，你就实现了生产级的重试和降级容灾，再也不怕 API 挂了导致服务不可用。

**能力 3：并行执行，大幅提升接口响应速度**

遇到需要同时调用多个模型、或者多个步骤的场景，LCEL 支持并行执行，不用你自己写 Promise.all，直接提升响应速度。

比如做一个 AI 文案生成工具，需要同时生成标题、正文、结尾，用 LCEL 的并行写法，直接同时执行，不用串行等待：

```javascript
import { RunnableParallel, RunnablePassthrough } from '@langchain/core/runnables';
import { ChatDeepSeek } from '@langchain/deepseek';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';

const model = new ChatDeepSeek({ model: 'deepseek-reasoner' });
const outputParser = new StringOutputParser();

// 标题生成Chain
const titleChain = ChatPromptTemplate.fromTemplate('给文章主题{topic}生成3个爆款标题') | model | outputParser;
// 正文生成Chain
const contentChain = ChatPromptTemplate.fromTemplate('给文章主题{topic}生成100字的正文') | model | outputParser;
// 结尾生成Chain
const endChain = ChatPromptTemplate.fromTemplate('给文章主题{topic}生成一个引导点赞关注的结尾') | model | outputParser;

// 并行执行三个Chain，同时返回结果
const parallelChain = RunnableParallel({
  title: titleChain,
  content: contentChain,
  end: endChain,
  // 把原始输入也透传下去
  topic: new RunnablePassthrough(),
});

// 一次调用，同时拿到三个结果，响应速度直接拉满
const res = await parallelChain.invoke('前端进阶学习指南');
console.log(res);
```

## 三、核心场景进阶实战：从玩具 Demo 到生产级应用

上一篇我们讲了基础的 Demo，这一节咱们直接升级，解决大家做项目时真正会遇到的痛点问题。

![解决真实项目痛点的升级方案]({{ site.baseurl }}/assets/images/generated/langchain-de-li-jie-yu-shi-zhan/scene-3.png)



### 3.1 提示词工程进阶：告别瞎写 Prompt，用模板体系拿捏模型输出

很多同学写 Prompt 就是随便写一句话，结果模型输出的内容忽好忽坏，完全不可控。其实 LangChain 已经给你提供了完整的提示词模板体系，帮你稳定模型输出。

**进阶 1：用 ChatPromptTemplate 替代 PromptTemplate，适配对话模型**

现在我们用的几乎都是对话大模型（Chat Model），而不是旧的补全模型，用 ChatPromptTemplate 可以精准控制消息的角色（系统提示、用户消息、AI 消息），效果比 PromptTemplate 好太多。

```javascript
import { ChatPromptTemplate } from '@langchain/core/prompts';

// 精准定义系统提示、用户消息，角色分离，模型更听话
const prompt = ChatPromptTemplate.fromMessages([
  // 系统提示词：给模型定规矩，写在这里不会被用户的输入轻易绕过
  ["system", "你是一个资深的前端架构师，回答必须简洁专业，只讲干货，不写废话，每一条回答不超过3条要点"],
  // 用户消息：用占位符接收用户输入
  ["human", "用户的问题：{question}，相关技术栈：{techStack}"],
]);

// 格式化提示词
const formattedPrompt = await prompt.formatMessages({
  question: 'React项目性能优化怎么做？',
  techStack: 'React 18 + TypeScript'
});

console.log(formattedPrompt);
```

**进阶 2：少样本学习 FewShotPromptTemplate，让模型秒懂你的要求**

想让模型按照你的格式输出，与其写一大堆要求，不如直接给几个示例，这就是少样本学习。LangChain 的 FewShotChatMessagePromptTemplate 可以轻松实现：

```javascript
import { ChatPromptTemplate, FewShotChatMessagePromptTemplate } from '@langchain/core/prompts';

// 1. 定义示例：告诉模型你想要的输入输出格式
const examples = [
  {
    input: "Vue和React的区别",
    output: "核心差异：1. 核心理念：Vue渐进式框架，React函数式UI；2. 响应式：Vue双向绑定，React单向数据流；3. 上手难度：Vue更低，React对JS要求更高"
  },
  {
    input: "var和let的区别",
    output: "核心差异：1. 作用域：var函数作用域，let块级作用域；2. 提升：var存在变量提升，let存在暂时性死区；3. 重复声明：var允许，let不允许"
  }
];

// 2. 定义单个示例的模板
const examplePrompt = ChatPromptTemplate.fromMessages([
  ["human", "{input}"],
  ["ai", "{output}"],
]);

// 3. 创建少样本提示词模板
const fewShotPrompt = new FewShotChatMessagePromptTemplate({
  examplePrompt,
  examples,
  inputVariables: ["input"],
});

// 4. 拼接成最终的提示词
const finalPrompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个资深前端讲师，回答问题必须简洁明了，只列核心差异，不写废话"],
  fewShotPrompt, // 把示例插在这里，模型自动学习格式
  ["human", "{input}"],
]);

// 调用模型，直接输出符合你格式的内容
const chain = finalPrompt | new ChatDeepSeek({ model: 'deepseek-reasoner' }) | new StringOutputParser();
const res = await chain.invoke({ input: "Promise和async/await的区别" });
console.log(res);
```

用了少样本学习，你会发现模型输出的内容稳定性直接拉满，再也不会出现格式乱飘的情况。

### 3.2 RAG 系统进阶：解决答非所问，从「能用」到「好用」

RAG（检索增强生成）是大家用得最多的场景，上一篇我们给了基础的 Demo，但是很多同学做完发现，检索出来的内容根本不对，模型永远答非所问。这一节咱们就把 RAG 的核心优化点讲透。

**先上基于 LCEL 的生产级 RAG 完整代码**

```javascript
import 'dotenv/config';
// 文档加载与分割
import { PDFLoader } from '@langchain/community/document_loaders/fs/pdf';
import { RecursiveCharacterTextSplitter } from '@langchain/textsplitters';
// 嵌入与向量数据库
import { OpenAIEmbeddings } from '@langchain/openai';
import { Chroma } from '@langchain/community/vectorstores/chroma';
// LCEL核心组件
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { ChatDeepSeek } from '@langchain/deepseek';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { RunnablePassthrough, RunnableSequence } from '@langchain/core/runnables';

// ========== 第一步：文档处理与向量库构建 ==========
// 1. 加载PDF文档
const loader = new PDFLoader('./前端开发规范.pdf');
const docs = await loader.load();

// 2. 文本分块（核心优化点！）
const textSplitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500, // 块大小：技术文档推荐300-800，不要太大也不要太小
  chunkOverlap: 100, // 块重叠：保留上下文，避免关键信息被截断
  separators: ["\n\n", "\n", "。", "！", "？", " ", ""], // 按语义分割，不要硬切
});
const splitDocs = await textSplitter.splitDocuments(docs);

// 3. 生成嵌入向量，存入向量数据库
const embeddings = new OpenAIEmbeddings({
  model: 'text-embedding-3-small', // 用专门的嵌入模型，不要用大模型的嵌入能力
});
const vectorStore = await Chroma.fromDocuments(splitDocs, embeddings, {
  collectionName: 'frontend_docs',
});

// 4. 创建检索器
const retriever = vectorStore.asRetriever({
  k: 4, // 只返回最相关的4条内容，不是越多越好
  searchType: 'similarity', // 相似度检索，进阶可以用mmr最大边际相关性，兼顾相关性和多样性
});

// ========== 第二步：构建RAG问答Chain ==========
// 1. 构建RAG专属提示词模板
const ragPrompt = ChatPromptTemplate.fromTemplate(`
你是一个专业的文档问答助手，只能基于下面的参考文档回答用户的问题，绝对不能编造文档里没有的信息。
如果参考文档里没有相关内容，直接回答"抱歉，参考文档中没有相关内容"，不要自己瞎编。

参考文档：
{context}

用户的问题：{question}
`);

// 2. 格式化检索到的文档内容
const formatDocs = (docs) => docs.map(doc => doc.pageContent).join('\n\n');

// 3. 用LCEL构建RAG Chain
const ragChain = RunnableSequence.from([
  // 并行获取检索内容和原始问题
  {
    context: (input) => retriever.invoke(input.question).then(formatDocs),
    question: new RunnablePassthrough(),
  },
  ragPrompt,
  new ChatDeepSeek({ model: 'deepseek-reasoner', temperature: 0 }),
  new StringOutputParser(),
]);

// ========== 第三步：调用问答 ==========
const answer = await ragChain.invoke({
  question: '公司的Git提交规范是什么？'
});

console.log(answer);
```

**RAG 核心优化点，解决答非所问的痛点**

- **文本分块是重中之重**：很多人 RAG 效果差，90% 的问题都出在分块上。不要一刀切用 1000 甚至 2000 的 chunkSize，技术文档推荐 300-800 的 chunkSize，一定要加 chunkOverlap，避免关键信息被切在两个块里，还要按语义分割，不要硬把一句话切成两半。
- **嵌入模型要选对**：不要用大模型自带的嵌入能力，专门的嵌入模型（比如 OpenAI 的 text-embedding-3-small、阿里云的 text-embedding-v2）效果好太多，而且成本极低。
- **检索结果不是越多越好**：很多人觉得 k 设得越大，内容越多越好，其实不对。太多无关内容会污染模型的上下文，反而让回答跑偏，一般 k 设 3-5 就足够了。
- **提示词一定要加边界限制**：必须明确告诉模型「只能用参考文档的内容回答，不能编造信息，没有就说不知道」，不然模型会一本正经地胡说八道，这就是 RAG 里最常见的「幻觉问题」。

### 3.3 多轮对话进阶：聊一百轮也不崩的上下文管理

做聊天机器人，最常见的问题就是聊个十几轮就崩了，要么上下文全忘了，要么 token 直接爆了。核心就是没做好上下文的内存管理。

LangChain 提供了完整的对话内存管理方案，结合 LCEL，轻松实现不崩的多轮对话：

```javascript
import 'dotenv/config';
import { ChatDeepSeek } from '@langchain/deepseek';
import { ChatPromptTemplate, MessagesPlaceholder } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { RunnableWithMessageHistory } from '@langchain/core/runnables';
import { ChatMessageHistory } from '@langchain/community/stores/message/in_memory';

// 1. 构建带历史消息的提示词模板
const chatPrompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个友好的前端技术助手，专业解答前端相关问题，回答简洁易懂"],
  // 关键：MessagesPlaceholder用来存放历史对话消息
  new MessagesPlaceholder("chat_history"),
  ["human", "{input}"],
]);

![ChatPromptTemplate构建消息模板的代码世界]({{ site.baseurl }}/assets/images/generated/langchain-de-li-jie-yu-shi-zhan/scene-4.png)



// 2. 初始化模型和Chain
const model = new ChatDeepSeek({ model: 'deepseek-reasoner', temperature: 0.7 });
const outputParser = new StringOutputParser();
const chatChain = chatPrompt | model | outputParser;

// 3. 给对话加上历史消息管理
const chainWithHistory = new RunnableWithMessageHistory({
  runnable: chatChain,
  // 按sessionId存储不同用户的对话历史，多用户场景直接用
  getMessageHistory: (sessionId) => new ChatMessageHistory(),
  inputMessagesKey: "input",
  historyMessagesKey: "chat_history",
});

// 4. 多轮对话测试
// 第一轮对话
const res1 = await chainWithHistory.invoke(
  { input: "我现在在学React，应该先学什么？" },
  { configurable: { sessionId: "user_001" } } // 每个用户一个唯一sessionId
);
console.log("AI回答1：", res1);

// 第二轮对话，AI自动记住上下文
const res2 = await chainWithHistory.invoke(
  { input: "那学完这些之后呢？" },
  { configurable: { sessionId: "user_001" } }
);
console.log("AI回答2：", res2);
```

**进阶优化：解决 token 爆仓问题**

对话轮次多了，历史消息会越来越长，token 直接就爆了。这时候可以用对话摘要内存，自动把长对话压缩成摘要，只保留关键信息，大幅减少 token 占用：

```javascript
import { ConversationSummaryMemory } from 'langchain/memory';

// 初始化摘要内存，自动总结对话历史
const memory = new ConversationSummaryMemory({
  llm: new ChatDeepSeek({ model: 'deepseek-reasoner' }),
  returnMessages: true,
  memoryKey: "chat_history",
});

// 每次对话结束，自动把新的对话内容更新到摘要里
// 不管聊多少轮，摘要都只会保留关键信息，token占用极低
```

## 四、LangChain 生产级避坑指南：90% 的人都踩过这些坑

**坑 1：乱用 PromptTemplate，对话模型效果直接打对折**

很多人不管什么场景都用 PromptTemplate，但对于对话模型，ChatPromptTemplate 的角色分离能力，能让模型的效果和可控性提升一个量级。记住：只要用的是 Chat 模型，优先用 ChatPromptTemplate。

**坑 2：文本分块一刀切，检索永远答非所问**

不要随便抄个 chunkSize=1000 就用，不同的文档类型，分块策略完全不一样：

- 技术文档、合同条款：chunkSize 小一点，300-800，保证语义完整
- 小说、长文：chunkSize 可以大一点，800-1500，保留上下文
- 一定要加 chunkOverlap，一般是 chunkSize 的 10%-20%

**坑 3：不做 token 管理，聊几句就爆上下文**

永远不要把完整的历史消息全丢给模型，一定要做上下文管理：要么用滑动窗口只保留最近的几轮对话，要么用摘要内存压缩历史消息，不然 token 账单和报错会教你做人。

**坑 4：没有错误处理和降级，线上一限流就崩**

LLM 的 API 不是 100% 稳定的，超时、限流、报错是常有的事。生产环境一定要加重试机制和降级策略，LCEL 的 withRetry 和 withFallbacks 直接用，不要自己手写一堆 try/catch。

**坑 5：不用 LCEL，硬写胶水代码，维护到哭**

很多人还在用旧的 LLMChain、RetrievalQA，甚至自己手写 Promise 串流程，代码又臭又长，改一个需求就要重构一半。赶紧拥抱 LCEL，声明式的写法，可组合、可复用、好维护，谁用谁知道。

**坑 6：硬编码 API 密钥，上线直接被刷爆欠费**

永远不要把 API 密钥硬编码在代码里！一定要用环境变量加载，生产环境用云服务的密钥管理服务，不然代码一提交到 GitHub，密钥直接被爬虫爬走，一夜之间欠费几万块，这种事真的天天都在发生。

## 五、进阶玩法拓展：LangChain 生态的王炸组合

掌握了上面的内容，你已经能写出生产级的 AI 应用了。如果还想进阶，LangChain 的生态还有两个王炸组合：

- **LangSmith**：LangChain 官方的调试、监控、评估平台，能看到每一次调用的完整链路、token 消耗、耗时，还能给模型的输出做评分，调试 AI 应用跟调试前端代码一样简单。
- **LangGraph**：基于 LangChain 的智能体工作流框架，能实现更复杂的循环、分支、多智能体协作，比如代码生成机器人（写代码→执行→调试→重写）、智能客服机器人（检索→判断→转人工），能实现普通 Chain 做不到的复杂业务逻辑。

## 结语

其实 LangChain 从来都不是什么高深的东西，它只是把 AI 应用开发里的通用能力做了封装，让我们这些开发者不用重复造轮子，能专注于业务逻辑本身。

对于咱们前端全栈开发者来说，JS/TS 版本的 LangChain，就是我们进入 AI 应用开发领域最好的入场券——不用学新的语言，不用换技术栈，用你最熟悉的代码，就能写出顶级的 AI 应用。

![JS/TS版本LangChain是前端开发者进入AI领域的入场券]({{ site.baseurl }}/assets/images/generated/langchain-de-li-jie-yu-shi-zhan/scene-5.png)

