"""Owner and visitor identity helpers for Super Xiaowang memory flows."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

try:
    from flask import session as flask_session
except RuntimeError:  # pragma: no cover - only happens outside Flask import setup
    flask_session = None


OWNER_DEFAULT_EMAILS = "wsyxjer@gmail.com,wsyxjer@qq.com"
OWNER_DEFAULT_USERNAMES = "wsyxjer@gmail.com,wsyxjer@qq.com,18667107187"
OWNER_DEFAULT_PHONES = "18667107187"


@dataclass(frozen=True)
class ActorIdentity:
    """Normalized identity used by chat, memory write, and admin APIs."""

    subject_id: str
    identity_scope: str
    user_id: int | None = None
    username: str = ""
    email: str = ""
    phone: str = ""
    role: str = "visitor"

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @property
    def is_owner(self) -> bool:
        return self.identity_scope == "owner"

    @property
    def is_admin(self) -> bool:
        return self.identity_scope in {"owner", "admin"}

    @property
    def trust_tier(self) -> str:
        if self.is_owner:
            return "owner"
        if self.identity_scope == "admin":
            return "admin"
        if self.is_authenticated:
            return "trusted_user"
        return "public_user"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "identity_scope": self.identity_scope,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "trust_tier": self.trust_tier,
            "authenticated": self.is_authenticated,
            "owner": self.is_owner,
            "admin": self.is_admin,
        }


def _split_env(name: str, default: str) -> set[str]:
    raw = os.environ.get(name, default)
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def owner_aliases() -> dict[str, set[str]]:
    return {
        "emails": _split_env("POLA_AGENT_OWNER_EMAILS", OWNER_DEFAULT_EMAILS),
        "usernames": _split_env("POLA_AGENT_OWNER_USERNAMES", OWNER_DEFAULT_USERNAMES),
        "phones": _split_env("POLA_AGENT_OWNER_PHONES", OWNER_DEFAULT_PHONES),
    }


def _row_get(row: Any, key: str, default: Any = "") -> Any:
    if row is None:
        return default
    if isinstance(row, Mapping):
        return row.get(key, default)
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def is_owner_alias(*, email: str = "", username: str = "", phone: str = "") -> bool:
    aliases = owner_aliases()
    email = (email or "").strip().lower()
    username = (username or "").strip().lower()
    phone = (phone or "").strip().lower()
    return (
        bool(email and email in aliases["emails"])
        or bool(username and username in aliases["usernames"])
        or bool(phone and phone in aliases["phones"])
    )


def resolve_actor(
    session_obj: Mapping[str, Any] | None = None,
    db_getter: Callable[[], Any] | None = None,
) -> ActorIdentity:
    """Resolve current request actor without requiring chat to be logged in."""

    session_data = session_obj
    if session_data is None and flask_session is not None:
        session_data = flask_session
    session_data = session_data or {}

    user_id = session_data.get("user_id")
    if not user_id:
        return ActorIdentity(subject_id="visitor:anonymous", identity_scope="visitor")

    row = None
    if db_getter is None:
        try:
            from . import get_db

            db_getter = get_db
        except Exception:
            db_getter = None
    if db_getter is not None:
        try:
            row = db_getter().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        except Exception:
            row = None

    username = str(_row_get(row, "username", session_data.get("username", "")) or "")
    email = str(_row_get(row, "email", session_data.get("email", "")) or "")
    phone = str(_row_get(row, "phone", session_data.get("phone", "")) or "")
    role = str(_row_get(row, "role", session_data.get("role", "user")) or "user")

    if is_owner_alias(email=email, username=username, phone=phone):
        scope = "owner"
    elif role == "admin" or username.lower() in {"admin", "sirius"}:
        scope = "admin"
    else:
        scope = "user"

    subject_id = "owner" if scope == "owner" else f"user:{user_id}"
    return ActorIdentity(
        subject_id=subject_id,
        identity_scope=scope,
        user_id=int(user_id),
        username=username,
        email=email,
        phone=phone,
        role=role,
    )
