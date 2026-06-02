#!/usr/bin/env python3
"""Safely check or configure the X access token for PolaZhenJing.

The script never prints token values. Use it on production to set
X_USER_ACCESS_TOKEN, then run scripts/x_publish_smoke.py with --post --yes.
"""

from __future__ import annotations

import argparse
import getpass
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


TOKEN_KEY = "X_USER_ACCESS_TOKEN"


def read_env_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def has_configured_token(lines: list[str]) -> bool:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == TOKEN_KEY:
            return bool(value.strip())
    return False


def upsert_token(lines: list[str], token: str) -> tuple[list[str], bool]:
    updated: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _ = stripped.split("=", 1)
            if key.strip() == TOKEN_KEY:
                updated.append(f"{TOKEN_KEY}={token}")
                replaced = True
                continue
        updated.append(line)
    if not replaced:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append(f"{TOKEN_KEY}={token}")
    return updated, replaced


def read_token(args: argparse.Namespace) -> str:
    if args.stdin:
        token = sys.stdin.read().strip()
    else:
        token = getpass.getpass(f"{TOKEN_KEY}: ").strip()
    if not token:
        raise ValueError(f"{TOKEN_KEY} 不能为空。")
    return token


def write_env(path: Path, lines: list[str]) -> Path | None:
    backup = None
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = path.with_name(f"{path.name}.bak.x-token-{stamp}")
        shutil.copy2(path, backup)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or configure PolaZhenJing X token.")
    parser.add_argument("--env-file", default=".env", help="Env file to inspect or update.")
    parser.add_argument("--check", action="store_true", help="Only report whether the token is configured.")
    parser.add_argument("--stdin", action="store_true", help="Read token from stdin instead of a hidden prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Validate input and report the planned update without writing.")
    parser.add_argument("--json", action="store_true", help="Print JSON status.")
    args = parser.parse_args()

    env_path = Path(args.env_file).expanduser()
    lines = read_env_lines(env_path)
    before = has_configured_token(lines)

    result: dict[str, object] = {
        "ok": True,
        "env_file": str(env_path),
        "key": TOKEN_KEY,
        "configured": before,
        "updated": False,
        "backup_created": False,
        "dry_run": bool(args.dry_run),
    }

    try:
        if not args.check:
            token = read_token(args)
            next_lines, replaced = upsert_token(lines, token)
            result["operation"] = "replace" if replaced else "append"
            if args.dry_run:
                result["would_configure"] = True
            else:
                backup = write_env(env_path, next_lines)
                result["updated"] = True
                result["configured"] = True
                result["backup_created"] = backup is not None
                result["backup_file"] = str(backup) if backup else ""
    except Exception as exc:
        result.update({"ok": False, "error": str(exc)})

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
