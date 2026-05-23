from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT
RAW = DATA / "raw"
SNIPPETS = RAW / "main_model_role_snippets"
OUT = DATA / "output"


MAIN_MODEL_IDS = ["2401.02954", "2405.04434", "2412.19437", "2512.02556", "V4-PDF"]

PAPER_META = {
    "2401.02954": ("DeepSeek LLM", "V1/LLM", "2024-01"),
    "2405.04434": ("DeepSeek-V2", "V2", "2024-05"),
    "2412.19437": ("DeepSeek-V3 Technical Report", "V3", "2024-12"),
    "2512.02556": ("DeepSeek-V3.2", "V3.2", "2025-12"),
    "V4-PDF": ("DeepSeek-V4", "V4", "2026-05"),
}

ROLE_ZH = {
    "Research & Engineering": "研发与工程",
    "Data Annotation": "数据标注",
    "Business & Compliance": "商务与合规",
    "Author list only": "作者名单（原文未拆角色）",
}

ROLE_BOOL_COLUMNS = {
    "Research & Engineering": "is_research_engineering",
    "Data Annotation": "is_data_annotation",
    "Business & Compliance": "is_business_compliance",
    "Author list only": "is_author_list_only_unspecified",
}

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


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clean_name(name: str) -> str:
    name = name.replace("\u00a0", " ")
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip(" ,;:.")
    name = re.sub(r"\*$", "", name).strip()
    name = re.sub(r"([A-Z])\.([A-Z])\.", r"\1. \2.", name)
    name = re.sub(r"([A-Z])\.([A-Z])", r"\1. \2", name)
    name = re.sub(r"\s+", " ", name)
    return MANUAL_NAME_MAP.get(name, name)


def extract_between(text: str, start: str, end_patterns: list[str]) -> str:
    start_re = re.escape(start) + r":?"
    match = re.search(start_re, text)
    if not match:
        return ""
    chunk = text[match.end() :]
    end_positions = []
    for end in end_patterns:
        end_match = re.search(re.escape(end) + r":?", chunk)
        if end_match:
            end_positions.append(end_match.start())
    if end_positions:
        chunk = chunk[: min(end_positions)]
    return chunk


def split_names(section: str) -> list[str]:
    section = re.sub(r"--- page \d+ ---", " ", section)
    section = re.sub(r"\b\d+\b", " ", section)
    section = section.replace("\r", "\n")
    section = re.sub(r"individu-\s*\n\s*als", "individuals", section)
    if section.count(",") >= 5:
        pieces = [p for p in section.replace("\n", " ").split(",")]
    else:
        pieces = section.splitlines()

    names = []
    for piece in pieces:
        piece = re.sub(r"\s+", " ", piece).strip()
        if not piece:
            continue
        if any(
            bad in piece
            for bad in [
                "Within each role",
                "Authors are listed",
                "Names marked",
                "denote individuals",
                "A.2.",
                "Acknowledgment",
                "Appendix",
                "Figure",
                "Table",
                "Evaluation Details",
            ]
        ):
            continue
        if len(piece.split()) > 5:
            continue
        names.append(piece)
    return names


def parse_role_snippet(paper_id: str) -> list[dict]:
    text = (SNIPPETS / f"{paper_id}_role_snippet.txt").read_text(encoding="utf-8")
    role_rows = []
    role_endings = {
        "Research & Engineering": ["Data Annotation", "Business & Compliance"],
        "Data Annotation": ["Business & Compliance"],
        "Business & Compliance": ["Within each role", "Authors are listed", "A.2. Acknowledgment", "B. Evaluation Details", "B. Ablation"],
    }
    short_title, stage, year_month = PAPER_META[paper_id]
    for role, endings in role_endings.items():
        section = extract_between(text, role, endings)
        if not section:
            continue
        for raw_order, raw_name in enumerate(split_names(section), start=1):
            cleaned = clean_name(raw_name)
            if not cleaned:
                continue
            role_rows.append(
                {
                    "paper_id": paper_id,
                    "short_title": short_title,
                    "stage": stage,
                    "year_month": year_month,
                    "role_group": role,
                    "role_group_zh": ROLE_ZH[role],
                    "raw_role_author_name": raw_name,
                    "clean_author_name": cleaned,
                    "departed_mark": "TRUE" if "*" in raw_name else "FALSE",
                    "source_file": str(SNIPPETS / f"{paper_id}_role_snippet.txt"),
                    "source_basis": "paper_appendix_role_list",
                }
            )
    return role_rows


def rows_for_llm(clean_rows: list[dict]) -> list[dict]:
    short_title, stage, year_month = PAPER_META["2401.02954"]
    rows = []
    for order, row in enumerate([r for r in clean_rows if r["paper_id"] == "2401.02954"], start=1):
        rows.append(
            {
                "paper_id": "2401.02954",
                "short_title": short_title,
                "stage": stage,
                "year_month": year_month,
                "role_group": "Author list only",
                "role_group_zh": ROLE_ZH["Author list only"],
                "raw_role_author_name": row["raw_author_name"],
                "clean_author_name": row["clean_author_name"],
                "departed_mark": row.get("departed_mark", ""),
                "source_file": str(RAW / "ar5iv_2401.02954.html"),
                "source_basis": "paper_author_list_no_role_split",
            }
        )
    return rows


def main() -> None:
    clean_rows = read_csv(OUT / "paper_authors_clean.csv")
    selected_clean = [r for r in clean_rows if r["paper_id"] in MAIN_MODEL_IDS]
    clean_names_by_paper = defaultdict(set)
    for row in selected_clean:
        clean_names_by_paper[row["paper_id"]].add(row["clean_author_name"])

    long_rows = rows_for_llm(clean_rows)
    for paper_id in ["2405.04434", "2412.19437", "2512.02556", "V4-PDF"]:
        long_rows.extend(parse_role_snippet(paper_id))

    dedup_long = []
    seen_long = set()
    for row in long_rows:
        clean_names = clean_names_by_paper[row["paper_id"]]
        name = row["clean_author_name"]
        parts = name.split()
        if name not in clean_names and len(parts) == 2:
            reversed_name = f"{parts[1]} {parts[0]}"
            if reversed_name in clean_names:
                row["clean_author_name"] = reversed_name
        key = (row["paper_id"], row["role_group"], row["clean_author_name"])
        if key in seen_long:
            continue
        seen_long.add(key)
        dedup_long.append(row)

    role_by_author = defaultdict(set)
    departed_by_author = defaultdict(bool)
    raw_by_author = defaultdict(list)
    for row in dedup_long:
        key = (row["paper_id"], row["clean_author_name"])
        role_by_author[key].add(row["role_group"])
        departed_by_author[key] = departed_by_author[key] or row["departed_mark"] == "TRUE"
        raw_by_author[key].append(row["raw_role_author_name"])

    clean_by_key = {(r["paper_id"], r["clean_author_name"]): r for r in selected_clean}
    all_keys = sorted(set(clean_by_key) | set(role_by_author), key=lambda x: (PAPER_META[x[0]][2], PAPER_META[x[0]][1], x[1]))

    author_rows = []
    for paper_id, author in all_keys:
        short_title, stage, year_month = PAPER_META[paper_id]
        roles = sorted(role_by_author.get((paper_id, author), []), key=lambda r: list(ROLE_BOOL_COLUMNS).index(r))
        base = clean_by_key.get((paper_id, author), {})
        row = {
            "paper_id": paper_id,
            "short_title": short_title,
            "stage": stage,
            "year_month": year_month,
            "clean_author_name": author,
            "raw_author_name_from_clean_table": base.get("raw_author_name", ""),
            "raw_author_name_from_role_list": " | ".join(raw_by_author.get((paper_id, author), [])),
            "role_groups": " | ".join(roles),
            "role_groups_zh": " | ".join(ROLE_ZH[r] for r in roles),
            "departed_mark": "TRUE" if departed_by_author[(paper_id, author)] or base.get("departed_mark") == "TRUE" else "FALSE",
            "in_clean_author_table": "TRUE" if (paper_id, author) in clean_by_key else "FALSE",
            "in_role_appendix": "TRUE" if roles else "FALSE",
            "role_source_note": "LLM paper does not split its 86 paper authors by role; appendix only lists separate acknowledgment teams."
            if paper_id == "2401.02954"
            else "Role group parsed from paper appendix author/contribution list.",
        }
        for role, col in ROLE_BOOL_COLUMNS.items():
            row[col] = "TRUE" if role in roles else "FALSE"
        author_rows.append(row)

    summary = []
    for paper_id in MAIN_MODEL_IDS:
        rows = [r for r in author_rows if r["paper_id"] == paper_id]
        appendix_rows = [r for r in dedup_long if r["paper_id"] == paper_id]
        clean_authors = {r["clean_author_name"] for r in selected_clean if r["paper_id"] == paper_id}
        role_authors = {r["clean_author_name"] for r in appendix_rows}
        role_counts = {}
        for role in ROLE_BOOL_COLUMNS:
            role_counts[role] = len({r["clean_author_name"] for r in appendix_rows if r["role_group"] == role})
        overlap_count = sum(1 for r in rows if len([role for role in ROLE_BOOL_COLUMNS if r[ROLE_BOOL_COLUMNS[role]] == "TRUE"]) > 1)
        summary.append(
            {
                "paper_id": paper_id,
                "short_title": PAPER_META[paper_id][0],
                "stage": PAPER_META[paper_id][1],
                "year_month": PAPER_META[paper_id][2],
                "clean_author_count": len(clean_authors),
                "role_unique_author_count": len(role_authors),
                "research_engineering_count": role_counts["Research & Engineering"],
                "data_annotation_count": role_counts["Data Annotation"],
                "business_compliance_count": role_counts["Business & Compliance"],
                "author_list_only_unspecified_count": role_counts["Author list only"],
                "authors_with_multiple_roles": overlap_count,
                "role_authors_missing_from_clean_table": len(role_authors - clean_authors),
                "clean_table_authors_missing_from_role_appendix": len(clean_authors - role_authors),
                "recommended_comparable_count": role_counts["Research & Engineering"] or role_counts["Author list only"],
                "note": "LLM: original paper author list has no role split; do not compare as Research & Engineering."
                if paper_id == "2401.02954"
                else "Comparable count uses Research & Engineering; total role count may include Data Annotation and Business & Compliance.",
            }
        )

    write_csv(
        OUT / "main_model_author_roles_long.csv",
        dedup_long,
        [
            "paper_id",
            "short_title",
            "stage",
            "year_month",
            "role_group",
            "role_group_zh",
            "raw_role_author_name",
            "clean_author_name",
            "departed_mark",
            "source_file",
            "source_basis",
        ],
    )
    write_csv(
        OUT / "main_model_authors_with_roles.csv",
        author_rows,
        [
            "paper_id",
            "short_title",
            "stage",
            "year_month",
            "clean_author_name",
            "raw_author_name_from_clean_table",
            "raw_author_name_from_role_list",
            "role_groups",
            "role_groups_zh",
            "is_research_engineering",
            "is_data_annotation",
            "is_business_compliance",
            "is_author_list_only_unspecified",
            "departed_mark",
            "in_clean_author_table",
            "in_role_appendix",
            "role_source_note",
        ],
    )
    write_csv(
        OUT / "main_model_role_summary.csv",
        summary,
        [
            "paper_id",
            "short_title",
            "stage",
            "year_month",
            "clean_author_count",
            "role_unique_author_count",
            "research_engineering_count",
            "data_annotation_count",
            "business_compliance_count",
            "author_list_only_unspecified_count",
            "authors_with_multiple_roles",
            "role_authors_missing_from_clean_table",
            "clean_table_authors_missing_from_role_appendix",
            "recommended_comparable_count",
            "note",
        ],
    )
    chart_rows = []
    for row in summary:
        chart_rows.append(
            {
                "stage": row["stage"],
                "paper_id": row["paper_id"],
                "year_month": row["year_month"],
                "short_title": row["short_title"],
                "total_signature_author_count": row["clean_author_count"],
                "research_engineering_count": row["research_engineering_count"],
                "data_annotation_count": row["data_annotation_count"],
                "business_compliance_count": row["business_compliance_count"],
                "author_list_only_unspecified_count": row["author_list_only_unspecified_count"],
                "recommended_comparable_count": row["recommended_comparable_count"],
                "authors_with_multiple_roles": row["authors_with_multiple_roles"],
                "note": row["note"],
            }
        )
    write_csv(
        OUT / "chart7_main_model_scale_by_role.csv",
        chart_rows,
        [
            "stage",
            "paper_id",
            "year_month",
            "short_title",
            "total_signature_author_count",
            "research_engineering_count",
            "data_annotation_count",
            "business_compliance_count",
            "author_list_only_unspecified_count",
            "recommended_comparable_count",
            "authors_with_multiple_roles",
            "note",
        ],
    )
    print(f"Wrote {OUT / 'main_model_author_roles_long.csv'}")
    print(f"Wrote {OUT / 'main_model_authors_with_roles.csv'}")
    print(f"Wrote {OUT / 'main_model_role_summary.csv'}")
    print(f"Wrote {OUT / 'chart7_main_model_scale_by_role.csv'}")


if __name__ == "__main__":
    main()

