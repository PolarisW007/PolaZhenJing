"""Admin workbench and insight topic routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .auth import login_required
from .insight_topics import (
    ALIDOCS_SOURCE_URL,
    TOPIC_STATUSES,
    build_upload_prefill,
    get_topic,
    load_topics,
    mark_topic_imported,
    topic_counts,
    update_topic_status,
)

admin_workbench_bp = Blueprint("admin_workbench", __name__, url_prefix="/admin")


def _is_admin() -> bool:
    return session.get("role") == "admin"


def _require_admin_redirect():
    if _is_admin():
        return None
    return redirect(url_for("auth.account"))


def _workbench_stats() -> dict:
    stats = {
        "articles": 0,
        "skills": 0,
        "memory_items": 0,
        "topics": 0,
        "topics_new": 0,
    }
    try:
        from .uploader import _scan_posts

        stats["articles"] = len(_scan_posts())
    except Exception:
        pass
    try:
        from .skillhub import _all_skills

        stats["skills"] = len(_all_skills())
    except Exception:
        pass
    try:
        from .memory_service import memory_status

        memory = memory_status()
        stats["memory_items"] = int((memory.get("stats") or {}).get("total") or 0)
    except Exception:
        pass
    topics = load_topics()
    counts = topic_counts(topics)
    stats["topics"] = counts.get("total", 0)
    stats["topics_new"] = counts.get("new", 0)
    return stats


@admin_workbench_bp.route("/workbench")
@login_required
def workbench():
    blocked = _require_admin_redirect()
    if blocked:
        return blocked
    topics = load_topics()
    return render_template(
        "admin_workbench.html",
        stats=_workbench_stats(),
        topics=topics[:5],
        topic_counts=topic_counts(topics),
        topic_statuses=TOPIC_STATUSES,
        alidocs_source_url=ALIDOCS_SOURCE_URL,
    )


@admin_workbench_bp.route("/insights/topics")
@login_required
def insight_topics():
    blocked = _require_admin_redirect()
    if blocked:
        return blocked
    status = request.args.get("status", "").strip()
    topics = load_topics()
    if status in TOPIC_STATUSES:
        topics = [topic for topic in topics if topic.get("status") == status]
    all_topics = load_topics()
    return render_template(
        "insight_topics.html",
        topics=topics,
        topic_counts=topic_counts(all_topics),
        topic_statuses=TOPIC_STATUSES,
        selected_status=status,
        alidocs_source_url=ALIDOCS_SOURCE_URL,
    )


@admin_workbench_bp.route("/insights/topics/<topic_id>/status", methods=["POST"])
@login_required
def update_insight_topic_status(topic_id: str):
    blocked = _require_admin_redirect()
    if blocked:
        return blocked
    status = request.form.get("status", "").strip()
    try:
        update_topic_status(topic_id, status)
        flash("选题状态已更新。", "success")
    except (KeyError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("admin_workbench.insight_topics"))


@admin_workbench_bp.route("/insights/topics/<topic_id>/import", methods=["POST"])
@login_required
def import_insight_topic(topic_id: str):
    blocked = _require_admin_redirect()
    if blocked:
        return blocked
    topic = get_topic(topic_id)
    if not topic:
        flash("选题不存在。", "error")
        return redirect(url_for("admin_workbench.insight_topics"))
    topic = mark_topic_imported(topic_id)
    prefill = build_upload_prefill(topic)
    flash("已导入洞察选题，上传页已预填 Markdown 草稿。", "success")
    return redirect(url_for("uploader.upload", insight_topic=prefill["topic_id"]))
