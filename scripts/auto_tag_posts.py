#!/usr/bin/env python3
"""Auto-tag PolaZhenjing markdown posts with the shared uploader taxonomy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.uploader import (  # noqa: E402
    ARTICLE_PRIMARY_TAGS,
    STYLE_TAGS,
    _article_keywords,
    _auto_article_tags,
    _dedupe_article_tags,
)


POSTS_DIR = ROOT / "_posts"


def split_post(raw: str) -> tuple[str, str, str]:
    if not raw.startswith("---"):
        return "", "", raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return "", "", raw
    return parts[1].strip("\n"), parts[2].lstrip("\n"), raw


def front_value(front: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", front, re.M)
    return match.group(1).strip() if match else ""


def normalized_tag_line(tags: list[str]) -> str:
    return f"tags: [{', '.join(tags)}]"


def update_front_tags(front: str, tags: list[str]) -> str:
    line = normalized_tag_line(tags)
    if re.search(r"^tags:\s*.*$", front, re.M):
        return re.sub(r"^tags:\s*.*$", line, front, count=1, flags=re.M)
    for anchor in ["summary", "description", "image", "date", "title", "layout"]:
        if re.search(rf"^{anchor}:\s*.*$", front, re.M):
            return re.sub(rf"^({anchor}:\s*.*)$", rf"\1\n{line}", front, count=1, flags=re.M)
    return front.rstrip() + "\n" + line


def desired_tags(front: str, body: str) -> list[str]:
    title = front_value(front, "title").strip('"').strip("'")
    current = _article_keywords(front_value(front, "tags"))
    current = _dedupe_article_tags(current)
    primary_tags = set(ARTICLE_PRIMARY_TAGS)
    should_retag = (
        not current
        or current[0] in STYLE_TAGS
        or current[0] not in primary_tags
    )
    if should_retag:
        return _auto_article_tags(title, body)
    return _auto_article_tags(title, body, ", ".join(current))


def process_post(path: Path, *, write: bool) -> dict:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    front, body, original = split_post(raw)
    if not front:
        return {"file": path.name, "changed": False, "error": "missing-front-matter"}
    before = _dedupe_article_tags(_article_keywords(front_value(front, "tags")))
    after = desired_tags(front, body)
    new_front = update_front_tags(front, after)
    new_raw = f"---\n{new_front}\n---\n\n{body}"
    changed = new_raw != original
    if changed and write:
        path.write_text(new_raw, encoding="utf-8")
    return {
        "file": path.name,
        "title": front_value(front, "title").strip('"').strip("'"),
        "changed": changed,
        "before": before,
        "after": after,
    }


def check_posts(results: list[dict]) -> list[str]:
    errors: list[str] = []
    primary_tags = set(ARTICLE_PRIMARY_TAGS)
    for item in results:
        if item.get("error"):
            errors.append(f"{item['file']}: {item['error']}")
            continue
        tags = item.get("after") or []
        if not tags:
            errors.append(f"{item['file']}: missing tags")
        elif tags[0] not in primary_tags:
            errors.append(f"{item['file']}: first tag is not primary category: {tags[0]}")
        if any(tag in STYLE_TAGS for tag in tags):
            errors.append(f"{item['file']}: contains style tag")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--posts-dir", type=Path, default=POSTS_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    posts = sorted(args.posts_dir.glob("*.md"))
    results = [process_post(path, write=not args.dry_run and not args.check) for path in posts]
    errors = check_posts(results)
    payload = {
        "ok": not errors,
        "mode": "check" if args.check else "dry-run" if args.dry_run else "write",
        "post_count": len(results),
        "changed_count": sum(1 for item in results if item.get("changed")),
        "errors": errors,
        "changed": [item for item in results if item.get("changed")][:80],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
