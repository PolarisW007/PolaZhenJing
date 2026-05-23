from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT
RAW = DATA / "raw"
OUT = DATA / "output"
OUT.mkdir(parents=True, exist_ok=True)


PAPERS = [
    ("2401.02954", "DeepSeek LLM", "2024-01", "主模型", "V1/LLM"),
    ("2401.06066", "DeepSeekMoE", "2024-01", "系统/效率", ""),
    ("2401.14196", "DeepSeek-Coder", "2024-01", "代码", ""),
    ("2402.03300", "DeepSeekMath", "2024-02", "数学/证明", ""),
    ("2403.05525", "DeepSeek-VL", "2024-03", "多模态", ""),
    ("2405.04434", "DeepSeek-V2", "2024-05", "主模型", "V2"),
    ("2405.14333", "DeepSeek-Prover", "2024-05", "数学/证明", ""),
    ("2406.11931", "DeepSeek-Coder-V2", "2024-06", "代码", ""),
    ("2407.01906", "ESFT", "2024-07", "系统/效率", ""),
    ("2408.08152", "DeepSeek-Prover-V1.5", "2024-08", "数学/证明", ""),
    ("2410.13848", "Janus", "2024-10", "多模态", ""),
    ("2412.10302", "DeepSeek-VL2", "2024-12", "多模态", ""),
    ("2412.19437", "DeepSeek-V3 Technical Report", "2024-12", "主模型", "V3"),
    ("2501.12948", "DeepSeek-R1", "2025-01", "推理/RL", "R1"),
    ("2501.17811", "Janus-Pro", "2025-01", "多模态", ""),
    ("2502.11089", "Native Sparse Attention", "2025-02", "系统/效率", ""),
    ("2504.02495", "Generalist Reward Modeling", "2025-04", "推理/RL", ""),
    ("2504.21801", "DeepSeek-Prover-V2", "2025-04", "数学/证明", ""),
    ("2505.09343", "Insights into DeepSeek-V3", "2025-05", "系统/效率", ""),
    ("2510.18234", "DeepSeek-OCR", "2025-10", "OCR", ""),
    ("2511.22570", "DeepSeekMath-V2", "2025-11", "数学/证明", ""),
    ("2512.02556", "DeepSeek-V3.2", "2025-12", "主模型", "V3.2"),
    ("2512.24880", "mHC", "2025-12", "系统/效率", ""),
    ("2601.07372", "Conditional Memory", "2026-01", "系统/效率", ""),
    ("2601.20552", "DeepSeek-OCR 2", "2026-01", "OCR", ""),
    ("2602.21548", "DualPath", "2026-02", "系统/效率", ""),
    ("V4-PDF", "DeepSeek-V4", "2026-05", "主模型", "V4"),
]


PAPER_META = {
    paper_id: {
        "paper_id": paper_id,
        "short_title": short_title,
        "year_month": year_month,
        "coarse_topic": topic,
        "main_model_stage": stage,
    }
    for paper_id, short_title, year_month, topic, stage in PAPERS
}


MANUAL_ADDED_AUTHORS = {
    # HF API misses these names; verified against paper author blocks.
    "2402.03300": ["Haowei Zhang", "Xiao Bi"],
    "2403.05525": ["Hao Yang"],
    "2512.24880": ["Kuai Yu"],
}


TEAM_NAMES = {"DeepSeek-AI", "DeepSeek AI", "DeepSeek", ":"}


MANUAL_NAME_MAP = {
    "YuKun Li": "Yukun Li",
    "Y.K. Li": "Yukun Li",
    "Y.K Li": "Yukun Li",
    "Y. K Li": "Yukun Li",
    "Y. K. Li": "Yukun Li",
    "Y. Wu": "Yu Wu",
    "R.X. Xu": "Runxin Xu",
    "R.X Xu": "Runxin Xu",
    "R. X Xu": "Runxin Xu",
    "R. X. Xu": "Runxin Xu",
    "M.S. Di": "M. S. Di",
    "M. S Di": "M. S. Di",
    "M.Y Xu": "M. Y Xu",
    "M. Y. Xu": "M. Y Xu",
    "J.Q. Zhu": "J. Q. Zhu",
    "J. Q Zhu": "J. Q. Zhu",
    "Y.Q. Wang": "Y. Q. Wang",
    "Y. Q Wang": "Y. Q. Wang",
    "Y.W. Ma": "Y. W. Ma",
    "Y. W Ma": "Y. W. Ma",
    "Y.C. Yan": "Y. C. Yan",
    "Y. C Yan": "Y. C. Yan",
    "Z.F. Wu": "Z. F. Wu",
    "Z. F Wu": "Z. F. Wu",
    "S.H. Liu": "S. H. Liu",
    "S. H Liu": "S. H. Liu",
    "W.L. Xiao": "W. L. Xiao",
    "W. L Xiao": "W. L. Xiao",
    "Dengr Chengqi": "Chengqi Deng",
    "Li Y. K.": "Yukun Li",
    "Wu Y.": "Yu Wu",
    "Xu R. X.": "Runxin Xu",
    "Wei Y. X.": "Y. X. Wei",
    "Zhu Y. X.": "Y. X. Zhu",
    "Xiao W. L.": "W. L. Xiao",
    "Wang T.": "T. Wang",
    "Cai J. L.": "J. L. Cai",
    "Chen R. J.": "R. J. Chen",
    "Jin R. L.": "R. L. Jin",
    "Li S. S.": "S. S. Li",
    "Li X. Q.": "X. Q. Li",
    "Ren Z. Z.": "Z. Z. Ren",
    "Zhang H.": "H. Zhang",
}


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def clean_spaces(name: str) -> str:
    name = name.replace("\u00a0", " ").strip()
    name = re.sub(r"\s+", " ", name)
    name = name.replace("＊", "*")
    return name


def basic_name(name: str) -> str:
    name = clean_spaces(name)
    name = name.strip(",;")
    name = re.sub(r"\*$", "", name).strip()
    name = re.sub(r"([A-Z])\.([A-Z])\.", r"\1. \2.", name)
    name = re.sub(r"([A-Z])\.([A-Z])", r"\1. \2", name)
    name = re.sub(r"\s+", " ", name)
    return MANUAL_NAME_MAP.get(name, name)


def read_hf_source_rows() -> tuple[list[dict], dict[str, dict]]:
    rows = []
    title_by_id = {}
    for paper_id, meta in PAPER_META.items():
        if paper_id == "V4-PDF":
            continue
        path = RAW / f"hf_api_{paper_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        title_by_id[paper_id] = {
            "title": payload.get("title", meta["short_title"]),
            "published_at": payload.get("publishedAt", ""),
            "source_url": f"https://huggingface.co/papers/{paper_id}",
        }
        for order, author in enumerate(payload.get("authors", []), start=1):
            rows.append(
                {
                    **meta,
                    "title": payload.get("title", meta["short_title"]),
                    "source": "hf_api",
                    "source_url": f"https://huggingface.co/papers/{paper_id}",
                    "raw_order": order,
                    "raw_author_name": clean_spaces(author.get("name", "")),
                    "v4_group": "",
                    "departed_mark": "",
                    "manual_note": "",
                }
            )
    return rows, title_by_id


def parse_v4_pdf_rows() -> list[dict]:
    if PdfReader is None:
        raise RuntimeError("pypdf is not available")
    pdf_path = RAW / "DeepSeek_V4.pdf"
    reader = PdfReader(str(pdf_path))
    text = "\n".join((reader.pages[i].extract_text() or "") for i in [53, 54])
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)
    text = re.sub(r"\s+", " ", text)

    research = text.split("Research & Engineering:", 1)[1].split("Business & Compliance:", 1)[0]
    business = text.split("Business & Compliance:", 1)[1].split("A.2. Acknowledgment", 1)[0]

    rows = []
    order = 0
    for group, chunk in [("Research & Engineering", research), ("Business & Compliance", business)]:
        for part in chunk.split(","):
            name = clean_spaces(part)
            name = name.strip(" .")
            if not name:
                continue
            order += 1
            departed = "TRUE" if "*" in name else "FALSE"
            rows.append(
                {
                    **PAPER_META["V4-PDF"],
                    "title": "DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence",
                    "source": "v4_pdf_text",
                    "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/DeepSeek_V4.pdf",
                    "raw_order": order,
                    "raw_author_name": name,
                    "v4_group": group,
                    "departed_mark": departed,
                    "manual_note": "V4 PDF author list; raw list includes duplicate Yao Li",
                }
            )
    return rows


def add_manual_rows(rows: list[dict]) -> None:
    max_order = defaultdict(int)
    for row in rows:
        max_order[row["paper_id"]] = max(max_order[row["paper_id"]], int(row["raw_order"]))

    for paper_id, names in MANUAL_ADDED_AUTHORS.items():
        meta = PAPER_META[paper_id]
        title = next((r["title"] for r in rows if r["paper_id"] == paper_id), meta["short_title"])
        for name in names:
            max_order[paper_id] += 1
            rows.append(
                {
                    **meta,
                    "title": title,
                    "source": "manual_author_block_fix",
                    "source_url": f"https://arxiv.org/abs/{paper_id}",
                    "raw_order": max_order[paper_id],
                    "raw_author_name": name,
                    "v4_group": "",
                    "departed_mark": "",
                    "manual_note": "HF API missing author; added from original author block",
                }
            )


def build_reverse_alias(rows: list[dict]) -> dict[str, str]:
    names = []
    v4_names = set()
    for row in rows:
        raw = row["raw_author_name"]
        if raw in TEAM_NAMES:
            continue
        name = basic_name(raw)
        names.append(name)
        if row["paper_id"] == "V4-PDF":
            v4_names.add(name)

    counts = Counter(names)
    aliases = {}
    for name in list(counts):
        parts = name.split()
        if len(parts) != 2:
            continue
        rev = f"{parts[1]} {parts[0]}"
        if rev not in counts or name == rev:
            continue
        if name in v4_names and rev not in v4_names:
            canonical = name
        elif rev in v4_names and name not in v4_names:
            canonical = rev
        elif counts[name] > counts[rev]:
            canonical = name
        elif counts[rev] > counts[name]:
            canonical = rev
        else:
            canonical = min(name, rev)
        aliases[name] = canonical
        aliases[rev] = canonical
    return aliases


def make_clean_rows(source_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    reverse_alias = build_reverse_alias(source_rows)
    cleaned = []
    quality = []
    seen = set()

    for row in source_rows:
        raw = row["raw_author_name"]
        if raw in TEAM_NAMES:
            quality.append(
                {
                    "paper_id": row["paper_id"],
                    "issue_type": "excluded_team_name",
                    "detail": raw,
                    "action": "excluded from personal author counts",
                }
            )
            continue
        name = basic_name(raw)
        name = reverse_alias.get(name, name)
        key = (row["paper_id"], name)
        duplicate = key in seen
        if duplicate:
            quality.append(
                {
                    "paper_id": row["paper_id"],
                    "issue_type": "deduplicated_author",
                    "detail": name,
                    "action": "kept first occurrence only",
                }
            )
            continue
        seen.add(key)
        cleaned.append(
            {
                **row,
                "raw_author_name": raw,
                "clean_author_name": name,
                "canonical_changed": "TRUE" if name != basic_name(raw) else "FALSE",
            }
        )
    return cleaned, quality


def derive_outputs(clean_rows: list[dict], quality_rows: list[dict]) -> None:
    papers = []
    for paper_id, meta in PAPER_META.items():
        rows = [r for r in clean_rows if r["paper_id"] == paper_id]
        first = rows[0] if rows else meta
        papers.append(
            {
                **meta,
                "title": first.get("title", meta["short_title"]),
                "author_count_clean": len({r["clean_author_name"] for r in rows}),
                "source_url": first.get("source_url", ""),
            }
        )

    chart2 = [
        {
            "paper_id": p["paper_id"],
            "year_month": p["year_month"],
            "short_title": p["short_title"],
            "coarse_topic": p["coarse_topic"],
            "author_count": p["author_count_clean"],
            "main_model_stage": p["main_model_stage"],
        }
        for p in papers
    ]

    by_author = defaultdict(list)
    by_paper = defaultdict(set)
    by_paper_comparable_main = defaultdict(set)
    topic_by_author = defaultdict(set)
    for row in clean_rows:
        author = row["clean_author_name"]
        by_author[author].append(row)
        by_paper[row["paper_id"]].add(author)
        if row["paper_id"] != "V4-PDF" or row["v4_group"] != "Business & Compliance":
            by_paper_comparable_main[row["paper_id"]].add(author)
        topic_by_author[author].add(row["coarse_topic"])

    high_freq = []
    for author, rows in by_author.items():
        paper_ids = sorted({r["paper_id"] for r in rows}, key=lambda pid: PAPER_META[pid]["year_month"])
        if len(paper_ids) >= 4:
            topics = sorted({r["coarse_topic"] for r in rows})
            high_freq.append(
                {
                    "author": author,
                    "paper_count": len(paper_ids),
                    "topic_count": len(topics),
                    "topics": "、".join(topics),
                    "first_seen": min(PAPER_META[pid]["year_month"] for pid in paper_ids),
                    "last_seen": max(PAPER_META[pid]["year_month"] for pid in paper_ids),
                    "papers": "；".join(PAPER_META[pid]["short_title"] for pid in paper_ids),
                }
            )
    high_freq.sort(key=lambda r: (-int(r["paper_count"]), r["author"]))

    topic_order = ["主模型", "代码", "数学/证明", "多模态", "OCR", "系统/效率", "推理/RL"]
    matrix = []
    for row in high_freq:
        author_rows = by_author[row["author"]]
        out = {
            "author": row["author"],
            "paper_count": row["paper_count"],
            "topic_count": row["topic_count"],
        }
        for topic in topic_order:
            out[topic] = len({r["paper_id"] for r in author_rows if r["coarse_topic"] == topic})
        matrix.append(out)

    main_chain_ids = ["2401.02954", "2405.04434", "2412.19437", "2501.12948", "2512.02556", "V4-PDF"]
    main_stage_by_id = {pid: PAPER_META[pid]["main_model_stage"] for pid in main_chain_ids}
    main_authors = sorted(set().union(*(by_paper_comparable_main[pid] for pid in main_chain_ids)))
    retention = []
    for author in main_authors:
        out = {"author": author}
        total = 0
        for pid in main_chain_ids:
            present = 1 if author in by_paper_comparable_main[pid] else 0
            out[main_stage_by_id[pid]] = present
            total += present
        out["main_model_paper_count"] = total
        retention.append(out)
    retention.sort(key=lambda r: (-r["main_model_paper_count"], r["author"]))

    main_scale = [
        {
            "stage": PAPER_META[pid]["main_model_stage"],
            "paper_id": pid,
            "year_month": PAPER_META[pid]["year_month"],
            "short_title": PAPER_META[pid]["short_title"],
            "author_count_for_chart": len(by_paper_comparable_main[pid]),
            "author_count_total": len(by_paper[pid]),
            "author_count_comparable": len(by_paper_comparable_main[pid]),
            "note": "V4 total includes Business & Compliance; comparable count keeps Research & Engineering only"
            if pid == "V4-PDF"
            else "",
        }
        for pid in main_chain_ids
    ]

    # Coauthor network: full author nodes, but edges are capped to repeated collaboration
    # so the visual is not dominated by one-off pairings in huge reports.
    author_stats = {}
    for author, rows in by_author.items():
        author_stats[author] = {
            "author": author,
            "paper_count": len({r["paper_id"] for r in rows}),
            "topic_count": len({r["coarse_topic"] for r in rows}),
            "first_seen": min(PAPER_META[r["paper_id"]]["year_month"] for r in rows),
            "last_seen": max(PAPER_META[r["paper_id"]]["year_month"] for r in rows),
            "is_high_freq_ge4": "TRUE" if len({r["paper_id"] for r in rows}) >= 4 else "FALSE",
        }

    edge_counter = Counter()
    edge_topics = defaultdict(set)
    edge_papers = defaultdict(set)
    for paper_id, authors in by_paper.items():
        # For huge all-hands reports, keep them in the source table but exclude
        # them from edge generation. Otherwise every author connects to every
        # other author and the network becomes unreadable.
        if len(authors) > 120:
            continue
        for a, b in combinations(sorted(authors), 2):
            edge_counter[(a, b)] += 1
            edge_topics[(a, b)].add(PAPER_META[paper_id]["coarse_topic"])
            edge_papers[(a, b)].add(PAPER_META[paper_id]["short_title"])

    edges = []
    degree = Counter()
    weighted_degree = Counter()
    for (a, b), weight in edge_counter.items():
        if weight < 2:
            continue
        degree[a] += 1
        degree[b] += 1
        weighted_degree[a] += weight
        weighted_degree[b] += weight
        edges.append(
            {
                "source": a,
                "target": b,
                "weight_shared_papers": weight,
                "topics": "、".join(sorted(edge_topics[(a, b)])),
                "papers": "；".join(sorted(edge_papers[(a, b)])),
            }
        )
    edges.sort(key=lambda r: (-r["weight_shared_papers"], r["source"], r["target"]))

    graph_authors = set(degree)
    nodes = []
    for author in graph_authors:
        node = dict(author_stats[author])
        node["degree"] = degree[author]
        node["weighted_degree"] = weighted_degree[author]
        nodes.append(node)
    nodes.sort(key=lambda r: (-r["paper_count"], r["author"]))

    write_csv(
        OUT / "papers_clean.csv",
        papers,
        ["paper_id", "short_title", "title", "year_month", "coarse_topic", "main_model_stage", "author_count_clean", "source_url"],
    )
    write_csv(
        OUT / "chart2_paper_author_counts.csv",
        chart2,
        ["paper_id", "year_month", "short_title", "coarse_topic", "author_count", "main_model_stage"],
    )
    write_csv(
        OUT / "chart3_coauthor_nodes.csv",
        nodes,
        ["author", "paper_count", "topic_count", "first_seen", "last_seen", "is_high_freq_ge4", "degree", "weighted_degree"],
    )
    write_csv(
        OUT / "chart3_coauthor_edges.csv",
        edges,
        ["source", "target", "weight_shared_papers", "topics", "papers"],
    )
    write_csv(
        OUT / "chart4_author_topic_matrix.csv",
        matrix,
        ["author", "paper_count", "topic_count", *topic_order],
    )
    write_csv(
        OUT / "chart4_main_model_retention.csv",
        retention,
        ["author", "V1/LLM", "V2", "V3", "R1", "V3.2", "V4", "main_model_paper_count"],
    )
    write_csv(
        OUT / "chart6_high_frequency_authors.csv",
        high_freq,
        ["author", "paper_count", "topic_count", "topics", "first_seen", "last_seen", "papers"],
    )
    write_csv(
        OUT / "chart7_main_model_scale.csv",
        main_scale,
        [
            "stage",
            "paper_id",
            "year_month",
            "short_title",
            "author_count_for_chart",
            "author_count_total",
            "author_count_comparable",
            "note",
        ],
    )
    write_csv(
        OUT / "data_quality_notes.csv",
        quality_rows,
        ["paper_id", "issue_type", "detail", "action"],
    )


def main() -> None:
    hf_rows, _ = read_hf_source_rows()
    v4_rows = parse_v4_pdf_rows()
    source_rows = hf_rows + v4_rows
    write_csv(
        OUT / "paper_authors_source_raw.csv",
        source_rows,
        [
            "paper_id",
            "short_title",
            "year_month",
            "coarse_topic",
            "main_model_stage",
            "title",
            "source",
            "source_url",
            "raw_order",
            "raw_author_name",
            "v4_group",
            "departed_mark",
            "manual_note",
        ],
    )

    source_plus_fixes = list(source_rows)
    add_manual_rows(source_plus_fixes)
    clean_rows, quality = make_clean_rows(source_plus_fixes)
    for row in source_plus_fixes:
        if row["source"] == "manual_author_block_fix":
            quality.append(
                {
                    "paper_id": row["paper_id"],
                    "issue_type": "manual_author_added",
                    "detail": row["raw_author_name"],
                    "action": "HF API missing author; added from original author block",
                }
            )

    write_csv(
        OUT / "paper_authors_clean.csv",
        clean_rows,
        [
            "paper_id",
            "short_title",
            "year_month",
            "coarse_topic",
            "main_model_stage",
            "title",
            "source",
            "source_url",
            "raw_order",
            "raw_author_name",
            "clean_author_name",
            "canonical_changed",
            "v4_group",
            "departed_mark",
            "manual_note",
        ],
    )

    canonical_map = []
    grouped = defaultdict(lambda: {"count": 0, "paper_ids": set(), "short_titles": set()})
    for row in clean_rows:
        if row["raw_author_name"] == row["clean_author_name"]:
            continue
        key = (row["raw_author_name"], row["clean_author_name"])
        grouped[key]["count"] += 1
        grouped[key]["paper_ids"].add(row["paper_id"])
        grouped[key]["short_titles"].add(row["short_title"])
    for (raw_name, clean_name), info in grouped.items():
        canonical_map.append(
            {
                "raw_author_name": raw_name,
                "clean_author_name": clean_name,
                "occurrence_count": info["count"],
                "paper_ids": "；".join(sorted(info["paper_ids"])),
                "short_titles": "；".join(sorted(info["short_titles"])),
            }
        )
    canonical_map.sort(key=lambda r: (r["clean_author_name"], r["raw_author_name"]))
    write_csv(
        OUT / "name_canonicalization_map.csv",
        canonical_map,
        ["raw_author_name", "clean_author_name", "occurrence_count", "paper_ids", "short_titles"],
    )

    derive_outputs(clean_rows, quality)
    print(f"Wrote outputs to {OUT}")


if __name__ == "__main__":
    main()

