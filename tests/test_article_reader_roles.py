from pathlib import Path

from app import create_app
from app.uploader import POSTS_DIR, _article_admin_filename


def _sample_article_filename() -> str:
    posts = sorted(Path(POSTS_DIR).glob("*.md"), reverse=True)
    assert posts
    return posts[0].name


def _client_with_role(role: str | None = None):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    if role:
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = role
    return client


def test_public_article_hides_admin_and_share_controls():
    filename = _sample_article_filename()
    admin_filename = _article_admin_filename(filename)
    client = _client_with_role()

    response = client.get(f"/articles/{admin_filename}")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="summary-box"' in body
    assert body.count('class="summary-box"') == 1
    assert "快速 Wiki" in body
    assert "上一篇" in body
    assert "下一篇" in body
    assert "PolaZhenjing 管理后台" not in body
    assert "管理员文章工具" not in body
    assert "同步发布" not in body
    assert "查看 ↗" not in body
    assert "微信/朋友圈" not in body
    assert ">即刻<" not in body
    assert "Twitter" not in body
    assert "LinkedIn" not in body
    assert "data-copy-cardlink" not in body
    assert "微信图文卡片" not in body
    assert "下载卡片图" not in body


def test_logged_in_non_admin_article_nav_uses_polauuh_not_backend():
    filename = _sample_article_filename()
    admin_filename = _article_admin_filename(filename)
    client = _client_with_role("user")

    response = client.get(f"/articles/{admin_filename}")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "PolaUUH 用户中心" in body
    assert "设置" in body
    assert "PolaZhenjing 管理后台" not in body
    assert "上传" not in body
    assert "小王记忆" not in body


def test_admin_article_keeps_management_and_share_tools():
    filename = _sample_article_filename()
    admin_filename = _article_admin_filename(filename)
    client = _client_with_role("admin")

    response = client.get(f"/admin/articles/{admin_filename}")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "PolaZhenjing 管理后台" in body
    assert "管理员文章工具" in body
    assert "编辑" in body
    assert "同步发布" in body
    assert "查看 ↗" in body
    assert "微信/朋友圈" in body
    assert "即刻" in body
    assert "Twitter" in body
    assert "LinkedIn" in body
    assert "data-copy-cardlink" in body
    assert "微信图文卡片" in body
    assert "快速 Wiki" in body


def test_admin_controls_on_root_public_article_keep_polazhenjing_prefix():
    filename = _sample_article_filename()
    admin_filename = _article_admin_filename(filename)
    client = _client_with_role("admin")

    response = client.get(f"/articles/{admin_filename}")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'href="/PolaZhenjing/admin/articles/{admin_filename}/edit"' in body
    assert f'href="/PolaZhenjing/admin/social/articles/{admin_filename}"' in body
    assert f'action="/PolaZhenjing/admin/articles/{admin_filename}/delete"' in body
    assert f'href="/admin/articles/{admin_filename}/edit"' not in body
