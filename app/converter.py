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


# ── Site-specific content selectors (priority order) ──────────────
# Blogs that wrap the markdown body in a well-known class should be matched
# first; pure <article> is last-resort because it often includes header,
# author bio, comments, and "related articles" side cards.
_MAIN_SELECTORS = [
    '.markdown-body',              # juejin, github, knowledge-base sites
    'article .article-content',    # juejin outer wrapper
    '.article-content',            # generic
    '.post-content',               # wordpress / ghost
    '.entry-content',              # wordpress
    '[class*="RichText"]',         # zhihu
    '[class*="article-body"]',
    '[class*="post-body"]',
    'main article',
    'article',
    'main',
]

_NOISE_ATTR_RE = re.compile(
    r'comment|recommend|sidebar|related|share|toolbar|'
    r'subscribe|signup|author-box|tag-list|nav-|breadcrumb|'
    r'footer|advert|banner|social',
    re.I,
)

# Station-name suffixes to strip from <title>: 'Title - Site' / 'Title | Site'.
_TITLE_SEPARATORS = [' - ', ' — ', ' – ', ' | ', '_', ' · ']


def _clean_title_suffix(title: str) -> str:
    """Strip trailing site-name suffixes like ' - 掘金' / ' | CSDN博客'."""
    title = title.strip()
    for sep in _TITLE_SEPARATORS:
        if sep in title:
            left, right = title.rsplit(sep, 1)
            # Only strip when suffix looks like a site name (short, no sentence).
            if left and 0 < len(right) <= 20 and len(left) >= 4:
                title = left.strip()
    return title


def _extract_title(soup) -> str:
    """Best-effort page title extraction.

    Priority: og:title → twitter:title → JSON-LD headline →
    h1.article-title → article h1 → cleaned <title>. Returns '' when nothing
    meaningful is found so the caller can fall back to ``extract_title(md)``.
    """
    # 1. OpenGraph
    og = soup.find('meta', attrs={'property': 'og:title'})
    if not og:
        og = soup.find('meta', attrs={'name': 'og:title'})
    if og and og.get('content'):
        return og['content'].strip()

    # 2. Twitter card
    tw = (soup.find('meta', attrs={'name': 'twitter:title'})
          or soup.find('meta', attrs={'property': 'twitter:title'}))
    if tw and tw.get('content'):
        return tw['content'].strip()

    # 3. JSON-LD schema.org Article headline (used by juejin, many CMS)
    import json as _json
    for s in soup.find_all('script', type='application/ld+json'):
        raw = (s.string or '').strip()
        if not raw:
            continue
        try:
            data = _json.loads(raw)
        except Exception:
            continue
        candidates = data if isinstance(data, list) else [data]
        for it in candidates:
            if isinstance(it, dict):
                headline = it.get('headline') or it.get('name')
                if headline and isinstance(headline, str):
                    return headline.strip()

    # 4. Article-title h1 by class hint
    h1 = soup.find('h1', class_=re.compile(r'(article|post|entry)[-_ ]?title', re.I))
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    # 5. First h1 inside <article>
    article_tag = soup.find('article')
    if article_tag:
        h = article_tag.find('h1')
        if h and h.get_text(strip=True):
            return h.get_text(strip=True)

    # 6. <title> with site-suffix cleanup
    if soup.title and soup.title.string:
        return _clean_title_suffix(soup.title.string)

    return ''


def _absolutize_urls(node, base_url: str):
    """Rewrite relative href/src to absolute URLs so Markdown links survive.

    Also promotes common lazy-load attributes (``data-src`` / ``data-original``)
    to ``src`` and tags external images with ``referrerpolicy="no-referrer"``
    to defeat hotlink-protected CDNs (e.g. juejin/csdn/zhihu image CDNs).
    """
    from urllib.parse import urljoin
    for a in node.find_all('a', href=True):
        try:
            a['href'] = urljoin(base_url, a['href'])
        except Exception:
            pass
    for img in node.find_all('img'):
        src = (img.get('src') or img.get('data-src')
               or img.get('data-original') or img.get('data-lazy-src'))
        if src:
            try:
                img['src'] = urljoin(base_url, src)
            except Exception:
                img['src'] = src
        # Strip lazy placeholders so html2text emits the real URL
        for k in ('data-src', 'data-original', 'data-lazy-src', 'data-lazy', 'srcset'):
            if k in img.attrs:
                del img.attrs[k]
        # Referrer policy to dodge CDN hotlink protection
        img['referrerpolicy'] = 'no-referrer'


def _extract_main_html(soup, base_url: str) -> str:
    """Return the HTML of the best-guess main content region.

    Strips scripts/styles/nav/footer/comment/recommendation blocks, iterates
    through priority selectors, and picks the first candidate with enough
    textual content (>200 chars) to be a real article.
    """
    # Remove structural noise
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header',
                     'aside', 'form', 'iframe', 'button', 'svg']):
        tag.decompose()
    # Remove noise by class/id naming convention
    for tag in list(soup.find_all(attrs={'class': _NOISE_ATTR_RE})):
        tag.decompose()
    for tag in list(soup.find_all(attrs={'id': _NOISE_ATTR_RE})):
        tag.decompose()

    for sel in _MAIN_SELECTORS:
        try:
            node = soup.select_one(sel)
        except Exception:
            continue
        if node and len(node.get_text(strip=True)) > 200:
            _absolutize_urls(node, base_url)
            return str(node)

    # Fallback: whole body
    body = soup.body or soup
    _absolutize_urls(body, base_url)
    return str(body)


def convert_html_string(html: str, base_url: str = '') -> str:
    """Convert an in-memory HTML string to Markdown.

    Uses site-specific content selectors to isolate the article body. When
    ``base_url`` is supplied, relative links/images are rewritten to absolute
    URLs so the resulting Markdown renders correctly outside the origin.
    """
    try:
        import html2text
    except ImportError:
        raise ImportError('URL 抓取需要 html2text，请执行: pip install html2text')

    cleaned = html
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        cleaned = _extract_main_html(soup, base_url)
    except Exception:
        pass

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = False
    md = h.handle(cleaned)
    # Collapse runs of 3+ blank lines that html2text sometimes emits.
    md = re.sub(r'\n{3,}', '\n\n', md).strip()
    return md


class URLFetchBlocked(Exception):
    """Raised when a URL can't be fetched via plain HTTP.

    Either the domain is on our anti-bot blocklist (pre-check) or the
    response body looks like a JS challenge / login wall (post-check).
    The message is user-facing; the ``suggestion`` field tells the UI how
    to work around it (typically: use baoyu-fetch locally then paste).
    """
    def __init__(self, message: str, suggestion: str = ''):
        super().__init__(message)
        self.suggestion = suggestion


# ── Known anti-bot / login-walled domains ─────────────────────────
# Pure HTTP fetches can't bypass these sites' JS fingerprinting,
# Cloudflare challenges, or auth walls — fail fast with a clear reason
# instead of burning LLM + image-gen credits on garbage HTML.
# Matched against the URL host suffix (e.g. 'm.juejin.cn' → 'juejin.cn').
_BLOCKED_HOSTS = {
    'juejin.cn': '掘金（JS 反爬挑战，纯 HTTP 抓不到正文）',
    'zhihu.com': '知乎（JS 挑战 + 登录墙）',
    'zhuanlan.zhihu.com': '知乎专栏（JS 挑战 + 登录墙）',
    'mp.weixin.qq.com': '微信公众号（环境指纹 + Referer 校验）',
    'weixin.qq.com': '微信（需登录）',
    'xiaohongshu.com': '小红书（登录墙）',
    'x.com': 'X/Twitter（需登录，动态渲染）',
    'twitter.com': 'X/Twitter（需登录，动态渲染）',
    'weibo.com': '微博（登录墙）',
    'douyin.com': '抖音（动态渲染）',
    'bilibili.com': 'B站专栏（动态渲染 + 风控）',
    'csdn.net': 'CSDN（JS 挑战）',
    'jianshu.com': '简书（JS 挑战）',
    'medium.com': 'Medium（付费墙 + JS 挑战）',
}

# Fingerprints of JS-challenge / login-wall responses.
# If the final rendered markdown contains any of these (and is short),
# treat the fetch as failed even if HTTP 200.
_ANTIBOT_MARKERS = (
    'please wait',
    'please enable javascript',
    'enable javascript to continue',
    'just a moment',
    'cf-browser-verification',
    'checking your browser',
    '环境异常',
    '访问验证',
    '滑动验证',
    '请完成安全验证',
)


def _check_blocked_host(url: str) -> None:
    """Pre-flight: raise ``URLFetchBlocked`` if URL is a known anti-bot host.

    Runs BEFORE any network call so the caller can short-circuit the whole
    LLM-rewrite + image-gen pipeline and show a friendly error immediately.
    """
    try:
        from urllib.parse import urlparse
        host = (urlparse(url).hostname or '').lower().lstrip('.')
    except Exception:
        return
    if not host:
        return
    for blocked, reason in _BLOCKED_HOSTS.items():
        # Suffix match so m.juejin.cn / api.juejin.cn both hit juejin.cn.
        if host == blocked or host.endswith('.' + blocked):
            raise URLFetchBlocked(
                f'该站点暂不支持直接抓取：{reason}。',
                suggestion=(
                    '请改用「粘贴内容」标签页：在本机用浏览器打开该链接，'
                    '复制正文后粘贴进来。或在本机终端运行 baoyu-fetch 抓成 '
                    'Markdown 后粘贴。'
                ),
            )


def _looks_like_antibot(md: str) -> bool:
    """Post-flight: detect JS-challenge / login-wall markers in the output."""
    if not md:
        return True
    compact = md.strip()
    # Real articles are virtually never shorter than 200 chars.
    if len(compact) < 200:
        lower = compact.lower()
        if any(m in lower for m in _ANTIBOT_MARKERS):
            return True
        # Extremely short response with no markers is also suspicious,
        # but we don't want false positives on legit micro-posts.
        if len(compact) < 40:
            return True
    return False


def fetch_url_as_markdown(url: str, timeout: int = 30) -> tuple[str, str]:
    """Fetch a URL and convert the HTML body to Markdown.

    Returns ``(markdown, title)``. Uses ``requests`` (gzip/brotli, redirects,
    charset auto-detect) so it handles more real-world pages than the old
    urllib-based implementation.

    Raises ``URLFetchBlocked`` when the domain is a known anti-bot host
    (pre-check, no network call) or when the response body looks like a
    JS-challenge / login-wall page (post-check). Callers should catch
    this to show a friendly error and skip the expensive LLM + image-gen
    pipeline.
    """
    # Pre-check: fail fast on known anti-bot sites before any network call.
    _check_blocked_host(url)

    try:
        import requests
    except ImportError:
        raise ImportError('URL 抓取需要 requests，请执行: pip install requests')

    headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/124.0 Safari/537.36'),
        'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                   'image/avif,image/webp,*/*;q=0.8'),
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Referer': url,
    }
    resp = requests.get(url, headers=headers, timeout=timeout,
                        allow_redirects=True)
    resp.raise_for_status()
    # Let requests infer from Content-Type / apparent_encoding
    if not resp.encoding or resp.encoding.lower() == 'iso-8859-1':
        resp.encoding = resp.apparent_encoding or 'utf-8'
    html = resp.text
    final_url = resp.url or url

    page_title = ''
    try:
        from bs4 import BeautifulSoup
        # Parse once for title; _extract_main_html below mutates its own soup.
        soup = BeautifulSoup(html, 'html.parser')
        page_title = _extract_title(soup)
    except Exception:
        pass

    md = convert_html_string(html, base_url=final_url)

    # Post-check: did the page serve us a JS challenge / login wall?
    if _looks_like_antibot(md):
        raise URLFetchBlocked(
            '抓取到的内容疑似反爬挑战页或登录墙（正文过短/含 JS 校验标记）。',
            suggestion=(
                '请改用「粘贴内容」标签页：在本机浏览器打开链接复制正文后粘贴，'
                '或用 baoyu-fetch 本地抓取后粘贴。'
            ),
        )

    if not page_title:
        page_title = extract_title(md)
    # Final safety: strip site suffix if we fell back to <title>
    page_title = _clean_title_suffix(page_title) if page_title else page_title
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
