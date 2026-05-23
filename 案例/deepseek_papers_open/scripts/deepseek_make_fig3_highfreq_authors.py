from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
FIG = BASE / "figures" / "author_frequency"
OUT = BASE / "output"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
FIG.mkdir(parents=True, exist_ok=True)

RAW_TOP25 = FIG / "fig3_high_frequency_authors_top25_data.csv"
AUG_TOP25 = FIG / "fig3_high_frequency_authors_top25_data_augmented.csv"
RESEARCH_POOL = FIG / "fig3_research_author_pool_v11.csv"
RAW_RESEARCH_TOP25 = FIG / "fig3_high_frequency_research_authors_top25_data_v11.csv"
ALL_RESEARCH_GE4 = FIG / "fig3_high_frequency_research_authors_all_ge4_data_v11.csv"
PLOT_DATA = FIG / "fig3_high_frequency_research_authors_top25_plot_data_v11.csv"

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


COLORS = {
    "主模型": "#6F35B6",
    "系统/效率": "#E45CC8",
    "多模态": "#E08C31",
    "数学/证明": "#2F9B72",
    "代码": "#2F6FB3",
    "推理/RL": "#9C67D9",
    "OCR": "#8A8798",
}

DISPLAY_TOPIC = {
    "主模型": "基座模型",
    "系统/效率": "系统",
    "数学/证明": "数学",
}

TOPIC_ORDER = ["主模型", "系统/效率", "多模态", "数学/证明", "代码", "推理/RL", "OCR"]

SCHOOL_BADGES = {
    "Chong Ruan": "北大",
    "Zhenda Xie": "清华",
    "Damai Dai": "北大",
    "Wenfeng Liang": "浙大",
    "Yu Wu": "北航",
    "Huazuo Gao": "北大",
    "Qihao Zhu": "北大",
    "Zhihong Shao": "清华",
    "Chengqi Deng": "浙大",
    "Liyue Zhang": "中山",
    "Shirong Ma": "清华",
    "Daya Guo": "中山",
    "Xingkai Yu": "南大",
    "Bingxuan Wang": "北大",
    "Chenggang Zhao": "清华",
    "Dejian Yang": "北航",
    "Jiashi Li": "北大",
    "Junxiao Song": "港科大",
    "Wangding Zeng": "北邮",
    "Yaofeng Sun": "北大",
    "Wen Liu": "上科大",
    "Runxin Xu": "北大",
    "Deli Chen": "北大",
    "Peiyi Wang": "北大",
    "Wenjun Gao": "上交",
}

SCHOOL_COLORS = {
    "北大": ("#8C1D40", "#F7EDF1"),
    "清华": ("#6F35B6", "#F1ECF8"),
    "浙大": ("#1D64B7", "#EEF4FC"),
    "中山": ("#2F7D61", "#EDF7F2"),
    "北航": ("#1F75B7", "#EEF5FB"),
    "港科大": ("#B78A2A", "#FBF6E8"),
    "北邮": ("#4E7BBD", "#EEF4FB"),
    "上科大": ("#4F6D7A", "#F0F4F6"),
    "南大": ("#7A3DB8", "#F2ECF8"),
    "上交": ("#B43A45", "#FAEEF0"),
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


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.805, y: float = 0.018, scale: float = 0.96) -> None:
    if not JIAZI_LOGO.exists():
        return
    logo_ax = fig.add_axes([x, y, 0.152 * scale, 0.055 * scale])
    logo_ax.imshow(plt.imread(JIAZI_LOGO))
    logo_ax.set_axis_off()


def build_top25_base() -> pd.DataFrame:
    pool = build_research_author_pool()

    base = pool[["clean_author_name", "paper_id", "year_month", "coarse_topic"]].drop_duplicates()
    grouped = (
        base.groupby("clean_author_name")
        .agg(
            paper_count=("paper_id", "nunique"),
            topic_count=("coarse_topic", "nunique"),
            first_seen=("year_month", "min"),
            last_seen=("year_month", "max"),
        )
        .reset_index()
        .rename(columns={"clean_author_name": "author"})
    )
    topics = (
        base.groupby("clean_author_name")["coarse_topic"]
        .apply(lambda values: "、".join([topic for topic in TOPIC_ORDER if topic in set(values)]))
        .reset_index()
        .rename(columns={"clean_author_name": "author", "coarse_topic": "topics"})
    )
    matrix = (
        base.assign(value=1)
        .pivot_table(
            index="clean_author_name",
            columns="coarse_topic",
            values="value",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename(columns={"clean_author_name": "author"})
    )

    for topic in TOPIC_ORDER:
        if topic not in matrix.columns:
            matrix[topic] = 0

    df = grouped.merge(topics, on="author", how="left").merge(matrix[["author", *TOPIC_ORDER]], on="author", how="left")
    df = df[df["paper_count"].astype(int) >= 4]
    df = df.sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True]).reset_index(drop=True)

    df.to_csv(ALL_RESEARCH_GE4, index=False, encoding="utf-8-sig")
    top25 = df.head(25).copy()
    top25.to_csv(RAW_RESEARCH_TOP25, index=False, encoding="utf-8-sig")
    return top25


def build_research_author_pool() -> pd.DataFrame:
    """Build the research-author pool used by Fig. 2.

    V2/V3/V3.2/V4 use appendix Research & Engineering lists. Other papers
    use the original cleaned author list.
    """

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
    pool.to_csv(RESEARCH_POOL, index=False, encoding="utf-8-sig")
    return pool


def load_data() -> pd.DataFrame:
    top25 = build_top25_base()

    if AUG_TOP25.exists():
        aug = pd.read_csv(AUG_TOP25, encoding="utf-8-sig")
        keep_cols = ["author", "chinese_name", "chinese_name_status"]
        top25 = top25.merge(aug[keep_cols], on="author", how="left")
    else:
        top25["chinese_name"] = ""
        top25["chinese_name_status"] = ""

    updates_path = FIG / "fig3_user_confirmed_author_updates.csv"
    if updates_path.exists():
        updates = pd.read_csv(updates_path, encoding="utf-8-sig")
        updates = updates[["author", "chinese_name"]].rename(columns={"chinese_name": "confirmed_chinese_name"})
        top25 = top25.merge(updates, on="author", how="left")
        missing = top25["chinese_name"].fillna("").astype(str).str.strip().eq("")
        confirmed = top25["confirmed_chinese_name"].fillna("").astype(str).str.strip().ne("")
        top25.loc[missing & confirmed, "chinese_name"] = top25.loc[missing & confirmed, "confirmed_chinese_name"]
        top25.loc[missing & confirmed, "chinese_name_status"] = "用户确认"
        top25 = top25.drop(columns=["confirmed_chinese_name"])

    v4 = pd.read_csv(OUT / "main_model_authors_with_roles.csv", encoding="utf-8-sig")
    departed_authors = set(
        v4.loc[
            (v4["short_title"].eq("DeepSeek-V4"))
            & (v4["departed_mark"].astype(str).str.upper().eq("TRUE")),
            "clean_author_name",
        ]
    )
    top25["departed"] = top25["author"].isin(departed_authors)
    top25["school_badge"] = top25["author"].map(SCHOOL_BADGES).fillna("")

    def display_name(row: pd.Series) -> str:
        name = str(row["author"])
        chinese = str(row.get("chinese_name", "")).strip()
        status = str(row.get("chinese_name_status", "")).strip()
        if chinese and status in {"已核验", "用户确认"}:
            name = f"{name}（{chinese}）"
        if bool(row["departed"]):
            name = f"{name}*"
        return name

    top25["display_name"] = top25.apply(display_name, axis=1)
    top25.to_csv(PLOT_DATA, index=False, encoding="utf-8-sig")
    return top25


def plot(top25: pd.DataFrame) -> None:
    high = pd.read_csv(ALL_RESEARCH_GE4, encoding="utf-8-sig")
    high_count = len(high)
    ge10_count = int((high["paper_count"].astype(int) >= 10).sum())
    identified_school_count = int(top25["school_badge"].astype(str).str.len().gt(0).sum())
    pku_count = int(top25["school_badge"].eq("北大").sum())
    pku_share = pku_count / identified_school_count if identified_school_count else 0

    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")

    purple = "#6F35B6"
    title_color = "#15151A"
    subtitle_color = "#2F2F36"
    footer_color = "#555555"

    # Header
    fig.add_artist(Rectangle((0.044, 0.870), 0.006, 0.092, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(
        0.058,
        0.946,
        "DeepSeeK Top25研发作者近四成来自北大",
        ha="left",
        va="center",
        fontproperties=font_prop(24.0, "bold"),
        color=title_color,
    )
    fig.text(
        0.058,
        0.916,
        "140人参与4篇以上论文，24位参与10篇以上；",
        ha="left",
        va="center",
        fontproperties=font_prop(15.0),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.894,
        "Top 25研发作者全部跨越3个以上技术栈，最强“跨界战士”一人横跨7个方向",
        ha="left",
        va="center",
        fontproperties=font_prop(15.0),
        color=subtitle_color,
    )

    # Main chart title and legend
    fig.text(
        0.044,
        0.828,
        "参与论文数Top25研发作者：按技术方向拆分",
        ha="left",
        va="center",
        fontproperties=font_prop(15.8, "bold"),
        color=title_color,
    )

    legend_ax = fig.add_axes([0.044, 0.778, 0.896, 0.030])
    legend_ax.set_axis_off()
    for i, topic in enumerate(TOPIC_ORDER):
        x = 0.045 + i * 0.135
        y = 0.52
        legend_ax.scatter([x], [y], s=40, color=COLORS[topic], transform=legend_ax.transAxes, clip_on=False)
        legend_ax.text(
            x + 0.020,
            y,
            DISPLAY_TOPIC.get(topic, topic),
            ha="left",
            va="center",
            transform=legend_ax.transAxes,
            fontproperties=font_prop(9.2),
            color="#303030",
        )

    # Stacked horizontal bars
    ax = fig.add_axes([0.355, 0.158, 0.585, 0.613])
    ax.set_facecolor("#FFFFFF")

    y = list(range(len(top25)))
    left = pd.Series([0] * len(top25), dtype=float)
    for topic in TOPIC_ORDER:
        values = top25[topic].fillna(0).astype(float)
        ax.barh(
            y,
            values,
            left=left,
            height=0.50,
            color=COLORS[topic],
            edgecolor="#FFFFFF",
            linewidth=0.7,
            zorder=3,
        )
        left += values

    ax.invert_yaxis()
    ax.set_ylim(len(top25) - 0.5, -0.5)
    ax.set_xlim(0, 20)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.tick_params(axis="x", labelsize=10, colors="#3A3A3A", length=3)
    ax.set_xlabel("参与论文数（篇）", fontproperties=font_prop(11.5), labelpad=8)
    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0, pad=0)
    ax.grid(axis="x", color="#E8E5EE", linewidth=0.75, linestyle="--", zorder=0)
    ax.grid(axis="y", visible=False)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#A6A2AF")
    ax.spines["bottom"].set_linewidth(0.9)

    name_font = font_prop(11.8)
    badge_font = font_prop(8.2, "bold")
    value_font = font_prop(10.8)
    for yi, (_, row) in zip(y, top25.iterrows()):
        badge = str(row.get("school_badge", "")).strip()
        if badge:
            edge, face = SCHOOL_COLORS.get(badge, ("#6F35B6", "#F3F0F8"))
            ax.text(
                -0.502,
                yi,
                badge,
                transform=ax.get_yaxis_transform(),
                ha="center",
                va="center",
                fontproperties=badge_font,
                color=edge,
                clip_on=False,
                zorder=7,
                bbox={
                    "boxstyle": "round,pad=0.22,rounding_size=0.16",
                    "facecolor": face,
                    "edgecolor": edge,
                    "linewidth": 0.75,
                },
            )
        ax.text(
            -0.445,
            yi,
            str(row["display_name"]),
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontproperties=name_font,
            color="#151515",
            clip_on=False,
            zorder=6,
        )
        ax.text(
            float(row["paper_count"]) + 0.22,
            yi,
            f"{int(row['paper_count'])}篇（{int(row['topic_count'])}方向）",
            ha="left",
            va="center",
            fontproperties=value_font,
            color="#202020",
            zorder=5,
        )

    # Footer
    fig.add_artist(Rectangle((0.044, 0.085), 0.908, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))

    footer_x = 0.044
    footer_font = font_prop(7.75)
    fig.text(footer_x, 0.070, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.056, "口径：高频作者基于清洗后的研发作者池统计；V2/V3/V3.2/V4使用R&E名单，其他论文使用原始署名并剔除团队名。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.042, "口径补充：Research & Engineering 同时包含研究和工程角色，本文统称为“研发作者”。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.028, "备注：参与论文数基于署名统计，不代表贡献大小、作者排序或组织层级；中文名与院校标签基于公开资料人工整理。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.014, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    draw_jiazi_logo(fig, x=0.805, y=0.020, scale=0.96)

    fig.savefig(FIG / "fig3_high_frequency_research_authors_v12.png", facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(FIG / "fig3_high_frequency_research_authors_v12.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_font()
    top25 = load_data()
    plot(top25)
    print(FIG / "fig3_high_frequency_research_authors_v12.png")
    print(PLOT_DATA)


if __name__ == "__main__":
    main()

