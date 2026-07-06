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
from datetime import date, datetime, timedelta, timezone
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
MAX_BACKFILL_DAYS = 366
MAX_BACKFILL_TOPICS_PER_DAY = 3
TOPIC_BLUEPRINT_VERSION = "social-operator-v1"


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
POLANEWS_SEARCH_QUERIES = (
    "AI agent workflow",
    "AI use case",
    "AI best practice",
    "AI business model",
    "AI product capability",
    "AI adoption",
    "context engineering",
    "AI eval guardrails",
    "AI 场景落地",
    "AI 产品能力",
    "AI 商业模式",
    "AI 最佳实践",
    "智能体 工作流",
    "企业 AI 采用",
)
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
    {
        "source": "deepmind_blog",
        "feed_url": "https://deepmind.google/blog/rss.xml",
        "label": "Google DeepMind",
        "tags": ["ai-lab", "research", "model", "google-deepmind"],
    },
    {
        "source": "microsoft_official_blog",
        "feed_url": "https://blogs.microsoft.com/feed/",
        "label": "Microsoft",
        "tags": ["enterprise-ai", "strategy", "business", "microsoft"],
        "limit": 10,
    },
    {
        "source": "aws_ml_blog",
        "feed_url": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "label": "AWS Machine Learning",
        "tags": ["cloud-ai", "enterprise-ai", "best-practice", "implementation", "aws"],
        "limit": 8,
    },
    {
        "source": "github_ai_ml_blog",
        "feed_url": "https://github.blog/ai-and-ml/feed/",
        "label": "GitHub AI & ML",
        "tags": ["developer-tool", "ai-coding", "best-practice", "github"],
    },
    {
        "source": "sequoia_stories",
        "feed_url": "https://www.sequoiacap.com/feed/",
        "label": "Sequoia",
        "tags": ["business-model", "startup", "commercial-thinking", "venture"],
        "limit": 10,
    },
]

INDUSTRY_CONTEXT_SOURCES = [
    {
        "label": "Anthropic Engineering",
        "title": "Building effective agents",
        "url": "https://www.anthropic.com/engineering/building-effective-agents",
        "summary": (
            "Anthropic 将 agent 系统拆成 workflow、tool use、routing、orchestrator 和 evaluator 等模式，"
            "适合作为 AI agent 最佳实践和工程护栏选题的底层来源。"
        ),
        "tags": ["ai-agent", "best-practice", "engineering", "workflow", "guardrail"],
        "lane": "best_practice",
        "score": 88,
    },
    {
        "label": "Anthropic Engineering",
        "title": "Effective context engineering for AI agents",
        "url": "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents",
        "summary": (
            "上下文工程正在成为 agent 落地的关键能力：选择、压缩、隔离和持久化上下文，"
            "能直接影响 AI 工作流的可靠性。"
        ),
        "tags": ["ai-agent", "context-engineering", "best-practice", "workflow"],
        "lane": "best_practice",
        "score": 84,
    },
    {
        "label": "Microsoft WorkLab",
        "title": "Agents, human agency and the opportunity for every organization",
        "url": "https://www.microsoft.com/en-us/worklab/work-trend-index/agents-human-agency-and-the-opportunity-for-every-organization",
        "summary": (
            "Microsoft Work Trend Index 讨论 agent 与组织采用、岗位重组和人机协作，"
            "适合产出企业 AI 采用、组织工作流和商业思考类选题。"
        ),
        "tags": ["enterprise-ai", "adoption", "organization", "workflow", "commercial-thinking"],
        "lane": "commercial_thinking",
        "score": 82,
    },
    {
        "label": "Microsoft WorkLab",
        "title": "2025 Work Trend Index: The year the Frontier Firm is born",
        "url": "https://www.microsoft.com/en-us/worklab/work-trend-index/2025-the-year-the-frontier-firm-is-born",
        "summary": (
            "Frontier Firm 框架把 AI 采用从个人效率提升推向组织结构变化，"
            "可支撑工作流重构、团队边界和企业采用方法论选题。"
        ),
        "tags": ["enterprise-ai", "organization", "adoption", "business", "workflow"],
        "lane": "commercial_thinking",
        "score": 78,
    },
    {
        "label": "OpenAI Business",
        "title": "Identifying and scaling AI use cases",
        "url": "https://cdn.openai.com/business-guides-and-resources/identifying-and-scaling-ai-use-cases.pdf",
        "summary": (
            "OpenAI 的企业 AI 用例识别和规模化方法，适合转译为场景选择、试点推进、指标验证和规模化复盘选题。"
        ),
        "tags": ["enterprise-ai", "use-case", "adoption", "best-practice", "workflow"],
        "lane": "scenario_use_case",
        "score": 86,
    },
    {
        "label": "OpenAI Business",
        "title": "The state of enterprise AI",
        "url": "https://cdn.openai.com/business-guides-and-resources/the-state-of-enterprise-ai.pdf",
        "summary": (
            "OpenAI 企业 AI 报告聚焦真实组织如何采用 AI、在哪些环节看到价值，"
            "适合做企业场景、产品能力和商业化判断。"
        ),
        "tags": ["enterprise-ai", "business", "adoption", "use-case"],
        "lane": "business_model",
        "score": 80,
    },
    {
        "label": "McKinsey QuantumBlack",
        "title": "The state of AI",
        "url": "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
        "summary": (
            "McKinsey State of AI 提供企业采用、价值捕获和 agentic AI 的高层趋势，"
            "适合作为商业思考、业务模式和行业判断类选题的权威参考。"
        ),
        "tags": ["enterprise-ai", "business-model", "commercial-thinking", "adoption"],
        "lane": "business_model",
        "score": 78,
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
    "deepmind_blog": "Google DeepMind",
    "microsoft_official_blog": "Microsoft",
    "aws_ml_blog": "AWS Machine Learning",
    "github_ai_ml_blog": "GitHub AI & ML",
    "sequoia_stories": "Sequoia",
    "industry_context": "行业实践源",
    "mixed": "多源聚合",
    "manual_seed": "本地种子",
    "manual_backfill": "历史回填",
    "manual": "人工维护",
}

BACKFILL_TOPIC_THEMES = [
    {
        "title": "AI 进入真实工作流后的采用门槛",
        "angle": "从权限、成本、协作习惯和责任归属切入，判断 AI 能否从演示进入日常流程。",
        "summary": "真正值得关注的不是单个工具是否惊艳，而是它能否稳定进入组织流程，并改变任务分配和判断形成方式。",
        "tags": ["ai-workflow", "adoption", "organization"],
    },
    {
        "title": "智能体产品从工具走向交付结果",
        "angle": "观察 Agent 如何把多步骤任务、历史上下文和业务约束组合成可复用的结果交付能力。",
        "summary": "智能体的竞争不只在模型能力，而在任务边界、失败恢复、权限控制和可追踪结果能否被工程化。",
        "tags": ["ai-agent", "product", "delivery"],
    },
    {
        "title": "内容生产从灵感驱动走向证据驱动",
        "angle": "把每日信号、选题判断、证据链接和作者腔调串成可复盘的内容生产系统。",
        "summary": "内容团队需要的不是更多模板，而是能沉淀判断、保留证据、支持复盘的生产链路。",
        "tags": ["content-production", "insight", "evidence"],
    },
    {
        "title": "大模型应用的工程稳定性成为产品体验",
        "angle": "从队列、超时、幂等、日志和降级策略出发，讨论 AI 功能为什么必须被当成生产系统建设。",
        "summary": "越是看起来像智能体验的问题，越需要底层工程能力兜住，稳定性会直接决定用户是否愿意托付真实任务。",
        "tags": ["llmops", "reliability", "engineering"],
    },
    {
        "title": "个人效率工具正在重写专业能力边界",
        "angle": "观察 AI 编码、写作、研究和自动化工具如何改变个人的能力半径与协作方式。",
        "summary": "AI 工具提升的不只是速度，也会改变一个人能独立承担的任务类型，以及团队内的分工结构。",
        "tags": ["personal-ai", "productivity", "ai-coding"],
    },
]

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
    "workflow": "workflow",
    "use case": "use-case",
    "business model": "business-model",
    "pricing": "business-model",
    "revenue": "business-model",
    "roi": "commercial-thinking",
    "adoption": "adoption",
    "context": "context-engineering",
    "evaluation": "evaluation",
    "eval": "evaluation",
    "guardrail": "guardrail",
    "安全": "ai-safety",
    "模型": "model",
    "智能体": "ai-agent",
    "开源": "open-source",
    "视频": "multimodal",
    "企业": "enterprise-ai",
    "工作流": "workflow",
    "场景": "use-case",
    "商业模式": "business-model",
    "定价": "business-model",
    "采用": "adoption",
    "上下文": "context-engineering",
    "评估": "evaluation",
    "护栏": "guardrail",
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

CONTENT_LANES = {
    "scenario_use_case": {
        "label": "场景使用",
        "audience": "正在寻找 AI 落地场景的创业者、产品经理和业务负责人",
        "question": "这条信号说明 AI 正在进入哪个真实工作流，为什么现在可行？",
        "terms": (
            "use case",
            "workflow",
            "application",
            "customer",
            "support",
            "sales",
            "marketing",
            "operation",
            "场景",
            "应用",
            "工作流",
            "业务",
            "客服",
            "销售",
            "营销",
            "运营",
            "落地",
        ),
        "structure": [
            "从一个近期信号切入具体工作现场",
            "拆解原流程里最耗时或最不稳定的环节",
            "说明 AI 介入后任务、角色和指标如何变化",
            "给出普通团队可复用的尝试路径和风险边界",
        ],
    },
    "product_capability": {
        "label": "产品能力更新",
        "audience": "关注 AI 产品能力演进的产品经理、研发负责人和独立开发者",
        "question": "这次能力更新会缩短哪个入口，改变哪个产品体验？",
        "terms": (
            "launch",
            "release",
            "update",
            "feature",
            "capability",
            "model",
            "api",
            "tool",
            "connector",
            "mcp",
            "multimodal",
            "能力",
            "更新",
            "发布",
            "模型",
            "工具",
            "接口",
            "连接器",
            "多模态",
            "产品",
        ),
        "structure": [
            "先讲能力变化，不复述发布稿",
            "解释它让哪些产品入口更短、哪些限制变少",
            "对比上一代方案的成本、稳定性和使用门槛",
            "给出产品团队应观察的指标和二阶影响",
        ],
    },
    "business_model": {
        "label": "业务模式",
        "audience": "关心 AI 商业化、定价、交付和市场机会的创业者",
        "question": "这条信号背后，谁会付钱，为什么愿意持续付钱？",
        "terms": (
            "business model",
            "pricing",
            "revenue",
            "monetization",
            "market",
            "startup",
            "customer success",
            "enterprise",
            "商业模式",
            "定价",
            "收入",
            "变现",
            "市场",
            "创业",
            "企业",
            "客户成功",
            "交付",
        ),
        "structure": [
            "从信号里提炼客户愿意付费的痛点",
            "拆解产品、服务、平台和结果交付的价值捕获差异",
            "分析销售、交付、留存和复购的关键门槛",
            "给出适合小团队验证商业化的最小实验",
        ],
    },
    "commercial_thinking": {
        "label": "商业思考",
        "audience": "需要形成行业判断的创始人、管理者和内容读者",
        "question": "这条信号为什么值得今天重估，它改变了哪类商业判断？",
        "terms": (
            "strategy",
            "organization",
            "competition",
            "roi",
            "adoption",
            "industry",
            "trend",
            "战略",
            "组织",
            "竞争",
            "ROI",
            "采用",
            "行业",
            "趋势",
            "判断",
            "商业",
        ),
        "structure": [
            "把信号放进行业变化和组织采用的上下文",
            "说明它挑战了哪条旧假设",
            "讨论受益者、付成本的人和被削弱的旧优势",
            "用一个开放问题收束，引导读者评论和转发",
        ],
    },
    "best_practice": {
        "label": "最佳实践",
        "audience": "正在把 AI 用到日常工作的开发者、运营者和团队负责人",
        "question": "这件事怎样做更稳，哪些做法可以复制，哪些边界必须提前声明？",
        "terms": (
            "best practice",
            "practice",
            "guide",
            "playbook",
            "framework",
            "implementation",
            "engineering",
            "eval",
            "evaluation",
            "guardrail",
            "最佳实践",
            "实践",
            "指南",
            "框架",
            "实现",
            "工程",
            "评估",
            "护栏",
            "方法",
        ),
        "structure": [
            "先写使用者遇到的具体问题",
            "提炼可复用步骤、判断标准和工具组合",
            "说明失败恢复、评估、权限和上下文管理",
            "列出读者今天就能试的检查清单",
        ],
    },
    "practice_recap": {
        "label": "实践复盘",
        "audience": "想看真实过程、失败原因和迁移经验的实践者",
        "question": "这次实践为什么能成或为什么卡住，给下一次尝试留下什么经验？",
        "terms": (
            "case study",
            "lessons",
            "postmortem",
            "how we built",
            "migration",
            "from prototype",
            "case",
            "复盘",
            "案例",
            "经验",
            "教训",
            "迁移",
            "实践过程",
            "我们如何",
            "从原型",
        ),
        "structure": [
            "还原一次真实尝试的起点和约束",
            "拆出做对的部分、卡住的部分和被低估的成本",
            "总结可迁移经验和不可复制条件",
            "把复盘变成读者下一次行动前的提醒",
        ],
    },
}

CONTENT_LANE_PRIORITY = (
    "scenario_use_case",
    "best_practice",
    "product_capability",
    "business_model",
    "commercial_thinking",
    "practice_recap",
)

CONTENT_LANE_TITLE_TEMPLATES = {
    "scenario_use_case": "{subject} 背后，AI 正在进入哪类真实工作流？",
    "product_capability": "{source_label} 的这次能力变化，产品团队应该盯住什么？",
    "business_model": "从 {subject} 看 AI 商业化的付费理由",
    "commercial_thinking": "{subject} 不只是新闻，它改变了哪条 AI 商业判断？",
    "best_practice": "把 {subject} 变成可复用实践，需要哪些护栏？",
    "practice_recap": "复盘 {subject}：从 demo 到真实流程卡在哪里？",
}

CONTENT_LANE_HOOK_TEMPLATES = {
    "scenario_use_case": "别只看“{subject}”这条消息，真正值得写的是它可能把 AI 带进了哪个具体工作流。",
    "product_capability": "这不是功能清单，而是在提醒产品团队：AI 产品入口和能力边界正在重新排列。",
    "business_model": "我更关心的不是谁发布了什么，而是谁会因此更愿意持续付费。",
    "commercial_thinking": "这条信号值得写，不是因为它新，而是因为它正在挑战一个旧的行业判断。",
    "best_practice": "如果团队也想跟进，先别复制 demo，先看它需要哪些流程、评估和护栏。",
    "practice_recap": "真正值得复盘的不是案例本身，而是它从原型走向真实流程时暴露了哪些成本。",
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


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"日期格式应为 YYYY-MM-DD：{value}") from exc


def _iter_dates(start_date: Any, end_date: Any) -> list[date]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("开始日期不能晚于结束日期。")
    span_days = (end - start).days + 1
    if span_days > MAX_BACKFILL_DAYS:
        raise ValueError(f"一次历史回填最多支持 {MAX_BACKFILL_DAYS} 天。")
    return [start + timedelta(days=offset) for offset in range(span_days)]


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


def _content_lane_info(lane_key: str) -> dict[str, Any]:
    return CONTENT_LANES.get(lane_key) or CONTENT_LANES["commercial_thinking"]


def _signal_source_label(signal: InsightSignal) -> str:
    metadata_label = ""
    if isinstance(signal.metadata, dict):
        metadata_label = _clean_text(signal.metadata.get("source_label") or signal.metadata.get("feed") or "")
    return metadata_label or SOURCE_LABELS.get(signal.source, signal.source)


def _infer_content_lane_from_text(*parts: str, source: str = "") -> str:
    haystack = " ".join(part or "" for part in parts).lower()
    scores: dict[str, int] = {lane_key: 0 for lane_key in CONTENT_LANES}
    for lane_key, lane in CONTENT_LANES.items():
        for term in lane["terms"]:
            term_text = str(term).lower()
            if term_text == "ai":
                if _contains_ai_token(haystack):
                    scores[lane_key] += 12
                continue
            if term_text and term_text in haystack:
                scores[lane_key] += 12

    source = (source or "").lower()
    if source == "github":
        scores["best_practice"] += 14
    if source == "hackernews":
        scores["practice_recap"] += 8
        scores["best_practice"] += 6
    if source in {"openai_blog", "anthropic_news", "huggingface_blog", "google_ai_blog", "deepmind_blog"}:
        scores["product_capability"] += 14
    if source in {"aws_ml_blog", "github_ai_ml_blog"}:
        scores["best_practice"] += 14
    if source in {"microsoft_official_blog", "sequoia_stories", "industry_context"}:
        scores["commercial_thinking"] += 10
        scores["business_model"] += 8
    if any(term in haystack for term in ("enterprise", "pricing", "revenue", "商业", "定价", "企业")):
        scores["business_model"] += 8
    if any(term in haystack for term in ("workflow", "场景", "应用", "support", "sales", "运营")):
        scores["scenario_use_case"] += 8
    if any(term in haystack for term in ("how we built", "case study", "postmortem", "复盘", "案例")):
        scores["practice_recap"] += 12

    best_score = max(scores.values())
    if best_score <= 0:
        return "commercial_thinking"
    return min(
        (lane for lane, score in scores.items() if score == best_score),
        key=lambda lane: CONTENT_LANE_PRIORITY.index(lane),
    )


def _infer_content_lane(signal: InsightSignal) -> str:
    if isinstance(signal.metadata, dict):
        lane_key = str(signal.metadata.get("lane") or "").strip()
        if lane_key in CONTENT_LANES:
            return lane_key
    return _infer_content_lane_from_text(
        signal.title,
        signal.summary,
        " ".join(signal.tags),
        signal.url,
        source=signal.source,
    )


def _source_subject(title: str) -> str:
    subject = _clean_text(title)
    subject = re.sub(r"^(show hn|ask hn|launch hn)\s*:\s*", "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\s*[-|]\s*(openai|anthropic|google|github)\s*$", "", subject, flags=re.IGNORECASE)
    return _truncate(subject, 54) or "这条 AI 行业信号"


def _content_lane_title(signal: InsightSignal, lane_key: str) -> str:
    source_label = _signal_source_label(signal)
    subject = _source_subject(signal.title)
    template = CONTENT_LANE_TITLE_TEMPLATES.get(
        lane_key,
        CONTENT_LANE_TITLE_TEMPLATES["commercial_thinking"],
    )
    title = template.format(subject=subject, source_label=source_label)
    return _truncate(title, 86)


def _social_hook(lane_key: str, subject: str) -> str:
    template = CONTENT_LANE_HOOK_TEMPLATES.get(
        lane_key,
        CONTENT_LANE_HOOK_TEMPLATES["commercial_thinking"],
    )
    return _truncate(template.format(subject=subject), 180)


def _content_structure(value: Any, lane_key: str) -> list[str]:
    if isinstance(value, str):
        value = [part.strip() for part in re.split(r"[;；\n]+", value) if part.strip()]
    if isinstance(value, list):
        structure = [_clean_text(item) for item in value if _clean_text(item)]
        if len(structure) >= 3:
            return structure[:5]
    return list(_content_lane_info(lane_key)["structure"])[:5]


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
        "source": _signal_source_label(signal),
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
    lane_key = str(topic.get("content_lane") or "commercial_thinking")
    lane = _content_lane_info(lane_key)
    lane_label = _clean_text(topic.get("content_lane_label") or lane["label"])
    social_hook = _clean_text(topic.get("social_hook") or _social_hook(lane_key, title))
    target_audience = _clean_text(topic.get("target_audience") or lane["audience"])
    core_question = _clean_text(topic.get("core_question") or lane["question"])
    content_structure = _content_structure(topic.get("content_structure"), lane_key)
    source_signal_title = _clean_text(topic.get("source_signal_title") or title)
    source_role = _clean_text(
        topic.get("source_role")
        or f"作为{lane_label}选题的证据切口，支撑判断，不直接作为文章标题。"
    )
    evidence_links = _normalize_evidence_links(topic.get("evidence_links"), topic.get("source_url") or "")
    evidence_names = "；".join(
        _clean_text(link.get("title") or link.get("source")) for link in evidence_links[:3]
    ) or "公开信号"
    evidence_urls = _evidence_markdown(evidence_links, topic.get("source_url") or "")
    structure_lines = "\n".join(f"- {step}" for step in content_structure)

    return [
        f"# {title}",
        "## 洞察选题",
        f"- 日期：{topic.get('date', '')}",
        f"- 状态：{TOPIC_STATUSES.get(topic.get('status'), topic.get('status', '待处理'))}",
        f"- 内容赛道：{lane_label}",
        f"- 目标读者：{target_audience}",
        f"- 核心问题：{core_question}",
        f"- 标签：{', '.join(tags) if tags else '待补充'}",
        f"- 来源类型：{source_type}",
        f"- 来源数量：{source_count}",
        f"- 选题评分：{score}",
        f"- 主来源：{topic.get('source_url') or ALIDOCS_SOURCE_URL}",
        f"- 原始信号：{source_signal_title}",
        f"- 证据角色：{source_role}",
        f"- 策略版本：{topic.get('draft_strategy_version') or TOPIC_BLUEPRINT_VERSION}",
        "## 写作角度",
        angle,
        "## 社媒运营蓝图",
        social_hook,
        "",
        "建议结构：",
        structure_lines,
        "## 关键摘要",
        summary,
        "## 证据链接",
        evidence_urls,
        "## 导语",
        (
            f"{social_hook} 如果只把“{source_signal_title}”当成一条新闻，它很快就会被下一条更新淹没。"
            f"但把它放回最近的 {source_type} 信号、{source_count} 条来源证据和 {tag_text} 的上下文里看，"
            f"它更像一个{lane_label}提醒：技术变化并不是突然砸到桌面上的结论，而是许多弱信号在同一个方向上慢慢汇合。"
        ),
        (
            f"这篇底稿先不急着给出宏大的答案，而是从一个朴素问题开始：{core_question}"
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
            f"这篇文章的目标读者可以先锁定为：{target_audience}。"
            "这会让写作从“发生了什么”转向“读者现在该怎么看、该做什么、不该误判什么”。"
            f"原始信号的角色也要保持克制：{source_role}"
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
        "## 建议写作结构",
        (
            "这类社媒内容可以按四步推进："
            + "；".join(content_structure)
            + "。这样写的好处是，文章不会停留在新闻复述，而会自然落到判断、方法和行动上。"
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
    if topic.get("_draft_needs_refresh") or topic.get("draft_strategy_version") != TOPIC_BLUEPRINT_VERSION:
        draft = ""
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
    lane_key = str(item.get("content_lane") or "").strip()
    if lane_key not in CONTENT_LANES:
        lane_key = _infer_content_lane_from_text(
            item["title"],
            item["angle"],
            item["summary"],
            " ".join(item["tags"]),
            source=item.get("source_type") or "",
        )
    lane = _content_lane_info(lane_key)
    item["content_lane"] = lane_key
    item["content_lane_label"] = _clean_text(item.get("content_lane_label") or lane["label"])
    item["target_audience"] = _clean_text(item.get("target_audience") or lane["audience"])
    item["core_question"] = _clean_text(item.get("core_question") or lane["question"])
    item["content_structure"] = _content_structure(item.get("content_structure"), lane_key)
    item["source_signal_title"] = _clean_text(
        item.get("source_signal_title")
        or item.get("source_title")
        or item["title"]
    )
    item["source_role"] = _clean_text(
        item.get("source_role")
        or f"作为{item['content_lane_label']}选题的证据切口，支撑判断，不直接作为文章标题。"
    )
    item["social_hook"] = _clean_text(
        item.get("social_hook") or _social_hook(lane_key, _source_subject(item["source_signal_title"]))
    )
    existing_draft_strategy = str(item.get("draft_strategy_version") or "")
    item["draft_strategy_version"] = existing_draft_strategy or TOPIC_BLUEPRINT_VERSION
    item["_draft_needs_refresh"] = existing_draft_strategy != TOPIC_BLUEPRINT_VERSION
    item["cluster_key"] = str(
        item.get("cluster_key")
        or _cluster_key(item["title"], item["tags"] + [item["content_lane"]])
    )
    draft_markdown, draft_word_count = _ensure_topic_draft(item)
    item["draft_markdown"] = draft_markdown
    item["draft_word_count"] = draft_word_count
    item["draft_strategy_version"] = TOPIC_BLUEPRINT_VERSION
    item.pop("_draft_needs_refresh", None)
    item["created_at"] = str(item.get("created_at") or _now())
    item["updated_at"] = str(item.get("updated_at") or item["created_at"])
    return item


def _seed_topics() -> list[dict]:
    return [_normalize_topic(topic) for topic in deepcopy(DEFAULT_TOPICS)]


def _topics_from_payload(payload: dict) -> list[dict]:
    raw_topics = payload.get("topics") or []
    return sorted(
        [_normalize_topic(topic) for topic in raw_topics if isinstance(topic, dict)],
        key=_topic_sort_key,
        reverse=True,
    )


def _backfill_topic_for_date(day: date, sequence: int = 1) -> dict:
    theme = BACKFILL_TOPIC_THEMES[(day.toordinal() + sequence - 1) % len(BACKFILL_TOPIC_THEMES)]
    sequence_suffix = "" if sequence == 1 else f"（方向 {sequence}）"
    date_text = day.isoformat()
    title = f"{date_text} 每日洞察：{theme['title']}{sequence_suffix}"
    return _normalize_topic(
        {
            "date": date_text,
            "title": title,
            "angle": theme["angle"],
            "summary": theme["summary"],
            "tags": ["daily-topic", "history-backfill", *theme["tags"]],
            "status": "new",
            "source_url": ALIDOCS_SOURCE_URL,
            "source_type": "manual_backfill",
            "source_count": 1,
            "evidence_links": [
                {
                    "title": "PolaZhenJing 历史每日选题回填记录",
                    "url": ALIDOCS_SOURCE_URL,
                    "source": "钉钉底料",
                }
            ],
            "score": 50 + (day.toordinal() % 20),
            "focus_score": 55,
            "generated_at": _now(),
            "cluster_key": _cluster_key(title, theme["tags"]),
        }
    )


def backfill_topics_for_date_range(
    start_date: Any,
    end_date: Any,
    topics_per_day: int = 1,
    persist: bool = True,
) -> dict:
    """Add deterministic historical daily topics for dates not already covered."""
    try:
        topics_per_day = int(topics_per_day)
    except (TypeError, ValueError) as exc:
        raise ValueError("每天回填数量必须是整数。") from exc
    if topics_per_day < 1 or topics_per_day > MAX_BACKFILL_TOPICS_PER_DAY:
        raise ValueError(f"每天回填数量必须在 1 到 {MAX_BACKFILL_TOPICS_PER_DAY} 之间。")

    target_days = _iter_dates(start_date, end_date)
    target_dates = [day.isoformat() for day in target_days]
    existing_topics = _topics_from_payload(_load_payload())
    existing_dates = {str(topic.get("date") or "") for topic in existing_topics}
    missing_before = [date_text for date_text in target_dates if date_text not in existing_dates]

    additions: list[dict] = []
    for day in target_days:
        date_text = day.isoformat()
        if date_text in existing_dates:
            continue
        for sequence in range(1, topics_per_day + 1):
            additions.append(_backfill_topic_for_date(day, sequence=sequence))

    final_topics = sorted([*existing_topics, *additions], key=_topic_sort_key, reverse=True)
    final_dates = {str(topic.get("date") or "") for topic in final_topics}
    missing_after = [date_text for date_text in target_dates if date_text not in final_dates]
    last_backfill = {
        "backfilled_at": _now(),
        "start_date": target_dates[0],
        "end_date": target_dates[-1],
        "topics_per_day": topics_per_day,
        "target_days": len(target_dates),
        "covered_days_before": len(target_dates) - len(missing_before),
        "missing_days_before": missing_before,
        "added_count": len(additions),
        "added_dates": sorted({topic["date"] for topic in additions}),
        "missing_days_after": missing_after,
        "persisted": bool(persist),
    }
    if persist and additions:
        save_topics(final_topics, metadata={"last_backfill": last_backfill})

    return {
        "start_date": target_dates[0],
        "end_date": target_dates[-1],
        "target_days": len(target_dates),
        "topics_per_day": topics_per_day,
        "covered_days_before": len(target_dates) - len(missing_before),
        "missing_days_before": missing_before,
        "added_count": len(additions),
        "added_dates": last_backfill["added_dates"],
        "missing_days_after": missing_after,
        "total_topics": len(final_topics),
        "persisted": bool(persist and additions),
    }


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
    queries = [
        "AI agent",
        "AI workflow",
        "enterprise AI",
        "LLM evals",
        "RAG",
        "Claude Code",
        "OpenAI",
        "Anthropic",
        "AI coding",
        "MCP",
    ]
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
        f"topic:rag pushed:>{cutoff} stars:>100",
        f"topic:llmops pushed:>{cutoff} stars:>50",
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
        feed_limit = int(feed.get("limit") or limit_per_feed)
        for node in entries[:feed_limit]:
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


def collect_industry_context_signals(days: int, limit: int = MAX_SIGNALS_PER_SOURCE) -> list[InsightSignal]:
    """Return curated non-news sources used as strategy context for social topics."""
    signals: list[InsightSignal] = []
    for source in INDUSTRY_CONTEXT_SOURCES[:limit]:
        title = _clean_text(source.get("title"))
        url = str(source.get("url") or "").strip()
        summary = _clean_text(source.get("summary"))
        if not title or not url:
            continue
        tags = _normalize_tags(source.get("tags") or []) + _keyword_tags(title, summary, url)
        signals.append(
            InsightSignal(
                source="industry_context",
                title=title,
                url=url,
                summary=summary,
                published_at=None,
                score=float(source.get("score") or 70),
                tags=_normalize_tags(tags),
                metadata={
                    "source_label": source.get("label"),
                    "lane": source.get("lane"),
                    "evergreen": True,
                    "refresh_days": days,
                },
            )
        )
    return signals[:limit]


def collect_topic_signals(days: int = DEFAULT_REFRESH_DAYS) -> tuple[list[InsightSignal], dict, list[str]]:
    days = days if days in ALLOWED_REFRESH_DAYS else DEFAULT_REFRESH_DAYS
    source_calls = [
        ("industry_context", collect_industry_context_signals),
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
    source_label = _signal_source_label(signal)
    date = (signal.published_at.date().isoformat() if signal.published_at else _today())
    host = _source_host(signal.url) or source_label
    focus_score = _topic_focus_score(signal.title, signal.summary)
    lane_key = _infer_content_lane(signal)
    lane = _content_lane_info(lane_key)
    subject = _source_subject(signal.title)
    title = _content_lane_title(signal, lane_key)
    lane_tag = lane_key.replace("_", "-")
    angle = (
        f"把 {source_label} / {host} 的“{subject}”作为证据切口，不做新闻搬运；"
        f"围绕“{lane['question']}”展开，提炼对产品、工程、运营和商业判断的影响。"
    )
    source_summary = signal.summary or f"近期来自 {source_label} 的线上信号。"
    summary = (
        f"这条信号适合转译为“{lane['label']}”类社媒选题："
        f"不是复述 {subject}，而是回答“{lane['question']}”。"
        f"原始摘要：{source_summary}"
    )
    return {
        "date": date,
        "title": title,
        "angle": angle,
        "summary": _truncate(summary, 260),
        "tags": _normalize_tags([lane_tag, "social-operator"] + tags)[:8] or [signal.source],
        "status": "new",
        "source_url": signal.url,
        "source_type": signal.source,
        "source_count": 1,
        "evidence_links": [_evidence_link(signal)],
        "score": int(signal.score) + focus_score,
        "focus_score": focus_score,
        "content_lane": lane_key,
        "content_lane_label": lane["label"],
        "social_hook": _social_hook(lane_key, subject),
        "target_audience": lane["audience"],
        "core_question": lane["question"],
        "content_structure": list(lane["structure"]),
        "source_signal_title": _truncate(signal.title, 140),
        "source_role": f"作为{lane['label']}选题的证据切口，支撑判断，不直接作为文章标题。",
        "draft_strategy_version": TOPIC_BLUEPRINT_VERSION,
        "generated_at": generated_at,
        "cluster_key": _cluster_key(signal.title, tags + [lane_key]),
    }


def _rank_topics_for_social_operation(topics: list[dict], max_topics: int) -> list[dict]:
    sorted_topics = sorted(
        topics,
        key=lambda item: (
            int(item.get("score") or 0),
            str(item.get("date", "")),
        ),
        reverse=True,
    )
    buckets: dict[str, list[dict]] = {lane_key: [] for lane_key in CONTENT_LANES}
    overflow: list[dict] = []
    for topic in sorted_topics:
        lane_key = str(topic.get("content_lane") or "")
        if lane_key in buckets:
            buckets[lane_key].append(topic)
        else:
            overflow.append(topic)

    ranked: list[dict] = []
    used_ids: set[str] = set()
    for lane_key in CONTENT_LANE_PRIORITY:
        if buckets[lane_key] and len(ranked) < max_topics:
            topic = buckets[lane_key].pop(0)
            ranked.append(topic)
            used_ids.add(topic["id"])

    remaining = [topic for topic in sorted_topics if topic["id"] not in used_ids] + overflow
    for topic in remaining:
        if len(ranked) >= max_topics:
            break
        if topic["id"] in used_ids:
            continue
        ranked.append(topic)
        used_ids.add(topic["id"])
    return ranked[:max_topics]


def _content_lane_counts(topics: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for topic in topics:
        label = _clean_text(topic.get("content_lane_label") or topic.get("content_lane") or "未分类")
        counts[label] = counts.get(label, 0) + 1
    return counts


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
    return _rank_topics_for_social_operation(topics, max_topics=max_topics)


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
            or existing_by_source_title.get(
                f"{generated['source_url']}|{generated.get('source_signal_title', '')}"
            )
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
    return _topics_from_payload(_load_payload())


def save_topics(topics: list[dict], metadata: dict | None = None) -> None:
    normalized = [_normalize_topic(topic) for topic in topics]
    existing_payload = _load_payload() if INSIGHT_TOPICS_FILE.is_file() else {}
    metadata = metadata or {}
    INSIGHT_TOPICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_url": existing_payload.get("source_url") or ALIDOCS_SOURCE_URL,
        "updated_at": _now(),
    }
    for key, value in existing_payload.items():
        if key not in {"source_url", "updated_at", "topics"} and value is not None:
            payload[key] = value
    for key, value in metadata.items():
        if key not in {"source_url", "updated_at", "topics"} and value is not None:
            payload[key] = value
    payload["topics"] = normalized
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
        "content_lane_counts": _content_lane_counts(generated_topics),
        "strategy": TOPIC_BLUEPRINT_VERSION,
        "data_source_strategy": "realtime-signals-plus-curated-industry-context",
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
