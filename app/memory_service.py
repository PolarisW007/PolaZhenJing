"""Memory service facade for Super Xiaowang."""

from __future__ import annotations

import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .memory_guard import classify_memory_type, scan_memory_risk, should_offer_owner_confirmation
from .memory_store import MemoryStore, MemoryStoreUnavailable, utc_now
from .owner_identity import ActorIdentity


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = PROJECT_ROOT / "data" / "agent_memory.json"


@lru_cache(maxsize=1)
def load_legacy_memory() -> dict[str, Any]:
    if not MEMORY_FILE.is_file():
        return {"stats": {"notes": 0, "chunks": 0, "chars": 0}, "chunks": [], "notes": []}
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"stats": {"notes": 0, "chunks": 0, "chars": 0}, "chunks": [], "notes": []}


def _tokens(text: str) -> list[str]:
    text = (text or "").lower()
    words = re.findall(r"[a-z0-9][a-z0-9._-]{1,}|[\u4e00-\u9fff]{2,}", text)
    chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
    return words + chars


def legacy_memory_search(query: str, limit: int = 6) -> list[dict[str, Any]]:
    memory = load_legacy_memory()
    chunks = memory.get("chunks") or []
    if not query or not chunks:
        return []
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    scored = []
    for chunk in chunks:
        haystack = f"{chunk.get('title', '')} {chunk.get('path', '')} {chunk.get('text', '')}".lower()
        score = 0
        for token in query_tokens:
            if token and token in haystack:
                score += 3 if len(token) > 1 else 1
        title = str(chunk.get("title", "")).lower()
        if any(token in title for token in query_tokens if len(token) > 1):
            score += 8
        if score:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    seen = set()
    for score, chunk in scored:
        path = chunk.get("path")
        if path in seen and len(results) >= 3:
            continue
        seen.add(path)
        text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        results.append({
            "title": chunk.get("title", "Untitled"),
            "path": path,
            "excerpt": text[:520],
            "score": score,
            "source": "legacy_json",
        })
        if len(results) >= limit:
            break
    return results


def memory_store_enabled() -> bool:
    enabled = os.environ.get("POLA_MEMORY_DB_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    return enabled and bool(os.environ.get("DATABASE_URL"))


def memory_write_enabled() -> bool:
    return os.environ.get("POLA_MEMORY_WRITE_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def get_store() -> MemoryStore:
    return MemoryStore()


def init_memory_store_if_enabled() -> dict[str, Any]:
    if not memory_store_enabled():
        return {"enabled": False, "reason": "POLA_MEMORY_DB_ENABLED/DATABASE_URL not configured"}
    store = get_store()
    try:
        store.init_schema()
        return {"enabled": True, "backend": "postgres"}
    except Exception as exc:
        return {"enabled": False, "error": str(exc)}


def memory_status() -> dict[str, Any]:
    legacy = load_legacy_memory()
    payload = {
        "generated_at": legacy.get("generated_at"),
        "source": legacy.get("source", {}),
        "stats": legacy.get("stats", {}),
        "legacy_json": {
            "available": MEMORY_FILE.is_file(),
            "path": str(MEMORY_FILE),
            "stats": legacy.get("stats", {}),
        },
        "store": {
            "enabled": memory_store_enabled(),
            "backend": "postgres",
            "configured": False,
        },
    }
    if memory_store_enabled():
        try:
            payload["store"].update(get_store().status())
        except Exception as exc:
            payload["store"].update({"configured": False, "error": str(exc)})
    return payload


def search_memories(query: str, limit: int = 8, include_candidates: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if memory_store_enabled():
        try:
            statuses = ["active", "pinned"]
            if include_candidates:
                statuses.append("candidate")
            results.extend(get_store().search_memory(query, limit=limit, status=statuses))
        except Exception:
            results = []
    if len(results) < limit:
        results.extend(legacy_memory_search(query, limit=limit - len(results)))
    return results[:limit]


def build_memory_context(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return "当前没有检索到相关长期记忆。"
    lines = []
    for idx, item in enumerate(memories, start=1):
        title = item.get("title") or item.get("memory_type") or "Memory"
        path = item.get("path") or item.get("id") or ""
        excerpt = item.get("excerpt") or item.get("content") or ""
        lines.append(f"[记忆 {idx}] {title}｜{path}\n{excerpt}")
    return "\n\n".join(lines)


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def record_raw_event(
    *,
    actor: ActorIdentity,
    source_type: str,
    content: str,
    source_uri: str = "",
    privacy_scope: str = "project",
) -> str | None:
    if not memory_store_enabled() or not memory_write_enabled():
        return None
    guard = scan_memory_risk(content, actor.trust_tier)
    try:
        return get_store().add_raw_event({
            "source_type": source_type,
            "source_uri": source_uri,
            "subject_id": actor.subject_id,
            "actor_id": actor.subject_id,
            "content": content,
            "content_hash": content_hash(f"{source_type}:{actor.subject_id}:{content}"),
            "occurred_at": utc_now(),
            "trust_tier": actor.trust_tier,
            "privacy_scope": privacy_scope,
            "risk_flags": guard.to_dict(),
        })
    except (MemoryStoreUnavailable, Exception):
        return None


def route_chat_memory_write(actor: ActorIdentity, message: str, raw_event_id: str | None) -> dict[str, Any] | None:
    if not raw_event_id or not memory_store_enabled() or not memory_write_enabled():
        return None
    memory_type = classify_memory_type(message)
    guard = scan_memory_risk(message, actor.trust_tier)

    if actor.is_owner and should_offer_owner_confirmation(message):
        return {
            "needed": True,
            "mode": "owner_confirm",
            "raw_event_id": raw_event_id,
            "proposed_type": memory_type,
            "proposed_content": message[:1000],
            "risk": "high" if guard.risk_flags else "low",
            "risk_flags": guard.risk_flags,
            "confirm_endpoint": "/PolaZhenjing/admin/api/agent/memory/confirm-write",
        }

    if not actor.is_owner and should_offer_owner_confirmation(message):
        try:
            suggestion_id = get_store().create_visitor_suggestion({
                "raw_event_id": raw_event_id,
                "visitor_subject_id": actor.subject_id,
                "suggestion_text": message[:2000],
                "suggested_memory_type": memory_type,
                "summary": message[:240],
                "risk_flags": guard.to_dict(),
                "status": "spam" if guard.status == "quarantined" else "pending",
            })
            return {
                "needed": False,
                "mode": "visitor_suggestion",
                "suggestion_id": suggestion_id,
                "status": "pending" if guard.status != "quarantined" else "spam",
            }
        except Exception:
            return None
    return None


def confirm_owner_memory(
    *,
    actor: ActorIdentity,
    raw_event_id: str | None,
    content: str,
    memory_type: str = "",
    status: str = "active",
) -> dict[str, Any]:
    if not actor.is_owner:
        return {"ok": False, "error": "只有 Owner 可以确认写入超级小王记忆。", "status_code": 403}
    if not memory_store_enabled() or not memory_write_enabled():
        return {"ok": False, "error": "记忆数据库写入尚未启用。", "status_code": 503}
    content = (content or "").strip()
    if not content:
        return {"ok": False, "error": "记忆内容不能为空。", "status_code": 400}
    guard = scan_memory_risk(content, actor.trust_tier)
    if guard.status == "quarantined":
        status = "quarantined"
    memory_type = memory_type or classify_memory_type(content)
    memory_id = get_store().create_memory_item({
        "memory_type": memory_type,
        "subject_id": "owner" if memory_type in {"identity", "values", "style", "boundary"} else actor.subject_id,
        "namespace": "super_xiaowang" if memory_type in {"identity", "values", "style", "boundary"} else actor.subject_id,
        "title": f"{memory_type}: {content[:32]}",
        "content": content,
        "status": status,
        "confidence": 0.9,
        "importance": 0.75 if memory_type in {"identity", "values", "boundary"} else 0.55,
        "sensitivity": "medium" if memory_type in {"identity", "values", "boundary"} else "low",
        "trust_tier": actor.trust_tier,
        "created_by": actor.subject_id,
        "evidence_event_ids": [raw_event_id] if raw_event_id else [],
    })
    return {"ok": True, "memory_id": memory_id, "status": status}


def list_memory_items(status: str = "", limit: int = 80) -> list[dict[str, Any]]:
    if not memory_store_enabled():
        return []
    return get_store().list_memory_items(status=status, limit=limit)


def update_memory_item(
    actor: ActorIdentity,
    memory_id: str,
    *,
    title: str | None = None,
    content: str | None = None,
    status: str | None = None,
    importance: float | None = None,
    reason: str = "",
) -> dict[str, Any]:
    if not actor.is_owner:
        return {"ok": False, "error": "只有 Owner 可以编辑超级小王记忆。", "status_code": 403}
    if not memory_store_enabled() or not memory_write_enabled():
        return {"ok": False, "error": "记忆数据库写入尚未启用。", "status_code": 503}
    if status and status not in {"candidate", "active", "pinned", "deprecated", "discarded", "quarantined"}:
        return {"ok": False, "error": "不支持的记忆状态。", "status_code": 400}
    if content is not None:
        guard = scan_memory_risk(content, actor.trust_tier)
        if guard.status == "quarantined":
            status = "quarantined"
    updated = get_store().update_memory_item(
        memory_id,
        title=title,
        content=content,
        status=status,
        importance=importance,
        actor_id=actor.subject_id,
        reason=reason,
    )
    if not updated:
        return {"ok": False, "error": "记忆不存在。", "status_code": 404}
    return {"ok": True, "memory": updated}


def list_visitor_suggestions(status: str = "", limit: int = 80) -> list[dict[str, Any]]:
    if not memory_store_enabled():
        return []
    return get_store().list_visitor_suggestions(status=status, limit=limit)


def discard_visitor_suggestion(actor: ActorIdentity, suggestion_id: str, reason: str = "") -> dict[str, Any]:
    if not actor.is_owner:
        return {"ok": False, "error": "只有 Owner 可以处理访客建议。", "status_code": 403}
    if not memory_store_enabled() or not memory_write_enabled():
        return {"ok": False, "error": "记忆数据库写入尚未启用。", "status_code": 503}
    get_store().update_visitor_suggestion(suggestion_id, status="discarded", discarded_reason=reason[:500])
    return {"ok": True, "status": "discarded"}


def adopt_visitor_suggestion(
    actor: ActorIdentity,
    suggestion_id: str,
    *,
    edited_content: str = "",
    status: str = "candidate",
) -> dict[str, Any]:
    if not actor.is_owner:
        return {"ok": False, "error": "只有 Owner 可以采纳访客建议。", "status_code": 403}
    if not memory_store_enabled() or not memory_write_enabled():
        return {"ok": False, "error": "记忆数据库写入尚未启用。", "status_code": 503}
    store = get_store()
    suggestion = store.get_visitor_suggestion(suggestion_id)
    if not suggestion:
        return {"ok": False, "error": "访客建议不存在。", "status_code": 404}
    content = (edited_content or suggestion.get("suggestion_text") or "").strip()
    if not content:
        return {"ok": False, "error": "采纳内容不能为空。", "status_code": 400}
    guard = scan_memory_risk(content, actor.trust_tier)
    memory_id = store.create_memory_item({
        "memory_type": suggestion.get("suggested_memory_type") or classify_memory_type(content),
        "subject_id": "owner",
        "namespace": "super_xiaowang",
        "title": f"访客建议采纳: {content[:28]}",
        "content": content,
        "status": "quarantined" if guard.status == "quarantined" else status,
        "confidence": 0.65,
        "importance": 0.45,
        "sensitivity": "low",
        "trust_tier": "owner",
        "created_by": actor.subject_id,
        "evidence_event_ids": [suggestion.get("raw_event_id")],
    })
    store.update_visitor_suggestion(
        suggestion_id,
        status="adopted" if not edited_content else "edited_adopted",
        adopted_memory_id=memory_id,
        adopted_by_owner_id=actor.user_id,
    )
    return {"ok": True, "status": "adopted", "memory_id": memory_id}
