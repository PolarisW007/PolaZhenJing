import sqlite3
from urllib.parse import parse_qs, urlparse

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, get_db
from app.identity.providers import ProviderError, consume_auth_request
from app.identity.verification import VerificationError, consume_otp


@pytest.fixture
def identity_app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "identity-test-secret",
            "POLAUUH_DATABASE_PATH": str(tmp_path / "identity.db"),
            "POLAUUH_EMAIL_VERIFICATION_REQUIRED": False,
            "POLAUUH_MAIL_ENABLED": True,
            "POLAUUH_SMS_ENABLED": True,
            "POLAUUH_OTP_RESEND_SECONDS": 60,
            "POLAUUH_OTP_MAX_ATTEMPTS": 2,
            "POLAUUH_ADMIN_USERNAMES": {"admin"},
            "POLAUUH_ADMIN_EMAILS": {"admin@example.com"},
        }
    )


@pytest.fixture
def identity_client(identity_app):
    return identity_app.test_client()


def register(client, username="demo", email="demo@example.com", password="secret1"):
    return client.post(
        "/admin/register",
        data={"username": username, "email": email, "password": password},
        follow_redirects=False,
    )


def login(client, username="demo", password="secret1"):
    return client.post(
        "/admin/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def _proxy_headers():
    return {
        "X-Script-Name": "/PolaUUH",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-Host": "aipd.me",
    }


def _enable_google(app):
    app.config.update(
        POLAUUH_GOOGLE_ENABLED=True,
        POLAUUH_GOOGLE_CLIENT_ID="google-client",
        POLAUUH_GOOGLE_CLIENT_SECRET="google-secret",
    )


def _google_start(client, *, mode="", next_url="/admin/account"):
    suffix = f"&mode={mode}" if mode else ""
    response = client.get(
        f"/admin/auth/google/start?next={next_url}{suffix}",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        follow_redirects=False,
    )
    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["Location"]).query)
    return response, query["state"][0]


def test_migration_preserves_legacy_user_and_builds_verified_contact(tmp_path):
    db_path = tmp_path / "legacy.db"
    db = sqlite3.connect(db_path)
    db.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        "INSERT INTO users (username, email, password_hash, email_verified) VALUES (?, ?, ?, 1)",
        ("legacy", "legacy@example.com", generate_password_hash("secret1")),
    )
    db.commit()
    db.close()

    app = create_app(
        {
            "TESTING": True,
            "POLAUUH_DATABASE_PATH": str(db_path),
            "POLAUUH_EMAIL_VERIFICATION_REQUIRED": False,
        }
    )

    with app.app_context():
        migrated = get_db().execute("SELECT * FROM users WHERE username = 'legacy'").fetchone()
        contact = get_db().execute("SELECT * FROM user_contacts WHERE user_id = ?", (migrated["id"],)).fetchone()
        assert migrated["password_enabled"] == 1
        assert migrated["status"] == "active"
        assert contact["contact_value"] == "legacy@example.com"
        assert contact["verified_at"] is not None


def test_password_login_and_sso_contract_remain_compatible(identity_client):
    assert register(identity_client).status_code == 302
    assert login(identity_client).status_code == 302

    response = identity_client.post(
        "/admin/api/sso/check",
        json={"app_id": "PolaRead", "permission": "polaread.use"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["authenticated"] is True
    assert payload["authorized"] is True
    assert payload["provider"] == "PolaUUH"


def test_email_otp_creates_passwordless_user_and_audit(identity_app, identity_client):
    sent = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "email", "target": "otp@example.com", "purpose": "register_login"},
    )
    assert sent.status_code == 200
    code = sent.get_json()["debug_code"]

    verified = identity_client.post(
        "/admin/auth/otp/verify",
        json={
            "channel": "email",
            "target": "otp@example.com",
            "purpose": "register_login",
            "code": code,
            "next": "/admin/account",
        },
    )
    assert verified.status_code == 200
    assert verified.get_json()["status"] == "created"

    me = identity_client.get("/admin/api/me").get_json()
    assert me["user"]["email"] == "otp@example.com"
    assert me["user"]["contacts"]["email_verified"] is True
    with identity_app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = 'otp@example.com'").fetchone()
        assert user["password_enabled"] == 0
        assert db.execute("SELECT COUNT(*) AS c FROM auth_audit_logs").fetchone()["c"] >= 2


def test_otp_marks_existing_pending_email_as_verified(identity_app, identity_client):
    with identity_app.app_context():
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO users
            (username, email, password_hash, password_enabled, email_verified, nickname, role, status)
            VALUES ('pending', 'pending@example.com', ?, 1, 0, 'pending', 'user', 'active')
            """,
            (generate_password_hash("secret1"),),
        )
        from app.identity.contacts import ensure_contact

        ensure_contact(db, cursor.lastrowid, "email", "pending@example.com", verified=False, primary=True)
        db.commit()
    sent = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "email", "target": "pending@example.com", "purpose": "register_login"},
    ).get_json()
    verified = identity_client.post(
        "/admin/auth/otp/verify",
        json={
            "channel": "email",
            "target": "pending@example.com",
            "purpose": "register_login",
            "code": sent["debug_code"],
        },
    )
    assert verified.status_code == 200
    with identity_app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = 'pending'").fetchone()
        contact = db.execute("SELECT * FROM user_contacts WHERE user_id = ?", (user["id"],)).fetchone()
        assert user["email_verified"] == 1
        assert contact["verified_at"] is not None


def test_otp_rate_limit_and_attempt_limit(identity_client):
    sent = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "email", "target": "limit@example.com", "purpose": "register_login"},
    )
    assert sent.status_code == 200
    repeated = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "email", "target": "limit@example.com", "purpose": "register_login"},
    )
    assert repeated.status_code == 429
    assert repeated.get_json()["error"] == "rate_limited"

    for _ in range(2):
        bad = identity_client.post(
            "/admin/auth/otp/verify",
            json={
                "channel": "email",
                "target": "limit@example.com",
                "purpose": "register_login",
                "code": "000000",
            },
        )
        assert bad.status_code == 400
    blocked = identity_client.post(
        "/admin/auth/otp/verify",
        json={
            "channel": "email",
            "target": "limit@example.com",
            "purpose": "register_login",
            "code": sent.get_json()["debug_code"],
        },
    )
    assert blocked.status_code == 429
    assert blocked.get_json()["error"] == "otp_attempts_exceeded"


def test_delivery_failure_rolls_back_code_and_returns_503(identity_app, identity_client, monkeypatch):
    identity_app.config["TESTING"] = False
    monkeypatch.setattr("app.identity.verification.send_verification_code", lambda *_args: False)

    response = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "email", "target": "failure@example.com", "purpose": "register_login"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "delivery_failed"
    with identity_app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) AS c FROM verification_codes").fetchone()["c"] == 0
        event = db.execute("SELECT * FROM auth_audit_logs ORDER BY id DESC LIMIT 1").fetchone()
        assert event["event_type"] == "otp_delivery_failed"


def test_sms_requires_captcha_before_otp(identity_app, identity_client, monkeypatch):
    identity_app.config.update(
        POLAUUH_ALIYUN_CAPTCHA_ENABLED=True,
        POLAUUH_ALIYUN_CAPTCHA_SCENE_ID="scene",
    )
    seen = []

    def fake_verify(value):
        seen.append(value)
        if value != "captcha-ok":
            from app.identity.captcha import CaptchaError

            raise CaptchaError("captcha_verify_failed", "真人验证失败。")

    monkeypatch.setattr("app.identity.verification.verify_sms_captcha", fake_verify)
    missing = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "sms", "target": "13800138000", "purpose": "register_login"},
    )
    assert missing.status_code == 400
    passed = identity_client.post(
        "/admin/auth/otp/send",
        json={
            "channel": "sms",
            "target": "13800138000",
            "purpose": "register_login",
            "captcha_verify_param": "captcha-ok",
        },
    )
    assert passed.status_code == 200
    assert seen == ["", "captcha-ok"]


def test_registration_verification_uses_server_side_hashed_code(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "POLAUUH_DATABASE_PATH": str(tmp_path / "register-verify.db"),
            "POLAUUH_EMAIL_VERIFICATION_REQUIRED": True,
            "POLAUUH_MAIL_ENABLED": True,
        }
    )
    client = app.test_client()
    response = register(client, email="verify@example.com")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/verify")
    with client.session_transaction() as session:
        assert "verify_code" not in session
        code = session["verify_debug_code"]
    verified = client.post("/admin/verify", data={"code": code})
    assert verified.status_code == 302
    with app.app_context():
        row = get_db().execute("SELECT * FROM users WHERE email = 'verify@example.com'").fetchone()
        assert row["email_verified"] == 1


def test_google_oauth_callback_uses_proxy_url_and_rejects_replay(identity_app, identity_client):
    _enable_google(identity_app)
    response, state = _google_start(identity_client, next_url="/PolaRead/login")
    query = parse_qs(urlparse(response.headers["Location"]).query)
    assert query["redirect_uri"] == ["https://aipd.me/PolaUUH/admin/auth/google/callback"]

    callback = identity_client.get(
        f"/admin/auth/google/callback?state={state}&test_subject=google-123&test_email=g@example.com&test_name=Google%20User",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert callback.headers["Location"].endswith("/PolaRead/login")
    me = identity_client.get(
        "/admin/api/me",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
    ).get_json()
    assert me["user"]["identity_providers"] == ["google"]

    replay = identity_client.get(
        f"/admin/auth/google/callback?state={state}&test_subject=google-123",
        base_url="https://aipd.me",
        headers={**_proxy_headers(), "Accept": "application/json"},
    )
    assert replay.status_code == 400
    assert replay.get_json()["error"] == "provider_callback_invalid"


def test_apple_form_post_callback_survives_missing_session_nonce(identity_app, identity_client):
    identity_app.config.update(
        POLAUUH_APPLE_ENABLED=True,
        POLAUUH_APPLE_CLIENT_ID="apple-client",
        POLAUUH_APPLE_TEAM_ID="team",
        POLAUUH_APPLE_KEY_ID="key",
        POLAUUH_APPLE_PRIVATE_KEY_PATH="/tmp/test-apple-key.p8",
    )
    response = identity_client.get(
        "/admin/auth/apple/start?next=/admin/account",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        follow_redirects=False,
    )
    state = parse_qs(urlparse(response.headers["Location"]).query)["state"][0]
    assert "polauuh_oauth_nonce=" in response.headers.get("Set-Cookie", "")
    with identity_client.session_transaction(base_url="https://aipd.me") as session:
        session.clear()
    callback = identity_client.post(
        "/admin/auth/apple/callback",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        data={"state": state, "test_subject": "apple-form-post"},
        follow_redirects=False,
    )
    assert callback.status_code == 302
    with identity_app.app_context():
        assert get_db().execute(
            "SELECT COUNT(*) AS c FROM user_identities WHERE provider = 'apple'"
        ).fetchone()["c"] == 1


def test_provider_verified_email_never_silently_merges_existing_user(identity_app, identity_client):
    register(identity_client, email="owner@example.com")
    identity_client.get("/admin/logout")
    _enable_google(identity_app)
    _response, state = _google_start(identity_client)

    callback = identity_client.get(
        f"/admin/auth/google/callback?state={state}&test_subject=other-google&test_email=owner@example.com",
        base_url="https://aipd.me",
        headers={**_proxy_headers(), "Accept": "application/json"},
    )
    assert callback.status_code == 409
    assert callback.get_json()["error"] == "identity_conflict"
    with identity_app.app_context():
        assert get_db().execute("SELECT COUNT(*) AS c FROM user_identities").fetchone()["c"] == 0


def test_logged_in_user_can_bind_provider(identity_app, identity_client):
    identity_client.post(
        "/admin/register",
        base_url="https://aipd.me",
        data={"username": "demo", "email": "demo@example.com", "password": "secret1"},
    )
    identity_client.post(
        "/admin/login",
        base_url="https://aipd.me",
        data={"username": "demo", "password": "secret1"},
    )
    _enable_google(identity_app)
    _response, state = _google_start(identity_client, mode="bind")

    callback = identity_client.get(
        f"/admin/auth/google/callback?state={state}&test_subject=bound-google&test_name=Bound",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        follow_redirects=False,
    )
    assert callback.status_code == 302
    with identity_app.app_context():
        row = get_db().execute("SELECT * FROM user_identities WHERE provider = 'google'").fetchone()
        owner = get_db().execute("SELECT id FROM users WHERE username = 'demo'").fetchone()
        assert row["user_id"] == owner["id"]


def test_provider_without_contact_cannot_unlink_its_only_identity(identity_app, identity_client):
    _enable_google(identity_app)
    _response, state = _google_start(identity_client)
    callback = identity_client.get(
        f"/admin/auth/google/callback?state={state}&test_subject=only-google",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        follow_redirects=False,
    )
    assert callback.status_code == 302
    response = identity_client.post(
        "/admin/account/identities/google/unlink",
        base_url="https://aipd.me",
        headers=_proxy_headers(),
        follow_redirects=False,
    )
    assert response.status_code == 302
    with identity_app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) AS c FROM user_contacts").fetchone()["c"] == 0
        assert db.execute("SELECT COUNT(*) AS c FROM user_identities").fetchone()["c"] == 1


def test_last_login_method_cannot_be_unlinked(identity_app, identity_client):
    sent = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "sms", "target": "13800138000", "purpose": "register_login"},
    ).get_json()
    identity_client.post(
        "/admin/auth/otp/verify",
        json={
            "channel": "sms",
            "target": "13800138000",
            "purpose": "register_login",
            "code": sent["debug_code"],
        },
    )
    with identity_app.app_context():
        contact_id = get_db().execute("SELECT id FROM user_contacts").fetchone()["id"]
    response = identity_client.post(
        f"/admin/account/contacts/{contact_id}/unlink",
        follow_redirects=False,
    )
    assert response.status_code == 302
    with identity_app.app_context():
        assert get_db().execute("SELECT COUNT(*) AS c FROM user_contacts").fetchone()["c"] == 1


def test_passwordless_user_can_set_password(identity_app, identity_client):
    sent = identity_client.post(
        "/admin/auth/otp/send",
        json={"channel": "email", "target": "setpass@example.com", "purpose": "register_login"},
    ).get_json()
    identity_client.post(
        "/admin/auth/otp/verify",
        json={
            "channel": "email",
            "target": "setpass@example.com",
            "purpose": "register_login",
            "code": sent["debug_code"],
        },
    )
    response = identity_client.post(
        "/admin/password",
        data={"current_password": "", "new_password": "newpass1", "confirm_password": "newpass1"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    identity_client.get("/admin/logout")
    logged_in = login(identity_client, username="setpass", password="newpass1")
    assert logged_in.status_code == 302


def test_otp_claim_rejects_a_concurrent_winner(identity_app, monkeypatch):
    class Cursor:
        def __init__(self, row=None, rowcount=-1):
            self._row = row
            self.rowcount = rowcount

        def fetchone(self):
            return self._row

    class LostClaimDb:
        def execute(self, sql, _params):
            if sql.lstrip().startswith("SELECT"):
                return Cursor(
                    {
                        "id": 1,
                        "attempt_count": 0,
                        "max_attempts": 5,
                        "expires_at": "2999-01-01T00:00:00+00:00",
                        "code_hash": "expected",
                    }
                )
            assert "used_at IS NULL" in sql
            return Cursor(rowcount=0)

    monkeypatch.setattr("app.identity.verification._code_hash", lambda *_args: "expected")
    with identity_app.app_context(), pytest.raises(VerificationError) as exc_info:
        consume_otp(LostClaimDb(), "email", "race@example.com", "register_login", "123456")
    assert exc_info.value.code == "otp_invalid"


def test_oauth_state_claim_rejects_a_concurrent_winner(identity_app):
    class Cursor:
        def __init__(self, row=None, rowcount=-1):
            self._row = row
            self.rowcount = rowcount

        def fetchone(self):
            return self._row

    class LostClaimDb:
        def execute(self, sql, _params):
            if sql.lstrip().startswith("SELECT"):
                return Cursor({"id": 1, "expires_at": "2999-01-01T00:00:00+00:00"})
            assert "consumed_at IS NULL" in sql
            return Cursor(rowcount=0)

    with identity_app.app_context(), pytest.raises(ProviderError) as exc_info:
        consume_auth_request(LostClaimDb(), "google", "racing-state")
    assert exc_info.value.code == "provider_callback_invalid"
