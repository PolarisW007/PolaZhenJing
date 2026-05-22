from app.search_projection import build_memory_document, redact_projection_payload


def test_memory_projection_uses_reloadable_target_id():
    doc = build_memory_document({
        "id": "mem_1",
        "title": "回答风格",
        "content": "回答要直接、清晰。",
        "memory_type": "style",
        "subject_id": "owner",
        "namespace": "super_xiaowang",
        "status": "active",
        "trust_tier": "owner",
    })

    assert doc["id"] == "memory:mem_1"
    assert doc["target_id"] == "mem_1"
    assert doc["target_type"] == "memory_item"


def test_projection_redacts_sensitive_keys():
    payload = redact_projection_payload({
        "title": "ok",
        "api_key": "secret",
        "password_hash": "hash",
        "content": "visible",
    })

    assert payload == {"title": "ok", "content": "visible"}
