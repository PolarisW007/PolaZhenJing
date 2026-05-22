#!/usr/bin/env python3
"""Import existing data/agent_memory.json chunks into the PostgreSQL ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory_guard import scan_memory_risk  # noqa: E402
from app.memory_store import MemoryStore, utc_now  # noqa: E402


def _hash(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def import_legacy(path: Path, *, limit: int = 0, active: bool = False) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks = data.get("chunks") or []
    if limit:
        chunks = chunks[:limit]
    store = MemoryStore()
    store.init_schema()
    imported_events = 0
    imported_memories = 0
    status = "active" if active else "candidate"
    for chunk in chunks:
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue
        title = str(chunk.get("title") or "Legacy memory").strip()
        source_uri = str(chunk.get("path") or "").strip()
        event_id = f"evt_legacy_{_hash(source_uri, title, text)[:24]}"
        guard = scan_memory_risk(text, "system")
        store.add_raw_event({
            "id": event_id,
            "source_type": "obsidian_note",
            "source_uri": source_uri,
            "subject_id": "owner",
            "actor_id": "system:legacy_import",
            "content": text,
            "content_hash": _hash("legacy", source_uri, text),
            "occurred_at": utc_now(),
            "trust_tier": "system",
            "privacy_scope": "owner",
            "risk_flags": guard.to_dict(),
        })
        imported_events += 1
        store.create_memory_item({
            "id": f"mem_legacy_{_hash(source_uri, title, text)[:24]}",
            "memory_type": "semantic",
            "subject_id": "owner",
            "namespace": "pola_memory",
            "title": title,
            "content": text[:4000],
            "status": "quarantined" if guard.status == "quarantined" else status,
            "confidence": 0.65,
            "importance": 0.35,
            "sensitivity": "medium",
            "trust_tier": "system",
            "created_by": "system:legacy_import",
            "evidence_event_ids": [event_id],
        })
        imported_memories += 1
    return {"events": imported_events, "memories": imported_memories}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(PROJECT_ROOT / "data" / "agent_memory.json"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--active", action="store_true", help="Import as active instead of candidate.")
    args = parser.parse_args()
    result = import_legacy(Path(args.file), limit=args.limit, active=args.active)
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
