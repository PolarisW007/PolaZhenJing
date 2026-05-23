from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import math

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT = BASE / "output"
FIG = BASE / "figures" / "coauthor_network" / "old for all&Top50" / "Top50"
AUTHOR_FREQUENCY = BASE / "figures" / "author_frequency"
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
PLOT_TARGET_EDGE_COUNT = 92
LAYOUT_SEED = 20260513
OUTPUT_STEM = "fig4_top50_researcher_coauthor_skeleton_v17"

ROLE_SPLIT_MAIN = {"2405.04434", "2412.19437", "2512.02556", "V4-PDF"}
R1_CORE_ONLY = {"2501.12948"}
TEAM_NAMES = {"DeepSeek-AI", "DeepSeek AI", "DeepSeek"}

LABEL_OFFSET_OVERRIDES = {
    "Chong Ruan": (0.000, 0.112),
    "Yukun Li": (0.112, 0.064),
    "Zhenda Xie": (0.090, -0.046),
    "Wenfeng Liang": (-0.120, 0.070),
    "Damai Dai": (-0.104, -0.040),
    "Yu Wu": (0.116, 0.082),
    "Qihao Zhu": (0.110, 0.036),
    "Daya Guo": (0.118, -0.060),
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
    path = next((candidate for candidate in candidates if candidate and candidate.exists()), None)
    kwargs: dict[str, object] = {}
    if size is not None:
        kwargs["size"] = size
    if weight is not None:
        kwargs["weight"] = weight
    if path:
        return font_manager.FontProperties(fname=str(path), **kwargs)
    return font_manager.FontProperties(**kwargs)


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.816, y: float = 0.018, scale: float = 0.84) -> None:
    if not JIAZI_LOGO.exists():
        return
    logo_ax = fig.add_axes([x, y, 0.152 * scale, 0.055 * scale])
    logo_ax.imshow(plt.imread(JIAZI_LOGO))
    logo_ax.set_axis_off()


def clean_author_token(name: str) -> str:
    manual = {
        "Z.F. Wu": "Z. F. Wu",
        "Z. F Wu": "Z. F. Wu",
        "Y.K. Li": "Yukun Li",
        "Y. K. Li": "Yukun Li",
        "Y. Wu": "Yu Wu",
    }
    name = str(name).replace("\u00a0", " ").strip()
    name = name.strip(" ,;:.")
    name = name.replace("*", "").strip()
    return manual.get(name, name)


def load_r1_core_contributors() -> set[str]:
    snippet = BASE / "raw" / "main_model_role_snippets" / "2501.12948_role_snippet.txt"
    if not snippet.exists():
        return set()
    text = snippet.read_text(encoding="utf-8")
    if "Core Contributors:" not in text:
        return set()
    section = text.split("Core Contributors:", 1)[1].split("Contributions of the Core Authors", 1)[0]
    names = [clean_author_token(part) for part in section.replace("\n", " ").split(",")]
    return {name for name in names if name}


def load_chinese_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for path in [
        AUTHOR_FREQUENCY / "fig3_high_frequency_authors_top25_data_augmented.csv",
        AUTHOR_FREQUENCY / "fig3_user_confirmed_author_updates.csv",
    ]:
        if not path.exists():
            continue
        df = pd.read_csv(path, encoding="utf-8-sig")
        if "author" not in df.columns or "chinese_name" not in df.columns:
            continue
        for _, row in df.iterrows():
            author = str(row.get("author", "")).strip()
            chinese = str(row.get("chinese_name", "")).strip()
            status = str(row.get("chinese_name_status", "")).strip()
            if author and chinese and chinese.lower() != "nan":
                if not status or status in {"已核验", "用户确认", "人工补充", "nan"}:
                    names[author] = chinese
    manual = {
        "Chong Ruan": "阮翀",
        "Qihao Zhu": "朱琪豪",
        "Daya Guo": "郭达雅",
        "Wenfeng Liang": "梁文锋",
        "Damai Dai": "代达劢",
        "Zhenda Xie": "解振达",
        "Yu Wu": "吴俣",
        "Yukun Li": "李宇琨",
        "Runxin Xu": "许润昕",
        "Liyue Zhang": "张力越",
        "Xingkai Yu": "俞星凯",
        "Chengqi Deng": "邓乘奇",
        "Wen Liu": "刘闻",
        "Deli Chen": "陈德里",
        "Yaofeng Sun": "孙耀峰",
        "Huazuo Gao": "高华佐",
    }
    names.update({k: v for k, v in manual.items() if k not in names})
    return names


def display_author(author: str, chinese_names: dict[str, str]) -> str:
    chinese = chinese_names.get(author, "")
    return f"{author}\n{chinese}" if chinese else author


def researcher_filtered_authors() -> tuple[pd.DataFrame, pd.DataFrame]:
    authors = pd.read_csv(OUT / "paper_authors_clean.csv", encoding="utf-8-sig")
    roles = pd.read_csv(OUT / "main_model_authors_with_roles.csv", encoding="utf-8-sig")

    authors["clean_author_name"] = authors["clean_author_name"].fillna("").astype(str).str.strip()
    authors = authors[authors["clean_author_name"].ne("")].copy()
    authors = authors[~authors["clean_author_name"].isin(TEAM_NAMES)].copy()

    is_re = roles["is_research_engineering"].astype(str).str.upper().eq("TRUE")
    re_role_keep = roles[is_re][["paper_id", "clean_author_name"]].drop_duplicates()
    re_keys = set(map(tuple, re_role_keep.values.tolist()))
    r1_core = load_r1_core_contributors()

    def keep_row(row: pd.Series) -> bool:
        paper_id = str(row["paper_id"])
        author = str(row["clean_author_name"])
        if paper_id in ROLE_SPLIT_MAIN:
            return (paper_id, author) in re_keys
        if paper_id in R1_CORE_ONLY and r1_core:
            return author in r1_core
        return True

    filtered = authors[authors.apply(keep_row, axis=1)].copy()
    filtered["researcher_filter_note"] = filtered["paper_id"].map(
        lambda pid: "role_split_keep_research_engineering"
        if pid in ROLE_SPLIT_MAIN
        else (
            "r1_keep_core_contributors_only"
            if pid in R1_CORE_ONLY
            else "non_role_split_signature_authors"
        )
    )
    filtered = filtered.drop_duplicates(["paper_id", "clean_author_name"]).copy()
    return authors, filtered


def author_meta(filtered: pd.DataFrame) -> pd.DataFrame:
    dedup = filtered.drop_duplicates(["clean_author_name", "paper_id"])
    paper_count = dedup.groupby("clean_author_name")["paper_id"].nunique()
    topic_count = (
        filtered.drop_duplicates(["clean_author_name", "paper_id", "coarse_topic"])
        .groupby("clean_author_name")["coarse_topic"]
        .nunique()
    )
    mainline_count = (
        filtered[filtered["main_model_stage"].fillna("").astype(str).str.strip().ne("")]
        .drop_duplicates(["clean_author_name", "paper_id"])
        .groupby("clean_author_name")["paper_id"]
        .nunique()
    )
    topics = (
        filtered.drop_duplicates(["clean_author_name", "coarse_topic"])
        .groupby("clean_author_name")["coarse_topic"]
        .apply(lambda values: "、".join(sorted(values)))
    )
    meta = pd.DataFrame(
        {
            "author": paper_count.index,
            "paper_count": paper_count.values,
            "topic_count": topic_count.reindex(paper_count.index).fillna(0).astype(int).values,
            "mainline_paper_count": mainline_count.reindex(paper_count.index).fillna(0).astype(int).values,
            "topics": topics.reindex(paper_count.index).fillna("").values,
        }
    )
    meta = meta.sort_values(["paper_count", "topic_count", "mainline_paper_count", "author"], ascending=[False, False, False, True]).reset_index(drop=True)
    meta["rank"] = meta.index + 1
    return meta


def build_weighted_edges(filtered: pd.DataFrame) -> pd.DataFrame:
    counts: Counter[tuple[str, str]] = Counter()
    frac: Counter[tuple[str, str]] = Counter()
    shared_papers: dict[tuple[str, str], list[str]] = defaultdict(list)
    shared_topics: dict[tuple[str, str], set[str]] = defaultdict(set)

    for paper_id, group in filtered.groupby("paper_id", sort=False):
        authors = sorted({str(name).strip() for name in group["clean_author_name"] if str(name).strip()})
        authors = [author for author in authors if author not in TEAM_NAMES]
        if len(authors) < 2:
            continue
        inc = 1 / max(len(authors) - 1, 1)
        short_title = str(group["short_title"].iloc[0])
        topic = str(group["coarse_topic"].iloc[0])
        for source, target in combinations(authors, 2):
            key = tuple(sorted((source, target)))
            counts[key] += 1
            frac[key] += inc
            shared_papers[key].append(short_title)
            shared_topics[key].add(topic)

    rows = []
    for (source, target), shared in counts.items():
        rows.append(
            {
                "source": source,
                "target": target,
                "shared_paper_count": int(shared),
                "fractional_weight": round(float(frac[(source, target)]), 6),
                "shared_papers": "；".join(shared_papers[(source, target)]),
                "shared_topics": "、".join(sorted(shared_topics[(source, target)])),
            }
        )
    return pd.DataFrame(rows).sort_values(["shared_paper_count", "fractional_weight", "source", "target"], ascending=[False, False, True, True])


def edge_key(source: str, target: str) -> tuple[str, str]:
    return tuple(sorted((source, target)))


def prepare_top50_graph(meta: pd.DataFrame, edges: pd.DataFrame) -> tuple[nx.Graph, nx.Graph, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    top_nodes = meta.head(CORE_TOP_N).copy()
    top_authors = set(top_nodes["author"])
    core_edges = edges[
        edges["source"].isin(top_authors)
        & edges["target"].isin(top_authors)
        & (edges["shared_paper_count"].astype(int) >= MIN_SHARED_PAPERS)
        & (edges["fractional_weight"].astype(float) >= MIN_FRACTIONAL_WEIGHT)
    ].copy()

    if len(core_edges) < 80:
        core_edges = edges[
            edges["source"].isin(top_authors)
            & edges["target"].isin(top_authors)
            & (edges["shared_paper_count"].astype(int) >= MIN_SHARED_PAPERS)
        ].copy()

    core_graph = nx.Graph()
    for _, row in top_nodes.iterrows():
        core_graph.add_node(
            row["author"],
            paper_count=int(row["paper_count"]),
            topic_count=int(row["topic_count"]),
            mainline_paper_count=int(row["mainline_paper_count"]),
        )
    for _, row in core_edges.iterrows():
        core_graph.add_edge(
            row["source"],
            row["target"],
            weight=float(row["fractional_weight"]),
            shared_paper_count=int(row["shared_paper_count"]),
        )

    top_nodes["degree_stable"] = top_nodes["author"].map(dict(core_graph.degree())).fillna(0).astype(int)
    top_nodes["weighted_degree_stable"] = top_nodes["author"].map(dict(core_graph.degree(weight="weight"))).fillna(0).round(6)
    betweenness = nx.betweenness_centrality(core_graph, weight="weight", normalized=True) if core_graph.number_of_edges() else {}
    top_nodes["betweenness_stable"] = top_nodes["author"].map(betweenness).fillna(0).round(6)

    community_map: dict[str, int] = {}
    if core_graph.number_of_edges():
        try:
            communities = nx.community.louvain_communities(core_graph, weight="weight", seed=LAYOUT_SEED, resolution=1.05)
        except Exception:
            communities = nx.community.greedy_modularity_communities(core_graph, weight="weight")
        for idx, members in enumerate(sorted(communities, key=len, reverse=True), start=1):
            for member in members:
                community_map[member] = idx
    top_nodes["layout_cluster_id"] = top_nodes["author"].map(community_map).fillna(0).astype(int)
    core_edges["source_cluster_id"] = core_edges["source"].map(community_map).fillna(0).astype(int)
    core_edges["target_cluster_id"] = core_edges["target"].map(community_map).fillna(0).astype(int)
    core_edges["is_cross_cluster"] = core_edges["source_cluster_id"] != core_edges["target_cluster_id"]

    sorted_edges = core_edges.sort_values(["fractional_weight", "shared_paper_count", "source", "target"], ascending=[False, False, True, True])
    chosen: set[tuple[str, str]] = set()
    for author in top_nodes["author"]:
        incident = sorted_edges[(sorted_edges["source"].eq(author)) | (sorted_edges["target"].eq(author))].head(PLOT_TOP_EDGES_PER_NODE)
        for _, row in incident.iterrows():
            chosen.add(edge_key(row["source"], row["target"]))

    # Keep extra cross-cluster links internally so the reader sees a connected mesh, without labeling those clusters.
    for _, row in sorted_edges[sorted_edges["is_cross_cluster"]].head(24).iterrows():
        chosen.add(edge_key(row["source"], row["target"]))
    if len(chosen) < PLOT_TARGET_EDGE_COUNT:
        for _, row in sorted_edges.iterrows():
            chosen.add(edge_key(row["source"], row["target"]))
            if len(chosen) >= min(PLOT_TARGET_EDGE_COUNT, len(sorted_edges)):
                break

    plot_edges = core_edges[core_edges.apply(lambda row: edge_key(row["source"], row["target"]) in chosen, axis=1)].copy()
    plot_edges = plot_edges.sort_values(["fractional_weight", "shared_paper_count", "source", "target"], ascending=[False, False, True, True])

    plot_graph = nx.Graph()
    for _, row in top_nodes.iterrows():
        plot_graph.add_node(
            row["author"],
            paper_count=int(row["paper_count"]),
            topic_count=int(row["topic_count"]),
            weighted_degree=float(row["weighted_degree_stable"]),
            betweenness=float(row["betweenness_stable"]),
        )
    for _, row in plot_edges.iterrows():
        plot_graph.add_edge(
            row["source"],
            row["target"],
            weight=float(row["fractional_weight"]),
            shared_paper_count=int(row["shared_paper_count"]),
        )

    return core_graph, plot_graph, top_nodes, core_edges, plot_edges


def node_size_from_count(count: int) -> float:
    return 120 + (int(count) ** 2) * 4.9


def label_authors(nodes: pd.DataFrame) -> list[str]:
    work = nodes.copy()
    for col in ["paper_count", "weighted_degree_stable", "betweenness_stable", "topic_count"]:
        maximum = float(work[col].max()) if float(work[col].max()) else 1.0
        work[f"{col}_n"] = work[col].astype(float) / maximum
    work["label_score"] = (
        work["paper_count_n"] * 0.42
        + work["weighted_degree_stable_n"] * 0.30
        + work["betweenness_stable_n"] * 0.20
        + work["topic_count_n"] * 0.08
    )
    preferred = [
        "Chong Ruan",
        "Yukun Li",
        "Wenfeng Liang",
        "Damai Dai",
        "Qihao Zhu",
        "Zhenda Xie",
        "Daya Guo",
        "Yu Wu",
        "Huazuo Gao",
        "Zhihong Shao",
    ]
    chosen = [author for author in preferred if author in set(work["author"])]
    for author in work.sort_values("label_score", ascending=False)["author"]:
        if author not in chosen:
            chosen.append(author)
        if len(chosen) >= 8:
            break
    return chosen[:8]


def normalize_positions(pos: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
    xs = [xy[0] for xy in pos.values()]
    ys = [xy[1] for xy in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max(max_x - min_x, 1e-9)
    height = max(max_y - min_y, 1e-9)
    return {node: ((x - min_x) / width, (y - min_y) / height) for node, (x, y) in pos.items()}


def plot_network(
    core_graph: nx.Graph,
    plot_graph: nx.Graph,
    nodes: pd.DataFrame,
    core_edges: pd.DataFrame,
    plot_edges: pd.DataFrame,
    original_unique: int,
    filtered_unique: int,
) -> None:
    configure_font()
    chinese_names = load_chinese_names()
    node_info = nodes.set_index("author").to_dict("index")
    if core_graph.number_of_edges():
        layout_graph = core_graph.copy()
    else:
        layout_graph = plot_graph.copy()
    pos_raw = nx.spring_layout(layout_graph, seed=LAYOUT_SEED, k=0.78, iterations=950, weight="weight", scale=1.0)
    pos = normalize_positions(pos_raw)

    fig = plt.figure(figsize=(8.35, 11.8), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    purple = "#6F35B6"
    title_color = "#15151A"
    subtitle_color = "#34343B"
    footer_color = "#555555"

    fig.add_artist(Rectangle((0.044, 0.878), 0.006, 0.088, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(
        0.058,
        0.949,
        "高频作者如何连接：DeepSeek论文里的合作骨架",
        ha="left",
        va="center",
        fontproperties=font_prop(21.2, "bold"),
        color=title_color,
    )
    subtitle_1 = "基于Top50高频研究作者的共著关系绘制。主线论文把这些作者反复连接在一起，"
    subtitle_2 = "他们并不是按方向切成固定小组，而是围绕主线模型和具体问题动态协作。"
    fig.text(0.058, 0.918, subtitle_1, ha="left", va="center", fontproperties=font_prop(12.9), color=subtitle_color)
    fig.text(0.058, 0.895, subtitle_2, ha="left", va="center", fontproperties=font_prop(12.9), color=subtitle_color)

    metric_y = 0.838
    metrics = [
        (f"{CORE_TOP_N}人", "Top50高频研究作者"),
        (f"{core_graph.number_of_edges()}条", "全部稳定共著关系"),
        (f"{plot_graph.number_of_edges()}条", "图中展示骨架关系"),
    ]
    for i, (value, label) in enumerate(metrics):
        x = 0.060 + i * 0.290
        fig.text(x, metric_y, value, ha="left", va="center", fontproperties=font_prop(21.0, "bold"), color=purple)
        fig.text(x, metric_y - 0.024, label, ha="left", va="center", fontproperties=font_prop(10.2), color="#555555")

    fig.text(
        0.044,
        0.775,
        "Top50研究员合作关系图",
        ha="left",
        va="center",
        fontproperties=font_prop(16.4, "bold"),
        color=title_color,
    )
    fig.text(
        0.044,
        0.752,
        "节点越大，参与论文数越多；连线越粗，合作强度越高。图中不强调固定分组，而是呈现交叉合作网络。",
        ha="left",
        va="center",
        fontproperties=font_prop(9.4),
        color="#555555",
    )

    legend_x = 0.685
    fig.add_artist(Rectangle((legend_x, 0.770), 0.018, 0.018, transform=fig.transFigure, facecolor=purple, edgecolor="white", linewidth=0.7, alpha=0.86))
    fig.text(legend_x + 0.026, 0.779, "节点大小：参与论文数", ha="left", va="center", fontproperties=font_prop(8.8), color="#555555")
    fig.add_artist(Rectangle((legend_x, 0.747), 0.034, 0.0035, transform=fig.transFigure, facecolor="#9CA3AF", edgecolor="none", alpha=0.50))
    fig.text(legend_x + 0.044, 0.749, "线宽：加权合作强度", ha="left", va="center", fontproperties=font_prop(8.8), color="#555555")

    ax = fig.add_axes([0.044, 0.112, 0.908, 0.615])
    ax.set_axis_off()
    ax.set_facecolor("#FFFFFF")

    weights = [float(plot_graph[u][v].get("weight", 0.0)) for u, v in plot_graph.edges()]
    max_w = max(weights) if weights else 1.0
    edge_widths = [0.35 + 4.3 * (w / max_w) ** 0.75 for w in weights]
    nx.draw_networkx_edges(
        plot_graph,
        pos,
        ax=ax,
        width=edge_widths,
        edge_color="#8E8A99",
        alpha=0.22,
    )

    counts = [int(node_info[node]["paper_count"]) for node in plot_graph.nodes()]
    min_count, max_count = min(counts), max(counts)
    cmap = LinearSegmentedColormap.from_list("deepseek_purple", ["#C7B3EA", "#9C67D9", "#6F35B6"])
    node_colors = []
    node_sizes = []
    for node in plot_graph.nodes():
        count = int(node_info[node]["paper_count"])
        norm = 0.0 if max_count == min_count else (count - min_count) / (max_count - min_count)
        node_colors.append(cmap(0.22 + norm * 0.72))
        node_sizes.append(node_size_from_count(count))

    nx.draw_networkx_nodes(
        plot_graph,
        pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        linewidths=1.1,
        edgecolors="#FFFFFF",
        alpha=0.94,
    )

    selected_labels = label_authors(nodes)
    for author in selected_labels:
        if author not in pos:
            continue
        x, y = pos[author]
        if author in LABEL_OFFSET_OVERRIDES:
            dx, dy = LABEL_OFFSET_OVERRIDES[author]
        else:
            dx = (x - 0.50) * 0.085
            dy = (y - 0.50) * 0.085
            if abs(dx) < 0.028:
                dx = 0.028 if x >= 0.5 else -0.028
            if abs(dy) < 0.028:
                dy = 0.028 if y >= 0.5 else -0.028
        lx, ly = x + dx, y + dy
        ax.plot([x, lx], [y, ly], color="#D8D4DF", linewidth=0.55, alpha=0.78, zorder=6)
        ax.text(
            lx,
            ly,
            display_author(author, chinese_names),
            ha="center",
            va="center",
            fontproperties=font_prop(7.9, "bold" if int(node_info[author]["paper_count"]) >= 10 else None),
            color="#151515",
            linespacing=1.04,
            bbox={
                "boxstyle": "round,pad=0.18,rounding_size=0.07",
                "facecolor": "#FFFFFF",
                "edgecolor": "#E5E1EC",
                "linewidth": 0.45,
                "alpha": 0.72,
            },
            zorder=8,
        )

    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(-0.04, 1.04)

    fig.add_artist(Rectangle((0.044, 0.086), 0.908, 0.0010, transform=fig.transFigure, color="#C8C5D1", alpha=0.9, linewidth=0))
    footer_font = font_prop(7.7)
    fig.text(0.044, 0.074, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    fig.text(
        0.044,
        0.058,
        "口径：Top50高频作者基于研究作者池统计；V2/V3/V3.2/V4使用Research & Engineering名单，R1按Core Contributors处理，其他论文使用原始署名并剔除团队名。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )
    fig.text(
        0.044,
        0.042,
        f"方法：w(i,j)=Σ1/(N_p-1)，用于降低百人级报告影响；先筛共同署名≥{MIN_SHARED_PAPERS}且w≥{MIN_FRACTIONAL_WEIGHT:.2f}的稳定关系，再保留每人最强{PLOT_TOP_EDGES_PER_NODE}条边及强连接。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )
    fig.text(
        0.044,
        0.026,
        f"说明：共著关系不代表真实组织架构、贡献大小或汇报关系；原始去重作者{original_unique}人，研究作者池去重{filtered_unique}人。",
        ha="left",
        va="center",
        fontproperties=footer_font,
        color=footer_color,
    )
    fig.text(0.044, 0.010, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color=footer_color)
    draw_jiazi_logo(fig)

    png = FIG / f"{OUTPUT_STEM}.png"
    svg = FIG / f"{OUTPUT_STEM}.svg"
    fig.savefig(png, facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(svg, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    original, filtered = researcher_filtered_authors()
    meta = author_meta(filtered)
    edges = build_weighted_edges(filtered)
    core_graph, plot_graph, top_nodes, core_edges, plot_edges = prepare_top50_graph(meta, edges)

    filtered.to_csv(FIG / f"{OUTPUT_STEM}_research_author_pool.csv", index=False, encoding="utf-8-sig")
    top_nodes.to_csv(FIG / f"{OUTPUT_STEM}_nodes.csv", index=False, encoding="utf-8-sig")
    core_edges.to_csv(FIG / f"{OUTPUT_STEM}_stable_edges.csv", index=False, encoding="utf-8-sig")
    plot_edges.to_csv(FIG / f"{OUTPUT_STEM}_plot_edges.csv", index=False, encoding="utf-8-sig")

    plot_network(
        core_graph=core_graph,
        plot_graph=plot_graph,
        nodes=top_nodes,
        core_edges=core_edges,
        plot_edges=plot_edges,
        original_unique=original["clean_author_name"].nunique(),
        filtered_unique=filtered["clean_author_name"].nunique(),
    )

    print(f"original_unique_authors={original['clean_author_name'].nunique()}")
    print(f"researcher_filtered_unique_authors={filtered['clean_author_name'].nunique()}")
    print(f"top50_stable_edges={core_graph.number_of_edges()}")
    print(f"top50_plot_edges={plot_graph.number_of_edges()}")
    print(FIG / f"{OUTPUT_STEM}.png")


if __name__ == "__main__":
    main()

