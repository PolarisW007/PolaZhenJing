import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app

from ..audit import log_auth_event
from ..contacts import ContactError, ensure_contact
from ..verification import create_user_for_contact
from .base import (
    AlipayAdapter,
    AppleAdapter,
    GoogleAdapter,
    HuaweiAdapter,
    ProviderError,
    ProviderIdentity,
    WeChatAdapter,
)


PROVIDERS = {
    "google": GoogleAdapter(),
    "apple": AppleAdapter(),
    "wechat": WeChatAdapter(),
    "alipay": AlipayAdapter(),
    "huawei": HuaweiAdapter(),
}


def provider_status(config) -> list[dict]:
    return [
        {
            "provider": name,
            "enabled": adapter.is_enabled(config),
            "configured": adapter.is_configured(config),
            "available": adapter.is_enabled(config) and adapter.is_configured(config),
            "first_batch": adapter.first_batch,
        }
        for name, adapter in PROVIDERS.items()
    ]


def get_provider(name: str):
    provider = (name or "").strip().lower()
    adapter = PROVIDERS.get(provider)
    if adapter is None:
        raise ProviderError("provider_disabled", "不支持的第三方登录方式。")
    return adapter


def _hash_value(value: str) -> str:
    secret = current_app.secret_key or "dev"
    return hashlib.sha256(f"{secret}:{value}".encode("utf-8")).hexdigest()


def _dt(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def create_auth_request(db, provider: str, next_url: str, bind_user_id: int | None = None) -> dict:
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    db.execute(
        """
        INSERT INTO auth_requests
        (provider, state_hash, nonce_hash, next_url, bind_user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            provider,
            _hash_value(state),
            _hash_value(nonce),
            next_url,
            bind_user_id,
            _dt(datetime.now(timezone.utc) + timedelta(minutes=10)),
            _dt(datetime.now(timezone.utc)),
        ),
    )
    db.commit()
    return {"state": state, "nonce": nonce}


def consume_auth_request(db, provider: str, state: str):
    row = db.execute(
        """
        SELECT * FROM auth_requests
        WHERE provider = ? AND state_hash = ? AND consumed_at IS NULL
        ORDER BY id DESC LIMIT 1
        """,
        (provider, _hash_value(state or "")),
    ).fetchone()
    if row is None:
        raise ProviderError("provider_callback_invalid", "登录状态无效或已使用。")
    if datetime.now(timezone.utc) > datetime.fromisoformat(row["expires_at"]):
        raise ProviderError("provider_callback_invalid", "登录状态已过期。")
    claimed = db.execute(
        "UPDATE auth_requests SET consumed_at = ? WHERE id = ? AND consumed_at IS NULL",
        (_dt(datetime.now(timezone.utc)), row["id"]),
    )
    if claimed.rowcount != 1:
        raise ProviderError("provider_callback_invalid", "登录状态无效或已使用。")
    return row


def verify_nonce(raw_nonce: str, nonce_hash: str | None) -> None:
    if nonce_hash and not hmac.compare_digest(_hash_value(raw_nonce or ""), nonce_hash):
        raise ProviderError("provider_callback_invalid", "第三方登录 nonce 校验失败。")


def upsert_provider_identity(db, identity: ProviderIdentity, bind_user_id: int | None = None):
    if not identity.subject:
        raise ProviderError("provider_callback_invalid", "第三方身份缺少 subject。")
    union_identity = None
    if identity.union_id:
        union_identity = db.execute(
            "SELECT * FROM user_identities WHERE provider = ? AND provider_union_id = ?",
            (identity.provider, identity.union_id),
        ).fetchone()
    existing = db.execute(
        "SELECT * FROM user_identities WHERE provider = ? AND provider_subject = ?",
        (identity.provider, identity.subject),
    ).fetchone()
    if union_identity and (existing is None or union_identity["id"] != existing["id"]):
        raise ProviderError("identity_conflict", "该第三方身份已绑定其它账号。")
    if existing:
        if bind_user_id and existing["user_id"] != bind_user_id:
            raise ProviderError("identity_conflict", "该第三方身份已绑定其它账号。")
        user = db.execute("SELECT * FROM users WHERE id = ?", (existing["user_id"],)).fetchone()
        if user is None or (user["status"] if "status" in user.keys() else "active") != "active":
            raise ProviderError("account_disabled", "账号当前不可用。")
        db.execute(
            """
            UPDATE user_identities
            SET provider_union_id = COALESCE(?, provider_union_id),
                provider_email = COALESCE(?, provider_email),
                provider_email_verified = CASE WHEN ? THEN 1 ELSE provider_email_verified END,
                provider_phone = COALESCE(?, provider_phone),
                display_name = COALESCE(?, display_name),
                avatar_url = COALESCE(?, avatar_url),
                last_login_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                identity.union_id,
                identity.email,
                1 if identity.email_verified else 0,
                identity.phone,
                identity.display_name,
                identity.avatar_url,
                existing["id"],
            ),
        )
        return user, "logged_in"
    if bind_user_id:
        user = db.execute("SELECT * FROM users WHERE id = ?", (bind_user_id,)).fetchone()
        if user is None:
            raise ProviderError("provider_callback_invalid", "当前绑定用户不存在。")
        if (user["status"] if "status" in user.keys() else "active") != "active":
            raise ProviderError("account_disabled", "账号当前不可用。")
        status = "bound"
    elif identity.email and identity.email_verified:
        normalized_email = identity.email.strip().lower()
        email_owner = db.execute(
            "SELECT id FROM users WHERE lower(email) = ?",
            (normalized_email,),
        ).fetchone()
        if email_owner:
            raise ProviderError(
                "identity_conflict",
                "该邮箱已有 PolaUUH 账号，请先使用原方式登录后再绑定第三方身份。",
            )
        user = create_user_for_contact(db, "email", normalized_email)
        status = "created"
    else:
        user = create_user_for_contact(db, "email", f"{identity.provider}-{_hash_value(identity.subject)[:12]}@polauuh.local")
        status = "created"
    raw_profile = identity.raw_profile or {}
    db.execute(
        """
        INSERT INTO user_identities
        (user_id, provider, provider_subject, provider_union_id, provider_email, provider_email_verified,
         provider_phone, display_name, avatar_url, raw_profile_json, last_login_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            user["id"],
            identity.provider,
            identity.subject,
            identity.union_id,
            identity.email,
            1 if identity.email_verified else 0,
            identity.phone,
            identity.display_name,
            identity.avatar_url,
            json.dumps(raw_profile, ensure_ascii=False, sort_keys=True),
        ),
    )
    if identity.email and identity.email_verified:
        try:
            ensure_contact(db, user["id"], "email", identity.email, verified=True, primary=False)
        except ContactError:
            pass
    log_auth_event(
        db,
        "identity_linked" if status == "bound" else "login_success",
        identity.provider,
        "success",
        user_id=user["id"],
        metadata={"status": status},
    )
    return db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone(), status


def testing_identity_from_args(provider: str, args: dict) -> ProviderIdentity | None:
    if not current_app.config.get("TESTING"):
        return None
    subject = (args.get("test_subject") or "").strip()
    if not subject:
        return None
    return ProviderIdentity(
        provider=provider,
        subject=subject,
        union_id=(args.get("test_union_id") or "").strip() or None,
        email=(args.get("test_email") or "").strip().lower() or None,
        email_verified=args.get("test_email_verified", "1") != "0",
        phone=(args.get("test_phone") or "").strip() or None,
        display_name=(args.get("test_name") or "").strip() or None,
        avatar_url=(args.get("test_avatar") or "").strip() or None,
        raw_profile={"source": "test"},
    )
