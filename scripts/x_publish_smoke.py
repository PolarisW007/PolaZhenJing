#!/usr/bin/env python3
"""X publishing smoke test for PolaZhenJing.

Default mode is read-only: it checks configuration, selects an article, builds
the X post text, and reports whether the final production post can run.
Use `--post --yes` only after X_USER_ACCESS_TOKEN is configured.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app import social_publish  # noqa: E402
from app.uploader import _scan_posts  # noqa: E402


def choose_filename(filename: str | None) -> str:
    if filename:
        return filename
    posts = _scan_posts()
    if not posts:
        raise RuntimeError("没有可用于 X smoke 的文章。")
    return posts[0]["filename"]


def run(args: argparse.Namespace) -> dict[str, Any]:
    app = create_app()
    base_url = args.base_url.rstrip("/") + "/"
    with app.test_request_context(base_url=base_url):
        filename = choose_filename(args.filename)
        ctx = social_publish._post_context(filename)
        status = social_publish._x_config_status()
        text = social_publish.build_x_post_text(ctx)
        existing = social_publish._latest_successful_publication(ctx["filename"], "x", {"posted"})

        result: dict[str, Any] = {
            "ok": True,
            "mode": "post" if args.post else "dry-run",
            "filename": ctx["filename"],
            "admin_filename": ctx["admin_filename"],
            "title": ctx["title"],
            "configured": bool(status.get("configured")),
            "missing": status.get("missing", []),
            "text_length": len(text),
            "text_preview": text[:120],
            "existing_post_id": existing.get("external_id") if existing else "",
            "existing_post_url": existing.get("external_url") if existing else "",
            "posted": False,
            "post_id": "",
            "post_url": "",
        }

        if not status.get("configured"):
            result["ok"] = not args.require_token and not args.post
            result["blocked_by"] = status.get("missing", ["X_USER_ACCESS_TOKEN"])
            return result

        if existing and not args.force:
            result["blocked_by"] = ["existing_x_post"]
            result["ok"] = not args.post
            return result

        if not args.post:
            result["ready_to_post"] = True
            return result

        if not args.yes:
            raise RuntimeError("真实发帖必须同时传入 --post --yes。")

        publication_id = social_publish._create_publication(ctx["filename"], "x", "pending", mode="post")
        post = social_publish._create_x_post(ctx)
        social_publish._update_publication(
            publication_id,
            status="posted",
            payload={
                "x": {
                    "post_id": post["post_id"],
                    "media_id": post["media_id"],
                    "text": post["text"],
                },
                "title": ctx["title"],
                "source_url": social_publish._public_source_url(ctx),
            },
            external_id=post["post_id"],
            external_url=post["url"],
            event_message="X smoke post 已发布。",
        )
        result.update({
            "posted": True,
            "post_id": post["post_id"],
            "post_url": post["url"],
            "text_length": len(post["text"]),
        })
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PolaZhenJing X publishing smoke test.")
    parser.add_argument("--filename", help="Article filename. Defaults to latest scanned post.")
    parser.add_argument("--base-url", default="https://aipd.me/PolaZhenjing", help="Public base URL used for generated links.")
    parser.add_argument("--post", action="store_true", help="Actually call X API and create a post.")
    parser.add_argument("--yes", action="store_true", help="Required with --post.")
    parser.add_argument("--force", action="store_true", help="Allow posting even when a previous X post exists.")
    parser.add_argument("--require-token", action="store_true", help="Exit non-zero if X token is missing.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    try:
        result = run(args)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")

    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
