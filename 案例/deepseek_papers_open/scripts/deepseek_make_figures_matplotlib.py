from __future__ import annotations

import math
from datetime import timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures" / "timeline"
ASSETS = ROOT / "assets"
FONT_DIR = ASSETS / "fonts"
DATA = FIG / "fig2_data_used.csv"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
FIG.mkdir(parents=True, exist_ok=True)


COLORS = {
    # Light-purple report palette with a few topic accents for readability.
    "主模型": "#6F35B6",
    "代码": "#2F6FB3",
    "数学/证明": "#2F9B72",
    "多模态": "#E08C31",
    "OCR": "#8A8798",
    "系统/效率": "#E45CC8",
    "推理/RL": "#9C67D9",
}

LABELS = {
    "DeepSeek LLM",
    "DeepSeek-V2",
    "DeepSeek-V3 Technical Report",
    "DeepSeek-R1",
    "DeepSeek-V3.2",
    "DeepSeek-V4",
    "DeepSeek-Coder-V2",
    "DeepSeek-VL2",
}

MAIN_POINT_LABELS = {
    "DeepSeek LLM": "DeepSeek LLM（86人）",
    "DeepSeek-V2": "DeepSeek-V2（156人）",
    "DeepSeek-V3 Technical Report": "DeepSeek-V3（197人）",
    "DeepSeek-R1": "DeepSeek-R1（197人）",
    "DeepSeek-V3.2": "DeepSeek-V3.2（262人）",
    "DeepSeek-V4": "DeepSeek-V4（317人）",
}

AXIS_LABEL_THRESHOLD = 30

SHORT_AXIS_LABELS = {
    "DeepSeek LLM": "LLM（86）",
    "DeepSeek-V2": "V2（156）",
    "DeepSeek-Coder-V2": "Coder-V2（39）",
    "DeepSeek-VL2": "VL2（27）",
    "DeepSeek-V3 Technical Report": "V3（197）",
    "DeepSeek-R1": "R1（197）",
    "DeepSeek-V3.2": "V3.2（262）",
    "DeepSeek-V4": "V4（317）",
}


def configure_font() -> None:
    candidates = [
        NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font = font_manager.FontProperties(fname=str(path)).get_name()
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 11


def font_prop(kind: str = "sans", size: float | None = None, weight: str | None = None):
    if kind == "serif":
        path = Path(r"C:\Windows\Fonts\NotoSerifSC-VF.ttf")
        if not path.exists():
            path = Path(r"C:\Windows\Fonts\simsun.ttc")
    else:
        candidates = [
            NOTO_SC_BOLD if weight == "bold" else NOTO_SC_REGULAR,
            NOTO_SC_REGULAR,
            Path(r"C:\Windows\Fonts\msyhbd.ttc") if weight == "bold" else Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
            Path(r"C:\Windows\Fonts\PingFang SC.ttf"),
            Path(r"C:\Windows\Fonts\HarmonyOS_Sans_SC_Regular.ttf"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
        ]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[-1])
    kwargs = {}
    if size is not None:
        kwargs["size"] = size
    if weight is not None:
        kwargs["weight"] = weight
    if path.exists():
        return font_manager.FontProperties(fname=str(path), **kwargs)
    return font_manager.FontProperties(**kwargs)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["year_month"] + "-01")
    # 图1主图统一展示每篇论文/技术报告的署名去重人数；
    # V4 的 Research & Engineering 口径仅放在页脚备注中。
    df["author_count_for_chart"] = df["author_count"]
    df = df.sort_values(["date", "short_title"]).reset_index(drop=True)

    # Small horizontal jitter for papers published in the same month.
    df["plot_date"] = df["date"]
    for _, idxs in df.groupby("year_month").groups.items():
        idxs = list(idxs)
        if len(idxs) == 1:
            continue
        offsets = [(i - (len(idxs) - 1) / 2) * 4 for i in range(len(idxs))]
        for idx, offset in zip(idxs, offsets):
            df.loc[idx, "plot_date"] = df.loc[idx, "date"] + timedelta(days=float(offset))
    return df


def add_legend(ax) -> None:
    handles = []
    labels = []
    for topic, color in COLORS.items():
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                linestyle="",
                markersize=7,
                markerfacecolor=color,
        markeredgecolor="white",
            )
        )
        labels.append(topic)
    ax.legend(
        handles,
        labels,
        loc="upper left",
        bbox_to_anchor=(0, 1.035),
        ncol=7,
        frameon=False,
        fontsize=10,
        handletextpad=0.4,
        columnspacing=1.1,
    )


def add_reader_header(fig, title: str, lines: list[str]) -> None:
    fig.text(0.065, 0.965, title, fontsize=22, weight="bold", color="#121212")
    y = 0.922
    for line in lines:
        fig.text(0.065, y, line, fontsize=12.2, color="#555")
        y -= 0.030


def add_reader_note(fig) -> None:
    fig.text(
        0.065,
        0.060,
        "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF。口径：每篇论文按作者名去重，剔除 DeepSeek-AI 等团队名，补齐 HF API 漏掉的 4 个作者。",
        fontsize=9.8,
        color="#666",
    )
    fig.text(
        0.065,
        0.038,
        "V4 备注：PDF 总名单为 317 人，其中 Research & Engineering 去重后 269 人；本图为和主模型研发团队可比，使用 269 人作图。",
        fontsize=9.8,
        color="#666",
    )
    fig.text(0.97, 0.038, "制图：甲子光年", ha="right", fontsize=10.2, color="#555", weight="bold")


def scatter(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(14, 8), dpi=180)
    fig.patch.set_facecolor("#fffdf9")
    ax.set_facecolor("#fffdf9")

    main = df[df["main_model_stage"].notna()]
    ax.plot(
        main["plot_date"],
        main["author_count_for_chart"],
        color="#c23b3b",
        linewidth=2.2,
        alpha=0.45,
        zorder=1,
    )

    for _, row in df.iterrows():
        is_main = pd.notna(row["main_model_stage"])
        ax.scatter(
            row["plot_date"],
            row["author_count_for_chart"],
            s=78 if is_main else 48,
            color=COLORS[row["coarse_topic"]],
            edgecolor="#202020" if is_main else "white",
            linewidth=1.2 if is_main else 0.8,
            zorder=3,
        )

    label_offsets = {
        "DeepSeek LLM": (8, 10),
        "DeepSeek-V2": (8, 12),
        "DeepSeek-V3 Technical Report": (-20, 16),
        "DeepSeek-R1": (8, -18),
        "DeepSeek-V3.2": (-30, 16),
        "DeepSeek-V4": (-110, -20),
    }
    for _, row in df[df["short_title"].isin(MAIN_POINT_LABELS)].iterrows():
        label = MAIN_POINT_LABELS[row["short_title"]]
        dx, dy = label_offsets.get(row["short_title"], (8, 8))
        ax.annotate(
            label,
            (row["plot_date"], row["author_count_for_chart"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=9,
            weight="bold",
            color="#222",
        )

    # Label the larger papers under the x-axis so the reader does not need to
    # hover or cross-check the data table.
    for _, row in df[df["author_count_for_chart"] >= AXIS_LABEL_THRESHOLD].iterrows():
        label = SHORT_AXIS_LABELS.get(
            row["short_title"],
            f"{row['short_title']}（{int(row['author_count_for_chart'])}）",
        )
        ax.annotate(
            label,
            xy=(row["plot_date"], 0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -44),
            textcoords="offset points",
            ha="right",
            va="top",
            rotation=45,
            fontsize=8.5,
            color="#333",
        )

    add_reader_header(
        fig,
        "DeepSeek 论文作者数变化：小队论文与大兵团报告并存",
        [
            "横轴是论文发布时间，纵轴是每篇论文的去重作者数，颜色代表粗方向。",
            "红色折线只连接主模型系列，用来观察 LLM、V2、V3、R1、V3.2、V4 的团队规模变化。",
            f"横轴下方额外标注作者数 ≥{AXIS_LABEL_THRESHOLD} 人的论文；V4 总名单 317 人，本图按研发工程团队 269 人计。",
        ],
    )
    add_legend(ax)
    ax.set_ylabel("每篇论文的去重作者数（人）", fontsize=11)
    ax.set_xlabel("论文发布时间", fontsize=10.5, labelpad=50)
    ax.set_ylim(0, 340)
    ax.set_yticks(range(0, 341, 50))
    ax.grid(axis="y", color="#dedede", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", labelrotation=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#777")
    ax.spines["bottom"].set_color("#777")
    add_reader_note(fig)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.28)
    fig.savefig(FIG / "fig2_author_count_scatter.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_scatter_mpl.svg", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_scatter_v2.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_scatter_v2.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def bar(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(16, 9.8), dpi=200)
    fig.patch.set_facecolor("#fffdf9")
    ax.set_facecolor("#fffdf9")

    x = range(len(df))
    colors = [COLORS[t] for t in df["coarse_topic"]]
    edges = ["#222" if pd.notna(v) else "none" for v in df["main_model_stage"]]
    widths = [1.2 if pd.notna(v) else 0 for v in df["main_model_stage"]]
    bars = ax.bar(x, df["author_count_for_chart"], color=colors, edgecolor=edges, linewidth=widths, width=0.72)

    for bar_obj, (_, row) in zip(bars, df.iterrows()):
        value = int(row["author_count_for_chart"])
        if value >= 30 or row["short_title"] in LABELS:
            ax.text(
                bar_obj.get_x() + bar_obj.get_width() / 2,
                value + 5,
                str(value),
                ha="center",
                va="bottom",
                fontsize=10.5,
                color="#333",
            )

    labels = (
        df["short_title"]
        .str.replace("DeepSeek-", "DS-", regex=False)
        .str.replace(" Technical Report", "", regex=False)
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=10.2)
    ax.set_ylabel("每篇论文的去重作者数（人）", fontsize=13)
    ax.set_ylim(0, 340)
    ax.set_yticks(range(0, 341, 50))
    ax.grid(False)
    ax.tick_params(axis="y", labelsize=11.5, colors="#222", length=4, width=0.9)
    ax.tick_params(axis="x", labelsize=10.2, colors="#111", length=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#777")
    ax.spines["bottom"].set_color("#777")
    add_reader_header(
        fig,
        "27 篇 DeepSeek 论文的作者规模",
        [
            "每根柱代表一篇论文或技术报告，柱高是该论文的去重作者数，颜色代表粗方向。",
            "上方气泡按篇数从大到小排列，显示 27 篇论文中各方向的分布。",
            "黑色描边表示主模型比较链：LLM、V2、V3、R1、V3.2、V4；V4 柱高使用 Research & Engineering 的 269 人。",
        ],
    )

    bubble_ax = fig.add_axes([0.08, 0.690, 0.89, 0.105])
    bubble_ax.set_facecolor("#fffdf9")
    topic_counts = (
        df["coarse_topic"]
        .value_counts()
        .rename_axis("topic")
        .reset_index(name="count")
    )
    topic_counts["priority"] = topic_counts["topic"].map({topic: i for i, topic in enumerate(COLORS)})
    topic_counts = topic_counts.sort_values(["count", "priority"], ascending=[False, True])
    xs = list(range(len(topic_counts)))
    sizes = [360 + count * 170 for count in topic_counts["count"]]
    bubble_ax.scatter(
        xs,
        [0] * len(xs),
        s=sizes,
        c=[COLORS[t] for t in topic_counts["topic"]],
        edgecolors="white",
        linewidths=1.5,
        zorder=2,
    )
    for x_pos, (_, item) in zip(xs, topic_counts.iterrows()):
        bubble_ax.text(x_pos, 0.25, f"{item['topic']}", ha="center", va="bottom", fontsize=11, color="#222")
        bubble_ax.text(x_pos, -0.30, f"{int(item['count'])}篇", ha="center", va="top", fontsize=10.5, color="#555")
    bubble_ax.text(-0.72, 0, "方向分布", ha="right", va="center", fontsize=12, color="#555", weight="bold")
    bubble_ax.set_xlim(-0.95, len(xs) - 0.45)
    bubble_ax.set_ylim(-0.55, 0.55)
    bubble_ax.axis("off")

    add_reader_note(fig)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.625, bottom=0.31)
    fig.savefig(FIG / "fig2_author_count_bar.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_mpl.svg", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_v2.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_v2.svg", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_bubbles.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_bubbles.svg", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_bubbles_v3.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_bar_bubbles_v3.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def mobile_bar(df: pd.DataFrame) -> None:
    """WeChat-first portrait version.

    The desktop-wide chart becomes tiny when WeChat scales it to phone width.
    This version is designed at 1080 px wide and uses much larger source-pixel
    text so it remains readable on a mobile screen.
    """

    fig, ax = plt.subplots(figsize=(7.2, 17.6), dpi=150)  # 1080 x 2640 px
    fig.patch.set_facecolor("#fffdf9")
    ax.set_facecolor("#fffdf9")

    display = (
        df["short_title"]
        .str.replace("DeepSeek-", "DS-", regex=False)
        .str.replace(" Technical Report", "", regex=False)
        .str.replace("Generalist Reward Modeling", "Reward Modeling", regex=False)
        .str.replace("Native Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Conditional Memory", "Cond. Memory", regex=False)
        .str.replace("Insights into DeepSeek-V3", "Insights V3", regex=False)
    )

    y = list(range(len(df)))
    colors = [COLORS[t] for t in df["coarse_topic"]]
    edges = ["#222222" if pd.notna(v) else "#fffdf9" for v in df["main_model_stage"]]
    widths = [2.0 if pd.notna(v) else 0.0 for v in df["main_model_stage"]]
    ax.barh(
        y,
        df["author_count_for_chart"],
        color=colors,
        edgecolor=edges,
        linewidth=widths,
        height=0.62,
    )
    ax.invert_yaxis()

    for yi, (_, row) in zip(y, df.iterrows()):
        value = int(row["author_count_for_chart"])
        x = value + 5
        if value < 18:
            x = 22
        ax.text(x, yi, str(value), va="center", ha="left", fontsize=16, color="#2b2b2b")

    ax.set_yticks(y)
    ax.set_yticklabels(display, fontsize=16, color="#111")
    ax.set_xlim(0, 300)
    ax.set_xticks([0, 100, 200, 300])
    ax.tick_params(axis="x", labelsize=15, colors="#555")
    ax.tick_params(axis="y", length=0, pad=7)
    ax.set_xlabel("每篇论文的去重作者数（人）", fontsize=16, labelpad=14)
    ax.grid(False)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#888")

    fig.text(0.07, 0.972, "27 篇 DeepSeek 论文的作者规模", fontsize=28, weight="bold", color="#111")
    fig.text(0.07, 0.946, "每根条代表一篇论文，长度是去重作者数；颜色代表粗方向。", fontsize=18, color="#555")
    fig.text(0.07, 0.924, "黑色描边表示主模型比较链；V4 使用研发工程团队 269 人作图。", fontsize=18, color="#555")

    bubble_ax = fig.add_axes([0.08, 0.805, 0.86, 0.095])
    bubble_ax.set_facecolor("#fffdf9")
    topic_counts = (
        df["coarse_topic"]
        .value_counts()
        .rename_axis("topic")
        .reset_index(name="count")
    )
    topic_counts["priority"] = topic_counts["topic"].map({topic: i for i, topic in enumerate(COLORS)})
    topic_counts = topic_counts.sort_values(["count", "priority"], ascending=[False, True])

    xs = list(range(len(topic_counts)))
    sizes = [520 + int(count) * 190 for count in topic_counts["count"]]
    bubble_ax.scatter(
        xs,
        [0] * len(xs),
        s=sizes,
        c=[COLORS[t] for t in topic_counts["topic"]],
        edgecolors="white",
        linewidths=1.8,
    )
    for x_pos, (_, item) in zip(xs, topic_counts.iterrows()):
        label = str(item["topic"])
        if label == "数学/证明":
            label = "数学"
        if label == "系统/效率":
            label = "系统"
        bubble_ax.text(x_pos, 0.34, label, ha="center", va="bottom", fontsize=14, color="#222")
        bubble_ax.text(x_pos, -0.36, f"{int(item['count'])}篇", ha="center", va="top", fontsize=13, color="#555")
    bubble_ax.text(-0.70, 0, "方向", ha="right", va="center", fontsize=15, color="#555", weight="bold")
    bubble_ax.set_xlim(-0.9, len(xs) - 0.35)
    bubble_ax.set_ylim(-0.60, 0.60)
    bubble_ax.axis("off")

    fig.text(
        0.07,
        0.035,
        "来源：Hugging Face Papers API、DeepSeek-V4 PDF；口径：同篇作者名去重，剔除团队名，补齐 HF API 漏掉的 4 个作者。",
        fontsize=12.5,
        color="#666",
    )
    fig.text(
        0.07,
        0.019,
        "V4：PDF 总名单 317 人，其中 Research & Engineering 去重后 269 人；本图使用 269 人作图。",
        fontsize=12.5,
        color="#666",
    )
    fig.text(0.93, 0.019, "制图：甲子光年", ha="right", fontsize=13, color="#555", weight="bold")

    fig.subplots_adjust(left=0.34, right=0.94, top=0.77, bottom=0.075)
    fig.savefig(FIG / "fig2_author_count_mobile.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_mobile.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def wrap_cn(text: str, max_chars: int) -> str:
    lines = []
    current = ""
    for char in text:
        current += char
        if len(current) >= max_chars and char in "，；。":
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return "\n".join(lines)


def add_watermark(fig) -> None:
    for x in [0.12, 0.32, 0.52, 0.72, 0.92]:
        for y in [0.12, 0.30, 0.48, 0.66, 0.84]:
            fig.text(
                x,
                y,
                "甲子光年",
                ha="center",
                va="center",
                rotation=28,
                fontsize=10,
                color="#6B3AB2",
                alpha=0.045,
            )


def jiazi_style_mobile(df: pd.DataFrame) -> None:
    """Portrait report-style chart following the provided JAZZYEAR reference."""

    fig = plt.figure(figsize=(7.8, 10.37), dpi=150)  # 1170 x 1555 px
    bg = "#F7F7FC"
    purple = "#6F35B6"
    deep_purple = "#563382"
    fig.patch.set_facecolor(bg)
    add_watermark(fig)

    serif_title = font_prop("serif", 25, "bold")
    serif_big = font_prop("serif", 33, "bold")
    sans = font_prop("sans", 11)
    sans_bold = font_prop("sans", 11.5, "bold")

    # Top identity row
    pill = FancyBboxPatch(
        (0.058, 0.948),
        0.245,
        0.028,
        boxstyle="round,pad=0.001,rounding_size=0.015",
        transform=fig.transFigure,
        fill=False,
        linewidth=1.1,
        edgecolor=purple,
    )
    fig.add_artist(pill)
    fig.text(0.084, 0.955, "甲子判断", fontproperties=font_prop("serif", 12.5, "bold"), color=deep_purple)
    fig.text(0.198, 0.955, "|", fontsize=13, color="#B8A7D6")
    fig.text(0.220, 0.955, "2026", fontproperties=font_prop("serif", 12.5, "bold"), color=deep_purple)
    fig.text(0.335, 0.953, "DeepSeek Papers", fontproperties=serif_title, color=deep_purple)
    fig.text(0.874, 0.960, "甲子光年", fontsize=10.5, weight="bold", color="#1E1E1E")
    fig.text(0.875, 0.948, "JIAZI YEAR", fontsize=5.5, color="#1E1E1E", family="serif")
    for i in range(5):
        fig.add_artist(
            Rectangle(
                (0.833 + i * 0.006, 0.958 - i * 0.0015),
                0.0022,
                0.024 - i * 0.002,
                transform=fig.transFigure,
                color="#8A36FF",
                alpha=0.95,
            )
        )

    # Main headline
    fig.add_artist(Rectangle((0.054, 0.835), 0.0045, 0.083, transform=fig.transFigure, color=purple))
    fig.text(
        0.072,
        0.878,
        "DeepSeek论文作者规模：\n从小队论文到百人级报告",
        fontproperties=serif_big,
        color="#050505",
        linespacing=0.95,
        va="center",
    )

    # Summary box
    box = FancyBboxPatch(
        (0.058, 0.726),
        0.884,
        0.088,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#FFFFFF",
        edgecolor="#B991DD",
        linewidth=1.1,
        alpha=0.88,
    )
    fig.add_artist(box)
    summary = (
        "27篇论文/技术报告中，DeepSeek既有3—20人左右的小队论文，也有百人级主模型报告。"
        "作者规模从DeepSeek LLM的86人，扩张到V4研发工程团队269人；"
        "系统/效率、主模型、数学/证明是论文数量最多的方向。"
    )
    fig.text(
        0.073,
        0.772,
        wrap_cn(summary, 35),
        fontproperties=font_prop("serif", 12.3, "bold"),
        color="#111",
        linespacing=1.55,
        va="center",
    )

    fig.text(
        0.058,
        0.689,
        "图1：DeepSeek 27篇论文作者规模与主题分布",
        fontproperties=font_prop("serif", 15.2, "bold"),
        color="#070707",
    )

    # Direction bubbles
    bubble_ax = fig.add_axes([0.08, 0.592, 0.84, 0.080])
    bubble_ax.set_facecolor(bg)
    topic_counts = (
        df["coarse_topic"]
        .value_counts()
        .rename_axis("topic")
        .reset_index(name="count")
    )
    topic_counts["priority"] = topic_counts["topic"].map({topic: i for i, topic in enumerate(COLORS)})
    topic_counts = topic_counts.sort_values(["count", "priority"], ascending=[False, True])
    xs = list(range(len(topic_counts)))
    sizes = [250 + int(count) * 120 for count in topic_counts["count"]]
    bubble_ax.scatter(
        xs,
        [0] * len(xs),
        s=sizes,
        c=[COLORS[t] for t in topic_counts["topic"]],
        edgecolors="white",
        linewidths=1.3,
    )
    for x_pos, (_, item) in zip(xs, topic_counts.iterrows()):
        label = str(item["topic"]).replace("数学/证明", "数学").replace("系统/效率", "系统")
        bubble_ax.text(x_pos, 0.34, label, ha="center", va="bottom", fontsize=10.5, color="#222")
        bubble_ax.text(x_pos, -0.34, f"{int(item['count'])}篇", ha="center", va="top", fontsize=9.5, color="#555")
    bubble_ax.text(-0.70, 0, "方向", ha="right", va="center", fontsize=12.5, color="#555", weight="bold")
    bubble_ax.set_xlim(-0.9, len(xs) - 0.35)
    bubble_ax.set_ylim(-0.62, 0.62)
    bubble_ax.axis("off")

    # Main chart
    ax = fig.add_axes([0.30, 0.135, 0.63, 0.425])
    ax.set_facecolor(bg)
    display = (
        df["short_title"]
        .str.replace("DeepSeek-", "DS-", regex=False)
        .str.replace(" Technical Report", "", regex=False)
        .str.replace("Generalist Reward Modeling", "Reward Modeling", regex=False)
        .str.replace("Native Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Conditional Memory", "Cond. Memory", regex=False)
        .str.replace("Insights into DeepSeek-V3", "Insights V3", regex=False)
    )
    y = list(range(len(df)))
    colors = [COLORS[t] for t in df["coarse_topic"]]
    edges = ["#222222" if pd.notna(v) else bg for v in df["main_model_stage"]]
    widths = [1.4 if pd.notna(v) else 0 for v in df["main_model_stage"]]
    ax.barh(y, df["author_count_for_chart"], color=colors, edgecolor=edges, linewidth=widths, height=0.58)
    ax.invert_yaxis()
    for yi, (_, row) in zip(y, df.iterrows()):
        value = int(row["author_count_for_chart"])
        ax.text(min(value + 4, 286), yi, str(value), va="center", ha="left", fontsize=8.8, color="#262626")
    ax.set_yticks(y)
    ax.set_yticklabels(display, fontsize=8.9, color="#111")
    ax.set_xlim(0, 300)
    ax.set_xticks([0, 100, 200, 300])
    ax.tick_params(axis="x", labelsize=9.5, colors="#333")
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_xlabel("每篇论文的去重作者数（人）", fontsize=11.5, labelpad=8)
    ax.grid(False)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#A0A0A8")
    ax.spines["bottom"].set_linewidth(0.9)

    # Footer
    fig.add_artist(Rectangle((0.058, 0.073), 0.884, 0.0012, transform=fig.transFigure, color="#C2A7E5", alpha=0.95))
    fig.text(
        0.058,
        0.060,
        "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF；口径：同篇作者名去重，剔除DeepSeek-AI等团队名，补齐HF API漏掉的4个作者。",
        fontsize=7.2,
        color="#777",
    )
    fig.text(
        0.058,
        0.045,
        "V4备注：PDF总名单317人，其中Research & Engineering去重后269人；本图使用269人作图。",
        fontsize=7.2,
        color="#777",
    )
    fig.text(0.918, 0.045, "制图：甲子光年", ha="right", fontsize=8, weight="bold", color="#555")

    fig.savefig(FIG / "fig2_author_count_jiazi_style.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_jiazi_style.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def portrait_clean(df: pd.DataFrame) -> None:
    """Portrait chart using the reference image's color mood, without its brand frame."""

    fig = plt.figure(figsize=(7.8, 11.0), dpi=150)  # 1170 x 1650 px
    bg = "#F7F7FC"
    purple = "#7A3DB8"
    fig.patch.set_facecolor(bg)

    title_font = font_prop("sans", 25, "bold")
    text_font = font_prop("sans", 11.5)
    text_bold = font_prop("sans", 11.5, "bold")

    fig.text(
        0.500,
        0.934,
        "DeepSeek 27篇论文的作者规模变化",
        fontproperties=font_prop("sans", 23.0, "bold"),
        color="#4A2778",
        ha="center",
        va="center",
    )

    box = FancyBboxPatch(
        (0.060, 0.822),
        0.880,
        0.072,
        boxstyle="round,pad=0.010,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#FFFFFF",
        edgecolor="#C5A7E6",
        linewidth=1.1,
        alpha=0.88,
    )
    fig.add_artist(box)
    summary = (
        "27篇论文/技术报告中，DeepSeek既有3—20人左右的小队论文，也有百人级主模型报告；\n"
        "主模型作者规模从DeepSeek LLM的86人，"
        "扩张到V4研发工程团队269人。"
    )
    fig.text(
        0.080,
        0.858,
        summary,
        fontproperties=font_prop("sans", 10.8),
        color="#222",
        linespacing=1.65,
        va="center",
    )

    fig.text(
        0.060,
        0.770,
        "主题分布",
        fontproperties=font_prop("sans", 13.5, "bold"),
        color="#333",
    )

    bubble_ax = fig.add_axes([0.085, 0.670, 0.850, 0.086])
    bubble_ax.set_facecolor(bg)
    topic_counts = (
        df["coarse_topic"]
        .value_counts()
        .rename_axis("topic")
        .reset_index(name="count")
    )
    topic_counts["priority"] = topic_counts["topic"].map({topic: i for i, topic in enumerate(COLORS)})
    topic_counts = topic_counts.sort_values(["count", "priority"], ascending=[False, True])
    xs = list(range(len(topic_counts)))
    sizes = [260 + int(count) * 130 for count in topic_counts["count"]]
    bubble_ax.scatter(
        xs,
        [0] * len(xs),
        s=sizes,
        c=[COLORS[t] for t in topic_counts["topic"]],
        edgecolors="white",
        linewidths=1.3,
    )
    for x_pos, (_, item) in zip(xs, topic_counts.iterrows()):
        label = str(item["topic"]).replace("数学/证明", "数学").replace("系统/效率", "系统")
        bubble_ax.text(x_pos, 0.34, label, ha="center", va="bottom", fontsize=10.8, color="#222")
        bubble_ax.text(x_pos, -0.35, f"{int(item['count'])}篇", ha="center", va="top", fontsize=10.0, color="#555")
    bubble_ax.set_xlim(-0.45, len(xs) - 0.55)
    bubble_ax.set_ylim(-0.62, 0.62)
    bubble_ax.axis("off")

    ax = fig.add_axes([0.315, 0.162, 0.610, 0.430])
    ax.set_facecolor(bg)
    display = (
        df["short_title"]
        .str.replace("DeepSeek-", "DS-", regex=False)
        .str.replace(" Technical Report", "", regex=False)
        .str.replace("Generalist Reward Modeling", "Reward Model", regex=False)
        .str.replace("Native Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Conditional Memory", "Cond. Memory", regex=False)
        .str.replace("Insights into DeepSeek-V3", "Insights V3", regex=False)
    )
    y = list(range(len(df)))
    colors = [COLORS[t] for t in df["coarse_topic"]]
    edges = ["#222222" if pd.notna(v) else bg for v in df["main_model_stage"]]
    widths = [1.5 if pd.notna(v) else 0 for v in df["main_model_stage"]]
    ax.barh(y, df["author_count_for_chart"], color=colors, edgecolor=edges, linewidth=widths, height=0.46)
    ax.invert_yaxis()
    for yi, (_, row) in zip(y, df.iterrows()):
        value = int(row["author_count_for_chart"])
        ax.text(min(value + 4, 286), yi, str(value), va="center", ha="left", fontsize=9.7, color="#262626")
    ax.set_yticks(y)
    ax.set_yticklabels(display, fontsize=9.5, color="#111")
    ax.set_xlim(0, 300)
    ax.set_xticks([0, 100, 200, 300])
    ax.tick_params(axis="x", labelsize=9.8, colors="#333")
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_xlabel("每篇论文的去重作者数（人）", fontsize=11.5, labelpad=8)
    ax.grid(False)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#A0A0A8")
    ax.spines["bottom"].set_linewidth(0.9)

    fig.add_artist(Rectangle((0.060, 0.105), 0.880, 0.0011, transform=fig.transFigure, color="#C2A7E5", alpha=0.95))
    fig.text(
        0.060,
        0.088,
        "图注：上方气泡表示27篇论文的粗主题分布，大小和数字均代表篇数；下方条形图按发布时间排列，黑色描边表示主模型比较链。",
        fontsize=8.2,
        color="#777",
    )
    fig.text(
        0.060,
        0.068,
        "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF；口径：同篇作者名去重，剔除DeepSeek-AI等团队名，补齐HF API漏掉的4个作者。",
        fontsize=7.8,
        color="#777",
    )
    fig.text(
        0.060,
        0.049,
        "V4备注：PDF总名单317人，其中Research & Engineering去重后269人；本图使用269人作图。",
        fontsize=7.8,
        color="#777",
    )
    fig.text(0.918, 0.049, "制图：甲子光年", ha="right", fontsize=8.5, weight="bold", color="#555")

    fig.savefig(FIG / "fig2_author_count_portrait_clean.png", facecolor=fig.get_facecolor())
    fig.savefig(FIG / "fig2_author_count_portrait_clean.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def short_topic_label(topic: str) -> str:
    return (
        str(topic)
        .replace("主模型", "基座模型")
        .replace("数学/证明", "数学")
        .replace("系统/效率", "系统")
    )


def short_paper_label(title: str) -> str:
    return (
        str(title)
        .replace("DeepSeek-", "DS-")
        .replace(" Technical Report", "")
    )


def make_display_labels(series: pd.Series) -> pd.Series:
    return (
        series
        .str.replace("DeepSeek-", "DS-", regex=False)
        .str.replace("DeepSeekMoE", "DS-MoE", regex=False)
        .str.replace("DeepSeekMath", "DS-Math", regex=False)
        .str.replace(" Technical Report", "", regex=False)
        .str.replace("Generalist Reward Modeling", "Reward Model", regex=False)
        .str.replace("Native Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Sparse Attention", "Sparse Attn.", regex=False)
        .str.replace("Conditional Memory", "Cond. Memory", regex=False)
        .str.replace("Insights into DeepSeek-V3", "Insights V3", regex=False)
        .str.replace("Insights into DS-V3", "Insights V3", regex=False)
    )


def draw_jiazi_logo(fig, x: float = 0.785, y: float = 0.032, scale: float = 1.0) -> None:
    """Place the provided JAZZYEAR logo image in the footer."""

    if not JIAZI_LOGO.exists():
        return
    logo_ax = fig.add_axes([x, y, 0.152 * scale, 0.055 * scale])
    logo_ax.imshow(plt.imread(JIAZI_LOGO))
    logo_ax.set_axis_off()


def draw_topic_icon(ax, topic: str, x: float, y: float) -> None:
    """Draw simple white vector icons inside topic circles."""

    white = "#FFFFFF"
    lw = 1.7
    z = 5

    if topic == "系统/效率":
        ax.add_patch(Circle((x, y), 0.014, transform=ax.transAxes, fill=False, edgecolor=white, linewidth=lw, zorder=z))
        ax.scatter([x], [y], s=13, color=white, transform=ax.transAxes, zorder=z)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            ax.plot(
                [x + math.cos(rad) * 0.018, x + math.cos(rad) * 0.024],
                [y + math.sin(rad) * 0.072, y + math.sin(rad) * 0.094],
                transform=ax.transAxes,
                color=white,
                linewidth=lw,
                solid_capstyle="round",
                zorder=z,
            )
        return

    if topic == "主模型":
        dx, dy = 0.021, 0.078
        front = [(x, y + dy), (x + dx, y + dy / 2), (x + dx, y - dy / 2), (x, y - dy), (x - dx, y - dy / 2), (x - dx, y + dy / 2), (x, y + dy)]
        ax.plot([p[0] for p in front], [p[1] for p in front], transform=ax.transAxes, color=white, linewidth=lw, zorder=z)
        ax.plot([x, x], [y + dy, y - dy], transform=ax.transAxes, color=white, linewidth=lw * 0.75, zorder=z)
        ax.plot([x - dx, x + dx], [y + dy / 2, y - dy / 2], transform=ax.transAxes, color=white, linewidth=lw * 0.75, zorder=z)
        ax.plot([x + dx, x - dx], [y + dy / 2, y - dy / 2], transform=ax.transAxes, color=white, linewidth=lw * 0.75, zorder=z)
        return

    if topic == "数学/证明":
        ax.text(
            x,
            y,
            "Σ",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=18,
            color=white,
            weight="bold",
            zorder=z,
        )
        return

    if topic == "多模态":
        ax.add_patch(Rectangle((x - 0.026, y - 0.066), 0.052, 0.132, transform=ax.transAxes, fill=False, edgecolor=white, linewidth=lw, zorder=z))
        ax.scatter([x + 0.014], [y + 0.030], s=8, color=white, transform=ax.transAxes, zorder=z)
        ax.plot(
            [x - 0.023, x - 0.007, x + 0.004, x + 0.024],
            [y - 0.048, y - 0.010, y - 0.030, y - 0.048],
            transform=ax.transAxes,
            color=white,
            linewidth=lw,
            zorder=z,
        )
        return

    if topic == "代码":
        ax.plot([x - 0.018, x - 0.030, x - 0.018], [y + 0.060, y, y - 0.060], transform=ax.transAxes, color=white, linewidth=lw + 0.3, solid_capstyle="round", zorder=z)
        ax.plot([x + 0.018, x + 0.030, x + 0.018], [y + 0.060, y, y - 0.060], transform=ax.transAxes, color=white, linewidth=lw + 0.3, solid_capstyle="round", zorder=z)
        ax.plot([x + 0.008, x - 0.008], [y + 0.072, y - 0.072], transform=ax.transAxes, color=white, linewidth=lw, solid_capstyle="round", zorder=z)
        return

    if topic == "OCR":
        corner = 0.026
        span_x, span_y = 0.028, 0.075
        for sx, sy in [(-1, 1), (1, 1), (-1, -1), (1, -1)]:
            ax.plot([x + sx * span_x, x + sx * (span_x - corner)], [y + sy * span_y, y + sy * span_y], transform=ax.transAxes, color=white, linewidth=lw, zorder=z)
            ax.plot([x + sx * span_x, x + sx * span_x], [y + sy * span_y, y + sy * (span_y - corner)], transform=ax.transAxes, color=white, linewidth=lw, zorder=z)
        ax.plot([x - 0.026, x + 0.026], [y, y], transform=ax.transAxes, color=white, linewidth=lw, zorder=z)
        ax.plot([x - 0.016, x + 0.016], [y - 0.030, y - 0.030], transform=ax.transAxes, color=white, linewidth=lw * 0.8, zorder=z)
        return

    if topic == "推理/RL":
        nodes = [(x - 0.022, y + 0.045), (x + 0.022, y + 0.060), (x - 0.004, y - 0.060)]
        ax.plot([nodes[0][0], nodes[1][0], nodes[2][0], nodes[0][0]], [nodes[0][1], nodes[1][1], nodes[2][1], nodes[0][1]], transform=ax.transAxes, color=white, linewidth=lw, zorder=z)
        for nx, ny in nodes:
            ax.scatter([nx], [ny], s=15, color=white, transform=ax.transAxes, zorder=z)


def draw_topic_marker(ax, topic: str, x: float, y: float, color: str) -> None:
    """Simple color marker for topic cards."""

    ax.scatter([x], [y], s=95, color=color, alpha=0.96, transform=ax.transAxes, zorder=3)


def add_topic_cards(fig, df: pd.DataFrame) -> None:
    """Top theme distribution cards: fixed-size cards, not bubble chart."""

    card_ax = fig.add_axes([0.044, 0.690, 0.908, 0.115])
    card_ax.set_axis_off()
    card_ax.set_facecolor("#FFFFFF")

    topic_order = [
        "系统/效率",
        "主模型",
        "数学/证明",
        "多模态",
        "代码",
        "OCR",
        "推理/RL",
    ]
    counts = df["coarse_topic"].value_counts().to_dict()

    side_pad = 0.006
    gap = 0.018
    card_w = (1 - side_pad * 2 - gap * (len(topic_order) - 1)) / len(topic_order)
    card_h = 0.92

    for i, topic in enumerate(topic_order):
        x0 = side_pad + i * (card_w + gap)
        color = COLORS[topic]
        label = short_topic_label(topic)
        count = int(counts.get(topic, 0))

        box = FancyBboxPatch(
            (x0, 0.04),
            card_w,
            card_h,
            boxstyle="round,pad=0.006,rounding_size=0.025",
            transform=card_ax.transAxes,
            facecolor="#FFFFFF",
            edgecolor=color,
            linewidth=0.9,
            alpha=0.42,
            clip_on=False,
        )
        card_ax.add_patch(box)

        draw_topic_marker(card_ax, topic, x0 + card_w / 2, 0.74, color)
        card_ax.text(
            x0 + card_w / 2,
            0.47,
            label,
            ha="center",
            va="center",
            transform=card_ax.transAxes,
            fontproperties=font_prop("sans", 11.7, "bold"),
            color="#151515",
        )
        card_ax.text(
            x0 + card_w / 2,
            0.20,
            f"{count}",
            ha="right",
            va="center",
            transform=card_ax.transAxes,
            fontproperties=font_prop("sans", 22.2, "bold"),
            color=color,
        )
        card_ax.text(
            x0 + card_w / 2 + 0.018,
            0.20,
            "篇",
            ha="left",
            va="center",
            transform=card_ax.transAxes,
            fontproperties=font_prop("sans", 9.5, "bold"),
            color=color,
        )


def half_year_segments(df: pd.DataFrame) -> list[tuple[str, int, int]]:
    """Build half-year labels from the month column, matching chart order."""

    labels = []
    for value in df["year_month"]:
        year, month = str(value).split("-")
        half = "H1" if int(month) <= 6 else "H2"
        label = f"{year}\n{half}"
        if year == "2026" and half == "H1":
            label = "2026\nH1\n至今"
        labels.append(label)

    segments: list[tuple[str, int, int]] = []
    start = 0
    current = labels[0]
    for i, label in enumerate(labels[1:], start=1):
        if label != current:
            segments.append((current, start, i - 1))
            start = i
            current = label
    segments.append((current, start, len(labels) - 1))
    return segments


def portrait_timeline_card(df: pd.DataFrame) -> None:
    """New portrait infographic with topic cards and half-year segmentation."""

    df = df.copy().reset_index(drop=True)

    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    bg = "#FFFFFF"
    fig.patch.set_facecolor(bg)

    purple = "#6F35B6"
    title_color = "#15151A"
    light_line = "#E6E1EE"

    fig.add_artist(
        Rectangle(
            (0.044, 0.884),
            0.006,
            0.078,
            transform=fig.transFigure,
            color=purple,
            linewidth=0,
        )
    )
    fig.text(
        0.058,
        0.944,
        "DeepSeek两年27篇论文：发了什么，谁在参与",
        ha="left",
        va="center",
        fontproperties=font_prop("sans", 26.0, "bold"),
        color=title_color,
    )
    fig.text(
        0.058,
        0.914,
        "主题覆盖系统、基座模型、数学等7个方向；",
        ha="left",
        va="center",
        fontproperties=font_prop("sans", 15.2),
        color="#2F2F36",
    )
    fig.text(
        0.058,
        0.893,
        "基座模型报告作者数从86人扩至317人，小队研究与百人级工程并行",
        ha="left",
        va="center",
        fontproperties=font_prop("sans", 15.2),
        color="#2F2F36",
    )

    fig.text(
        0.044,
        0.835,
        "主题分布",
        ha="left",
        va="center",
        fontproperties=font_prop("sans", 16.0, "bold"),
        color=purple,
    )
    add_topic_cards(fig, df)

    fig.text(
        0.044,
        0.662,
        "27篇论文按发布时间排序：去重作者数",
        ha="left",
        va="center",
        fontproperties=font_prop("sans", 15.5, "bold"),
        color=title_color,
    )

    fig.add_artist(
        Rectangle(
            (0.722, 0.657),
            0.020,
            0.010,
            transform=fig.transFigure,
            facecolor="#FFFFFF",
            edgecolor="#222222",
            linewidth=1.1,
        )
    )
    fig.text(
        0.754,
        0.662,
        "黑色描边：基座模型系列",
        ha="left",
        va="center",
        fontproperties=font_prop("sans", 9.5),
        color="#303030",
    )

    ax = fig.add_axes([0.342, 0.125, 0.610, 0.515])
    ax.set_facecolor(bg)

    display = make_display_labels(df["short_title"])
    y = list(range(len(df)))
    bar_colors = [COLORS[t] for t in df["coarse_topic"]]
    is_base_model = df["main_model_stage"].notna() & ~df["short_title"].eq("DeepSeek-R1")
    edges = ["#222222" if flag else bg for flag in is_base_model]
    widths = [1.35 if flag else 0.0 for flag in is_base_model]

    ax.barh(
        y,
        df["author_count_for_chart"],
        color=bar_colors,
        edgecolor=edges,
        linewidth=widths,
        height=0.48,
        zorder=3,
    )
    ax.invert_yaxis()

    for yi, (_, row) in zip(y, df.iterrows()):
        value = int(row["author_count_for_chart"])
        ax.text(
            min(value + 5, 342),
            yi,
            str(value),
            va="center",
            ha="left",
            fontproperties=font_prop("sans", 11.0),
            color="#202020",
            zorder=5,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0, pad=0)

    label_font = font_prop("sans", 12.0)
    for yi, label, (_, row) in zip(y, display, df.iterrows()):
        ax.scatter(
            -0.295,
            yi,
            s=18,
            color=COLORS[row["coarse_topic"]],
            edgecolors="none",
            transform=ax.get_yaxis_transform(),
            clip_on=False,
            zorder=6,
        )
        ax.text(
            -0.268,
            yi,
            str(label),
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontproperties=label_font,
            color="#151515",
            clip_on=False,
            zorder=6,
        )

    ax.set_xlim(0, 350)
    ax.set_xticks([0, 50, 100, 150, 200, 250, 300, 350])
    ax.tick_params(axis="x", labelsize=9.5, colors="#3A3A3A", length=3)
    ax.set_xlabel("每篇论文的去重作者数（人）", fontproperties=font_prop("sans", 11.5), labelpad=8)

    ax.grid(axis="x", color="#E8E5EE", linewidth=0.75, linestyle="--", zorder=0)
    ax.grid(axis="y", visible=False)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#A6A2AF")
    ax.spines["bottom"].set_linewidth(0.9)

    segments = half_year_segments(df)
    for _, start, _ in segments[1:]:
        ax.axhline(
            start - 0.5,
            xmin=-0.36,
            xmax=1.0,
            color=light_line,
            linestyle="--",
            linewidth=0.8,
            clip_on=False,
            zorder=1,
        )

    for label, start, end in segments:
        mid = (start + end) / 2
        ax.text(
            -0.355,
            mid,
            label,
            transform=ax.get_yaxis_transform(),
            ha="center",
            va="center",
            fontproperties=font_prop("sans", 10.8, "bold"),
            color=purple,
            linespacing=1.25,
            clip_on=False,
        )
        ax.plot(
            [-0.430, -0.430],
            [start - 0.35, end + 0.35],
            transform=ax.get_yaxis_transform(),
            color="#ECE5F4",
            linewidth=0.70,
            clip_on=False,
            zorder=2,
        )
        ax.plot(
            [-0.430, -0.416],
            [start - 0.35, start - 0.35],
            transform=ax.get_yaxis_transform(),
            color="#ECE5F4",
            linewidth=0.70,
            clip_on=False,
            zorder=2,
        )
        ax.plot(
            [-0.430, -0.416],
            [end + 0.35, end + 0.35],
            transform=ax.get_yaxis_transform(),
            color="#ECE5F4",
            linewidth=0.70,
            clip_on=False,
            zorder=2,
        )

    ax.annotate(
        "",
        xy=(-0.487, len(df) - 0.4),
        xytext=(-0.487, -0.4),
        xycoords=ax.get_yaxis_transform(),
        textcoords=ax.get_yaxis_transform(),
        arrowprops=dict(arrowstyle="-|>", color=purple, linewidth=1.1),
        annotation_clip=False,
    )
    ax.text(
        -0.487,
        -0.95,
        "早期",
        transform=ax.get_yaxis_transform(),
        ha="center",
        va="bottom",
        fontproperties=font_prop("sans", 9.4),
        color=purple,
        clip_on=False,
    )
    ax.text(
        -0.487,
        len(df) - 0.05,
        "最新",
        transform=ax.get_yaxis_transform(),
        ha="center",
        va="top",
        fontproperties=font_prop("sans", 9.4),
        color=purple,
        clip_on=False,
    )

    fig.add_artist(
        Rectangle(
            (0.044, 0.070),
            0.908,
            0.0010,
            transform=fig.transFigure,
            color="#C8C5D1",
            alpha=0.9,
            linewidth=0,
        )
    )

    footer_x = 0.044
    footer_color = "#555555"
    footer_font = font_prop("sans", 8.35)
    fig.text(
        footer_x,
        0.054,
        "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )
    fig.text(
        footer_x,
        0.039,
        "口径：主图统一使用每篇论文/技术报告的署名去重人数，剔除 DeepSeek-AI 等团队名。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )
    fig.text(
        footer_x,
        0.024,
        "备注：V2/V3/V3.2/V4可按附录拆分研究工程(R&E)、数据标注、商业合规；R&E去重为107/150/211/269。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )
    fig.text(
        footer_x,
        0.010,
        "制图：甲子光年",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )

    draw_jiazi_logo(fig, x=0.795, y=0.022, scale=0.88)

    df.to_csv(FIG / "fig2_data_used_v9_base_model.csv", index=False, encoding="utf-8-sig")

    fig.savefig(
        FIG / "fig2_author_count_timeline_card_v9_base_model.png",
        facecolor=fig.get_facecolor(),
        dpi=300,
    )
    fig.savefig(
        FIG / "fig2_author_count_timeline_card_v9_base_model.svg",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)


def main() -> None:
    configure_font()
    df = load_data()
    portrait_timeline_card(df)
    print(FIG)


if __name__ == "__main__":
    main()

