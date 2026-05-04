"""Async job queue for long-running tasks (e.g. LLM article generation).

Uses SQLite for cross-worker state (multiple gunicorn workers can serve
status/progress requests), and a daemon thread for actual execution.

Design notes:
- A background thread owns its own sqlite connection (not Flask's request-scoped g.db).
- Job state: pending → running → done | failed
- When gunicorn worker restarts, any in-flight jobs become orphaned; on next status
  poll the client sees stale 'running'. For this admin tool that's acceptable.
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# Resolve DB path once — same as app.get_db()
_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wiki.db')

# Status constants
PENDING = 'pending'
RUNNING = 'running'
DONE = 'done'
FAILED = 'failed'

_SCHEMA = '''
CREATE TABLE IF NOT EXISTS jobs (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER,
    kind            TEXT NOT NULL,
    status          TEXT NOT NULL,
    stage           TEXT,
    progress        INTEGER DEFAULT 0,
    title           TEXT,
    result_filename TEXT,
    error           TEXT,
    messages        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''


def init_schema():
    """Create jobs table if missing. Safe to call multiple times."""
    conn = sqlite3.connect(_DB_PATH)
    try:
        conn.executescript(_SCHEMA)
        # Idempotent migration: add `title` column if the table predates it.
        cols = {r[1] for r in conn.execute('PRAGMA table_info(jobs)')}
        if 'title' not in cols:
            conn.execute('ALTER TABLE jobs ADD COLUMN title TEXT')
        conn.commit()
    finally:
        conn.close()


def _connect():
    """Open a new sqlite connection for use inside a worker thread."""
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def create_job(kind: str, user_id: int | None = None, title: str | None = None) -> str:
    """Insert a new pending job, return job_id."""
    job_id = uuid.uuid4().hex[:16]
    conn = _connect()
    try:
        conn.execute(
            'INSERT INTO jobs (id, user_id, kind, status, stage, progress, messages, title) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (job_id, user_id, kind, PENDING, '排队中…', 0, '[]', title),
        )
        conn.commit()
    finally:
        conn.close()
    return job_id


def update_job(job_id: str, **fields):
    """Update mutable fields on a job row. Accepts status/stage/progress/
    result_filename/error/messages/title. Also bumps updated_at."""
    if not fields:
        return
    allowed = {'status', 'stage', 'progress', 'result_filename', 'error', 'messages', 'title'}
    cols = [k for k in fields if k in allowed]
    if not cols:
        return
    set_clause = ', '.join(f'{c}=?' for c in cols) + ', updated_at=CURRENT_TIMESTAMP'
    values = [fields[c] for c in cols] + [job_id]
    conn = _connect()
    try:
        conn.execute(f'UPDATE jobs SET {set_clause} WHERE id=?', values)
        conn.commit()
    finally:
        conn.close()


def get_job(job_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d['messages'] = json.loads(d.get('messages') or '[]')
    except Exception:
        d['messages'] = []
    return d


def append_message(job_id: str, level: str, text: str):
    """Append a flash-style message to the job's messages JSON list."""
    job = get_job(job_id)
    if not job:
        return
    msgs = job.get('messages') or []
    msgs.append({'level': level, 'text': text})
    update_job(job_id, messages=json.dumps(msgs, ensure_ascii=False))


def list_active_jobs(kind: str | None = None, limit: int = 50) -> list[dict]:
    """Return non-done jobs (pending/running/failed) for status display on
    the articles list page. Most recent first. Also include very recent
    failed jobs so users can see what went wrong.
    """
    conn = _connect()
    try:
        sql = (
            "SELECT * FROM jobs WHERE status IN (?, ?, ?) "
            "AND datetime(updated_at) > datetime('now', '-1 day') "
        )
        params: list = [PENDING, RUNNING, FAILED]
        if kind:
            sql += 'AND kind=? '
            params.append(kind)
        sql += 'ORDER BY datetime(created_at) DESC LIMIT ?'
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def submit(target, *args, **kwargs) -> None:
    """Spawn a daemon thread running `target(*args, **kwargs)`.
    The target function is expected to manage its own job state via update_job().
    """
    t = threading.Thread(target=_safe_run, args=(target, args, kwargs), daemon=True)
    t.start()


def _safe_run(target, args, kwargs):
    """Wrapper that catches unexpected exceptions and records them on the job.

    Assumes the first positional arg is the job_id (by convention).
    """
    try:
        target(*args, **kwargs)
    except Exception as e:
        logger.exception('Background job failed')
        job_id = args[0] if args else kwargs.get('job_id')
        if job_id:
            update_job(
                job_id,
                status=FAILED,
                error=f'{type(e).__name__}: {e}',
                stage='任务异常终止',
            )
