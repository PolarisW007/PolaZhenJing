from __future__ import annotations

import csv
import html
import math
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output"
FIG = ROOT / "figures" / "timeline"
FIG.mkdir(parents=True, exist_ok=True)


COLORS = {
    "主模型": "#c23b3b",
    "代码": "#2f6fbb",
    "数学/证明": "#2f8f5b",
    "多模态": "#d68428",
    "OCR": "#6f6f7a",
    "系统/效率": "#2a9d9b",
    "推理/RL": "#8b61b5",
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


def count_for_chart(row: dict) -> int:
    if row["short_title"] == "DeepSeek-V4":
        return 269
    return int(row["author_count"])


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["author_count"] = int(row["author_count"])
        row["author_count_for_chart"] = count_for_chart(row)
        row["count_note"] = "V4 总名单 317；作图使用 Research & Engineering 269" if row["short_title"] == "DeepSeek-V4" else ""
    rows.sort(key=lambda r: (r["year_month"], r["short_title"]))
    return rows


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def month_number(ym: str) -> int:
    year, month = ym.split("-")
    return int(year) * 12 + int(month)


def month_label(month_num: int) -> str:
    year = month_num // 12
    month = month_num % 12
    if month == 0:
        year -= 1
        month = 12
    return f"{year}-{month:02d}"


def make_svg(width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif; fill: #222; }}
.title {{ font-size: 30px; font-weight: 700; }}
.subtitle {{ font-size: 16px; fill: #555; }}
.axis {{ font-size: 13px; fill: #666; }}
.label {{ font-size: 13px; fill: #222; font-weight: 600; }}
.small {{ font-size: 12px; fill: #555; }}
.legend {{ font-size: 13px; fill: #333; }}
.grid {{ stroke: #dedede; stroke-width: 1; }}
.axis-line {{ stroke: #777; stroke-width: 1.2; }}
</style>
<rect width="100%" height="100%" fill="#fffdf9"/>
{body}
</svg>
"""


def legend(items: list[str], x: int, y: int) -> str:
    parts = []
    cursor_x = x
    cursor_y = y
    for item in items:
        color = COLORS[item]
        parts.append(f'<circle cx="{cursor_x}" cy="{cursor_y - 4}" r="6" fill="{color}"/>')
        parts.append(f'<text class="legend" x="{cursor_x + 12}" y="{cursor_y}">{esc(item)}</text>')
        cursor_x += 112 if item != "数学/证明" else 132
        if cursor_x > 1180:
            cursor_x = x
            cursor_y += 24
    return "\n".join(parts)


def scatter_chart(rows: list[dict]) -> str:
    width, height = 1400, 860
    margin = {"left": 92, "right": 80, "top": 142, "bottom": 110}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    min_m = month_number(min(r["year_month"] for r in rows))
    max_m = month_number(max(r["year_month"] for r in rows))
    y_max = 340

    by_month = defaultdict(list)
    for row in rows:
        by_month[row["year_month"]].append(row)

    def x_pos(row: dict) -> float:
        m = month_number(row["year_month"])
        base = margin["left"] + (m - min_m) / (max_m - min_m) * plot_w
        same = by_month[row["year_month"]]
        if len(same) == 1:
            return base
        idx = sorted(same, key=lambda r: r["short_title"]).index(row)
        offset = (idx - (len(same) - 1) / 2) * 18
        return base + offset

    def y_pos(value: int) -> float:
        return margin["top"] + plot_h - value / y_max * plot_h

    parts = [
        '<text class="title" x="72" y="54">DeepSeek 论文作者数变化：小队论文与大兵团报告并存</text>',
        '<text class="subtitle" x="72" y="84">27 篇论文 / 技术报告；点的位置为发布时间，纵轴为去重作者数。V4 作图口径使用 Research & Engineering 的 269 人。</text>',
        legend(list(COLORS), 72, 120),
    ]

    for tick in range(0, y_max + 1, 50):
        y = y_pos(tick)
        parts.append(f'<line class="grid" x1="{margin["left"]}" y1="{y:.1f}" x2="{width - margin["right"]}" y2="{y:.1f}"/>')
        parts.append(f'<text class="axis" x="{margin["left"] - 16}" y="{y + 4:.1f}" text-anchor="end">{tick}</text>')

    parts.append(
        f'<line class="axis-line" x1="{margin["left"]}" y1="{margin["top"] + plot_h}" '
        f'x2="{width - margin["right"]}" y2="{margin["top"] + plot_h}"/>'
    )
    parts.append(
        f'<line class="axis-line" x1="{margin["left"]}" y1="{margin["top"]}" '
        f'x2="{margin["left"]}" y2="{margin["top"] + plot_h}"/>'
    )
    parts.append(f'<text class="axis" x="28" y="{margin["top"] + 20}" transform="rotate(-90 28,{margin["top"] + 20})">去重作者数</text>')

    # Month ticks every three months.
    for m in range(min_m, max_m + 1):
        if (m - min_m) % 3 != 0 and m != max_m:
            continue
        x = margin["left"] + (m - min_m) / (max_m - min_m) * plot_w
        parts.append(f'<line x1="{x:.1f}" y1="{margin["top"] + plot_h}" x2="{x:.1f}" y2="{margin["top"] + plot_h + 6}" stroke="#777"/>')
        parts.append(f'<text class="axis" x="{x:.1f}" y="{margin["top"] + plot_h + 28}" text-anchor="middle">{month_label(m)}</text>')

    # Light connector for the main model chain.
    main_rows = [r for r in rows if r["main_model_stage"]]
    line_points = []
    for row in main_rows:
        count = row["author_count_for_chart"]
        line_points.append(f'{x_pos(row):.1f},{y_pos(count):.1f}')
    parts.append(f'<polyline points="{" ".join(line_points)}" fill="none" stroke="#c23b3b" stroke-width="2.5" stroke-opacity="0.5"/>')

    for row in rows:
        count = row["author_count_for_chart"]
        x, y = x_pos(row), y_pos(count)
        color = COLORS[row["coarse_topic"]]
        r = 7 if row["main_model_stage"] else 5
        stroke = "#222" if row["main_model_stage"] else "#fffdf9"
        stroke_w = 1.6 if row["main_model_stage"] else 1
        tooltip = f'{row["short_title"]}｜{row["year_month"]}｜{row["coarse_topic"]}｜作者数 {count}'
        parts.append(f'<g><title>{esc(tooltip)}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_w}"/></g>')

        if row["short_title"] in LABELS:
            dx = 10
            dy = -10
            if row["short_title"] in {"DeepSeek-R1", "DeepSeek-V3 Technical Report"}:
                dy = 18
            if row["short_title"] == "DeepSeek-V4":
                dx = -110
                dy = -12
            label = f'{row["short_title"]} {count}'
            if row["short_title"] == "DeepSeek-V4":
                label = "DeepSeek-V4 269 / 总317"
            parts.append(f'<text class="label" x="{x + dx:.1f}" y="{y + dy:.1f}">{esc(label)}</text>')

    parts.append(
        f'<text class="small" x="{width - margin["right"]}" y="{height - 28}" text-anchor="end">'
        '数据：HF Papers API、DeepSeek-V4 PDF；清洗：剔除团队名、同篇去重、补 HF 漏人</text>'
    )
    return make_svg(width, height, "\n".join(parts))


def bar_chart(rows: list[dict]) -> str:
    width, height = 1600, 900
    margin = {"left": 78, "right": 44, "top": 122, "bottom": 245}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]
    y_max = 340

    def y_pos(value: int) -> float:
        return margin["top"] + plot_h - value / y_max * plot_h

    bar_gap = 8
    bar_w = (plot_w - bar_gap * (len(rows) - 1)) / len(rows)

    parts = [
        '<text class="title" x="72" y="54">27 篇 DeepSeek 论文的作者规模</text>',
        '<text class="subtitle" x="72" y="84">每根柱代表一篇论文；颜色为粗方向。V4 柱高使用 Research & Engineering 269 人，总名单 317 人另作备注。</text>',
        legend(list(COLORS), 72, 118),
    ]

    for tick in range(0, y_max + 1, 50):
        y = y_pos(tick)
        parts.append(f'<line class="grid" x1="{margin["left"]}" y1="{y:.1f}" x2="{width - margin["right"]}" y2="{y:.1f}"/>')
        parts.append(f'<text class="axis" x="{margin["left"] - 14}" y="{y + 4:.1f}" text-anchor="end">{tick}</text>')

    parts.append(
        f'<line class="axis-line" x1="{margin["left"]}" y1="{margin["top"] + plot_h}" '
        f'x2="{width - margin["right"]}" y2="{margin["top"] + plot_h}"/>'
    )
    parts.append(
        f'<line class="axis-line" x1="{margin["left"]}" y1="{margin["top"]}" '
        f'x2="{margin["left"]}" y2="{margin["top"] + plot_h}"/>'
    )

    baseline = margin["top"] + plot_h
    for i, row in enumerate(rows):
        count = row["author_count_for_chart"]
        x = margin["left"] + i * (bar_w + bar_gap)
        y = y_pos(count)
        h = baseline - y
        color = COLORS[row["coarse_topic"]]
        stroke = "#222" if row["main_model_stage"] else "none"
        stroke_w = 1.2 if row["main_model_stage"] else 0
        tooltip = f'{row["short_title"]}｜{row["year_month"]}｜{row["coarse_topic"]}｜作者数 {count}'
        parts.append(f'<g><title>{esc(tooltip)}</title><rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_w}"/></g>')

        if count >= 30 or row["short_title"] in LABELS:
            parts.append(f'<text class="small" x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle">{count}</text>')

        label = row["short_title"].replace("DeepSeek-", "DS-").replace(" Technical Report", "")
        angle_x = x + bar_w / 2
        parts.append(
            f'<text class="axis" x="{angle_x:.1f}" y="{baseline + 18}" text-anchor="end" '
            f'transform="rotate(-55 {angle_x:.1f},{baseline + 18})">{esc(label)}</text>'
        )

    parts.append(
        f'<text class="small" x="{width - margin["right"]}" y="{height - 28}" text-anchor="end">'
        '数据：HF Papers API、DeepSeek-V4 PDF；清洗：剔除团队名、同篇去重、补 HF 漏人</text>'
    )
    return make_svg(width, height, "\n".join(parts))


def main() -> None:
    rows = read_rows(DATA / "chart2_paper_author_counts.csv")

    # Keep a frozen copy of the exact rows used for this draft figure.
    with (FIG / "fig2_data_used.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "paper_id",
            "year_month",
            "short_title",
            "coarse_topic",
            "author_count",
            "author_count_for_chart",
            "main_model_stage",
            "count_note",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    scatter = scatter_chart(rows)
    (FIG / "fig2_author_count_scatter.svg").write_text(scatter, encoding="utf-8")

    bars = bar_chart(rows)
    (FIG / "fig2_author_count_bar.svg").write_text(bars, encoding="utf-8")

    preview = f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>DeepSeek Figure 2 Drafts</title>
<style>
body {{ margin: 24px; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f6f4ef; color: #222; }}
h1 {{ font-size: 24px; }}
section {{ margin: 28px 0 48px; }}
img {{ display: block; max-width: 100%; height: auto; background: white; border: 1px solid #ddd; }}
</style>
<h1>DeepSeek 论文作者数变化：两版草图</h1>
<section>
  <h2>散点图版</h2>
  <img src="fig2_author_count_scatter.svg" alt="DeepSeek 论文作者数变化散点图">
</section>
<section>
  <h2>条形图版</h2>
  <img src="fig2_author_count_bar.svg" alt="DeepSeek 论文作者数变化条形图">
</section>
</html>
"""
    (FIG / "fig2_preview.html").write_text(preview, encoding="utf-8")

    print(FIG)


if __name__ == "__main__":
    main()

