from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import math

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import to_rgba
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT = BASE / "output"
FIG = BASE / "figures" / "coauthor_network" / "old for all&Top50" / "ALL R&E"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
FIG.mkdir(parents=True, exist_ok=True)


AUTHOR_CHINESE_OVERRIDES = {
    "Yukun Li": "李宇琨",
    "Yu Wu": "吴俣",
    "Chengqi Deng": "邓乘奇",
    "Liyue Zhang": "张力越",
    "Xingkai Yu": "俞星凯",
    "Yaofeng Sun": "孙耀峰",
    "Wen Liu": "刘闻",
    "Runxin Xu": "许润昕",
    "Deli Chen": "陈德里",
    "Qihao Zhu": "朱琪豪",
    "Wangding Zeng": "曾旺丁",
}

# Do not mark internal/external status on the graphic unless it can be
# verified case by case. The chart uses paper signatures, not personnel files.
AUTHOR_CONTEXT_LABELS: dict[str, str] = {}


DRAW_MIN_SHARED_PAPERS = 2
DRAW_MIN_FRACTIONAL_WEIGHT = 0.018
DRAW_TOP_EDGES_PER_NODE = 2
LAYOUT_SEED = 20260510
MIN_GROUP_SIZE_FOR_COUNT = 3

ROLE_SPLIT_MAIN_IDS = {"2405.04434", "2412.19437", "2512.02556", "V4-PDF"}
R1_PAPER_ID = "2501.12948"
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


PALETTE = [
    "#6F35B6",
    "#E45CC8",
    "#2F9B72",
    "#2F6FB3",
    "#E08C31",
    "#9C67D9",
    "#4E7BBD",
    "#D65F5F",
    "#6B7280",
    "#2AA3A1",
    "#A05A2C",
    "#4F46E5",
]


SCENARIOS = [
    ("loose_2_0.006", 2, 0.006),
    ("balanced_2_0.012", 2, 0.012),
    ("mid_2_0.020", 2, 0.020),
    ("strict_3_0.030", 3, 0.030),
    ("top50_rule_3_0.080", 3, 0.080),
]


def configure_font() -> None:
    candidates = [
        NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyh.ttc"),
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


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.800, y: float = 0.022, scale: float = 0.92) -> None:
    if not JIAZI_LOGO.exists():
        return
    logo_ax = fig.add_axes([x, y, 0.155 * scale, 0.056 * scale])
    logo_ax.imshow(plt.imread(JIAZI_LOGO))
    logo_ax.set_axis_off()


def load_chinese_names() -> dict[str, str]:
    author_aug = BASE / "figures" / "author_frequency" / "fig3_high_frequency_authors_top25_data_augmented.csv"
    if not author_aug.exists():
        return AUTHOR_CHINESE_OVERRIDES.copy()
    aug = pd.read_csv(author_aug, encoding="utf-8-sig")
    if "author" not in aug.columns or "chinese_name" not in aug.columns:
        return AUTHOR_CHINESE_OVERRIDES.copy()
    names = {}
    for _, row in aug.iterrows():
        author = str(row.get("author", "")).strip()
        chinese = str(row.get("chinese_name", "")).strip()
        if author and chinese and chinese.lower() != "nan":
            names[author] = chinese
    confirmed = BASE / "figures" / "author_frequency" / "fig3_user_confirmed_author_updates.csv"
    if confirmed.exists():
        updates = pd.read_csv(confirmed, encoding="utf-8-sig")
        for _, row in updates.iterrows():
            author = str(row.get("author", "")).strip()
            chinese = str(row.get("chinese_name", "")).strip()
            if author and chinese and chinese.lower() != "nan":
                names[author] = chinese
    names.update(AUTHOR_CHINESE_OVERRIDES)
    return names


def display_author(author: str, chinese_names: dict[str, str]) -> str:
    chinese = chinese_names.get(author, "")
    return f"{author}\n{chinese}" if chinese else author


def inline_author(author: str, chinese_names: dict[str, str]) -> str:
    chinese = chinese_names.get(author, "")
    return f"{author}（{chinese}）" if chinese else author


def compact_author(author: str, chinese_names: dict[str, str]) -> str:
    return chinese_names.get(author, "") or author


def compact_author_for_chart(author: str, chinese_names: dict[str, str]) -> str:
    return compact_author(author, chinese_names)


def wrap_author_labels(labels: list[str]) -> str:
    labels = [label for label in labels if label]
    return "\n".join(labels)


def short_topic(topic: str) -> str:
    return (
        str(topic)
        .replace("主模型", "主线模型")
        .replace("数学/证明", "数学")
    )


def group_topic_summary(paper_authors: pd.DataFrame, members: list[str], max_topics: int = 2) -> str:
    rows = paper_authors[paper_authors["clean_author_name"].isin(members)]
    rows = rows.drop_duplicates(["clean_author_name", "paper_id", "coarse_topic"])
    counts = Counter(rows["coarse_topic"].astype(str))
    non_main = [(topic, count) for topic, count in counts.most_common() if topic != "主模型"]
    picked = non_main[:max_topics] if len(non_main) >= max_topics else counts.most_common(max_topics)
    return "、".join(short_topic(topic) for topic, _ in picked)


def group_work_summary(group_id: int, fallback: str) -> str:
    # Manual wording based on representative papers with the most members in each group.
    summaries = {
        1: "R1、V3.2、Coder",
        2: "VL、VL2、Janus、Cond. Memory",
        3: "Prover、Math、Coder、R1",
        4: "mHC、NSA、MoE、Insights V3",
        5: "R1、Reward Model、ESFT、DeepSeekMath",
        6: "DualPath、V3.2、V4",
    }
    return summaries.get(group_id, fallback)


def wrap_work_summary(summary: str) -> str:
    parts = str(summary).split("、")
    if len(parts) <= 3:
        return str(summary)
    mid = 2
    return "、".join(parts[:mid]) + "\n" + "、".join(parts[mid:])


def group_link_summary(stable_edges: pd.DataFrame, community_lookup: dict[str, int]) -> pd.DataFrame:
    links: dict[tuple[int, int], dict[str, float | int]] = {}
    for _, row in stable_edges.iterrows():
        source = row["source"]
        target = row["target"]
        g1 = community_lookup.get(source)
        g2 = community_lookup.get(target)
        if not g1 or not g2 or g1 == g2:
            continue
        key = tuple(sorted((int(g1), int(g2))))
        if key not in links:
            links[key] = {"source_group": key[0], "target_group": key[1], "weight": 0.0, "edge_count": 0}
        links[key]["weight"] = float(links[key]["weight"]) + float(row["fractional_weight"])
        links[key]["edge_count"] = int(links[key]["edge_count"]) + 1
    return pd.DataFrame(links.values()).sort_values(["weight", "edge_count"], ascending=[False, False])


def clean_authors(paper_authors: pd.DataFrame) -> pd.DataFrame:
    cleaned = paper_authors.copy()
    cleaned["clean_author_name"] = cleaned["clean_author_name"].fillna("").astype(str).str.strip()
    cleaned = cleaned[
        cleaned["clean_author_name"].ne("")
        & ~cleaned["clean_author_name"].isin(TEAM_NAMES)
    ].copy()
    return cleaned


def build_research_author_pool() -> pd.DataFrame:
    """Build the research-author pool for the full coauthor network.

    V2/V3/V3.2/V4 use only Research & Engineering authors from the role
    appendix. R1 is conservatively included as signature authors intersected
    with V3 Research & Engineering. Other unsplit papers keep the cleaned
    signature list, excluding team names and duplicate authors within the same
    paper.
    """

    raw = pd.read_csv(OUT / "paper_authors_clean.csv", encoding="utf-8-sig")
    papers = pd.read_csv(OUT / "papers_clean.csv", encoding="utf-8-sig")
    roles = pd.read_csv(OUT / "main_model_authors_with_roles.csv", encoding="utf-8-sig")

    raw = clean_authors(raw)
    raw_unsplit = raw[
        ~raw["paper_id"].astype(str).isin(ROLE_SPLIT_MAIN_IDS | {R1_PAPER_ID})
    ].copy()
    raw_unsplit["research_pool_source"] = "原始署名名单"

    meta_cols = [
        column
        for column in [
            "paper_id",
            "short_title",
            "year_month",
            "coarse_topic",
            "main_model_stage",
            "title",
            "source",
            "source_url",
        ]
        if column in papers.columns
    ]
    paper_meta = papers[meta_cols].drop_duplicates()

    role_mask = (
        roles["short_title"].isin(ROLE_SPLIT_RESEARCH_TITLES)
        & roles["is_research_engineering"].astype(str).str.upper().eq("TRUE")
    )
    role_research = roles.loc[
        role_mask,
        ["paper_id", "short_title", "clean_author_name", "departed_mark"],
    ].copy()
    role_research["clean_author_name"] = role_research["clean_author_name"].fillna("").astype(str).str.strip()
    role_research = role_research[role_research["clean_author_name"].ne("")]
    role_research = role_research[~role_research["clean_author_name"].isin(TEAM_NAMES)]
    role_research = role_research.merge(paper_meta, on=["paper_id", "short_title"], how="left")
    role_research["research_pool_source"] = "Research & Engineering"

    v3_re_names = set(
        roles.loc[
            roles["short_title"].eq("DeepSeek-V3 Technical Report")
            & roles["is_research_engineering"].astype(str).str.upper().eq("TRUE"),
            "clean_author_name",
        ]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    r1_research = raw[
        raw["paper_id"].astype(str).eq(R1_PAPER_ID)
        & raw["clean_author_name"].isin(v3_re_names)
    ].copy()
    r1_research["research_pool_source"] = "R1署名∩V3 R&E"

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
        if column not in r1_research.columns:
            r1_research[column] = ""

    pool = pd.concat([raw_unsplit[keep_cols], role_research[keep_cols], r1_research[keep_cols]], ignore_index=True)
    pool["clean_author_name"] = pool["clean_author_name"].fillna("").astype(str).str.strip()
    pool = pool[pool["clean_author_name"].ne("")]
    pool = pool[~pool["clean_author_name"].isin(TEAM_NAMES)]
    pool = pool.drop_duplicates(["paper_id", "clean_author_name"]).reset_index(drop=True)
    pool.to_csv(FIG / "fig4_all_author_research_author_pool.csv", index=False, encoding="utf-8-sig")
    return pool


def build_author_meta(paper_authors: pd.DataFrame) -> pd.DataFrame:
    topic_counts = (
        paper_authors.drop_duplicates(["clean_author_name", "paper_id", "coarse_topic"])
        .groupby("clean_author_name")["coarse_topic"]
        .nunique()
    )
    paper_counts = (
        paper_authors.drop_duplicates(["clean_author_name", "paper_id"])
        .groupby("clean_author_name")["paper_id"]
        .nunique()
    )
    first_seen = paper_authors.groupby("clean_author_name")["year_month"].min()
    last_seen = paper_authors.groupby("clean_author_name")["year_month"].max()
    meta = pd.DataFrame(
        {
            "author": paper_counts.index,
            "paper_count": paper_counts.values,
            "topic_count": topic_counts.reindex(paper_counts.index).fillna(0).astype(int).values,
            "first_seen": first_seen.reindex(paper_counts.index).values,
            "last_seen": last_seen.reindex(paper_counts.index).values,
        }
    )
    meta = meta.sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True]).reset_index(drop=True)
    meta["rank_by_papers"] = meta.index + 1
    return meta


def build_edges(paper_authors: pd.DataFrame) -> pd.DataFrame:
    edge_data: dict[tuple[str, str], dict[str, object]] = {}
    for paper_id, group in paper_authors.groupby("paper_id", sort=False):
        authors = sorted(set(group["clean_author_name"]))
        if len(authors) < 2:
            continue
        short_title = str(group["short_title"].iloc[0])
        topic = str(group["coarse_topic"].iloc[0])
        n_authors = len(authors)
        fractional = 1 / max(n_authors - 1, 1)

        for source, target in combinations(authors, 2):
            key = (source, target)
            if key not in edge_data:
                edge_data[key] = {
                    "source": source,
                    "target": target,
                    "shared_paper_count": 0,
                    "fractional_weight": 0.0,
                    "shared_papers": [],
                    "shared_topics": Counter(),
                }
            item = edge_data[key]
            item["shared_paper_count"] = int(item["shared_paper_count"]) + 1
            item["fractional_weight"] = float(item["fractional_weight"]) + fractional
            item["shared_papers"].append(short_title)
            item["shared_topics"][topic] += 1

    rows = []
    for item in edge_data.values():
        rows.append(
            {
                "source": item["source"],
                "target": item["target"],
                "shared_paper_count": int(item["shared_paper_count"]),
                "fractional_weight": round(float(item["fractional_weight"]), 6),
                "shared_papers": "；".join(item["shared_papers"]),
                "top_shared_topics": "、".join(topic for topic, _ in item["shared_topics"].most_common(3)),
            }
        )
    return pd.DataFrame(rows).sort_values(["shared_paper_count", "fractional_weight"], ascending=[False, False])


def filtered_edges(edges: pd.DataFrame, min_shared: int, min_weight: float) -> pd.DataFrame:
    return edges[
        (edges["shared_paper_count"].astype(int) >= min_shared)
        & (edges["fractional_weight"].astype(float) >= min_weight)
    ].copy()


def detect_communities(graph: nx.Graph) -> list[set[str]]:
    if graph.number_of_edges() == 0:
        return [{node} for node in graph.nodes()]
    try:
        communities = nx.community.louvain_communities(graph, weight="weight", seed=LAYOUT_SEED, resolution=1.08)
    except Exception:
        communities = nx.community.greedy_modularity_communities(graph, weight="weight")
    return [set(community) for community in communities]


def summarize_scenarios(all_authors: list[str], edges: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, min_shared, min_weight in SCENARIOS:
        selected = filtered_edges(edges, min_shared, min_weight)
        graph = nx.Graph()
        graph.add_nodes_from(all_authors)
        for _, row in selected.iterrows():
            graph.add_edge(row["source"], row["target"], weight=float(row["fractional_weight"]))
        communities = detect_communities(graph)
        sizes = sorted([len(c) for c in communities], reverse=True)
        non_singleton = [size for size in sizes if size >= 2]
        groups_ge3 = [size for size in sizes if size >= 3]
        groups_ge5 = [size for size in sizes if size >= 5]
        rows.append(
            {
                "scenario": name,
                "min_shared_papers": min_shared,
                "min_fractional_weight": min_weight,
                "stable_edges": len(selected),
                "authors_with_stable_edges": graph.number_of_nodes() - nx.number_of_isolates(graph),
                "isolated_authors": nx.number_of_isolates(graph),
                "communities_total_including_singletons": len(communities),
                "communities_ge3": len(groups_ge3),
                "communities_ge5": len(groups_ge5),
                "largest_community_size": sizes[0] if sizes else 0,
                "top_community_sizes": " / ".join(map(str, sizes[:12])),
            }
        )
    return pd.DataFrame(rows)


def choose_plot_edges(stable_edges: pd.DataFrame, authors: list[str]) -> pd.DataFrame:
    chosen: set[tuple[str, str]] = set()
    sorted_edges = stable_edges.sort_values(["fractional_weight", "shared_paper_count"], ascending=[False, False])
    for author in authors:
        incident = sorted_edges[(sorted_edges["source"].eq(author)) | (sorted_edges["target"].eq(author))].head(DRAW_TOP_EDGES_PER_NODE)
        for _, row in incident.iterrows():
            chosen.add(tuple(sorted((row["source"], row["target"]))))
    plot_edges = stable_edges[
        stable_edges.apply(lambda row: tuple(sorted((row["source"], row["target"]))) in chosen, axis=1)
    ].copy()
    return plot_edges


def make_layout(graph: nx.Graph, isolates: list[str]) -> dict[str, tuple[float, float]]:
    connected_nodes = [node for node in graph.nodes() if node not in isolates]
    connected_graph = graph.subgraph(connected_nodes).copy()
    pos: dict[str, tuple[float, float]] = {}
    if connected_graph.number_of_nodes():
        pos.update(nx.spring_layout(connected_graph, seed=LAYOUT_SEED, k=0.42, iterations=500, weight="weight", scale=4.6))

    if isolates:
        columns = max(20, int(math.sqrt(len(isolates)) * 2.2))
        start_x = -4.8
        start_y = -5.8
        gap_x = 0.42
        gap_y = 0.32
        for idx, author in enumerate(sorted(isolates)):
            col = idx % columns
            row = idx // columns
            pos[author] = (start_x + col * gap_x, start_y - row * gap_y)
    return pos


def plot_all_author_network(meta: pd.DataFrame, stable_edges: pd.DataFrame, community_summary: pd.DataFrame) -> None:
    all_authors = meta["author"].tolist()
    graph = nx.Graph()
    graph.add_nodes_from(all_authors)
    for _, row in stable_edges.iterrows():
        graph.add_edge(row["source"], row["target"], weight=float(row["fractional_weight"]), shared=int(row["shared_paper_count"]))

    communities = detect_communities(graph)
    community_rows = []
    for idx, community in enumerate(communities, start=1):
        members = sorted(community)
        group_meta = meta[meta["author"].isin(members)].copy()
        community_rows.append(
            {
                "community_id": idx,
                "member_count": len(members),
                "authors_with_edges": sum(1 for author in members if graph.degree(author) > 0),
                "avg_paper_count": round(float(group_meta["paper_count"].mean()), 2) if len(group_meta) else 0,
                "top_authors": "、".join(group_meta.sort_values(["paper_count", "topic_count"], ascending=[False, False])["author"].head(8)),
            }
        )
    community_data = pd.DataFrame(community_rows).sort_values(["member_count", "authors_with_edges"], ascending=[False, False]).reset_index(drop=True)
    community_data["display_group"] = community_data.index + 1
    community_data.to_csv(FIG / "fig4_all_author_communities_explore.csv", index=False, encoding="utf-8-sig")

    community_lookup = {}
    color_lookup = {}
    for _, row in community_data.iterrows():
        authors = set(communities[int(row["community_id"]) - 1])
        display_group = int(row["display_group"])
        for author in authors:
            community_lookup[author] = display_group
            if int(row["member_count"]) >= MIN_GROUP_SIZE_FOR_COUNT:
                color_lookup[author] = PALETTE[(display_group - 1) % len(PALETTE)]
            else:
                color_lookup[author] = "#D5D1DC"

    plot_edges = choose_plot_edges(stable_edges, [node for node in graph.nodes() if graph.degree(node) > 0])
    plot_edges.to_csv(FIG / "fig4_all_author_edges_plot_explore.csv", index=False, encoding="utf-8-sig")

    plot_graph = nx.Graph()
    plot_graph.add_nodes_from(all_authors)
    for _, row in plot_edges.iterrows():
        plot_graph.add_edge(row["source"], row["target"], weight=float(row["fractional_weight"]), shared=int(row["shared_paper_count"]))

    isolates = [node for node in graph.nodes() if graph.degree(node) == 0]
    pos = make_layout(graph, isolates)

    fig, ax = plt.subplots(figsize=(19, 22), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_axis_off()

    widths = [0.25 + min(float(data.get("weight", 0)) * 16, 2.1) for _, _, data in plot_graph.edges(data=True)]
    edge_colors = [to_rgba("#A9A5B3", 0.17) for _ in plot_graph.edges()]
    nx.draw_networkx_edges(plot_graph, pos, ax=ax, width=widths, edge_color=edge_colors)

    meta_lookup = meta.set_index("author").to_dict("index")
    node_sizes = []
    node_colors = []
    node_alpha = []
    for author in all_authors:
        paper_count = int(meta_lookup[author]["paper_count"])
        node_sizes.append(10 + paper_count * paper_count * 1.55)
        node_colors.append(color_lookup.get(author, "#D5D1DC"))
        node_alpha.append(0.78 if graph.degree(author) else 0.32)

    nx.draw_networkx_nodes(
        plot_graph,
        pos,
        nodelist=all_authors,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors="#FFFFFF",
        linewidths=0.35,
        alpha=0.88,
        ax=ax,
    )

    top_labels = meta[meta["author"].isin([node for node in graph.nodes() if graph.degree(node) > 0])]
    top_labels = top_labels.sort_values(["paper_count", "topic_count"], ascending=[False, False]).head(35)
    for _, row in top_labels.iterrows():
        author = row["author"]
        x, y = pos[author]
        degree = graph.degree(author)
        dx = 0.08 if x <= 0 else -0.08
        ha = "left" if x <= 0 else "right"
        ax.text(
            x + dx,
            y + 0.035,
            author,
            ha=ha,
            va="center",
            fontproperties=font_prop(7.0),
            color="#202020",
            bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "#E4E0EA", "alpha": 0.56, "linewidth": 0.35},
            zorder=10 + degree,
        )

    groups_ge3 = community_data[community_data["member_count"] >= MIN_GROUP_SIZE_FOR_COUNT]
    title = "DeepSeek 27篇论文研究作者共著网络（探索版）"
    subtitle = (
        f"{len(meta)}位研究作者入图；V2/V3/V3.2/V4仅纳入Research & Engineering；"
        f"稳定边=共同署名≥{DRAW_MIN_SHARED_PAPERS}篇且w≥{DRAW_MIN_FRACTIONAL_WEIGHT}；"
        f"形成{len(groups_ge3)}个至少{MIN_GROUP_SIZE_FOR_COUNT}人的共著小组，灰色小点为未形成稳定共著边作者"
    )
    ax.set_title(title + "\n" + subtitle, fontproperties=font_prop(18, "bold"), color="#15151A", pad=20)

    note = (
        "说明：位置与颜色用于探索共著小组，不代表真实组织架构；"
        f"为避免过密，图中仅绘制每位作者最强{DRAW_TOP_EDGES_PER_NODE}条稳定边。"
    )
    fig.text(0.05, 0.035, note, ha="left", va="center", fontproperties=font_prop(9.5), color="#555555")

    fig.savefig(FIG / "fig4_all_author_network_explore.png", bbox_inches="tight", dpi=220)
    fig.savefig(FIG / "fig4_all_author_network_explore.svg", bbox_inches="tight")
    plt.close(fig)


def build_formal_communities(meta: pd.DataFrame, stable_edges: pd.DataFrame) -> tuple[nx.Graph, pd.DataFrame, dict[str, int]]:
    graph = nx.Graph()
    graph.add_nodes_from(meta["author"].tolist())
    for _, row in stable_edges.iterrows():
        graph.add_edge(row["source"], row["target"], weight=float(row["fractional_weight"]), shared=int(row["shared_paper_count"]))

    communities = detect_communities(graph)
    rows = []
    for idx, community in enumerate(communities):
        members = set(community)
        group_meta = meta[meta["author"].isin(members)].copy()
        rows.append(
            {
                "community_idx": idx,
                "member_count": len(members),
                "authors_with_edges": sum(1 for author in members if graph.degree(author) > 0),
                "avg_paper_count": round(float(group_meta["paper_count"].mean()), 2) if len(group_meta) else 0,
                "top_authors": " / ".join(group_meta.sort_values(["paper_count", "topic_count"], ascending=[False, False])["author"].head(3)),
            }
        )
    community_data = pd.DataFrame(rows).sort_values(["member_count", "authors_with_edges"], ascending=[False, False]).reset_index(drop=True)
    community_data["display_group"] = community_data.index + 1
    community_data = community_data[community_data["member_count"] >= MIN_GROUP_SIZE_FOR_COUNT].copy()

    community_lookup: dict[str, int] = {}
    for _, row in community_data.iterrows():
        members = communities[int(row["community_idx"])]
        for author in members:
            community_lookup[author] = int(row["display_group"])
    return graph, community_data, community_lookup


def formal_node_size(paper_count: int) -> float:
    return 14 + int(paper_count) * int(paper_count) * 1.25


def clustered_layout(plot_graph: nx.Graph, community_data: pd.DataFrame, community_lookup: dict[str, int]) -> dict[str, tuple[float, float]]:
    centers = {
        1: (0.0, 0.10),
        2: (-2.72, 1.34),
        3: (2.72, 1.34),
        4: (-2.62, -2.04),
        5: (0.78, -2.14),
        6: (3.34, -2.10),
    }
    radii = {
        1: 1.38,
        2: 0.88,
        3: 0.82,
        4: 0.76,
        5: 0.58,
        6: 0.54,
    }
    pos: dict[str, tuple[float, float]] = {}
    golden_angle = math.pi * (3 - math.sqrt(5))
    for _, row in community_data.iterrows():
        group_id = int(row["display_group"])
        members = [author for author, group in community_lookup.items() if group == group_id and author in plot_graph]
        if not members:
            continue
        members = sorted(members, key=lambda author: plot_graph.degree(author), reverse=True)
        cx, cy = centers.get(group_id, (0, 0))
        radius = radii.get(group_id, 0.55)
        n = max(len(members), 1)
        for idx, author in enumerate(members):
            if idx == 0:
                x, y = 0.0, 0.0
            else:
                r = radius * math.sqrt(idx / n)
                angle = idx * golden_angle
                x, y = r * math.cos(angle), r * math.sin(angle)
            pos[author] = (cx + x, cy + y)
    return pos


def plot_all_author_network_formal(meta: pd.DataFrame, stable_edges: pd.DataFrame, paper_authors: pd.DataFrame) -> None:
    chinese_names = load_chinese_names()
    stable_graph, community_data, community_lookup = build_formal_communities(meta, stable_edges)

    stable_authors = [author for author in meta["author"] if stable_graph.degree(author) > 0 and author in community_lookup]
    tail_authors = [author for author in meta["author"] if stable_graph.degree(author) == 0]
    plot_graph = stable_graph.subgraph(stable_authors).copy()
    pos = clustered_layout(plot_graph, community_data, community_lookup)
    meta_lookup = meta.set_index("author").to_dict("index")

    group_letters = list("ABCDEF")
    group_rows = []
    for idx, row in community_data.head(6).reset_index(drop=True).iterrows():
        group_id = int(row["display_group"])
        members = [author for author in stable_authors if community_lookup.get(author) == group_id]
        group_meta = meta[meta["author"].isin(members)].sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True])
        reps = group_meta["author"].head(4).tolist()
        fallback_summary = group_topic_summary(paper_authors, members)
        group_rows.append(
            {
                "display_group": group_id,
                "group_letter": group_letters[idx],
                "member_count": int(row["member_count"]),
                "direction_summary": group_work_summary(group_id, fallback_summary),
                "top_authors": " / ".join(reps),
                "top_authors_cn": " / ".join(inline_author(author, chinese_names) for author in reps),
                "top_authors_compact": " / ".join(compact_author(author, chinese_names) for author in reps),
                "top_authors_chart_label": " / ".join(compact_author_for_chart(author, chinese_names) for author in reps),
                "context_note": "；".join(
                    f"{compact_author(author, chinese_names)}：{AUTHOR_CONTEXT_LABELS[author]}"
                    for author in reps
                    if author in AUTHOR_CONTEXT_LABELS
                ),
            }
        )
    group_summary = pd.DataFrame(group_rows)
    group_summary.to_csv(FIG / "fig4_all_author_communities_formal_v13.csv", index=False, encoding="utf-8-sig")

    group_links = group_link_summary(stable_edges, community_lookup)
    group_links.to_csv(FIG / "fig4_all_author_group_links_formal_v13.csv", index=False, encoding="utf-8-sig")
    largest_group_count = int(group_summary["member_count"].max()) if len(group_summary) else 0

    fig = plt.figure(figsize=(8.4, 11.2), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    purple = "#6F35B6"
    title_color = "#15151A"
    footer_color = "#555555"

    fig.add_artist(Rectangle((0.052, 0.922), 0.006, 0.058, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(
        0.070,
        0.960,
        "DeepSeek论文里的研究作者合作网络",
        ha="left",
        va="center",
        fontproperties=font_prop(21.6, "bold"),
        color=title_color,
    )
    fig.text(
        0.070,
        0.928,
        f"{len(meta)}位去重研究作者中，{len(stable_authors)}位进入稳定合作网络；形成{len(community_data)}个至少3人的合作小组。",
        ha="left",
        va="center",
        fontproperties=font_prop(14.8),
        color="#2F2F36",
    )
    fig.text(
        0.070,
        0.902,
        f"最大合作组{largest_group_count}人，其余小组覆盖多模态、系统效率、数学/推理等方向；{len(tail_authors)}位研究作者处于长尾。",
        ha="left",
        va="center",
        fontproperties=font_prop(13.8),
        color="#555555",
    )

    fig.text(
        0.070,
        0.880,
        "图中的“合作小组”基于研究作者池的论文署名关系识别，不代表真实组织团队。",
        ha="left",
        va="center",
        fontproperties=font_prop(9.6),
        color="#666666",
    )

    metric_y = 0.824
    metrics = [
        ("去重研究作者", f"{len(meta)}人"),
        ("进入稳定合作网络", f"{len(stable_authors)}人"),
        ("论文合作小组", f"{len(community_data)}个"),
        ("长尾研究作者", f"{len(tail_authors)}人"),
    ]
    for idx, (label, value) in enumerate(metrics):
        x = 0.070 + idx * 0.222
        fig.text(x, metric_y, value, ha="left", va="center", fontproperties=font_prop(18.4, "bold"), color=purple)
        fig.text(x, metric_y - 0.023, label, ha="left", va="center", fontproperties=font_prop(9.2), color="#555555")

    fig.text(0.060, 0.748, f"{len(stable_authors)}位研究作者的合作地图：{len(community_data)}个小组如何连接", ha="left", va="center", fontproperties=font_prop(16.6, "bold"), color=title_color)
    fig.text(0.060, 0.723, "每个圆点代表一位研究作者，颜色表示不同合作小组，圆点越大代表参与论文越多；灰线表示小组之间更强的跨组合作。", ha="left", va="center", fontproperties=font_prop(10.6), color="#555555")

    ax = fig.add_axes([0.050, 0.232, 0.900, 0.475])
    ax.set_axis_off()
    ax.set_facecolor("#FFFFFF")

    centers = {
        1: (0.0, 0.10),
        2: (-2.72, 1.34),
        3: (2.72, 1.34),
        4: (-2.62, -2.04),
        5: (0.78, -2.14),
            6: (3.34, -2.10),
    }
    radii = {
        1: 1.38,
        2: 0.88,
        3: 0.82,
        4: 0.76,
        5: 0.58,
        6: 0.54,
    }

    # Draw aggregate cross-group links instead of hundreds of author-level edges.
    top_links = group_links.head(8)
    max_link_weight = float(top_links["weight"].max()) if len(top_links) else 1.0
    for _, link in top_links.iterrows():
        g1 = int(link["source_group"])
        g2 = int(link["target_group"])
        if g1 not in centers or g2 not in centers:
            continue
        rad = 0.12 if (g1 + g2) % 2 else -0.12
        patch = FancyArrowPatch(
            centers[g1],
            centers[g2],
            arrowstyle="-",
            connectionstyle=f"arc3,rad={rad}",
            linewidth=0.7 + 3.2 * float(link["weight"]) / max_link_weight,
            color=to_rgba("#8E899B", 0.16),
            zorder=1,
        )
        ax.add_patch(patch)

    for _, row in group_summary.iterrows():
        group_id = int(row["display_group"])
        letter = row["group_letter"]
        color = PALETTE[(group_id - 1) % len(PALETTE)]
        cx, cy = centers[group_id]
        radius = radii[group_id]
        circle_radius = radius * 1.18
        title_y = cy + circle_radius + 0.36
        work_y = cy + circle_radius + 0.10
        ax.add_patch(
            Circle(
                (cx, cy),
                radius=circle_radius,
                facecolor=to_rgba(color, 0.055),
                edgecolor=to_rgba(color, 0.24),
                linewidth=0.9,
                zorder=0,
            )
        )
        ax.text(
            cx,
            title_y,
            f"小组{letter}｜{int(row['member_count'])}人",
            ha="center",
            va="center",
            fontproperties=font_prop(13.0, "bold"),
            color=color,
            zorder=6,
        )
        ax.text(
            cx,
            work_y,
            ("主要覆盖：\n" + str(row["direction_summary"])) if group_id >= 5 else ("主要覆盖：" + wrap_work_summary(str(row["direction_summary"])).replace("\n", "、")),
            ha="center",
            va="center",
            fontproperties=font_prop(10.6 if group_id >= 5 else 11.2, "bold"),
            color="#3F3F46",
            linespacing=1.12,
            bbox={"boxstyle": "round,pad=0.14", "facecolor": "#FFFFFF", "edgecolor": "#E8E3EE", "linewidth": 0.35, "alpha": 0.82},
            zorder=7,
        )
        compact_names = str(row["top_authors_chart_label"]).split(" / ")
        author_names = wrap_author_labels(compact_names[:4])
        author_y = cy - circle_radius * (0.06 if group_id <= 4 else 0.10)
        ax.text(
            cx,
            author_y,
            "高频作者：\n" + author_names,
            ha="center",
            va="center",
            fontproperties=font_prop(10.6 if group_id <= 4 else 9.4),
            color="#2F2F36",
            linespacing=1.16,
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "#FFFFFF", "edgecolor": "#E8E3EE", "linewidth": 0.35, "alpha": 0.74},
            zorder=7,
        )
    for _, row in group_summary.iterrows():
        group_id = int(row["display_group"])
        color = PALETTE[(group_id - 1) % len(PALETTE)]
        members = [author for author in stable_authors if community_lookup.get(author) == group_id]
        members = sorted(members, key=lambda author: int(meta_lookup[author]["paper_count"]))
        ax.scatter(
            [pos[author][0] for author in members],
            [pos[author][1] for author in members],
            s=[formal_node_size(int(meta_lookup[author]["paper_count"])) for author in members],
            color=color,
            edgecolors="#FFFFFF",
            linewidths=0.42,
            alpha=0.86,
            zorder=3,
        )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-4.65, 4.75)
    ax.set_ylim(-3.08, 3.02)

    tail_ax = fig.add_axes([0.058, 0.125, 0.884, 0.070])
    tail_ax.set_axis_off()
    tail_ax.text(0.000, 0.950, f"长尾研究作者：{len(tail_authors)}位未进入稳定合作网络", ha="left", va="top", transform=tail_ax.transAxes, fontproperties=font_prop(10.4, "bold"), color=title_color)
    cols = 49
    for idx, author in enumerate(tail_authors):
        col = idx % cols
        row = idx // cols
        x = 0.004 + col * (0.985 / (cols - 1))
        y = 0.500 - row * 0.135
        tail_ax.scatter([x], [y], s=9 + int(meta_lookup[author]["paper_count"]) * 2.5, color="#CFCBD6", alpha=0.72, transform=tail_ax.transAxes, linewidths=0)

    fig.add_artist(Rectangle((0.052, 0.108), 0.896, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(7.45)
    fig.text(0.052, 0.091, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.075, "说明：合作关系基于论文署名，不代表真实组织架构、贡献大小、当前任职或汇报关系", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.059, "口径：V2/V3/V3.2/V4仅纳入Research & Engineering；其他未拆分角色论文使用原始署名并剔除团队名。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.043, "定义：s(i,j)为共同署名论文数；稳定边=s(i,j)≥2且w(i,j)≥0.012；稳定合作者=d_s(i)≥1，长尾研究作者=d_s(i)=0", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.027, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    draw_jiazi_logo(fig, x=0.807, y=0.030, scale=0.84)

    fig.savefig(FIG / "fig4_all_author_network_formal_v13.png", facecolor=fig.get_facecolor(), dpi=430)
    fig.savefig(FIG / "fig4_all_author_network_formal_v13.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def wrap_card_items(text: str, first_line_count: int = 3) -> str:
    parts = [part.strip() for part in str(text).split("、") if part.strip()]
    if len(parts) <= first_line_count:
        return "、".join(parts)
    return "、".join(parts[:first_line_count]) + "\n" + "、".join(parts[first_line_count:])


def tint_color(color: str, strength: float = 0.055) -> tuple[float, float, float, float]:
    r, g, b, _ = to_rgba(color)
    return (1 - (1 - r) * strength, 1 - (1 - g) * strength, 1 - (1 - b) * strength, 1.0)


def wrap_card_authors(authors: str, group_id: int) -> str:
    names = [name.strip() for name in str(authors).split(" / ") if name.strip()]
    if not names:
        return ""
    if group_id == 6:
        return "\n".join(names[:2])
    if group_id == 1 and len(names) >= 3:
        return " / ".join(names[:2]) + "\n" + names[2]
    if len(names) >= 3:
        return " / ".join(names[:2]) + "\n" + names[2]
    return "\n".join(names)


def wrap_group_coverage(coverage: str, group_id: int) -> str:
    split_after = {
        2: 3,
        3: 2,
        4: 3,
        5: 2,
    }.get(group_id, 3)
    return wrap_card_items(coverage, split_after)


def draw_unit_grid(
    ax: plt.Axes,
    count: int,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str,
    cols: int,
    size: float,
    alpha: float = 0.82,
) -> None:
    if count <= 0:
        return
    rows = math.ceil(count / cols)
    x_pad = w * 0.08
    y_pad = h * 0.10
    x_step = (w - 2 * x_pad) / max(cols - 1, 1)
    y_step = (h - 2 * y_pad) / max(rows - 1, 1)
    xs: list[float] = []
    ys: list[float] = []
    for idx in range(count):
        row = idx // cols
        col = idx % cols
        xs.append(x + x_pad + col * x_step)
        ys.append(y + h - y_pad - row * y_step)
    ax.scatter(xs, ys, s=size, color=color, alpha=alpha, linewidths=0, transform=ax.transAxes, zorder=7)


def draw_group_card(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    letter: str,
    count: int,
    coverage: str,
    authors: str,
    color: str,
    dot_cols: int,
    dot_size: float,
    group_id: int,
) -> None:
    is_large = group_id == 1
    is_small = w < 0.32
    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.010,rounding_size=0.020",
        transform=ax.transAxes,
        facecolor=tint_color(color, 0.050),
        edgecolor=to_rgba(color, 0.30),
        linewidth=1.0,
        zorder=5,
    )
    ax.add_patch(card)
    ax.text(
        x + 0.035 * w,
        y + h - 0.070 * h,
        f"小组{letter}｜{count}人",
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontproperties=font_prop(13.4 if is_large else 12.2, "bold"),
        color=color,
        zorder=8,
    )
    ax.text(
        x + 0.035 * w,
        y + h - 0.205 * h,
        "覆盖：" + wrap_group_coverage(coverage, group_id),
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontproperties=font_prop(10.4 if is_large else 9.4, "bold"),
        color="#303039",
        linespacing=1.16,
        zorder=8,
    )
    ax.text(
        x + 0.035 * w,
        y + h - (0.380 if is_large else 0.415) * h,
        "高频作者：" + wrap_card_authors(authors, group_id),
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontproperties=font_prop(9.4 if is_large else (8.5 if is_small else 8.8)),
        color="#303039",
        linespacing=1.14,
        zorder=8,
    )
    dot_y = y + 0.040 * h
    dot_h = h * (0.340 if is_small else 0.375)
    draw_unit_grid(ax, count, x + 0.020 * w, dot_y, w * 0.960, dot_h, color, dot_cols, dot_size)


def plot_all_author_network_cards(meta: pd.DataFrame, stable_edges: pd.DataFrame, paper_authors: pd.DataFrame) -> None:
    chinese_names = load_chinese_names()
    stable_graph, community_data, community_lookup = build_formal_communities(meta, stable_edges)

    stable_authors = [author for author in meta["author"] if stable_graph.degree(author) > 0 and author in community_lookup]
    tail_authors = [author for author in meta["author"] if stable_graph.degree(author) == 0]
    group_letters = list("ABCDEF")
    group_rows = []
    for idx, row in community_data.head(6).reset_index(drop=True).iterrows():
        group_id = int(row["display_group"])
        members = [author for author in stable_authors if community_lookup.get(author) == group_id]
        group_meta = meta[meta["author"].isin(members)].sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True])
        reps = group_meta["author"].head(3).tolist()
        fallback_summary = group_topic_summary(paper_authors, members)
        group_rows.append(
            {
                "display_group": group_id,
                "group_letter": group_letters[idx],
                "member_count": int(row["member_count"]),
                "direction_summary": group_work_summary(group_id, fallback_summary),
                "top_authors": " / ".join(reps),
                "top_authors_cn": " / ".join(inline_author(author, chinese_names) for author in reps),
                "top_authors_compact": " / ".join(compact_author_for_chart(author, chinese_names) for author in reps),
            }
        )
    group_summary = pd.DataFrame(group_rows)
    group_summary.to_csv(FIG / "fig4_all_author_communities_formal_v16.csv", index=False, encoding="utf-8-sig")

    group_links = group_link_summary(stable_edges, community_lookup)
    group_links.to_csv(FIG / "fig4_all_author_group_links_formal_v16.csv", index=False, encoding="utf-8-sig")
    largest_group_count = int(group_summary["member_count"].max()) if len(group_summary) else 0

    fig = plt.figure(figsize=(8.4, 11.2), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    purple = "#6F35B6"
    title_color = "#15151A"
    footer_color = "#555555"

    fig.add_artist(Rectangle((0.052, 0.925), 0.006, 0.055, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(
        0.070,
        0.960,
        "DeepSeek论文里的研究作者合作网络",
        ha="left",
        va="center",
        fontproperties=font_prop(21.4, "bold"),
        color=title_color,
    )
    fig.text(
        0.070,
        0.930,
        f"{len(meta)}位去重研究作者中，{len(stable_authors)}位进入稳定合作网络；形成{len(community_data)}个至少3人的合作小组。",
        ha="left",
        va="center",
        fontproperties=font_prop(14.0),
        color="#2F2F36",
    )
    fig.text(
        0.070,
        0.906,
        f"最大合作组{largest_group_count}人，主线论文仍把一批高频研究作者连接成主干合作群。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.9),
        color="#4F4F59",
    )
    fig.text(
        0.070,
        0.884,
        f"其余小组覆盖多模态、系统效率、数学/推理等方向，另有{len(tail_authors)}位研究作者处于长尾。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.9),
        color="#4F4F59",
    )
    fig.text(
        0.070,
        0.864,
        "图中的“合作小组”基于研究作者池的论文署名关系识别，不代表真实组织团队。",
        ha="left",
        va="center",
        fontproperties=font_prop(9.5),
        color="#666666",
    )

    metric_y = 0.815
    metrics = [
        ("去重研究作者", f"{len(meta)}人"),
        ("进入稳定合作网络", f"{len(stable_authors)}人"),
        ("论文合作小组", f"{len(community_data)}个"),
        ("长尾研究作者", f"{len(tail_authors)}人"),
    ]
    for idx, (label, value) in enumerate(metrics):
        x = 0.070 + idx * 0.222
        fig.text(x, metric_y, value, ha="left", va="center", fontproperties=font_prop(19.2, "bold"), color=purple)
        fig.text(x, metric_y - 0.024, label, ha="left", va="center", fontproperties=font_prop(9.2), color="#555555")

    fig.text(0.060, 0.746, f"{len(stable_authors)}位研究作者的合作地图：{len(community_data)}个小组如何连接", ha="left", va="center", fontproperties=font_prop(17.0, "bold"), color=title_color)
    fig.text(0.060, 0.722, "每个点代表一位研究作者；颜色区分合作小组；灰线表示较强跨组合作，线越粗关系越强。", ha="left", va="center", fontproperties=font_prop(10.8), color="#555555")

    ax = fig.add_axes([0.050, 0.235, 0.900, 0.465])
    ax.set_axis_off()
    ax.set_facecolor("#FFFFFF")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    card_layout = {
        1: (0.170, 0.365, 0.660, 0.300, 17, 7.8),
        2: (0.025, 0.690, 0.440, 0.260, 7, 12.0),
        3: (0.535, 0.690, 0.440, 0.260, 7, 12.0),
        4: (0.025, 0.060, 0.300, 0.270, 7, 13.5),
        5: (0.350, 0.060, 0.300, 0.270, 5, 16.0),
        6: (0.675, 0.060, 0.300, 0.270, 3, 18.0),
    }

    centers = {group_id: (x + w / 2, y + h / 2) for group_id, (x, y, w, h, _, _) in card_layout.items()}
    top_links = group_links.head(8)
    max_link_weight = float(top_links["weight"].max()) if len(top_links) else 1.0
    for _, link in top_links.iterrows():
        g1 = int(link["source_group"])
        g2 = int(link["target_group"])
        if g1 not in centers or g2 not in centers:
            continue
        rad = 0.16 if (g1 + g2) % 2 else -0.16
        patch = FancyArrowPatch(
            centers[g1],
            centers[g2],
            arrowstyle="-",
            connectionstyle=f"arc3,rad={rad}",
            linewidth=0.8 + 3.0 * float(link["weight"]) / max_link_weight,
            color=to_rgba("#8E899B", 0.18),
            transform=ax.transAxes,
            zorder=1,
        )
        ax.add_patch(patch)

    for _, row in group_summary.iterrows():
        group_id = int(row["display_group"])
        x, y, w, h, dot_cols, dot_size = card_layout[group_id]
        draw_group_card(
            ax,
            x=x,
            y=y,
            w=w,
            h=h,
            letter=str(row["group_letter"]),
            count=int(row["member_count"]),
            coverage=str(row["direction_summary"]),
            authors=str(row["top_authors_compact"]),
            color=PALETTE[(group_id - 1) % len(PALETTE)],
            dot_cols=int(dot_cols),
            dot_size=float(dot_size),
            group_id=group_id,
        )

    tail_ax = fig.add_axes([0.058, 0.122, 0.884, 0.075])
    tail_ax.set_axis_off()
    tail_box = FancyBboxPatch(
        (0.000, 0.020),
        1.000,
        0.900,
        boxstyle="round,pad=0.006,rounding_size=0.025",
        transform=tail_ax.transAxes,
        facecolor="#F7F6FA",
        edgecolor="#DEDAE6",
        linewidth=0.8,
    )
    tail_ax.add_patch(tail_box)
    tail_ax.text(0.025, 0.640, f"长尾研究作者｜{len(tail_authors)}人", ha="left", va="center", transform=tail_ax.transAxes, fontproperties=font_prop(12.6, "bold"), color=title_color)
    tail_ax.text(0.025, 0.330, "未进入稳定合作网络", ha="left", va="center", transform=tail_ax.transAxes, fontproperties=font_prop(10.4), color="#555555")
    draw_unit_grid(tail_ax, len(tail_authors), 0.300, 0.170, 0.665, 0.650, "#CFCBD6", cols=39, size=8.0, alpha=0.70)

    fig.add_artist(Rectangle((0.052, 0.108), 0.896, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(8.15)
    fig.text(0.052, 0.088, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.071, "口径：V2/V3/V3.2/V4仅纳入Research & Engineering；其他未拆分角色论文使用原始署名并剔除团队名。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.054, "加权方式：w(i,j)=Σ1/(N_p-1)，N_p为论文去重作者数。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.037, "说明：图中的合作小组不代表真实组织架构、贡献大小或汇报关系。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.020, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    draw_jiazi_logo(fig, x=0.807, y=0.027, scale=0.84)

    fig.savefig(FIG / "fig4_all_author_network_formal_v16.png", facecolor=fig.get_facecolor(), dpi=430)
    fig.savefig(FIG / "fig4_all_author_network_formal_v16.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


GROUP_LABELS_V17 = {
    1: ("基模大兵团", "R1 / V3 / V4 主干"),
    2: ("系统效率小队", "Infra / NSA / 模型维稳"),
    3: ("数学与推理小队", "Prover / Math / 推理泛化"),
    4: ("多模态小队", "视觉 / Janus 系列"),
    5: ("缓存与系统小队", "DualPath / 小型系统优化"),
    6: ("垂类数学小队", "DeepSeekMath-V2"),
    7: ("OCR视觉小队", "复杂文档视觉理解"),
}


def wrap_v17_authors(authors: str) -> str:
    names = [name.strip() for name in str(authors).split(" / ") if name.strip()]
    if not names:
        return ""
    has_romanized = any(any(("A" <= char <= "Z") or ("a" <= char <= "z") for char in name) for name in names)
    keep = 2 if has_romanized else 3
    return " / ".join(names[:keep])


def draw_group_card_v17(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    letter: str,
    group_name: str,
    count: int,
    coverage: str,
    authors: str,
    color: str,
    dot_cols: int,
    dot_size: float,
    group_id: int,
) -> None:
    is_large = group_id == 1
    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.010,rounding_size=0.020",
        transform=ax.transAxes,
        facecolor=tint_color(color, 0.050),
        edgecolor=to_rgba(color, 0.30),
        linewidth=1.0,
        zorder=5,
    )
    ax.add_patch(card)
    ax.text(
        x + 0.035 * w,
        y + h - 0.105 * h,
        f"小组{letter} | {group_name} {count}人",
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontproperties=font_prop(12.8 if is_large else 10.9, "bold"),
        color=color,
        zorder=8,
    )
    ax.text(
        x + 0.035 * w,
        y + h - (0.250 if is_large else 0.280) * h,
        coverage,
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontproperties=font_prop(9.8 if is_large else 8.8, "bold"),
        color="#3F3F46",
        linespacing=1.12,
        zorder=8,
    )
    ax.text(
        x + 0.035 * w,
        y + h - (0.390 if is_large else 0.445) * h,
        "代表作者：" + wrap_v17_authors(authors),
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontproperties=font_prop(8.8 if is_large else 7.9),
        color="#303039",
        linespacing=1.14,
        zorder=8,
    )
    dot_y = y + 0.045 * h
    dot_h = h * (0.380 if is_large else 0.300)
    draw_unit_grid(ax, count, x + 0.020 * w, dot_y, w * 0.960, dot_h, color, dot_cols, dot_size)


def plot_all_author_network_cards_v17(meta: pd.DataFrame, stable_edges: pd.DataFrame, paper_authors: pd.DataFrame) -> None:
    chinese_names = load_chinese_names()
    stable_graph, community_data, community_lookup = build_formal_communities(meta, stable_edges)

    reference_nodes_path = BASE / "figures" / "coauthor_network" / "fig4_deepseek_research_matrix_network_v1_hub_labels_nodes.csv"
    if reference_nodes_path.exists():
        reference_nodes = pd.read_csv(reference_nodes_path, encoding="utf-8-sig")
        reference_nodes = reference_nodes[reference_nodes["author"].isin(meta["author"])].copy()
        reference_nodes["community"] = reference_nodes["community"].astype(int)
        community_lookup = dict(zip(reference_nodes["author"], reference_nodes["community"]))
        community_data = (
            reference_nodes.groupby("community", as_index=False)["author"]
            .nunique()
            .rename(columns={"community": "display_group", "author": "member_count"})
            .sort_values("display_group")
            .reset_index(drop=True)
        )
        stable_author_set = set(reference_nodes["author"])
        stable_author_count = len(stable_author_set)
        stable_authors = [author for author in meta["author"] if author in stable_author_set]
        tail_authors = [author for author in meta["author"] if author not in stable_author_set]
    else:
        stable_author_count = sum(1 for author in meta["author"] if stable_graph.degree(author) > 0)
        stable_authors = [author for author in meta["author"] if stable_graph.degree(author) > 0 and author in community_lookup]
        tail_authors = [author for author in meta["author"] if stable_graph.degree(author) == 0]
    meta_lookup = meta.set_index("author").to_dict("index")

    group_letters = list("ABCDEFG")
    group_rows = []
    for idx, row in community_data.head(7).reset_index(drop=True).iterrows():
        group_id = int(row["display_group"])
        members = [author for author in stable_authors if community_lookup.get(author) == group_id]
        group_meta = meta[meta["author"].isin(members)].sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True])
        reps = group_meta["author"].head(3).tolist()
        group_name, direction = GROUP_LABELS_V17.get(group_id, (f"合作小组{group_id}", group_topic_summary(paper_authors, members)))
        group_rows.append(
            {
                "display_group": group_id,
                "group_letter": group_letters[idx],
                "group_name": group_name,
                "member_count": int(row["member_count"]),
                "direction_summary": direction,
                "top_authors": " / ".join(reps),
                "top_authors_cn": " / ".join(inline_author(author, chinese_names) for author in reps),
                "top_authors_compact": " / ".join(compact_author_for_chart(author, chinese_names) for author in reps),
            }
        )
    group_summary = pd.DataFrame(group_rows)
    group_summary.to_csv(FIG / "fig4_all_author_communities_formal_v17.csv", index=False, encoding="utf-8-sig")

    group_links = group_link_summary(stable_edges, community_lookup)
    group_links.to_csv(FIG / "fig4_all_author_group_links_formal_v17.csv", index=False, encoding="utf-8-sig")
    largest_group_count = int(group_summary["member_count"].max()) if len(group_summary) else 0

    fig = plt.figure(figsize=(8.4, 11.2), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    purple = "#6F35B6"
    title_color = "#15151A"
    footer_color = "#555555"

    fig.add_artist(Rectangle((0.052, 0.925), 0.006, 0.055, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.070, 0.960, "DeepSeek论文里的研发作者合作网络", ha="left", va="center", fontproperties=font_prop(21.4, "bold"), color=title_color)
    fig.text(
        0.070,
        0.930,
        f"{len(meta)}位去重研发作者中，{stable_author_count}位进入稳定合作网络；形成{len(community_data)}个至少3人的合作小组。",
        ha="left",
        va="center",
        fontproperties=font_prop(14.0),
        color="#2F2F36",
    )
    fig.text(
        0.070,
        0.906,
        f"最大合作组{largest_group_count}人，主线论文仍把一批高频研发作者连接成主干合作群。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.9),
        color="#4F4F59",
    )
    fig.text(
        0.070,
        0.884,
        f"其余小组覆盖多模态、系统效率、数学/推理等方向，另有{len(tail_authors)}位长尾研发作者。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.9),
        color="#4F4F59",
    )
    fig.text(
        0.070,
        0.864,
        "图中的“合作小组”基于研发作者池的论文署名关系识别，不代表真实组织团队。",
        ha="left",
        va="center",
        fontproperties=font_prop(9.5),
        color="#666666",
    )

    metric_y = 0.815
    metrics = [
        ("去重研发作者", f"{len(meta)}人"),
        ("进入稳定合作网络", f"{stable_author_count}人"),
        ("论文合作小组", f"{len(community_data)}个"),
        ("长尾研发作者", f"{len(tail_authors)}人"),
    ]
    for idx, (label, value) in enumerate(metrics):
        x = 0.070 + idx * 0.222
        fig.text(x, metric_y, value, ha="left", va="center", fontproperties=font_prop(19.2, "bold"), color=purple)
        fig.text(x, metric_y - 0.024, label, ha="left", va="center", fontproperties=font_prop(9.2), color="#555555")

    fig.text(0.060, 0.746, f"{stable_author_count}位研发作者的合作地图：{len(community_data)}个小组如何连接", ha="left", va="center", fontproperties=font_prop(17.0, "bold"), color=title_color)
    fig.text(0.060, 0.722, "每张卡片代表一个稳定合作小组；卡片内小点对应组内研发作者，灰线表示较强跨组合作。", ha="left", va="center", fontproperties=font_prop(10.8), color="#555555")

    ax = fig.add_axes([0.050, 0.235, 0.900, 0.465])
    ax.set_axis_off()
    ax.set_facecolor("#FFFFFF")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    card_layout = {
        1: (0.130, 0.350, 0.740, 0.290, 19, 6.2),
        2: (0.025, 0.690, 0.300, 0.260, 7, 11.2),
        3: (0.350, 0.690, 0.300, 0.260, 7, 11.5),
        4: (0.675, 0.690, 0.300, 0.260, 5, 12.0),
        5: (0.025, 0.060, 0.300, 0.250, 5, 13.2),
        6: (0.350, 0.060, 0.300, 0.250, 3, 16.0),
        7: (0.675, 0.060, 0.300, 0.250, 3, 18.5),
    }

    centers = {group_id: (x + w / 2, y + h / 2) for group_id, (x, y, w, h, _, _) in card_layout.items()}
    top_links = group_links.head(10)
    max_link_weight = float(top_links["weight"].max()) if len(top_links) else 1.0
    for _, link in top_links.iterrows():
        g1 = int(link["source_group"])
        g2 = int(link["target_group"])
        if g1 not in centers or g2 not in centers:
            continue
        rad = 0.14 if (g1 + g2) % 2 else -0.14
        patch = FancyArrowPatch(
            centers[g1],
            centers[g2],
            arrowstyle="-",
            connectionstyle=f"arc3,rad={rad}",
            linewidth=0.7 + 3.2 * float(link["weight"]) / max_link_weight,
            color=to_rgba("#8E899B", 0.16),
            transform=ax.transAxes,
            zorder=1,
        )
        ax.add_patch(patch)

    for _, row in group_summary.iterrows():
        group_id = int(row["display_group"])
        x, y, w, h, dot_cols, dot_size = card_layout[group_id]
        draw_group_card_v17(
            ax,
            x=x,
            y=y,
            w=w,
            h=h,
            letter=str(row["group_letter"]),
            group_name=str(row["group_name"]),
            count=int(row["member_count"]),
            coverage=str(row["direction_summary"]),
            authors=str(row["top_authors_compact"]),
            color=PALETTE[(group_id - 1) % len(PALETTE)],
            dot_cols=int(dot_cols),
            dot_size=float(dot_size),
            group_id=group_id,
        )

    tail_ax = fig.add_axes([0.058, 0.122, 0.884, 0.075])
    tail_ax.set_axis_off()
    tail_box = FancyBboxPatch(
        (0.000, 0.020),
        1.000,
        0.900,
        boxstyle="round,pad=0.006,rounding_size=0.025",
        transform=tail_ax.transAxes,
        facecolor="#F7F6FA",
        edgecolor="#DEDAE6",
        linewidth=0.8,
    )
    tail_ax.add_patch(tail_box)
    tail_ax.text(0.025, 0.640, f"长尾研发作者 | {len(tail_authors)}人", ha="left", va="center", transform=tail_ax.transAxes, fontproperties=font_prop(12.8, "bold"), color=title_color)
    tail_ax.text(0.025, 0.330, "未进入稳定合作网络", ha="left", va="center", transform=tail_ax.transAxes, fontproperties=font_prop(10.6), color="#555555")

    fig.add_artist(Rectangle((0.052, 0.108), 0.896, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(7.20)
    fig.text(0.052, 0.092, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.076, "口径：V2/V3/V3.2/V4仅取Research & Engineering名单；R1按“R1署名∩V3 R&E”保守纳入；LLM及其他未拆角色论文使用原始署名并剔除团队名。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.060, "口径补充：Research & Engineering同时包含研究和工程角色，本文统称为“研发作者”。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.044, f"算法：稳定边=共同署名≥{DRAW_MIN_SHARED_PAPERS}篇且w≥{DRAW_MIN_FRACTIONAL_WEIGHT}，并保留每位作者最强{DRAW_TOP_EDGES_PER_NODE}条稳定边；在稳定合作网络上用Louvain聚类识别小组。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.028, "说明：图中的合作小组不代表真实组织架构、贡献大小、当前任职或汇报关系。", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(0.052, 0.012, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    draw_jiazi_logo(fig, x=0.807, y=0.022, scale=0.84)

    fig.savefig(FIG / "fig4_all_author_network_formal_v17.png", facecolor=fig.get_facecolor(), dpi=430)
    fig.savefig(FIG / "fig4_all_author_network_formal_v17.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_font()
    paper_authors = build_research_author_pool()
    meta = build_author_meta(paper_authors)
    edges = build_edges(paper_authors)

    all_authors = meta["author"].tolist()
    scenario_summary = summarize_scenarios(all_authors, edges)
    scenario_summary.to_csv(FIG / "fig4_all_author_threshold_scenarios.csv", index=False, encoding="utf-8-sig")

    stable_edge_candidates = filtered_edges(edges, DRAW_MIN_SHARED_PAPERS, DRAW_MIN_FRACTIONAL_WEIGHT)
    stable_edge_candidates.to_csv(FIG / "fig4_all_author_edges_stable_candidates_explore.csv", index=False, encoding="utf-8-sig")
    stable_edges = choose_plot_edges(stable_edge_candidates, all_authors)
    stable_edges.to_csv(FIG / "fig4_all_author_edges_stable_explore.csv", index=False, encoding="utf-8-sig")
    meta.to_csv(FIG / "fig4_all_author_nodes_explore.csv", index=False, encoding="utf-8-sig")

    plot_all_author_network(meta, stable_edges, scenario_summary)
    plot_all_author_network_cards_v17(meta, stable_edges, paper_authors)

    print(FIG / "fig4_all_author_network_explore.png")
    print(FIG / "fig4_all_author_network_formal_v17.png")
    print(FIG / "fig4_all_author_threshold_scenarios.csv")
    print(FIG / "fig4_all_author_communities_explore.csv")


if __name__ == "__main__":
    main()

