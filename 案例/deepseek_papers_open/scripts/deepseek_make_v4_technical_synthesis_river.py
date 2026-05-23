from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT_DIR = BASE / "figures" / "technical_synthesis"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"
DATA = BASE / "figures" / "timeline" / "fig2_data_used_v9_base_model.csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_STEM = "fig5_v4_technical_synthesis_river_v1"

COLORS = {
    "main": "#6F35B6",
    "system": "#E45C9B",
    "math": "#2F9B72",
    "multi": "#E08C31",
    "ocr": "#8A8798",
    "code": "#2F6FB3",
    "text": "#15151A",
    "body": "#2F2F36",
    "muted": "#5B5B63",
    "line": "#C8C5D1",
}

MAIN_NODES = [
    {"key": "DeepSeek LLM", "label": "DeepSeek\nLLM", "date": "2024.01", "x": 0.12, "w": 0.100},
    {"key": "DeepSeek-V2", "label": "V2", "date": "2024.05", "x": 0.265, "w": 0.080},
    {"key": "DeepSeek-V3 Technical Report", "label": "V3", "date": "2024.12", "x": 0.420, "w": 0.080},
    {"key": "DeepSeek-R1", "label": "R1", "date": "2025.01", "x": 0.530, "w": 0.076},
    {"key": "DeepSeek-V3.2", "label": "V3.2", "date": "2025.12", "x": 0.695, "w": 0.090},
    {"key": "DeepSeek-V4", "label": "DeepSeek\nV4", "date": "2026.05", "x": 0.865, "w": 0.126},
]

BRANCHES = [
    {
        "group": "系统 / 效率支流",
        "subtitle": "长上下文、显存、稳定性、缓存",
        "color": COLORS["system"],
        "width": 4.9,
        "nodes": [
            {"name": "Sparse Attention", "note": "长上下文效率", "xy": (0.120, 0.705), "target": (0.690, 0.538), "rad": -0.24, "w": 0.128},
            {"name": "mHC", "note": "训练主干稳定", "xy": (0.285, 0.735), "target": (0.820, 0.540), "rad": -0.18, "w": 0.090},
            {"name": "Cond. Memory", "note": "显存优化", "xy": (0.438, 0.705), "target": (0.850, 0.542), "rad": -0.15, "w": 0.128},
            {"name": "DualPath", "note": "缓存 / 路径重构", "xy": (0.585, 0.735), "target": (0.875, 0.538), "rad": -0.10, "w": 0.108},
            {"name": "Insights into V3", "note": "模型维稳复盘", "xy": (0.300, 0.648), "target": (0.430, 0.540), "rad": -0.08, "w": 0.132},
        ],
    },
    {
        "group": "数学 / 推理支流",
        "subtitle": "可验证推理、奖励建模、泛化",
        "color": COLORS["math"],
        "width": 3.8,
        "nodes": [
            {"name": "DeepSeekMath 系列", "note": "数学能力底座", "xy": (0.705, 0.710), "target": (0.515, 0.540), "rad": 0.18, "w": 0.136},
            {"name": "DS-Prover 系列", "note": "可验证推理", "xy": (0.860, 0.725), "target": (0.560, 0.540), "rad": 0.20, "w": 0.128},
            {"name": "Reward Model", "note": "奖励建模", "xy": (0.820, 0.660), "target": (0.785, 0.532), "rad": -0.08, "w": 0.116},
        ],
    },
    {
        "group": "多模态 / OCR支流",
        "subtitle": "视觉、文档理解、跨模态经验",
        "color": COLORS["multi"],
        "width": 3.2,
        "nodes": [
            {"name": "DS-VL / VL2", "note": "视觉理解", "xy": (0.135, 0.300), "target": (0.420, 0.472), "rad": 0.20, "w": 0.112},
            {"name": "Janus / Janus-Pro", "note": "生成与理解", "xy": (0.318, 0.265), "target": (0.600, 0.474), "rad": 0.18, "w": 0.132},
            {"name": "DS-OCR / OCR 2", "note": "复杂文档视觉", "xy": (0.500, 0.310), "target": (0.835, 0.472), "rad": 0.16, "color": COLORS["ocr"], "w": 0.126},
        ],
    },
    {
        "group": "代码支流",
        "subtitle": "代码能力与工程底座",
        "color": COLORS["code"],
        "width": 3.0,
        "nodes": [
            {"name": "DS-Coder 系列", "note": "代码能力底座", "xy": (0.780, 0.300), "target": (0.340, 0.474), "rad": -0.24, "w": 0.124},
        ],
    },
]


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


def blend(color: str, target: str = "#FFFFFF", amount: float = 0.82) -> str:
    def parse(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    a = parse(color)
    b = parse(target)
    mixed = tuple(round(a[i] * (1 - amount) + b[i] * amount) for i in range(3))
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.790, y: float = 0.025, scale: float = 0.82) -> None:
    if not JIAZI_LOGO.exists():
        return
    try:
        logo_ax = fig.add_axes([x, y, 0.170 * scale, 0.060 * scale])
        logo_ax.imshow(plt.imread(JIAZI_LOGO))
        logo_ax.set_axis_off()
    except Exception:
        return


def pill(
    ax: plt.Axes,
    cx: float,
    cy: float,
    w: float,
    h: float,
    face: str,
    edge: str,
    title: str,
    note: str | None = None,
    title_size: float = 8.5,
    note_size: float = 6.7,
    title_color: str = "#15151A",
    lw: float = 1.0,
    z: int = 5,
) -> None:
    patch = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.006,rounding_size=0.018",
        linewidth=lw,
        edgecolor=edge,
        facecolor=face,
        zorder=z,
    )
    ax.add_patch(patch)
    if note:
        ax.text(cx, cy + h * 0.16, title, ha="center", va="center", fontproperties=font_prop(title_size, "bold"), color=title_color, zorder=z + 1)
        ax.text(cx, cy - h * 0.22, note, ha="center", va="center", fontproperties=font_prop(note_size), color=COLORS["muted"], zorder=z + 1)
    else:
        ax.text(cx, cy, title, ha="center", va="center", fontproperties=font_prop(title_size, "bold"), color=title_color, zorder=z + 1, linespacing=0.9)


def flow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    lw: float,
    rad: float,
    alpha: float = 0.55,
    z: int = 2,
) -> None:
    glow = FancyArrowPatch(
        start,
        end,
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>",
        mutation_scale=15,
        linewidth=lw + 4.0,
        color=color,
        alpha=0.14,
        shrinkA=13,
        shrinkB=18,
        zorder=z,
    )
    ax.add_patch(glow)
    line = FancyArrowPatch(
        start,
        end,
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=lw,
        color=color,
        alpha=alpha,
        shrinkA=14,
        shrinkB=18,
        zorder=z + 1,
    )
    ax.add_patch(line)


def group_title(ax: plt.Axes, x: float, y: float, title: str, subtitle: str, color: str, align: str = "left") -> None:
    ax.scatter([x], [y], s=42, color=color, edgecolors="white", linewidths=1.0, zorder=6)
    ha = "left" if align == "left" else "right"
    tx = x + 0.018 if align == "left" else x - 0.018
    ax.text(tx, y + 0.008, title, ha=ha, va="center", fontproperties=font_prop(10.2, "bold"), color=color, zorder=6)
    ax.text(tx, y - 0.016, subtitle, ha=ha, va="center", fontproperties=font_prop(7.4), color=COLORS["muted"], zorder=6)


def draw_main_spine(ax: plt.Axes) -> None:
    main_y = 0.505
    ax.add_patch(
        FancyArrowPatch(
            (0.075, main_y),
            (0.925, main_y),
            arrowstyle="-|>",
            mutation_scale=22,
            linewidth=12.5,
            color=COLORS["main"],
            alpha=0.25,
            zorder=1,
        )
    )
    ax.add_patch(
        FancyArrowPatch(
            (0.085, main_y),
            (0.915, main_y),
            arrowstyle="-|>",
            mutation_scale=20,
            linewidth=8.5,
            color=COLORS["main"],
            alpha=0.90,
            zorder=2,
        )
    )
    for idx, node in enumerate(MAIN_NODES):
        is_v4 = node["key"] == "DeepSeek-V4"
        w = float(node["w"])
        h = 0.056 if not is_v4 else 0.075
        x = float(node["x"])
        if is_v4:
            glow = FancyBboxPatch(
                (x - w / 2 - 0.010, main_y - h / 2 - 0.010),
                w + 0.020,
                h + 0.020,
                boxstyle="round,pad=0.006,rounding_size=0.028",
                linewidth=0,
                facecolor=COLORS["main"],
                alpha=0.18,
                zorder=3,
            )
            ax.add_patch(glow)
        face = COLORS["main"] if is_v4 else "#FFFFFF"
        edge = COLORS["main"]
        text_color = "#FFFFFF" if is_v4 else COLORS["main"]
        pill(
            ax,
            x,
            main_y,
            w,
            h,
            face,
            edge,
            str(node["label"]),
            title_size=12.0 if is_v4 else 10.0,
            title_color=text_color,
            lw=1.6 if is_v4 else 1.25,
            z=7,
        )
        ax.text(x, main_y - 0.050 if not is_v4 else main_y - 0.061, str(node["date"]), ha="center", va="center", fontproperties=font_prop(6.8), color="#7A7584", zorder=7)
        if idx < len(MAIN_NODES) - 1:
            next_x = float(MAIN_NODES[idx + 1]["x"])
            ax.text((x + next_x) / 2, main_y - 0.076, "→", ha="center", va="center", fontproperties=font_prop(9.8, "bold"), color=blend(COLORS["main"], amount=0.45), zorder=4)


def draw_branches(ax: plt.Axes) -> None:
    group_title(ax, 0.070, 0.775, "系统 / 效率支流", "最密集的底层填坑动作", COLORS["system"])
    group_title(ax, 0.628, 0.775, "数学 / 推理支流", "从数学、证明到奖励建模", COLORS["math"])
    group_title(ax, 0.070, 0.360, "多模态 / OCR支流", "视觉与复杂文档理解经验", COLORS["multi"])
    group_title(ax, 0.665, 0.360, "代码支流", "代码能力与工程底座", COLORS["code"])

    for group in BRANCHES:
        color = group["color"]
        for item in group["nodes"]:
            item_color = item.get("color", color)
            x, y = item["xy"]
            target = item["target"]
            flow(ax, (x, y), target, item_color, group["width"], item["rad"], alpha=0.66 if group["group"].startswith("系统") else 0.50)
    for group in BRANCHES:
        color = group["color"]
        for item in group["nodes"]:
            item_color = item.get("color", color)
            title_size = 7.0 if len(item["name"]) > 13 else 7.3
            pill(
                ax,
                item["xy"][0],
                item["xy"][1],
                item.get("w", 0.118 if len(item["name"]) <= 13 else 0.138),
                item.get("h", 0.040),
                blend(item_color, amount=0.88),
                item_color,
                item["name"],
                item["note"],
                title_size=title_size,
                note_size=5.9,
                title_color=item_color,
                lw=1.05,
                z=8,
            )


def draw_header(fig: plt.Figure) -> None:
    fig.add_artist(Rectangle((0.044, 0.920), 0.006, 0.060, transform=fig.transFigure, color=COLORS["main"], linewidth=0))
    fig.text(0.062, 0.957, "V4是如何炼成的？", ha="left", va="center", fontproperties=font_prop(23.0, "bold"), color=COLORS["text"])
    fig.text(0.062, 0.920, "一场历时一年、死磕底层的系统级大缝合", ha="left", va="center", fontproperties=font_prop(16.8, "bold"), color=COLORS["text"])
    fig.text(
        0.062,
        0.880,
        "过去一年，DeepSeek把注意力机制、训练稳定性、缓存与长上下文等“补丁”不断打进主干，最终收束于 V4。",
        ha="left",
        va="center",
        fontproperties=font_prop(10.9),
        color=COLORS["body"],
    )
    fig.text(
        0.062,
        0.856,
        "这些看起来枯燥的系统论文，不是散点，而是在算力受限下给更大模型造桥铺路。",
        ha="left",
        va="center",
        fontproperties=font_prop(10.9),
        color=COLORS["body"],
    )


def draw_v4_callout(ax: plt.Axes) -> None:
    ax.plot([0.735, 0.815], [0.605, 0.548], color=COLORS["main"], linewidth=1.05, alpha=0.65, zorder=9)
    ax.scatter([0.815], [0.548], s=20, color=COLORS["main"], zorder=10)
    ax.text(0.675, 0.615, "V4：技术支流的汇合点", ha="left", va="center", fontproperties=font_prop(8.6, "bold"), color=COLORS["main"], zorder=10)
    ax.text(0.675, 0.592, "底层修补动作的汇总交卷", ha="left", va="center", fontproperties=font_prop(6.9), color=COLORS["body"], zorder=10)


def draw_takeaways(ax: plt.Axes) -> None:
    items = [
        (COLORS["main"], "不是突变", "V4是系统、数学、推理、多模态等支流的大收束"),
        (COLORS["system"], "不是追热点", "最密集投入落在系统/效率底座，而非应用外壳"),
        (COLORS["math"], "不是口号", "算力受限下的死磕，体现为连续论文和工程补丁"),
    ]
    xs = [0.082, 0.372, 0.662]
    for x, (color, title, body) in zip(xs, items):
        ax.add_patch(Rectangle((x, 0.155), 0.006, 0.050, color=color, linewidth=0, zorder=4))
        ax.text(x + 0.018, 0.190, title, ha="left", va="center", fontproperties=font_prop(9.8, "bold"), color=color, zorder=4)
        ax.text(x + 0.018, 0.166, body, ha="left", va="center", fontproperties=font_prop(7.2), color=COLORS["body"], zorder=4)


def draw_footer(fig: plt.Figure) -> None:
    fig.add_artist(Rectangle((0.052, 0.118), 0.896, 0.0010, transform=fig.transFigure, color=COLORS["line"], linewidth=0))
    footer = font_prop(7.05)
    fig.text(0.052, 0.096, "数据来源：DeepSeek 各论文/技术报告，Hugging Face Papers API，论文正文人工整理。", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.077, "口径：按论文发布时间梳理主线与技术支流，重点展示系统、推理、数学、多模态等方向对 V4 的汇入关系。", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.058, "注：主干表示主线模型演进；两侧支流表示相关论文或技术模块；连线为解释性技术反哺与能力收束关系，并非严格因果证明。", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.039, "制图：甲子光年", ha="left", va="center", fontproperties=footer, color="#555555")
    draw_jiazi_logo(fig, x=0.805, y=0.030, scale=0.78)


def export_node_table() -> None:
    rows: list[dict[str, object]] = []
    for node in MAIN_NODES:
        rows.append({"type": "main", "group": "主干", "name": node["key"], "label": node["label"], "date_label": node["date"], "x": node["x"], "y": 0.505})
    for group in BRANCHES:
        for item in group["nodes"]:
            rows.append(
                {
                    "type": "branch",
                    "group": group["group"],
                    "name": item["name"],
                    "label": item["note"],
                    "date_label": "",
                    "x": item["xy"][0],
                    "y": item["xy"][1],
                    "target_x": item["target"][0],
                    "target_y": item["target"][1],
                }
            )
    if DATA.exists():
        data = pd.read_csv(DATA, encoding="utf-8-sig")
        lookup = data.set_index("short_title").to_dict("index")
        for row in rows:
            if row["name"] in lookup:
                row["paper_id"] = lookup[row["name"]].get("paper_id", "")
                row["year_month"] = lookup[row["name"]].get("year_month", "")
                row["coarse_topic"] = lookup[row["name"]].get("coarse_topic", "")
    pd.DataFrame(rows).to_csv(OUT_DIR / f"{OUTPUT_STEM}_nodes.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    configure_font()
    fig = plt.figure(figsize=(8.35, 11.8), dpi=240)
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    draw_header(fig)
    draw_main_spine(ax)
    draw_branches(ax)
    draw_v4_callout(ax)
    draw_takeaways(ax)
    draw_footer(fig)

    out_png = OUT_DIR / f"{OUTPUT_STEM}.png"
    out_svg = OUT_DIR / f"{OUTPUT_STEM}.svg"
    fig.savefig(out_png, dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(out_svg, facecolor=fig.get_facecolor())
    plt.close(fig)
    export_node_table()
    print(out_png)
    print(out_svg)


if __name__ == "__main__":
    main()

