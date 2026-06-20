"""Insight topic storage and upload prefill helpers."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests

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

ALLOWED_REFRESH_DAYS = (1, 3, 7, 14, 30)
DEFAULT_REFRESH_DAYS = 7
MAX_SIGNALS_PER_SOURCE = 60
MAX_GENERATED_TOPICS = 24
REQUEST_TIMEOUT = 8

POLANEWS_ARTICLES_URL = os.getenv(
    "POLANEWS_ARTICLES_URL",
    "https://aipd.me/polanews/api/articles",
)
POLANEWS_SEARCH_QUERIES = ("AI", "人工智能", "大模型", "智能体", "OpenAI", "Claude", "Agent")
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
RSS_SOURCES = [
    {
        "source": "openai_blog",
        "feed_url": "https://openai.com/news/rss.xml",
        "label": "OpenAI",
        "tags": ["ai-lab", "openai"],
    },
    {
        "source": "anthropic_news",
        "feed_url": "https://www.anthropic.com/news/rss.xml",
        "label": "Anthropic",
        "tags": ["ai-lab", "anthropic"],
    },
    {
        "source": "huggingface_blog",
        "feed_url": "https://huggingface.co/blog/feed.xml",
        "label": "Hugging Face",
        "tags": ["open-source", "models"],
    },
    {
        "source": "google_ai_blog",
        "feed_url": "https://blog.google/technology/ai/rss/",
        "label": "Google AI",
        "tags": ["ai-lab", "google"],
    },
]

SOURCE_LABELS = {
    "polanews": "PolaNews",
    "hackernews": "Hacker News",
    "github": "GitHub",
    "openai_blog": "OpenAI",
    "anthropic_news": "Anthropic",
    "huggingface_blog": "Hugging Face",
    "google_ai_blog": "Google AI",
    "mixed": "多源聚合",
    "manual_seed": "本地种子",
    "manual": "人工维护",
}

KEYWORD_TAGS = {
    "agent": "ai-agent",
    "agents": "ai-agent",
    "llm": "llm",
    "openai": "openai",
    "anthropic": "anthropic",
    "claude": "claude",
    "coding": "ai-coding",
    "cursor": "ai-coding",
    "github": "developer-tool",
    "developer": "developer-tool",
    "model": "model",
    "models": "model",
    "multimodal": "multimodal",
    "robot": "robotics",
    "robotics": "robotics",
    "enterprise": "enterprise-ai",
    "安全": "ai-safety",
    "模型": "model",
    "智能体": "ai-agent",
    "开源": "open-source",
    "视频": "multimodal",
    "企业": "enterprise-ai",
}

RELEVANCE_TERMS = (
    "ai",
    "llm",
    "agent",
    "agents",
    "openai",
    "anthropic",
    "claude",
    "cursor",
    "gpt",
    "model",
    "mcp",
    "coding",
    "developer",
    "robot",
    "人工智能",
    "模型",
    "智能体",
    "大模型",
    "开源",
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "PolaZhenJingTopicCrawler/1.0 "
        "(https://aipd.me/PolaZhenjing; contact: admin@aipd.me)"
    )
}


@dataclass
class InsightSignal:
    source: str
    title: str
    url: str
    summary: str = ""
    published_at: datetime | None = None
    score: float = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> str:
    return datetime.now().date().isoformat()


def _topic_id(topic: dict) -> str:
    raw = f"{topic.get('date', '')}|{topic.get('title', '')}|{topic.get('angle', '')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _topic_sort_key(item: dict) -> tuple[str, int, str]:
    return (
        str(item.get("date", "")),
        int(item.get("score") or 0),
        str(item.get("updated_at", "")),
    )


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate(text: str, limit: int) -> str:
    text = _clean_text(text)
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 0)].rstrip() + "…"


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    formats = (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _within_days(value: datetime | None, days: int) -> bool:
    if not value:
        return True
    if not value.tzinfo:
        value = value.replace(tzinfo=timezone.utc)
    return value >= _utc_now() - timedelta(days=days)


def _source_host(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _normalize_tags(tags: Any) -> list[str]:
    if isinstance(tags, str):
        tags = re.split(r"[,，\s]+", tags)
    if not isinstance(tags, list):
        return []
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in tags:
        tag = _clean_text(raw).lower().strip("#")
        if tag and tag not in seen:
            seen.add(tag)
            normalized.append(tag)
    return normalized[:8]


def _keyword_tags(*parts: str) -> list[str]:
    haystack = " ".join(part or "" for part in parts).lower()
    tags = [tag for keyword, tag in KEYWORD_TAGS.items() if keyword in haystack]
    if _contains_ai_token(haystack) or "人工智能" in haystack:
        tags.insert(0, "ai")
    return _normalize_tags(tags)


def _importance_score(value: Any) -> float:
    if value is None:
        return 1
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    mapping = {
        "low": 0.5,
        "normal": 1,
        "medium": 1.5,
        "high": 2.5,
        "critical": 3.5,
    }
    if text in mapping:
        return mapping[text]
    try:
        return float(text)
    except ValueError:
        return 1


def _contains_ai_token(text: str) -> bool:
    return bool(re.search(r"(^|[^a-z0-9])ai([^a-z0-9]|$)", text.lower()))


def _is_relevant_signal(*parts: str) -> bool:
    haystack = " ".join(part or "" for part in parts).lower()
    for term in RELEVANCE_TERMS:
        if term == "ai":
            if _contains_ai_token(haystack):
                return True
            continue
        if term in haystack:
            return True
    return False


def _cluster_key(title: str, tags: list[str]) -> str:
    words = [
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}|[\u4e00-\u9fff]{2,}", title.lower())
        if word not in {"the", "and", "with", "from", "this", "that", "about", "using"}
    ]
    seed = "|".join((tags[:3] or words[:5] or [_clean_text(title).lower()])[:5])
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]


def _evidence_link(signal: InsightSignal) -> dict:
    return {
        "title": _truncate(signal.title, 96),
        "url": signal.url,
        "source": SOURCE_LABELS.get(signal.source, signal.source),
    }


def _request_json(url: str, params: dict | None = None) -> dict:
    response = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _request_text(url: str) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _load_payload() -> dict:
    if not INSIGHT_TOPICS_FILE.is_file():
        return {
            "source_url": ALIDOCS_SOURCE_URL,
            "updated_at": _now(),
            "topics": _seed_topics(),
        }
    try:
        raw = json.loads(INSIGHT_TOPICS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "source_url": ALIDOCS_SOURCE_URL,
            "updated_at": _now(),
            "topics": _seed_topics(),
        }
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {
            "source_url": ALIDOCS_SOURCE_URL,
            "updated_at": _now(),
            "topics": raw,
        }
    return {
        "source_url": ALIDOCS_SOURCE_URL,
        "updated_at": _now(),
        "topics": [],
    }


def _normalize_evidence_links(value: Any, fallback_url: str = "") -> list[dict]:
    links: list[dict] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                url = str(item.get("url") or "").strip()
                title = _clean_text(item.get("title") or url)
                source = _clean_text(item.get("source") or _source_host(url) or "来源")
            else:
                url = str(item).strip()
                title = url
                source = _source_host(url) or "来源"
            if url and not any(link["url"] == url for link in links):
                links.append({"title": title[:120], "url": url, "source": source[:40]})
    if not links and fallback_url:
        links.append(
            {
                "title": _source_host(fallback_url) or fallback_url,
                "url": fallback_url,
                "source": _source_host(fallback_url) or "来源",
            }
        )
    return links[:5]


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
    item["source_type"] = str(
        item.get("source_type")
        or ("manual_seed" if item["source_url"] == ALIDOCS_SOURCE_URL else "manual")
    ).strip()
    try:
        item["source_count"] = max(1, int(item.get("source_count") or 1))
    except (TypeError, ValueError):
        item["source_count"] = 1
    try:
        item["score"] = int(float(item.get("score") or 0))
    except (TypeError, ValueError):
        item["score"] = 0
    item["evidence_links"] = _normalize_evidence_links(
        item.get("evidence_links"),
        item.get("source_url") or "",
    )
    item["generated_at"] = str(item.get("generated_at") or "")
    item["cluster_key"] = str(item.get("cluster_key") or _cluster_key(item["title"], item["tags"]))
    item["created_at"] = str(item.get("created_at") or _now())
    item["updated_at"] = str(item.get("updated_at") or item["created_at"])
    return item


def _seed_topics() -> list[dict]:
    return [_normalize_topic(topic) for topic in deepcopy(DEFAULT_TOPICS)]


def collect_polanews_signals(days: int, limit: int = MAX_SIGNALS_PER_SOURCE) -> list[InsightSignal]:
    articles: list[dict] = []
    seen_ids: set[str] = set()
    per_query = max(6, min(16, limit // max(len(POLANEWS_SEARCH_QUERIES), 1) + 2))
    for query in POLANEWS_SEARCH_QUERIES:
        payload = _request_json(
            POLANEWS_ARTICLES_URL,
            params={"page": 1, "limit": per_query, "search": query},
        )
        for article in (((payload or {}).get("data") or {}).get("articles") or []):
            if not isinstance(article, dict):
                continue
            article_key = str(article.get("id") or article.get("url") or "")
            if article_key and article_key in seen_ids:
                continue
            seen_ids.add(article_key)
            articles.append(article)
        time.sleep(0.05)
    signals: list[InsightSignal] = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        published_at = _parse_datetime(article.get("published_at") or article.get("created_at"))
        if not _within_days(published_at, days):
            continue
        categories = article.get("categories") or {}
        raw_tags = []
        if isinstance(categories, dict):
            for value in categories.values():
                if isinstance(value, list):
                    raw_tags.extend(value)
                elif value:
                    raw_tags.append(value)
        raw_tags.extend([article.get("feed_title"), article.get("region")])
        title = _clean_text(article.get("title_zh") or article.get("title"))
        summary = _clean_text(
            article.get("summary_zh")
            or article.get("ai_summary")
            or article.get("summary")
            or article.get("description")
        )
        url = str(article.get("url") or "").strip()
        if not title or not url:
            continue
        if not _is_relevant_signal(title, summary, url, " ".join(str(tag) for tag in raw_tags)):
            continue
        importance = _importance_score(article.get("importance"))
        tags = _normalize_tags(raw_tags) + _keyword_tags(title, summary)
        signals.append(
            InsightSignal(
                source="polanews",
                title=title,
                url=url,
                summary=summary,
                published_at=published_at,
                score=35 + importance * 12,
                tags=_normalize_tags(tags),
                metadata={"feed_title": article.get("feed_title"), "id": article.get("id")},
            )
        )
    return signals[:limit]


def collect_hackernews_signals(days: int, per_query: int = 8) -> list[InsightSignal]:
    queries = ["AI agent", "LLM", "Claude Code", "OpenAI", "Anthropic", "AI coding", "MCP"]
    signals: list[InsightSignal] = []
    seen_urls: set[str] = set()
    for query in queries:
        payload = _request_json(
            HN_SEARCH_URL,
            params={"query": query, "tags": "story", "hitsPerPage": per_query},
        )
        for hit in (payload or {}).get("hits") or []:
            if not isinstance(hit, dict):
                continue
            published_at = _parse_datetime(hit.get("created_at"))
            if not _within_days(published_at, days):
                continue
            item_id = str(hit.get("objectID") or "").strip()
            url = str(hit.get("url") or "").strip() or f"https://news.ycombinator.com/item?id={item_id}"
            if not url or url in seen_urls:
                continue
            title = _clean_text(hit.get("title") or hit.get("story_title"))
            if not title:
                continue
            story_text = _clean_text(hit.get("story_text") or hit.get("comment_text") or "")
            if not _is_relevant_signal(title, story_text, url):
                continue
            seen_urls.add(url)
            points = float(hit.get("points") or 0)
            comments = float(hit.get("num_comments") or 0)
            signals.append(
                InsightSignal(
                    source="hackernews",
                    title=title,
                    url=url,
                    summary=f"HN 近期讨论：{points:.0f} points / {comments:.0f} comments。",
                    published_at=published_at,
                    score=25 + min(points / 8, 30) + min(comments / 5, 20),
                    tags=_normalize_tags(["hackernews"] + _keyword_tags(title, story_text, url)),
                    metadata={"query": query, "object_id": item_id},
                )
            )
        time.sleep(0.05)
    return signals[:MAX_SIGNALS_PER_SOURCE]


def collect_github_signals(days: int, per_query: int = 6) -> list[InsightSignal]:
    cutoff = (_utc_now() - timedelta(days=days)).date().isoformat()
    queries = [
        f"topic:ai-agent pushed:>{cutoff} stars:>100",
        f"topic:llm pushed:>{cutoff} stars:>500",
        f"topic:mcp pushed:>{cutoff} stars:>50",
        f"AI pushed:>{cutoff} stars:>1000",
    ]
    signals: list[InsightSignal] = []
    seen_urls: set[str] = set()
    for query in queries:
        payload = _request_json(
            GITHUB_SEARCH_URL,
            params={"q": query, "sort": "updated", "order": "desc", "per_page": per_query},
        )
        for repo in (payload or {}).get("items") or []:
            if not isinstance(repo, dict):
                continue
            pushed_at = _parse_datetime(repo.get("pushed_at") or repo.get("updated_at"))
            if not _within_days(pushed_at, days):
                continue
            url = str(repo.get("html_url") or "").strip()
            if not url or url in seen_urls:
                continue
            name = _clean_text(repo.get("full_name") or repo.get("name"))
            description = _clean_text(repo.get("description") or "")
            if not name:
                continue
            seen_urls.add(url)
            stars = float(repo.get("stargazers_count") or 0)
            topics = repo.get("topics") or []
            title = f"{name}: {description}" if description else name
            signals.append(
                InsightSignal(
                    source="github",
                    title=_truncate(title, 140),
                    url=url,
                    summary=description or f"GitHub 仓库近期活跃，stars={stars:.0f}。",
                    published_at=pushed_at,
                    score=20 + min(stars / 600, 35),
                    tags=_normalize_tags(["github", "developer-tool"] + list(topics) + _keyword_tags(name, description)),
                    metadata={"stars": int(stars), "query": query},
                )
            )
        time.sleep(0.05)
    return signals[:MAX_SIGNALS_PER_SOURCE]


def _xml_first_text(node: ElementTree.Element, names: tuple[str, ...]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return _clean_text(found.text)
    for child in list(node):
        tag = child.tag.split("}", 1)[-1]
        if tag in names and child.text:
            return _clean_text(child.text)
    return ""


def _xml_link(node: ElementTree.Element) -> str:
    for child in list(node):
        tag = child.tag.split("}", 1)[-1]
        if tag == "link":
            href = child.attrib.get("href") or child.text
            if href:
                return href.strip()
    return _xml_first_text(node, ("link",))


def collect_rss_signals(days: int, limit_per_feed: int = 6) -> list[InsightSignal]:
    signals: list[InsightSignal] = []
    for feed in RSS_SOURCES:
        try:
            xml_text = _request_text(feed["feed_url"])
            root = ElementTree.fromstring(xml_text)
        except Exception:
            continue
        entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for node in entries[:limit_per_feed]:
            title = _xml_first_text(node, ("title",))
            url = _xml_link(node)
            published_at = _parse_datetime(
                _xml_first_text(node, ("pubDate", "published", "updated", "dc:date"))
            )
            if not title or not url or not _within_days(published_at, days):
                continue
            summary = _xml_first_text(node, ("description", "summary", "content"))
            if not _is_relevant_signal(title, summary, url):
                continue
            signals.append(
                InsightSignal(
                    source=feed["source"],
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=published_at,
                    score=30,
                    tags=_normalize_tags(feed.get("tags") or []) + _keyword_tags(title, summary),
                    metadata={"feed": feed.get("label")},
                )
            )
    return signals[:MAX_SIGNALS_PER_SOURCE]


def collect_topic_signals(days: int = DEFAULT_REFRESH_DAYS) -> tuple[list[InsightSignal], dict, list[str]]:
    days = days if days in ALLOWED_REFRESH_DAYS else DEFAULT_REFRESH_DAYS
    source_calls = [
        ("polanews", collect_polanews_signals),
        ("hackernews", collect_hackernews_signals),
        ("github", collect_github_signals),
        ("rss", collect_rss_signals),
    ]
    signals: list[InsightSignal] = []
    source_counts: dict[str, int] = {}
    errors: list[str] = []
    for source_name, collector in source_calls:
        try:
            source_signals = collector(days)
        except Exception as exc:
            errors.append(f"{source_name}: {exc}")
            source_counts[source_name] = 0
            continue
        source_counts[source_name] = len(source_signals)
        signals.extend(source_signals)
    return signals, source_counts, errors


def _topic_from_signal(signal: InsightSignal, generated_at: str) -> dict:
    tags = _normalize_tags(signal.tags + _keyword_tags(signal.title, signal.summary))
    source_label = SOURCE_LABELS.get(signal.source, signal.source)
    date = (signal.published_at.date().isoformat() if signal.published_at else _today())
    host = _source_host(signal.url) or source_label
    angle = (
        f"从 {source_label} / {host} 的近期信号切入，观察"
        f"{'、'.join(tags[:3]) if tags else 'AI 产业'}正在发生的变化，并提炼对产品、工程和商业判断的影响。"
    )
    summary = signal.summary or f"近期来自 {source_label} 的线上信号，适合展开为一篇洞察文章。"
    return {
        "date": date,
        "title": _truncate(signal.title, 80),
        "angle": angle,
        "summary": _truncate(summary, 260),
        "tags": tags[:8] or [signal.source],
        "status": "new",
        "source_url": signal.url,
        "source_type": signal.source,
        "source_count": 1,
        "evidence_links": [_evidence_link(signal)],
        "score": int(signal.score),
        "generated_at": generated_at,
        "cluster_key": _cluster_key(signal.title, tags),
    }


def signals_to_topics(
    signals: list[InsightSignal],
    max_topics: int = MAX_GENERATED_TOPICS,
) -> list[dict]:
    deduped: list[InsightSignal] = []
    seen: set[str] = set()
    for signal in signals:
        title = _clean_text(signal.title)
        url = str(signal.url or "").strip()
        key = hashlib.sha1(f"{url}|{title.lower()}".encode("utf-8")).hexdigest()
        if not title or not url or key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
    deduped.sort(key=lambda item: item.score, reverse=True)
    generated_at = _now()
    clustered: dict[str, dict] = {}
    for signal in deduped:
        topic = _topic_from_signal(signal, generated_at)
        key = topic["cluster_key"]
        existing = clustered.get(key)
        if not existing:
            clustered[key] = topic
            continue
        existing["source_count"] += 1
        existing["score"] = max(existing["score"], topic["score"]) + min(existing["source_count"] * 2, 12)
        existing["tags"] = _normalize_tags(existing["tags"] + topic["tags"])[:8]
        existing["evidence_links"] = _normalize_evidence_links(
            existing["evidence_links"] + topic["evidence_links"]
        )
        if existing["source_type"] != topic["source_type"]:
            existing["source_type"] = "mixed"
        if len(topic["summary"]) > len(existing.get("summary", "")):
            existing["summary"] = topic["summary"]
    topics = [_normalize_topic(topic) for topic in clustered.values()]
    topics.sort(key=lambda item: (item.get("score", 0), item.get("date", "")), reverse=True)
    return topics[:max_topics]


def merge_preserving_status(existing_topics: list[dict], generated_topics: list[dict]) -> list[dict]:
    existing_by_source_title = {
        f"{topic.get('source_url', '')}|{topic.get('title', '')}": topic
        for topic in existing_topics
        if topic.get("source_url") and topic.get("title")
    }
    source_counts: dict[str, int] = {}
    for topic in existing_topics:
        source_url = str(topic.get("source_url") or "")
        if source_url:
            source_counts[source_url] = source_counts.get(source_url, 0) + 1
    existing_by_source = {
        str(topic.get("source_url") or ""): topic
        for topic in existing_topics
        if topic.get("source_url") and source_counts.get(str(topic.get("source_url") or ""), 0) == 1
    }
    existing_by_cluster = {
        str(topic.get("cluster_key") or ""): topic for topic in existing_topics if topic.get("cluster_key")
    }
    merged: list[dict] = []
    generated_ids: set[str] = set()
    for generated in generated_topics:
        generated = _normalize_topic(generated)
        old = (
            existing_by_source_title.get(f"{generated['source_url']}|{generated['title']}")
            or existing_by_source.get(generated["source_url"])
            or existing_by_cluster.get(generated["cluster_key"])
        )
        if old:
            generated["id"] = old.get("id") or generated["id"]
            generated["created_at"] = old.get("created_at") or generated["created_at"]
            generated["status"] = old.get("status") if old.get("status") in TOPIC_STATUSES else generated["status"]
        generated["updated_at"] = _now()
        generated_ids.add(generated["id"])
        merged.append(generated)
    for old in existing_topics:
        normalized = _normalize_topic(old)
        if normalized["id"] in generated_ids:
            continue
        if normalized["status"] in {"selected", "imported", "archived"} or normalized["source_type"].startswith("manual"):
            merged.append(normalized)
    merged.sort(key=_topic_sort_key, reverse=True)
    return merged[: max(MAX_GENERATED_TOPICS + 12, len([t for t in merged if t.get("status") != "new"]))]


def load_topics() -> list[dict]:
    """Load topics, seeding a default list when no data file exists."""
    if not INSIGHT_TOPICS_FILE.is_file():
        topics = _seed_topics()
        save_topics(topics)
        return topics
    payload = _load_payload()
    raw_topics = payload.get("topics") or []
    topics = [_normalize_topic(topic) for topic in raw_topics if isinstance(topic, dict)]
    return sorted(topics, key=_topic_sort_key, reverse=True)


def save_topics(topics: list[dict], metadata: dict | None = None) -> None:
    normalized = [_normalize_topic(topic) for topic in topics]
    existing_payload = _load_payload() if INSIGHT_TOPICS_FILE.is_file() else {}
    metadata = metadata or {}
    INSIGHT_TOPICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_url": ALIDOCS_SOURCE_URL,
        "updated_at": _now(),
        "last_refresh": metadata.get("last_refresh") or existing_payload.get("last_refresh"),
        "topics": normalized,
    }
    tmp_path = INSIGHT_TOPICS_FILE.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, INSIGHT_TOPICS_FILE)


def get_last_refresh() -> dict | None:
    value = _load_payload().get("last_refresh")
    return value if isinstance(value, dict) else None


def refresh_topics_from_sources(days: int = DEFAULT_REFRESH_DAYS) -> dict:
    days = days if days in ALLOWED_REFRESH_DAYS else DEFAULT_REFRESH_DAYS
    existing_topics = load_topics()
    signals, source_counts, errors = collect_topic_signals(days)
    generated_topics = signals_to_topics(signals)
    if generated_topics:
        topics = merge_preserving_status(existing_topics, generated_topics)
    else:
        topics = existing_topics
    last_refresh = {
        "refreshed_at": _now(),
        "days": days,
        "signal_count": len(signals),
        "topic_count": len(generated_topics),
        "source_counts": source_counts,
        "errors": errors[:8],
    }
    save_topics(topics, metadata={"last_refresh": last_refresh})
    return {
        "topics": topics,
        "last_refresh": last_refresh,
        "source_counts": source_counts,
        "errors": errors,
    }


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
    evidence_links = _normalize_evidence_links(topic.get("evidence_links"), source_url)
    title = topic.get("title") or "洞察选题"
    summary = topic.get("summary") or ""
    angle = topic.get("angle") or ""
    source_type = SOURCE_LABELS.get(topic.get("source_type"), topic.get("source_type", "来源"))
    evidence_markdown = "\n".join(
        f"- [{link.get('title') or link.get('source')}]({link.get('url')})"
        for link in evidence_links
        if link.get("url")
    )
    markdown = "\n\n".join(
        part for part in [
            f"# {title}",
            "## 洞察选题",
            f"- 日期：{topic.get('date', '')}",
            f"- 状态：{TOPIC_STATUSES.get(topic.get('status'), topic.get('status', '待处理'))}",
            f"- 标签：{', '.join(tags) if tags else '待补充'}",
            f"- 来源类型：{source_type}",
            f"- 来源数量：{topic.get('source_count', 1)}",
            f"- 选题评分：{topic.get('score', 0)}",
            f"- 主来源：{source_url}",
            "## 写作角度\n" + (angle or "请补充这篇文章最值得展开的判断角度。"),
            "## 关键摘要\n" + (summary or "请补充选题背后的事实、信号和可写切口。"),
            "## 证据链接\n" + (evidence_markdown or f"- {source_url}"),
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
