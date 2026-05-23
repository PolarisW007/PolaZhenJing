from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import math

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib import font_manager
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT = BASE / "output"
FIG = BASE / "figures" / "coauthor_network"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"

FIG.mkdir(parents=True, exist_ok=True)

ROLE_SPLIT_MAIN = {"2405.04434", "2412.19437", "2512.02556", "V4-PDF"}
R1_PAPER_ID = "2501.12948"
TEAM_NAMES = {"DeepSeek-AI", "DeepSeek AI", "DeepSeek", "deepseek-ai"}
MIN_SHARED_PAPERS = 2
MIN_FRACTIONAL_WEIGHT = 0.018
TOP_EDGES_PER_NODE = 2
OUTPUT_STEM = "fig4_deepseek_research_matrix_network_v1_hub_labels"

PALETTE = [
    "#6F35B6",
    "#E45C9B",
    "#2F9B72",
    "#2F6FB3",
    "#E08C31",
    "#9C67D9",
    "#26A3A1",
    "#D65F5F",
    "#64748B",
    "#8B5E34",
]

CLUSTER_LABELS = {
    1: ("基模大兵团", "主攻 R1 / V3 / V4 大主干"),
    2: ("系统效率小队", "主攻 Infra、NSA、模型维稳"),
    3: ("数学与推理小队", "主攻 Prover / Math / 推理泛化"),
    4: ("多模态小队", "主攻 视觉 / Janus 系列"),
    5: ("缓存与系统小队", "主攻 DualPath / 小型系统优化"),
    6: ("垂类数学小队", "主攻 DeepSeekMath-V2"),
    7: ("OCR视觉小队", "主攻 复杂文档视觉理解"),
}

GROUP_ORDER = [1, 2, 3, 4, 5, 6, 7]

TITLE = "DeepSeek打破部门墙，25位“多边形战士”串联7大研发矩阵"
SUBTITLE_LINES = [
    "基于核心论文的共著关系聚类显示，DeepSeek的研发并未被死板的部门割裂。",
    "1个基模大兵团（94人）与6支精锐特种小队配合，顶尖大牛作为枢纽频繁跨界，",
    "解决系统、数学与多模态等多方面问题。",
]

DEPARTED_AUTHORS = {"Chong Ruan", "Daya Guo", "Bingxuan Wang"}
AUTHOR_CHINESE_OVERRIDES = {
    "Chong Ruan": "阮翀",
    "Daya Guo": "郭达雅",
    "Bingxuan Wang": "王炳宣",
}


def configure_font() -> None:
    for path in [
        NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(path)).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


def font_prop(size: float, weight: str | None = None) -> font_manager.FontProperties:
    candidates = [
        NOTO_SC_BOLD if weight == "bold" else NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyhbd.ttc") if weight == "bold" else Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    path = next((p for p in candidates if p and p.exists()), None)
    kwargs: dict[str, object] = {"size": size}
    if weight:
        kwargs["weight"] = weight
    if path:
        return font_manager.FontProperties(fname=str(path), **kwargs)
    return font_manager.FontProperties(**kwargs)


def load_chinese_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for path in [
        BASE / "figures" / "author_frequency" / "fig3_high_frequency_authors_top25_data_augmented.csv",
        BASE / "figures" / "author_frequency" / "fig3_user_confirmed_author_updates.csv",
    ]:
        if not path.exists():
            continue
        df = pd.read_csv(path, encoding="utf-8-sig")
        if "author" not in df.columns or "chinese_name" not in df.columns:
            continue
        for _, row in df.iterrows():
            author = str(row.get("author", "")).strip()
            chinese = str(row.get("chinese_name", "")).strip()
            if author and chinese and chinese.lower() != "nan":
                names[author] = chinese
    names.update(AUTHOR_CHINESE_OVERRIDES)
    return names


def display_author(author: str, chinese: dict[str, str]) -> str:
    label = chinese.get(author, author)
    return f"{label}*" if author in DEPARTED_AUTHORS else label


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.760, y: float = 0.022, scale: float = 0.82) -> None:
    if not JIAZI_LOGO.exists():
        return
    try:
        logo_ax = fig.add_axes([x, y, 0.170 * scale, 0.060 * scale])
        logo_ax.imshow(plt.imread(JIAZI_LOGO))
        logo_ax.set_axis_off()
    except Exception:
        return


def node_size_from_papers(paper_count: int) -> float:
    return 22 + (max(paper_count, 1) ** 1.72) * 6.6


def interpolate_color(color_a: str, color_b: str, t: float) -> tuple[float, float, float, float]:
    a = to_rgb(color_a)
    b = to_rgb(color_b)
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
        1.0,
    )


def draw_gradient_edge(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color_a: str,
    color_b: str,
    width: float,
    alpha: float,
    zorder: float = 1,
) -> None:
    segments = []
    colors = []
    steps = 10
    for idx in range(steps):
        t0 = idx / steps
        t1 = (idx + 1) / steps
        x0 = start[0] + (end[0] - start[0]) * t0
        y0 = start[1] + (end[1] - start[1]) * t0
        x1 = start[0] + (end[0] - start[0]) * t1
        y1 = start[1] + (end[1] - start[1]) * t1
        segments.append([(x0, y0), (x1, y1)])
        rgba = interpolate_color(color_a, color_b, (t0 + t1) / 2)
        colors.append((rgba[0], rgba[1], rgba[2], alpha))
    ax.add_collection(LineCollection(segments, colors=colors, linewidths=width, zorder=zorder, capstyle="round"))


def spread_cluster_layout(g: nx.Graph, community: dict[str, int]) -> dict[str, tuple[float, float]]:
    pos = nx.spring_layout(
        g,
        seed=20260510,
        weight="weight",
        k=2.85 / math.sqrt(max(g.number_of_nodes(), 1)),
        iterations=760,
        scale=6.0,
    )
    centroids: dict[int, tuple[float, float]] = {}
    for cid in set(community.values()):
        members = [node for node in g.nodes() if community.get(node) == cid]
        if not members:
            continue
        centroids[cid] = (
            sum(pos[node][0] for node in members) / len(members),
            sum(pos[node][1] for node in members) / len(members),
        )

    adjusted: dict[str, tuple[float, float]] = {}
    for node, (x, y) in pos.items():
        cid = community.get(node, 1)
        cx, cy = centroids.get(cid, (0.0, 0.0))
        adjusted[node] = (
            cx * 1.52 + (x - cx) * 1.18,
            cy * 1.52 + (y - cy) * 1.18,
        )
    return adjusted


def place_labels_without_overlap(
    fig: plt.Figure,
    ax: plt.Axes,
    labels: list[plt.Text],
    max_iter: int = 260,
) -> None:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for _ in range(max_iter):
        moved = False
        boxes = [label.get_window_extent(renderer=renderer).expanded(1.18, 1.36) for label in labels]
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                b1 = boxes[i]
                b2 = boxes[j]
                if not b1.overlaps(b2):
                    continue
                cx1 = (b1.x0 + b1.x1) / 2
                cy1 = (b1.y0 + b1.y1) / 2
                cx2 = (b2.x0 + b2.x1) / 2
                cy2 = (b2.y0 + b2.y1) / 2
                dx = cx1 - cx2
                dy = cy1 - cy2
                if abs(dx) < 0.1 and abs(dy) < 0.1:
                    dx, dy = 1.0, 0.6
                norm = math.sqrt(dx * dx + dy * dy)
                push_x = 7.4 * dx / norm
                push_y = 7.4 * dy / norm
                for label, sx, sy in [(labels[i], push_x, push_y), (labels[j], -push_x, -push_y)]:
                    x, y = label.get_position()
                    x_disp, y_disp = ax.transData.transform((x, y))
                    x_new, y_new = ax.transData.inverted().transform((x_disp + sx, y_disp + sy))
                    label.set_position((x_new, y_new))
                moved = True
        if not moved:
            break
        fig.canvas.draw()


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
    name = manual.get(name, name)
    return name


def researcher_filtered_authors() -> tuple[pd.DataFrame, pd.DataFrame]:
    authors = pd.read_csv(OUT / "paper_authors_clean.csv", encoding="utf-8-sig")
    roles = pd.read_csv(OUT / "main_model_authors_with_roles.csv", encoding="utf-8-sig")

    authors["clean_author_name"] = authors["clean_author_name"].fillna("").astype(str).str.strip()
    authors = authors[authors["clean_author_name"].ne("")]
    authors = authors[~authors["clean_author_name"].isin(TEAM_NAMES)].copy()

    is_re = roles["is_research_engineering"].astype(str).str.upper().eq("TRUE")
    role_keep = roles[is_re][["paper_id", "clean_author_name"]].drop_duplicates()
    keep_keys = set(map(tuple, role_keep.values.tolist()))
    v3_re_names = set(
        roles.loc[
            roles["short_title"].eq("DeepSeek-V3 Technical Report")
            & roles["is_research_engineering"].astype(str).str.upper().eq("TRUE"),
            "clean_author_name",
        ].astype(str).str.strip()
    )

    def keep_row(row: pd.Series) -> bool:
        paper_id = str(row["paper_id"])
        author = str(row["clean_author_name"])
        if paper_id in ROLE_SPLIT_MAIN:
            return (paper_id, author) in keep_keys
        if paper_id == R1_PAPER_ID:
            return author in v3_re_names
        return True

    filtered = authors[authors.apply(keep_row, axis=1)].copy()
    filtered["researcher_filter_note"] = filtered["paper_id"].map(
        lambda pid: "role_split_keep_research_engineering"
        if pid in ROLE_SPLIT_MAIN
        else (
            "r1_proxy_signature_intersection_v3_re"
            if pid == R1_PAPER_ID
            else "unsplit_signature_authors_excluding_team_names"
        )
    )
    filtered = filtered.drop_duplicates(["paper_id", "clean_author_name"]).reset_index(drop=True)
    return authors, filtered


def author_meta(paper_authors: pd.DataFrame) -> pd.DataFrame:
    dedup = paper_authors.drop_duplicates(["clean_author_name", "paper_id"])
    paper_count = dedup.groupby("clean_author_name")["paper_id"].nunique()
    topic_count = paper_authors.drop_duplicates(["clean_author_name", "paper_id", "coarse_topic"]).groupby("clean_author_name")["coarse_topic"].nunique()
    meta = pd.DataFrame(
        {
            "author": paper_count.index,
            "paper_count": paper_count.values,
            "topic_count": topic_count.reindex(paper_count.index).fillna(0).astype(int).values,
        }
    )
    return meta.sort_values(["paper_count", "topic_count", "author"], ascending=[False, False, True]).reset_index(drop=True)


def build_weighted_edges(paper_authors: pd.DataFrame) -> pd.DataFrame:
    paper_to_authors = {
        pid: sorted(group["clean_author_name"].dropna().unique())
        for pid, group in paper_authors.groupby("paper_id")
    }
    paper_titles = paper_authors.drop_duplicates("paper_id").set_index("paper_id")["short_title"].to_dict()
    counts: Counter[tuple[str, str]] = Counter()
    frac: Counter[tuple[str, str]] = Counter()
    papers: dict[tuple[str, str], set[str]] = defaultdict(set)

    for pid, authors in paper_to_authors.items():
        n = len(authors)
        if n < 2:
            continue
        inc = 1 / (n - 1)
        for a, b in combinations(authors, 2):
            key = (a, b)
            counts[key] += 1
            frac[key] += inc
            papers[key].add(str(paper_titles.get(pid, pid)))

    rows = []
    for (a, b), shared in counts.items():
        rows.append(
            {
                "source": a,
                "target": b,
                "shared_papers": int(shared),
                "fractional_weight": float(frac[(a, b)]),
                "papers": "；".join(sorted(papers[(a, b)])),
            }
        )
    return pd.DataFrame(rows)


def stable_subgraph(edges: pd.DataFrame, meta: pd.DataFrame) -> tuple[nx.Graph, pd.DataFrame]:
    stable = edges[
        (edges["shared_papers"] >= MIN_SHARED_PAPERS)
        & (edges["fractional_weight"] >= MIN_FRACTIONAL_WEIGHT)
    ].copy()

    if stable.empty:
        return nx.Graph(), stable

    degree_score = Counter()
    for _, row in stable.iterrows():
        degree_score[row["source"]] += float(row["fractional_weight"])
        degree_score[row["target"]] += float(row["fractional_weight"])

    # Demo: keep the strongest local skeleton so the graph is readable.
    keep_edges = set()
    for author in set(stable["source"]) | set(stable["target"]):
        local = stable[(stable["source"].eq(author)) | (stable["target"].eq(author))].copy()
        local = local.sort_values(["fractional_weight", "shared_papers"], ascending=[False, False]).head(TOP_EDGES_PER_NODE)
        for _, row in local.iterrows():
            keep_edges.add(tuple(sorted((row["source"], row["target"]))))
    skeleton = stable[stable.apply(lambda r: tuple(sorted((r["source"], r["target"]))) in keep_edges, axis=1)].copy()

    g = nx.Graph()
    for _, row in meta.iterrows():
        g.add_node(row["author"], paper_count=int(row["paper_count"]), topic_count=int(row["topic_count"]))
    for _, row in skeleton.iterrows():
        g.add_edge(
            row["source"],
            row["target"],
            weight=float(row["fractional_weight"]),
            shared_papers=int(row["shared_papers"]),
        )
    g.remove_nodes_from(list(nx.isolates(g)))
    return g, skeleton


def communities_for_graph(g: nx.Graph) -> dict[str, int]:
    if g.number_of_nodes() == 0:
        return {}
    try:
        comms = nx.community.louvain_communities(g, weight="weight", seed=20260510, resolution=1.08)
    except Exception:
        comms = nx.community.greedy_modularity_communities(g, weight="weight")
    comms = sorted([sorted(c) for c in comms], key=len, reverse=True)
    lookup = {}
    for idx, members in enumerate(comms, start=1):
        for author in members:
            lookup[author] = idx
    return lookup


def draw_demo(
    g: nx.Graph,
    community: dict[str, int],
    meta: pd.DataFrame,
    original_count: int,
    filtered_count: int,
    stable_edges: pd.DataFrame,
) -> Path:
    configure_font()
    chinese = load_chinese_names()
    meta_by_author = meta.set_index("author").to_dict("index")

    fig = plt.figure(figsize=(8.35, 11.8), dpi=240)
    fig.patch.set_facecolor("#FFFFFF")
    title_color = "#15151A"
    body_color = "#2F2F36"
    purple = "#6F35B6"

    fig.add_artist(Rectangle((0.044, 0.922), 0.006, 0.058, transform=fig.transFigure, color=purple, linewidth=0))
    fig.text(0.062, 0.962, TITLE, ha="left", va="center", fontproperties=font_prop(20.2, "bold"), color=title_color)
    fig.text(0.062, 0.930, SUBTITLE_LINES[0], ha="left", va="center", fontproperties=font_prop(11.7), color=body_color)
    fig.text(0.062, 0.908, SUBTITLE_LINES[1], ha="left", va="center", fontproperties=font_prop(11.7), color=body_color)
    fig.text(0.062, 0.886, SUBTITLE_LINES[2], ha="left", va="center", fontproperties=font_prop(11.7), color=body_color)

    ax = fig.add_axes([0.030, 0.222, 0.940, 0.568])
    ax.set_facecolor("#FFFFFF")
    ax.set_axis_off()

    if g.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "没有形成稳定共著网络", ha="center", va="center", fontproperties=font_prop(18, "bold"))
        out = FIG / f"{OUTPUT_STEM}.png"
        fig.savefig(out, dpi=240, bbox_inches="tight")
        plt.close(fig)
        return out

    pos = spread_cluster_layout(g, community)
    xs = [xy[0] for xy in pos.values()]
    ys = [xy[1] for xy in pos.values()]
    pad_x = max((max(xs) - min(xs)) * 0.120, 0.62)
    pad_y = max((max(ys) - min(ys)) * 0.125, 0.62)
    ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
    ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)

    hubs = [
        node
        for node in g.nodes()
        if int(meta_by_author.get(node, {}).get("topic_count", 0)) >= 3 and g.degree(node) >= 3
    ]
    hub_set = set(hubs)

    weights = [g[u][v].get("weight", 0.0) for u, v in g.edges()]
    max_w = max(weights) if weights else 1
    for u, v, data in g.edges(data=True):
        weight = float(data.get("weight", 0.0))
        width = 0.30 + 2.30 * weight / max_w
        c1 = int(community.get(u, 1))
        c2 = int(community.get(v, 1))
        if c1 == c2:
            ax.plot(
                [pos[u][0], pos[v][0]],
                [pos[u][1], pos[v][1]],
                color="#B8B5C1",
                linewidth=width,
                alpha=0.26,
                zorder=1,
                solid_capstyle="round",
            )
        else:
            draw_gradient_edge(
                ax,
                pos[u],
                pos[v],
                PALETTE[(c1 - 1) % len(PALETTE)],
                PALETTE[(c2 - 1) % len(PALETTE)],
                width=0.55 + 3.25 * weight / max_w,
                alpha=0.58,
            )
    non_hubs = [node for node in g.nodes() if node not in hubs]
    node_size_lookup = {node: node_size_from_papers(int(meta_by_author.get(node, {}).get("paper_count", 1))) for node in g.nodes()}
    node_color_lookup = {node: PALETTE[(community.get(node, 1) - 1) % len(PALETTE)] for node in g.nodes()}

    non_hub_collection = nx.draw_networkx_nodes(
        g,
        pos,
        nodelist=non_hubs,
        ax=ax,
        node_size=[node_size_lookup[node] for node in non_hubs],
        node_color=[node_color_lookup[node] for node in non_hubs],
        linewidths=0.52,
        edgecolors="white",
        alpha=0.90,
    )
    non_hub_collection.set_zorder(4)
    hub_collection = nx.draw_networkx_nodes(
        g,
        pos,
        nodelist=hubs,
        ax=ax,
        node_size=[node_size_lookup[node] * 1.06 for node in hubs],
        node_color=[node_color_lookup[node] for node in hubs],
        linewidths=2.10,
        edgecolors="#FFFFFF",
        alpha=0.95,
    )
    hub_collection.set_zorder(5)

    weighted_degree = {
        node: sum(float(g[node][nbr].get("weight", 0.0)) for nbr in g.neighbors(node))
        for node in g.nodes()
    }
    scored = []
    for node in g.nodes():
        paper_count = int(meta_by_author[node]["paper_count"])
        topic_count = int(meta_by_author[node]["topic_count"])
        score = paper_count * 3.0 + g.degree(node) * 2.0 + weighted_degree[node] + topic_count * 1.7
        scored.append((score, node))
    score_lookup = {node: score for score, node in scored}
    selected_labels = sorted(hubs, key=lambda node: score_lookup.get(node, 0.0), reverse=True)

    labels: list[plt.Text] = []
    label_authors: list[str] = []
    x_mid = (min(xs) + max(xs)) / 2
    y_mid = (min(ys) + max(ys)) / 2
    cluster_centers: dict[int, tuple[float, float]] = {}
    for cid in set(community.values()):
        members = [node for node, node_cid in community.items() if node_cid == cid and node in pos]
        if not members:
            continue
        cluster_centers[cid] = (
            sum(pos[node][0] for node in members) / len(members),
            sum(pos[node][1] for node in members) / len(members),
        )
    for author in selected_labels:
        x, y = pos[author]
        cx, cy = cluster_centers.get(community.get(author, 0), (x_mid, y_mid))
        cluster_angle = math.atan2(y - cy, x - cx)
        global_angle = math.atan2(y - y_mid, x - x_mid)
        angle = global_angle * 0.68 + cluster_angle * 0.32
        if abs(x - x_mid) < 0.04 and abs(y - y_mid) < 0.04:
            angle = cluster_angle
        offset = 0.30 + math.sqrt(node_size_lookup[author]) / 150
        label = ax.text(
            x + math.cos(angle) * offset,
            y + math.sin(angle) * offset,
            display_author(author, chinese),
            ha="center",
            va="center",
            fontproperties=font_prop(10.15, "bold"),
            color="#FFFFFF",
            bbox={
                "boxstyle": "round,pad=0.18,rounding_size=0.14",
                "facecolor": (0, 0, 0, 0.70),
                "edgecolor": (1, 1, 1, 0.24),
                "linewidth": 0.35,
            },
            zorder=10,
        )
        labels.append(label)
        label_authors.append(author)
    place_labels_without_overlap(fig, ax, labels)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    clamp_x = (xlim[1] - xlim[0]) * 0.018
    clamp_y = (ylim[1] - ylim[0]) * 0.018
    for label in labels:
        lx, ly = label.get_position()
        label.set_position(
            (
                min(max(lx, xlim[0] + clamp_x), xlim[1] - clamp_x),
                min(max(ly, ylim[0] + clamp_y), ylim[1] - clamp_y),
            )
        )
    for author, label in zip(label_authors, labels):
        lx, ly = label.get_position()
        nx0, ny0 = pos[author]
        if math.hypot(lx - nx0, ly - ny0) > 0.30:
            ax.plot(
                [nx0, lx],
                [ny0, ly],
                color="#55505E",
                linewidth=0.58,
                alpha=0.36,
                zorder=8,
                solid_capstyle="round",
            )

    comm_sizes = Counter(community.values())
    metrics = [
        ("研发作者", f"{filtered_count}人"),
        ("稳定网络", f"{g.number_of_nodes()}人"),
        ("骨架关系", f"{g.number_of_edges()}条"),
        ("研发矩阵", f"{len(comm_sizes)}组"),
        ("跨界枢纽", f"{len(hubs)}人"),
    ]
    metric_y = 0.842
    for idx, (label, value) in enumerate(metrics):
        x = 0.062 + idx * 0.178
        fig.text(x, metric_y, value, ha="left", va="center", fontproperties=font_prop(16.8, "bold"), color=purple)
        fig.text(x, metric_y - 0.023, label, ha="left", va="center", fontproperties=font_prop(8.9), color="#555555")

    legend_ax = fig.add_axes([0.052, 0.104, 0.896, 0.090])
    legend_ax.set_axis_off()
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    for idx, cid in enumerate(GROUP_ORDER):
        row = idx // 4
        col = idx % 4
        x = 0.012 + col * 0.246
        y = 0.690 - row * 0.460
        if cid == 4:
            x += 0.060
        color = PALETTE[(cid - 1) % len(PALETTE)]
        label, _ = CLUSTER_LABELS[cid]
        count = comm_sizes.get(cid, 0)
        legend_ax.scatter([x], [y], s=88, color=color, linewidths=1.0, edgecolors="white", zorder=2)
        legend_ax.text(x + 0.026, y, f"{label}｜{count}人", ha="left", va="center", fontproperties=font_prop(11.65, "bold"), color=color)

    fig.add_artist(Rectangle((0.052, 0.091), 0.896, 0.0010, transform=fig.transFigure, color="#C8C5D1", linewidth=0))
    footer_font = font_prop(6.75)
    fig.text(0.052, 0.079, "数据来源：Hugging Face Papers API、DeepSeek-V4 PDF", ha="left", va="center", fontproperties=footer_font, color="#555555")
    fig.text(0.052, 0.066, "口径：V2/V3/V3.2/V4仅取Research & Engineering；R1按“R1署名∩V3 R&E”保守纳入；其他未拆角色论文使用原始署名并剔除团队名。", ha="left", va="center", fontproperties=footer_font, color="#555555")
    fig.text(0.052, 0.053, "口径补充：Research & Engineering 同时包含研究与工程角色，本文统称为“研发作者”。", ha="left", va="center", fontproperties=footer_font, color="#555555")
    fig.text(0.052, 0.040, f"算法：稳定边=s(i,j)≥{MIN_SHARED_PAPERS}且w(i,j)≥{MIN_FRACTIONAL_WEIGHT:.3f}，再保留每位作者最强{TOP_EDGES_PER_NODE}条边；小组为Louvain共著聚类；跨界枢纽=覆盖≥3个粗方向且稳定网络度数≥3。", ha="left", va="center", fontproperties=footer_font, color="#555555")
    fig.text(0.052, 0.027, "说明：姓名后*为作者已离职；图中的小组不代表真实组织架构、贡献大小或汇报关系。", ha="left", va="center", fontproperties=footer_font, color="#555555")
    fig.text(0.052, 0.014, "制图：甲子光年", ha="left", va="center", fontproperties=footer_font, color="#555555")
    draw_jiazi_logo(fig, x=0.805, y=0.020, scale=0.78)

    out = FIG / f"{OUTPUT_STEM}.png"
    svg = FIG / f"{OUTPUT_STEM}.svg"
    fig.savefig(out, dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(svg, facecolor=fig.get_facecolor())
    plt.close(fig)

    node_rows = []
    for node in sorted(g.nodes()):
        node_rows.append(
            {
                "author": node,
                "paper_count": meta_by_author[node]["paper_count"],
                "topic_count": meta_by_author[node]["topic_count"],
                "community": community.get(node, ""),
                "cluster_label": CLUSTER_LABELS.get(int(community.get(node, 0)), ("", ""))[0],
                "degree_in_demo": g.degree(node),
                "weighted_degree_in_demo": weighted_degree[node],
                "is_cross_direction_hub": node in hubs,
                "is_labeled": node in selected_labels,
            }
        )
    pd.DataFrame(node_rows).to_csv(OUT / "fig4_researcher_coauthor_demo_nodes.csv", index=False, encoding="utf-8-sig")
    stable_edges.to_csv(OUT / "fig4_researcher_coauthor_demo_edges.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(node_rows).to_csv(FIG / f"{OUTPUT_STEM}_nodes.csv", index=False, encoding="utf-8-sig")
    stable_edges.to_csv(FIG / f"{OUTPUT_STEM}_edges.csv", index=False, encoding="utf-8-sig")
    return out


def main() -> None:
    original, filtered = researcher_filtered_authors()
    filtered.to_csv(OUT / "paper_authors_researcher_filtered_demo.csv", index=False, encoding="utf-8-sig")
    filtered.to_csv(FIG / f"{OUTPUT_STEM}_research_author_pool.csv", index=False, encoding="utf-8-sig")

    meta = author_meta(filtered)
    edges = build_weighted_edges(filtered)
    g, skeleton = stable_subgraph(edges, meta)
    community = communities_for_graph(g)

    out = draw_demo(
        g,
        community,
        meta,
        original_count=original["clean_author_name"].nunique(),
        filtered_count=filtered["clean_author_name"].nunique(),
        stable_edges=skeleton,
    )
    print(f"original_unique_authors={original['clean_author_name'].nunique()}")
    print(f"researcher_filtered_unique_authors={filtered['clean_author_name'].nunique()}")
    print(f"demo_nodes={g.number_of_nodes()}")
    print(f"demo_edges={g.number_of_edges()}")
    print(f"demo_communities={len(set(community.values())) if community else 0}")
    print(out)


if __name__ == "__main__":
    main()

