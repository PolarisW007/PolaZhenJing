# DeepSeek 论文数据新闻资料包

这是一份围绕 DeepSeek 近两年 27 篇论文/技术报告整理的数据新闻资料包。它包含文章中使用的 6 张正式图、支撑这些图的最终 CSV 数据、原始抓取资料、清洗结果和 Python 脚本。

这套资料包的核心价值不是“成品图”，而是把一篇数据新闻背后的工作流打开：如何从论文署名出发，清洗作者、拆分角色、统计技术方向、计算共著关系，并最终生成可复核的信息图。

## 适合谁看

- 想复核文章数据口径的读者。
- 想学习“0 代码基础 + Agent 辅助做数据新闻”的作者、编辑、研究员。
- 想用类似方法分析其他 AI 公司、实验室或开源团队的人。

## 目录结构

```text
deepseek_papers_open/
  README.md                  # 你正在看的快速导览
  TUTORIAL.md                # 从原始数据到图表的复现教程
  requirements.txt           # Python 依赖
  assets/                    # Logo、字体等视觉资源
  raw/                       # HF API JSON、HTML、PDF、角色名单片段
  output/                    # 核心清洗表和基础统计表
  figures/                   # 文章最终使用的 6 张图及其作图数据
  scripts/                   # 数据清洗和绘图脚本
  templates/                 # 视觉模板说明
```

## 文章使用的 6 张图

`figures/` 只保留文章正式使用的图片和直接支撑它们的 CSV。旧版图、探索图和测试表已清理。

| 图 | PNG | 直接数据 |
|---|---|---|
| 论文时间线与作者规模 | `figures/timeline/fig2_author_count_timeline_card_v9_base_model.png` | `figures/timeline/fig2_data_used_v9_base_model.csv` |
| Top25 高频研发作者 | `figures/author_frequency/fig3_high_frequency_research_authors_v12.png` | `figures/author_frequency/fig3_high_frequency_research_authors_top25_plot_data_v11.csv` |
| 研发作者跨方向结构 | `figures/author_direction_span/researcher_cross_direction_overview_v3_card_style.png` | `figures/author_direction_span/research_author_direction_profile.csv` 等 |
| 全体研发作者合作网络 | `figures/coauthor_network/old for all&Top50/ALL R&E/fig4_all_author_network_formal_v17.png` | `figures/coauthor_network/old for all&Top50/ALL R&E/fig4_all_author_communities_formal_v17.csv` |
| 研发矩阵网络 | `figures/matrix_network/fig4_deepseek_research_matrix_network_v1_hub_labels.png` | `figures/matrix_network/fig4_deepseek_research_matrix_network_v1_hub_labels_nodes.csv` |
| 技术模块演进 | `figures/technical_synthesis/fig5_v4_technical_synthesis_river_v1.png` | `figures/technical_synthesis/fig5_v4_technical_synthesis_river_v1_nodes.csv` |

每张图都同时保留 PNG 和 SVG。PNG 适合直接放文章，SVG 适合进一步编辑。

## 核心数据表

`output/` 中是最重要的清洗结果：

- `papers_clean.csv`：27 篇论文/报告主表，包含发布时间、主题、基座模型阶段等。
- `paper_authors_source_raw.csv`：原始作者表，保留抓取和抽取阶段的原始署名。
- `paper_authors_clean.csv`：清洗后的作者表，剔除团队名、规范部分姓名。
- `main_model_authors_with_roles.csv`：基座模型报告作者角色拆分表。
- `main_model_role_summary.csv`：V2/V3/V3.2/V4 的 Research & Engineering、Data Annotation、Business & Compliance 等角色统计。
- `name_canonicalization_map.csv`：姓名规范化映射。
- `data_quality_notes.csv`：清洗备注和已知问题。

## 最重要的口径

1. **409 人不是 DeepSeek 研究员人数。**  
   409 是 27 篇论文/报告的总去重署名作者，包含 DeepSeek 团队、外部合作作者，以及部分非研发角色。

2. **人才相关分析使用“研发作者池”。**  
   V2/V3/V3.2/V4 只取 Research & Engineering 名单；其他未拆角色论文使用原始署名作者并剔除团队名。当前研发作者池为 328 人。

3. **V4 的 317 和 269 不能混用。**  
   317 是 V4 PDF 总署名去重人数；269 是 V4 Research & Engineering 去重人数。图1讲署名规模用 317，人才网络分析用 R&E 口径。

4. **合作网络不是组织架构图。**  
   网络边来自论文共同署名，聚类来自算法识别，不代表真实团队、贡献大小、作者排序或汇报关系。

5. **跨方向不是岗位变化。**  
   跨方向只表示作者参与论文覆盖多个粗技术方向，不等于个人岗位或职责发生变化。

## 如何复现

先安装依赖：

```powershell
pip install -r requirements.txt
```

再按 `TUTORIAL.md` 的步骤运行脚本。最核心顺序是：

```powershell
python scripts/deepseek_clean_data.py
python scripts/deepseek_build_main_model_roles.py
python scripts/deepseek_make_figures_matplotlib.py
python scripts/deepseek_make_fig3_highfreq_authors.py
python scripts/deepseek_make_research_author_cross_direction_page.py
python scripts/deepseek_make_researcher_coauthor_demo.py
python scripts/deepseek_make_v4_technical_synthesis_river.py
```

脚本已经改成相对路径，会默认读取当前资料包里的 `raw/ output/ figures/ assets/`。

## 版权和使用提醒

- 本资料包用于学习、复核和方法分享。
- `raw/` 中如包含论文 PDF，建议仅作个人复核使用；公开二次分发时可改为保留来源链接和抽取片段。
- 使用图表或数据时，请保留数据来源和口径说明。

## Notice：使用前请先看

1. **这不是 DeepSeek 官方数据包。**  
   本资料包由公开论文、Hugging Face Papers 页面/API 返回结果、DeepSeek-V4 PDF 以及人工清洗表整理而成，仅用于数据新闻复核和方法分享。

2. **`raw/` 里保存的是当时抓取/整理后的原始资料快照。**  
   包括 Hugging Face Papers API 返回的 `hf_api_*.json`、部分 ar5iv HTML、论文 PDF 以及从大报告中抽取出的角色名单片段。  
   也就是说，本资料包的复现流程默认从这些已经保存好的 raw data 开始，而不是每次都重新联网抓取。

3. **关于 Hugging Face API 抓取。**  
   当时的起点是用户提供的 DeepSeek HF Papers 链接：`https://huggingface.co/deepseek-ai/papers`。后续通过 Hugging Face Papers 页面/API 获取论文元数据和作者信息，并保存为 `raw/hf_api_*.json`。  
   由于当前包已经保留了这些 JSON 快照，读者复现清洗和作图时不需要重新调用 API。若要更新到未来新论文，需要自行重新访问 Hugging Face Papers 页面或相关 API，并按现有 JSON 格式补入 `raw/`。

4. **论文 PDF 不一定适合公开二次分发。**  
   PDF 在本项目中主要用于复核作者和角色名单。若你准备公开转发资料包，建议优先保留 API JSON、角色片段、清洗表和脚本；论文原文请以 Hugging Face、arXiv 或 DeepSeek 官方来源为准。

5. **不要把论文署名统计误读为真实组织结构。**  
   作者数、Top 作者、跨方向统计、合作网络都来自论文署名和清洗规则，不代表真实员工总数、贡献大小、作者排序、部门归属或汇报关系。

6. **核心口径可以复核，也可以改。**  
   这套资料包开放的是一种工作流：先定义口径，再清洗数据，再生成图表。如果你不同意某个口径，可以修改脚本或 CSV 重新计算，但请在引用结果时说明自己的口径。

7. **不一定只能用 Codex。**  
   本项目的脚本和数据都是普通文件：CSV、JSON、Python、PNG、SVG，并没有依赖 Codex 私有接口。理论上，只要你的 Agent 工具能够读取本地文件、编辑脚本并运行 Python 命令，也可以用 Claude Code、OpenClaw 或其他类似工具复现和修改。  
   需要说明的是，本项目主要在 Codex 中完成；Claude Code、OpenClaw 等工具尚未逐项实测，因此更准确的说法是“原则上兼容”，而不是“已完整测试支持”。
