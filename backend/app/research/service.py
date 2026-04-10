"""
=============================================================================
Module: research.service
Description: Core orchestration service for the deep research AI pipeline.
             Manages research CRUD and the multi-step generation process
             that yields SSE events for real-time progress streaming.
             深度研究AI管道核心编排服务 - 管理研究CRUD和多步骤生成流程。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: sqlalchemy, app.ai, app.research.html_renderer
=============================================================================
"""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_provider
from app.common.exceptions import BadRequestException, NotFoundException
from app.research.html_renderer import render_report
from app.research.models import Research, ResearchStatus
from app.research.schemas import ResearchGenerateEvent
from app.research.web_search import get_search_provider

logger = logging.getLogger("polazj.research.service")


# ── CRUD ─────────────────────────────────────────────────────────────────

async def create_research(
    db: AsyncSession,
    author_id: uuid.UUID,
    query: str,
    title: str | None = None,
) -> Research:
    """
    Create a new research record in PENDING status.
    Prevents duplicate: if an active (pending/generating) research with the
    same query already exists for this user, raises a 409 Conflict.
    创建新的研究记录，防止重复提交。
    """
    # Check for duplicate active research with same query
    dup_stmt = select(Research).where(
        Research.author_id == author_id,
        Research.query == query,
        Research.status.in_([ResearchStatus.PENDING, ResearchStatus.GENERATING]),
    )
    existing = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=409,
            detail="已存在相同问题的研究任务正在进行中",
            headers={"X-Existing-Id": str(existing.id)},
        )

    research = Research(
        title=title or "",
        query=query,
        status=ResearchStatus.PENDING,
        author_id=author_id,
    )
    db.add(research)
    await db.flush()
    await db.refresh(research)
    return research


async def get_research_by_id(db: AsyncSession, research_id: uuid.UUID) -> Research:
    """Fetch a single research by ID."""
    stmt = select(Research).where(Research.id == research_id)
    result = await db.execute(stmt)
    research = result.scalar_one_or_none()
    if research is None:
        raise NotFoundException(detail="Research not found")
    return research


async def list_researches(
    db: AsyncSession,
    author_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Research], int]:
    """List researches for a user with pagination."""
    stmt = select(Research).where(Research.author_id == author_id)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Research.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def delete_research(db: AsyncSession, research_id: uuid.UUID) -> None:
    """Delete a research by ID."""
    research = await get_research_by_id(db, research_id)
    await db.delete(research)
    await db.flush()


# ── Smart Describe (Query Optimization) ──────────────────────────────────

OPTIMIZE_QUERY_SYSTEM_PROMPT = """You are a senior research analyst and prompt engineer.
The user wants to generate a deep research report. They have written a rough research question.
Your job is to **optimize and enhance** the research question to be:

1. **More structured**: Break the vague intent into explicit, clear sub-questions or dimensions.
2. **More comprehensive**: Supplement angles or perspectives the user might have missed, such as:
   - Historical context and evolution timeline
   - Key technical comparisons
   - Important papers, milestones, or data points
   - Current challenges and future outlook
   - Industry or practical implications
3. **Better formatted**: Use numbered points or clear segmentation so the AI report generator can produce higher-quality results.
4. **Same language**: Keep the same language as the user's input.

Do NOT change the core intent or topic—only make the description richer, more precise, and more structured.

Return a JSON object with this exact structure:
{
  "optimized_query": "the enhanced research question text",
  "optimized_title": "an optional improved title if applicable, or null"
}

Output ONLY the JSON, no markdown fences, no extra text."""


async def optimize_query(query: str, title: str | None = None) -> dict:
    """
    Use AI to enhance and restructure the user's research query.
    利用AI优化和结构化用户的研究问题。
    """
    ai = get_ai_provider()

    user_prompt = f"Research question:\n{query}"
    if title:
        user_prompt = f"Title: {title}\n\n{user_prompt}"

    raw = await ai._chat(OPTIMIZE_QUERY_SYSTEM_PROMPT, user_prompt)

    # Parse JSON from response
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Failed to parse optimize query JSON: %s", text[:500])
        # Fallback: return the raw text as the optimized query
        return {"optimized_query": text, "optimized_title": title}

    return {
        "optimized_query": result.get("optimized_query", query),
        "optimized_title": result.get("optimized_title", title),
    }


# ── AI Pipeline Prompts ──────────────────────────────────────────────────

OUTLINE_SYSTEM_PROMPT = """You are a senior research analyst. Given a research question, generate a structured outline for a comprehensive deep research report.

Return a valid JSON object with this exact structure:
{
  "title": "Report title in the same language as the question",
  "badge": "Short category badge like '深度研究 | 人工智能' or 'Deep Research | AI'",
  "abstract_points": ["key finding 1", "key finding 2", "key finding 3"],
  "core_conclusion": "One sentence core conclusion",
  "sections": [
    {
      "id": "section_1",
      "title": "Section title (e.g. '一、预训练与后训练的基本概念与区别')",
      "description": "Brief description of what to cover",
      "content_type": "mixed",
      "subsections": ["subsection title 1", "subsection title 2"]
    }
  ],
  "conclusion_points": ["conclusion point 1", "conclusion point 2", "conclusion point 3"]
}

Generate 4-7 sections. Match the language of the user's question. Be thorough and systematic."""

SECTION_SYSTEM_PROMPT = """You are a senior research analyst writing a section of a deep research report.

Write the content for the specified section. Your output must be valid HTML fragments (no <html>, <head>, or <body> tags).

Use these HTML elements as appropriate:
- <p> for paragraphs
- <h3> for subsection headings
- <ul>/<ol> and <li> for lists
- <strong> for emphasis
- <table><thead><tbody><tr><th><td> for comparison tables
- <div class="highlight-box"><strong>Key Point:</strong> ...</div> for important callouts
- <div class="timeline"><div class="timeline-item"><span class="year">YEAR</span> <strong>Event</strong>: Description</div></div> for chronological events
- <span class="tag">TagName</span> for inline tags/labels
- For paper references, use: <ul class="paper-list"><li><a href="URL">Paper Title</a> (Year) - Brief description</li></ul>

Write in the same language as the section title. Be detailed, include specific examples, data, and references where relevant. Output ONLY the HTML content, no markdown, no code fences."""

CONCLUSION_SYSTEM_PROMPT = """You are a senior research analyst writing the conclusion of a deep research report.

Given the report title and conclusion points, write a compelling conclusion as HTML.
Use <p> tags. Add <br> between key points for readability.
Use <strong> for the most important takeaway.
Write in the same language as the input. Output ONLY the HTML content."""


# ── AI Pipeline Generator ────────────────────────────────────────────────

async def generate_research(
    db: AsyncSession,
    research_id: uuid.UUID,
) -> AsyncGenerator[ResearchGenerateEvent, None]:
    """
    Multi-step AI pipeline that yields SSE events.

    Steps:
        1. Analyze & generate outline (10%)
        2. Web search for sources (20%) [optional]
        3. Generate content per section (20-80%)
        4. Compile full report (85%)
        5. Render HTML (95%)
        6. Save & complete (100%)
    """
    research = await get_research_by_id(db, research_id)

    if research.status == ResearchStatus.COMPLETED:
        raise BadRequestException(
            detail="该研究报告已生成完成，无需重复生成"
        )

    # Update status to GENERATING
    research.status = ResearchStatus.GENERATING
    await db.flush()

    ai = get_ai_provider()
    search_provider = get_search_provider()

    try:
        # ── Step 1: Analyze & Outline ────────────────────────────────
        yield ResearchGenerateEvent(
            step="outline", status="running",
            message="正在分析研究问题并生成报告大纲...",
            progress=5,
        )

        outline_raw = await ai._chat(
            OUTLINE_SYSTEM_PROMPT,
            f"Research question:\n{research.query}",
        )

        # Parse JSON from response (handle markdown code fences)
        outline_text = outline_raw.strip()
        if outline_text.startswith("```"):
            lines = outline_text.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            outline_text = "\n".join(lines)

        try:
            outline = json.loads(outline_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse outline JSON: %s", outline_text[:500])
            research.status = ResearchStatus.FAILED
            await db.flush()
            yield ResearchGenerateEvent(
                step="outline", status="error",
                message="AI返回的大纲格式无法解析，请重试",
                progress=5,
            )
            return

        report_title = outline.get("title", research.query[:100])
        research.title = report_title
        research.outline = json.dumps(outline, ensure_ascii=False)
        await db.flush()

        yield ResearchGenerateEvent(
            step="outline", status="done",
            message=f"大纲生成完成：{report_title}",
            progress=10,
            data={"title": report_title, "section_count": len(outline.get("sections", []))},
        )

        # ── Step 2: Web Search (optional) ────────────────────────────
        search_context = ""
        if search_provider.is_available:
            yield ResearchGenerateEvent(
                step="search", status="running",
                message="正在搜索相关资料和最新信息...",
                progress=12,
            )

            search_results = await search_provider.search(research.query, max_results=8)
            if search_results:
                search_context = "\n\nRelevant web search results for context:\n"
                source_urls = []
                for r in search_results:
                    search_context += f"- {r.title}: {r.snippet[:200]}\n  URL: {r.url}\n"
                    source_urls.append(r.url)
                research.source_urls = json.dumps(source_urls, ensure_ascii=False)
                await db.flush()

            yield ResearchGenerateEvent(
                step="search", status="done",
                message=f"搜索完成，找到 {len(search_results)} 条相关结果",
                progress=20,
            )
        else:
            yield ResearchGenerateEvent(
                step="search", status="done",
                message="未配置搜索API，使用AI内置知识生成",
                progress=20,
            )

        # ── Step 3: Generate sections ────────────────────────────────
        sections_data = outline.get("sections", [])
        section_count = len(sections_data)
        generated_sections = []

        for i, sec in enumerate(sections_data):
            progress = 20 + int((i / max(section_count, 1)) * 60)
            yield ResearchGenerateEvent(
                step="section", status="running",
                message=f"正在生成第 {i+1}/{section_count} 节：{sec.get('title', '')}",
                progress=progress,
            )

            section_prompt = (
                f"Report title: {report_title}\n"
                f"Section title: {sec.get('title', '')}\n"
                f"Section description: {sec.get('description', '')}\n"
                f"Subsections to cover: {', '.join(sec.get('subsections', []))}\n"
            )
            if search_context:
                section_prompt += f"\n{search_context}"

            section_html = await ai._chat(SECTION_SYSTEM_PROMPT, section_prompt)

            # Clean any accidental code fences
            section_html = section_html.strip()
            if section_html.startswith("```"):
                lines = section_html.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                section_html = "\n".join(lines)

            generated_sections.append({
                "title": sec.get("title", f"Section {i+1}"),
                "content": section_html,
            })

            yield ResearchGenerateEvent(
                step="section", status="done",
                message=f"第 {i+1}/{section_count} 节完成",
                progress=20 + int(((i + 1) / max(section_count, 1)) * 60),
            )

        # ── Step 4: Compile ──────────────────────────────────────────
        yield ResearchGenerateEvent(
            step="compile", status="running",
            message="正在编译完整报告...",
            progress=82,
        )

        # Generate abstract HTML
        abstract_points = outline.get("abstract_points", [])
        core_conclusion = outline.get("core_conclusion", "")
        abstract_html = ""
        if abstract_points or core_conclusion:
            abstract_html = f"<p>{'</p><p>'.join(abstract_points)}</p>"
            if core_conclusion:
                abstract_html += (
                    f'<div class="highlight-box"><strong>核心结论：</strong> '
                    f"{core_conclusion}</div>"
                )

        # Generate conclusion HTML
        conclusion_points = outline.get("conclusion_points", [])
        conclusion_prompt = (
            f"Report title: {report_title}\n"
            f"Conclusion points: {json.dumps(conclusion_points, ensure_ascii=False)}"
        )
        conclusion_html = await ai._chat(CONCLUSION_SYSTEM_PROMPT, conclusion_prompt)
        conclusion_html = conclusion_html.strip()
        if conclusion_html.startswith("```"):
            lines = conclusion_html.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            conclusion_html = "\n".join(lines)

        # Save compiled content as JSON
        full_content = {
            "title": report_title,
            "abstract": abstract_html,
            "sections": generated_sections,
            "conclusion": conclusion_html,
        }
        research.content = json.dumps(full_content, ensure_ascii=False)
        research.summary = core_conclusion or (abstract_points[0] if abstract_points else "")
        await db.flush()

        yield ResearchGenerateEvent(
            step="compile", status="done",
            message="报告编译完成",
            progress=85,
        )

        # ── Step 5: Render HTML ──────────────────────────────────────
        yield ResearchGenerateEvent(
            step="render", status="running",
            message="正在渲染HTML报告...",
            progress=90,
        )

        now = datetime.now(timezone.utc)
        meta_line = f"日期：{now.strftime('%Y年%m月')} &nbsp;|&nbsp; 来源：PolaZhenjing AI Research"
        badge = outline.get("badge", "深度研究 | AI Research")

        html_output = render_report(
            title=report_title,
            badge=badge,
            meta_line=meta_line,
            abstract_html=abstract_html,
            sections=generated_sections,
            conclusion_html=conclusion_html,
        )

        research.html_content = html_output
        await db.flush()

        # Also write to disk
        output_dir = _get_output_dir()
        slug = slugify(report_title) or str(research.id)[:8]
        file_name = f"{slug}-{now.strftime('%Y%m%d')}.html"
        file_path = output_dir / file_name
        file_path.write_text(html_output, encoding="utf-8")
        logger.info("Research HTML written to %s", file_path)

        yield ResearchGenerateEvent(
            step="render", status="done",
            message="HTML报告渲染完成",
            progress=95,
        )

        # ── Step 6: Done ─────────────────────────────────────────────
        research.status = ResearchStatus.COMPLETED
        research.metadata_json = json.dumps({
            "file_path": str(file_path),
            "section_count": section_count,
            "has_search": search_provider.is_available,
        }, ensure_ascii=False)
        await db.flush()

        yield ResearchGenerateEvent(
            step="complete", status="done",
            message="研究报告生成完成！",
            progress=100,
            data={"file_path": str(file_path)},
        )

    except Exception as e:
        logger.exception("Research generation failed: %s", e)
        research.status = ResearchStatus.FAILED
        await db.flush()
        err_msg = str(e).strip() or type(e).__name__
        yield ResearchGenerateEvent(
            step="error", status="error",
            message=f"生成失败：{err_msg[:200]}",
            progress=0,
        )


def _get_output_dir():
    """Get the research output directory, creating it if needed."""
    from pathlib import Path
    from app.config import settings
    output_dir = Path(settings.RESEARCH_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
