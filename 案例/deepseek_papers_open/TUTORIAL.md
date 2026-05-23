# Tutorial：0 代码基础复现 DeepSeek 论文数据新闻

这份教程面向不会写 Python、但想理解和复现这篇数据新闻的人。你不需要从零写代码，只需要知道每一步在做什么，然后按顺序运行脚本。

如果你会用 Agent 工具，也可以把每一步当作提示词模板：让 Agent 解释脚本、修改图表、调整口径，或者迁移到其他公司/实验室的数据。

## 0. 这套流程在做什么

我们从 DeepSeek 近两年 27 篇论文/技术报告出发，完成了 6 类分析：

1. 论文发布时间线和每篇论文作者规模。
2. Top25 高频研发作者。
3. 研发作者跨技术方向参与情况。
4. 全体研发作者合作网络。
5. 研发矩阵网络。
6. V4 相关技术模块演进。

最终图在 `figures/` 目录中，支撑图的数据也放在同一子目录下。

## 1. 安装环境

推荐使用 Anaconda Prompt、PowerShell 或 VS Code 终端。

进入资料包目录：

```powershell
cd "C:\你的路径\deepseek_papers_open"
```

安装依赖：

```powershell
pip install -r requirements.txt
```

如果你已经安装了 Anaconda、pandas、matplotlib、networkx，大概率只需要补装：

```powershell
pip install pypdf
```

## 2. 认识原始数据

`raw/` 里主要有三类东西：

- `hf_api_*.json`：Hugging Face Papers API 返回的论文元数据。
- `ar5iv_*.html`：部分论文的 HTML 页面。
- `main_model_role_snippets/*.txt`：从 V2/V3/V3.2/V4/V4 PDF 中抽出的角色名单片段。

注意：论文 PDF 不一定适合公开二次分发。如果要给读者发网盘包，建议强调这些材料仅供复核，也可以改成只保留来源链接和角色片段。

## 3. 第一步：清洗论文和作者基础表

运行：

```powershell
python scripts/deepseek_clean_data.py
```

它会生成/更新：

- `output/papers_clean.csv`
- `output/paper_authors_source_raw.csv`
- `output/paper_authors_clean.csv`
- `output/name_canonicalization_map.csv`
- `output/data_quality_notes.csv`

这一步主要做：

- 汇总 27 篇论文/报告。
- 抽取作者署名。
- 剔除 `DeepSeek-AI` 等团队名。
- 统一部分作者姓名写法。
- 保存原始作者表和清洗作者表。

重要提醒：这一步得到的是“论文署名作者”，不是“DeepSeek 员工名单”。

## 4. 第二步：拆分基座模型报告角色

运行：

```powershell
python scripts/deepseek_build_main_model_roles.py
```

它会生成/更新：

- `output/main_model_authors_with_roles.csv`
- `output/main_model_author_roles_long.csv`
- `output/main_model_role_summary.csv`

这一步用来解决一个关键问题：大报告里的几百个署名作者并不全是同一种角色。

当前重要数字：

| 报告 | 总署名去重人数 | Research & Engineering |
|---|---:|---:|
| DeepSeek LLM | 86 | 未拆角色 |
| DeepSeek-V2 | 156 | 107 |
| DeepSeek-V3 | 197 | 150 |
| DeepSeek-V3.2 | 262 | 211 |
| DeepSeek-V4 | 317 | 269 |

图1使用总署名人数；高频作者、跨方向和网络图使用 R&E 口径。

## 5. 第三步：生成图1，论文时间线

运行：

```powershell
python scripts/deepseek_make_figures_matplotlib.py
```

正式图：

- `figures/timeline/fig2_author_count_timeline_card_v9_base_model.png`
- `figures/timeline/fig2_author_count_timeline_card_v9_base_model.svg`

正式数据：

- `figures/timeline/fig2_data_used_v9_base_model.csv`

这张图回答：DeepSeek 两年 27 篇论文发了什么、什么时候发、每篇署名规模多大。

口径：每篇论文/技术报告的署名去重人数。V4 使用 317，而不是 R&E 的 269。

## 6. 第四步：生成图2，Top25 高频研发作者

运行：

```powershell
python scripts/deepseek_make_fig3_highfreq_authors.py
```

正式图：

- `figures/author_frequency/fig3_high_frequency_research_authors_v12.png`
- `figures/author_frequency/fig3_high_frequency_research_authors_v12.svg`

正式数据：

- `figures/author_frequency/fig3_high_frequency_research_authors_top25_plot_data_v11.csv`
- `figures/author_frequency/fig3_high_frequency_research_authors_all_ge4_data_v11.csv`
- `figures/author_frequency/fig3_research_author_pool_v11.csv`

这张图回答：哪些研发作者反复出现在论文里，覆盖了哪些技术方向。

口径：

- V2/V3/V3.2/V4 使用 Research & Engineering 名单。
- 其他未拆角色论文使用原始署名作者并剔除团队名。
- 参与论文数不代表贡献大小或作者排序。

## 7. 第五步：生成图3，研发作者跨方向结构

运行：

```powershell
python scripts/deepseek_make_research_author_cross_direction_page.py
```

正式图：

- `figures/author_direction_span/researcher_cross_direction_overview_v3_card_style.png`
- `figures/author_direction_span/researcher_cross_direction_overview_v3_card_style.svg`

正式数据：

- `figures/author_direction_span/research_author_direction_profile.csv`
- `figures/author_direction_span/research_author_direction_pairs_top.csv`
- `figures/author_direction_span/research_author_direction_participation_counts.csv`

这张图回答：研发作者是不是只在单一方向工作，还是会跨多个技术方向移动。

注意：

- “各方向参与作者数”表示至少参与过该方向 1 篇论文的人数。
- 各方向人数相加大于 328 是正常现象，因为同一作者可以覆盖多个方向。
- 跨方向不等于岗位变化。

## 8. 第六步：生成图4/图5，合作网络

全作者合作网络正式图：

- `figures/coauthor_network/old for all&Top50/ALL R&E/fig4_all_author_network_formal_v17.png`
- `figures/coauthor_network/old for all&Top50/ALL R&E/fig4_all_author_network_formal_v17.svg`

矩阵网络正式图：

- `figures/matrix_network/fig4_deepseek_research_matrix_network_v1_hub_labels.png`
- `figures/matrix_network/fig4_deepseek_research_matrix_network_v1_hub_labels.svg`

对应脚本：

```powershell
python scripts/deepseek_make_fig4_all_author_network_explore.py
python scripts/deepseek_make_researcher_coauthor_demo.py
```

共著权重使用：

```text
w(i,j)=Σ 1/(N_p-1)
```

其中 `N_p` 是论文 `p` 的去重作者数。这个公式用来降低百人级报告对共著关系的放大。

注意：

- 节点和边来自共同署名。
- 算法聚类不代表真实部门。
- 线越粗只表示论文署名层面的共著关系更强，不代表贡献大小或上下级关系。

## 9. 第七步：生成图6，技术模块演进

运行：

```powershell
python scripts/deepseek_make_v4_technical_synthesis_river.py
```

正式图：

- `figures/technical_synthesis/fig5_v4_technical_synthesis_river_v1.png`
- `figures/technical_synthesis/fig5_v4_technical_synthesis_river_v1.svg`

正式数据：

- `figures/technical_synthesis/fig5_v4_technical_synthesis_river_v1_nodes.csv`
- `figures/technical_synthesis/deepseek_tech_evolution_modules_latest.csv`

这张图回答：V4 不是突然出现的，它和前序论文中的 MoE、MLA、GRPO、mHC、OCR 等模块存在可追溯的技术路线关系。

注意：这不是严格代码复用率，只能表述为“论文中可追溯的技术模块/路线演进”。

## 10. 如果你想重新改图

优先改这几类内容：

- 标题、副标题、脚注：直接在对应绘图脚本里搜索中文。
- 配色：搜索 `COLORS`。
- 字体：看脚本顶部的 `NotoSansSC-Regular.ttf` 和 `NotoSansSC-Bold.ttf`。
- 数据口径：优先改 CSV 或清洗函数，不建议只在图上手动改数字。

改完之后重新运行对应脚本，PNG 和 SVG 会重新导出。

## 11. 常见错误

1. **把 409 人写成 DeepSeek 研究员人数。**  
   错。409 是总去重署名作者，包含外部合作和非研发角色。

2. **把 V4 的 317 和 269 混用。**  
   317 是总署名；269 是 Research & Engineering。

3. **把合作网络写成组织架构。**  
   错。合作网络只来自论文共同署名。

4. **把高频作者写成贡献排名。**  
   错。参与论文数只代表署名出现次数。

5. **把院校标签写成当前单位。**  
   错。院校标签多数来自公开教育背景，不代表当前雇主。

## 12. 给 0 代码基础读者的建议

你不需要一开始理解所有代码。更好的方式是：

1. 先打开 `figures/` 看最终图。
2. 再打开同目录下的 CSV，看图里的数字从哪里来。
3. 再按本教程运行一次脚本。
4. 最后让 Agent 帮你解释脚本里不懂的函数。

人负责判断问题、核对口径和决定表达；Agent 负责写脚本、跑数据和反复改图。这就是这次“数据厨房”真正值得复用的地方。

