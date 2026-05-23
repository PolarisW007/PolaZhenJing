from app.release_awareness import format_release_awareness_context


def test_release_awareness_context_exposes_update_without_secrets():
    context = format_release_awareness_context({
        "commit": "abc1234",
        "branch": "main",
        "commit_subject": "feat: 增加小王更新感知",
        "commit_time": "2026-05-23T08:00:00+08:00",
        "release_doc": "docs/pola/release/example.md",
        "delivery_doc": "docs/requirement_delivery_logs/2026-05/example.md",
        "delivery_summary": ["交付日志：小王更新感知"],
        "release_summary": ["发布清单：版本状态 API"],
    })

    assert "abc1234" in context
    assert "增加小王更新感知" in context
    assert "只有当用户询问你是否更新" in context
    assert "DATABASE_URL" not in context
