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
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT = BASE / "output"
FIG_ROOT = BASE / "figures"
FIG = FIG_ROOT / "coauthor_network"
AUTHOR_FREQUENCY = FIG_ROOT / "author_frequency"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
FIG.mkdir(parents=True, exist_ok=True)


CORE_TOP_N = 50
MIN_SHARED_PAPERS = 3
MIN_FRACTIONAL_WEIGHT = 0.08
PLOT_TOP_EDGES_PER_NODE = 2
PLOT_TOP_CROSS_EDGES = 12
LABEL_TOP_N = 15
LAYOUT_SEED = 42


TOPIC_ORDER = ["主模型", "系统/效率", "多模态", "数学/证明", "代码", "推理/RL", "OCR"]
DISPLAY_TOPIC = {
    "主模型": "主线模型",
    "系统/效率": "系统",
    "数学/证明": "数学",
}

COMMUNITY_COLORS = [
    "#6F35B6",
    "#E45CC8",
    "#2F9B72",
    "#2F6FB3",
    "#E08C31",
    "#9C67D9",
    "#8A8798",
    "#4E7BBD",
]

GROUP_SPECS = [
    {
        "label": "A",
        "match_authors": {"Chong Ruan", "Qihao Zhu", "Zhihong Shao"},
        "topics": "主线模型为底座，数学/推理更突出",
        "representatives": "Chong Ruan、Qihao Zhu、Zhihong Shao",
        "color": "#6F35B6",
        "order": 1,
    },
    {
        "label": "B",
        "match_authors": {"Zhenda Xie", "Wenfeng Liang", "Huazuo Gao"},
        "topics": "主线模型为底座，系统/多模态更突出",
        "representatives": "Zhenda Xie、Wenfeng Liang、Huazuo Gao",
        "color": "#E45CC8",
        "order": 2,
    },
    {
        "label": "C",
        "match_authors": {"Yukun Li", "Kai Dong", "Yaofeng Sun"},
        "topics": "主线模型为底座，多模态/代码/OCR更突出",
        "representatives": "Yukun Li、Kai Dong、Yaofeng Sun",
        "color": "#2F9B72",
        "order": 3,
    },
    {
        "label": "D",
        "match_authors": {"Damai Dai", "Yu Wu", "Runxin Xu"},
        "topics": "主线模型为底座，系统/推理更突出",
        "representatives": "Damai Dai、Yu Wu、Runxin Xu",
        "color": "#2F6FB3",
        "order": 4,
    },
]


LABEL_OFFSET_OVERRIDES = {
    "Damai Dai": (-0.120, 0.170),
    "Runxin Xu": (-0.190, 0.105),
    "Wenfeng Liang": (-0.175, 0.075),
    "Huazuo Gao": (0.180, 0.105),
    "Zhenda Xie": (0.245, -0.175),
    "Chong Ruan": (0.300, 0.040),
    "Yaofeng Sun": (-0.135, -0.165),
    "Yukun Li": (-0.170, -0.115),
    "Kai Dong": (-0.175, 0.020),
    "Yu Wu": (-0.150, -0.100),
    "Zhihong Shao": (0.130, -0.145),
    "Qihao Zhu": (-0.135, -0.125),
}


MAINLINE_STAGE_ORDER = ["V1/LLM", "LLM", "V2", "V3", "R1", "V3.2", "V4"]
MAINLINE_STAGE_LABELS = {
    "V1/LLM": "LLM",
    "DeepSeek LLM": "LLM",
    "LLM": "LLM",
    "V2": "V2",
    "V3": "V3",
    "R1": "R1",
    "V3.2": "V3.2",
    "V4": "V4",
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


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.803, y: float = 0.020, scale: float = 0.96) -> None:
    if not JIAZI_LOGO.exists():
        return
    logo_ax = fig.add_axes([x, y, 0.152 * scale, 0.055 * scale])
    logo_ax.imshow(plt.imread(JIAZI_LOGO))
    logo_ax.set_axis_off()


def node_size_from_paper_count(count: int) -> float:
    return 42 + (int(count) ** 2) * 2.35


def load_author_meta() -> pd.DataFrame:
    high = pd.read_csv(OUT / "chart6_high_frequency_authors.csv", encoding="utf-8-sig")
    topic_matrix = pd.read_csv(OUT / "chart4_author_topic_matrix.csv", encoding="utf-8-sig")
    cols = ["author", "paper_count", "topic_count", "topics", "first_seen", "last_seen"]
    topic_cols = [topic for topic in TOPIC_ORDER if topic in topic_matrix.columns]
    meta = high[cols].merge(topic_matrix[["author", *topic_cols]], on="author", how="left")

    author_aug = AUTHOR_FREQUENCY / "fig3_high_frequency_authors_top25_data_augmented.csv"
    if author_aug.exists():
        aug = pd.read_csv(author_aug, encoding="utf-8-sig")
        keep = ["author", "chinese_name", "chinese_name_status", "confirmed_school"]
        keep = [col for col in keep if col in aug.columns]
        meta = meta.merge(aug[keep], on="author", how="left")
    else:
        meta["chinese_name"] = ""
        meta["chinese_name_status"] = ""
        meta["confirmed_school"] = ""

    for col in ["chinese_name", "chinese_name_status", "confirmed_school"]:
        if col not in meta.columns:
            meta[col] = ""
        meta[col] = meta[col].fillna("")

    meta["rank_by_papers"] = (
        meta.sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True])
        .reset_index()
        .index
        + 1
    )
    return meta


def build_edges(paper_authors: pd.DataFrame, papers: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    paper_meta = papers.set_index("paper_id").to_dict("index")
    edge_data: dict[tuple[str, str], dict[str, object]] = {}
    node_paper_topics: dict[str, Counter] = defaultdict(Counter)

    for paper_id, group in paper_authors.groupby("paper_id", sort=False):
        authors = sorted({str(name).strip() for name in group["clean_author_name"] if str(name).strip()})
        authors = [name for name in authors if name not in {"DeepSeek-AI", "DeepSeek AI", "DeepSeek"}]
        if len(authors) < 2:
            continue

        info = paper_meta.get(paper_id, {})
        short_title = str(info.get("short_title", group["short_title"].iloc[0]))
        topic = str(info.get("coarse_topic", group["coarse_topic"].iloc[0]))
        year_month = str(info.get("year_month", group["year_month"].iloc[0]))
        author_count = len(authors)
        fractional = 1 / max(author_count - 1, 1)
        is_main_model = pd.notna(info.get("main_model_stage")) and str(info.get("main_model_stage")).strip() != ""
        is_large_report = author_count >= 80

        for author in authors:
            node_paper_topics[author][topic] += 1

        for source, target in combinations(authors, 2):
            key = (source, target)
            if key not in edge_data:
                edge_data[key] = {
                    "source": source,
                    "target": target,
                    "shared_paper_count": 0,
                    "fractional_weight": 0.0,
                    "main_model_shared_count": 0,
                    "large_report_shared_count": 0,
                    "shared_topics": set(),
                    "shared_papers": [],
                    "shared_year_months": [],
                }
            item = edge_data[key]
            item["shared_paper_count"] = int(item["shared_paper_count"]) + 1
            item["fractional_weight"] = float(item["fractional_weight"]) + fractional
            item["main_model_shared_count"] = int(item["main_model_shared_count"]) + int(is_main_model)
            item["large_report_shared_count"] = int(item["large_report_shared_count"]) + int(is_large_report)
            item["shared_topics"].add(topic)
            item["shared_papers"].append(short_title)
            item["shared_year_months"].append(year_month)

    edge_rows = []
    for item in edge_data.values():
        shared_topics = sorted(item["shared_topics"], key=lambda t: TOPIC_ORDER.index(t) if t in TOPIC_ORDER else 99)
        edge_rows.append(
            {
                "source": item["source"],
                "target": item["target"],
                "shared_paper_count": item["shared_paper_count"],
                "fractional_weight": round(float(item["fractional_weight"]), 6),
                "main_model_shared_count": item["main_model_shared_count"],
                "large_report_shared_count": item["large_report_shared_count"],
                "shared_topics": "、".join(shared_topics),
                "shared_papers": "；".join(item["shared_papers"]),
                "shared_year_months": "；".join(item["shared_year_months"]),
            }
        )
    edges = pd.DataFrame(edge_rows)
    edges = edges.sort_values(["shared_paper_count", "fractional_weight", "source", "target"], ascending=[False, False, True, True])

    node_rows = []
    for author, topic_counts in node_paper_topics.items():
        topics = [topic for topic, _ in topic_counts.most_common()]
        node_rows.append(
            {
                "author": author,
                "raw_paper_count_from_edges": sum(topic_counts.values()),
                "raw_topic_count_from_edges": len(topic_counts),
                "raw_topics_from_edges": "、".join(topics),
            }
        )
    raw_nodes = pd.DataFrame(node_rows)
    return edges, raw_nodes


def edge_key(source: str, target: str) -> tuple[str, str]:
    return tuple(sorted((source, target)))


def select_plot_edges(core_edges: pd.DataFrame, authors: list[str]) -> pd.DataFrame:
    chosen: set[tuple[str, str]] = set()
    sorted_edges = core_edges.sort_values(
        ["fractional_weight", "shared_paper_count", "source", "target"],
        ascending=[False, False, True, True],
    )
    for author in authors:
        incident = sorted_edges[(sorted_edges["source"].eq(author)) | (sorted_edges["target"].eq(author))].head(PLOT_TOP_EDGES_PER_NODE)
        for _, row in incident.iterrows():
            chosen.add(edge_key(row["source"], row["target"]))

    cross = sorted_edges[sorted_edges["is_cross_community"]].head(PLOT_TOP_CROSS_EDGES)
    for _, row in cross.iterrows():
        chosen.add(edge_key(row["source"], row["target"]))

    plot_edges = core_edges[core_edges.apply(lambda row: edge_key(row["source"], row["target"]) in chosen, axis=1)].copy()
    return plot_edges.sort_values(["fractional_weight", "shared_paper_count"], ascending=[False, False])


def prepare_core_graph(nodes: pd.DataFrame, edges: pd.DataFrame) -> tuple[nx.Graph, nx.Graph, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    top_authors = set(nodes.sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True]).head(CORE_TOP_N)["author"])
    core_edges = edges[
        edges["source"].isin(top_authors)
        & edges["target"].isin(top_authors)
        & (edges["shared_paper_count"].astype(int) >= MIN_SHARED_PAPERS)
        & (edges["fractional_weight"].astype(float) >= MIN_FRACTIONAL_WEIGHT)
    ].copy()

    if len(core_edges) < 45:
        core_edges = edges[
            edges["source"].isin(top_authors)
            & edges["target"].isin(top_authors)
            & (edges["shared_paper_count"].astype(int) >= MIN_SHARED_PAPERS)
        ].copy()

    plot_authors = sorted(set(core_edges["source"]).union(set(core_edges["target"])))
    core_nodes = nodes[nodes["author"].isin(plot_authors)].copy()

    graph = nx.Graph()
    for _, row in core_nodes.iterrows():
        graph.add_node(row["author"], paper_count=int(row["paper_count"]), topic_count=int(row["topic_count"]))
    for _, row in core_edges.iterrows():
        graph.add_edge(
            row["source"],
            row["target"],
            weight=float(row["fractional_weight"]),
            shared_paper_count=int(row["shared_paper_count"]),
        )

    communities = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight"))
    community_map = {}
    for idx, members in enumerate(sorted(communities, key=len, reverse=True), start=1):
        for member in members:
            community_map[member] = idx
    core_nodes["community_id"] = core_nodes["author"].map(community_map).fillna(0).astype(int)

    degree = dict(graph.degree())
    weighted_degree = dict(graph.degree(weight="weight"))
    betweenness = nx.betweenness_centrality(graph, weight="weight", normalized=True) if graph.number_of_nodes() else {}
    core_nodes["plot_degree"] = core_nodes["author"].map(degree).fillna(0).astype(int)
    core_nodes["plot_weighted_degree"] = core_nodes["author"].map(weighted_degree).fillna(0).round(6)
    core_nodes["plot_betweenness"] = core_nodes["author"].map(betweenness).fillna(0).round(6)
    core_nodes["is_top25"] = core_nodes["rank_by_papers"].astype(int) <= 25
    core_nodes["is_labeled"] = core_nodes["rank_by_papers"].astype(int) <= LABEL_TOP_N

    core_edges["source_community"] = core_edges["source"].map(community_map).fillna(0).astype(int)
    core_edges["target_community"] = core_edges["target"].map(community_map).fillna(0).astype(int)
    core_edges["is_cross_community"] = core_edges["source_community"] != core_edges["target_community"]

    plot_edges = select_plot_edges(core_edges, plot_authors)
    plot_graph = nx.Graph()
    for _, row in core_nodes.iterrows():
        plot_graph.add_node(row["author"], paper_count=int(row["paper_count"]), topic_count=int(row["topic_count"]))
    for _, row in plot_edges.iterrows():
        plot_graph.add_edge(
            row["source"],
            row["target"],
            weight=float(row["fractional_weight"]),
            shared_paper_count=int(row["shared_paper_count"]),
        )

    summary_rows = []
    for community_id, group in core_nodes.groupby("community_id"):
        group_sorted = group.sort_values(["paper_count", "topic_count", "plot_betweenness"], ascending=[False, False, False])
        topic_counter: Counter[str] = Counter()
        for _, row in group.iterrows():
            for topic in TOPIC_ORDER:
                if topic in row and pd.notna(row[topic]):
                    topic_counter[topic] += int(row[topic])
        top_topics = [DISPLAY_TOPIC.get(topic, topic) for topic, _ in topic_counter.most_common(3)]
        summary_rows.append(
            {
                "community_id": int(community_id),
                "member_count": len(group),
                "top_authors": "、".join(group_sorted["author"].head(5)),
                "top_topics": "、".join(top_topics),
                "avg_paper_count": round(float(group["paper_count"].mean()), 2),
                "max_paper_count": int(group["paper_count"].max()),
            }
        )
    community_summary = pd.DataFrame(summary_rows).sort_values(["member_count", "max_paper_count"], ascending=[False, False])

    return graph, plot_graph, core_nodes, core_edges, plot_edges, community_summary


def make_display_label(row: pd.Series, compact: bool = False) -> str:
    author = str(row["author"])
    chinese = str(row.get("chinese_name", "")).strip()
    status = str(row.get("chinese_name_status", "")).strip()
    label = author
    if chinese and status in {"已核验", "用户确认"}:
        label = f"{author}\n{chinese}" if compact else f"{author}（{chinese}）"
    return label


def apply_display_groups(core_nodes: pd.DataFrame, community_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = community_summary.copy()
    assigned: dict[int, dict[str, object]] = {}
    used_communities: set[int] = set()

    for spec in GROUP_SPECS:
        for _, row in summary.iterrows():
            community_id = int(row["community_id"])
            if community_id in used_communities:
                continue
            top_authors = set(str(row["top_authors"]).split("、"))
            if top_authors & set(spec["match_authors"]):
                assigned[community_id] = spec
                used_communities.add(community_id)
                break

    next_order = len(GROUP_SPECS) + 1
    for _, row in summary.iterrows():
        community_id = int(row["community_id"])
        if community_id in assigned:
            continue
        label = chr(ord("A") + next_order - 1)
        assigned[community_id] = {
            "label": label,
            "topics": row["top_topics"],
            "representatives": row["top_authors"],
            "color": COMMUNITY_COLORS[(next_order - 1) % len(COMMUNITY_COLORS)],
            "order": next_order,
        }
        next_order += 1

    def get_spec_value(community_id: int, key: str) -> object:
        return assigned[int(community_id)][key]

    summary["display_group"] = summary["community_id"].apply(lambda cid: get_spec_value(int(cid), "label"))
    summary["display_order"] = summary["community_id"].apply(lambda cid: get_spec_value(int(cid), "order"))
    summary["display_topics"] = summary["community_id"].apply(lambda cid: get_spec_value(int(cid), "topics"))
    summary["display_representatives"] = summary["community_id"].apply(lambda cid: get_spec_value(int(cid), "representatives"))
    summary["display_color"] = summary["community_id"].apply(lambda cid: get_spec_value(int(cid), "color"))
    summary = summary.sort_values("display_order").reset_index(drop=True)

    nodes = core_nodes.copy()
    nodes["display_group"] = nodes["community_id"].map(summary.set_index("community_id")["display_group"])
    nodes["display_color"] = nodes["community_id"].map(summary.set_index("community_id")["display_color"])
    representative_authors = set().union(*(set(spec["match_authors"]) for spec in GROUP_SPECS))
    nodes["is_group_representative"] = nodes["author"].isin(representative_authors)
    nodes["is_labeled"] = nodes["is_group_representative"]
    return nodes, summary


def add_mainline_stage_summary(core_nodes: pd.DataFrame, community_summary: pd.DataFrame, paper_authors: pd.DataFrame) -> pd.DataFrame:
    """Add mainline model stage coverage for each displayed collaboration group."""
    summary = community_summary.copy()
    stage_rows = paper_authors.copy()
    stage_rows["main_model_stage"] = stage_rows["main_model_stage"].fillna("").astype(str).str.strip()
    stage_rows = stage_rows[stage_rows["main_model_stage"] != ""].copy()

    group_lookup = core_nodes.set_index("author")["display_group"].to_dict()
    stage_rows["display_group"] = stage_rows["clean_author_name"].map(group_lookup)
    stage_rows = stage_rows.dropna(subset=["display_group"])

    stage_rows = stage_rows.drop_duplicates(["display_group", "clean_author_name", "short_title", "main_model_stage"])

    def stage_key(stage: str) -> tuple[int, str]:
        if stage in MAINLINE_STAGE_ORDER:
            return MAINLINE_STAGE_ORDER.index(stage), stage
        return 99, stage

    stage_display: dict[str, str] = {}
    stage_counts: dict[str, str] = {}
    for group, group_df in stage_rows.groupby("display_group"):
        stages = sorted(set(group_df["main_model_stage"]), key=stage_key)
        labels = [MAINLINE_STAGE_LABELS.get(stage, stage) for stage in stages]
        stage_display[str(group)] = "/".join(labels)

        counts = (
            group_df.groupby("main_model_stage")["clean_author_name"]
            .nunique()
            .sort_index(key=lambda index: [stage_key(str(value))[0] for value in index])
        )
        stage_counts[str(group)] = "；".join(f"{MAINLINE_STAGE_LABELS.get(str(stage), str(stage))}:{int(count)}人" for stage, count in counts.items())

    summary["display_mainline_stages"] = summary["display_group"].map(stage_display).fillna("无")
    summary["display_mainline_stage_counts"] = summary["display_group"].map(stage_counts).fillna("")
    return summary


def save_data(nodes: pd.DataFrame, edges: pd.DataFrame, core_nodes: pd.DataFrame, core_edges: pd.DataFrame, plot_edges: pd.DataFrame, community_summary: pd.DataFrame) -> None:
    nodes.to_csv(FIG / "fig4_coauthor_nodes_all.csv", index=False, encoding="utf-8-sig")
    edges.to_csv(FIG / "fig4_coauthor_edges_all.csv", index=False, encoding="utf-8-sig")
    core_nodes.to_csv(FIG / "fig4_coauthor_nodes_core.csv", index=False, encoding="utf-8-sig")
    core_edges.to_csv(FIG / "fig4_coauthor_edges_core.csv", index=False, encoding="utf-8-sig")
    plot_edges.to_csv(FIG / "fig4_coauthor_edges_plot.csv", index=False, encoding="utf-8-sig")
    community_summary.to_csv(FIG / "fig4_coauthor_community_summary.csv", index=False, encoding="utf-8-sig")


def plot_network(core_graph: nx.Graph, plot_graph: nx.Graph, core_nodes: pd.DataFrame, plot_edges: pd.DataFrame, community_summary: pd.DataFrame) -> None:
    pos = nx.spring_layout(plot_graph, seed=LAYOUT_SEED, k=1.18, iterations=900, weight="weight", scale=1.0)

    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")

    purple = "#6F35B6"
    representative_gold = "#996600"
    title_color = "#15151A"
    subtitle_color = "#2F2F36"
    footer_color = "#555555"

    fig.add_artist(Rectangle((0.044, 0.873), 0.006, 0.089, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(
        0.058,
        0.946,
        "高频作者如何连接：DeepSeek论文里的合作骨架",
        ha="left",
        va="center",
        fontproperties=font_prop(21.0, "bold"),
        color=title_color,
    )
    fig.text(
        0.058,
        0.916,
        "Top50高频作者中，稳定共著关系形成4个合作小组；4组均覆盖主线模型全阶段。",
        ha="left",
        va="center",
        fontproperties=font_prop(15.2),
        color=subtitle_color,
    )
    fig.text(
        0.058,
        0.893,
        "主线模型之外，各小组分别侧重系统、数学、多模态、代码/OCR、推理/RL等方向。",
        ha="left",
        va="center",
        fontproperties=font_prop(15.2),
        color=subtitle_color,
    )

    metric_y = 0.844
    metrics = [
        ("Top50高频作者", f"{core_graph.number_of_nodes()}人"),
        ("全部稳定共著关系", f"{core_graph.number_of_edges()}条"),
        ("合作小组", f"{len(community_summary)}组"),
        ("图中展示骨架关系", f"{plot_graph.number_of_edges()}条"),
    ]
    for i, (label, value) in enumerate(metrics):
        x = 0.058 + i * 0.215
        fig.text(x, metric_y, value, ha="left", va="center", fontproperties=font_prop(18.0, "bold"), color=purple)
        fig.text(x, metric_y - 0.021, label, ha="left", va="center", fontproperties=font_prop(9.8), color="#555555")

    ax = fig.add_axes([0.044, 0.220, 0.908, 0.540])
    ax.set_axis_off()
    ax.set_facecolor("#FFFFFF")

    node_info = core_nodes.set_index("author").to_dict("index")
    edge_widths = []
    edge_colors = []
    for source, target, data in plot_graph.edges(data=True):
        shared = int(data.get("shared_paper_count", 1))
        edge_widths.append(0.22 + min(shared, 10) * 0.12)
        s_comm = int(node_info[source].get("community_id", 0))
        t_comm = int(node_info[target].get("community_id", 0))
        if s_comm == t_comm:
            alpha = 0.16 + min(shared, 10) * 0.010
            edge_colors.append(to_rgba("#8F8A9A", alpha))
        else:
            alpha = 0.08 + min(shared, 10) * 0.008
            edge_colors.append(to_rgba("#C8C5D1", alpha))

    nx.draw_networkx_edges(
        plot_graph,
        pos,
        ax=ax,
        width=edge_widths,
        edge_color=edge_colors,
        alpha=None,
    )

    for community_id, group in core_nodes.groupby("community_id"):
        members = list(group["author"])
        color = str(group["display_color"].iloc[0]) if "display_color" in group.columns else COMMUNITY_COLORS[(int(community_id) - 1) % len(COMMUNITY_COLORS)]
        sizes = [node_size_from_paper_count(int(node_info[node]["paper_count"])) for node in members]
        nx.draw_networkx_nodes(
            plot_graph,
            pos,
            nodelist=members,
            node_size=sizes,
            node_color=color,
            edgecolors="#FFFFFF",
            linewidths=1.0,
            alpha=0.94,
            ax=ax,
        )

    representative_nodes = list(core_nodes.loc[core_nodes["is_group_representative"], "author"])
    representative_sizes = [node_size_from_paper_count(int(node_info[node]["paper_count"])) + 58 for node in representative_nodes]
    nx.draw_networkx_nodes(
        plot_graph,
        pos,
        nodelist=representative_nodes,
        node_size=representative_sizes,
        node_color="none",
        edgecolors=representative_gold,
        linewidths=2.0,
        alpha=0.95,
        ax=ax,
    )

    label_nodes = core_nodes[core_nodes["is_labeled"]].copy().sort_values("rank_by_papers")
    offsets = [(0.00, 0.125), (0.145, 0.090), (-0.145, 0.090), (0.145, -0.090), (-0.145, -0.090), (0.00, -0.125), (0.178, 0.000), (-0.178, 0.000)]
    for label_idx, (_, row) in enumerate(label_nodes.iterrows()):
        author = row["author"]
        x, y = pos[author]
        if author in LABEL_OFFSET_OVERRIDES:
            dx, dy = LABEL_OFFSET_OVERRIDES[author]
        else:
            radius = math.hypot(float(x), float(y))
            if radius > 0.08:
                dx = float(x) / radius * 0.155
                dy = float(y) / radius * 0.155
            else:
                dx, dy = offsets[label_idx % len(offsets)]
        if dx or dy:
            ax.plot([x, x + dx], [y, y + dy], color="#D8D4DF", linewidth=0.55, alpha=0.80, zorder=7)
        ax.text(
            x + dx,
            y + dy,
            make_display_label(row, compact=True),
            ha="center",
            va="center",
            fontproperties=font_prop(7.3),
            color="#151515",
            linespacing=1.05,
            bbox={
                "boxstyle": "round,pad=0.18,rounding_size=0.08",
                "facecolor": "#FFFFFF",
                "edgecolor": "#E2DEE9",
                "linewidth": 0.45,
                "alpha": 0.68,
            },
            zorder=8,
        )

    fig.text(
        0.044,
        0.780,
        "核心网络图：Top50作者共著骨架",
        ha="left",
        va="center",
        fontproperties=font_prop(15.8, "bold"),
        color=title_color,
    )
    fig.text(
        0.044,
        0.758,
        "圆圈越大，参与论文数越多；连线越粗，合作强度越高。",
        ha="left",
        va="center",
        fontproperties=font_prop(9.2),
        color="#555555",
    )

    legend_x2 = 0.625
    fig.text(legend_x2, 0.784, "颜色：共著关系识别出的合作小组", ha="left", va="center", fontproperties=font_prop(9.2), color="#555555")
    for i, (_, row) in enumerate(community_summary.head(4).iterrows()):
        fig.add_artist(Rectangle((legend_x2 + i * 0.038, 0.768), 0.020, 0.008, transform=fig.transFigure, color=str(row["display_color"]), linewidth=0))
    fig.add_artist(Rectangle((legend_x2, 0.744), 0.020, 0.009, transform=fig.transFigure, facecolor="none", edgecolor=representative_gold, linewidth=1.5))
    fig.text(legend_x2 + 0.028, 0.749, "金色描边：小组内高连接作者", ha="left", va="center", fontproperties=font_prop(8.8), color="#555555")

    summary_ax2 = fig.add_axes([0.058, 0.105, 0.875, 0.102])
    summary_ax2.set_axis_off()
    card_focus = {
        "A": "主要覆盖数学、推理/RL",
        "B": "主要覆盖系统、多模态",
        "C": "主要覆盖多模态、代码、OCR",
        "D": "主要覆盖系统、推理/RL",
    }
    for idx, row in community_summary.head(4).reset_index(drop=True).iterrows():
        color = str(row["display_color"])
        col = idx % 2
        line = idx // 2
        x0 = 0.015 + col * 0.500
        y0 = 0.565 if line == 0 else 0.075

        summary_ax2.scatter([x0 + 0.016], [y0 + 0.315], s=48, color=color, transform=summary_ax2.transAxes)
        summary_ax2.text(
            x0 + 0.040,
            y0 + 0.320,
            f"小组{row['display_group']}｜{int(row['member_count'])}人",
            ha="left",
            va="center",
            transform=summary_ax2.transAxes,
            fontproperties=font_prop(8.8, "bold"),
            color="#151515",
        )

        group_label = str(row["display_group"])
        focus = card_focus.get(group_label, str(row["display_topics"]).replace("主线模型为底座，", ""))
        summary_ax2.text(
            x0 + 0.040,
            y0 + 0.205,
            focus,
            ha="left",
            va="center",
            transform=summary_ax2.transAxes,
            fontproperties=font_prop(7.8),
            color="#555555",
        )
        reps = str(row["display_representatives"]).replace("、", " / ")
        summary_ax2.text(
            x0 + 0.040,
            y0 + 0.095,
            f"代表：{reps}",
            ha="left",
            va="center",
            transform=summary_ax2.transAxes,
            fontproperties=font_prop(7.1),
            color="#666666",
        )

    fig.add_artist(Rectangle((0.044, 0.085), 0.908, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_x = 0.044
    footer_font = font_prop(8.2)
    fig.text(footer_x, 0.074, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.058, "公式：w(i,j)=Σ 1/(N_p-1)，N_p为论文去重作者数，用于降低百人级报告对共著强度的放大", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.042, f"口径：节点为Top{CORE_TOP_N}高频作者；先按共同署名次数与加权强度筛出稳定共著关系，作图时仅保留每位作者最强{PLOT_TOP_EDGES_PER_NODE}条边及跨组强连接", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.026, "说明：颜色为基于共著关系识别出的合作小组，不代表真实组织架构、贡献大小或汇报关系", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(footer_x, 0.010, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    draw_jiazi_logo(fig, x=0.824, y=0.018, scale=0.86)

    fig.savefig(FIG / "fig4_coauthor_network_core_v16.png", facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(FIG / "fig4_coauthor_network_core_v16.svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_font()

    papers = pd.read_csv(OUT / "papers_clean.csv", encoding="utf-8-sig")
    paper_authors = pd.read_csv(OUT / "paper_authors_clean.csv", encoding="utf-8-sig")
    meta = load_author_meta()
    edges, raw_nodes = build_edges(paper_authors, papers)

    nodes = raw_nodes.merge(meta, left_on="author", right_on="author", how="left")
    nodes["paper_count"] = nodes["paper_count"].fillna(nodes["raw_paper_count_from_edges"]).astype(int)
    nodes["topic_count"] = nodes["topic_count"].fillna(nodes["raw_topic_count_from_edges"]).astype(int)
    nodes["topics"] = nodes["topics"].fillna(nodes["raw_topics_from_edges"])
    nodes["is_high_freq_ge4"] = nodes["paper_count"] >= 4
    nodes["rank_by_papers"] = nodes["rank_by_papers"].fillna(9999).astype(int)
    nodes["is_top50"] = nodes["rank_by_papers"] <= CORE_TOP_N

    full_graph = nx.Graph()
    full_graph.add_nodes_from(nodes["author"])
    for _, row in edges.iterrows():
        full_graph.add_edge(row["source"], row["target"], weight=float(row["fractional_weight"]))
    nodes["degree_all"] = nodes["author"].map(dict(full_graph.degree())).fillna(0).astype(int)
    nodes["weighted_degree_all"] = nodes["author"].map(dict(full_graph.degree(weight="weight"))).fillna(0).round(6)

    core_graph, plot_graph, core_nodes, core_edges, plot_edges, community_summary = prepare_core_graph(nodes, edges)
    core_nodes, community_summary = apply_display_groups(core_nodes, community_summary)
    community_summary = add_mainline_stage_summary(core_nodes, community_summary, paper_authors)
    save_data(nodes, edges, core_nodes, core_edges, plot_edges, community_summary)
    plot_network(core_graph, plot_graph, core_nodes, plot_edges, community_summary)

    print(FIG / "fig4_coauthor_network_core_v16.png")
    print(FIG / "fig4_coauthor_nodes_core.csv")
    print(FIG / "fig4_coauthor_edges_core.csv")
    print(FIG / "fig4_coauthor_community_summary.csv")


if __name__ == "__main__":
    main()

