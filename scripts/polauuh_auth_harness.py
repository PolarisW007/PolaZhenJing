#!/usr/bin/env python3
"""Run an isolated PolaUUH identity integration harness inside PolaZhenJing."""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, get_db


def result(name, ok, details=None):
    return {"name": name, "ok": bool(ok), "details": details or {}}


def run_harness():
    checks = []
    with tempfile.TemporaryDirectory(prefix="polauuh-auth-harness-") as temp_dir:
        app = create_app(
            {
                "TESTING": True,
                "POLAUUH_DATABASE_PATH": str(Path(temp_dir) / "identity.db"),
                "POLAUUH_EMAIL_VERIFICATION_REQUIRED": False,
                "POLAUUH_MAIL_ENABLED": True,
                "POLAUUH_SMS_ENABLED": True,
                "POLAUUH_GOOGLE_ENABLED": True,
                "POLAUUH_GOOGLE_CLIENT_ID": "harness-google-client",
                "POLAUUH_GOOGLE_CLIENT_SECRET": "harness-google-secret",
            }
        )
        client = app.test_client()

        response = client.get("/healthz")
        checks.append(result("healthz", response.status_code == 200, response.get_json()))

        login_page = client.get("/admin/login").get_data(as_text=True)
        labels = ["微信", "Apple", "Google", "支付宝", "华为"]
        checks.append(
            result(
                "identity-entrypoints",
                all(label in login_page for label in labels)
                and "/admin/auth/google/start" in login_page,
            )
        )

        response = client.post(
            "/admin/register",
            data={"username": "demo", "email": "demo@example.com", "password": "secret1"},
            follow_redirects=False,
        )
        checks.append(result("password-register", response.status_code in {302, 303}))
        response = client.post(
            "/admin/login",
            data={"username": "demo", "password": "secret1"},
            follow_redirects=False,
        )
        checks.append(result("password-login", response.status_code in {302, 303}))

        response = client.post(
            "/admin/api/sso/check",
            json={"app_id": "PolaRead", "permission": "polaread.use"},
        )
        payload = response.get_json()
        checks.append(
            result(
                "sso-contract",
                response.status_code == 200
                and payload.get("authenticated") is True
                and payload.get("authorized") is True,
            )
        )

        client.get("/admin/logout")
        response = client.post(
            "/admin/auth/otp/send",
            json={"channel": "email", "target": "otp@example.com", "purpose": "register_login"},
        )
        otp_payload = response.get_json()
        checks.append(
            result(
                "email-otp-send",
                response.status_code == 200 and bool(otp_payload.get("debug_code")),
            )
        )
        response = client.post(
            "/admin/auth/otp/verify",
            json={
                "channel": "email",
                "target": "otp@example.com",
                "purpose": "register_login",
                "code": otp_payload.get("debug_code"),
            },
        )
        checks.append(
            result(
                "email-otp-login",
                response.status_code == 200 and response.get_json().get("status") == "created",
            )
        )

        response = client.post(
            "/admin/auth/otp/send",
            json={"channel": "sms", "target": "13800138000", "purpose": "bind"},
        )
        sms_payload = response.get_json()
        response = client.post(
            "/admin/auth/otp/verify",
            json={
                "channel": "sms",
                "target": "13800138000",
                "purpose": "bind",
                "code": sms_payload.get("debug_code"),
            },
        )
        checks.append(
            result(
                "phone-bind",
                response.status_code == 200 and response.get_json().get("status") == "bound",
            )
        )

        client.get("/admin/logout")
        response = client.get("/admin/auth/google/start?next=/admin/account", follow_redirects=False)
        state = parse_qs(urlparse(response.headers.get("Location", "")).query).get("state", [""])[0]
        response = client.get(
            f"/admin/auth/google/callback?state={state}"
            "&test_subject=harness-google&test_email=harness-google@example.com",
            follow_redirects=False,
        )
        checks.append(
            result(
                "google-callback",
                bool(state) and response.status_code in {302, 303},
            )
        )
        response = client.get("/admin/api/me")
        profile = response.get_json().get("user", {})
        checks.append(
            result(
                "identity-payload",
                response.status_code == 200 and profile.get("identity_providers") == ["google"],
            )
        )

        with app.app_context():
            db = get_db()
            tables = {
                row["name"]
                for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            audit_count = db.execute("SELECT COUNT(*) AS count FROM auth_audit_logs").fetchone()["count"]
        required_tables = {
            "user_contacts",
            "user_identities",
            "verification_codes",
            "auth_requests",
            "auth_audit_logs",
        }
        checks.append(
            result(
                "identity-schema-and-audit",
                required_tables.issubset(tables) and audit_count >= 5,
                {"audit_count": audit_count},
            )
        )

    return all(check["ok"] for check in checks), checks


def main():
    parser = argparse.ArgumentParser(description="Run the PolaUUH identity harness.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    ok, checks = run_harness()
    if args.json:
        print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    else:
        for check in checks:
            print(f"{'PASS' if check['ok'] else 'FAIL'} {check['name']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
