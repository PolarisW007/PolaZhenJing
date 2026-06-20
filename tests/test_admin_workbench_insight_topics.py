import json

from app import create_app
from app import insight_topics


def _admin_client(monkeypatch, tmp_path):
    topics_file = tmp_path / "insight_topics.json"
    monkeypatch.setattr(insight_topics, "INSIGHT_TOPICS_FILE", topics_file)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"
    return client, topics_file


def test_admin_workbench_shows_core_modules(monkeypatch, tmp_path):
    client, _ = _admin_client(monkeypatch, tmp_path)

    response = client.get("/admin/workbench")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Admin 工作台" in body
    assert "文章管理" in body
    assert "小王记忆管理" in body
    assert "洞察选题" in body
    assert "钉钉底料" in body
    assert "需要登录授权" in body
    assert 'href="/admin/insights/topics"' in body


def test_insight_topics_list_and_status_update(monkeypatch, tmp_path):
    client, topics_file = _admin_client(monkeypatch, tmp_path)

    response = client.get("/admin/insights/topics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "内容生产 v2" in body
    assert "钉钉底料需要登录授权" in body
    topic_id = insight_topics.load_topics()[0]["id"]

    status_response = client.post(
        f"/admin/insights/topics/{topic_id}/status",
        data={"status": "selected"},
        follow_redirects=True,
    )
    assert status_response.status_code == 200
    payload = json.loads(topics_file.read_text(encoding="utf-8"))
    updated = next(topic for topic in payload["topics"] if topic["id"] == topic_id)
    assert updated["status"] == "selected"


def test_import_topic_prefills_upload_markdown(monkeypatch, tmp_path):
    client, topics_file = _admin_client(monkeypatch, tmp_path)
    topic_id = insight_topics.load_topics()[0]["id"]

    response = client.post(
        f"/admin/insights/topics/{topic_id}/import",
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "已导入洞察选题" in body
    assert 'value="markdown" checked' in body
    assert "## 洞察选题" in body
    assert "## 写作角度" in body
    assert "状态：已导入" in body
    assert "content-production" in body
    payload = json.loads(topics_file.read_text(encoding="utf-8"))
    imported = next(topic for topic in payload["topics"] if topic["id"] == topic_id)
    assert imported["status"] == "imported"


def test_non_admin_workbench_redirects_to_account(monkeypatch, tmp_path):
    monkeypatch.setattr(insight_topics, "INSIGHT_TOPICS_FILE", tmp_path / "topics.json")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["role"] = "user"

    response = client.get("/admin/workbench")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/account")
