#!/usr/bin/env python3
"""Import _posts/*.md articles as raw events and semantic memory candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT_ROOT / "_posts"
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory_guard import scan_memory_risk  # noqa: E402
from app.memory_store import MemoryStore, utc_now  # noqa: E402


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_post(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    frontmatter = {}
    body = raw
    if raw.startswith("---"):
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, flags=re.S)
        if match:
            for line in match.group(1).splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip().strip('"').strip("'")
            body = match.group(2)
    title = frontmatter.get("title") or path.stem
    summary = re.sub(r"\s+", " ", body).strip()[:4000]
    return {"title": title, "body": body, "summary": summary, "raw": raw}


def import_articles(*, limit: int = 0, active: bool = False) -> dict[str, int]:
    files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    if limit:
        files = files[:limit]
    store = MemoryStore()
    store.init_schema()
    status = "active" if active else "candidate"
    imported = 0
    for path in files:
        parsed = parse_post(path)
        if not parsed["summary"]:
            continue
        guard = scan_memory_risk(parsed["body"], "system")
        source_uri = f"_posts/{path.name}"
        event_id = f"evt_article_{_hash(source_uri + parsed['raw'])[:24]}"
        store.add_raw_event({
            "id": event_id,
            "source_type": "pola_article",
            "source_uri": source_uri,
            "subject_id": "owner",
            "actor_id": "system:article_import",
            "content": parsed["raw"],
            "content_hash": _hash("article" + source_uri + parsed["raw"]),
            "occurred_at": utc_now(),
            "trust_tier": "system",
            "privacy_scope": "public",
            "risk_flags": guard.to_dict(),
        })
        store.create_memory_item({
            "id": f"mem_article_{_hash(source_uri + parsed['summary'])[:24]}",
            "memory_type": "semantic",
            "subject_id": "owner",
            "namespace": "polazj_articles",
            "title": parsed["title"],
            "content": parsed["summary"],
            "status": "quarantined" if guard.status == "quarantined" else status,
            "confidence": 0.7,
            "importance": 0.4,
            "sensitivity": "low",
            "trust_tier": "system",
            "created_by": "system:article_import",
            "evidence_event_ids": [event_id],
        })
        imported += 1
    return {"articles": imported}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--active", action="store_true", help="Import as active instead of candidate.")
    args = parser.parse_args()
    result = import_articles(limit=args.limit, active=args.active)
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
