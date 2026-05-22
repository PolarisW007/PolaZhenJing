#!/usr/bin/env python3
"""Rebuild Meilisearch projection from PostgreSQL memory tables."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory_store import MemoryStore  # noqa: E402
from app.search_projection import build_memory_document, build_visitor_suggestion_document  # noqa: E402


def _headers() -> dict[str, str]:
    api_key = os.environ.get("MEILISEARCH_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _post_documents(index: str, docs: list[dict]) -> None:
    if not docs:
        return
    url = os.environ.get("MEILISEARCH_URL", "").rstrip("/")
    if not url:
        raise RuntimeError("MEILISEARCH_URL is not configured")
    resp = requests.post(
        f"{url}/indexes/{index}/documents",
        headers=_headers(),
        data=json.dumps(docs, ensure_ascii=False).encode("utf-8"),
        timeout=30,
    )
    resp.raise_for_status()


def rebuild(limit: int = 1000) -> dict[str, int]:
    store = MemoryStore()
    memories = store.list_memory_items(limit=limit)
    suggestions = store.list_visitor_suggestions(limit=limit)
    memory_docs = [build_memory_document(row) for row in memories]
    suggestion_docs = [build_visitor_suggestion_document(row) for row in suggestions]
    _post_documents("xiaowang_memory", memory_docs)
    _post_documents("xiaowang_visitor_suggestions", suggestion_docs)
    return {"memory_docs": len(memory_docs), "suggestion_docs": len(suggestion_docs)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    result = rebuild(limit=args.limit)
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
