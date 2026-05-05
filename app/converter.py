"""File conversion pipeline: PDF, DOCX, HTML → Markdown."""
import os
import re
import tempfile


def convert_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF with basic structure detection."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return _fallback_read(file_path, 'PDF')

    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            if block['type'] != 0:  # skip images
                continue
            for line_data in block.get('lines', []):
                line_text = ''.join(span['text'] for span in line_data['spans']).strip()
                if not line_text:
                    continue
                # Detect headings by font size
                max_size = max((span['size'] for span in line_data['spans']), default=0)
                if max_size >= 18:
                    line_text = f'# {line_text}'
                elif max_size >= 14:
                    line_text = f'## {line_text}'
                elif max_size >= 12 and len(line_text) < 80 and line_text == line_text.strip():
                    # Possibly a sub-heading if short and medium-sized
                    bold = any(span.get('flags', 0) & 2 for span in line_data['spans'])
                    if bold:
                        line_text = f'### {line_text}'
                text_parts.append(line_text)
        text_parts.append('')  # page break
    doc.close()
    return '\n'.join(text_parts)


def _clean_markdown_formatting(text: str) -> str:
    """Strip excessive bold/italic wrappers from converted markdown.

    mammoth + html2text often produces **_text_** or ** _text_** patterns
    when the source Word doc uses bold+italic styling throughout.
    """
    import re
    # Strip patterns like **_text_** or ** _text_ ** (bold+italic wrappers)
    text = re.sub(r'\*\*\s*_([^_]+?)_\s*\*\*', r'\1', text)
    # Strip standalone bold wrappers **text**
    text = re.sub(r'\*\*([^*]+?)\*\*', r'\1', text)
    # Clean up leftover double-spaces
    text = re.sub(r'  +', ' ', text)
    return text


def convert_docx(file_path: str) -> str:
    """Convert DOCX to Markdown via mammoth → html2text."""
    try:
        import mammoth
        import html2text
    except ImportError:
        return _fallback_read(file_path, 'DOCX')

    with open(file_path, 'rb') as f:
        result = mammoth.convert_to_html(f)
        html = result.value

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = False
    md = h.handle(html)
    # Clean bold/italic formatting artifacts from Word docs
    return _clean_markdown_formatting(md)


def convert_html(file_path: str) -> str:
    """Convert HTML file to Markdown."""
    try:
        import html2text
    except ImportError:
        return _fallback_read(file_path, 'HTML')

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = False
    return h.handle(html)


def convert_html_string(html: str) -> str:
    """Convert an in-memory HTML string to Markdown.

    Tries to extract the main <article>/<main> body first (strips nav, footer,
    scripts, styles). Falls back to full-page conversion when no main region
    is detected.
    """
    try:
        import html2text
    except ImportError:
        raise ImportError('URL 抓取需要 html2text，请执行: pip install html2text')

    cleaned = html
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'aside', 'form']):
            tag.decompose()
        main = soup.find('article') or soup.find('main') or soup.body or soup
        cleaned = str(main)
    except Exception:
        pass

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = False
    return h.handle(cleaned)


def fetch_url_as_markdown(url: str, timeout: int = 30) -> tuple[str, str]:
    """Fetch a URL and convert the HTML body to Markdown.

    Returns ``(markdown, title)``. Raises on network / parse failure so the
    caller can surface a friendly flash message.
    """
    from urllib.request import Request, urlopen
    headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/124.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or 'utf-8'
    try:
        html = raw.decode(charset, errors='replace')
    except LookupError:
        html = raw.decode('utf-8', errors='replace')

    # Extract <title> before stripping
    page_title = ''
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        if soup.title and soup.title.string:
            page_title = soup.title.string.strip()
        # Prefer og:title if present
        og = soup.find('meta', property='og:title')
        if og and og.get('content'):
            page_title = og['content'].strip()
    except Exception:
        pass

    md = convert_html_string(html)
    if not page_title:
        page_title = extract_title(md)
    return md, page_title


def detect_and_convert(file_path: str, ext: str) -> str:
    """Route to correct converter based on file extension."""
    ext = ext.lower().lstrip('.')
    if ext == 'pdf':
        return convert_pdf(file_path)
    elif ext in ('docx', 'doc'):
        return convert_docx(file_path)
    elif ext in ('html', 'htm'):
        return convert_html(file_path)
    elif ext in ('md', 'markdown', 'txt'):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise ValueError(f'Unsupported file format: .{ext}')


def extract_title(markdown_text: str) -> str:
    """Auto-detect title from first # heading or first line.

    Strips markdown formatting and caps at 20 CJK chars / 40 latin chars.
    """
    import re
    raw = ''
    for line in markdown_text.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            raw = line[2:].strip()
            break
        elif line and not line.startswith('#'):
            raw = line
            break
    if not raw:
        return 'Untitled'
    # Strip markdown formatting: **bold**, _italic_, *bold*, __bold__
    raw = re.sub(r'\*\*\s*_?|_?\s*\*\*', '', raw)
    raw = re.sub(r'__|[*_]', '', raw)
    raw = raw.strip()
    # Truncate at first sentence boundary within 64 chars
    if len(raw) > 64:
        for punct in ['。', '！', '？', '，', '、', '；', '.', '!', '?', ',', ' ']:
            idx = raw.rfind(punct, 20, 64)  # between 20-64 chars
            if idx > 0:
                return raw[:idx]
        return raw[:64]
    return raw or 'Untitled'


def _fallback_read(file_path: str, fmt: str) -> str:
    """Fallback when conversion libraries not installed."""
    raise ImportError(f'{fmt} 转换需要额外的库，请执行: pip install PyMuPDF mammoth html2text')
