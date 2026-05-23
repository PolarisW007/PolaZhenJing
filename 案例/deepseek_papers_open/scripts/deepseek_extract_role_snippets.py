from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
SNIPPETS = RAW / "main_model_role_snippets"
SNIPPETS.mkdir(parents=True, exist_ok=True)


PDFS = {
    "2405.04434": RAW / "paper_2405.04434.pdf",
    "2412.19437": RAW / "paper_2412.19437.pdf",
    "2501.12948": RAW / "paper_2501.12948.pdf",
    "2512.02556": RAW / "paper_2512.02556.pdf",
    "V4-PDF": RAW / "DeepSeek_V4.pdf",
}


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def extract_relevant_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    page_indexes = set()
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if any(
            key in text
            for key in [
                "Research & Engineering",
                "Data Annotation",
                "Business & Compliance",
                "Business Team",
                "Contributions and Acknowledgments",
                "Core Contributors",
            ]
        ):
            page_indexes.update(range(idx, min(idx + 3, len(reader.pages))))
    if not page_indexes:
        page_indexes.update(range(max(0, len(reader.pages) - 5), len(reader.pages)))
    pages = [f"\n\n--- page {i + 1} ---\n{reader.pages[i].extract_text() or ''}" for i in sorted(page_indexes)]
    return clean_text("\n".join(pages))


def main() -> None:
    for paper_id, path in PDFS.items():
        text = extract_relevant_text(path)
        out = SNIPPETS / f"{paper_id}_role_snippet.txt"
        out.write_text(text, encoding="utf-8")
        print(f"{paper_id}\t{path.name}\t{len(text)} chars\t{out}")


if __name__ == "__main__":
    main()

