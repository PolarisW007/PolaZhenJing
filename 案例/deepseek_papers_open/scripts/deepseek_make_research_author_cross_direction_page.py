from __future__ import annotations

from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle


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
R1_TITLE = "DeepSeek-R1"

TEAM_NAMES = {
    "DeepSeek-AI",
    "DeepSeek AI",
    "DeepSeek",
    "deepseek-ai",
}

RAW_TOPIC_ORDER = ["主模型", "系统/效率", "数学/证明", "多模态", "代码", "OCR", "推理/RL"]
TOPIC_DISPLAY = {
    "主模型": "基座模型",
    "系统/效率": "系统",
    "数学/证明": "数学",
    "多模态": "多模态",
    "代码": "代码",
    "OCR": "OCR",
    "推理/RL": "推理/RL",
}
TOPIC_SHORT = {
    "基座模型": "基座",
    "系统": "系统",
    "数学": "数学",
    "多模态": "多模态",
    "代码": "代码",
    "OCR": "OCR",
    "推理/RL": "推理",
}
TOPIC_COLORS = {
    "基座模型": "#6F35B6",
    "系统": "#E45CC8",
    "数学": "#2F9B72",
    "多模态": "#E08C31",
    "代码": "#2F6FB3",
    "OCR": "#8A8798",
    "推理/RL": "#9C67D9",
}

HIGHLIGHT_AUTHORS = ["Chong Ruan", "Yukun Li", "Wenfeng Liang", "Daya Guo", "Fuli Luo"]
CHINESE_NAMES = {
    "Chong Ruan": "阮翀",
    "Yukun Li": "李宇琨",
    "Daya Guo": "郭达雅",
    "Wenfeng Liang": "梁文锋",
    "Fuli Luo": "罗福莉",
}
REPRESENTATIVE_WORKS = {
    "Chong Ruan": "V2 / V3 / NSA / Prover",
    "Yukun Li": "OCR / Cond. Memory / Coder",
    "Daya Guo": "R1 / Coder / Math",
    "Wenfeng Liang": "V2 / V3 / NSA / mHC",
    "Fuli Luo": "MoE / Coder / Prover",
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


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.805, y: float = 0.030, scale: float = 0.96) -> None:
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

    raw_unsplit = raw[~raw["short_title"].isin(ROLE_SPLIT_RESEARCH_TITLES | {R1_TITLE})].copy()
    raw_unsplit["research_pool_source"] = "原始署名名单"

    role_mask = roles["short_title"].isin(ROLE_SPLIT_RESEARCH_TITLES) & roles["is_research_engineering"].astype(str).str.upper().eq("TRUE")
    role_research = roles.loc[role_mask, ["paper_id", "short_title", "clean_author_name", "departed_mark"]].copy()
    role_research = role_research.merge(meta, on=["paper_id", "short_title"], how="left")
    role_research["research_pool_source"] = "Research & Engineering"

    v3_re_names = set(
        roles.loc[
            roles["short_title"].eq("DeepSeek-V3 Technical Report")
            & roles["is_research_engineering"].astype(str).str.upper().eq("TRUE"),
            "clean_author_name",
        ]
    )
    r1_proxy = raw[
        raw["short_title"].eq(R1_TITLE)
        & raw["clean_author_name"].astype(str).str.strip().isin(v3_re_names)
    ].copy()
    r1_proxy["research_pool_source"] = "R1推定R&E（R1署名∩V3 R&E）"

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
        if column not in r1_proxy.columns:
            r1_proxy[column] = ""

    pool = pd.concat([raw_unsplit[keep_cols], role_research[keep_cols], r1_proxy[keep_cols]], ignore_index=True)
    pool["clean_author_name"] = pool["clean_author_name"].astype(str).str.strip()
    pool = pool[pool["clean_author_name"].ne("")]
    pool = pool[~pool["clean_author_name"].isin(TEAM_NAMES)]
    pool = pool.drop_duplicates(["paper_id", "clean_author_name"]).reset_index(drop=True)
    pool.to_csv(FIG / "research_author_pool_for_cross_direction_page.csv", index=False, encoding="utf-8-sig")
    return pool


def make_tables(pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = pool[["clean_author_name", "paper_id", "coarse_topic"]].drop_duplicates().copy()
    base["direction"] = base["coarse_topic"].map(TOPIC_DISPLAY)

    def direction_list(values: pd.Series) -> str:
        directions = set(values)
        ordered = [TOPIC_DISPLAY[topic] for topic in RAW_TOPIC_ORDER if TOPIC_DISPLAY[topic] in directions]
        return "、".join(ordered)

    profile = (
        base.groupby("clean_author_name")
        .agg(
            paper_count=("paper_id", "nunique"),
            direction_count=("direction", "nunique"),
            directions=("direction", direction_list),
        )
        .reset_index()
        .rename(columns={"clean_author_name": "author_name"})
    )
    profile["is_highlighted"] = profile["author_name"].isin(HIGHLIGHT_AUTHORS)
    profile = profile.sort_values(["direction_count", "paper_count", "author_name"], ascending=[False, False, True]).reset_index(drop=True)

    span_agg = (
        profile.groupby("direction_count")
        .size()
        .reindex(range(1, 8), fill_value=0)
        .reset_index(name="author_count")
    )

    pairs: list[dict[str, object]] = []
    for _, row in profile.iterrows():
        directions = str(row["directions"]).split("、")
        if len(directions) < 2:
            continue
        for a, b in combinations(directions, 2):
            pairs.append({"author_name": row["author_name"], "direction_a": a, "direction_b": b})
    pair_rows = pd.DataFrame(pairs)
    pair_counts = (
        pair_rows.groupby(["direction_a", "direction_b"])
        .agg(author_count=("author_name", "nunique"))
        .reset_index()
        .sort_values(["author_count", "direction_a", "direction_b"], ascending=[False, True, True])
        .reset_index(drop=True)
    )
    pair_counts["pair"] = pair_counts["direction_a"] + " × " + pair_counts["direction_b"]
    pair_counts["pair_short"] = pair_counts["direction_a"].map(TOPIC_SHORT) + " × " + pair_counts["direction_b"].map(TOPIC_SHORT)

    participation = (
        base.groupby("direction")
        .agg(author_count=("clean_author_name", "nunique"))
        .reindex([TOPIC_DISPLAY[topic] for topic in RAW_TOPIC_ORDER])
        .reset_index()
        .rename(columns={"direction": "direction"})
    )
    direction_display_order = ["基座模型", "推理/RL", "系统", "代码", "数学", "多模态", "OCR"]
    participation["direction"] = pd.Categorical(participation["direction"], direction_display_order, ordered=True)
    participation = participation.sort_values("direction").reset_index(drop=True)
    participation["direction"] = participation["direction"].astype(str)

    profile.to_csv(FIG / "research_author_direction_profile.csv", index=False, encoding="utf-8-sig")
    pair_counts.to_csv(FIG / "research_author_direction_pairs_top.csv", index=False, encoding="utf-8-sig")
    participation.to_csv(FIG / "research_author_direction_participation_counts.csv", index=False, encoding="utf-8-sig")
    span_agg.to_csv(FIG / "research_author_direction_span_distribution_agg_for_page.csv", index=False, encoding="utf-8-sig")
    return profile, span_agg, pair_counts, participation


def summary_card(fig: plt.Figure, x: float, y: float, value: str, label: str, icon: str = "", color: str = "#6F35B6") -> None:
    card = FancyBboxPatch(
        (x, y),
        0.213,
        0.072,
        boxstyle="round,pad=0.006,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#FFFFFF",
        edgecolor="#D8CBEA",
        linewidth=0.9,
        zorder=2,
    )
    fig.add_artist(card)
    fig.text(x + 0.035, y + 0.046, value, ha="left", va="center", fontproperties=font_prop(20.0, "bold"), color=color)
    fig.text(x + 0.035, y + 0.023, label, ha="left", va="center", fontproperties=font_prop(8.6), color="#3E3E46")


def plot(profile: pd.DataFrame, span_agg: pd.DataFrame, pair_counts: pd.DataFrame, participation: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")

    purple = "#6F35B6"
    dark = "#15151A"
    gray = "#555555"
    subtitle_color = "#2F2F36"

    total_authors = len(profile)
    span2plus = int(profile["direction_count"].ge(2).sum())
    span3plus = int(profile["direction_count"].ge(3).sum())
    top_pair_n = 8
    pair_top = pair_counts.head(top_pair_n).copy()

    # Header
    fig.add_artist(Rectangle((0.044, 0.875), 0.006, 0.087, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.058, 0.946, "不设限的DeepSeek：超半数研发作者在跨界", ha="left", va="center", fontproperties=font_prop(25.5, "bold"), color=dark)
    fig.text(
        0.058,
        0.913,
        "基于27篇论文研发作者统计：多数研发作者集中在1—2个方向，",
        ha="left",
        va="center",
        fontproperties=font_prop(12.6),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.891,
        "也有一批人横跨多个技术线，从基座模型到系统、数学、多模态等方向流动。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.6),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.868,
        "以下统计基于去重后的研发作者池，不等同于公司全部研发作者名单。",
        ha="left",
        va="center",
        fontproperties=font_prop(9.5),
        color="#686868",
    )

    # A: direction span distribution.
    fig.text(0.060, 0.800, "研发作者覆盖技术方向数分布", ha="left", va="center", fontproperties=font_prop(16.2, "bold"), color=dark)
    ax_a = fig.add_axes([0.095, 0.545, 0.500, 0.215])
    x = span_agg["direction_count"].astype(int).tolist()
    y = span_agg["author_count"].astype(int).tolist()
    bars = ax_a.bar(x, y, width=0.58, color=purple, alpha=0.92, edgecolor="#4C2389", linewidth=1.0, zorder=3)
    for bar, value in zip(bars, y):
        ax_a.text(bar.get_x() + bar.get_width() / 2, value + max(y) * 0.022, str(value), ha="center", va="bottom", fontproperties=font_prop(11.0, "bold"), color=dark)
    ax_a.set_xlim(0.35, 7.65)
    ax_a.set_ylim(0, max(y) * 1.18)
    ax_a.set_xticks(range(1, 8))
    ax_a.set_xlabel("覆盖技术方向数（个）", fontproperties=font_prop(9.8), labelpad=4)
    ax_a.set_ylabel("研发作者人数（人）", fontproperties=font_prop(9.8), labelpad=4)
    ax_a.tick_params(axis="both", labelsize=9.5, colors="#303030", length=3)
    ax_a.grid(axis="y", color="#E8E5EE", linewidth=0.75, linestyle="--", zorder=0)
    ax_a.grid(axis="x", visible=False)
    for spine in ["top", "right"]:
        ax_a.spines[spine].set_visible(False)
    ax_a.spines["left"].set_color("#A6A2AF")
    ax_a.spines["bottom"].set_color("#A6A2AF")

    conclusion = FancyBboxPatch(
        (0.060, 0.245),
        0.535,
        0.215,
        boxstyle="round,pad=0.012,rounding_size=0.016",
        transform=fig.transFigure,
        facecolor="#F4F0FA",
        edgecolor="#D8CBEA",
        linewidth=0.9,
    )
    fig.add_artist(conclusion)
    fig.text(0.085, 0.424, "这组数据说明什么？", ha="left", va="center", fontproperties=font_prop(15.0, "bold"), color=purple)
    conclusion_lines = [
        "多数研发作者集中在1—2个方向；",
        f"但{span2plus}人覆盖2个及以上方向，已超过半数，",
        f"其中{span3plus}人覆盖3个及以上方向。",
        "高频研发作者的跨方向参与，主要围绕基座模型展开，",
        "并向系统、推理、代码、多模态等方向延伸。",
        "这说明在DeepSeek，研发作者更像围绕问题流动，",
        "而不是固定在单一职责里。",
    ]
    for idx, line in enumerate(conclusion_lines):
        fig.text(0.085, 0.391 - idx * 0.023, line, ha="left", va="center", fontproperties=font_prop(10.0), color="#38343F")

    # C: direction participation.
    desired_order = ["基座模型", "推理/RL", "系统", "代码", "数学", "多模态", "OCR"]
    participation = participation.copy()
    participation["direction"] = pd.Categorical(participation["direction"], desired_order, ordered=True)
    participation = participation.sort_values("direction").reset_index(drop=True)

    fig.text(0.640, 0.800, "各方向参与作者数", ha="left", va="center", fontproperties=font_prop(14.8, "bold"), color=dark)
    ax_c = fig.add_axes([0.735, 0.640, 0.215, 0.125])
    participation_plot = participation.iloc[::-1].copy()
    colors = [TOPIC_COLORS.get(str(direction), purple) for direction in participation_plot["direction"]]
    ax_c.barh(participation_plot["direction"].astype(str), participation_plot["author_count"], color=colors, alpha=0.92, height=0.60, zorder=3)
    for yi, value in enumerate(participation_plot["author_count"]):
        ax_c.text(value + max(participation["author_count"]) * 0.025, yi, str(int(value)), ha="left", va="center", fontproperties=font_prop(8.8, "bold"), color=dark)
    ax_c.set_xlim(0, max(participation["author_count"]) * 1.25)
    ax_c.set_xlabel("研发作者人数（人）", fontproperties=font_prop(7.8), labelpad=2)
    ax_c.tick_params(axis="x", labelsize=7.8, colors="#303030", length=2)
    ax_c.tick_params(axis="y", labelsize=8.3, length=0)
    ax_c.grid(axis="x", color="#E8E5EE", linewidth=0.65, linestyle="--", zorder=0)
    for spine in ["top", "right", "left"]:
        ax_c.spines[spine].set_visible(False)
    ax_c.spines["bottom"].set_color("#A6A2AF")

    # B: top cross-direction pairs.
    fig.text(0.640, 0.550, "最常见跨界组合", ha="left", va="center", fontproperties=font_prop(14.8, "bold"), color=dark)
    ax_b = fig.add_axes([0.735, 0.405, 0.215, 0.110])
    pair_plot = pair_top.iloc[::-1].copy()
    ax_b.barh(pair_plot["pair_short"], pair_plot["author_count"], color="#9C67D9", alpha=0.92, height=0.62, zorder=3)
    for yi, value in enumerate(pair_plot["author_count"]):
        ax_b.text(value + max(pair_top["author_count"]) * 0.025, yi, str(int(value)), ha="left", va="center", fontproperties=font_prop(8.8, "bold"), color=dark)
    ax_b.set_xlim(0, max(pair_top["author_count"]) * 1.22)
    ax_b.set_xlabel("研发作者人数（人）", fontproperties=font_prop(7.8), labelpad=2)
    ax_b.tick_params(axis="x", labelsize=7.8, colors="#303030", length=2)
    ax_b.tick_params(axis="y", labelsize=8.3, length=0)
    ax_b.grid(axis="x", color="#E8E5EE", linewidth=0.65, linestyle="--", zorder=0)
    for spine in ["top", "right", "left"]:
        ax_b.spines[spine].set_visible(False)
    ax_b.spines["bottom"].set_color("#A6A2AF")

    # D: high-frequency samples.
    card = FancyBboxPatch(
        (0.640, 0.132),
        0.312,
        0.205,
        boxstyle="round,pad=0.010,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#F5F1FB",
        edgecolor="#D2C5E8",
        linewidth=0.9,
    )
    fig.add_artist(card)
    fig.text(0.660, 0.316, "高频跨界样本", ha="left", va="center", fontproperties=font_prop(13.4, "bold"), color=purple)
    fig.text(0.660, 0.298, "代表人物非全部，仅作示意", ha="left", va="center", fontproperties=font_prop(7.6), color=gray)
    col_x = [0.660, 0.718, 0.772, 0.825]
    headers = ["作者", "参与论文", "覆盖方向", "代表方向"]
    for x_pos, header in zip(col_x, headers):
        fig.text(x_pos, 0.274, header, ha="left", va="center", fontproperties=font_prop(7.4, "bold"), color="#4B4652")
    fig.add_artist(Rectangle((0.660, 0.260), 0.270, 0.0008, transform=fig.transFigure, color="#D8CBEA", linewidth=0))
    y0 = 0.242
    for idx, name in enumerate(HIGHLIGHT_AUTHORS):
        row = profile[profile["author_name"].eq(name)]
        if row.empty:
            continue
        row = row.iloc[0]
        base_y = y0 - idx * 0.025
        fig.text(col_x[0], base_y, CHINESE_NAMES[name], ha="left", va="center", fontproperties=font_prop(7.9, "bold"), color=dark)
        fig.text(col_x[1], base_y, f"{int(row['paper_count'])}篇", ha="left", va="center", fontproperties=font_prop(7.8), color=dark)
        fig.text(col_x[2], base_y, f"{int(row['direction_count'])}向", ha="left", va="center", fontproperties=font_prop(7.8), color=dark)
        fig.text(col_x[3], base_y, REPRESENTATIVE_WORKS[name], ha="left", va="center", fontproperties=font_prop(6.8), color=gray)

    # Footer.
    fig.add_artist(Rectangle((0.044, 0.100), 0.908, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(7.95)
    fig.text(0.044, 0.080, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=gray)
    fig.text(
        0.044,
        0.062,
        "口径：仅统计去重后的研发作者池；覆盖方向数按7个粗技术方向计算。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=gray,
    )
    fig.text(
        0.044,
        0.044,
        "说明：“各方向参与作者数”表示至少参与过该方向1篇论文的研发作者人数，不代表主攻方向；参与论文数和覆盖方向数不代表贡献大小或组织层级。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=gray,
    )
    fig.text(0.044, 0.026, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=gray)
    draw_jiazi_logo(fig, x=0.805, y=0.034, scale=0.92)

    fig.savefig(FIG / "researcher_cross_direction_overview_v2_layout.png", facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(FIG / "researcher_cross_direction_overview_v2_layout.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def plot(profile: pd.DataFrame, span_agg: pd.DataFrame, pair_counts: pd.DataFrame, participation: pd.DataFrame) -> None:
    """Card-based media infographic version."""

    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    fig.patch.set_facecolor("#FEFDFF")

    purple = "#6F35B6"
    violet = "#8F5BD6"
    dark = "#15151A"
    gray = "#555555"
    subtitle_color = "#2F2F36"
    card_edge = "#DDD2EE"
    grid_color = "#E8E2F0"

    total_authors = len(profile)
    span3plus = int(profile["direction_count"].ge(3).sum())
    span3_rate = span3plus / total_authors if total_authors else 0
    top_pair_n = 8
    pair_top = pair_counts.head(top_pair_n).copy()

    def panel(x: float, y: float, w: float, h: float, facecolor: str = "#FFFFFF") -> None:
        fig.add_artist(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                transform=fig.transFigure,
                facecolor=facecolor,
                edgecolor=card_edge,
                linewidth=0.8,
                zorder=-10,
            )
        )

    # Header.
    fig.add_artist(Rectangle((0.044, 0.872), 0.006, 0.092, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.062, 0.946, "不设限的DeepSeek：超半数研发作者在跨界", ha="left", va="center", fontproperties=font_prop(22.6, "bold"), color=dark)
    fig.text(
        0.058,
        0.916,
        "基于27篇论文研发作者统计：多数研发作者集中在1—2个方向，",
        ha="left",
        va="center",
        fontproperties=font_prop(11.3),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.896,
        "也有一批人横跨多个技术线；基座模型之外，系统、数学、推理等方向同样吸引力强。",
        ha="left",
        va="center",
        fontproperties=font_prop(11.3),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.873,
        "以下统计基于去重后的研发作者池，不等同于公司全部研发作者名单。",
        ha="left",
        va="center",
        fontproperties=font_prop(8.7),
        color="#686868",
    )

    summary_card(fig, 0.046, 0.785, f"{total_authors}", "去重研发作者", "人")
    summary_card(fig, 0.278, 0.785, f"{span3plus}", "覆盖3个及以上方向", "3+")
    summary_card(fig, 0.510, 0.785, f"{top_pair_n}", "最常见跨界组合展示数", "8")
    summary_card(fig, 0.742, 0.785, "7", "粗技术方向", "7")

    # A: direction span distribution.
    panel(0.046, 0.375, 0.437, 0.375)
    fig.text(0.068, 0.723, "研发作者覆盖技术方向数分布", ha="left", va="center", fontproperties=font_prop(16.6, "bold"), color=dark)
    fig.add_artist(Rectangle((0.072, 0.685), 0.010, 0.010, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.088, 0.690, "研发作者数（人）", ha="left", va="center", fontproperties=font_prop(10.0), color="#49434F")
    ax_a = fig.add_axes([0.100, 0.465, 0.345, 0.195])
    x = span_agg["direction_count"].astype(int).tolist()
    y = span_agg["author_count"].astype(int).tolist()
    bars = ax_a.bar(x, y, width=0.52, color=purple, alpha=0.94, edgecolor="#5A2A96", linewidth=0.8, zorder=3)
    for bar, value in zip(bars, y):
        ax_a.text(bar.get_x() + bar.get_width() / 2, value + max(y) * 0.018, str(value), ha="center", va="bottom", fontproperties=font_prop(10.4, "bold"), color=dark)
    ax_a.set_xlim(0.35, 7.65)
    ax_a.set_ylim(0, max(y) * 1.22)
    ax_a.set_xticks(range(1, 8))
    ax_a.set_xlabel("覆盖技术方向数（个）", fontproperties=font_prop(10.4), labelpad=4)
    ax_a.tick_params(axis="both", labelsize=10.0, colors="#303030", length=2.5)
    ax_a.grid(axis="y", color=grid_color, linewidth=0.55, linestyle="--", zorder=0)
    ax_a.grid(axis="x", visible=False)
    ax_a.set_ylabel("")
    for spine in ["top", "right"]:
        ax_a.spines[spine].set_visible(False)
    ax_a.spines["left"].set_color("#AAA4B2")
    ax_a.spines["bottom"].set_color("#AAA4B2")

    # Core conclusion.
    conclusion = FancyBboxPatch(
        (0.046, 0.135),
        0.437,
        0.205,
        boxstyle="round,pad=0.010,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#F6F1FB",
        edgecolor="#D8CBEA",
        linewidth=0.9,
    )
    fig.add_artist(conclusion)
    fig.text(0.078, 0.308, "核心结论：这组数据说明什么？", ha="left", va="center", fontproperties=font_prop(14.8, "bold"), color=purple)
    bullets = [
        "多数研发作者集中在1—2个方向，研究重心相对聚焦；",
        f"约{span3_rate:.0%}覆盖3个及以上方向，跨界特征明显；",
        "以基座模型为核心，系统、推理、代码等方向延伸；",
        "研发作者围绕问题流动，未固定在单一岗位。",
    ]
    for idx, line in enumerate(bullets):
        y_pos = 0.277 - idx * 0.039
        fig.text(0.070, y_pos, "✓", ha="center", va="center", fontproperties=font_prop(14.0, "bold"), color=purple)
        fig.text(0.088, y_pos, line, ha="left", va="center", fontproperties=font_prop(10.4), color="#38343F")

    # C: direction participation.
    desired_order = ["基座模型", "推理/RL", "系统", "代码", "数学", "多模态", "OCR"]
    participation = participation.copy()
    participation["direction"] = pd.Categorical(participation["direction"], desired_order, ordered=True)
    participation = participation.sort_values("direction").reset_index(drop=True)

    panel(0.518, 0.590, 0.437, 0.160)
    fig.text(0.535, 0.723, "各方向参与作者数", ha="left", va="center", fontproperties=font_prop(16.0, "bold"), color=dark)
    fig.add_artist(Rectangle((0.810, 0.723), 0.010, 0.010, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.825, 0.728, "研发作者数（人）", ha="left", va="center", fontproperties=font_prop(9.4), color="#49434F")
    ax_c = fig.add_axes([0.615, 0.620, 0.315, 0.090])
    participation_plot = participation.iloc[::-1].copy()
    colors = [TOPIC_COLORS.get(str(direction), purple) for direction in participation_plot["direction"]]
    ax_c.barh(participation_plot["direction"].astype(str), participation_plot["author_count"], color=colors, alpha=0.92, height=0.52, zorder=3)
    for yi, value in enumerate(participation_plot["author_count"]):
        ax_c.text(value + max(participation["author_count"]) * 0.025, yi, str(int(value)), ha="left", va="center", fontproperties=font_prop(9.4, "bold"), color=dark)
    ax_c.set_xlim(0, max(participation["author_count"]) * 1.25)
    ax_c.tick_params(axis="x", labelsize=8.8, colors="#303030", length=2)
    ax_c.tick_params(axis="y", labelsize=9.4, length=0)
    ax_c.grid(axis="x", color=grid_color, linewidth=0.55, linestyle="--", zorder=0)
    ax_c.set_xlabel("")
    for spine in ["top", "right", "left"]:
        ax_c.spines[spine].set_visible(False)
    ax_c.spines["bottom"].set_color("#A6A2AF")

    # B: top cross-direction pairs.
    panel(0.518, 0.375, 0.437, 0.182)
    fig.text(0.535, 0.535, "最常见跨界组合", ha="left", va="center", fontproperties=font_prop(16.0, "bold"), color=dark)
    fig.add_artist(Rectangle((0.810, 0.535), 0.010, 0.010, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.825, 0.540, "研发作者数（人）", ha="left", va="center", fontproperties=font_prop(9.4), color="#49434F")
    ax_b = fig.add_axes([0.620, 0.407, 0.315, 0.102])
    pair_plot = pair_top.iloc[::-1].copy()
    ax_b.barh(pair_plot["pair_short"], pair_plot["author_count"], color=violet, alpha=0.92, height=0.52, zorder=3)
    for yi, value in enumerate(pair_plot["author_count"]):
        ax_b.text(value + max(pair_top["author_count"]) * 0.025, yi, str(int(value)), ha="left", va="center", fontproperties=font_prop(9.4, "bold"), color=dark)
    ax_b.set_xlim(0, max(pair_top["author_count"]) * 1.22)
    ax_b.tick_params(axis="x", labelsize=8.8, colors="#303030", length=2)
    ax_b.tick_params(axis="y", labelsize=9.2, length=0)
    ax_b.grid(axis="x", color=grid_color, linewidth=0.55, linestyle="--", zorder=0)
    ax_b.set_xlabel("")
    for spine in ["top", "right", "left"]:
        ax_b.spines[spine].set_visible(False)
    ax_b.spines["bottom"].set_color("#A6A2AF")

    # D: high-frequency samples.
    panel(0.518, 0.135, 0.437, 0.205, "#F8F4FC")
    fig.text(0.535, 0.318, "高频跨界样本", ha="left", va="center", fontproperties=font_prop(16.2, "bold"), color=purple)
    col_x = [0.548, 0.635, 0.705, 0.775]
    headers = ["作者", "参与论文", "覆盖方向", "代表方向"]
    for x_pos, header in zip(col_x, headers):
        fig.text(x_pos, 0.286, header, ha="left", va="center", fontproperties=font_prop(9.0, "bold"), color="#4B4652")
    fig.add_artist(Rectangle((0.548, 0.271), 0.370, 0.0008, transform=fig.transFigure, color="#D8CBEA", linewidth=0))
    y0 = 0.252
    for idx, name in enumerate(HIGHLIGHT_AUTHORS):
        row = profile[profile["author_name"].eq(name)]
        if row.empty:
            continue
        row = row.iloc[0]
        base_y = y0 - idx * 0.024
        if idx > 0:
            fig.add_artist(Rectangle((0.548, base_y + 0.013), 0.370, 0.0006, transform=fig.transFigure, color="#E4DDEF", linewidth=0))
        fig.text(col_x[0], base_y, CHINESE_NAMES[name], ha="left", va="center", fontproperties=font_prop(9.2, "bold"), color=dark)
        fig.text(col_x[1], base_y, f"{int(row['paper_count'])}篇", ha="left", va="center", fontproperties=font_prop(8.8), color=dark)
        fig.text(col_x[2], base_y, f"{int(row['direction_count'])}向", ha="left", va="center", fontproperties=font_prop(8.8), color=dark)
        fig.text(col_x[3], base_y, REPRESENTATIVE_WORKS[name], ha="left", va="center", fontproperties=font_prop(7.8), color=gray)

    # Footer.
    fig.add_artist(Rectangle((0.044, 0.108), 0.908, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(6.35)
    fig.text(0.052, 0.091, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=gray)
    fig.text(
        0.052,
        0.076,
        "口径：仅统计去重后的研发作者池；V2/V3/V3.2/V4仅取R&E名单；R1按“R1署名∩V3R&E”保守纳入；",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=gray,
    )
    fig.text(
        0.052,
        0.061,
        "LLM及其他未拆角色论文使用原始署名并剔除团队名；覆盖方向数按7个粗技术方向计算。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=gray,
    )
    fig.text(
        0.052,
        0.046,
        "口径补充：Research & Engineering 同时包含研究和工程角色，本文统称为“研发作者”。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=gray,
    )
    fig.text(
        0.052,
        0.031,
        "说明：各方向参与作者数表示至少参与该方向1篇论文的研发作者人数；跨界组合表示至少参与两个方向论文的作者数。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=gray,
    )
    fig.text(0.052, 0.014, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=gray)
    draw_jiazi_logo(fig, x=0.790, y=0.035, scale=0.92)

    fig.savefig(FIG / "researcher_cross_direction_overview_v3_card_style.png", facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(FIG / "researcher_cross_direction_overview_v3_card_style.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_font()
    pool = build_research_author_pool()
    profile, span_agg, pair_counts, participation = make_tables(pool)
    plot(profile, span_agg, pair_counts, participation)
    print(FIG / "researcher_cross_direction_overview_v3_card_style.png")
    print(FIG / "research_author_direction_profile.csv")
    print(FIG / "research_author_direction_pairs_top.csv")
    print(FIG / "research_author_direction_participation_counts.csv")


if __name__ == "__main__":
    main()

