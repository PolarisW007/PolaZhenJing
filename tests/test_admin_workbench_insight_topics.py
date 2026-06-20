import json
from datetime import datetime, timezone

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
    assert "公开线上信号" in body
    assert 'href="/admin/insights/topics"' in body


def test_insight_topics_list_and_status_update(monkeypatch, tmp_path):
    client, topics_file = _admin_client(monkeypatch, tmp_path)

    response = client.get("/admin/insights/topics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "内容生产 v2" in body
    assert "刷新线上选题" in body
    assert "PolaNews" in body
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
    assert "## 证据链接" in body
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


def test_refresh_topics_from_online_signals_preserves_status(monkeypatch, tmp_path):
    client, topics_file = _admin_client(monkeypatch, tmp_path)
    topic = insight_topics.load_topics()[0]
    client.post(f"/admin/insights/topics/{topic['id']}/status", data={"status": "selected"})

    def fake_collect_topic_signals(days):
        assert days == 7
        return (
            [
                insight_topics.InsightSignal(
                    source="polanews",
                    title=topic["title"],
                    url=topic["source_url"],
                    summary="来自 PolaNews 的周期信号。",
                    published_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
                    score=88,
                    tags=["ai", "trend"],
                ),
                insight_topics.InsightSignal(
                    source="github",
                    title="open-source agent framework is moving fast",
                    url="https://github.com/example/agent-framework",
                    summary="GitHub 上的 agent framework 近期活跃。",
                    published_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
                    score=75,
                    tags=["github", "ai-agent"],
                ),
            ],
            {"polanews": 1, "github": 1},
            [],
        )

    monkeypatch.setattr(insight_topics, "collect_topic_signals", fake_collect_topic_signals)
    response = client.post("/admin/insights/topics/refresh", data={"days": "7"}, follow_redirects=True)
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "已从线上信号刷新" in body
    assert "open-source agent framework" in body
    payload = json.loads(topics_file.read_text(encoding="utf-8"))
    assert payload["last_refresh"]["source_counts"]["polanews"] == 1
    refreshed = next(item for item in payload["topics"] if item["id"] == topic["id"])
    assert refreshed["status"] == "selected"
    assert refreshed["source_type"] == "polanews"
    assert refreshed["evidence_links"][0]["url"] == topic["source_url"]


def test_refresh_topic_import_includes_evidence_links(monkeypatch, tmp_path):
    client, _ = _admin_client(monkeypatch, tmp_path)

    def fake_collect_topic_signals(days):
        return (
            [
                insight_topics.InsightSignal(
                    source="hackernews",
                    title="Show HN: a useful LLM workflow",
                    url="https://news.ycombinator.com/item?id=123",
                    summary="HN 上关于 LLM workflow 的讨论升温。",
                    published_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
                    score=66,
                    tags=["llm", "workflow"],
                )
            ],
            {"hackernews": 1},
            [],
        )

    monkeypatch.setattr(insight_topics, "collect_topic_signals", fake_collect_topic_signals)
    client.post("/admin/insights/topics/refresh", data={"days": "7"})
    generated = next(topic for topic in insight_topics.load_topics() if topic["source_type"] == "hackernews")

    response = client.post(
        f"/admin/insights/topics/{generated['id']}/import",
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "来源类型：Hacker News" in body
    assert "## 证据链接" in body
    assert "news.ycombinator.com/item?id=123" in body
