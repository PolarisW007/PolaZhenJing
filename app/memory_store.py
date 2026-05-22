"""PostgreSQL-backed typed memory ledger for Super Xiaowang.

The module is intentionally optional at runtime: if PostgreSQL or psycopg is not
configured, the public Agent falls back to the existing JSON memory file.
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterable

try:  # pragma: no cover - dependency availability depends on deployment env
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except Exception:  # pragma: no cover
    psycopg = None
    dict_row = None
    Jsonb = None


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def sanitize_pg_text(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\x00", "")
    return value


def sanitize_pg_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_pg_text(value)
    if isinstance(value, list):
        return [sanitize_pg_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_pg_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(sanitize_pg_text(key)): sanitize_pg_value(item)
            for key, item in value.items()
        }
    return value


def pg_jsonb(value: Any) -> Any:
    return Jsonb(sanitize_pg_value(value))


class MemoryStoreUnavailable(RuntimeError):
    """Raised when the optional PostgreSQL memory store is not usable."""


class MemoryStore:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get("DATABASE_URL", "")

    @property
    def configured(self) -> bool:
        return bool(self.dsn and psycopg is not None)

    @contextmanager
    def connect(self):
        if not self.configured:
            raise MemoryStoreUnavailable("PostgreSQL memory store is not configured")
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            yield conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            try:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            except Exception:
                conn.rollback()
                conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            conn.execute(SCHEMA_SQL)
            conn.commit()

    def status(self) -> dict[str, Any]:
        with self.connect() as conn:
            counts = {}
            for name in (
                "raw_events",
                "memory_items",
                "visitor_suggestions",
                "search_index_jobs",
            ):
                counts[name] = conn.execute(f"SELECT count(*) AS count FROM {name}").fetchone()["count"]
            active = conn.execute(
                "SELECT count(*) AS count FROM memory_items WHERE status IN ('active', 'pinned')"
            ).fetchone()["count"]
            candidate = conn.execute(
                "SELECT count(*) AS count FROM memory_items WHERE status = 'candidate'"
            ).fetchone()["count"]
        return {
            "backend": "postgres",
            "configured": True,
            "counts": counts,
            "active_memories": active,
            "candidates": candidate,
        }

    def add_raw_event(self, data: dict[str, Any]) -> str:
        event_id = data.get("id") or new_id("evt")
        payload = {
            "id": event_id,
            "source_type": data["source_type"],
            "source_uri": data.get("source_uri") or "",
            "subject_id": data["subject_id"],
            "actor_id": data.get("actor_id") or "",
            "content": data["content"],
            "content_hash": data["content_hash"],
            "occurred_at": data.get("occurred_at") or utc_now(),
            "ingested_at": data.get("ingested_at") or utc_now(),
            "trust_tier": data["trust_tier"],
            "privacy_scope": data.get("privacy_scope") or "project",
            "risk_flags": pg_jsonb(data.get("risk_flags") or {}),
        }
        payload = sanitize_pg_value(payload)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO raw_events (
                  id, source_type, source_uri, subject_id, actor_id, content,
                  content_hash, occurred_at, ingested_at, trust_tier,
                  privacy_scope, risk_flags
                )
                VALUES (
                  %(id)s, %(source_type)s, %(source_uri)s, %(subject_id)s,
                  %(actor_id)s, %(content)s, %(content_hash)s, %(occurred_at)s,
                  %(ingested_at)s, %(trust_tier)s, %(privacy_scope)s, %(risk_flags)s
                )
                ON CONFLICT (content_hash, source_type, subject_id) DO NOTHING
                """,
                payload,
            )
            conn.commit()
        return event_id

    def create_memory_item(self, data: dict[str, Any]) -> str:
        memory_id = data.get("id") or new_id("mem")
        now = utc_now()
        payload = {
            "id": memory_id,
            "memory_type": data["memory_type"],
            "subject_id": data["subject_id"],
            "namespace": data.get("namespace") or data["subject_id"],
            "title": data.get("title") or "",
            "content": data["content"],
            "status": data.get("status") or "candidate",
            "confidence": float(data.get("confidence", 0.7)),
            "importance": float(data.get("importance", 0.5)),
            "sensitivity": data.get("sensitivity") or "low",
            "trust_tier": data["trust_tier"],
            "valid_from": data.get("valid_from"),
            "valid_to": data.get("valid_to"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
            "created_by": data.get("created_by") or "",
            "version": int(data.get("version", 1)),
            "evidence_event_ids": pg_jsonb(data.get("evidence_event_ids") or []),
            "supersedes_id": data.get("supersedes_id"),
            "conflict_group_id": data.get("conflict_group_id"),
        }
        payload = sanitize_pg_value(payload)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_items (
                  id, memory_type, subject_id, namespace, title, content, status,
                  confidence, importance, sensitivity, trust_tier, valid_from,
                  valid_to, created_at, updated_at, created_by, version,
                  evidence_event_ids, supersedes_id, conflict_group_id
                )
                VALUES (
                  %(id)s, %(memory_type)s, %(subject_id)s, %(namespace)s,
                  %(title)s, %(content)s, %(status)s, %(confidence)s,
                  %(importance)s, %(sensitivity)s, %(trust_tier)s,
                  %(valid_from)s, %(valid_to)s, %(created_at)s, %(updated_at)s,
                  %(created_by)s, %(version)s, %(evidence_event_ids)s,
                  %(supersedes_id)s, %(conflict_group_id)s
                )
                ON CONFLICT (id) DO UPDATE SET
                  title = EXCLUDED.title,
                  content = EXCLUDED.content,
                  status = EXCLUDED.status,
                  confidence = EXCLUDED.confidence,
                  importance = EXCLUDED.importance,
                  updated_at = EXCLUDED.updated_at,
                  evidence_event_ids = EXCLUDED.evidence_event_ids
                """,
                payload,
            )
            self._enqueue_search_job(conn, "memory_item", memory_id, "upsert")
            conn.commit()
        return memory_id

    def create_visitor_suggestion(self, data: dict[str, Any]) -> str:
        suggestion_id = data.get("id") or new_id("sug")
        now = utc_now()
        payload = {
            "id": suggestion_id,
            "raw_event_id": data["raw_event_id"],
            "visitor_subject_id": data["visitor_subject_id"],
            "suggestion_text": data["suggestion_text"],
            "suggested_memory_type": data.get("suggested_memory_type") or "",
            "summary": data.get("summary") or data["suggestion_text"][:240],
            "risk_flags": pg_jsonb(data.get("risk_flags") or {}),
            "status": data.get("status") or "pending",
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        payload = sanitize_pg_value(payload)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO visitor_suggestions (
                  id, raw_event_id, visitor_subject_id, suggestion_text,
                  suggested_memory_type, summary, risk_flags, status,
                  created_at, updated_at
                )
                VALUES (
                  %(id)s, %(raw_event_id)s, %(visitor_subject_id)s,
                  %(suggestion_text)s, %(suggested_memory_type)s, %(summary)s,
                  %(risk_flags)s, %(status)s, %(created_at)s, %(updated_at)s
                )
                """,
                payload,
            )
            self._enqueue_search_job(conn, "visitor_suggestion", suggestion_id, "upsert")
            conn.commit()
        return suggestion_id

    def list_visitor_suggestions(self, status: str = "", limit: int = 80) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        where = ""
        if status:
            where = "WHERE status = %(status)s"
            params["status"] = status
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM visitor_suggestions
                {where}
                ORDER BY created_at DESC
                LIMIT %(limit)s
                """,
                params,
            ).fetchall()
        return list(rows)

    def get_visitor_suggestion(self, suggestion_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM visitor_suggestions WHERE id = %s",
                (suggestion_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_visitor_suggestion(
        self,
        suggestion_id: str,
        *,
        status: str,
        adopted_memory_id: str | None = None,
        adopted_by_owner_id: int | None = None,
        discarded_reason: str = "",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE visitor_suggestions
                SET status = %(status)s,
                    adopted_memory_id = %(adopted_memory_id)s,
                    adopted_by_owner_id = %(adopted_by_owner_id)s,
                    adopted_at = CASE WHEN %(adopted_memory_id)s IS NULL THEN adopted_at ELSE %(now)s END,
                    discarded_reason = %(discarded_reason)s,
                    updated_at = %(now)s
                WHERE id = %(id)s
                """,
                {
                    "id": suggestion_id,
                    "status": status,
                    "adopted_memory_id": adopted_memory_id,
                    "adopted_by_owner_id": adopted_by_owner_id,
                    "discarded_reason": sanitize_pg_text(discarded_reason),
                    "now": utc_now(),
                },
            )
            self._enqueue_search_job(conn, "visitor_suggestion", suggestion_id, "upsert")
            conn.commit()

    def search_memory(self, query: str, limit: int = 20, status: Iterable[str] | None = None) -> list[dict[str, Any]]:
        query = (query or "").strip()
        statuses = list(status or ["active", "pinned"])
        params: dict[str, Any] = {"limit": limit, "statuses": statuses}
        where = ["status = ANY(%(statuses)s)"]
        if query:
            params["pattern"] = f"%{query}%"
            where.append("(title ILIKE %(pattern)s OR content ILIKE %(pattern)s OR memory_type ILIKE %(pattern)s)")
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, memory_type, subject_id, namespace, title, content,
                       status, confidence, importance, trust_tier, updated_at,
                       evidence_event_ids
                FROM memory_items
                WHERE {' AND '.join(where)}
                ORDER BY importance DESC, updated_at DESC
                LIMIT %(limit)s
                """,
                params,
            ).fetchall()
        return [self._memory_row_to_result(row) for row in rows]

    def list_memory_items(self, status: str = "", limit: int = 80) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        where = ""
        if status:
            where = "WHERE status = %(status)s"
            params["status"] = status
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, memory_type, subject_id, namespace, title, content,
                       status, confidence, importance, trust_tier, updated_at,
                       evidence_event_ids
                FROM memory_items
                {where}
                ORDER BY updated_at DESC
                LIMIT %(limit)s
                """,
                params,
            ).fetchall()
        return [self._memory_row_to_result(row) for row in rows]

    def get_memory_item(self, memory_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, memory_type, subject_id, namespace, title, content,
                       status, confidence, importance, trust_tier, updated_at,
                       evidence_event_ids
                FROM memory_items
                WHERE id = %s
                """,
                (memory_id,),
            ).fetchone()
        return self._memory_row_to_result(row) if row else None

    def update_memory_item(
        self,
        memory_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
        importance: float | None = None,
        actor_id: str = "",
        reason: str = "",
    ) -> dict[str, Any] | None:
        before = self.get_memory_item(memory_id)
        if not before:
            return None
        fields = []
        params: dict[str, Any] = {"id": memory_id, "updated_at": utc_now()}
        for name, value in (
            ("title", title),
            ("content", content),
            ("status", status),
            ("importance", importance),
        ):
            if value is not None:
                fields.append(f"{name} = %({name})s")
                params[name] = sanitize_pg_value(value)
        if not fields:
            return before
        fields.append("updated_at = %(updated_at)s")
        with self.connect() as conn:
            conn.execute(
                f"UPDATE memory_items SET {', '.join(fields)} WHERE id = %(id)s",
                params,
            )
            after_row = conn.execute(
                """
                SELECT id, memory_type, subject_id, namespace, title, content,
                       status, confidence, importance, trust_tier, updated_at,
                       evidence_event_ids
                FROM memory_items
                WHERE id = %(id)s
                """,
                {"id": memory_id},
            ).fetchone()
            after = self._memory_row_to_result(after_row)
            conn.execute(
                """
                INSERT INTO memory_audit_logs (
                  id, action, actor_id, target_type, target_id, before_json,
                  after_json, reason
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    new_id("aud"),
                    "memory_item.update",
                    actor_id,
                    "memory_item",
                    memory_id,
                    pg_jsonb(before),
                    pg_jsonb(after),
                    sanitize_pg_text(reason),
                ),
            )
            self._enqueue_search_job(conn, "memory_item", memory_id, "upsert")
            conn.commit()
        return after

    def pending_search_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM search_index_jobs
                WHERE status IN ('pending', 'retry')
                ORDER BY created_at ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return list(rows)

    def mark_search_job(self, job_id: str, *, status: str, error: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE search_index_jobs
                SET status = %s,
                    attempts = attempts + 1,
                    last_error = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (status, sanitize_pg_text(error[:1000]), utc_now(), job_id),
            )
            conn.commit()

    def _enqueue_search_job(self, conn: Any, target_type: str, target_id: str, action: str) -> None:
        conn.execute(
            """
            INSERT INTO search_index_jobs (id, target_type, target_id, action, status)
            VALUES (%s, %s, %s, %s, 'pending')
            """,
            (new_id("sij"), target_type, target_id, action),
        )

    @staticmethod
    def _memory_row_to_result(row: dict[str, Any]) -> dict[str, Any]:
        content = row.get("content") or ""
        return {
            "id": row.get("id"),
            "memory_type": row.get("memory_type"),
            "subject_id": row.get("subject_id"),
            "namespace": row.get("namespace"),
            "title": row.get("title") or row.get("memory_type") or "Memory",
            "path": f"postgres://memory_items/{row.get('id')}",
            "excerpt": content[:520],
            "content": content,
            "status": row.get("status"),
            "confidence": row.get("confidence"),
            "importance": row.get("importance"),
            "trust_tier": row.get("trust_tier"),
            "updated_at": row.get("updated_at"),
            "evidence_event_ids": row.get("evidence_event_ids") or [],
            "score": float(row.get("importance") or 0),
            "source": "postgres",
        }


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_events (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_uri TEXT,
  subject_id TEXT NOT NULL,
  actor_id TEXT,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  occurred_at TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  trust_tier TEXT NOT NULL,
  privacy_scope TEXT NOT NULL,
  risk_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(content_hash, source_type, subject_id)
);

CREATE TABLE IF NOT EXISTS memory_items (
  id TEXT PRIMARY KEY,
  memory_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  namespace TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0,
  importance REAL NOT NULL DEFAULT 0,
  sensitivity TEXT NOT NULL DEFAULT 'low',
  trust_tier TEXT NOT NULL,
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  evidence_event_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  supersedes_id TEXT,
  conflict_group_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_memory_items_status ON memory_items(status);
CREATE INDEX IF NOT EXISTS idx_memory_items_subject ON memory_items(subject_id);
CREATE INDEX IF NOT EXISTS idx_memory_items_content_trgm ON memory_items USING gin (content gin_trgm_ops);

CREATE TABLE IF NOT EXISTS memory_embeddings (
  id TEXT PRIMARY KEY,
  memory_item_id TEXT NOT NULL,
  embedding_model TEXT NOT NULL,
  embedding_dimension INTEGER,
  content_hash TEXT NOT NULL,
  backend TEXT NOT NULL DEFAULT 'pgvector',
  vector_store_ref TEXT,
  vector_json JSONB,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deprecated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_memory_embeddings_item ON memory_embeddings(memory_item_id);
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_status ON memory_embeddings(status);

CREATE TABLE IF NOT EXISTS persona_versions (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  status TEXT NOT NULL,
  core_identity TEXT NOT NULL,
  values_json JSONB NOT NULL,
  style_json JSONB NOT NULL,
  boundaries_json JSONB NOT NULL,
  prompt_template TEXT NOT NULL,
  change_summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by TEXT,
  harness_run_id TEXT
);

CREATE TABLE IF NOT EXISTS visitor_suggestions (
  id TEXT PRIMARY KEY,
  raw_event_id TEXT NOT NULL,
  visitor_subject_id TEXT NOT NULL,
  suggestion_text TEXT NOT NULL,
  suggested_memory_type TEXT,
  summary TEXT,
  risk_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'pending',
  adopted_memory_id TEXT,
  adopted_by_owner_id INTEGER,
  adopted_at TIMESTAMPTZ,
  discarded_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memory_audit_logs (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  before_json JSONB,
  after_json JSONB,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS search_index_jobs (
  id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  action TEXT NOT NULL,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""
