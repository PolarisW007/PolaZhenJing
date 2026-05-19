---
layout: industry-vision
theme: wukong
title: "Anthropic 是如何搭建可以持续运行 6 小时的 Agent Harness?"
date: 2026-05-19
tags: []
summary: "“build a retro game maker”。就这一句话。一个完整的复古游戏制作器，54色调色板、8-bit怀旧美术风格、可玩的play mode、能感知角色撞墙的物理反馈，还有一套AI关卡助手——你跟它说“造一座城堡，让小角色守在门口”，它真的能给你做出来。整个过程持续了6小时，耗资约200美元。"
---

![三个AI Agent在像素游戏场景中协作，Generator在编写代码，Evaluator在测试，Planner在规划，整体呈现吉卜力风格的团队合作画面]({{ site.baseurl }}/assets/images/generated/anthropic-shi-ru-he-da-jian-ke-yi-chi-xu-yun-xing-6-xiao-shi/cover.png)

# Anthropic是如何搭建可以持续运行6小时的Agent Harness？

## 6小时、200美元，一个“糟糕”的prompt引发生成式AI工程革命

“build a retro game maker”。

就这一句话。一个完整的复古游戏制作器，54色调色板、8-bit怀旧美术风格、可玩的play mode、能感知角色撞墙的物理反馈，还有一套AI关卡助手——你跟它说“造一座城堡，让小角色守在门口”，它真的能给你做出来。

![复古游戏制作器界面，54色调色板，8bit像素风格，AI关卡助手正在帮角色建造城堡]({{ site.baseurl }}/assets/images/generated/anthropic-shi-ru-he-da-jian-ke-yi-chi-xu-yun-xing-6-xiao-shi/scene-1.png)



整个过程持续了6小时，耗资约200美元。

这是Anthropic Applied AI团队的Ash Prabaker和Andrew Wilson在AI Engineer大会上展示的demo。他们用同样的prompt、同样的模型跑了一个单循环对照版。表面上看完成度差不多，但只要按方向键、空格键试着玩一下——游戏完全不响应。

模型不知道怎么对自己交付的结果进行测试，更不知道怎么“玩一个游戏”。

这个完成度的差距，不是模型造成的，是Harness给的。

---

## 自评估：一个被严重低估的陷阱

影响Agent持久运行的问题，业界通常归为三类：Context window有限导致跨session失忆；Planning能力不足导致要么试图一发做完、要么写半个feature就停手；以及第三个、往往被忽视的问题——模型极不擅长评估自己的输出。

它会看着一个半成品功能说“做完了”，或者只做了一个按钮、后端根本没通，却报告说feature已就绪。

我们都熟悉LLM的sycophancy（讨好倾向）。它会在对话里讨好你，但同样的毛病在自己的代码上也会发作，变成一种自我安慰。

大多数团队今天搭长程Agent的做法是开一个Claude Code session，让它自己干、再让它自己检查。这个方法有明确的天花板：同一个模型在同一个context里既当裁判又当运动员，自评估这件事它根本做不到。

Anthropic内部解决这个问题的方式，是直接从GAN（生成对抗网络）借鉴思路——把generator和evaluator完全分成两个独立的context，system prompt不同，岗位不同，任务不同。Generator写代码，Evaluator用Playwright打开浏览器、点来点去、截图、做判断，然后把critique文件交回generator。

但这里有个显而易见的问题：Evaluator自己也是LLM，凭什么不会同样盖章了事？

Ash给出的答案是，**把一个独立的critic调教得很严格是可行的，把一个builder调教得对自己批判，这件事做不到**。这是LLM能力的一个基本局限性：让它点评一道菜或一幅画很容易，让它自己画或自己做就难得多。Critic和Generator是两件事，塞到同一个角色里只能得到讨好型的代码，拆开才能通过对抗压力优化代码。

---

## 三个角色如何真正协作：不是分工，是对抗

光把角色分开还不够。Anthropic又加了一个Planner。

Planner接到一句话prompt，只把整体工作流分解成一组sprint，不规划颗粒度细的技术细节。原因很简单：**细节越早定越容易错，而错会沿sprint一路传播，在多小时尺度上放大成灾难**。

如果你仔细看，这就是个普通的PM、IC、QA三角组织。他们没发明任何东西，只是给每个角色一个独立context window。

![三个独立的气泡context window，分别代表PM、IC、QA三个角色，形成三角协作组织]({{ site.baseurl }}/assets/images/generated/anthropic-shi-ru-he-da-jian-ke-yi-chi-xu-yun-xing-6-xiao-shi/scene-2.png)



Generator和Evaluator之间的“胶水”才是这套设计的关键。Generator在写第一行代码之前，要先和Evaluator谈判“完成”是什么意思：

- Generator提议：我做X feature，你用Y测试验证。
- Evaluator顶回去：scope太大、测试太弱、漏了XYZ边界。

两个Agent通过磁盘上的markdown文件来回，一个写、另一个读，反复直到双方点头。之后Evaluator评分，用的是这份谈出来的contract，不是Planner一开始写的spec。

这一步用一句话叫：**把user story桥接成可测的assertion**，不需要Planner在前面就把所有细节定死。Ash把这看成Ralph Loop一直缺的那一块。Ralph Loop是去年开始流行的一种简单做法，把prompt喂进CLI循环跑直到任务完成，本质就是一个plan.md加一个固定loop；问题在于没有人在另一边反驳主loop，谁也不质疑“完成”是否真完成。

回到Retro Forge演示的那个demo，两个Agent总共谈出来27条contract。粒度细到这个程度，critique才能让generator知道“我要去修的就是这一行”。粒度一粗，critique就含糊，generator只会耸肩了事。

---

## Claude是个糟糕的通用QA Agent

Ash在演讲中明确表示：**开箱即用的Claude是个非常糟糕的通用QA Agent**。

LLM-as-judge那套已知的问题——讨好倾向、容易放水——在Evaluator角色上一样存在。早期跑Retro Forge的时候，QA Agent经常找到一个bug，直接说“以后再修、大概要两周”，然后甩手不干。

Anthropic没有什么秘诀。他们花在这上面的时间，大部分是手工读trace。

整个系统好不好，关键就是读trace。主调试loop是逐行读Agent实际做了什么，看它的判断在哪儿和他们拉开，然后回头改prompt。比起再跑一次实验，这个慢办法管用得多。

读trace是一种类似读stack trace的肌肉记忆。这一点不光适用于Agent调试，也适用于Agent设计本身。做Claude for Chrome那个浏览器use工具时，Anthropic团队做过一个练习：闭着眼睛在网页上导航，每10秒钟睁眼看一张静态截图，再闭眼操作。这就是模型当时的处境。

**要搭出在线上能信任的Agent，你需要站在模型的视角去思考。**

---

## Harness不会随模型变强而消失——但会被简化

Andrew用一年时间线把Claude Code的演进梳理了一遍：从Sonnet 4.5的1小时长跑能力，到Opus 4.6在最简单scaffold下的12小时。这一年里每发一次模型，几乎都同步发一批对Harness的改动。

但同步进化不是简单地堆砌Harness。模式是这样的：**Harness先填模型的坑，然后这一坑被训练进下一代模型，对应的Harness模块就被拆掉，循环往复**。

![Harness填模型坑的循环进化图，旧的Harness模块被拆掉，模型变强]({{ site.baseurl }}/assets/images/generated/anthropic-shi-ru-he-da-jian-ke-yi-chi-xu-yun-xing-6-xiao-shi/scene-3.png)



Sonnet 4.5时代，跨session的context reset是必须的，因为模型一接近context window末尾就anxiety发作、草草收尾。Opus 4.6通过post-training把这个问题的根源做掉了，Anthropic内部就把“开新context window”这一招直接弃用，改成单session加compaction。同样地，Opus 4.5必须依赖把sprint切碎、一勺一勺喂feature才能稳定运行；到了Opus 4.6，它能连续2小时连贯写代码，这一招也简化了。

Ash总结：目前这套Harness在4.5上是对的，前沿模型一改动，他们就跑到简化版看看够不够用。**所以今天写下来的任何Harness pattern，寿命都是有限的**。它更像一根针对当代模型短板的脚手架，谈不上基础设施。

---

## 最终形态：简单到令人意外

Anthropic内部目前用的最终架构，其实简单得令人意外。

Planner、Generator、Evaluator三角依然是核心loop，大量增加复杂度的辅助组件被拆掉。共享状态用文件系统，不用context window——**长程Agent把状态都堆context里是一条死路**。

文件系统这一招还有个隐藏好处。Ash习惯在loop里到处插prompt，让模型把“学到的东西”和当前状态写进一个JSON文件。模型对JSON比对markdown克制得多，不爱整段覆写。一个时间戳化的log，记录每次试了什么、Evaluator怎么评、做了什么修复、是否成功；再加一份live更新的高层级文档说清楚文件结构。两份文件就足够下一个进来的人或模型上手。

这是一种“breadcrumbs”思路。**不假设这个Agent会一口气跑完所有事，而是假设迟早会有人（或者另一个Agent）从中间介入。**

---

## Evaluator会让Generator推倒重来——这是好事

有人在Q&A里问：跑出来的东西不满意怎么办？能不能让人在中间review一下、把它引到更好的方向？

这里有个出乎意料的观察。Opus和Sonnet 4.6一代的模型，在Evaluator反复打分的压力下，极其乐意“推倒重来”。哪怕已经迭代了10轮，只要在rubric上爬不动，它会高兴地把所有代码扔了从零再来。

Ash没有看到他们一开始预期的那种“Evaluator嫌烦、放过Generator”的现象，反而经常看到Evaluator主动提议：这条路明显走不通，把所有东西删了重来。

这件事写代码的人都熟悉。为了换一个fresh context，为了不在已经搞乱的codebase上继续修补，我们自己也常这么干。模型也走到了这一步。

![程序员坐在整洁的工作台前，面前是从混乱codebase切换到fresh context的对比]({{ site.baseurl }}/assets/images/generated/anthropic-shi-ru-he-da-jian-ke-yi-chi-xu-yun-xing-6-xiao-shi/scene-4.png)



这一点带出了Anthropic在Harness哲学上的一个明确选择：**他们要的是完全自主的Harness，不打算塞人进去补稳定性**。Ash在面对“要不要做sprint review，让人定期介入”这个问题时，直接反问：我们要不要让Agent也体验一把scrum review的折磨？

如果一定要加人，他们的做法是用hooks：Evaluator触发停止条件、把控制权交给人、允许人输入消息、继续loop。但这是个例外形态，不是默认形态。**Harness的稳定性应该烤进Harness自身，不是靠人外挂补救。**

---

## 现在就能开始搭建

你不需要等内部Harness公开，因为能用的零件已经齐备了：

- **Auto mode**：刚发的功能，介于安全和自主之间的yellow模式，免得你动不动dangerously skip permissions
- **Custom sub-agents**：已经是一个基础能力，你只需要定义一个严格的system prompt加详细rubric，即是一个Evaluator和QA的角色
- **MCP集成**：网页app上Playwright MCP或Claude for Chrome MCP已经能直接用，原生app用computer use
- **Skills**：把评分rubric打包进日常开发流的好方法

---

## 五条建议，贴墙上

如果你要落地一套类似的对抗式Harness，这五条建议值得贴在墙上：

**第一，自评估是陷阱，用对抗式Evaluator。**

同一个模型既写代码又判断质量，一定会讨好自己。把角色拆开，让Evaluator有独立的context和严格的rubric。

**第二，compaction不等于coherence。**

有损总结一定走偏。结构化交接加干净context是更好的pattern，别迷信“把长对话压缩一下就能继续”。

**第三，主观品质能评分，只要你对“好”有强烈意见。**

很多人觉得“我知道什么是好，但说不出来”。其实强迫自己写下来是最好的调试方式。把rubric写清楚，Evaluator才知道真正的目标是什么。

**第四，角色拆开，共享状态用文件系统。**

不要把状态堆在context window里。文件系统的隐式好处是：它逼着模型做结构化输出，而JSON比markdown克制得多。

**第五，坐下来读trace。**

这是真正决定scaffold哪一块该删、哪一块该留的方法。别光跑实验，trace里有模型判断和你预期之间的gap，那才是改进的起点。

---

## 你的Harness可能才是问题所在

这套思路并不只适用于“6小时做出一个游戏”。你现在团队里那些反复让一个Agent既写代码又自检的脚本、那些Ralph Loop改造版、那些把spec一次性堆给sub-agent的工作流，都可以套这个lens检查一遍。

![审视团队现有Agent工作流的画面，检查清单、工作流图和多个AI Agent脚本]({{ site.baseurl }}/assets/images/generated/anthropic-shi-ru-he-da-jian-ke-yi-chi-xu-yun-xing-6-xiao-shi/scene-5.png)



有没有把generator和critic强行塞在同一个角色里？

contract是不是一开始就被定死了、有没有人在另一边反驳？

状态是不是被堆在context window里、跨session就丢了？

**如果有，问题大概率不在模型，而在Harness上。**