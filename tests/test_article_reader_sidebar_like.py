from pathlib import Path

from app import create_app, get_db
from app.uploader import POSTS_DIR, _article_admin_filename


def _sample_article_filename() -> str:
    posts = sorted(Path(POSTS_DIR).glob("*.md"), reverse=True)
    assert posts
    return posts[0].name


def _client():
    app = create_app()
    app.config["TESTING"] = True
    return app, app.test_client()


def _saved_like_state(app, article_id: str):
    with app.app_context():
        row = get_db().execute(
            "SELECT like_count FROM article_likes WHERE article_id = ?",
            (article_id,),
        ).fetchone()
        return None if row is None else int(row["like_count"] or 0)


def _restore_like_state(app, article_id: str, previous_count):
    with app.app_context():
        db = get_db()
        if previous_count is None:
            db.execute("DELETE FROM article_likes WHERE article_id = ?", (article_id,))
        else:
            db.execute(
                """
                INSERT INTO article_likes (article_id, like_count, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(article_id) DO UPDATE
                   SET like_count = excluded.like_count,
                       updated_at = CURRENT_TIMESTAMP
                """,
                (article_id, previous_count),
            )
        db.commit()


def test_article_reader_uses_side_panel_and_like_controls():
    filename = _sample_article_filename()
    admin_filename = _article_admin_filename(filename)
    _, client = _client()

    response = client.get(f"/articles/{admin_filename}", base_url="https://aipd.me")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-reader-shell' in body
    assert 'data-reader-sidebar' in body
    assert 'article-reader-nav-side' in body
    assert 'data-reader-width-toggle' in body
    assert 'data-like-button' in body
    assert 'data-like-count' in body
    assert f'data-article-id="{admin_filename}"' in body
    assert f'data-like-url="/articles/{admin_filename}/like"' in body
    assert body.index('class="author-footer"') < body.index('data-reader-sidebar')


def test_article_like_api_increments_and_decrements():
    filename = _sample_article_filename()
    admin_filename = _article_admin_filename(filename)
    app, client = _client()
    previous_count = _saved_like_state(app, admin_filename)

    try:
        get_response = client.get(
            f"/articles/{admin_filename}/like",
            base_url="https://aipd.me",
        )
        assert get_response.status_code == 200
        initial_count = int(get_response.get_json()["like_count"])

        like_response = client.post(
            f"/articles/{admin_filename}/like",
            json={"liked": True},
            base_url="https://aipd.me",
        )
        assert like_response.status_code == 200
        like_payload = like_response.get_json()
        assert like_payload["ok"] is True
        assert like_payload["liked"] is True
        assert like_payload["like_count"] == initial_count + 1

        unlike_response = client.post(
            f"/articles/{admin_filename}/like",
            json={"liked": False},
            base_url="https://aipd.me",
        )
        assert unlike_response.status_code == 200
        unlike_payload = unlike_response.get_json()
        assert unlike_payload["ok"] is True
        assert unlike_payload["liked"] is False
        assert unlike_payload["like_count"] == initial_count
    finally:
        _restore_like_state(app, admin_filename, previous_count)
