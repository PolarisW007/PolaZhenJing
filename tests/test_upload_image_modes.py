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


def _long_paragraph(index):
    return (
        f"第{index}段讨论人工智能产品如何从真实用户问题出发，"
        "先识别约束和证据，再通过小步验证形成可复用的方法。"
        "这一段包含足够具体的角色、工具、场景与冲突，可以独立转成视觉画面。"
    )


def _article_with_paragraphs(count=6):
    return "# 测试文章\n\n" + "\n\n".join(
        _long_paragraph(index) for index in range(1, count + 1)
    )


def test_upload_page_shows_four_image_modes_in_all_three_forms():
    response = _admin_client().get("/admin/upload")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert body.count('name="image_generation_mode"') == 12
    for value in ("cover", "summary", "standard", "detailed"):
        assert body.count(f'value="{value}"') == 3
    assert body.count('value="standard" checked') == 3
    assert "只生成题图" in body
    assert "3 张 · 题图 + 全文概括" in body
    assert "5 张 · 题图 + 核心观点" in body
    assert "逐段配图 · 最多 12 段" in body


def test_parse_image_generation_mode_uses_safe_default():
    for value in ("cover", "summary", "standard", "detailed"):
        assert uploader._parse_image_generation_mode(value) == value
    assert uploader._parse_image_generation_mode("unknown") == "standard"
    assert uploader._parse_image_generation_mode(None) == "standard"


def test_upload_draft_persists_image_generation_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(uploader, "DRAFT_DIR", str(tmp_path))
    client = _admin_client()

    response = client.post(
        "/admin/upload",
        data={
            "content_format": "markdown",
            "content": "# 原文标题\n\n这是用于测试详细生图模式的正文内容。",
            "media_strategy": "keep",
            "rewrite_rate": "100",
            "image_generation_mode": "detailed",
        },
    )

    assert response.status_code == 302
    draft = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert draft["image_generation_mode"] == "detailed"


def test_generate_route_passes_image_mode_from_draft(tmp_path, monkeypatch):
    monkeypatch.setattr(uploader, "DRAFT_DIR", str(tmp_path))
    captured = {}
    client = _admin_client()
    draft_id = uploader._save_draft(
        "正文内容",
        "模式传递测试",
        "ai",
        "",
        image_generation_mode="summary",
    )
    with client.session_transaction() as sess:
        sess["draft_id"] = draft_id

    monkeypatch.setattr(uploader.jobs, "create_job", lambda **kwargs: "mode-job")

    def fake_submit(target, job_id, payload):
        captured["target"] = target
        captured["job_id"] = job_id
        captured["payload"] = payload

    monkeypatch.setattr(uploader.jobs, "submit", fake_submit)
    response = client.post("/admin/generate", data={"style": "deep-technical"})

    assert response.status_code == 302
    assert captured["target"] is uploader._run_generate_job
    assert captured["job_id"] == "mode-job"
    assert captured["payload"]["image_generation_mode"] == "summary"


def test_fixed_image_modes_generate_exact_total_counts(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(uploader, "_call_visual_brief_llm", lambda *args, **kwargs: None)

    def fake_t2i(prompt, aspect_ratio="16:9", request_timeout=180):
        calls.append((aspect_ratio, request_timeout))
        return b"fake-png"

    monkeypatch.setattr(uploader, "_call_minimax_t2i", fake_t2i)
    content = _article_with_paragraphs(7)

    for mode, expected in (("cover", 1), ("summary", 3), ("standard", 5)):
        calls.clear()
        images = uploader._generate_illustrations(
            "精确数量测试", content, f"mode-{mode}", str(tmp_path), mode
        )
        assert len(calls) == expected
        assert len(images) == expected
        assert images[0]["role"] == "cover"
        assert len([item for item in images if item["role"] == "scene"]) == expected - 1


def test_visual_llm_cannot_expand_scene_count_or_change_anchors(tmp_path, monkeypatch):
    content = _article_with_paragraphs(6)
    expected_blocks = uploader._visual_blocks_for_image_mode(content, "summary")
    oversized_plan = {
        "cover": {"alt": "题图", "prompt": "题图提示"},
        "scenes": [
            {"block_index": 999, "alt": f"场景{index}", "prompt": f"场景提示{index}"}
            for index in range(10)
        ],
    }
    monkeypatch.setattr(
        uploader, "_call_visual_brief_llm", lambda *args, **kwargs: oversized_plan
    )
    monkeypatch.setattr(
        uploader,
        "_call_minimax_t2i",
        lambda *args, **kwargs: b"fake-png",
    )

    images = uploader._generate_illustrations(
        "后端数量约束", content, "forced-count", str(tmp_path), "summary"
    )

    scenes = [item for item in images if item["role"] == "scene"]
    assert len(images) == 3
    assert [item["block_index"] for item in scenes] == [
        item["block_index"] for item in expected_blocks
    ]


def test_detailed_mode_uses_prose_paragraphs_and_skips_non_prose(tmp_path, monkeypatch):
    content = "\n\n".join(
        [
            "# 详细模式测试",
            _long_paragraph(1),
            "```python\nprint('code block')\n```",
            _long_paragraph(2),
            "![已有图片](/assets/images/existing.png)",
            "- 导航一\n- 导航二\n- 导航三",
            _long_paragraph(3),
            "作者：测试作者，欢迎点赞、在看和转发。",
        ]
    )
    monkeypatch.setattr(uploader, "_call_visual_brief_llm", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        uploader,
        "_call_minimax_t2i",
        lambda *args, **kwargs: b"fake-png",
    )

    blocks = uploader._extract_detailed_visual_blocks(content)
    images = uploader._generate_illustrations(
        "逐段测试", content, "detailed-prose", str(tmp_path), "detailed"
    )

    assert len(blocks) == 3
    assert len(images) == 4
    assert [item["block_index"] for item in images[1:]] == [
        item["block_index"] for item in blocks
    ]


def test_detailed_mode_is_capped_and_spread_across_article():
    content = _article_with_paragraphs(20)
    blocks = uploader._extract_detailed_visual_blocks(content)

    assert len(blocks) == uploader.DETAILED_IMAGE_MAX_SCENES == 12
    assert blocks[0]["block_index"] == 1
    assert blocks[-1]["block_index"] == 20
    assert len({item["block_index"] for item in blocks}) == 12


def test_image_batch_budget_stops_before_new_api_calls(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(uploader, "IMAGE_GENERATION_BATCH_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(uploader, "_call_visual_brief_llm", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        uploader,
        "_call_minimax_t2i",
        lambda *args, **kwargs: calls.append(args) or b"fake-png",
    )

    images = uploader._generate_illustrations(
        "超时预算测试",
        _article_with_paragraphs(4),
        "budget-stop",
        str(tmp_path),
        "standard",
    )

    assert images == []
    assert calls == []


def test_image_batch_byte_budget_stops_before_writing_oversized_batch(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(uploader, "MAX_GENERATED_IMAGE_BATCH_BYTES", 5)
    monkeypatch.setattr(uploader, "_call_visual_brief_llm", lambda *args, **kwargs: None)

    def fake_t2i(*args, **kwargs):
        calls.append(kwargs.get("request_timeout"))
        return b"1234"

    monkeypatch.setattr(uploader, "_call_minimax_t2i", fake_t2i)
    images = uploader._generate_illustrations(
        "批次容量测试",
        _article_with_paragraphs(4),
        "byte-budget",
        str(tmp_path),
        "summary",
    )

    assert len(calls) == 2
    assert len(images) == 1


def test_cover_does_not_shift_original_scene_anchor():
    content = "# 标题\n\n这是应该先完整出现的正文段落，插图需要放在这一段之后。"
    images = [
        {
            "role": "cover",
            "relpath": "assets/images/generated/demo/cover.png",
            "alt": "题图",
            "block_index": None,
        },
        {
            "role": "scene",
            "relpath": "assets/images/generated/demo/scene-1.png",
            "alt": "段落图",
            "block_index": 1,
        },
    ]

    rendered = uploader._inject_illustrations(content, images)

    assert rendered.index("这是应该先完整出现的正文段落") < rendered.index("scene-1.png")


def test_generate_job_reports_selected_mode_and_partial_count(tmp_path, monkeypatch):
    (tmp_path / "_posts").mkdir()
    updates = []
    messages = []
    monkeypatch.setattr(
        uploader.jobs, "update_job", lambda job_id, **fields: updates.append(fields)
    )
    monkeypatch.setattr(
        uploader.jobs,
        "append_message",
        lambda job_id, level, message: messages.append((level, message)),
    )
    monkeypatch.setattr(uploader, "_cleanup_draft_illustrations", lambda *args: None)
    monkeypatch.setattr(uploader, "_call_llm_rewrite", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        uploader,
        "_generate_illustrations",
        lambda *args, **kwargs: [{
            "role": "cover",
            "relpath": "assets/images/generated/mode/cover.png",
            "alt": "题图",
            "block_index": None,
        }],
    )

    class DeployResult:
        pushed = False

    monkeypatch.setattr(uploader, "guarded_commit_and_push", lambda *args, **kwargs: DeployResult())
    payload = {
        "content": _article_with_paragraphs(4),
        "title": "任务消息测试",
        "tags": "ai",
        "description": "",
        "inserted_images": [],
        "revision_instruction": "",
        "rewrite_rate": 0,
        "image_generation_mode": "summary",
        "preserve_original_media": False,
        "original_media": [],
        "style": "deep-technical",
        "theme": "wukong",
        "project_root": str(tmp_path),
    }

    uploader._run_generate_job("mode-message", payload)

    assert any("概括" in update.get("stage", "") and "计划 3 张" in update.get("stage", "") for update in updates)
    assert ("warning", "「概括」模式计划 3 张，实际生成 1 张吉卜力风格插画。") in messages
    assert len(list((tmp_path / "_posts").glob("*.md"))) == 1
