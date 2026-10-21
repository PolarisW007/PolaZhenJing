import hashlib
import re


class ContactError(ValueError):
    pass


def contact_hash(contact_type: str, value: str) -> str:
    return hashlib.sha256(f"{contact_type}:{value}".encode("utf-8")).hexdigest()


def normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ContactError("请输入有效邮箱。")
    return email


def normalize_phone(value: str) -> str:
    raw = (value or "").strip()
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        normalized = f"+{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        normalized = f"+86{digits}"
    else:
        normalized = f"+{digits}"
    if len(digits) < 8 or len(digits) > 15:
        raise ContactError("请输入有效手机号。")
    return normalized


def normalize_contact(contact_type: str, value: str) -> str:
    if contact_type == "email":
        return normalize_email(value)
    if contact_type == "phone":
        return normalize_phone(value)
    raise ContactError("不支持的联系方式。")


def mask_contact(contact_type: str, value: str) -> str:
    if contact_type == "email":
        name, domain = value.split("@", 1)
        visible = name[:2] if len(name) > 2 else name[:1]
        return f"{visible}***@{domain}"
    if contact_type == "phone":
        return f"{value[:3]}****{value[-4:]}"
    return "***"


def ensure_contact(
    db,
    user_id: int,
    contact_type: str,
    value: str,
    *,
    verified: bool = True,
    primary: bool = True,
) -> int:
    normalized = normalize_contact(contact_type, value)
    value_hash = contact_hash(contact_type, normalized)
    if contact_type == "email":
        email_owner = db.execute(
            "SELECT id FROM users WHERE lower(email) = ? AND id <> ?",
            (normalized, user_id),
        ).fetchone()
        if email_owner:
            raise ContactError("该邮箱已属于其它账号。")
    existing = db.execute(
        "SELECT * FROM user_contacts WHERE contact_type = ? AND contact_value_hash = ?",
        (contact_type, value_hash),
    ).fetchone()
    if existing and existing["user_id"] != user_id:
        raise ContactError("该联系方式已绑定其它账号。")
    if primary:
        db.execute(
            "UPDATE user_contacts SET is_primary = 0 WHERE user_id = ? AND contact_type = ?",
            (user_id, contact_type),
        )
    if existing:
        db.execute(
            """
            UPDATE user_contacts
            SET verified_at = COALESCE(verified_at, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END),
                is_primary = CASE WHEN ? THEN 1 ELSE is_primary END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if verified else 0, 1 if primary else 0, existing["id"]),
        )
        contact_id = existing["id"]
    else:
        cursor = db.execute(
            """
            INSERT INTO user_contacts
            (user_id, contact_type, contact_value, contact_value_hash, display_value, verified_at, is_primary)
            VALUES (?, ?, ?, ?, ?, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END, ?)
            """,
            (
                user_id,
                contact_type,
                normalized,
                value_hash,
                mask_contact(contact_type, normalized),
                1 if verified else 0,
                1 if primary else 0,
            ),
        )
        contact_id = cursor.lastrowid
    if primary and contact_type == "email":
        db.execute(
            """
            UPDATE users
            SET email = ?, email_verified = CASE WHEN ? THEN 1 ELSE email_verified END,
                primary_email_contact_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (normalized, 1 if verified else 0, contact_id, user_id),
        )
    elif primary and contact_type == "phone":
        db.execute(
            "UPDATE users SET primary_phone_contact_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (contact_id, user_id),
        )
    return contact_id


def get_contact_by_value(db, contact_type: str, value: str):
    normalized = normalize_contact(contact_type, value)
    return db.execute(
        "SELECT * FROM user_contacts WHERE contact_type = ? AND contact_value_hash = ?",
        (contact_type, contact_hash(contact_type, normalized)),
    ).fetchone()


def contacts_for_user(db, user_id: int) -> list[dict]:
    rows = db.execute(
        """
        SELECT id, contact_type, display_value, verified_at, is_primary, created_at
        FROM user_contacts
        WHERE user_id = ?
        ORDER BY contact_type, is_primary DESC, id DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def login_method_count(db, user_id: int) -> int:
    password_row = db.execute(
        "SELECT password_hash, password_enabled FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    count = 1 if password_row and password_row["password_hash"] and password_row["password_enabled"] else 0
    count += db.execute(
        "SELECT COUNT(*) AS c FROM user_contacts WHERE user_id = ? AND verified_at IS NOT NULL",
        (user_id,),
    ).fetchone()["c"]
    count += db.execute(
        "SELECT COUNT(*) AS c FROM user_identities WHERE user_id = ?",
        (user_id,),
    ).fetchone()["c"]
    return count
