# 甲子光年竖版信息图模板

本模板以 `fig2_author_count_timeline_card_v7.png` 为基准。后续 DeepSeek 论文数据新闻相关图表，优先沿用这套视觉结构，除非某张图的表达方式明显不适合。

## 基础规格

- 画布：竖版，约 `8.35 x 11.8 inch`，`300dpi` 导出 PNG，另存 SVG。
- 背景：白色。
- 版心：整体偏左，左边距约 `0.044`，右边距约 `0.048`。
- 视觉气质：信息图 / 微信正文配图，不做海报化大装饰，不堆叠卡片。

## 字体

- 字体优先级：Noto Sans CJK SC / Source Han Sans SC / Microsoft YaHei / PingFang SC / HarmonyOS Sans SC / SimHei。
- 主标题：现代中文无衬线 Bold，约 `26pt`。
- 副标题：约 `15.2pt`，深灰。
- 区块标题：约 `16pt`，加粗。
- 主题卡片数字：约 `22pt`，加粗；“篇”约 `9.5pt`。
- 主图模型名称：约 `12pt`。
- 条尾作者数：约 `11pt`。
- 页脚：约 `8.7pt`，颜色约 `#555555`。

## 配色

- 主紫：`#6F35B6`。
- 文字黑：`#15151A`。
- 正文灰：`#2F2F36`。
- 页脚灰：`#555555`。
- 分割线：`#C8C5D1`。
- 半年分隔线：`#E6E1EE`。
- 半年括号线：`#ECE5F4`。

主题色沿用当前口径：

- 系统/效率：`#E45CC8`
- 主线模型：`#6F35B6`
- 数学/证明：`#2F9B72`
- 多模态：`#E08C31`
- 代码：`#2F6FB3`
- OCR：`#8A8798`
- 推理/RL：`#9C67D9`

## 结构

1. 顶部：左侧紫色竖线 + 一行主标题 + 两行副标题。
2. 主题分布：固定大小卡片，7个方向等宽排列；小圆点只做颜色提示，不抢数字信息。
3. 主图区：标题左对齐；右侧保留必要图例，图例不加外框。
4. 时间分组：左侧竖向“早期-最新”箭头；半年标签使用 `2024 H1`、`2024 H2`、`2025 H1`、`2025 H2`、`2026 H1 至今`。
5. 主图标签：每篇论文名前保留对应主题色小圆点；论文名左对齐；条尾数字略小于论文名。
6. 页脚：分割线以下四行左对齐；右下放甲子光年 logo，logo 不超过页脚分割线。

## 页脚固定口径

- 数据来源：Hugging Face Papers API、DeepSeek-V4 PDF
- 口径：同篇作者去重，剔除 DeepSeek-AI 等团队名，补齐 HF API 漏掉的4个作者
- 备注：V4 PDF 总名单317人，其中 Research & Engineering 去重后269人；本图使用269人作图
- 制图：甲子光年

## 输出命名

- 不覆盖旧图。
- 新图使用递增版本号，例如 `fig3_xxx_v1.png/svg`、`fig4_xxx_v1.png/svg`。
- 如果只是在同一张图上微调，使用 `_v2`、`_v3` 递增。

## 当前基准图

- PNG：`C:\Users\Esthe\Documents\New project\data\deepseek_papers\figures\fig2_author_count_timeline_card_v7.png`
- SVG：`C:\Users\Esthe\Documents\New project\data\deepseek_papers\figures\fig2_author_count_timeline_card_v7.svg`
