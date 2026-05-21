#!/usr/bin/env python3
"""Production harness for the AIPD unified account center.

Run from the PolaZhenjing project root on the server. The harness creates a
real Flask session cookie for the target account, then checks the local app
bridges that should trust that unified session.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any


DEFAULT_CHECKS = [
    {
        "name": "pola-auth-check",
        "url": "http://127.0.0.1:5000/admin/api/sso/check",
        "payload": {"app_id": "PolaZhenjing", "permission": "articles.read"},
        "expect_status": 200,
        "expect_authorized": True,
    },
    {
        "name": "polaread-sso",
        "url": "http://127.0.0.1:8766/api/auth/sso/aipd",
        "payload": {},
        "expect_status": 200,
    },
    {
        "name": "polanews-sso",
        "url": "http://127.0.0.1:3456/polanews/api/auth/sso/aipd",
        "payload": {},
        "expect_status": 200,
    },
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    status: int | None
    detail: str
    data: dict[str, Any] | None = None


def request_json(url: str, payload: dict[str, Any], cookie: str,
                 timeout: float = 8.0) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Cookie": cookie,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            return response.status, data
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw}
        return exc.code, data


def get_json(url: str, headers: dict[str, str],
             timeout: float = 8.0) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            return response.status, data
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw}
        return exc.code, data


def make_session_cookie(email: str) -> tuple[str, dict[str, Any]]:
    sys.path.insert(0, str(Path.cwd()))
    from app import create_app  # noqa: WPS433
    from app.auth import get_db, user_payload  # noqa: WPS433

    app = create_app()
    with app.test_client() as client:
        with app.app_context():
            user = get_db().execute(
                "SELECT * FROM users WHERE email = ? OR username = ?",
                (email, email),
            ).fetchone()
            if user is None:
                raise SystemExit(f"no user found for {email}")
            payload = user_payload(user)
        with client.session_transaction() as session:
            session["user_id"] = int(user["id"])
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        cookie = client.get_cookie(cookie_name)
        if cookie is None:
            raise SystemExit("failed to create Flask session cookie")
        morsel = SimpleCookie()
        morsel[cookie_name] = cookie.value
        return morsel.output(header="", sep="").strip(), payload


def run_checks(cookie: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for check in DEFAULT_CHECKS:
        try:
            status, data = request_json(check["url"], check["payload"], cookie)
        except Exception as exc:  # pragma: no cover - harness diagnostics.
            results.append(CheckResult(
                name=check["name"],
                ok=False,
                status=None,
                detail=f"{type(exc).__name__}: {exc}",
            ))
            continue

        ok = status == check["expect_status"]
        if check.get("expect_authorized") is not None:
            ok = ok and data.get("authorized") is check["expect_authorized"]
        detail = "ok" if ok else json.dumps(data, ensure_ascii=False)[:500]
        results.append(CheckResult(
            name=check["name"],
            ok=ok,
            status=status,
            detail=detail,
            data=data,
        ))

        if check["name"] == "polaread-sso" and ok:
            token = data.get("data", {}).get("access_token")
            status, settings = get_json(
                "http://127.0.0.1:8766/api/settings",
                {"Authorization": f"Bearer {token}", "Cookie": cookie},
            )
            prefs_ok = (
                status == 200
                and settings.get("data", {}).get("theme") == "dream-gold"
                and settings.get("data", {}).get("font_family") == "system"
            )
            results.append(CheckResult(
                name="polaread-preferences-overlay",
                ok=prefs_ok,
                status=status,
                detail="ok" if prefs_ok else json.dumps(settings, ensure_ascii=False)[:500],
                data=settings,
            ))

        if check["name"] == "polanews-sso" and ok:
            token = data.get("data", {}).get("token")
            status, settings = get_json(
                "http://127.0.0.1:3456/polanews/api/settings",
                {"Authorization": f"Bearer {token}", "Cookie": cookie},
            )
            prefs_ok = (
                status == 200
                and settings.get("success") is True
                and settings.get("data", {}).get("theme") == "dream-gold"
                and settings.get("data", {}).get("font_family") == "system"
            )
            results.append(CheckResult(
                name="polanews-preferences-overlay",
                ok=prefs_ok,
                status=status,
                detail="ok" if prefs_ok else json.dumps(settings, ensure_ascii=False)[:500],
                data=settings,
            ))
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="wsyxjer@gmail.com")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cookie, user = make_session_cookie(args.email)
    results = run_checks(cookie)
    payload = {
        "ok": all(result.ok for result in results),
        "user": {
            "email": user.get("email"),
            "role": user.get("role"),
            "nickname": user.get("nickname"),
            "preferences": user.get("preferences"),
            "permissions": user.get("permissions"),
        },
        "checks": [result.__dict__ for result in results],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for result in results:
            mark = "PASS" if result.ok else "FAIL"
            print(f"{mark} {result.name} status={result.status} {result.detail}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
