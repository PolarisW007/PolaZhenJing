from app import create_app


def _client_with_role(role: str | None = None):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    if role:
        with client.session_transaction(base_url="https://aipd.me") as sess:
            sess["user_id"] = 1
            sess["role"] = role
    return client


def test_public_articles_homepage_renders_wiki_explorer():
    client = _client_with_role()

    response = client.get("/articles", base_url="https://aipd.me")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-public-article-home' in body
    assert "文章知识库" in body
    assert "快速 Wiki" in body
    assert 'data-article-search' in body
    assert 'data-article-sort' in body
    assert 'data-filter-topic="all"' in body
    assert 'data-article-card' in body
    assert 'href="https://aipd.me/feed.xml"' in body
    assert 'href="https://aipd.me/articles.json"' in body
    assert 'href="https://aipd.me/llms.txt"' in body
    assert '"@type": "ItemList"' in body
    assert "PolaZhenjing 管理后台" not in body
    assert "+ 新建文章" not in body
    assert "同步到 GitHub" not in body


def test_non_admin_admin_articles_uses_public_homepage():
    client = _client_with_role("user")

    response = client.get("/admin/articles", base_url="https://aipd.me")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-public-article-home' in body
    assert "PolaUUH 用户中心" in body
    assert "设置" in body
    assert "PolaZhenjing 管理后台" not in body
    assert "文章管理" not in body
    assert "/admin/upload" not in body
    assert "+ 新建文章" not in body
    assert "同步到 GitHub" not in body


def test_admin_articles_keeps_management_list():
    client = _client_with_role("admin")

    response = client.get("/admin/articles", base_url="https://aipd.me")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "PolaZhenjing 管理后台" in body
    assert "文章管理" in body
    assert "+ 新建文章" in body
    assert "同步到 GitHub" in body
    assert 'data-public-article-home' not in body


def test_public_articles_honors_script_name_prefix():
    client = _client_with_role("user")

    response = client.get(
        "/admin/articles",
        base_url="https://aipd.me",
        headers={"X-Script-Name": "/PolaZhenjing"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-public-article-home' in body
    assert 'href="/PolaZhenjing/admin/account"' in body
    assert 'href="/PolaZhenjing/admin/upload"' not in body
