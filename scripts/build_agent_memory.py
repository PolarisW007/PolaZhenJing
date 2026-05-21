#!/usr/bin/env python3
"""Build the Pola Agent memory index from an Obsidian vault."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_VAULT = Path("/Users/wangchang/Desktop/Sirius/PolaMemory/PolaMemory")
DEFAULT_OUT = Path("data/agent_memory.json")
OBSIDIAN_CLI = Path("/Applications/Obsidian.app/Contents/MacOS/obsidian-cli")


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[\[\]#>*_`~|-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_chunks(text: str, size: int = 900, overlap: int = 120,
                 min_chars: int = 80) -> list[str]:
    text = strip_markdown(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + size].strip()
        if len(chunk) >= min_chars:
            chunks.append(chunk)
        start += max(1, size - overlap)
    return chunks


def obsidian_files(vault_name: str | None) -> set[str]:
    if not vault_name or not OBSIDIAN_CLI.exists():
        return set()
    try:
        result = subprocess.run(
            [str(OBSIDIAN_CLI), "files", f"vault={vault_name}"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:
        return set()
    if result.returncode != 0:
        return set()
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().lower().endswith((".md", ".canvas"))
    }


def iter_note_paths(vault: Path, vault_name: str | None) -> list[Path]:
    cli_paths = obsidian_files(vault_name)
    paths = []
    if cli_paths:
        for rel in cli_paths:
            path = vault / rel
            if path.is_file():
                paths.append(path)
    if not paths:
        paths = list(vault.rglob("*.md")) + list(vault.rglob("*.canvas"))
    return sorted({path.resolve() for path in paths})


def build_index(vault: Path, vault_name: str | None, output: Path) -> dict:
    notes = []
    chunks = []
    for path in iter_note_paths(vault, vault_name):
        if any(part.startswith(".") for part in path.relative_to(vault).parts):
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(vault).as_posix()
        title = path.stem
        min_chars = 24 if rel.startswith("wiki/derived/炽驹人设/") else 80
        note_chunks = split_chunks(raw, min_chars=min_chars)
        if not note_chunks:
            continue
        stat = path.stat()
        notes.append({
            "path": rel,
            "title": title,
            "chars": len(raw),
            "chunks": len(note_chunks),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        })
        for idx, chunk in enumerate(note_chunks):
            chunks.append({
                "id": f"{rel}#{idx + 1}",
                "title": title,
                "path": rel,
                "chunk_index": idx + 1,
                "text": chunk,
            })

    payload = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "vault_name": vault_name or "",
            "vault_path": str(vault),
            "reader": "obsidian-cli files + local vault text",
        },
        "stats": {
            "notes": len(notes),
            "chunks": len(chunks),
            "chars": sum(note["chars"] for note in notes),
        },
        "notes": notes,
        "chunks": chunks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", default=str(DEFAULT_VAULT))
    parser.add_argument("--vault-name", default="PolaMemory")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    payload = build_index(Path(args.vault).expanduser(), args.vault_name, Path(args.output))
    print(json.dumps(payload["stats"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
