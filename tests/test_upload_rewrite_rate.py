import json

from app import create_app
from app import uploader


def _admin_client():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"
    return client


def test_upload_page_shows_rewrite_rate_presets():
    client = _admin_client()
    response = client.get("/admin/upload")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert body.count('name="rewrite_rate"') == 15
    for value in ("0", "25", "50", "75", "100"):
        assert f'value="{value}"' in body
    assert "不改写，只插图" in body
    assert "完整改写" in body


def test_parse_rewrite_rate_normalizes_to_presets():
    assert uploader._parse_rewrite_rate("0") == 0
    assert uploader._parse_rewrite_rate("25") == 25
    assert uploader._parse_rewrite_rate("63") == 75
    assert uploader._parse_rewrite_rate("-5") == 0
    assert uploader._parse_rewrite_rate("bad") == 100


def test_upload_draft_persists_rewrite_rate(tmp_path, monkeypatch):
    monkeypatch.setattr(uploader, "DRAFT_DIR", str(tmp_path))
    client = _admin_client()

    response = client.post(
        "/admin/upload",
        data={
            "content_format": "markdown",
            "content": "# 原文标题\n\n这是原文正文，包含足够内容。",
            "title": "",
            "tags": "",
            "description": "",
            "media_strategy": "keep",
            "rewrite_rate": "25",
        },
    )

    assert response.status_code == 302
    drafts = list(tmp_path.glob("*.json"))
    assert len(drafts) == 1
    payload = json.loads(drafts[0].read_text(encoding="utf-8"))
    assert payload["rewrite_rate"] == 25


def _job_payload(tmp_path, rewrite_rate):
    return {
        "content": "原始正文第一段。\n\n原始正文第二段。",
        "title": "改写率测试文章",
        "tags": "ai",
        "description": "",
        "inserted_images": [],
        "revision_instruction": "保持事实不变",
        "rewrite_rate": rewrite_rate,
        "preserve_original_media": False,
        "original_media": [],
        "style": "deep-technical",
        "theme": "wukong",
        "project_root": str(tmp_path),
    }


def _patch_generate_side_effects(monkeypatch):
    calls = {"llm": 0, "images": 0}
    monkeypatch.setattr(uploader.jobs, "update_job", lambda *args, **kwargs: None)
    monkeypatch.setattr(uploader.jobs, "append_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(uploader, "_cleanup_draft_illustrations", lambda *args, **kwargs: None)

    def fake_images(title, content, slug, project_root):
        calls["images"] += 1
        return []

    def fake_commit(*args, **kwargs):
        class Result:
            pushed = False
        return Result()

    monkeypatch.setattr(uploader, "_generate_illustrations", fake_images)
    monkeypatch.setattr(uploader, "guarded_commit_and_push", fake_commit)
    return calls


def test_generate_job_rewrite_rate_zero_skips_llm_but_runs_images(tmp_path, monkeypatch):
    (tmp_path / "_posts").mkdir()
    calls = _patch_generate_side_effects(monkeypatch)

    def fail_llm(*args, **kwargs):
        calls["llm"] += 1
        raise AssertionError("0% rewrite must not call LLM")

    monkeypatch.setattr(uploader, "_call_llm_rewrite", fail_llm)

    uploader._run_generate_job("job-zero", _job_payload(tmp_path, 0))

    assert calls["llm"] == 0
    assert calls["images"] == 1
    post = next((tmp_path / "_posts").glob("*.md"))
    assert "原始正文第一段" in post.read_text(encoding="utf-8")


def test_generate_job_mid_rewrite_rate_calls_llm_with_rate(tmp_path, monkeypatch):
    (tmp_path / "_posts").mkdir()
    calls = _patch_generate_side_effects(monkeypatch)
    seen = {}

    def fake_llm(content, title, system_prompt, revision_instruction="", rewrite_rate=100):
        calls["llm"] += 1
        seen["rewrite_rate"] = rewrite_rate
        return "改写后的正文"

    monkeypatch.setattr(uploader, "_call_llm_rewrite", fake_llm)

    uploader._run_generate_job("job-mid", _job_payload(tmp_path, 50))

    assert calls["llm"] == 1
    assert seen["rewrite_rate"] == 50
    post = next((tmp_path / "_posts").glob("*.md"))
    assert "改写后的正文" in post.read_text(encoding="utf-8")


def test_call_llm_rewrite_prompt_contains_mid_rate_instruction(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "整理后的正文"}}]
            }).encode("utf-8")

    def fake_urlopen(req, timeout=0):
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(uploader, "_get_minimax_api_key", lambda: "test-key")
    monkeypatch.setattr(uploader, "urlopen", fake_urlopen)

    result = uploader._call_llm_rewrite(
        "原始正文",
        "测试标题",
        "系统提示",
        revision_instruction="更清晰",
        rewrite_rate=50,
    )

    assert result == "整理后的正文"
    user_msg = captured["payload"]["messages"][1]["content"]
    assert "AI改写率为50%" in user_msg
    assert "结构优化" in user_msg
    assert captured["payload"]["temperature"] == 0.5
