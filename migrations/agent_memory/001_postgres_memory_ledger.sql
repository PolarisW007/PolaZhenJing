-- Super Xiaowang Phase 1 memory ledger.
-- PostgreSQL is the source of truth. JSON memory remains fallback only.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

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
