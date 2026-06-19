"""Article body conversion and preview helpers.

The admin upload/edit pages accept both rich HTML and Markdown, but the
project stores articles as canonical Markdown. This module keeps that contract
in one place so preview, save, AI revision, and publishing see the same body.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Callable

import markdown as md_lib


MarkdownImageLocalizer = Callable[[object], None]


@dataclass
class PreviewResult:
    """Rendered article preview and the Markdown it was rendered from."""

    html: str
    canonical_markdown: str
    warnings: list[str] = field(default_factory=list)


def looks_like_html_fragment(text: str) -> bool:
    """Return whether text appears to be rich/editor HTML."""
    if not text:
        return False
    return bool(
        re.search(
            r'<(?:div|p|span|h[1-6]|ul|ol|li|blockquote|img|table|section|article|figure|video|iframe)\b',
            text,
            re.I,
        )
    )


def normalize_markdown(markdown_text: str) -> str:
    """Normalize Markdown without changing article meaning."""
    text = (markdown_text or '').replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('&mdash;', '——').replace('&nbsp;', ' ')
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r' {3,}', '  ', text)
    return text.strip()


def _sanitize_rich_html_attrs(soup):
    """Strip clipboard metadata and unsafe attributes before conversion."""
    allowed_attrs = {
        'a': {'href', 'title'},
        'img': {'src', 'alt', 'title', 'width', 'height', 'loading'},
        'iframe': {
            'src', 'title', 'width', 'height', 'allow', 'allowfullscreen',
            'loading', 'referrerpolicy',
        },
        'video': {'src', 'controls', 'poster', 'width', 'height', 'preload'},
        'source': {'src', 'type'},
    }
    for tag in soup.find_all(True):
        tag_allowed = allowed_attrs.get(tag.name, set())
        cleaned = {}
        for key, value in list(tag.attrs.items()):
            lower = key.lower()
            if lower.startswith('on') or lower.startswith('data-') or lower in {
                'style', 'class', 'id', 'name', 'uuid', 'contenteditable',
            }:
                continue
            if lower in tag_allowed:
                cleaned[lower] = value
        if tag.name == 'a' and cleaned.get('href'):
            href = str(cleaned['href']).strip()
            if not href.startswith(('http://', 'https://', '/', '#', 'mailto:')):
                cleaned.pop('href', None)
        tag.attrs = cleaned


def _safe_media_html(tag) -> str:
    """Serialize media tags that Markdown cannot represent well."""
    name = getattr(tag, 'name', '')
    allowed = {
        'iframe': {
            'src', 'title', 'width', 'height', 'allow', 'allowfullscreen',
            'loading', 'referrerpolicy',
        },
        'video': {'src', 'controls', 'poster', 'width', 'height', 'preload'},
        'source': {'src', 'type'},
        'picture': set(),
    }
    if name not in allowed:
        return ''
    for child in tag.find_all(True):
        child_allowed = allowed.get(child.name, set())
        child.attrs = {k: v for k, v in child.attrs.items() if k in child_allowed}
    tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed[name]}
    if name in {'iframe', 'video'}:
        src = tag.get('src', '')
        if src and not src.startswith(('http://', 'https://', '/')):
            return ''
    return str(tag)


def html_to_canonical_markdown(
    html: str,
    *,
    preserve_media: bool = True,
    image_localizer: MarkdownImageLocalizer | None = None,
) -> str:
    """Convert trusted editor HTML into canonical Markdown."""
    if not html:
        return ''
    try:
        from bs4 import BeautifulSoup
        import html2text
    except ImportError:
        return normalize_markdown(html)

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()

    if preserve_media and image_localizer:
        image_localizer(soup)

    _sanitize_rich_html_attrs(soup)

    preserved: list[tuple[str, str]] = []
    if not preserve_media:
        for tag in soup(['img', 'iframe', 'video', 'picture', 'source']):
            tag.decompose()
    else:
        for idx, tag in enumerate(soup.find_all(['iframe', 'video', 'picture']), start=1):
            safe_html = _safe_media_html(tag)
            token = f'RICH_MEDIA_BLOCK_{idx:03d}'
            if safe_html:
                preserved.append((token, safe_html))
                tag.replace_with(soup.new_string(f'\n\n{token}\n\n'))
            else:
                tag.decompose()

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = not preserve_media
    h.ignore_emphasis = False
    markdown_text = h.handle(str(soup))
    for token, media_html in preserved:
        markdown_text = markdown_text.replace(token, media_html)
    return normalize_markdown(markdown_text)


def markdown_to_editor_html(markdown_text: str, *, asset_base: str = '') -> str:
    """Render Markdown into editable HTML for the rich editor."""
    canonical = normalize_markdown(markdown_text)
    if asset_base:
        canonical = canonical.replace('{{ site.baseurl }}', asset_base)
    return md_lib.markdown(canonical, extensions=['extra', 'codehilite', 'toc', 'tables'])


def canonicalize_editor_content(
    content: str,
    content_format: str = 'markdown',
    *,
    preserve_media: bool = True,
    image_localizer: MarkdownImageLocalizer | None = None,
) -> str:
    """Canonicalize editor content regardless of the visible editor mode."""
    fmt = (content_format or 'markdown').strip().lower()
    text = content or ''
    if fmt == 'rich_html' or looks_like_html_fragment(text):
        return html_to_canonical_markdown(
            text,
            preserve_media=preserve_media,
            image_localizer=image_localizer,
        )
    return normalize_markdown(text)


def render_article_preview(
    content: str,
    content_format: str = 'markdown',
    *,
    asset_base: str = '',
    preserve_media: bool = True,
    image_localizer: MarkdownImageLocalizer | None = None,
) -> PreviewResult:
    """Render a save-equivalent preview from any editor mode."""
    canonical = canonicalize_editor_content(
        content,
        content_format,
        preserve_media=preserve_media,
        image_localizer=image_localizer,
    )
    render_source = canonical.replace('{{ site.baseurl }}', asset_base) if asset_base else canonical
    html = md_lib.markdown(render_source, extensions=['extra', 'codehilite', 'toc', 'tables'])
    return PreviewResult(html=html, canonical_markdown=canonical)
