---
layout: academic-insight
theme: wukong
title: "FDE 模式 探索和研究"
date: 2026-05-21
image: "/assets/images/generated/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/cover.png"
tags: []
summary: "2026年5月4日，OpenAI和Anthropic在同一天各自宣布了一件大事。OpenAI联合TPG等19家机构成立了Deployment Company，砸了40亿美元，专门往企业里派工程师帮他们把AI塞进核心业务流程。"
description: "2026年5月4日，OpenAI和Anthropic在同一天各自宣布了一件大事。OpenAI联合TPG等19家机构成立了Deployment Company，砸了40亿美元，专门往企业里派工程师帮他们把AI塞进核心业务流程。"
---

![一位工程师站在企业核心位置，身后连接着数据平台的光芒，解决方案像光线一样从工程师位置向平台汇聚]({{ site.baseurl }}/assets/images/generated/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/cover.png)

# 最近半年一直在关注 Palantir 的 FDE 模式

2026年5月4日，OpenAI和Anthropic在同一天各自宣布了一件大事。OpenAI联合TPG等19家机构成立了Deployment Company，砸了40亿美元，专门往企业里派工程师帮他们把AI塞进核心业务流程。同一天，Anthropic宣布跟Blackstone、Goldman Sachs、Hellman & Friedman合作，投入15亿美元成立企业服务实体，把Claude部署到中型企业的日常运营中。几天之后，Google Cloud CEO Thomas Kurian亲自发LinkedIn招聘帖，宣布要招数百名FDE。

![最近半年一直在关注 Palantir 的 FDE 模式 — 用户配图 1]({{ site.baseurl }}/assets/images/uploads/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/user-01.webp)



三家巨头同时下注同一个事情，这在科技行业并不常见。但比这更值得玩味的，是他们在争夺的那个词——FDE，Forward Deployed Engineer，前线部署工程师——在行业里引发的争议。

有人说这是Palantir的看家本领，支撑它从神秘小公司走到千亿市值的秘密武器。也有人说这不过是个硅谷味的造词，本质上就是换了包装的咨询师。还有人说现在大量公司只是在把Solutions Engineer改个title叫FDE，实际上什么都没变。

三种说法听起来都有道理。但这不意味着FDE是个见仁见智的概念——恰恰相反，这说明市面上讨论的压根不是同一个东西。

## 给FDE一个清晰的定义

过去半年，我把市面上关于FDE的研究整理了一遍。Bob McGrew（Palantir FDE从0到1的亲历者，后任OpenAI VP Research）在YC的访谈，a16z、Sequoia、Flybridge等VC的分析，Palantir官方博客里FDSE的工作日常，Gartner和Everest Group等机构的报告——加起来有6万字。整理完之后，我的结论是：市场对FDE的讨论之所以混乱，是因为至少有两种完全不同的叙事被混在了一起。

先把定义说清楚。

**FDE是嵌入客户环境的工程师，背靠一个平台级产品，通过在现场解决客户的真实问题来发现产品应该长什么样。他的工作产物不属于单一客户，而是回流到平台，成为可服务更多客户的产品能力。**

这个定义里有四个要素，少了任何一个，它就变成别的东西：

**第一，有平台。** 没有平台级产品，就没有FDE。这是前提。产品管理领域的教父级人物Marty Cagan说过：“真正让Palantir如此高效、如此有价值的原因，是他们以platform product company的方式来解决这个问题。”没有平台，FDE的工作就是一次性的。

**第二，嵌入客户环境。** Forward Deployed，字面意思就是部署到前线。不是远程支持，不是售后回访，是在客户的工作环境里，从内部理解问题。

**第三，目的是产品发现，不是实施。** FDE去客户现场不是把一个已知方案装上去，而是去发现“产品应该长什么样”。产品的形态还没有定型，只有在现场解决真实问题的过程中才能被发现。

**第四，产物回流平台。** FDE在客户现场做出来的东西，不只是留给这个客户的交付物，而是要回流到平台，成为可服务更多客户的产品能力。

用这四个要素做尺子，很多事情就清楚了。去掉平台，你是咨询师。不嵌入客户，你是传统产品团队。只做实施不做发现，你是系统集成商。产物不回流，你是外包。

## 试金石：怎么判断真假FDE

FDE这个概念之所以争议这么大，一个重要原因是它的名字被大量滥用。McKinsey在招"Principal Forward Deployment Engineer"，EY在英国推出了FDE岗位，Accenture跟Microsoft、ServiceNow合作搞"Forward Deployed Engineering Program"。这些公司有自己的平台产品吗？没有。他们在做的事情是帮客户用别人的工具做AI转型，产物属于客户，不会回流到任何平台。每个项目从头来，线性增长。

这就是咨询。或者更准确地说，是三种传统角色穿上了新衣服：

**咨询型**：帮客户规划“你应该用AI做什么”，组合市场上的工具出方案。产出是方案和建议。

**实施型**：帮客户把某个AI产品部署上线、配好、跑通。产出是一个配置好的系统。

**SE换标签型**：Pragmatic Engineer的Gergely Orosz观察到，大量公司只是把现有的Solutions Engineer或Solutions Architect改了个头衔叫FDE，工作内容没有任何变化。

三种都不是FDE。因为产物都不回流到任何平台。

那怎么判断一个人到底是FDE还是咨询师？

我有一个暴论：**看这个人的成本在公司内部是算产品研发的，还是算项目交付的。** 如果是后者，不管你title写的是什么，你就是在做咨询。

VC Thomas Otter说过一句类似的话：“If the FDE is billable, they are working for the project, not the product.” FDE一旦按项目计费，他就是在为项目工作，不是为产品工作。

![最近半年一直在关注 Palantir 的 FDE 模式 — 用户配图 2]({{ site.baseurl }}/assets/images/uploads/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/user-02.webp)



还有一个更直觉的检验：**你的第10个客户跟第1个客户花的精力一样多吗？** 如果是，你就是在做咨询。FDE模式下，每一次客户部署都应该让平台变得更强，下一次部署的effort应该更少。这是一个飞轮，不是一条直线。

a16z合伙人Marc Andrusko的判断很直接：如果你只复制了嵌入式工程师的部分，却没有底下的平台在支撑，最终你不是“某领域的Palantir”，你只是“某领域的Accenture，换了个更好看的前端界面”。

市场数据也在支持这个判断。Paraform的分析显示，FDE岗位在2025年1-9月增长了800%，但合格候选人池只增长了约50%。59%的FDE招聘公司还处于Seed到Series A阶段——这些公司连产品都没完全定型，更需要FDE去前线探索，但也很容易把FDE用成咨询。

## FDE是怎么运作的

说FDE是一种方法论而不是一个孤立的岗位，是因为它需要一整套协作方式来支撑。Palantir内部有三个核心角色，共同构成了这套体系：

**Echo（回声团队）是嵌入式分析师。** 他们来自客户所在的领域：前陆军军官、医疗行业老兵、金融合规专家。但Bob McGrew说了一个关键条件：他们必须是“叛逆者”。他们理解这个行业现在是怎么运作的，但同时认为现状不够好。如果一个Echo觉得“这个行业挺好的”，他永远找不到那个让新软件必须存在的3x-10x的改变机会。

**Delta（三角洲团队）是前线工程师，也就是狭义上的FDE。** 他们的核心能力是快速做原型。Flybridge与Palantir现任FDE Brian Keohane的讨论得出一个关键结论：“错误的Delta画像是匠人”。追求完美抽象、想写能维护十二年的代码，那不是这个角色的任务。Palantir内部一位FDE负责人Katherine用了另一个说法：“我们更像是一个艺术家社群”。每个FDE的核心能力不同，但共同点是高用户同理心、对商业战略的理解力和创造性解题能力。你要的不是完美代码，而是一个能在客户现场用粗糙但管用的方案快速交付结果的人。

**Dev（平台工程师）是留在总部的人。** 他们负责开发和维护Palantir的平台产品。他们不去客户现场，但他们的工作直接决定了FDE在前线有多少产品杠杆可用。Palantir官方博客对这两种工程师有一个很简洁的总结：Dev的视角是“一个能力，多个客户”；Delta的视角是“一个客户，多种能力”。

三个角色的关系是：Echo在客户现场找到正确的问题，Delta快速构建解决方案，Dev把前线验证过的方案抽象为平台能力，让下一个Delta去下一个客户时有更强的武器。这是一个完整的循环，不是三个独立的岗位。

那么FDE在客户现场每天具体干什么活？Palantir的一位FDSE在官方博客里列过他的典型技术问题：

- 怎么构建、扩展和维护一个TB级的数据管道，给关键任务的运营工作流提供数据？
- 怎么根据客户独特的合规要求，配置平台的数据访问权限和工作流控制？
- 怎么为一个非技术背景的客户设计一个可视化工作流，让他们能跟高噪声数据交互？怎么把这个功能泛化，让其他FDE和客户也能受益？
- 生产环境出了故障，怎么排查根因、部署修复、监控稳定性？

注意最后两个问题里反复出现的一个词：“泛化”。这就是FDE和普通实施工程师的区别。实施工程师解决完问题就完了，FDE解决完问题之后还要想：“这个方案能不能变成平台的一部分，让下一个人不用重来？”

什么样的人适合做FDE？从上面的描述你大概能感觉到，FDE需要的不是一般的工程师画像。Flybridge的Daniel跟Palantir现任FDE Brian Keohane讨论后，总结了一个相当一致的人才画像：

- **极强的ownership和韧性**。他们像founder一样对结果负责，把客户的工作流当自己的产品，不惜一切让生产系统跑起来。
- **偏好行动而非分析**。先交付一个粗糙但管用的“碎石路”方案，快速创造价值，而不是分析到死。
- **对模糊性感到自在**。客户说不清需求，环境混乱，真正的问题藏在表面之下。FDE在这种环境里如鱼得水。
- **技术+沟通双能力**。能写生产级代码，也能给CFO讲架构决策。这个组合极其稀缺。

简单说：**像founder，不像craftsman。**

这也是为什么Palantir出了那么多startup founder：Kalshi的Tarek Mansour、Hex的Glen Takahashi、Sourcegraph的Quinn Slack、Anduril的Matt Grimm、Fern的Deep Singhvi，都是前FDE。

## 飞轮：从碎石路到铺好的路

FDE在客户现场做出来的东西，在Palantir内部叫“碎石路”（gravel road）。粗糙、直接、只为这一个客户解决这一个问题。这完全合理，也是FDE应该做的事情。

但碎石路不能直接搬进产品。产品团队的工作是把碎石路变成“铺好的路”（paved road），一条不只经过这一个客户、还能经过后面一堆客户的路。

![最近半年一直在关注 Palantir 的 FDE 模式 — 用户配图 3]({{ site.baseurl }}/assets/images/uploads/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/user-03.webp)



这就是飞轮：

- FDE在客户A的现场发现了一个需求，做了一个碎石路方案
- 带回总部，产品团队问：“这个问题的通用版本是什么？”
- 拉来客户B、C的FDE一起讨论，确保通用版本对他们也管用
- 产品团队构建通用能力，纳入平台
- 下一个FDE去客户D的时候，可以直接用这个能力，不用从头来

Palantir最著名的产品能力Ontology就是这么来的。最开始，每个客户都有自己的数据库：人、资金、船只各一张表。部署到第二个客户的时候，表结构就对不上了。产品团队把它抽象成了"objects + properties + links"的通用模型，让FDE按客户自行定义具体的对象类型。这个抽象化的过程，就是碎石路变成铺好的路。

这个飞轮里有一个容易被忽略的点：**产品团队的用户不只是最终客户，还有FDE本身。** 产品要给FDE提供杠杆，让他们能用更少的effort交付更多的价值。如果产品做得对，FDE应该会主动选择用产品的通用能力，而不是自己hack一个一次性方案。如果FDE不愿意用你的产品，大概率是产品做错了。Thomas Otter甚至预判：“明年最酷的岗位将是platform product manager”。

飞轮能不能转，关键不在FDE，而在平台产品团队。

当然，这个飞轮的效率不是文章暗示的那么理想。即使是Palantir，professional services收入占比多年来也没有显著下降。飞轮在转，但转得不快。对大多数公司来说，飞轮从启动到产生可见效果需要1-3年，这段时间里你看起来就是一家咨询公司。能不能坚持下去，取决于你对“过渡态”的信念和资本的耐心。

## 为什么AI时代天然适合FDE

FDE这个模式是Palantir在2010年发明的，为什么到了2026年突然所有AI公司都在做？

答案不是“因为Palantir成功了所以大家抄”。如果只是抄，前面说了，绝大多数会抄成咨询。

答案是：**AI这个品类本身的特性，让FDE成为了一种结构性需要。**

传统SaaS替换的是已有产品。你做一个更好的CRM来替代Salesforce，市场长什么样，大家都知道。你可以坐在办公室里研究竞品，做出一个更好的版本，然后卖出去。

AI agent不是。Bob McGrew说得很直接：“构建AI agent”这件事本身可能包含很多完全不同的东西，我们现在还不知道那些东西是什么。五年后回头看，可能“AI agent”这个词根本不存在了。

这意味着AI产品天然有一个价值发现的瓶颈。能力可能很强，但如果没人找到killer use case，能力就是空转的。

在个人用户场景下，这个瓶颈可以靠自然传播解决：有人发现了一个用法，发到社交媒体，其他人跟进。但在企业场景下不行。企业有合规要求、有遗留系统、有组织惯性，不会有人在Twitter上发帖说“我发现我们银行的反洗钱流程可以用Claude压缩90%”。你需要有人去现场帮他们发现。

这个人就是FDE。他的角色不只是“去客户现场搞清楚需求”，而是**主动制造golden case**。

Stripe的Forward Deployed AI Accelerator（FDA）是最好的企业端案例。Stripe发现自己的marketer已经在自发地用AI做出了一些东西：自己搭数据看板，创建能把多天流程压缩的agent。FDA团队的工作不是从零开始教人用AI，而是把这些已经被发现的golden case系统化地推广到整个营销组织。他们的成功标准是“你永久改变了多少个工作流”。

价值是marketer自己先发现的，FDA是去系统化推广已被验证的用法。这跟传统的“产品团队设计功能然后推给用户”完全是反过来的。

Anthropic+FIS的合作也是同一个逻辑。就在这个月（2026年5月），Anthropic把FDE直接嵌入了FIS，合作开发反洗钱AI Agent，目标是把调查时间从数小时压缩到数分钟。模型能力（Claude）是现成的，金融合规知识在FIS那边，但把两者结合起来、在受监管环境中跑通，需要有人坐在中间。FIS的Ferris说了一句很直接的话：“You're not going to innovate around us.”

能力远超采用，FDE填的就是这个gap。

a16z合伙人Joe Schmidt的类比很到位：企业买AI就像你奶奶拿到一台iPhone，她想用，但需要你帮她设置好。在platform shift期间，implementation-heavy的模式不是缺陷，而是特征。Salesforce IPO前烧掉了5200万美元才产生2200万美元收入。但正因为它把复杂实施做到位了，现在市值2540亿美元。

![最近半年一直在关注 Palantir 的 FDE 模式 — 用户配图 4]({{ site.baseurl }}/assets/images/uploads/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/user-04.webp)



Joe Schmidt还说了一个更深层的判断：**软件不再是辅助工人的工具，软件本身就是工人。** 但软件要成为合格的“工人”，需要FDE帮企业重新设计岗位职能和流程。Alex Rampell把这个拉到了市场规模的层面：企业软件市场年支出3000亿美元，但白领劳动力市场是数万亿美元。FDE做的事情不是在3000亿的市场里分蛋糕，而是在撬动万亿级的新市场。

## 窗口期与终局

最后说一个不那么乐观的判断。

Sequoia合伙人Julien Bek提出了一个Intelligence vs Judgement的框架。写代码是intelligence（可编码、可规则化的认知工作），决定下一步做什么是judgement（需要经验和品味的决策）。AI正在快速接管intelligence型的工作，但judgement目前还需要人类。

FDE目前做的大量工作属于judgement：判断客户真正需要什么、决定怎么设计工作流、在模糊的环境里定义问题。但Julien Bek的关键判断是：“Today's judgement will become tomorrow's intelligence.” 今天需要judgement的事，随着AI系统积累足够多的数据，最终也会变成intelligence。

这个窗口会收缩。

FDE不是一个永恒的角色。它是一个窗口期的角色。但窗口期内的卡位，决定了谁拥有工作流的定义权。

Gartner分析师Alex Coqueiro预测，到2028年，70%的企业将被迫放弃由FDE主导的AI项目。原因是高成本和内部能力不足。他给了一个判断标准：“如果FDE在连续部署中的投入保持不变，这就是一个信号：这段合作产生的是依赖，而非能力。”

这个标准跟我们前面说的试金石是一回事：第10个客户跟第1个客户花的精力一样多吗？如果是，飞轮没在转，你做的是咨询。

70%被放弃，也意味着30%活下来了。活下来的那些，会是真正用FDE方法论建起了平台飞轮的公司。它们在窗口期内卡住了位，拥有了工作流的定义权。

Sequoia的Julien Bek给出了一个终局判断：

> "The next $1T company will be a software company masquerading as a services firm."

下一个万亿美元公司，将是一家伪装成服务公司的软件公司。

这句话精确地描述了FDE模式的终局形态：从外面看，它在做服务（嵌入客户、解决问题、交付结果）；从里面看，它在做产品（每一次服务都让平台更强）。当平台足够强大、用户可以自己跑起来的那一天，FDE作为角色会消失。但FDE作为方法论留下了一个东西：一个被无数次客户部署打磨过的、真正好用的平台。

## 写在最后

过去半年对FDE的研究让我有一个很深的感触：市场上的讨论之所以混乱，不是因为FDE是个模糊的概念，而是因为太多人把不同的东西装进了同一个词里。

FDE的定义是清晰的：**有平台、嵌入客户、产品发现、产物回流。** 满足这四条的，不管你叫它什么名字，都在做FDE。不满足的，不管你title写什么，都不是。

那些说“FDE不过是consulting”的人，没说错。他们看到的就是那种。问题不在于他们的判断，在于他们把所有叫FDE的东西都当成了同一种东西。

Marc Andrusko说过一句话，值得所有想学Palantir的公司记住：

> "Palantir should be seen as an inspiration, rather than a rule or playbook."

Palantir是启发，不是可以照抄的手册。它的FDE方法论可以学，但它同时做到的四件事——嵌入式工程、集成平台、高接触GTM、按结果定价——不需要你全盘复制。把四层混在一起当作一个东西来模仿，就是大部分startup踩坑的原因。

如果你正在考虑是不是要用FDE，或者是不是要加入一家FDE公司，我的建议是：先问自己五个问题。

**第一，给我看你的平台边界在哪里。共享产品止于何处？定制从哪里开始？**

**第二，走一遍部署时间线。从签约到生产环境要多少engineer-months？**

**第三，第三年的利润率是什么样的？成熟客户的FDE投入是否在下降？**

**第四，如果明年签50个客户，什么会先崩？**

**第五，你如何决定不做定制？拒绝客户需求的能力，是产品公司和服务公司的分水岭。**

这五个问题比任何定义都更实用。如果答不上来，大概率不是在做FDE。

FDE是个好东西。但好东西最怕被滥用。当一个策略变得足够性感、足以被奉为“标准打法”时，总是危险的信号。

![最近半年一直在关注 Palantir 的 FDE 模式 — 用户配图 5]({{ site.baseurl }}/assets/images/uploads/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/user-05.webp)



![最近半年一直在关注 Palantir 的 FDE 模式 — 用户配图 6]({{ site.baseurl }}/assets/images/uploads/zui-jin-ban-nian-yi-zhi-zai-guan-zhu-palantir-de-fde-mo-shi/user-06.webp)



做FDE，先做平台。或者至少，做FDE之前，先想清楚你的平台在哪里。
