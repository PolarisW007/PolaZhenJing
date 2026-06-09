"""Regression test: long article body should not trigger 413.

Werkzeug 3.x defaults max_form_memory_size to 500KB. A long article edited in
TinyMCE rich mode can easily exceed that (HTML is 1.5-2x larger than markdown,
plus pasted images). The article_edit POST route must accept bodies up to
MAX_FORM_MEMORY_SIZE.
"""
import pytest

from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    target = posts_dir / "2026-06-09-bigbody.md"
    target.write_text(
        "---\nlayout: deep-technical\ntitle: big body\ndate: 2026-06-09\n---\n\nseed\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ALLOW_FAKE_LOGIN", "1")
    app = create_app()
    app.config["TESTING"] = True
    # Mirror the production path layout without touching real /PolaZhenjing.
    monkeypatch.setattr("app.uploader.POSTS_DIR", str(posts_dir), raising=False)
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user_id"] = 1
            s["role"] = "admin"
    yield app.test_client()


def _post_with_body_kb(client, kb):
    body = ("<p>" + ("x" * 50) + "</p>") * (kb * 1024 // 60)
    return client.post(
        "/admin/articles/2026-06-09-bigbody.md/edit",
        data={"title": "t", "date": "2026-06-09", "body": body, "save_mode": "save"},
        follow_redirects=False,
    )


def test_500kb_body_should_not_413(client):
    """The default Werkzeug max_form_memory_size is 500KB, so this would 413
    before the fix. After MAX_FORM_MEMORY_SIZE = 16MB, expect 302."""
    r = _post_with_body_kb(client, 500)
    assert r.status_code == 302, f"got {r.status_code}, body[:200]={r.get_data(as_text=True)[:200]!r}"


def test_1mb_body_should_not_413(client):
    r = _post_with_body_kb(client, 1024)
    assert r.status_code == 302, f"got {r.status_code}, body[:200]={r.get_data(as_text=True)[:200]!r}"


def test_8mb_body_should_not_413(client):
    r = _post_with_body_kb(client, 8192)
    assert r.status_code == 302, f"got {r.status_code}, body[:200]={r.get_data(as_text=True)[:200]!r}"


