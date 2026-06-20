"""Insight topic storage and upload prefill helpers."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSIGHT_TOPICS_FILE = PROJECT_ROOT / "data" / "insight_topics.json"
ALIDOCS_SOURCE_URL = (
    "https://alidocs.dingtalk.com/i/nodes/"
    "y20BglGWO2LKQjdrtgBEGo1L8A7depqY?utm_scene=person_space"
)

TOPIC_STATUSES = {
    "new": "待处理",
    "selected": "已选中",
    "imported": "已导入",
    "archived": "已归档",
}

DEFAULT_TOPICS = [
    {
        "date": "2026-06-20",
        "title": "内容生产 v2：从上传工具走向作者型写作系统",
        "angle": "把实时信号、作者风格、去 AI 味审稿串成一条内容生产流水线。",
        "summary": (
            "PolaZhenJing 已经具备上传、改写、配图、发布能力，下一步重点是让系统先完成"
            "选题洞察、证据整理和作者腔调校验，再进入文章生成。"
        ),
        "tags": ["content-production", "author-workflow", "insight"],
        "status": "new",
        "source_url": ALIDOCS_SOURCE_URL,
    },
    {
        "date": "2026-06-20",
        "title": "去 AI 味不是检测器，而是编辑工作流",
        "angle": "检测器只能提示风险，真正有效的是证据、判断、场景和删改机制。",
        "summary": (
            "围绕中文套话、模板结构、证据缺口和第一人称判断建立审稿报告，减少文章的模型味。"
        ),
        "tags": ["humanizer", "editorial-review", "writing"],
        "status": "new",
        "source_url": ALIDOCS_SOURCE_URL,
    },
    {
        "date": "2026-06-20",
        "title": "实时趋势研究如何进入每日选题",
        "angle": "把 X、GitHub、行业文章等信号归一化为 clusters、controversies 和 links。",
        "summary": (
            "选题不只来自灵感，也来自可追溯的近期信号；缺失来源必须显式标注，避免伪研究。"
        ),
        "tags": ["trend-research", "signals", "daily-topics"],
        "status": "new",
        "source_url": ALIDOCS_SOURCE_URL,
    },
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _topic_id(topic: dict) -> str:
    raw = f"{topic.get('date', '')}|{topic.get('title', '')}|{topic.get('angle', '')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _normalize_topic(topic: dict) -> dict:
    item = dict(topic)
    item["id"] = str(item.get("id") or _topic_id(item))
    item["date"] = str(item.get("date") or datetime.now().date().isoformat())
    item["title"] = str(item.get("title") or "未命名选题").strip()
    item["angle"] = str(item.get("angle") or "").strip()
    item["summary"] = str(item.get("summary") or "").strip()
    tags = item.get("tags") or []
    if isinstance(tags, str):
        tags = [part.strip() for part in tags.split(",") if part.strip()]
    item["tags"] = [str(tag).strip() for tag in tags if str(tag).strip()]
    item["status"] = item.get("status") if item.get("status") in TOPIC_STATUSES else "new"
    item["source_url"] = str(item.get("source_url") or ALIDOCS_SOURCE_URL).strip()
    item["created_at"] = str(item.get("created_at") or _now())
    item["updated_at"] = str(item.get("updated_at") or item["created_at"])
    return item


def _seed_topics() -> list[dict]:
    return [_normalize_topic(topic) for topic in deepcopy(DEFAULT_TOPICS)]


def load_topics() -> list[dict]:
    """Load topics, seeding a default list when no data file exists."""
    if not INSIGHT_TOPICS_FILE.is_file():
        topics = _seed_topics()
        save_topics(topics)
        return topics
    try:
        raw = json.loads(INSIGHT_TOPICS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _seed_topics()
    if isinstance(raw, dict):
        raw_topics = raw.get("topics") or []
    elif isinstance(raw, list):
        raw_topics = raw
    else:
        raw_topics = []
    topics = [_normalize_topic(topic) for topic in raw_topics if isinstance(topic, dict)]
    return sorted(topics, key=lambda item: (item.get("date", ""), item.get("updated_at", "")), reverse=True)


def save_topics(topics: list[dict]) -> None:
    normalized = [_normalize_topic(topic) for topic in topics]
    INSIGHT_TOPICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_url": ALIDOCS_SOURCE_URL,
        "updated_at": _now(),
        "topics": normalized,
    }
    tmp_path = INSIGHT_TOPICS_FILE.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, INSIGHT_TOPICS_FILE)


def get_topic(topic_id: str) -> dict | None:
    for topic in load_topics():
        if topic.get("id") == topic_id:
            return topic
    return None


def update_topic_status(topic_id: str, status: str) -> dict:
    if status not in TOPIC_STATUSES:
        raise ValueError("未知选题状态。")
    topics = load_topics()
    for topic in topics:
        if topic.get("id") == topic_id:
            topic["status"] = status
            topic["updated_at"] = _now()
            save_topics(topics)
            return topic
    raise KeyError("选题不存在。")


def mark_topic_imported(topic_id: str) -> dict:
    return update_topic_status(topic_id, "imported")


def topic_counts(topics: list[dict] | None = None) -> dict:
    topics = topics if topics is not None else load_topics()
    counts = {status: 0 for status in TOPIC_STATUSES}
    for topic in topics:
        status = topic.get("status") if topic.get("status") in TOPIC_STATUSES else "new"
        counts[status] = counts.get(status, 0) + 1
    counts["total"] = len(topics)
    return counts


def build_upload_prefill(topic: dict) -> dict:
    """Build markdown prefill payload for the upload page."""
    tags = topic.get("tags") or []
    source_url = topic.get("source_url") or ALIDOCS_SOURCE_URL
    title = topic.get("title") or "洞察选题"
    summary = topic.get("summary") or ""
    angle = topic.get("angle") or ""
    markdown = "\n\n".join(
        part for part in [
            f"# {title}",
            "## 洞察选题",
            f"- 日期：{topic.get('date', '')}",
            f"- 状态：{TOPIC_STATUSES.get(topic.get('status'), topic.get('status', '待处理'))}",
            f"- 标签：{', '.join(tags) if tags else '待补充'}",
            f"- 来源：{source_url}",
            "## 写作角度\n" + (angle or "请补充这篇文章最值得展开的判断角度。"),
            "## 关键摘要\n" + (summary or "请补充选题背后的事实、信号和可写切口。"),
            "## 待展开问题\n- 这个趋势为什么现在发生？\n- 对创业者、产品经理或工程团队有什么直接影响？\n- 哪些证据、案例或反例能支撑这个判断？",
        ] if part
    )
    return {
        "topic_id": topic.get("id", ""),
        "title": title,
        "tags": ", ".join(tags),
        "description": summary[:160],
        "content": markdown,
        "source_url": source_url,
    }
