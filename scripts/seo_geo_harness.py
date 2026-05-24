#!/usr/bin/env python3
"""SEO/GEO metadata harness for Jekyll posts and portal static pages."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_jekyll_posts() -> list[str]:
    errors: list[str] = []
    head = (ROOT / "_includes" / "head.html").read_text(encoding="utf-8")
    for token in [
        "og:description",
        "og:image",
        "twitter:card",
        "application/ld+json",
        "canonical",
        "truncate: 180",
    ]:
        if token not in head:
            errors.append(f"_includes/head.html missing {token}")

    for post in (ROOT / "_posts").glob("*.md"):
        raw = post.read_text(encoding="utf-8", errors="ignore")
        if not raw.startswith("---"):
            errors.append(f"{post.name} missing front matter")
            continue
        front = raw.split("---", 2)[1]
        for key in ["title", "date", "description", "image"]:
            if not re.search(rf"^{key}:", front, re.M):
                errors.append(f"{post.name} missing {key}")
        description = re.search(r"^description:\s*[\"']?(.*?)[\"']?\s*$", front, re.M)
        if description and len(description.group(1)) > 220:
            errors.append(f"{post.name} description too long: {len(description.group(1))}")
        image = re.search(r"^image:\s*[\"']?(.*?)[\"']?\s*$", front, re.M)
        if image and not (image.group(1).startswith("/") or image.group(1).startswith("https://")):
            errors.append(f"{post.name} image is not absolute-ready: {image.group(1)}")
    return errors


def check_static_portal() -> list[str]:
    errors: list[str] = []
    for rel in ["portal/index.html", "portal/about.html", "portal/agent.html"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for token in ["canonical", "og:image", "twitter:card", "application/ld+json"]:
            if token not in text:
                errors.append(f"{rel} missing {token}")
    for rel in ["robots.txt", "sitemap.xml", "llms.txt", "portal/robots.txt", "portal/sitemap.xml", "portal/llms.txt"]:
        if not (ROOT / rel).exists():
            errors.append(f"missing {rel}")
    return errors


def main() -> int:
    errors = check_jekyll_posts() + check_static_portal()
    print(json.dumps({"ok": not errors, "error_count": len(errors), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
