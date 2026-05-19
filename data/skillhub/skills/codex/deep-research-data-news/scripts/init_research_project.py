#!/usr/bin/env python3
"""Scaffold a reproducible data-news research project."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "research-project"


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Research topic or working title")
    parser.add_argument("--root", default=".", help="Parent directory")
    parser.add_argument("--slug", default="", help="Project folder name")
    args = parser.parse_args()

    slug = args.slug or slugify(args.topic)
    root = Path(args.root).expanduser().resolve() / slug
    for folder in ["raw", "output", "figures", "scripts", "templates", "article"]:
        (root / folder).mkdir(parents=True, exist_ok=True)

    write_if_missing(root / "requirements.txt", "pandas\nmatplotlib\nnetworkx\nrequests\nbeautifulsoup4\n")
    write_if_missing(
        root / "README.md",
        f"""# {args.topic}

Reproducible data-news project.

## Structure

- `raw/`: immutable source snapshots.
- `output/`: cleaned tables and analysis CSV/JSON.
- `figures/`: demo and final PNG/SVG charts plus plot data.
- `scripts/`: fetch, parse, clean, analyze, and plot scripts.
- `article/`: draft, outline, and method note.

## Run Order

```bash
python scripts/01_fetch_sources.py
python scripts/02_parse_raw.py
python scripts/03_clean_data.py
python scripts/04_analyze.py
python scripts/05_make_figures.py
```
""",
    )
    write_if_missing(
        root / "METHOD_WORKFLOW.md",
        f"""# Method Workflow

## Topic

{args.topic}

## Research Questions

1. 
2. 
3. 

## Data Sources

| Source | Access | Fields | Limitation |
|---|---|---|---|

## Definitions

| Metric | Definition | Denominator | Caveat |
|---|---|---|---|

## Chart Plan

| Chart | Question | Source table | Status |
|---|---|---|---|
""",
    )
    write_if_missing(
        root / "output" / "data_quality_notes.csv",
        "item_id,issue_type,detail,action\n",
    )
    for name in ["01_fetch_sources.py", "02_parse_raw.py", "03_clean_data.py", "04_analyze.py", "05_make_figures.py"]:
        write_if_missing(
            root / "scripts" / name,
            '"""Fill this script according to METHOD_WORKFLOW.md."""\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef main() -> None:\n    raise SystemExit("TODO: implement")\n\n\nif __name__ == "__main__":\n    main()\n',
        )
    print(root)


if __name__ == "__main__":
    main()
