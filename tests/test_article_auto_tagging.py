from pathlib import Path

from app import create_app
from app import uploader
from app.uploader import (
    POSTS_DIR,
    _article_keywords,
    _auto_article_tags,
)


def test_auto_article_tags_classifies_agent_and_codex():
    tags = _auto_article_tags(
        "Codex App 作为 AI Agent 产品",
        "Claude Code、Codex、Agent Harness、工具调用和工作流正在改变开发者工具。",
    )

    assert tags[0] in {"agent-systems", "coding-tools"}
    assert "codex" in tags
    assert "ai" in tags


def test_auto_article_tags_classifies_data_infrastructure():
    tags = _auto_article_tags(
        "谈到 FDE, 浅析下 DataBricks 和 Snowflake",
        "Databricks、Snowflake、Palantir 和数据基础设施正在重塑企业数据平台。",
    )

    assert tags[0] == "data-infrastructure"
    assert "databricks" in tags
    assert "snowflake" in tags


def test_auto_article_tags_preserves_user_tags_normalized():
    tags = _auto_article_tags(
        "Any title",
        "Any body",
        "AI Engineering, Claude_Code, deep-technical, Agent Systems",
    )

    assert tags == ["ai-engineering", "claude-code", "agent-systems"]


def test_upload_generates_tags_when_user_leaves_tags_blank(tmp_path, monkeypatch):
    monkeypatch.setattr(uploader, "DRAFT_DIR", str(tmp_path))
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    response = client.post(
        "/admin/upload",
        data={
            "content_format": "markdown",
            "content": "# Codex Agent Harness\n\nCodex 和 Claude Code 通过工具调用、上下文工程和工作流帮助开发者。",
            "title": "",
            "tags": "",
            "description": "",
            "media_strategy": "keep",
        },
    )

    assert response.status_code == 302
    drafts = list(tmp_path.glob("*.json"))
    assert len(drafts) == 1
    data = drafts[0].read_text(encoding="utf-8")
    assert "agent-systems" in data or "coding-tools" in data
    assert "codex" in data


def test_upload_keeps_user_tags_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(uploader, "DRAFT_DIR", str(tmp_path))
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    response = client.post(
        "/admin/upload",
        data={
            "content_format": "markdown",
            "content": "# 自定义标签文章\n\n正文内容。",
            "title": "",
            "tags": "Product Design, Claude",
            "description": "",
            "media_strategy": "keep",
        },
    )

    assert response.status_code == 302
    data = list(tmp_path.glob("*.json"))[0].read_text(encoding="utf-8")
    assert "product-design, claude" in data


def test_local_posts_have_business_primary_tags_after_batch_tagging():
    primary_tags = set(uploader.ARTICLE_PRIMARY_TAGS)
    posts = sorted(Path(POSTS_DIR).glob("*.md"))
    assert posts
    for path in posts:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        front = raw.split("---", 2)[1] if raw.startswith("---") else ""
        tags_line = ""
        for line in front.splitlines():
            if line.startswith("tags:"):
                tags_line = line.split(":", 1)[1].strip()
                break
        tags = _article_keywords(tags_line)
        assert tags, path.name
        assert tags[0] in primary_tags, (path.name, tags)
