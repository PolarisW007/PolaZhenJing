"""
=============================================================================
Module: research.html_renderer
Description: Renders structured research data into a self-contained HTML
             report using Jinja2 templates.
             使用Jinja2模板将结构化研究数据渲染为独立HTML报告。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: jinja2
=============================================================================
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("polazj.research.renderer")

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,  # We control the HTML ourselves
    )


def render_report(
    title: str,
    badge: str,
    meta_line: str,
    abstract_html: str,
    sections: list[dict],
    conclusion_html: str,
    footer_text: str = "PolaZhenjing Deep Research | 基于AI生成的深度研究报告",
) -> str:
    """
    Render a research report to HTML.

    Args:
        title: Report main title.
        badge: Short category badge text (e.g. "深度研究 | 人工智能").
        meta_line: Metadata line below title (e.g. "日期：2026年4月 | 来源：...").
        abstract_html: Pre-rendered HTML for the abstract/summary card.
        sections: List of dicts with 'title' and 'content' (HTML) keys.
        conclusion_html: Pre-rendered HTML for the conclusion block.
        footer_text: Footer copyright line.

    Returns:
        Complete self-contained HTML string.
    """
    env = _get_env()
    template = env.get_template("report.html")

    now = datetime.now(timezone.utc)

    html = template.render(
        title=title,
        badge=badge,
        meta_line=meta_line,
        abstract=abstract_html,
        sections=sections,
        conclusion=conclusion_html,
        year=now.year,
        footer_text=footer_text,
    )

    return html
