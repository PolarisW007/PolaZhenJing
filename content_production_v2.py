"""Content production v2 helpers for research-backed writing workflows.

This module keeps the non-LLM parts of the v2 writing pipeline deterministic:
- capability maps for referenced upstream projects
- normalized real-time signal summaries
- heuristic "de-AI" review reports against PolaZhenJing author DNA
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


CAPABILITY_MAP: list[dict[str, Any]] = [
    {
        "name": "humanizer",
        "github": "https://github.com/blader/humanizer",
        "phase": "去 AI 味规则库",
        "focus": ["英文套话修复", "比较句去模板化", "语言人味修整"],
    },
    {
        "name": "Humanizer-zh",
        "github": "https://github.com/op7418/Humanizer-zh",
        "phase": "去 AI 味规则库",
        "focus": ["中文翻译腔清理", "工程汇报腔识别", "空泛总结句修复"],
    },
    {
        "name": "stop-slop",
        "github": "https://github.com/hardikpandya/stop-slop",
        "phase": "审稿规则",
        "focus": ["filler phrase 清理", "结构套路识别", "公式化表达压缩"],
    },
    {
        "name": "taste-skill",
        "github": "https://github.com/Leonxlnx/taste-skill",
        "phase": "标题与表达品味",
        "focus": ["标题审美", "generic output 检查", "段落质感提示"],
    },
    {
        "name": "ai-flavor-remover",
        "github": "https://github.com/hylarucoder/ai-flavor-remover",
        "phase": "中文去味规则",
        "focus": ["中文 prompt 修复", "AI 味句式压缩", "事实不变前提下润色"],
    },
    {
        "name": "shuorenhua",
        "github": "https://github.com/MrGeDiao/shuorenhua",
        "phase": "中文说人话",
        "focus": ["说人话改写", "减少工程师腔", "读者视角重述"],
    },
    {
        "name": "nuwa-skill",
        "github": "https://github.com/alchaincyf/nuwa-skill",
        "phase": "作者风格 DNA",
        "focus": ["作者画像蒸馏", "判断框架提炼", "表达习惯建模"],
    },
    {
        "name": "writing-agent",
        "github": "https://github.com/dongbeixiaohuo/writing-agent",
        "phase": "全链路写作",
        "focus": ["提纲到成稿", "编辑反馈回路", "图文发布流程"],
    },
    {
        "name": "chatgpt-comparison-detection",
        "github": "https://github.com/Hello-SimpleAI/chatgpt-comparison-detection",
        "phase": "检测辅助",
        "focus": ["AI/人类对比参考", "检测器辅助评分", "误判提醒"],
    },
    {
        "name": "De-AI-Prompt-Enhancer",
        "github": "https://github.com/OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL",
        "phase": "提示词增强",
        "focus": ["去 AI 味提示增强", "写作助推", "作者风格复现参考"],
    },
    {
        "name": "last30days-skill",
        "github": "https://github.com/mvanhorn/last30days-skill",
        "phase": "实时信号研究",
        "focus": ["近 30 天多源抓取", "观点簇整理", "争议点与链接证据"],
    },
]


@dataclass(frozen=True)
class AuthorStyleDNA:
    name: str
    opening_preference: str
    structure_preference: str
    evidence_preference: str
    avoid_phrases: tuple[str, ...]
    avoid_tone: tuple[str, ...]
    required_traits: tuple[str, ...]


POLA_ZHENJING_DNA = AuthorStyleDNA(
    name="PolaZhenJing / 炽驹Polaris",
    opening_preference="从具体场景、反常识判断或真实使用体验切入",
    structure_preference="故事切入 -> 问题拆解 -> 行业坐标 -> 方法论 -> 自己怎么用",
    evidence_preference="优先引用真实链接、案例、时间点、数字和可核验观察",
    avoid_phrases=(
        "首先",
        "其次",
        "最后",
        "综上所述",
        "值得注意的是",
        "让我们来看看",
        "说白了",
        "换句话说",
        "不可否认",
        "本质上",
    ),
    avoid_tone=(
        "宏大背景空转",
        "翻译腔",
        "工程汇报腔",
        "万能总结句",
        "无证据强判断",
    ),
    required_traits=(
        "具体场景感",
        "作者判断",
        "事实引用",
        "节奏变化",
        "保留不确定性边界",
    ),
)


SCENE_MARKERS = ("昨天", "今天", "刚刚", "那天", "我在", "我看到", "我想起", "上周", "这两天")
FILLER_PATTERNS = (
    "在这个快速发展的时代",
    "不难发现",
    "可以说",
    "某种程度上",
    "带来了新的可能",
    "引发了广泛关注",
    "提供了新的思路",
)
EVIDENCE_HINTS = ("http://", "https://", "《", "》", "%", "年", "月", "日")


def capability_map_markdown() -> str:
    lines = [
        "# PolaZhenJing 内容生产 v2 能力地图",
        "",
        "| 项目 | 阶段 | 可借鉴能力 | GitHub |",
        "| --- | --- | --- | --- |",
    ]
    for item in CAPABILITY_MAP:
        lines.append(
            f"| {item['name']} | {item['phase']} | {'、'.join(item['focus'])} | {item['github']} |"
        )
    return "\n".join(lines) + "\n"


def normalize_signal_summary(topic: str, signals: list[dict[str, Any]] | None) -> dict[str, Any]:
    normalized_sources: list[dict[str, Any]] = []
    missing_sources: list[str] = []
    for source in signals or []:
        name = str(source.get("source") or source.get("name") or "").strip() or "unknown"
        available = bool(source.get("available", True))
        entry = {
            "source": name,
            "available": available,
            "summary": str(source.get("summary") or "").strip(),
            "clusters": list(source.get("clusters") or []),
            "controversies": list(source.get("controversies") or []),
            "links": list(source.get("links") or []),
        }
        normalized_sources.append(entry)
        if not available or not entry["links"]:
            missing_sources.append(name)

    merged_clusters: list[str] = []
    merged_controversies: list[str] = []
    merged_links: list[str] = []
    for entry in normalized_sources:
        merged_clusters.extend(str(item).strip() for item in entry["clusters"] if str(item).strip())
        merged_controversies.extend(str(item).strip() for item in entry["controversies"] if str(item).strip())
        merged_links.extend(str(item).strip() for item in entry["links"] if str(item).strip())

    return {
        "topic": topic.strip(),
        "sources": normalized_sources,
        "clusters": _unique(merged_clusters),
        "controversies": _unique(merged_controversies),
        "links": _unique(merged_links),
        "missing_sources": _unique(missing_sources),
        "status": "ok" if normalized_sources and not missing_sources else "partial",
    }


def review_article(
    article_markdown: str,
    signal_summary: dict[str, Any] | None = None,
    style_dna: AuthorStyleDNA = POLA_ZHENJING_DNA,
) -> dict[str, Any]:
    text = article_markdown.strip()
    paragraphs = [segment.strip() for segment in re.split(r"\n\s*\n", text) if segment.strip()]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first_paragraph = paragraphs[0] if paragraphs else ""

    tone_hits = [phrase for phrase in style_dna.avoid_phrases if phrase in text]
    filler_hits = [phrase for phrase in FILLER_PATTERNS if phrase in text]
    has_scene_opening = any(marker in first_paragraph for marker in SCENE_MARKERS)
    has_first_person = any(token in text for token in ("我", "我们"))
    has_evidence = any(hint in text for hint in EVIDENCE_HINTS)
    has_links = bool(re.findall(r"https?://\S+", text))

    structural_patterns: list[str] = []
    if re.search(r"首先|其次|最后", text):
        structural_patterns.append("存在首先/其次/最后式模板结构，容易暴露模板感。")
    if len(paragraphs) < 4:
        structural_patterns.append("段落数量偏少，难以承载故事切入与论证展开。")
    if not has_scene_opening:
        structural_patterns.append("开头缺少具体场景、反常识判断或真实体验切口。")

    evidence_gaps: list[str] = []
    if not has_evidence:
        evidence_gaps.append("正文缺少时间点、数字、书名号或明确事实锚点。")
    if not has_links:
        evidence_gaps.append("正文没有可核验链接，发布前应补充来源。")
    if isinstance(signal_summary, list):
        signal_summary = normalize_signal_summary("", signal_summary)
    if signal_summary and signal_summary.get("missing_sources"):
        evidence_gaps.append(
            "实时信号仍有来源缺失: " + "、".join(signal_summary["missing_sources"])
        )

    author_gaps: list[str] = []
    if not has_first_person:
        author_gaps.append("通篇缺少作者第一人称判断，作者感偏弱。")
    if tone_hits:
        author_gaps.append("命中禁用套话: " + "、".join(tone_hits))
    if filler_hits:
        author_gaps.append("命中 filler phrase: " + "、".join(filler_hits))

    removable_lines = [
        line for line in lines
        if any(phrase in line for phrase in tone_hits + filler_hits) or len(line) <= 8
    ][:8]

    return {
        "style": style_dna.name,
        "opening_ok": has_scene_opening,
        "evidence_ok": has_evidence and has_links,
        "signal_status": (signal_summary or {}).get("status", "missing"),
        "chinese_tone": _unique(tone_hits + filler_hits),
        "structural_patterns": structural_patterns,
        "evidence_gaps": evidence_gaps,
        "author_voice_gaps": author_gaps,
        "removable_lines": removable_lines,
        "required_traits": list(style_dna.required_traits),
    }


def render_review_markdown(
    topic: str,
    article_markdown: str,
    signal_summary: dict[str, Any] | None = None,
    style_dna: AuthorStyleDNA = POLA_ZHENJING_DNA,
) -> str:
    if isinstance(signal_summary, list):
        signal_summary = normalize_signal_summary(topic, signal_summary)
    report = review_article(article_markdown, signal_summary=signal_summary, style_dna=style_dna)
    lines = [
        f"# 去 AI 味审稿报告：{topic}",
        "",
        f"- 风格基准：{report['style']}",
        f"- 实时信号状态：{report['signal_status']}",
        f"- 开头场景感：{'通过' if report['opening_ok'] else '需加强'}",
        f"- 证据密度：{'通过' if report['evidence_ok'] else '需补来源'}",
        "",
        "## 中文腔调问题",
    ]
    lines.extend(_bullet_lines(report["chinese_tone"], fallback="未命中已知套话，但仍需人工复核语气。"))
    lines.append("")
    lines.append("## 结构套路")
    lines.extend(_bullet_lines(report["structural_patterns"], fallback="未发现明显模板结构。"))
    lines.append("")
    lines.append("## 证据缺口")
    lines.extend(_bullet_lines(report["evidence_gaps"], fallback="证据锚点基本完整。"))
    lines.append("")
    lines.append("## 作者感缺口")
    lines.extend(_bullet_lines(report["author_voice_gaps"], fallback="作者判断与个人视角基本可见。"))
    lines.append("")
    lines.append("## 可删句子")
    lines.extend(_bullet_lines(report["removable_lines"], fallback="暂未识别明显可删句。"))
    lines.append("")
    lines.append("## 必须保留的作者特征")
    lines.extend(_bullet_lines(report["required_traits"]))
    if signal_summary:
        lines.append("")
        lines.append("## 实时信号摘要")
        lines.extend(render_signal_summary_lines(signal_summary))
    return "\n".join(lines) + "\n"


def render_signal_summary_lines(signal_summary: dict[str, Any]) -> list[str]:
    lines = [
        f"- 主题：{signal_summary.get('topic', '').strip() or '未命名主题'}",
        f"- 观点簇：{'、'.join(signal_summary.get('clusters') or ['待补'])}",
        f"- 争议点：{'、'.join(signal_summary.get('controversies') or ['待补'])}",
        f"- 链接数：{len(signal_summary.get('links') or [])}",
    ]
    missing = signal_summary.get("missing_sources") or []
    if missing:
        lines.append(f"- 来源缺失：{'、'.join(missing)}")
    for source in signal_summary.get("sources") or []:
        status = "可用" if source.get("available") else "缺失"
        lines.append(
            f"- [{status}] {source.get('source', 'unknown')}: "
            f"{source.get('summary') or '无摘要'}"
        )
    return lines


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _bullet_lines(items: list[str], fallback: str | None = None) -> list[str]:
    if items:
        return [f"- {item}" for item in items]
    return [f"- {fallback}"] if fallback else []
