from app.memory_store import sanitize_pg_value


def test_sanitize_pg_value_removes_nul_bytes_recursively():
    payload = {
        "content": "hello\x00world",
        "risk_flags": {"bad\x00key": ["x\x00y", {"nested": "z\x00"}]},
        "tuple_value": ("a\x00",),
    }

    assert sanitize_pg_value(payload) == {
        "content": "helloworld",
        "risk_flags": {"badkey": ["xy", {"nested": "z"}]},
        "tuple_value": ["a"],
    }
