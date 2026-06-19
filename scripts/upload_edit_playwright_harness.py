#!/usr/bin/env python3
"""Local Playwright harness for PolaZhenjing upload/edit editors.

Run a local Flask server first, for example:

    SECRET_KEY=dev-secret-change-me FLASK_APP='app:create_app' \
      .venv/bin/flask run --host 127.0.0.1 --port 5019

Then run:

    .venv/bin/python scripts/upload_edit_playwright_harness.py \
      --base-url http://127.0.0.1:5019
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_ARTICLE = "2026-04-11-test-article.md"
HARNESS_ARTICLE = "2026-06-19-upload-edit-harness.md"
SCREENSHOT_DIR = ROOT / "tmp" / "harness" / "upload-edit"


def _ensure_harness_user() -> tuple[str, str]:
    db_path = ROOT / "data" / "wiki.db"
    if not db_path.exists():
        raise RuntimeError(f"Local auth database not found: {db_path}")
    username = f"pola_harness_{os.getpid()}"
    email = f"{username}@local.test"
    password = f"pola-harness-{os.getpid()}"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, email, password_hash, nickname, role, email_verified)
            VALUES (?, ?, ?, ?, 'admin', 1)
            """,
            (username, email, generate_password_hash(password), username),
        )
        conn.commit()
    return username, password


def _delete_harness_user(username: str) -> None:
    db_path = ROOT / "data" / "wiki.db"
    if not db_path.exists() or not username:
        return
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            DELETE FROM users
            WHERE username = ? AND email LIKE 'pola_harness_%@local.test'
            """,
            (username,),
        )
        conn.commit()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-") or "page"


def _screenshot(page: Page, label: str) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{int(time.time())}-{_safe_name(label)}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def _create_harness_article() -> Path:
    posts_dir = ROOT / "_posts"
    posts_dir.mkdir(exist_ok=True)
    path = posts_dir / HARNESS_ARTICLE
    path.write_text(
        "---\n"
        "layout: deep-technical\n"
        "theme: claude\n"
        "title: Harness 保存测试\n"
        "date: 2026-06-19\n"
        "tags: [harness]\n"
        "summary: 临时保存链路测试文章\n"
        "---\n\n"
        "seed\n",
        encoding="utf-8",
    )
    return path


def _delete_harness_article(path: Path | None) -> None:
    if path and path.exists() and path.name == HARNESS_ARTICLE:
        path.unlink()


def _console_summary(messages: list[str], failed_requests: list[str], http_errors: list[str]) -> None:
    hard_errors = [
        msg
        for msg in messages
        if not any(
            ignored in msg.lower()
            for ignored in (
                "favicon",
                "devtools",
                "tinymce is running in read-only mode",
                "failed to load resource",
            )
        )
    ]
    hard_http_errors = [
        item for item in http_errors
        if "/favicon.ico" not in item
        and "/PolaZhenjing/assets/css/" not in item
    ]
    _assert(not hard_errors, "Console errors detected:\n" + "\n".join(hard_errors[:10]))
    hard_failed_requests = [
        item for item in failed_requests
        if "/PolaZhenjing/assets/css/" not in item
        and "fonts.googleapis.com/css2" not in item
    ]
    _assert(
        not hard_failed_requests,
        "Network failures detected:\n" + "\n".join(hard_failed_requests[:10]),
    )
    _assert(
        not hard_http_errors,
        "HTTP errors detected:\n" + "\n".join(hard_http_errors[:10]),
    )


def _wait_for_edit_preview(page: Page) -> None:
    preview = page.locator("#article-preview")
    preview.wait_for(state="visible", timeout=10_000)
    page.locator("#refresh-preview").click()
    page.wait_for_function(
        """
        () => {
          const el = document.querySelector('#article-preview');
          return el && el.textContent && !el.textContent.includes('预览生成中');
        }
        """,
        timeout=15_000,
    )


EDITOR_HTML_READY = """
() => {
  const fallback = document.querySelector('#rich-content')?.value || '';
  const editor = window.tinymce && tinymce.get('rich-content');
  if (!editor) return fallback.includes('<h1') && fallback.includes('<img');
  if (!editor.initialized || !editor.serializer) return false;
  try {
    const html = editor.getContent();
    return html && html.includes('<h1') && html.includes('<img');
  } catch (error) {
    return false;
  }
}
"""


def run(base_url: str, chrome_path: str, article: str, headed: bool = False) -> list[Path]:
    screenshots: list[Path] = []
    console_messages: list[str] = []
    failed_requests: list[str] = []
    http_errors: list[str] = []
    username, password = _ensure_harness_user()
    harness_article_path = _create_harness_article()
    launch_kwargs: dict[str, object] = {"headless": not headed}
    if chrome_path and Path(chrome_path).exists():
        launch_kwargs["executable_path"] = chrome_path

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                viewport={"width": 1440, "height": 1100},
                locale="zh-CN",
                base_url=base_url,
            )
            page = context.new_page()
            page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url} {req.failure}"))
            page.on("response", lambda res: http_errors.append(f"{res.status} {res.url}") if res.status >= 400 else None)

            page.goto("/admin/login", wait_until="domcontentloaded")
            page.locator('input[name="username"]').fill(username)
            page.locator('input[name="password"]').fill(password)
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_url(re.compile(r".*/admin/.*"), timeout=10_000)
            page.goto("/admin/upload", wait_until="domcontentloaded")

            _assert(page.locator("text=上传文章").count() > 0, "Upload page did not render title")
            _assert(page.locator("#paste-form").is_visible(), "Paste form is not visible")
            _assert(page.locator('input[name="rewrite_rate"]').count() >= 15, "Upload rewrite-rate options missing")

            page.locator('#tab-paste input[name="editor_mode"][value="markdown"]').check()
            page.wait_for_function("() => document.querySelector('#content-format')?.value === 'markdown'", timeout=10_000)
            page.locator("#content").fill("# Harness 上传测试\n\n![图](/assets/images/test_cover.jpg)\n\n**正文** 段落。")
            page.locator('#tab-paste input[name="editor_mode"][value="rich"]').check()
            page.wait_for_function("() => document.querySelector('#content-format')?.value === 'rich_html'", timeout=15_000)
            page.wait_for_function(EDITOR_HTML_READY, timeout=15_000)
            screenshots.append(_screenshot(page, "upload-rich-switch"))

            edit_path = f"/admin/articles/{article}/edit"
            page.goto(edit_path, wait_until="domcontentloaded")
            _assert(page.locator("#article-edit-form").is_visible(), "Edit form is not visible")
            _assert(page.locator("#content").is_visible(), "Edit Markdown textarea should be visible by default")
            _assert(page.locator('#content-format').input_value() == "markdown", "Edit default mode should be markdown")
            _assert(page.locator('input[name="rewrite_rate"]').count() >= 5, "Edit rewrite-rate options missing")

            page.locator("#content").fill("# Harness 编辑测试\n\n![图](/assets/images/test_cover.jpg)\n\n**正文** 段落。")
            _wait_for_edit_preview(page)
            preview_html = page.locator("#article-preview").inner_html()
            _assert("<h1" in preview_html and "<img" in preview_html, "Edit preview did not render heading and image")

            page.locator('input[name="editor_mode"][value="rich"]').check()
            page.wait_for_function("() => document.querySelector('#content-format')?.value === 'rich_html'", timeout=15_000)
            page.wait_for_function(EDITOR_HTML_READY, timeout=15_000)
            page.locator('input[name="editor_mode"][value="markdown"]').check()
            page.wait_for_function("() => document.querySelector('#content-format')?.value === 'markdown'", timeout=15_000)
            markdown = page.locator("#content").input_value()
            _assert(
                "# Harness 编辑测试" in markdown and "![" in markdown,
                "Rich to Markdown conversion lost content:\n" + markdown[:500],
            )

            page.locator("#revision_instruction").fill("Harness：验证修改建议字段可以填写。")
            _assert("Harness" in page.locator("#revision_instruction").input_value(), "Revision note field is not editable")
            screenshots.append(_screenshot(page, "edit-markdown-rich-preview"))

            page.goto(f"/admin/articles/{HARNESS_ARTICLE}/edit", wait_until="domcontentloaded")
            page.locator("#content").fill("## Harness 保存验证\n\n保存按钮必须真实提交并写回文章。")
            page.locator("#revision_instruction").fill("Harness：验证保存按钮可提交；改写率为 0，不调用模型。")
            page.locator('input[name="rewrite_rate"][value="0"]').check()
            page.locator('button[type="submit"][name="save_mode"][value="save"]').click()
            page.wait_for_url(
                re.compile(r".*/admin/articles/(2026\-06\-19\-)?upload\-edit\-harness\.md$"),
                timeout=15_000,
            )
            saved = harness_article_path.read_text(encoding="utf-8")
            _assert("Harness 保存验证" in saved, "Save button did not write updated Markdown")
            _assert("保存按钮必须真实提交并写回文章" in saved, "Saved article body is missing expected content")
            screenshots.append(_screenshot(page, "edit-save-submitted"))

            _console_summary(console_messages, failed_requests, http_errors)
            context.close()
            browser.close()
    finally:
        _delete_harness_user(username)
        _delete_harness_article(harness_article_path)
    return screenshots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5019")
    parser.add_argument("--chrome", default=os.getenv("PLAYWRIGHT_CHROME", DEFAULT_CHROME))
    parser.add_argument("--article", default=os.getenv("PZJ_HARNESS_ARTICLE", DEFAULT_ARTICLE))
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    parsed = urlparse(args.base_url)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit(f"Invalid --base-url: {args.base_url}")

    screenshots = run(args.base_url.rstrip("/"), args.chrome, args.article, headed=args.headed)
    print("Playwright upload/edit harness passed")
    for path in screenshots:
        print(f"screenshot: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
