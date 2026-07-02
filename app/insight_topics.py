"""Insight topic storage and upload prefill helpers."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import threading
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

ALLOWED_REFRESH_DAYS = (1, 3, 7, 10, 14, 30)
DEFAULT_REFRESH_DAYS = 10
MAX_SIGNALS_PER_SOURCE = 60
MAX_GENERATED_TOPICS = 24
REQUEST_TIMEOUT = 8
TARGET_DRAFT_CHARS = 5000
MIN_DRAFT_CHARS = 4500
MAX_DRAFT_CHARS = 5600


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


AUTO_REFRESH_MAX_AGE_HOURS = _env_float("POLAZJ_INSIGHT_AUTO_REFRESH_HOURS", 20)
AUTO_REFRESH_LOCK_TTL_SECONDS = 60 * 60
AUTO_REFRESH_LOCK_FILE = PROJECT_ROOT / "data" / "insight_topics_refresh.lock"

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

CORE_AI_TERMS = (
    "ai",
    "artificial intelligence",
    "llm",
    "agent",
    "agents",
    "openai",
    "anthropic",
    "claude",
    "gpt",
    "mcp",
    "人工智能",
    "大模型",
    "智能体",
    "模型",
)

PREFERRED_TOPIC_TERMS = {
    "scenario": (
        "use case",
        "workflow",
        "application",
        "app",
        "场景",
        "应用",
        "工作流",
        "落地",
        "业务",
    ),
    "methodology": (
        "methodology",
        "framework",
        "playbook",
        "cognitive",
        "thinking",
        "方法论",
        "认知",
        "框架",
        "范式",
        "判断",
    ),
    "practice": (
        "best practice",
        "practice",
        "implementation",
        "engineering",
        "coding",
        "developer",
        "实践",
        "实现",
        "工程",
        "最佳实践",
    ),
    "industry": (
        "industry",
        "enterprise",
        "business",
        "market",
        "行业",
        "企业",
        "商业",
        "产业",
        "组织",
    ),
    "skills": (
        "skill",
        "skills",
        "solution",
        "automation",
        "tool",
        "工具",
        "技能",
        "解决方案",
        "自动化",
    ),
}

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


def _draft_visible_text(markdown_text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", markdown_text or "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*_`~\-\[\](){},.:：，。；;！？!?/\\|]+", " ", text)
    text = re.sub(r"\s+", "", text)
    return text.strip()


def _draft_word_count(markdown_text: str) -> int:
    return len(_draft_visible_text(markdown_text))


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


def _contains_any_term(text: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        if term == "ai":
            if _contains_ai_token(text):
                return True
            continue
        if term in text:
            return True
    return False


def _topic_focus_score(*parts: str) -> int:
    """Score how well a signal matches PolaZhenjing's desired topic lane."""
    haystack = " ".join(part or "" for part in parts).lower()
    score = 0
    if _contains_any_term(haystack, CORE_AI_TERMS):
        score += 45
    for terms in PREFERRED_TOPIC_TERMS.values():
        if _contains_any_term(haystack, terms):
            score += 18
    if "skill" in haystack or "技能" in haystack or "解决方案" in haystack:
        score += 10
    return min(score, 100)


def _is_focused_topic_signal(signal: InsightSignal) -> bool:
    focus_score = _topic_focus_score(signal.title, signal.summary)
    if focus_score >= 45:
        return True
    if signal.source in {"openai_blog", "anthropic_news", "huggingface_blog", "google_ai_blog"}:
        return _contains_any_term((signal.title + " " + signal.summary).lower(), CORE_AI_TERMS)
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


def _evidence_markdown(links: list[dict], fallback_url: str = "") -> str:
    markdown = "\n".join(
        f"- [{link.get('title') or link.get('source')}]({link.get('url')})"
        for link in links
        if link.get("url")
    )
    return markdown or (f"- {fallback_url}" if fallback_url else "- 待补充")


def _draft_paragraphs(topic: dict) -> list[str]:
    title = _clean_text(topic.get("title") or "洞察选题")
    angle = _clean_text(topic.get("angle") or "从近期公开信号中提炼一个值得展开的行业判断。")
    summary = _clean_text(topic.get("summary") or "这是一条适合进一步写成洞察文章的选题。")
    tags = _normalize_tags(topic.get("tags") or [])
    tag_text = "、".join(tags[:5]) if tags else "AI 产业、产品和工程实践"
    source_type = SOURCE_LABELS.get(topic.get("source_type"), topic.get("source_type", "公开来源"))
    source_count = int(topic.get("source_count") or 1)
    score = int(topic.get("score") or 0)
    evidence_links = _normalize_evidence_links(topic.get("evidence_links"), topic.get("source_url") or "")
    evidence_names = "；".join(
        _clean_text(link.get("title") or link.get("source")) for link in evidence_links[:3]
    ) or "公开信号"
    evidence_urls = _evidence_markdown(evidence_links, topic.get("source_url") or "")

    return [
        f"# {title}",
        "## 洞察选题",
        f"- 日期：{topic.get('date', '')}",
        f"- 状态：{TOPIC_STATUSES.get(topic.get('status'), topic.get('status', '待处理'))}",
        f"- 标签：{', '.join(tags) if tags else '待补充'}",
        f"- 来源类型：{source_type}",
        f"- 来源数量：{source_count}",
        f"- 选题评分：{score}",
        f"- 主来源：{topic.get('source_url') or ALIDOCS_SOURCE_URL}",
        "## 写作角度",
        angle,
        "## 关键摘要",
        summary,
        "## 证据链接",
        evidence_urls,
        "## 导语",
        (
            f"如果只把“{title}”当成一条新闻，它很快就会被下一条更新淹没。"
            f"但把它放回最近的 {source_type} 信号、{source_count} 条来源证据和 {tag_text} 的上下文里看，"
            "它更像一个提醒：技术变化并不是突然砸到桌面上的结论，而是许多弱信号在同一个方向上慢慢汇合。"
        ),
        (
            f"这篇底稿先不急着给出宏大的答案，而是从一个朴素问题开始：为什么是现在？"
            f"为什么这些信号会围绕 {tag_text} 聚在一起？如果它只是噪音，我们会看到什么；如果它是趋势，"
            "产品、工程、内容和商业决策又应该怎么提前调整？"
        ),
        "## 核心判断",
        (
            f"我的初步判断是：{summary} 这句话背后真正值得写的，不是某个单点事件，"
            "而是它暴露出的组织能力变化。过去我们习惯把新技术理解成工具升级，今天更值得关注的是，"
            "这些工具开始改变任务的分配方式、判断的形成方式，以及团队内部谁拥有解释权。"
        ),
        (
            f"从 {evidence_names} 这些证据看，信号并不完全一致。有的偏产品，有的偏工程，有的偏资本市场或社区讨论。"
            "但它们共同指向一个事实：用户不再只问“这个东西能不能用”，而是在追问“它能不能进入真实流程”。"
            "这也是洞察文章应该抓住的第一层张力。"
        ),
        "## 为什么值得今天写",
        (
            "值得今天写，是因为窗口期往往出现在共识尚未完全形成的时候。等所有人都把它叫作趋势，"
            "文章就只能做复述；在信号刚刚汇聚时写，才有机会给读者一个判断框架。这个框架不需要押注唯一答案，"
            "但要把问题拆清楚：谁在受益，谁在付成本，谁的旧优势正在变弱。"
        ),
        (
            f"围绕 {tag_text}，读者真正需要的不是新闻摘要，而是一张决策地图。"
            "它应该告诉创业者该观察哪些早期需求，告诉产品经理该重构哪些入口，告诉工程团队哪些能力不再只是实验，"
            "也告诉普通读者为什么这些变化会穿透到工作方式里。"
        ),
        "## 事实和证据如何组织",
        (
            f"第一组证据来自来源本身：{source_type} 提供了近期发生的事实，"
            "这些事实可以作为文章开头的切口。写作时不必堆满链接，而要挑出最有解释力的两三条，"
            "说明它们分别代表需求、供给和传播三个方向。"
        ),
        (
            "第二组证据来自对比。可以把当前信号与过去一年的类似现象放在一起看："
            "哪些只是概念重复，哪些发生了能力迁移，哪些开始出现真实用户和真实预算。"
            "对比的价值在于，它能帮文章避免“看起来很新，其实只是换了说法”的陷阱。"
        ),
        (
            "第三组证据来自反例。任何趋势判断都应该主动回答反方问题：如果这件事没有那么重要，"
            "最可能的原因是什么？是技术不稳定，还是用户场景不够刚性；是成本太高，还是组织没有准备好。"
            "反例写得越扎实，主判断越可信。"
        ),
        "## 对产品和工程的启发",
        (
            "对产品来说，这个选题的价值在于提醒我们不要只盯功能，而要盯工作流。"
            "当用户愿意把一个新能力放进日常流程，它才真正从玩具变成基础设施。"
            "因此文章可以追问：这个变化会让哪些入口更短，哪些步骤被合并，哪些角色被重新定义。"
        ),
        (
            "对工程来说，真正的挑战不是写一个 demo，而是让系统能稳定处理边界、失败、权限和历史数据。"
            "越是看起来像内容或智能体验的问题，越需要底层工程能力兜住。文章可以把这一点写出来："
            "AI 时代的产品竞争，越来越像工程系统、数据质量和组织流程的综合竞争。"
        ),
        "## 对商业和组织的启发",
        (
            "商业上，最值得关注的是价值捕获位置是否改变。过去卖工具，收入来自授权；后来卖平台，收入来自生态；"
            "现在越来越多公司在卖结果、卖流程、卖一段被重新组织过的能力。这个变化会让定价、销售、交付和客户成功都发生位移。"
        ),
        (
            "组织上，问题会更微妙。新技术不会自动替代团队，但会放大团队原本的结构问题。"
            "如果一个组织原本就缺少清晰流程，新工具只会制造更多噪音；如果组织已经有稳定反馈回路，"
            "它反而能把新能力吸收到日常工作中。"
        ),
        "## 可写的故事线",
        (
            "这篇文章可以采用“三段式”结构。第一段写一个具体信号，让读者快速进入现场；"
            "第二段把信号拆成能力变化、需求变化和组织变化；第三段给出判断：未来一段时间，"
            "真正重要的不是谁先喊出概念，而是谁能把它变成可复用、可交付、可持续迭代的系统。"
        ),
        (
            "如果要写得更有个人色彩，可以加入作者自己的观察：最近在哪些产品、团队或讨论里反复看到类似问题。"
            "这种观察不必夸张，越具体越有力。读者需要感到文章不是从资料堆里拼出来的，而是从真实使用和真实判断里长出来的。"
        ),
        "## 风险和反方",
        (
            "反方观点至少有三类。第一类认为这只是短期热度，很快会退潮；第二类认为技术还不稳定，"
            "不足以支撑严肃场景；第三类认为商业模式并没有被证明，大家只是在用融资或流量维持叙事。"
        ),
        (
            "这些反方不能被轻轻带过。文章应该承认它们的合理性，再指出关键区别："
            "趋势不是没有波动，而是在波动之后仍然留下新的能力结构。只要某些流程被永久缩短，"
            "某些成本被永久降低，某些角色的边界被永久改写，它就不再只是热闹。"
        ),
        "## 结尾收束",
        (
            f"所以，{title} 真正值得写的地方，不在标题本身，而在它连接起的那条暗线："
            f"{tag_text} 正在从概念、工具、演示，慢慢进入更具体的工作现场。"
            "文章最后可以把问题抛回给读者：如果这个判断成立，你现在所在的产品、团队或行业，"
            "哪一个环节会最先被重新定义？"
        ),
        (
            "好的洞察文章不负责制造确定性，它负责提高读者看见变化的分辨率。"
            "这份底稿可以继续补充更具体的数据、人物、公司案例和反例，最终形成一篇既有证据，"
            "也有判断温度的长文。"
        ),
    ]


def _generate_topic_draft(topic: dict) -> str:
    paragraphs = _draft_paragraphs(topic)
    extension_templates = [
        (
            "补充观察 {index}：如果把这个选题继续往下挖，最值得追问的是采用门槛。"
            "很多技术看似已经成熟，但真正进入组织时，还要经过权限、成本、培训、协作习惯和责任归属的过滤。"
            "这些过滤条件决定了它是一次短暂试用，还是会沉淀成新的基础流程。"
        ),
        (
            "补充观察 {index}：另一个需要写清楚的是用户心智。用户并不会因为一个概念先进就改变习惯，"
            "他们只会在新方案明显更省力、更可靠或更有收益时迁移。文章可以把这种心智迁移写成一个过程，"
            "而不是把它处理成一句乐观判断。"
        ),
        (
            "补充观察 {index}：还可以加入供给侧视角。工具、模型、社区和资本都在推动变化，"
            "但每一方的动机不同。供给侧越热，越需要回到需求侧检查真实使用频率、留存和复购，"
            "否则很容易把市场噪音误判为结构性机会。"
        ),
        (
            "补充观察 {index}：最后要保留一点克制。真正有说服力的文章，不是把所有现象都解释成同一个大趋势，"
            "而是承认有些信号只是边缘事件，有些还需要等待验证。克制不是削弱观点，而是让观点更耐读。"
        ),
    ]
    index = 1
    while _draft_word_count("\n\n".join(paragraphs)) < TARGET_DRAFT_CHARS:
        template = extension_templates[(index - 1) % len(extension_templates)]
        paragraphs.append(template.format(index=index))
        index += 1
    draft = "\n\n".join(paragraphs)
    if _draft_word_count(draft) > MAX_DRAFT_CHARS:
        return draft
    return draft


def _ensure_topic_draft(topic: dict) -> tuple[str, int]:
    draft = str(topic.get("draft_markdown") or topic.get("draft") or "").strip()
    if _draft_word_count(draft) < MIN_DRAFT_CHARS:
        draft = _generate_topic_draft(topic)
    return draft, _draft_word_count(draft)


def _upload_article_draft(topic: dict) -> str:
    """Return a long article draft for upload without topic-pool metadata."""
    draft, _ = _ensure_topic_draft(topic)
    draft = draft.strip()
    if not draft:
        return ""
    title_line = draft.splitlines()[0].strip()
    marker = "\n## 导语"
    if marker not in draft:
        return draft
    article_body = draft[draft.index(marker) + 1 :].strip()
    article_draft = "\n\n".join(part for part in (title_line, article_body) if part).strip()
    if _draft_word_count(article_draft) < MIN_DRAFT_CHARS:
        return draft
    extension_index = 1
    extension_templates = [
        (
            "## 延展观察\n\n"
            "如果继续把这个选题推进成正式文章，还需要补一层和读者处境有关的判断。"
            "读者并不只关心某个新概念是否成立，他们更关心它会不会改变自己的工作顺序、能力边界和决策成本。"
            "因此写作时可以把抽象趋势拆成三个更具体的问题：它让谁少做了一步，它让谁多承担了责任，"
            "以及它让哪类旧经验开始失效。"
        ),
        (
            "## 作者提醒\n\n"
            "正式成稿前，还可以补一组更贴近现场的案例。案例不必多，但要能证明这个趋势已经进入真实流程，"
            "而不是只停留在演示、融资或社交媒体讨论里。一个好的案例应该同时说明使用者为什么采用、"
            "采用后什么指标发生变化，以及仍然卡在哪些组织和工程问题上。"
        ),
    ]
    while _draft_word_count(article_draft) < TARGET_DRAFT_CHARS:
        article_draft = "\n\n".join(
            [
                article_draft,
                extension_templates[(extension_index - 1) % len(extension_templates)],
            ]
        )
        extension_index += 1
    if _draft_word_count(article_draft) > MAX_DRAFT_CHARS:
        return article_draft[:MAX_DRAFT_CHARS].rstrip()
    return article_draft


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
    try:
        item["focus_score"] = int(float(item.get("focus_score") or 0))
    except (TypeError, ValueError):
        item["focus_score"] = 0
    item["evidence_links"] = _normalize_evidence_links(
        item.get("evidence_links"),
        item.get("source_url") or "",
    )
    item["generated_at"] = str(item.get("generated_at") or "")
    item["cluster_key"] = str(item.get("cluster_key") or _cluster_key(item["title"], item["tags"]))
    draft_markdown, draft_word_count = _ensure_topic_draft(item)
    item["draft_markdown"] = draft_markdown
    item["draft_word_count"] = draft_word_count
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
    focus_score = _topic_focus_score(signal.title, signal.summary)
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
        "score": int(signal.score) + focus_score,
        "focus_score": focus_score,
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
        if not _is_focused_topic_signal(signal):
            continue
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


def _last_refresh_age_hours(last_refresh: dict | None) -> float | None:
    if not last_refresh:
        return None
    refreshed_at = _parse_datetime(last_refresh.get("refreshed_at"))
    if not refreshed_at:
        return None
    if not refreshed_at.tzinfo:
        refreshed_at = refreshed_at.replace(tzinfo=timezone.utc)
    return max(0.0, (_utc_now() - refreshed_at.astimezone(timezone.utc)).total_seconds() / 3600)


def _auto_refresh_enabled() -> bool:
    value = os.getenv("POLAZJ_INSIGHT_AUTO_REFRESH", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _acquire_auto_refresh_lock() -> bool:
    AUTO_REFRESH_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        if AUTO_REFRESH_LOCK_FILE.exists():
            age = time.time() - AUTO_REFRESH_LOCK_FILE.stat().st_mtime
            if age > AUTO_REFRESH_LOCK_TTL_SECONDS:
                AUTO_REFRESH_LOCK_FILE.unlink(missing_ok=True)
        fd = os.open(str(AUTO_REFRESH_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_now())
        return True
    except FileExistsError:
        return False
    except OSError:
        return False


def _release_auto_refresh_lock() -> None:
    try:
        AUTO_REFRESH_LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _run_auto_refresh(days: int) -> None:
    try:
        refresh_topics_from_sources(days=days)
    finally:
        _release_auto_refresh_lock()


def trigger_stale_refresh_in_background(
    days: int = DEFAULT_REFRESH_DAYS,
    max_age_hours: float = AUTO_REFRESH_MAX_AGE_HOURS,
) -> dict:
    """Start a bounded background refresh when the topic pool is stale."""
    if not _auto_refresh_enabled():
        return {"status": "disabled"}
    last_refresh = get_last_refresh()
    age_hours = _last_refresh_age_hours(last_refresh)
    if age_hours is not None and age_hours < max_age_hours:
        return {"status": "fresh", "age_hours": age_hours}
    if not _acquire_auto_refresh_lock():
        return {"status": "locked", "age_hours": age_hours}
    thread = threading.Thread(
        target=_run_auto_refresh,
        args=(days if days in ALLOWED_REFRESH_DAYS else DEFAULT_REFRESH_DAYS,),
        name="polazj-insight-auto-refresh",
        daemon=True,
    )
    thread.start()
    return {"status": "started", "age_hours": age_hours}


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
    topic = _normalize_topic(topic)
    tags = topic.get("tags") or []
    source_url = topic.get("source_url") or ALIDOCS_SOURCE_URL
    title = topic.get("title") or "洞察选题"
    summary = _clean_text(topic.get("summary") or "")
    markdown = _upload_article_draft(topic)
    if not markdown:
        markdown = summary or _clean_text(topic.get("angle") or "") or "请补充这篇文章的核心摘要。"
    return {
        "topic_id": topic.get("id", ""),
        "title": title,
        "tags": ", ".join(tags),
        "description": summary[:160],
        "content": markdown,
        "source_url": source_url,
    }
