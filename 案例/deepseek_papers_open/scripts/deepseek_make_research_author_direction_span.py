from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT = BASE / "output"
FIG = BASE / "figures" / "author_direction_span"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
FIG.mkdir(parents=True, exist_ok=True)

ROLE_SPLIT_RESEARCH_TITLES = {
    "DeepSeek-V2",
    "DeepSeek-V3 Technical Report",
    "DeepSeek-V3.2",
    "DeepSeek-V4",
}

TEAM_NAMES = {
    "DeepSeek-AI",
    "DeepSeek AI",
    "DeepSeek",
    "deepseek-ai",
}

TOPIC_ORDER = ["主模型", "系统/效率", "数学/证明", "多模态", "代码", "OCR", "推理/RL"]
TOPIC_DISPLAY = {
    "主模型": "基座模型",
    "系统/效率": "系统",
    "数学/证明": "数学",
    "多模态": "多模态",
    "代码": "代码",
    "OCR": "OCR",
    "推理/RL": "推理/RL",
}

HIGHLIGHT_AUTHORS = ["Chong Ruan", "Yukun Li", "Daya Guo", "Wenfeng Liang"]
CHINESE_NAMES = {
    "Chong Ruan": "阮翀",
    "Yukun Li": "李宇琨",
    "Daya Guo": "郭达雅",
    "Wenfeng Liang": "梁文锋",
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
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(path)).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


def font_prop(size: float | None = None, weight: str | None = None) -> font_manager.FontProperties:
    candidates = [
        NOTO_SC_BOLD if weight == "bold" else NOTO_SC_REGULAR,
        NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyhbd.ttc") if weight == "bold" else Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    kwargs: dict[str, object] = {}
    if size is not None:
        kwargs["size"] = size
    if weight is not None:
        kwargs["weight"] = weight
    if path:
        return font_manager.FontProperties(fname=str(path), **kwargs)
    return font_manager.FontProperties(**kwargs)


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.805, y: float = 0.020, scale: float = 0.96) -> None:
    if not JIAZI_LOGO.exists():
        return
    logo_ax = fig.add_axes([x, y, 0.152 * scale, 0.055 * scale])
    logo_ax.imshow(plt.imread(JIAZI_LOGO))
    logo_ax.set_axis_off()


def build_research_author_pool() -> pd.DataFrame:
    raw = pd.read_csv(OUT / "paper_authors_clean.csv", encoding="utf-8-sig")
    papers = pd.read_csv(OUT / "papers_clean.csv", encoding="utf-8-sig")
    roles = pd.read_csv(OUT / "main_model_authors_with_roles.csv", encoding="utf-8-sig")

    meta_cols = [
        column
        for column in ["paper_id", "short_title", "year_month", "coarse_topic", "main_model_stage", "title", "source", "source_url"]
        if column in papers.columns
    ]
    meta = papers[meta_cols].drop_duplicates()

    raw_unsplit = raw[~raw["short_title"].isin(ROLE_SPLIT_RESEARCH_TITLES)].copy()
    raw_unsplit["research_pool_source"] = "原始署名名单"

    role_mask = roles["short_title"].isin(ROLE_SPLIT_RESEARCH_TITLES) & roles["is_research_engineering"].astype(str).str.upper().eq("TRUE")
    role_research = roles.loc[role_mask, ["paper_id", "short_title", "clean_author_name", "departed_mark"]].copy()
    role_research = role_research.merge(meta, on=["paper_id", "short_title"], how="left")
    role_research["research_pool_source"] = "Research & Engineering"

    keep_cols = [
        "paper_id",
        "short_title",
        "year_month",
        "coarse_topic",
        "main_model_stage",
        "title",
        "source",
        "source_url",
        "clean_author_name",
        "departed_mark",
        "research_pool_source",
    ]
    for column in keep_cols:
        if column not in raw_unsplit.columns:
            raw_unsplit[column] = ""
        if column not in role_research.columns:
            role_research[column] = ""

    pool = pd.concat([raw_unsplit[keep_cols], role_research[keep_cols]], ignore_index=True)
    pool["clean_author_name"] = pool["clean_author_name"].astype(str).str.strip()
    pool = pool[pool["clean_author_name"].ne("")]
    pool = pool[~pool["clean_author_name"].isin(TEAM_NAMES)]
    pool = pool.drop_duplicates(["paper_id", "clean_author_name"]).reset_index(drop=True)
    pool.to_csv(FIG / "research_author_pool_for_direction_span.csv", index=False, encoding="utf-8-sig")
    return pool


def make_author_span_tables(pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = pool[["clean_author_name", "paper_id", "coarse_topic"]].drop_duplicates()

    def direction_list(values: pd.Series) -> str:
        topics = set(values)
        return "、".join([TOPIC_DISPLAY[topic] for topic in TOPIC_ORDER if topic in topics])

    author = (
        base.groupby("clean_author_name")
        .agg(
            paper_count=("paper_id", "nunique"),
            direction_count=("coarse_topic", "nunique"),
            directions=("coarse_topic", direction_list),
        )
        .reset_index()
        .rename(columns={"clean_author_name": "author_name"})
    )
    author["is_highlighted"] = author["author_name"].isin(HIGHLIGHT_AUTHORS)
    author = author.sort_values(["direction_count", "paper_count", "author_name"], ascending=[False, False, True]).reset_index(drop=True)

    agg = (
        author.groupby("direction_count")
        .size()
        .reindex(range(1, 8), fill_value=0)
        .reset_index(name="author_count")
    )

    author.to_csv(FIG / "research_author_direction_span_distribution.csv", index=False, encoding="utf-8-sig")
    agg.to_csv(FIG / "research_author_direction_span_distribution_agg.csv", index=False, encoding="utf-8-sig")
    return author, agg


def plot(author: pd.DataFrame, agg: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")

    purple = "#6F35B6"
    dark = "#15151A"
    gray = "#555555"
    subtitle_color = "#2F2F36"

    three = int(agg.loc[agg["direction_count"].eq(3), "author_count"].iloc[0])
    four = int(agg.loc[agg["direction_count"].eq(4), "author_count"].iloc[0])
    five = int(agg.loc[agg["direction_count"].eq(5), "author_count"].iloc[0])
    six_plus = int(agg.loc[agg["direction_count"].isin([6, 7]), "author_count"].sum())

    fig.add_artist(Rectangle((0.044, 0.880), 0.006, 0.082, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(
        0.058,
        0.946,
        "DeepSeek研究员有多“跨界”",
        ha="left",
        va="center",
        fontproperties=font_prop(27.0, "bold"),
        color=dark,
    )
    fig.text(
        0.058,
        0.914,
        f"覆盖3个技术方向的研究作者{three}人，4个方向{four}人，5个方向{five}人；",
        ha="left",
        va="center",
        fontproperties=font_prop(14.8),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.891,
        "少数高频作者覆盖6—7个方向，能在基座模型、系统、数学、多模态等问题之间流动。",
        ha="left",
        va="center",
        fontproperties=font_prop(14.8),
        color=subtitle_color,
    )

    fig.text(
        0.044,
        0.824,
        "研究作者覆盖技术方向数分布",
        ha="left",
        va="center",
        fontproperties=font_prop(17.2, "bold"),
        color=dark,
    )

    ax = fig.add_axes([0.100, 0.335, 0.575, 0.430])
    ax.set_facecolor("#FFFFFF")

    x = agg["direction_count"].astype(int).tolist()
    y = agg["author_count"].astype(int).tolist()
    bars = ax.bar(x, y, width=0.58, color=purple, alpha=0.92, edgecolor="#4C2389", linewidth=1.0, zorder=3)

    for bar, value in zip(bars, y):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(y) * 0.018,
            str(value),
            ha="center",
            va="bottom",
            fontproperties=font_prop(12.5, "bold"),
            color=dark,
            zorder=5,
        )

    ax.set_xlim(0.35, 7.65)
    ax.set_ylim(0, max(y) * 1.18)
    ax.set_xticks(range(1, 8))
    ax.set_xlabel("覆盖技术方向数（个）", fontproperties=font_prop(12.8), labelpad=12)
    ax.set_ylabel("研究作者人数（人）", fontproperties=font_prop(12.8), labelpad=12)
    ax.tick_params(axis="both", labelsize=11.0, colors="#303030", length=3)
    ax.grid(axis="y", color="#E8E5EE", linewidth=0.85, linestyle="--", zorder=0)
    ax.grid(axis="x", visible=False)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#A6A2AF")
    ax.spines["bottom"].set_color("#A6A2AF")
    ax.spines["left"].set_linewidth(0.9)
    ax.spines["bottom"].set_linewidth(0.9)

    # Right-side callout for selected high-frequency cross-direction authors.
    box = FancyBboxPatch(
        (0.710, 0.390),
        0.242,
        0.340,
        boxstyle="round,pad=0.010,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#F5F1FB",
        edgecolor="#D2C5E8",
        linewidth=0.9,
    )
    fig.add_artist(box)
    fig.text(0.730, 0.704, "高频跨界样本", ha="left", va="center", fontproperties=font_prop(14.4, "bold"), color=purple)
    fig.text(0.730, 0.681, "代表人物并非全部，仅作示意", ha="left", va="center", fontproperties=font_prop(9.2), color=gray)

    y0 = 0.642
    for idx, name in enumerate(HIGHLIGHT_AUTHORS):
        row = author[author["author_name"].eq(name)]
        if row.empty:
            continue
        row = row.iloc[0]
        chinese = CHINESE_NAMES.get(name, name)
        line1 = f"{chinese}"
        line2 = f"{int(row['paper_count'])}篇论文，覆盖{int(row['direction_count'])}个方向"
        fig.text(0.730, y0 - idx * 0.064, line1, ha="left", va="center", fontproperties=font_prop(12.4, "bold"), color=dark)
        fig.text(0.730, y0 - idx * 0.064 - 0.023, line2, ha="left", va="center", fontproperties=font_prop(10.0), color=gray)

    # Compact direction note.
    note = FancyBboxPatch(
        (0.100, 0.258),
        0.852,
        0.046,
        boxstyle="round,pad=0.006,rounding_size=0.008",
        transform=fig.transFigure,
        facecolor="#FFFFFF",
        edgecolor="#D9D5E3",
        linewidth=0.8,
    )
    fig.add_artist(note)
    fig.text(
        0.120,
        0.281,
        "7个粗方向：基座模型、系统、数学、多模态、代码、OCR、推理/RL",
        ha="left",
        va="center",
        fontproperties=font_prop(10.5),
        color="#333333",
    )

    fig.add_artist(Rectangle((0.044, 0.105), 0.908, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(8.6)
    fig.text(0.044, 0.085, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=gray)
    fig.text(0.044, 0.067, "口径：V2/V3/V3.2/V4使用R&E名单；其他论文使用原始署名并剔除团队名。", ha="left", va="center", fontproperties=footer_font, color=gray)
    fig.text(0.044, 0.049, "备注：覆盖方向数按7个粗技术方向计算；参与论文数和覆盖方向数不代表贡献大小、作者排序或组织层级。", ha="left", va="center", fontproperties=footer_font, color=gray)
    fig.text(0.044, 0.031, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=gray)
    draw_jiazi_logo(fig, x=0.805, y=0.034, scale=0.96)

    fig.savefig(FIG / "research_author_direction_span_distribution.png", facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(FIG / "research_author_direction_span_distribution.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_font()
    pool = build_research_author_pool()
    author, agg = make_author_span_tables(pool)
    plot(author, agg)
    print(FIG / "research_author_direction_span_distribution.png")
    print(FIG / "research_author_direction_span_distribution.csv")
    print(FIG / "research_author_direction_span_distribution_agg.csv")


if __name__ == "__main__":
    main()

