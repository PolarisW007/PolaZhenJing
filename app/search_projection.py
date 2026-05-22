"""Meilisearch projection helpers.

This module deliberately builds documents from PostgreSQL rows only. A
Meilisearch hit must always reload PostgreSQL before it can enter a prompt.
"""

from __future__ import annotations

import re
from typing import Any


SENSITIVE_KEYS = {
    "risk_flags",
    "before_json",
    "after_json",
    "password_hash",
    "token",
    "secret",
    "api_key",
}


def _clean_text(value: str, limit: int = 1200) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value[:limit]


def build_memory_document(row: dict[str, Any]) -> dict[str, Any]:
    """Build a safe, rebuildable Meilisearch document for a memory row."""

    return {
        "id": f"memory:{row.get('id')}",
        "target_type": "memory_item",
        "target_id": row.get("id"),
        "title": _clean_text(row.get("title") or row.get("memory_type") or "Memory", 180),
        "content": _clean_text(row.get("content") or ""),
        "memory_type": row.get("memory_type") or "",
        "subject_id": row.get("subject_id") or "",
        "namespace": row.get("namespace") or "",
        "status": row.get("status") or "",
        "trust_tier": row.get("trust_tier") or "",
        "updated_at": str(row.get("updated_at") or ""),
    }


def build_visitor_suggestion_document(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"visitor_suggestion:{row.get('id')}",
        "target_type": "visitor_suggestion",
        "target_id": row.get("id"),
        "title": _clean_text(row.get("summary") or "访客建议", 180),
        "content": _clean_text(row.get("suggestion_text") or ""),
        "memory_type": row.get("suggested_memory_type") or "",
        "subject_id": row.get("visitor_subject_id") or "",
        "status": row.get("status") or "",
        "updated_at": str(row.get("updated_at") or ""),
    }


def redact_projection_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove keys that should never be projected into a search index."""

    clean = {}
    for key, value in payload.items():
        lowered = key.lower()
        if lowered in SENSITIVE_KEYS or any(marker in lowered for marker in ("secret", "token", "password")):
            continue
        clean[key] = value
    return clean
