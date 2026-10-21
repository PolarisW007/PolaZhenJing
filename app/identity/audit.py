import hashlib
import json

from flask import request


def hash_request_value(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def request_ip_hash() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = (forwarded.split(",", 1)[0] or request.remote_addr or "").strip()
    return hash_request_value(ip) if ip else ""


def request_user_agent() -> str:
    return (request.headers.get("User-Agent") or "")[:240]


def log_auth_event(
    db,
    event_type: str,
    provider: str,
    result: str,
    *,
    user_id: int | None = None,
    reason: str = "",
    metadata: dict | None = None,
) -> None:
    safe_metadata = {}
    for key, value in (metadata or {}).items():
        if key.lower() in {"token", "access_token", "refresh_token", "code", "secret", "password"}:
            continue
        safe_metadata[key] = value
    db.execute(
        """
        INSERT INTO auth_audit_logs
        (user_id, event_type, provider, result, reason, request_ip_hash, request_user_agent, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            event_type,
            provider,
            result,
            reason[:160],
            request_ip_hash(),
            request_user_agent(),
            json.dumps(safe_metadata, ensure_ascii=False, sort_keys=True),
        ),
    )
