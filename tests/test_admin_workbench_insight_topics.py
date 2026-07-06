import html
import json
import time
from datetime import datetime, timedelta, timezone

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


def _textarea_value(body: str, element_id: str = "content") -> str:
    marker = f'id="{element_id}"'
    assert marker in body
    after_marker = body.split(marker, 1)[1]
    raw_value = after_marker.split(">", 1)[1].split("</textarea>", 1)[0]
    return html.unescape(raw_value)


def test_admin_workbench_shows_core_modules(monkeypatch, tmp_path):
    client, _ = _admin_client(monkeypatch, tmp_path)

    response = client.get("/admin/workbench")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Admin 工作台" in body
    assert "文章管理" in body
    assert "小王记忆管理" in body
    assert "洞察选题" in body
    assert "钉钉底料" not in body
    assert "公开线上信号" in body
    assert 'href="/admin/insights/topics"' in body


def test_insight_topics_list_and_status_update(monkeypatch, tmp_path):
    client, topics_file = _admin_client(monkeypatch, tmp_path)

    response = client.get("/admin/insights/topics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "内容生产 v2" in body
    assert "刷新线上选题" in body
    assert "AI 行业社媒运营选题" in body
    assert "PolaNews" in body
    assert "好的洞察文章不负责制造确定性" not in body
    topic_id = insight_topics.load_topics()[0]["id"]
    topic = insight_topics.load_topics()[0]
    assert topic["draft_word_count"] >= 4500
    assert "## 核心判断" in topic["draft_markdown"]
    assert topic["content_lane"] in insight_topics.CONTENT_LANES
    assert topic["content_lane_label"] in body
    assert f"底稿 {topic['draft_word_count']}" not in body
    assert f"来源：{topic['source_type']}" not in body
    assert f"评分 {topic['score']}" not in body
    assert topic["summary"] in body

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
    topic = insight_topics.load_topics()[0]
    topic_id = topic["id"]

    response = client.post(
        f"/admin/insights/topics/{topic_id}/import",
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "已导入洞察选题" in body
    assert 'value="markdown" checked' in body
    assert "Markdown 源码模式已就绪，导入内容可直接编辑。" in body
    textarea = _textarea_value(body)
    assert topic["summary"] in textarea
    assert insight_topics._draft_word_count(textarea) >= 5000
    assert insight_topics._draft_word_count(textarea) <= 30000
    assert "## 核心判断" in textarea
    assert "好的洞察文章不负责制造确定性" in textarea
    assert "## 洞察选题" not in textarea
    assert "## 写作角度" not in textarea
    assert "## 证据链接" not in textarea
    assert "状态：已导入" not in textarea
    assert "来源类型：" not in textarea
    assert "选题评分：" not in textarea
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
                    summary="来自 PolaNews 的 AI 工作流周期信号。",
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
    assert refreshed["draft_word_count"] >= 4500
    assert "## 核心判断" in refreshed["draft_markdown"]
    assert refreshed["content_lane"] in insight_topics.CONTENT_LANES
    assert refreshed["social_hook"]
    assert "来源信号" in body


def test_refresh_topic_import_prefills_long_article_draft(monkeypatch, tmp_path):
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
    textarea = _textarea_value(body)
    assert "HN 上关于 LLM workflow 的讨论升温。" in textarea
    assert insight_topics._draft_word_count(textarea) >= 5000
    assert insight_topics._draft_word_count(textarea) <= 30000
    assert "## 核心判断" in textarea
    assert "## 洞察选题" not in textarea
    assert "来源类型：Hacker News" not in textarea
    assert "## 证据链接" not in textarea
    assert "news.ycombinator.com/item?id=123" not in textarea


def test_signals_to_topics_generates_social_operation_blueprints_not_news_titles():
    raw_title = "New usage analytics and spend controls for enterprise AI teams"
    topics = insight_topics.signals_to_topics(
        [
            insight_topics.InsightSignal(
                source="openai_blog",
                title=raw_title,
                url="https://openai.com/index/usage-analytics-enterprise-ai",
                summary="OpenAI 更新企业 AI usage analytics、spend controls 和 API 管理能力。",
                published_at=datetime(2026, 7, 6, tzinfo=timezone.utc),
                score=72,
                tags=["openai", "enterprise-ai", "product", "api"],
            )
        ]
    )

    assert len(topics) == 1
    topic = topics[0]
    assert topic["title"] != raw_title
    assert topic["content_lane"] == "product_capability"
    assert topic["content_lane_label"] == "产品能力更新"
    assert topic["social_hook"]
    assert topic["target_audience"]
    assert topic["core_question"]
    assert len(topic["content_structure"]) >= 3
    assert topic["source_signal_title"] == raw_title
    assert "证据切口" in topic["source_role"]
    assert topic["draft_strategy_version"] == insight_topics.TOPIC_BLUEPRINT_VERSION
    assert "## 社媒运营蓝图" in topic["draft_markdown"]


def test_backfill_topics_for_date_range_fills_missing_days(monkeypatch, tmp_path):
    topics_file = tmp_path / "insight_topics.json"
    monkeypatch.setattr(insight_topics, "INSIGHT_TOPICS_FILE", topics_file)
    existing_topic = insight_topics._normalize_topic(
        {
            "date": "2026-06-20",
            "title": "已有的 6 月 20 日选题",
            "angle": "保留线上已有选题，不被历史回填覆盖。",
            "summary": "这条选题代表线上已经存在的运营数据。",
            "tags": ["existing"],
            "status": "selected",
            "source_url": "https://example.com/existing",
            "source_type": "manual",
        }
    )
    insight_topics.save_topics([existing_topic])

    result = insight_topics.backfill_topics_for_date_range("2026-06-18", "2026-06-20")
    payload = json.loads(topics_file.read_text(encoding="utf-8"))
    topics = payload["topics"]
    topics_by_date = {topic["date"]: topic for topic in topics}
    backfilled = [topic for topic in topics if topic["source_type"] == "manual_backfill"]

    assert result["added_count"] == 2
    assert result["added_dates"] == ["2026-06-18", "2026-06-19"]
    assert result["missing_days_after"] == []
    assert topics_by_date["2026-06-20"]["id"] == existing_topic["id"]
    assert topics_by_date["2026-06-20"]["status"] == "selected"
    assert len(backfilled) == 2
    assert {topic["date"] for topic in backfilled} == {"2026-06-18", "2026-06-19"}
    assert all(topic["draft_word_count"] >= 4500 for topic in backfilled)
    assert payload["last_backfill"]["added_count"] == 2
    assert payload["last_backfill"]["missing_days_after"] == []


def test_backfill_topics_for_date_range_dry_run_does_not_write(monkeypatch, tmp_path):
    topics_file = tmp_path / "insight_topics.json"
    monkeypatch.setattr(insight_topics, "INSIGHT_TOPICS_FILE", topics_file)
    insight_topics.save_topics([])

    result = insight_topics.backfill_topics_for_date_range(
        "2026-07-01",
        "2026-07-02",
        persist=False,
    )
    payload = json.loads(topics_file.read_text(encoding="utf-8"))

    assert result["added_count"] == 2
    assert result["persisted"] is False
    assert payload["topics"] == []
    assert "last_backfill" not in payload


def test_stale_topic_pool_triggers_background_refresh(monkeypatch, tmp_path):
    topics_file = tmp_path / "insight_topics.json"
    lock_file = tmp_path / "insight_topics_refresh.lock"
    monkeypatch.setattr(insight_topics, "INSIGHT_TOPICS_FILE", topics_file)
    monkeypatch.setattr(insight_topics, "AUTO_REFRESH_LOCK_FILE", lock_file)

    old_refresh = {
        "refreshed_at": (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(),
        "days": 10,
        "signal_count": 0,
        "topic_count": 0,
        "source_counts": {},
        "errors": [],
    }
    insight_topics.save_topics(insight_topics.load_topics(), metadata={"last_refresh": old_refresh})

    calls = []

    def fake_run(days):
        calls.append(days)
        insight_topics._release_auto_refresh_lock()

    monkeypatch.setattr(insight_topics, "_run_auto_refresh", fake_run)
    result = insight_topics.trigger_stale_refresh_in_background(days=10, max_age_hours=20)

    deadline = time.time() + 2
    while time.time() < deadline and not calls:
        time.sleep(0.01)

    assert result["status"] == "started"
    assert calls == [10]
    deadline = time.time() + 2
    while time.time() < deadline and lock_file.exists():
        time.sleep(0.01)
    assert not lock_file.exists()


def test_signals_to_topics_prefers_ai_application_and_practice_topics():
    topics = insight_topics.signals_to_topics(
        [
            insight_topics.InsightSignal(
                source="hackernews",
                title="Show HN: Bored People Chat - Anonymous global chat room",
                url="https://news.ycombinator.com/item?id=1",
                summary="HN 近期讨论：大量评论，主题是匿名聊天室。",
                published_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
                score=200,
                tags=["hackernews"],
            ),
            insight_topics.InsightSignal(
                source="github",
                title="AI agent workflow skill for enterprise support",
                url="https://github.com/example/agent-workflow-skill",
                summary="把 AI 智能体、业务工作流和客户支持场景串成可复用 skill 的最佳实践。",
                published_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
                score=40,
                tags=["ai-agent", "workflow", "skill", "enterprise-ai"],
            ),
        ]
    )

    assert len(topics) == 1
    assert topics[0]["source_url"] == "https://github.com/example/agent-workflow-skill"
    assert topics[0]["title"] != "AI agent workflow skill for enterprise support"
    assert topics[0]["content_lane"] in insight_topics.CONTENT_LANES
    assert topics[0]["social_hook"]
    assert topics[0]["focus_score"] >= 45
