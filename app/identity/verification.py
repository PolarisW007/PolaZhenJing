import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import generate_password_hash

from .audit import log_auth_event, request_ip_hash, request_user_agent
from .captcha import CaptchaError, verify_sms_captcha
from .contacts import ContactError, contact_hash, ensure_contact, get_contact_by_value, normalize_contact
from ..mailer import send_verification_code
from ..sms import send_sms_verification_code


class VerificationError(ValueError):
    def __init__(self, code: str, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.code = code
        self.retry_after = retry_after


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dt(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _code_hash(channel: str, purpose: str, target_hash: str, code: str) -> str:
    secret = current_app.secret_key or "dev"
    return hashlib.sha256(f"{secret}:{channel}:{purpose}:{target_hash}:{code}".encode("utf-8")).hexdigest()


def _username_from_contact(db, channel: str, target: str) -> str:
    if channel == "email":
        base = target.split("@", 1)[0]
    else:
        base = f"phone_{target[-4:]}"
    base = "".join(ch for ch in base.lower() if ch.isalnum() or ch in {"_", "-"})[:28] or "user"
    candidate = base
    suffix = 1
    while db.execute("SELECT 1 FROM users WHERE username = ?", (candidate,)).fetchone():
        suffix += 1
        candidate = f"{base[:24]}{suffix}"
    return candidate


def _synthetic_email_for_phone(target_hash: str) -> str:
    return f"phone-{target_hash[:16]}@polauuh.local"


def _validate_otp_request(channel: str, purpose: str) -> tuple[str, str, str]:
    channel = (channel or "").strip().lower()
    purpose = (purpose or "").strip().lower()
    if channel not in {"email", "sms"}:
        raise VerificationError("invalid_request", "不支持的验证码渠道。")
    if purpose not in {"register_login", "bind", "change", "unlink", "reauth"}:
        raise VerificationError("invalid_request", "不支持的验证码用途。")
    return channel, purpose, "phone" if channel == "sms" else "email"


def _enforce_rate_limits(db, channel: str, purpose: str, target_hash: str, ip_hash: str) -> None:
    now = utcnow()
    resend_seconds = int(current_app.config["POLAUUH_OTP_RESEND_SECONDS"])
    recent = db.execute(
        """
        SELECT created_at FROM verification_codes
        WHERE channel = ? AND purpose = ? AND target_hash = ?
        ORDER BY id DESC LIMIT 1
        """,
        (channel, purpose, target_hash),
    ).fetchone()
    if recent:
        elapsed = (now - datetime.fromisoformat(recent["created_at"])).total_seconds()
        if elapsed < resend_seconds:
            raise VerificationError(
                "rate_limited",
                "验证码发送过于频繁。",
                retry_after=max(1, int(resend_seconds - elapsed)),
            )

    hour_ago = _dt(now - timedelta(hours=1))
    target_count = db.execute(
        """
        SELECT COUNT(*) AS c FROM verification_codes
        WHERE channel = ? AND target_hash = ? AND created_at >= ?
        """,
        (channel, target_hash, hour_ago),
    ).fetchone()["c"]
    if target_count >= int(current_app.config["POLAUUH_OTP_TARGET_HOURLY_LIMIT"]):
        raise VerificationError("rate_limited", "该联系方式请求验证码次数过多。", retry_after=3600)
    if ip_hash:
        ip_count = db.execute(
            "SELECT COUNT(*) AS c FROM verification_codes WHERE request_ip_hash = ? AND created_at >= ?",
            (ip_hash, hour_ago),
        ).fetchone()["c"]
        if ip_count >= int(current_app.config["POLAUUH_OTP_IP_HOURLY_LIMIT"]):
            raise VerificationError("rate_limited", "当前网络请求验证码次数过多。", retry_after=3600)


def send_otp(db, channel: str, target: str, purpose: str, captcha_verify_param: str = "") -> dict:
    channel, purpose, contact_type = _validate_otp_request(channel, purpose)
    if channel == "sms":
        try:
            verify_sms_captcha(captcha_verify_param)
        except CaptchaError as exc:
            raise VerificationError(exc.code, str(exc)) from exc
    normalized = normalize_contact(contact_type, target)
    target_hash = contact_hash(contact_type, normalized)
    ip_hash = request_ip_hash()
    _enforce_rate_limits(db, channel, purpose, target_hash, ip_hash)
    resend_seconds = int(current_app.config["POLAUUH_OTP_RESEND_SECONDS"])
    ttl_seconds = int(current_app.config["POLAUUH_OTP_TTL_SECONDS"])
    max_attempts = int(current_app.config["POLAUUH_OTP_MAX_ATTEMPTS"])
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = utcnow() + timedelta(seconds=ttl_seconds)
    db.execute(
        """
        INSERT INTO verification_codes
        (channel, purpose, target_hash, code_hash, expires_at, max_attempts, request_ip_hash, request_user_agent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            channel,
            purpose,
            target_hash,
            _code_hash(channel, purpose, target_hash, code),
            _dt(expires_at),
            max_attempts,
            ip_hash,
            request_user_agent(),
            _dt(utcnow()),
        ),
    )
    testing = bool(current_app.config.get("TESTING"))
    if testing:
        sent = False
    elif channel == "email":
        sent = send_verification_code(normalized, code)
    else:
        sent = send_sms_verification_code(normalized, code)
    if not sent and not testing:
        db.rollback()
        log_auth_event(
            db,
            "otp_delivery_failed",
            "phone_otp" if channel == "sms" else "email_otp",
            "failed",
            reason="delivery_failed",
            metadata={"purpose": purpose},
        )
        db.commit()
        raise VerificationError("delivery_failed", "验证码投递失败，请稍后重试。")
    log_auth_event(
        db,
        "otp_sent",
        "phone_otp" if channel == "sms" else "email_otp",
        "success",
        metadata={"purpose": purpose, "sent": sent},
    )
    db.commit()
    result = {"expires_in": ttl_seconds, "retry_after": resend_seconds, "sent": sent}
    if testing:
        result["debug_code"] = code
    return result


def consume_otp(db, channel: str, target: str, purpose: str, code: str):
    channel, purpose, contact_type = _validate_otp_request(channel, purpose)
    normalized = normalize_contact(contact_type, target)
    target_hash = contact_hash(contact_type, normalized)
    row = db.execute(
        """
        SELECT * FROM verification_codes
        WHERE channel = ? AND purpose = ? AND target_hash = ? AND used_at IS NULL
        ORDER BY id DESC LIMIT 1
        """,
        (channel, purpose, target_hash),
    ).fetchone()
    if row is None:
        raise VerificationError("otp_invalid", "验证码无效。")
    if row["attempt_count"] >= row["max_attempts"]:
        raise VerificationError("otp_attempts_exceeded", "验证码尝试次数过多。")
    if utcnow() > datetime.fromisoformat(row["expires_at"]):
        raise VerificationError("otp_expired", "验证码已过期。")
    if _code_hash(channel, purpose, target_hash, (code or "").strip()) != row["code_hash"]:
        db.execute(
            "UPDATE verification_codes SET attempt_count = attempt_count + 1 WHERE id = ?",
            (row["id"],),
        )
        db.commit()
        raise VerificationError("otp_invalid", "验证码错误。")
    claimed = db.execute(
        "UPDATE verification_codes SET used_at = ? "
        "WHERE id = ? AND used_at IS NULL AND attempt_count < max_attempts",
        (_dt(utcnow()), row["id"]),
    )
    if claimed.rowcount != 1:
        raise VerificationError("otp_invalid", "验证码无效或已使用。")
    return normalized


def login_or_create_with_otp(db, channel: str, target: str, purpose: str, code: str):
    if purpose != "register_login":
        raise VerificationError("invalid_request", "当前接口只支持注册/登录验证码。")
    normalized = consume_otp(db, channel, target, purpose, code)
    contact_type = "phone" if channel == "sms" else "email"
    contact = get_contact_by_value(db, contact_type, normalized)
    if contact:
        user = db.execute("SELECT * FROM users WHERE id = ?", (contact["user_id"],)).fetchone()
        ensure_contact(
            db,
            user["id"],
            contact_type,
            normalized,
            verified=True,
            primary=bool(contact["is_primary"]),
        )
        status = "logged_in"
    elif contact_type == "email":
        user = db.execute("SELECT * FROM users WHERE email = ?", (normalized,)).fetchone()
        if user:
            ensure_contact(db, user["id"], "email", normalized, verified=True, primary=True)
            status = "logged_in"
        else:
            user = create_user_for_contact(db, "email", normalized)
            status = "created"
    else:
        user = create_user_for_contact(db, "phone", normalized)
        status = "created"
    if user is None or (user["status"] if "status" in user.keys() else "active") != "active":
        raise VerificationError("account_disabled", "账号当前不可用。")
    db.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
    log_auth_event(
        db,
        "login_success",
        "phone_otp" if channel == "sms" else "email_otp",
        "success",
        user_id=user["id"],
        metadata={"status": status},
    )
    db.commit()
    return db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone(), status


def create_user_for_contact(db, contact_type: str, normalized: str):
    value_hash = contact_hash(contact_type, normalized)
    username = _username_from_contact(db, contact_type, normalized)
    email = normalized if contact_type == "email" else _synthetic_email_for_phone(value_hash)
    synthetic_email = contact_type == "email" and normalized.endswith("@polauuh.local")
    cursor = db.execute(
        """
        INSERT INTO users
        (username, email, password_hash, password_enabled, email_verified, nickname, role, status)
        VALUES (?, ?, ?, 0, ?, ?, 'user', 'active')
        """,
        (
            username,
            email,
            generate_password_hash(secrets.token_urlsafe(32)),
            1 if contact_type == "email" and not synthetic_email else 0,
            username,
        ),
    )
    user_id = cursor.lastrowid
    if not synthetic_email:
        ensure_contact(db, user_id, contact_type, normalized, verified=True, primary=True)
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def bind_contact_with_otp(db, user_id: int, channel: str, target: str, purpose: str, code: str) -> int:
    if purpose not in {"bind", "change"}:
        raise VerificationError("invalid_request", "当前接口只支持绑定或换绑验证码。")
    normalized = consume_otp(db, channel, target, purpose, code)
    contact_type = "phone" if channel == "sms" else "email"
    try:
        contact_id = ensure_contact(db, user_id, contact_type, normalized, verified=True, primary=True)
    except ContactError as exc:
        raise VerificationError("contact_conflict", str(exc)) from exc
    log_auth_event(
        db,
        "contact_bound",
        "phone_otp" if channel == "sms" else "email_otp",
        "success",
        user_id=user_id,
        metadata={"contact_type": contact_type, "purpose": purpose},
    )
    db.commit()
    return contact_id
