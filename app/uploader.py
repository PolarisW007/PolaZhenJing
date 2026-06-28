"""Upload and article management blueprint."""
import base64
import binascii
import ipaddress
import os
import re
import socket
import subprocess
import tempfile
import json
import hashlib
import logging
import shutil
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

import markdown as md_lib
from werkzeug.utils import secure_filename

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for, current_app)

from .article_content import (
    canonicalize_editor_content,
    html_to_canonical_markdown,
    looks_like_html_fragment,
    markdown_to_editor_html,
    normalize_markdown,
    render_article_preview,
)
from .article_ai import (
    REWRITE_RATE_DEFAULT,
    REWRITE_RATE_PRESETS,
    parse_rewrite_rate,
    rewrite_rate_instruction,
    rewrite_temperature,
)
from .article_repository import (
    article_admin_filename as repo_article_admin_filename,
    load_post,
    parse_post as repo_parse_post,
    safe_post_path as repo_safe_post_path,
    write_post,
)
from .auth import login_required
from .converter import (_clean_markdown_formatting, detect_and_convert, extract_title,
                        fetch_url_as_markdown, URLFetchBlocked)
from .insight_topics import build_upload_prefill, get_topic
from git_safety import GitSafetyError, guarded_commit_and_push
from . import get_db, jobs

logger = logging.getLogger(__name__)

uploader_bp = Blueprint('uploader', __name__, url_prefix='/admin')
public_articles_bp = Blueprint('public_articles', __name__)

STYLES = [
    {'id': 'deep-technical', 'name': '深度技术', 'color': '#1a1a2e',
     'desc': '代码密集，技术深度。灵感来源：Andrej Karpathy。'},
    {'id': 'academic-insight', 'name': '学术洞察', 'color': '#2d6a4f',
     'desc': '学术风格，引用丰富。灵感来源：Yann LeCun。'},
    {'id': 'industry-vision', 'name': '产业视野', 'color': '#e63946',
     'desc': '大胆观点，行业趋势。灵感来源：李开复。'},
    {'id': 'friendly-explainer', 'name': '亲和讲解', 'color': '#f4a261',
     'desc': '温暖亲切，通俗易懂。灵感来源：数字生命卡兹克。'},
    {'id': 'creative-visual', 'name': '创意视觉', 'color': '#7b2cbf',
     'desc': '视觉叙事，富媒体。灵感来源：Jim Fan。'},
    {'id': 'literary-narrative', 'name': '耕烟煮云', 'color': '#5c6b73',
     'desc': '文学叙事，诗意笔法。灵感来源：陈春成。'},
]

THEMES = [
    {'id': 'wukong', 'name': '黑金', 'color': '#E4BF7A',
     'desc': '暗色背景 + 金色点缀，高端大气。'},
    {'id': 'claude', 'name': '书卷', 'color': '#875932',
     'desc': '暖色米底 + 棕色文字，古典书卷。'},
    {'id': 'pmframe', 'name': '科技', 'color': '#1a7a4a',
     'desc': '极简暖白 + 分类色彩，现代科技。'},
]

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
DRAFT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'drafts')
THEME_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'theme.json')
ALLOWED_EXT = {'md', 'markdown', 'txt', 'pdf', 'docx', 'doc', 'html', 'htm'}
ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'webp'}
RICH_MEDIA_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', 'richtext')
MAX_REMOTE_IMAGE_BYTES = 8 * 1024 * 1024
REMOTE_IMAGE_TIMEOUT = 8
REMOTE_IMAGE_CONTENT_TYPES = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
}
SHARE_IMAGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', 'share')
SHARE_IMAGE_URL_PREFIX = '/assets/images/share'
SHARE_IMAGE_PRESETS = {
    'wechat': {'suffix': 'wechat', 'size': (300, 300), 'quality': 86},
    'og': {'suffix': 'og', 'size': (1200, 630), 'quality': 88},
}
WECHAT_TICKET_CACHE = {
    'access_token': '',
    'access_token_expires_at': 0,
    'jsapi_ticket': '',
    'jsapi_ticket_expires_at': 0,
}


def _get_theme() -> str:
    """Read current UI theme from data/theme.json. Default: wukong."""
    try:
        if os.path.isfile(THEME_FILE):
            with open(THEME_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('theme', 'wukong')
    except Exception:
        pass
    return 'wukong'


def _is_admin_session() -> bool:
    """Return whether the current session is allowed to see admin controls."""
    return session.get('role') == 'admin'


def _article_asset_base() -> str:
    """Return the URL prefix for article-owned assets.

    Public article pages can be exposed at root /articles/... while the
    generated/uploaded media is served by the PolaZhenjing app prefix.
    """
    return request.script_root or '/PolaZhenjing'


def _polazhenjing_admin_url(endpoint: str, **values) -> str:
    """Build admin URLs that stay under the deployed PolaZhenjing prefix.

    Root-domain public article pages are also served at /articles/... where
    Flask has no SCRIPT_NAME. Plain url_for() would then produce /admin/...
    links, which bypass the production app prefix and break admin actions.
    """
    path = url_for(endpoint, **values)
    if path == '/admin' or path.startswith('/admin/'):
        return f'/PolaZhenjing{path}'
    return path


def _set_theme(theme_id: str):
    """Persist selected UI theme to data/theme.json."""
    os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
    with open(THEME_FILE, 'w', encoding='utf-8') as f:
        json.dump({'theme': theme_id}, f)


@uploader_bp.app_context_processor
def inject_theme():
    """Make current_theme available to all templates."""
    return {'current_theme': _get_theme()}

# Style accent colors for summary box theming
STYLE_ACCENTS = {
    'deep-technical': '#8b9dc3',
    'academic-insight': '#52b788',
    'industry-vision': '#e63946',
    'friendly-explainer': '#f4a261',
    'creative-visual': '#b68efc',
    'literary-narrative': '#8a9ba8',
}

# ── Skill-based LLM rewriting ──────────────────────────────────────
# Map style IDs to their writer skill system prompts.
# When a style has a skill, the raw content is rewritten by the LLM.

_POLA_NICE_WRITER_PROMPT = """你正在以「炽驹Polaris」的身份写一篇公众号长文。

炽驹Polaris是一个关注AI与技术前沿的内容创作者，文风师法陈春成，追求在科技叙事中注入文学的肌理与诗意。风格一句话概括：「用写小说的笔法，讲这个时代正在发生的事。」

核心价值观：万物皆可入梦，文字应当有自己的光泽，真诚地面对困惑，有所不为。

风格内核：
- 语言的质地：追求每一个句子都有触感，在现代汉语中混入古典的骨骼
- 意象思维：不直接说结论，找到意象来承载感受，一篇文章有一个贯穿全文的核心意象
- 虚实交织：在论述中插入虚构场景、想象的对话，让文章获得梦的质地
- 节奏如呼吸：句子长短交替像呼吸一样自然，段落之间留白
- 通感与联觉：打通不同感官界限，代码的气味，算法的触感
- 克制的抒情：情感浓烈但表达克制，用画面传递情绪
- 时间的褶皱：叙事中折叠时间，制造纵深感
- 回环结构：结尾回到开头的意象
- 留白与省略：不把话说满
- 私人视角：用「我想起了」「我总觉得」连接个人记忆和公共议题

绝对禁区：
- 禁用套话：首先其次最后、综上所述、值得注意的是、让我们来看看
- 不使用冒号「：」用逗号代替，不使用破折号「——」，不使用双引号用「」
- 禁用词：说白了、意味着什么、本质上、换句话说、不可否认、震撼、赋能、助力、打造
- 禁止直白抒情，禁止教科书式开头

开头从具体画面或意象切入。文章4000-8000字，段落长短交替，不加小标题像散文流动。

固定尾部：
以上，既然看到这里了，如果觉得不错，随手点个赞、在看、转发三连吧，如果想第一时间收到推送，也可以给我个星标⭐～
谢谢你读到这里。下次见。
> / 作者：炽驹Polaris
> / 投稿或爆料，请联系邮箱：wsyxjer@gmail.com"""

_KHAZIX_WRITER_PROMPT = """你正在以「数字生命卡兹克」的身份写一篇公众号长文。

卡兹克（Khazix）是一个在AI行业深耕三年的内容创作者和创业者，运营着公众号「数字生命卡兹克」。风格一句话概括："有见识的普通人在认真聊一件打动他的事。"

核心价值观：永远对世界保持好奇，讲人话像个活人，真诚是唯一的捷径，有所为有所不为。

风格内核：
- 节奏感：像跟朋友聊天，句子时长时短，大量逗号制造口语停顿，一句话自成一段制造重点
- 论述中故意打破：口语打断来破坏严谨性，让论述有温度
- 知识输出方式：聊着聊着顺手掏出来，不是来给大家科普
- 私人视角：从自己真实经历切入
- 判断力：敢下判断，但以承认被影响的姿态表达
- 情绪表达：用。。。表示语气拖长，会自嘲，直接表达兴奋
- 亲自下场：让读者感觉到这个人真的做了这件事
- 文化升维：聊完具体事情后连接到更大的文化哲学历史参照物
- 句式断裂：极短句子独立成段制造重量感
- 回环呼应（契诃夫之枪）：前面埋的细节后面都得响
- 谦逊铺垫法：给出建议前先用自谦的话降低防御心

推荐口语化词组：坦率的讲、说真的、怎么说呢、其实吧、你想想看、这玩意、不是哥们、太牛逼了

绝对禁区：
- 禁用套话：首先其次最后、综上所述、值得注意的是
- 不使用冒号用逗号代替，不使用破折号，不使用双引号用「」
- 禁用词：说白了、意味着什么、本质上、换句话说、不可否认
- 禁止假设性例子，禁止教科书式开头

开头永远从具体当下事件切入。文章4000-8000字，段落要短，很多时候一句话就是一段。

固定尾部：
以上，既然看到这里了，如果觉得不错，随手点个赞、在看、转发三连吧，如果想第一时间收到推送，也可以给我个星标⭐～
谢谢你看我的文章，我们，下次再见。
> / 作者：卡兹克
> / 投稿或爆料，请联系邮箱：wzglyay@virxact.com"""

STYLE_SKILL_MAP = {
    'literary-narrative': _POLA_NICE_WRITER_PROMPT,
    'friendly-explainer': _KHAZIX_WRITER_PROMPT,
}

# Generic LLM rewrite prompt for styles without a dedicated writer skill.
# Cleans up formatting, adds section headings, and restructures content.
_GENERIC_REWRITE_PROMPT = """你是一个专业的内容编辑。请对以下素材进行整理和优化：

1. 给文章加上清晰的段落标题（用 ## 标记），使结构一目了然
2. 清理格式问题（多余的加粗、斜体、空行等）
3. 保持原文的核心观点和数据不变，不要添加新内容
4. 语言流畅自然，段落之间过渡顺畅
5. 如果内容是技术类，保留代码示例和技术细节
6. 文章开头用一段引人入胜的导语概括全文

输出纯 Markdown 格式，不要输出任何解释说明。"""

def _get_style_prompt(style: str) -> str | None:
    """Get the LLM prompt for a given style.

    Returns dedicated writer prompt if available, otherwise generic prompt.
    """
    return STYLE_SKILL_MAP.get(style, _GENERIC_REWRITE_PROMPT)

MINIMAX_API_URL = 'https://api.minimax.chat/v1/chat/completions'
MINIMAX_MODEL = 'MiniMax-M3'

# ── MiniMax Text-to-Image (Ghibli-style illustrations) ──────────────
# T2I endpoint. The API key domain must match this URL:
#   - Mainland (official, recommended): https://api.minimaxi.com/v1/image_generation
#   - International:                    https://api.minimax.io/v1/image_generation
# The legacy https://api.minimax.chat/... endpoint no longer exposes
# image_generation and was silently returning failures, which is why every
# recent article ended up without illustrations. Override via MINIMAX_IMAGE_URL
# if the key was registered on a different portal.
MINIMAX_IMAGE_URL = os.environ.get(
    'MINIMAX_IMAGE_URL', 'https://api.minimaxi.com/v1/image_generation'
)
MINIMAX_IMAGE_MODEL = os.environ.get('MINIMAX_IMAGE_MODEL', 'image-01')

# Locked global illustration style: Studio Ghibli. Applied to every article.
GHIBLI_STYLE_PROMPT = (
    'Studio Ghibli-inspired classic Japanese hand-drawn animation atmosphere, '
    'hand-drawn watercolor textures, soft natural lighting, '
    'dreamy pastoral atmosphere, warm color palette, '
    'delicate linework, cinematic composition, highly detailed, '
    'no text, no watermark, no logo'
)


def _get_minimax_api_key() -> str | None:
    """Read MINIMAX_TOKEN_PLAN_API_KEY from environment (.env or system env)."""
    return os.environ.get('MINIMAX_TOKEN_PLAN_API_KEY') or None


def _parse_rewrite_rate(value, default: int = REWRITE_RATE_DEFAULT) -> int:
    """Normalize upload rewrite rate to one of the supported presets."""
    return parse_rewrite_rate(value, default=default)


def _form_flag(value) -> bool:
    """Parse HTML form truthy values without accepting arbitrary text."""
    return str(value or '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _rewrite_rate_instruction(rewrite_rate: int) -> str:
    """Return the prompt contract for the selected rewrite strength."""
    return rewrite_rate_instruction(rewrite_rate)


def _call_llm_rewrite(content: str, title: str, system_prompt: str,
                      revision_instruction: str = '',
                      rewrite_rate: int = REWRITE_RATE_DEFAULT) -> str | None:
    """Call MiniMax LLM to rewrite content using the given skill prompt.

    Returns rewritten content string, or None on failure.
    """
    rewrite_rate = _parse_rewrite_rate(rewrite_rate)
    if rewrite_rate <= 0:
        return None

    api_key = _get_minimax_api_key()
    if not api_key:
        logger.warning('MINIMAX_TOKEN_PLAN_API_KEY not found, skipping LLM rewrite')
        return None

    instruction = (revision_instruction or '').strip()
    instruction_text = (
        f'\n\n额外修改建议：\n{instruction}\n\n请在不改变事实和核心主题的前提下，优先落实这些修改建议。'
        if instruction else ''
    )
    rewrite_contract = _rewrite_rate_instruction(rewrite_rate)
    if rewrite_rate >= 100:
        task_intro = '请根据以下素材，以你的风格写一篇公众号长文。'
    else:
        task_intro = '请根据以下素材，在指定 AI 改写率边界内编辑文章。'
    user_msg = (
        f'{task_intro}{rewrite_contract}'
        f'如果素材是个人博客/技术解读，保留原文的代码例子、术语和数据。'
        f'标题是「{title}」，保持标题与正文语义一致。'
        f'{instruction_text}\n\n'
        f'素材内容：\n{content}'
    )

    payload = json.dumps({
        'model': MINIMAX_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_msg},
        ],
        'temperature': rewrite_temperature(rewrite_rate),
        'max_tokens': 16000,
    }, ensure_ascii=False).encode('utf-8')

    req = Request(MINIMAX_API_URL, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')

    try:
        with urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        raw = data['choices'][0]['message']['content']
        # Strip <think>...</think> reasoning tokens from reasoning models
        cleaned = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        return cleaned or raw
    except Exception as e:
        logger.error('LLM rewrite failed: %s', e)
        if hasattr(e, 'read'):
            try:
                logger.error('Error body: %s', e.read().decode('utf-8')[:500])
            except Exception:
                pass
        return None


def _call_minimax_t2i(prompt: str, aspect_ratio: str = '16:9') -> bytes | None:
    """Call MiniMax text-to-image API and return image bytes, or None on failure.

    Uses ``response_format='base64'`` per the official example so the bytes are
    returned inline and we avoid a second network hop that can fail (temporary
    URLs expire in 24h and are sometimes blocked by corporate networks).
    Falls back to the ``image_urls`` path for backward compatibility.
    """
    api_key = _get_minimax_api_key()
    if not api_key:
        logger.warning('MINIMAX_TOKEN_PLAN_API_KEY not found, skipping illustration')
        return None

    payload = json.dumps({
        'model': MINIMAX_IMAGE_MODEL,
        'prompt': prompt,
        'aspect_ratio': aspect_ratio,
        'response_format': 'base64',
        'n': 1,
        # Keep disabled so article-specific visual metaphors are not normalized
        # into generic clouds/grassland by the optimizer.
        'prompt_optimizer': False,
    }, ensure_ascii=False).encode('utf-8')

    req = Request(MINIMAX_IMAGE_URL, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')

    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logger.error('MiniMax T2I request failed (%s): %s', MINIMAX_IMAGE_URL, e)
        if hasattr(e, 'read'):
            try:
                logger.error('Error body: %s', e.read().decode('utf-8')[:800])
            except Exception:
                pass
        return None

    d = data.get('data') or {}

    # Preferred: base64-encoded image bytes straight from the API
    base64_list = d.get('image_base64') or []
    if isinstance(base64_list, list) and base64_list:
        try:
            import base64
            return base64.b64decode(base64_list[0])
        except Exception as e:
            logger.error('Failed to decode base64 image: %s', e)

    # Fallback: signed URL (legacy response shape)
    urls: list = d.get('image_urls') or d.get('urls') or []
    if not urls and isinstance(data.get('images'), list):
        urls = [x.get('url') for x in data['images'] if isinstance(x, dict) and x.get('url')]
    if not urls:
        logger.error('MiniMax T2I returned no image data: %s', str(data)[:800])
        return None
    try:
        with urlopen(urls[0], timeout=60) as img_resp:
            return img_resp.read()
    except Exception as e:
        logger.error('Failed to download generated image from %s: %s', urls[0], e)
        return None


def _strip_markdown_noise(text: str) -> str:
    """Remove markdown syntax that hurts visual planning."""
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    text = re.sub(r'\[[^\]]+\]\([^)]+\)', lambda m: m.group(0).split('](')[0].lstrip('['), text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'[#>*_~|-]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _extract_visual_blocks(content: str, min_blocks: int = 3,
                           max_blocks: int = 5) -> list[dict]:
    """Pick 3-5 meaningful article paragraphs for paragraph illustrations."""
    raw_blocks = re.split(r'\n\s*\n+', content.strip())
    candidates: list[dict] = []
    fallback_candidates: list[dict] = []
    for block_index, block in enumerate(raw_blocks):
        clean = _strip_markdown_noise(block)
        if len(clean) < 45:
            if len(clean) >= 24 and not clean.startswith('!['):
                fallback_candidates.append({
                    'block_index': block_index,
                    'excerpt': clean[:420],
                })
            continue
        if any(kw in clean for kw in ['点个赞', '在看', '转发', '星标', '联系邮箱', '作者：']):
            continue
        # Prefer argument paragraphs over code/list debris.
        cjk_count = sum(1 for ch in clean if '\u4e00' <= ch <= '\u9fff')
        if cjk_count < 24:
            continue
        candidates.append({
            'block_index': block_index,
            'excerpt': clean[:420],
        })

    if len(candidates) < min_blocks:
        seen = {item['block_index'] for item in candidates}
        for item in fallback_candidates:
            if item['block_index'] not in seen:
                candidates.append(item)
                seen.add(item['block_index'])
            if len(candidates) >= min_blocks:
                break

    if not candidates:
        clean = _strip_markdown_noise(content)
        return [{'block_index': 0, 'excerpt': clean[:420] or '文章核心观点'}]

    if len(candidates) < min_blocks:
        whole = _strip_markdown_noise(content)
        for idx in range(len(candidates), min_blocks):
            start = min(len(whole), idx * 260)
            excerpt = whole[start:start + 420] or whole[:420] or '文章核心观点'
            candidates.append({'block_index': idx, 'excerpt': excerpt})

    target_count = min(max_blocks, max(min_blocks, len(candidates)))
    if len(candidates) <= target_count:
        return candidates
    if target_count <= 1:
        return [candidates[len(candidates) // 2]]

    # Spread selected blocks across the article so scenes map to different beats.
    selected = []
    used = set()
    for i in range(target_count):
        idx = round(i * (len(candidates) - 1) / (target_count - 1))
        while idx in used and idx + 1 < len(candidates):
            idx += 1
        used.add(idx)
        selected.append(candidates[idx])
    return selected


def _article_visual_source(title: str, content: str, max_chars: int = 2800) -> str:
    """Build compact article context for visual-brief LLM."""
    blocks = [_strip_markdown_noise(b) for b in re.split(r'\n\s*\n+', content)]
    blocks = [b for b in blocks if len(b) >= 35]
    source = f'标题：{title}\n\n' + '\n\n'.join(blocks[:18])
    return source[:max_chars]


def _call_visual_brief_llm(title: str, content: str,
                           visual_blocks: list[dict]) -> dict | None:
    """Ask LLM to turn article arguments into concrete image prompts."""
    api_key = _get_minimax_api_key()
    if not api_key:
        return None

    block_lines = '\n'.join(
        f'{i + 1}. block_index={item["block_index"]}: {item["excerpt"]}'
        for i, item in enumerate(visual_blocks)
    )
    user_msg = f"""请为一篇中文文章生成插画规划。要求：
1. 题图必须提取整篇文章的核心观点，生成一个有明确人物、物件、场景和隐喻的场景图，不要只画天空、草地、云。
2. 段落图必须分别对应下面 3-5 个核心段落，每张图都要明显不同。
3. 风格统一为吉卜力动画电影感、水彩质感、自然光，但画面主体必须由文章内容决定。
4. 不要出现文字、logo、水印、界面截图。
5. 只输出 JSON，不要解释。

JSON 格式：
{{
  "cover": {{"alt": "...", "prompt": "..."}},
  "scenes": [
    {{"block_index": 0, "alt": "...", "prompt": "..."}}
  ]
}}

文章内容：
{_article_visual_source(title, content)}

核心段落：
{block_lines}
"""
    payload = json.dumps({
        'model': MINIMAX_MODEL,
        'messages': [
            {'role': 'system', 'content': '你是视觉编辑，擅长把文章观点转成具体电影场景。'},
            {'role': 'user', 'content': user_msg},
        ],
        'temperature': 0.45,
        'max_tokens': 5000,
    }, ensure_ascii=False).encode('utf-8')

    req = Request(MINIMAX_API_URL, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')

    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        raw = data['choices'][0]['message']['content']
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        match = re.search(r'\{.*\}', raw, flags=re.DOTALL)
        plan = json.loads(match.group(0) if match else raw)
        if isinstance(plan, dict) and isinstance(plan.get('cover'), dict):
            return plan
    except Exception as e:
        logger.error('Visual brief LLM failed: %s', e)
    return None


def _fallback_visual_plan(title: str, content: str,
                          visual_blocks: list[dict]) -> dict:
    """Create content-specific prompts without an extra LLM call."""
    summary = _generate_summary(content, max_chars=260) or title
    scenes = []
    for item in visual_blocks:
        excerpt = item['excerpt']
        scenes.append({
            'block_index': item['block_index'],
            'alt': f'{title} — 段落图',
            'prompt': (
                f'Create a concrete cinematic scene inspired by this article paragraph: '
                f'{excerpt}. Show symbolic characters, tools, places, and tension from '
                f'the paragraph. Avoid generic empty landscapes.'
            ),
        })
    return {
        'cover': {
            'alt': f'{title} — 题图',
            'prompt': (
                f'Create a cinematic cover scene for the article "{title}". '
                f'Core thesis: {summary}. Use concrete symbolic objects and people '
                f'that represent the thesis. Avoid generic grass hills or empty clouds.'
            ),
        },
        'scenes': scenes,
    }


def _compose_image_prompt(base_prompt: str) -> str:
    """Combine article-specific prompt with the global Ghibli style lock."""
    return (
        f'{base_prompt.strip()}\n'
        f'Visual requirements: {GHIBLI_STYLE_PROMPT}. '
        f'Make the subject specific to the article, visually distinct from other scenes.'
    )


def _generate_illustrations(title: str, content: str, slug: str, project_root: str) -> list[dict]:
    """Generate 1 cover + 3-5 paragraph scene Ghibli-style illustrations.

    Saves PNG files under ``assets/images/generated/<slug>/`` and returns a list
    of dicts ``[{'role': 'cover'|'scene', 'relpath': 'assets/images/…', 'alt': …}]``.
    On any failure (no API key, network error) returns an empty list — the
    article is then written without images. Individual scene failures do not
    abort the whole batch; the caller will inject whatever survived.
    """
    visual_blocks = _extract_visual_blocks(content, min_blocks=3, max_blocks=5)
    plan = _call_visual_brief_llm(title, content, visual_blocks)
    if not plan:
        plan = _fallback_visual_plan(title, content, visual_blocks)

    out_dir_rel = os.path.join('assets', 'images', 'generated', slug)
    out_dir_abs = os.path.join(project_root, out_dir_rel)
    os.makedirs(out_dir_abs, exist_ok=True)
    try:
        with open(os.path.join(out_dir_abs, 'visual-plan.json'), 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning('Failed to write visual plan: %s', e)

    jobs_spec = []
    cover = plan.get('cover') or {}
    cover_prompt = cover.get('prompt') or _fallback_visual_plan(title, content, visual_blocks)['cover']['prompt']
    jobs_spec.append({
        'role': 'cover',
        'prompt': _compose_image_prompt(cover_prompt),
        'aspect': '16:9',
        'fname': 'cover.png',
        'alt': cover.get('alt') or f'{title} — 题图',
        'block_index': None,
    })

    plan_scenes = plan.get('scenes') if isinstance(plan.get('scenes'), list) else []
    fallback_scenes = _fallback_visual_plan(title, content, visual_blocks)['scenes']
    if len(plan_scenes) < 3:
        plan_scenes = fallback_scenes
    for idx, scene in enumerate(plan_scenes[:5], start=1):
        if not isinstance(scene, dict):
            continue
        fallback = fallback_scenes[min(idx - 1, len(fallback_scenes) - 1)]
        block_index = scene.get('block_index', fallback.get('block_index', idx - 1))
        try:
            block_index = int(block_index)
        except (TypeError, ValueError):
            block_index = fallback.get('block_index', idx - 1)
        jobs_spec.append({
            'role': 'scene',
            'prompt': _compose_image_prompt(scene.get('prompt') or fallback['prompt']),
            'aspect': '4:3',
            'fname': f'scene-{idx}.png',
            'alt': scene.get('alt') or fallback['alt'],
            'block_index': block_index,
        })

    results: list[dict] = []
    for job in jobs_spec:
        img_bytes = _call_minimax_t2i(job['prompt'], aspect_ratio=job['aspect'])
        if not img_bytes:
            continue
        fpath = os.path.join(out_dir_abs, job['fname'])
        try:
            with open(fpath, 'wb') as f:
                f.write(img_bytes)
        except Exception as e:
            logger.error('Failed to save illustration %s: %s', fpath, e)
            continue
        results.append({
            'role': job['role'],
            'relpath': os.path.join(out_dir_rel, job['fname']).replace(os.sep, '/'),
            'alt': job['alt'],
            'block_index': job['block_index'],
            'prompt': job['prompt'],
        })
    return results


def _image_markdown(img: dict) -> str:
    """Build a Jekyll-safe Markdown image tag."""
    return f'![{img["alt"]}]({{{{ site.baseurl }}}}/{img["relpath"]})'


def _inject_illustrations(content: str, images: list[dict]) -> str:
    """Prepend cover image and distribute scene images through the body.

    Cover goes at the very top. Scene images are spread evenly across the
    article (e.g. 3 scenes → roughly 25% / 50% / 75%), each snapped to the
    next blank line for cleaner placement. Markdown image URLs use the
    Jekyll ``{{ site.baseurl }}`` prefix so they work under the
    ``/PolaZhenjing/`` sub-path on aipd.me.
    """
    if not images:
        return content

    cover = next((i for i in images if i['role'] == 'cover'), None)
    scenes = [i for i in images if i['role'] != 'cover']

    body = content.strip()
    if cover:
        body = _image_markdown(cover) + '\n\n' + body

    if scenes:
        blocks = re.split(r'(\n\s*\n+)', body)
        paragraph_positions = []
        paragraph_index = -1
        for idx, part in enumerate(blocks):
            if not part.strip() or re.match(r'\n\s*\n+', part):
                continue
            if part.strip().startswith('!['):
                continue
            paragraph_index += 1
            paragraph_positions.append((paragraph_index, idx))

        insertions = []
        for fallback_idx, scene in enumerate(scenes):
            target_block = scene.get('block_index')
            try:
                target_block = int(target_block)
            except (TypeError, ValueError):
                target_block = None
            if target_block is None or not paragraph_positions:
                pos_idx = round((fallback_idx + 1) * (len(paragraph_positions) - 1) / (len(scenes) + 1)) if paragraph_positions else len(blocks)
                block_pos = paragraph_positions[pos_idx][1] if paragraph_positions else len(blocks)
            else:
                block_pos = min(paragraph_positions, key=lambda item: abs(item[0] - target_block))[1]
            insertions.append((block_pos + 1, '\n\n' + _image_markdown(scene) + '\n\n'))

        for pos, scene_md in sorted(insertions, reverse=True):
            blocks.insert(pos, scene_md)
        body = ''.join(blocks)

    return body


def _generate_summary(content: str, max_chars: int = 200) -> str:
    """Extract a concise summary from article content.

    Uses extractive approach: picks the first 2-3 meaningful paragraphs,
    skipping very short lines, title echoes, and sign-off boilerplate.
    Future: plug in LLM call with pola-nice-writer prompt for literary style.
    """
    lines = content.strip().split('\n')
    paragraphs = []
    for line in lines:
        line = line.strip()
        # Skip empty, very short, markdown headings, and boilerplate
        if not line or len(line) < 10:
            continue
        if line.startswith('!['):
            continue
        if line.startswith('#') or line.startswith('>'):
            continue
        if any(kw in line for kw in ['点个赞', '在看', '转发', '星标', '下次再见', '联系邮箱', '作者：']):
            continue
        paragraphs.append(line)
    # Join and trim to max_chars at sentence boundary
    joined = ''.join(paragraphs)
    if len(joined) <= max_chars:
        return joined
    # Try to cut at a sentence-ending punctuation
    truncated = joined[:max_chars]
    for punct in ['。', '！', '？', '.', '!', '?']:
        idx = truncated.rfind(punct)
        if idx > max_chars // 2:
            return truncated[:idx + 1]
    return truncated + '…'


def _valid_uploaded_image(file_storage) -> tuple[bool, str]:
    """Validate an optional uploaded illustration."""
    filename = secure_filename(file_storage.filename or '')
    ext = _get_ext(filename)
    if not filename:
        return False, ''
    if ext not in ALLOWED_IMAGE_EXT:
        return False, ext
    return True, ext


def _save_richtext_image(file_storage) -> str:
    """Persist an image pasted into the rich text editor and return asset URL."""
    ok, ext = _valid_uploaded_image(file_storage)
    if not ok:
        raise ValueError(f'不支持的图片类型：.{ext or "unknown"}')

    month = datetime.now().strftime('%Y-%m')
    out_dir = os.path.join(RICH_MEDIA_DIR, month)
    os.makedirs(out_dir, exist_ok=True)

    original = secure_filename(file_storage.filename or f'image.{ext}')
    seed = f'{original}{datetime.now().isoformat()}'.encode('utf-8')
    filename = f'{hashlib.sha256(seed).hexdigest()[:16]}.{ext}'
    out_path = os.path.join(out_dir, filename)
    file_storage.save(out_path)
    return f'{_article_asset_base()}/assets/images/richtext/{month}/{filename}'


def _richtext_image_url_from_bytes(data: bytes, ext: str) -> str:
    """Persist image bytes and return a stable richtext asset URL."""
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError(f'不支持的图片类型：.{ext or "unknown"}')
    if not data or len(data) > MAX_REMOTE_IMAGE_BYTES:
        raise ValueError('图片内容为空或超过大小限制')
    month = datetime.now().strftime('%Y-%m')
    out_dir = os.path.join(RICH_MEDIA_DIR, month)
    os.makedirs(out_dir, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()[:16]
    filename = f'{digest}.{ext}'
    out_path = os.path.join(out_dir, filename)
    if not os.path.isfile(out_path):
        with open(out_path, 'wb') as f:
            f.write(data)
    return f'{_article_asset_base()}/assets/images/richtext/{month}/{filename}'


def _log_remote_image_localization_failure(image_url: str, reason: str):
    """Log remote image localization failures without leaking query strings."""
    try:
        parsed = urlparse(image_url or '')
        host = parsed.netloc or parsed.path[:80]
        current_app.logger.warning('Rich image localization failed for host=%s: %s', host, reason)
    except RuntimeError:
        logger.warning('Rich image localization failed: %s', reason)


def _first_srcset_url(srcset: str) -> str:
    """Return the first URL from an HTML srcset attribute."""
    if not srcset:
        return ''
    first = next((item.strip() for item in srcset.split(',') if item.strip()), '')
    return first.split()[0] if first else ''


def _normalize_remote_image_src(value: str) -> str:
    """Normalize pasted image URL variants before validation/download."""
    src = (value or '').strip().strip('"\'')
    if src.startswith('//'):
        src = f'https:{src}'
    if src.startswith('http://'):
        src = f'https://{src[7:]}'
    return src


def _usable_rich_image_src(tag) -> str:
    """Choose the most useful image source from pasted rich HTML."""
    attrs = [
        'src', 'data-src', 'data-original', 'data-url', 'data-image-src',
        'data-image-url', 'data-media-url', 'data-full-url',
        'data-actualsrc', 'data-actual-src', 'data-lazy-src',
    ]
    for attr in attrs:
        value = _normalize_remote_image_src(tag.get(attr) or '')
        if value and value not in {'#', 'about:blank'}:
            return value
    for attr in ('srcset', 'data-srcset'):
        value = _normalize_remote_image_src(_first_srcset_url(tag.get(attr) or ''))
        if value and value not in {'#', 'about:blank'}:
            return value
    parent = tag.find_parent('picture') if hasattr(tag, 'find_parent') else None
    if parent:
        for source in parent.find_all('source'):
            value = _normalize_remote_image_src(source.get('src') or '')
            if not value:
                value = _normalize_remote_image_src(_first_srcset_url(source.get('srcset') or ''))
            if not value:
                value = _normalize_remote_image_src(_first_srcset_url(source.get('data-srcset') or ''))
            if value and value not in {'#', 'about:blank'}:
                return value
    return ''


def _style_image_urls(style: str) -> list[str]:
    """Extract image URLs from pasted background-image style values."""
    if not style:
        return []
    urls = []
    for match in re.finditer(r'url\((["\']?)(.*?)\1\)', style, re.I):
        src = _normalize_remote_image_src(match.group(2))
        if src:
            urls.append(src)
    return urls


def _looks_like_pasted_content_image_url(image_url: str) -> bool:
    """Avoid turning decorative CSS assets into article images."""
    src = _normalize_remote_image_src(image_url)
    if not src:
        return False
    if src.startswith('data:image/'):
        return True
    parsed = urlparse(src)
    host = (parsed.hostname or '').lower()
    path = (parsed.path or '').lower()
    return (
        host.endswith('twimg.com')
        or path.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))
        or 'format=' in (parsed.query or '').lower()
    )


def _promote_pasted_background_images(soup):
    """Convert content images copied as CSS backgrounds into normal img tags."""
    seen = {
        _usable_rich_image_src(img)
        for img in soup.find_all('img')
        if _usable_rich_image_src(img)
    }
    for tag in list(soup.find_all(True)):
        for src in _style_image_urls(tag.get('style') or ''):
            if not _looks_like_pasted_content_image_url(src) or src in seen:
                continue
            img = soup.new_tag('img')
            img['src'] = src
            img['alt'] = tag.get('aria-label') or tag.get('alt') or '粘贴图片'
            img['loading'] = 'lazy'
            tag.insert_after(img)
            seen.add(src)


def _is_local_article_image_url(image_url: str) -> bool:
    """Return True for local article assets that should not be re-downloaded."""
    value = (image_url or '').strip()
    if not value:
        return False
    if value.startswith(('data:', 'blob:')):
        return False
    if value.startswith('{{ site.baseurl }}'):
        return True
    parsed_path = urlparse(value).path if value.startswith(('http://', 'https://')) else value
    return (
        parsed_path.startswith('/PolaZhenjing/assets/')
        or parsed_path.startswith('/assets/')
        or parsed_path.startswith('assets/')
    )


def _is_public_remote_image_url(image_url: str) -> bool:
    """Validate that a remote image URL resolves to public network addresses."""
    parsed = urlparse(image_url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
    except OSError:
        return False
    if not infos:
        return False
    for info in infos:
        host = info[4][0].split('%', 1)[0]
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
    return True


def _download_remote_image_to_richtext(image_url: str) -> str | None:
    """Download a public remote image into richtext assets and return local URL."""
    image_url = (image_url or '').strip()
    if image_url.startswith('//'):
        image_url = f'https:{image_url}'
    if not _is_public_remote_image_url(image_url):
        return None

    try:
        req = Request(
            image_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PolaZhenJing/1.0; +https://aipd.me/)',
                'Accept': 'image/avif,image/webp,image/png,image/jpeg,image/*,*/*;q=0.8',
            },
        )
        with urlopen(req, timeout=REMOTE_IMAGE_TIMEOUT) as resp:
            final_url = getattr(resp, 'url', image_url)
            if 'noauth' in final_url.lower():
                _log_remote_image_localization_failure(image_url, 'redirected to noAuth image')
                return None
            content_type = (resp.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            ext = REMOTE_IMAGE_CONTENT_TYPES.get(content_type)
            if not ext:
                _log_remote_image_localization_failure(image_url, f'unsupported content type {content_type or "unknown"}')
                return None
            try:
                content_length = int(resp.headers.get('Content-Length') or '0')
            except ValueError:
                content_length = 0
            if content_length > MAX_REMOTE_IMAGE_BYTES:
                _log_remote_image_localization_failure(image_url, 'content length exceeds limit')
                return None
            data = resp.read(MAX_REMOTE_IMAGE_BYTES + 1)
            if len(data) > MAX_REMOTE_IMAGE_BYTES:
                _log_remote_image_localization_failure(image_url, 'download exceeds limit')
                return None
            if not data or b'<html' in data[:512].lower():
                _log_remote_image_localization_failure(image_url, 'response is empty or html')
                return None
            return _richtext_image_url_from_bytes(data, ext)
    except Exception as exc:
        _log_remote_image_localization_failure(image_url, exc.__class__.__name__)
        return None


def _save_data_image_to_richtext(data_url: str) -> str | None:
    """Persist a data:image URL from pasted rich HTML as a local asset."""
    match = re.match(r'^data:(image/(?:png|jpeg|jpg|webp));base64,(.+)$', data_url or '', re.I | re.S)
    if not match:
        return None
    content_type = match.group(1).lower()
    ext = REMOTE_IMAGE_CONTENT_TYPES.get(content_type)
    if not ext:
        return None
    try:
        data = base64.b64decode(match.group(2), validate=True)
        return _richtext_image_url_from_bytes(data, ext)
    except (binascii.Error, ValueError):
        return None


def _localize_rich_html_images(soup):
    """Replace pasted external image URLs with local richtext assets when possible."""
    _promote_pasted_background_images(soup)
    for img in soup.find_all('img'):
        src = _usable_rich_image_src(img)
        if not src:
            img.decompose()
            continue
        src = _normalize_remote_image_src(src)
        if src.startswith('blob:'):
            img.decompose()
            continue
        local_url = None
        if src.startswith('data:image/'):
            local_url = _save_data_image_to_richtext(src)
        elif _is_local_article_image_url(src):
            local_url = src
        elif src.startswith(('http://', 'https://')):
            local_url = _download_remote_image_to_richtext(src)
        if local_url:
            img['src'] = local_url
            img['loading'] = img.get('loading') or 'lazy'
        else:
            img['src'] = src
        for attr in ('srcset', 'data-srcset'):
            img.attrs.pop(attr, None)


def _sanitize_rich_html_attrs(soup):
    """Strip large clipboard metadata and unsafe attributes before markdown conversion."""
    allowed_attrs = {
        'a': {'href', 'title'},
        'img': {'src', 'alt', 'title', 'width', 'height', 'loading'},
        'iframe': {'src', 'title', 'width', 'height', 'allow', 'allowfullscreen',
                   'loading', 'referrerpolicy'},
        'video': {'src', 'controls', 'poster', 'width', 'height', 'preload'},
        'source': {'src', 'srcset', 'type'},
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
    """Serialize a media tag with only the attributes needed for articles."""
    name = getattr(tag, 'name', '')
    allowed = {
        'img': {'src', 'alt', 'title', 'width', 'height', 'loading'},
        'iframe': {'src', 'title', 'width', 'height', 'allow', 'allowfullscreen',
                   'loading', 'referrerpolicy'},
        'video': {'src', 'controls', 'poster', 'width', 'height', 'preload'},
        'source': {'src', 'srcset', 'type'},
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
        if src and not (src.startswith('http://') or src.startswith('https://') or src.startswith('/')):
            return ''
    return str(tag)


def _rich_html_to_markdown(html: str, preserve_media: bool = True) -> str:
    """Convert TinyMCE HTML into canonical Markdown.

    Kept as a compatibility wrapper while the implementation lives in
    app.article_content.
    """
    return html_to_canonical_markdown(
        html,
        preserve_media=preserve_media,
        image_localizer=_localize_rich_html_images if preserve_media else None,
    )


def _looks_like_html_fragment(text: str) -> bool:
    """Detect copied editor HTML that should be converted before generation."""
    return looks_like_html_fragment(text)


def _normalize_pasted_markdown(text: str, preserve_media: bool = True) -> str:
    """Accept real Markdown and accidental copied HTML in the Markdown editor."""
    text = (text or '').strip()
    if _looks_like_html_fragment(text):
        return _rich_html_to_markdown(text, preserve_media=preserve_media)
    return normalize_markdown(text)


_MARKDOWN_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')
_RAW_MEDIA_RE = re.compile(
    r'<(?:img|iframe|video|picture)\b[\s\S]*?</(?:iframe|video|picture)>|<img\b[^>]*>',
    re.IGNORECASE,
)
_LLM_THINK_BLOCK_RE = re.compile(r'<think\b[^>]*>[\s\S]*?</think>', re.IGNORECASE)
_LLM_META_OPENING_RE = re.compile(
    r'^\s*(?:The user wants|I need to|Let me|Looking at the original|We need to|I should)\b',
    re.IGNORECASE,
)


def _strip_markdown_media(content: str) -> str:
    """Remove Markdown and raw-HTML media references from article input."""
    content = _MARKDOWN_IMAGE_RE.sub('', content or '')
    content = _RAW_MEDIA_RE.sub('', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def _extract_markdown_media_blocks(content: str) -> list[str]:
    """Collect original media blocks so generation can keep them after rewrite."""
    if not content:
        return []
    blocks = _MARKDOWN_IMAGE_RE.findall(content)
    blocks.extend(match.group(0) for match in _RAW_MEDIA_RE.finditer(content))
    seen = set()
    unique = []
    for block in blocks:
        cleaned = block.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


def _ensure_original_media(content: str, media_blocks: list[str]) -> str:
    """Append any preserved original media that the LLM rewrite dropped."""
    missing = [block for block in media_blocks if block and block not in content]
    if not missing:
        return content
    return content.rstrip() + '\n\n## 原文媒体\n\n' + '\n\n'.join(missing) + '\n'


def _clean_llm_revision_output(content: str) -> str:
    """Keep only article Markdown from a model revision response."""
    cleaned = _LLM_THINK_BLOCK_RE.sub('', content or '').strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:markdown|md)?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned).strip()
    if _LLM_META_OPENING_RE.match(cleaned[:240]):
        logger.warning('LLM revision looked like model commentary, rejecting output')
        return ''
    return cleaned


def _apply_revision_instruction(content: str, title: str, revision_instruction: str,
                                style: str = '',
                                rewrite_rate: int = 50) -> str | None:
    """Ask the LLM to revise existing Markdown according to a short note."""
    instruction = (revision_instruction or '').strip()
    if not instruction:
        return None
    rewrite_rate = _parse_rewrite_rate(rewrite_rate, default=50)
    if rewrite_rate <= 0:
        return None
    media_blocks = _extract_markdown_media_blocks(content)
    system_prompt = (
        '你是一名资深中文文章编辑。请基于用户的修改建议，对现有 Markdown 文章做二次修改。'
        '必须保留原文事实、数据、专有名词、代码块、Markdown 图片、HTML 媒体标签和 front matter 之外的正文结构。'
        '不要输出解释说明，只输出修改后的 Markdown 正文。不要重复结尾，不要删除图片语法。'
    )
    style_hint = f'文章当前风格是 {style}。' if style else ''
    rewrite_contract = _rewrite_rate_instruction(rewrite_rate)
    user_msg = (
        f'标题：{title}\n'
        f'{style_hint}\n'
        f'{rewrite_contract}\n'
        f'修改建议：\n{instruction}\n\n'
        f'原文 Markdown：\n{content}'
    )
    api_key = _get_minimax_api_key()
    if not api_key:
        logger.warning('MINIMAX_TOKEN_PLAN_API_KEY not found, skipping revision instruction')
        return None
    payload = json.dumps({
        'model': MINIMAX_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_msg},
        ],
        'temperature': rewrite_temperature(rewrite_rate),
        'max_tokens': 16000,
    }).encode('utf-8')
    req = Request(
        MINIMAX_API_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
    )
    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        revised = _clean_llm_revision_output(data['choices'][0]['message']['content'] or '')
        if not revised:
            return None
        return _ensure_original_media(revised, media_blocks)
    except Exception as e:
        logger.warning('LLM revision failed: %s', e)
        return None


def _save_draft_illustrations(draft_id: str, files) -> list[dict]:
    """Persist user-supplied article illustrations alongside the draft."""
    saved: list[dict] = []
    image_files = [f for f in files if getattr(f, 'filename', '')]
    if not image_files:
        return saved

    image_dir = os.path.join(DRAFT_DIR, f'{draft_id}_images')
    os.makedirs(image_dir, exist_ok=True)
    for idx, f in enumerate(image_files, start=1):
        ok, ext = _valid_uploaded_image(f)
        if not ok:
            logger.warning('Skipped unsupported uploaded illustration: %s', f.filename)
            continue
        original_name = secure_filename(f.filename) or f'illustration-{idx}.{ext}'
        stored_name = f'illustration-{idx:02d}.{ext}'
        stored_path = os.path.join(image_dir, stored_name)
        f.save(stored_path)
        saved.append({
            'filename': original_name,
            'path': stored_path,
            'ext': ext,
            'index': idx,
        })
    return saved


def _copy_with_watermark_cleanup(src: str, dst: str) -> dict:
    """Copy an uploaded image, conservatively softening likely edge watermarks.

    The remover only touches small high-contrast clusters near the four edges.
    If no confident watermark-like region is found, the file is copied byte for
    byte so the original visual details remain unchanged.
    """
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFilter
    except Exception:
        shutil.copy2(src, dst)
        return {'status': 'copied', 'changed': False, 'reason': 'pillow_unavailable'}

    try:
        with Image.open(src) as im:
            im.load()
            work = im.convert('RGBA')
            w, h = work.size
            if w < 160 or h < 120:
                shutil.copy2(src, dst)
                return {'status': 'copied', 'changed': False, 'reason': 'image_too_small'}

            corners = [
                (0, 0, int(w * 0.36), int(h * 0.22)),
                (int(w * 0.64), 0, w, int(h * 0.22)),
                (0, int(h * 0.78), int(w * 0.36), h),
                (int(w * 0.64), int(h * 0.78), w, h),
            ]
            gray = work.convert('L')
            watermark_mask = Image.new('L', (w, h), 0)
            changed = False

            for box in corners:
                crop = gray.crop(box)
                blurred = crop.filter(ImageFilter.GaussianBlur(5))
                diff = ImageChops.difference(crop, blurred)
                # High local contrast often captures small text/logo overlays.
                candidate = diff.point(lambda px: 255 if px > 34 else 0)
                bbox = candidate.getbbox()
                if not bbox:
                    continue
                count = sum(1 for px in candidate.getdata() if px)
                density = count / float(candidate.size[0] * candidate.size[1])
                if density < 0.002 or density > 0.12:
                    continue
                left, top, right, bottom = bbox
                abs_box = (
                    max(0, box[0] + left - 10),
                    max(0, box[1] + top - 10),
                    min(w, box[0] + right + 10),
                    min(h, box[1] + bottom + 10),
                )
                ImageDraw.Draw(watermark_mask).rectangle(abs_box, fill=220)
                changed = True

            if not changed:
                shutil.copy2(src, dst)
                return {'status': 'copied', 'changed': False, 'reason': 'no_confident_watermark'}

            # Feather the mask and borrow nearby texture through a local median
            # filter. This avoids resizing, recoloring, or changing the rest.
            mask = watermark_mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(7))
            softened = work.filter(ImageFilter.MedianFilter(9))
            cleaned = Image.composite(softened, work, mask)

            clean_ext = _get_ext(dst)
            if clean_ext in {'jpg', 'jpeg'}:
                cleaned = cleaned.convert('RGB')
                cleaned.save(dst, quality=95, subsampling=0)
            else:
                cleaned.save(dst)
            return {'status': 'cleaned', 'changed': True, 'reason': 'edge_watermark_candidate'}
    except Exception as e:
        logger.warning('Watermark cleanup failed for %s: %s', src, e)
        shutil.copy2(src, dst)
        return {'status': 'copied', 'changed': False, 'reason': 'cleanup_failed'}


def _prepare_uploaded_illustrations(uploaded: list[dict], title: str, content: str,
                                    slug: str, project_root: str) -> list[dict]:
    """Move draft illustrations into article assets and assign body anchors."""
    if not uploaded:
        return []

    out_dir_rel = os.path.join('assets', 'images', 'uploads', slug)
    out_dir_abs = os.path.join(project_root, out_dir_rel)
    originals_abs = os.path.join(out_dir_abs, 'originals')
    os.makedirs(out_dir_abs, exist_ok=True)
    os.makedirs(originals_abs, exist_ok=True)

    visual_blocks = _extract_visual_blocks(content, min_blocks=1, max_blocks=max(1, min(5, len(uploaded))))
    anchors = [item.get('block_index', idx) for idx, item in enumerate(visual_blocks)]
    if not anchors:
        anchors = [idx * 2 for idx in range(len(uploaded))]

    prepared: list[dict] = []
    for idx, item in enumerate(uploaded, start=1):
        src = item.get('path') or ''
        if not src or not os.path.isfile(src):
            continue
        ext = item.get('ext') or _get_ext(src) or 'png'
        original_name = f'user-{idx:02d}-original.{ext}'
        cleaned_name = f'user-{idx:02d}.{ext}'
        original_dst = os.path.join(originals_abs, original_name)
        cleaned_dst = os.path.join(out_dir_abs, cleaned_name)
        try:
            shutil.copy2(src, original_dst)
            cleanup = _copy_with_watermark_cleanup(src, cleaned_dst)
        except Exception as e:
            logger.warning('Failed to prepare uploaded illustration %s: %s', src, e)
            continue

        anchor = anchors[min(idx - 1, len(anchors) - 1)]
        try:
            anchor = int(anchor)
        except (TypeError, ValueError):
            anchor = idx * 2
        prepared.append({
            'role': 'uploaded',
            'relpath': os.path.join(out_dir_rel, cleaned_name).replace(os.sep, '/'),
            'original_relpath': os.path.join(out_dir_rel, 'originals', original_name).replace(os.sep, '/'),
            'alt': f'{title} — 用户配图 {idx}',
            'block_index': anchor,
            'source_filename': item.get('filename') or original_name,
            'watermark_cleanup': cleanup,
        })
    return prepared


def _merge_article_images(generated: list[dict], uploaded: list[dict]) -> list[dict]:
    """Merge generated and uploaded images with uploaded illustrations winning.

    Generated cover is kept at the top. For body scenes, any generated image
    anchored at the same or neighboring paragraph as an uploaded illustration
    is removed so the uploaded image replaces it and images do not stack.
    """
    if not uploaded:
        return generated
    cover = [img for img in generated if img.get('role') == 'cover']
    uploaded_blocks = []
    for img in uploaded:
        try:
            uploaded_blocks.append(int(img.get('block_index')))
        except (TypeError, ValueError):
            pass

    merged_scenes: list[dict] = []
    for img in generated:
        if img.get('role') == 'cover':
            continue
        try:
            block_index = int(img.get('block_index'))
        except (TypeError, ValueError):
            block_index = None
        if block_index is not None and any(abs(block_index - b) <= 2 for b in uploaded_blocks):
            continue
        merged_scenes.append(img)

    merged_scenes.extend(uploaded)

    def _sort_key(img: dict) -> tuple[int, int]:
        role_rank = 0 if img.get('role') == 'cover' else 1
        try:
            block_index = int(img.get('block_index'))
        except (TypeError, ValueError):
            block_index = 999999
        return role_rank, block_index

    return sorted(cover, key=_sort_key) + sorted(merged_scenes, key=_sort_key)


def _cleanup_draft_illustrations(uploaded: list[dict]):
    """Remove transient draft-image directories after assets are copied."""
    parents = {os.path.dirname(item.get('path', '')) for item in uploaded if item.get('path')}
    for parent in parents:
        if parent.startswith(os.path.abspath(DRAFT_DIR)) and os.path.isdir(parent):
            shutil.rmtree(parent, ignore_errors=True)


def _calc_read_time(content: str) -> int:
    """Estimate reading time in minutes for Chinese/mixed content."""
    # Count CJK characters + word-split for latin
    cjk_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    latin_words = len(re.findall(r'[a-zA-Z]+', content))
    total_units = cjk_count + latin_words
    return max(1, total_units // 300)


def _slugify(text: str) -> str:
    """Simple slug generator."""
    try:
        from slugify import slugify
        return slugify(text, max_length=60)
    except ImportError:
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        return slug[:60]


def _article_short_slug(title: str, date_str: str, max_title_len: int = 32) -> str:
    """Build a compact article slug used by Jekyll as the final HTML path."""
    compact_date = date_str.replace('-', '')
    clean_title = re.sub(r'[#*_`~>\[\]()]', ' ', title or '')
    ascii_tokens = re.findall(r'[A-Za-z0-9]+', clean_title)
    if ascii_tokens:
        base = '-'.join(token.lower() for token in ascii_tokens[:4])
    else:
        base = _slugify(clean_title)
    base = re.sub(r'[^a-z0-9-]+', '-', base.lower()).strip('-')
    base = re.sub(r'-{2,}', '-', base)[:max_title_len].strip('-')
    if not base:
        base = 'article'
    return f'{base}-{compact_date}'


def _unique_post_filename(posts_dir: str, date_str: str, slug: str) -> str:
    """Return a non-overwriting Jekyll post filename."""
    filename = f'{date_str}-{slug}.md'
    if not os.path.exists(os.path.join(posts_dir, filename)):
        return filename
    idx = 2
    while True:
        filename = f'{date_str}-{slug}-{idx}.md'
        if not os.path.exists(os.path.join(posts_dir, filename)):
            return filename
        idx += 1


_POST_FILENAME_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$')
_SHORT_CODE_RE = re.compile(r'^[0-9a-f]{8}$')


def _article_admin_filename(filename: str) -> str:
    """Return the short admin URL filename for a Jekyll post filename."""
    return repo_article_admin_filename(filename)


def _resolve_post_filename(filename: str) -> str | None:
    """Resolve either a real Jekyll filename or a short admin filename."""
    if not filename or '/' in filename or '\\' in filename or not filename.endswith('.md'):
        return None
    direct = os.path.join(POSTS_DIR, filename)
    if os.path.isfile(direct):
        return filename

    wanted = filename.strip()
    for fname in os.listdir(POSTS_DIR) if os.path.isdir(POSTS_DIR) else []:
        if not fname.endswith('.md'):
            continue
        if _article_admin_filename(fname) == wanted:
            return fname
    return None


def _article_short_code(filename: str) -> str:
    """Return a stable short-link code for a real Jekyll post filename."""
    normalized = (filename or '').strip()
    digest = hashlib.sha1(f'pzj-short-link:{normalized}'.encode('utf-8')).hexdigest()
    return digest[:8]


def _resolve_short_code(code: str) -> str | None:
    """Resolve a short-link code to a real Jekyll post filename."""
    code = (code or '').strip().lower()
    if not _SHORT_CODE_RE.match(code):
        return None
    if not os.path.isdir(POSTS_DIR):
        return None
    for fname in os.listdir(POSTS_DIR):
        if not fname.endswith('.md'):
            continue
        if _article_short_code(fname) == code:
            return fname
    return None


def _absolute_public_url(path: str) -> str:
    """Build a root-domain public URL, ignoring admin reverse-proxy prefixes."""
    return _force_public_https(urljoin(request.host_url, path.lstrip('/')))


def _public_article_url(admin_filename: str) -> str:
    return _absolute_public_url(f'/articles/{admin_filename}')


def _public_short_url(short_code: str) -> str:
    return _absolute_public_url(f'/s/{short_code}')


def _public_card_url(short_code: str) -> str:
    return _absolute_public_url(f'/c/{short_code}')


def _save_draft(content: str, title: str, tags: str, description: str,
                illustration_files=None, preserve_original_media: bool = False,
                original_media=None, revision_instruction: str = '',
                rewrite_rate: int = REWRITE_RATE_DEFAULT) -> str:
    """Save draft to temp file, return draft ID."""
    os.makedirs(DRAFT_DIR, exist_ok=True)
    draft_id = hashlib.md5(f'{title}{datetime.now().isoformat()}'.encode()).hexdigest()[:12]
    inserted_images = _save_draft_illustrations(draft_id, illustration_files or [])
    draft_path = os.path.join(DRAFT_DIR, f'{draft_id}.json')
    with open(draft_path, 'w', encoding='utf-8') as f:
        json.dump({
            'content': content,
            'title': title,
            'tags': tags,
            'description': description,
            'inserted_images': inserted_images,
            'preserve_original_media': preserve_original_media,
            'original_media': original_media or [],
            'revision_instruction': (revision_instruction or '').strip(),
            'rewrite_rate': _parse_rewrite_rate(rewrite_rate),
        }, f, ensure_ascii=False)
    return draft_id


def _load_draft(draft_id: str) -> dict | None:
    """Load and delete draft file."""
    if not draft_id:
        return None
    draft_path = os.path.join(DRAFT_DIR, f'{draft_id}.json')
    if not os.path.isfile(draft_path):
        return None
    with open(draft_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    os.remove(draft_path)
    return data


def _get_ext(filename: str) -> str:
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def _scan_posts():
    """Scan _posts/ directory and return list of post metadata."""
    posts = []
    if not os.path.isdir(POSTS_DIR):
        return posts
    for fname in sorted(os.listdir(POSTS_DIR), reverse=True):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(POSTS_DIR, fname)
        meta = {
            'filename': fname,
            'admin_filename': _article_admin_filename(fname),
            'path': fpath,
        }
        # Parse front matter
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        meta[key.strip()] = val.strip().strip('"').strip("'")
        # Fallback title from filename
        if 'title' not in meta:
            meta['title'] = fname.replace('.md', '').split('-', 3)[-1] if '-' in fname else fname
        posts.append(meta)
    return posts


def _post_public_summary(filename: str, meta: dict, body: str) -> dict:
    """Build compact public metadata for homepage cards."""
    title = meta.get('title') or filename.replace('.md', '').split('-', 3)[-1]
    date = meta.get('date') or filename[:10]
    cover_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', body)
    cover = ''
    if cover_match:
        cover = cover_match.group(1).replace('{{ site.baseurl }}', request.script_root or '/PolaZhenjing')
        if cover.startswith('/assets/'):
            cover = (request.script_root or '/PolaZhenjing') + cover
    summary = meta.get('summary') or ''
    if '![' in summary:
        summary = ''
    summary = summary or _generate_summary(body, max_chars=120)
    summary = re.sub(r'!\[[^\]]*(?:\]\([^)]+\))?', '', summary).strip()
    admin_filename = _article_admin_filename(filename)
    local_url = url_for('public_articles.public_article_view', filename=admin_filename)
    short_code = _article_short_code(filename)
    keywords = _article_keywords(meta.get('tags', ''))
    return {
        'filename': filename,
        'admin_filename': admin_filename,
        'title': title,
        'date': date,
        'summary': summary,
        'layout': meta.get('layout', ''),
        'theme': meta.get('theme', ''),
        'cover': cover,
        'url': local_url,
        'canonical_url': _public_article_url(admin_filename),
        'short_url': _public_short_url(short_code),
        'keywords': keywords,
        'section': _article_section(meta.get('layout', ''), keywords),
        'read_time': _calc_read_time(body),
        'word_count': _article_word_count(body),
        'admin_url': url_for('uploader.view_article', filename=admin_filename),
    }


def _public_filter_id(value: str) -> str:
    """Return a DOM-safe filter id for public article chips."""
    value = (value or '').strip().lower()
    if not value:
        return 'uncategorized'
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', value).strip('-') or 'uncategorized'


def _public_article_home_context(summaries: list[dict]) -> dict:
    """Build derived context for the public article homepage."""
    topic_counts: dict[str, int] = {}
    keyword_counts: dict[str, int] = {}
    read_time_total = 0
    word_count_total = 0
    for post in summaries:
        section = (post.get('section') or 'AI Articles').strip()
        topic_counts[section] = topic_counts.get(section, 0) + 1
        read_time_total += int(post.get('read_time') or 0)
        word_count_total += int(post.get('word_count') or 0)
        for keyword in post.get('keywords') or []:
            keyword = str(keyword).strip()
            if keyword:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    topic_filters = [
        {'id': _public_filter_id(name), 'label': name, 'count': count}
        for name, count in sorted(topic_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    keyword_filters = [
        {'id': _public_filter_id(name), 'label': name, 'count': count}
        for name, count in sorted(keyword_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    return {
        'featured_post': summaries[0] if summaries else None,
        'topic_filters': topic_filters,
        'keyword_filters': keyword_filters,
        'article_stats': {
            'article_count': len(summaries),
            'topic_count': len(topic_filters),
            'read_time_total': read_time_total,
            'word_count_total': word_count_total,
        },
    }


def _article_nav_item(post: dict, current_filename: str) -> dict:
    """Build a compact article navigation item without reading full content."""
    filename = post.get('filename', '')
    admin_filename = post.get('admin_filename') or _article_admin_filename(filename)
    return {
        'filename': filename,
        'admin_filename': admin_filename,
        'title': post.get('title') or admin_filename.replace('.md', ''),
        'date': post.get('date') or filename[:10],
        'url': url_for('public_articles.public_article_view', filename=admin_filename),
        'is_current': filename == current_filename,
    }


def _article_navigation_context(current_filename: str, quick_limit: int = 8) -> dict:
    """Return previous/next and quick article links for the reader page."""
    posts = _scan_posts()
    if not posts:
        return {'previous': None, 'next': None, 'quick': []}

    current_index = next(
        (idx for idx, post in enumerate(posts) if post.get('filename') == current_filename),
        None,
    )
    if current_index is None:
        return {'previous': None, 'next': None, 'quick': []}

    current_post = posts[current_index]
    previous_post = posts[current_index - 1] if current_index > 0 else None
    next_post = posts[current_index + 1] if current_index + 1 < len(posts) else None

    quick_posts = posts[:quick_limit]
    if current_post not in quick_posts:
        quick_posts = [current_post] + quick_posts[:max(quick_limit - 1, 0)]

    return {
        'previous': _article_nav_item(previous_post, current_filename) if previous_post else None,
        'next': _article_nav_item(next_post, current_filename) if next_post else None,
        'quick': [_article_nav_item(post, current_filename) for post in quick_posts],
    }


def _article_like_count(article_id: str) -> int:
    """Return persisted like count for an article."""
    if not article_id:
        return 0
    try:
        row = get_db().execute(
            'SELECT like_count FROM article_likes WHERE article_id = ?',
            (article_id,),
        ).fetchone()
    except Exception:
        logger.exception('Failed to read article like count for %s', article_id)
        return 0
    if not row:
        return 0
    try:
        return max(int(row['like_count'] or 0), 0)
    except (TypeError, ValueError):
        return 0


@uploader_bp.route('/api/public/articles')
def public_articles():
    """Return recent article metadata for the public AIPD homepage."""
    try:
        limit = min(max(int(request.args.get('limit', 5)), 1), 12)
    except ValueError:
        limit = 5

    articles = []
    for post in _scan_posts()[:limit]:
        filename = post.get('filename', '')
        fpath = post.get('path', '')
        if not filename or not fpath or not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()
        except OSError:
            continue
        body = raw
        meta = dict(post)
        if raw.startswith('---'):
            parts = raw.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
        articles.append(_post_public_summary(filename, meta, body))
    return jsonify({'ok': True, 'articles': articles})


@uploader_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        content = ''
        title = ''
        preserve_original_media = request.form.get('media_strategy', 'keep') == 'keep'
        content_format = request.form.get('content_format', '').strip()
        markdown_content = request.form.get('content', '').strip()
        rich_content = request.form.get('rich_content', '').strip()
        revision_instruction = request.form.get('revision_instruction', '').strip()
        rewrite_rate = _parse_rewrite_rate(request.form.get('rewrite_rate'))

        # Handle file upload
        if 'file' in request.files and request.files['file'].filename:
            f = request.files['file']
            ext = _get_ext(f.filename)
            if ext not in ALLOWED_EXT:
                flash(f'不支持的文件类型：.{ext}', 'error')
                return render_template('upload.html')

            os.makedirs(UPLOAD_DIR, exist_ok=True)
            tmp_path = os.path.join(UPLOAD_DIR, f.filename)
            f.save(tmp_path)

            try:
                content = detect_and_convert(tmp_path, ext)
                if not preserve_original_media:
                    content = _strip_markdown_media(content)
                title = extract_title(content)
            except Exception as e:
                flash(f'转换错误：{e}', 'error')
                return render_template('upload.html')

        # Handle Markdown paste explicitly. Keep this before rich text so the
        # visible editor mode is the source of truth when both fields exist.
        elif content_format == 'markdown' and markdown_content:
            content = _normalize_pasted_markdown(markdown_content, preserve_media=preserve_original_media)
            if not preserve_original_media:
                content = _strip_markdown_media(content)
            title = extract_title(content)

        # Handle rich text content from TinyMCE
        elif content_format == 'rich_html' and rich_content:
            content = _rich_html_to_markdown(
                rich_content,
                preserve_media=preserve_original_media,
            )
            title = extract_title(content)

        # Backward-compatible paste fallback. This also saves users who typed
        # into the rich editor while the old UI still showed both editors.
        elif markdown_content:
            content = _normalize_pasted_markdown(markdown_content, preserve_media=preserve_original_media)
            if not preserve_original_media:
                content = _strip_markdown_media(content)
            title = extract_title(content)

        elif rich_content:
            content = _rich_html_to_markdown(
                rich_content,
                preserve_media=preserve_original_media,
            )
            title = extract_title(content)

        # Handle URL input
        elif request.form.get('url', '').strip():
            url = request.form['url'].strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                flash('请输入以 http:// 或 https:// 开头的 URL。', 'error')
                return render_template('upload.html')
            try:
                content, fetched_title = fetch_url_as_markdown(url)
                if not preserve_original_media:
                    content = _strip_markdown_media(content)
            except URLFetchBlocked as e:
                # Known anti-bot site OR response looked like a JS challenge.
                # Fail fast here so we never burn LLM + image-gen credits
                # on garbage HTML. Show the reason + actionable suggestion.
                logger.info('URL blocked: %s (%s)', url, e)
                flash(f'抓取失败：{e} {e.suggestion}'.strip(), 'error')
                return render_template('upload.html')
            except Exception as e:
                logger.exception('URL fetch failed: %s', url)
                flash(f'抓取 URL 失败：{e}', 'error')
                return render_template('upload.html')
            if not content.strip():
                flash('未能从该 URL 提取到文章内容。请改用「粘贴内容」。', 'error')
                return render_template('upload.html')
            title = fetched_title or extract_title(content)

        else:
            flash('请上传文件、粘贴内容或输入 URL。', 'error')
            return render_template('upload.html')

        # Store in temp file (avoid session cookie size limit)
        resolved_title = request.form.get('title', '').strip() or title
        resolved_tags = _format_article_tags(
            _auto_article_tags(resolved_title, content, request.form.get('tags', '').strip())
        )
        original_media = _extract_markdown_media_blocks(content) if preserve_original_media else []
        draft_id = _save_draft(content,
                               resolved_title,
                               resolved_tags,
                               request.form.get('description', '').strip(),
                               request.files.getlist('illustrations'),
                               preserve_original_media=preserve_original_media,
                               original_media=original_media,
                               revision_instruction=revision_instruction,
                               rewrite_rate=rewrite_rate)
        session['draft_id'] = draft_id
        return redirect(url_for('uploader.style_select'))

    insight_prefill = None
    insight_topic_id = request.args.get('insight_topic', '').strip()
    if insight_topic_id:
        topic = get_topic(insight_topic_id)
        if topic:
            insight_prefill = build_upload_prefill(topic)
        else:
            flash('洞察选题不存在，已进入普通上传模式。', 'warning')
    return render_template('upload.html', insight_prefill=insight_prefill)


@uploader_bp.route('/upload/media', methods=['POST'])
@login_required
def upload_richtext_media():
    """Receive images pasted or dropped into the rich text editor."""
    file_storage = request.files.get('file')
    if not file_storage or not file_storage.filename:
        return jsonify({'error': '缺少图片文件'}), 400
    try:
        location = _save_richtext_image(file_storage)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        logger.exception('Rich text media upload failed')
        return jsonify({'error': '图片上传失败'}), 500
    return jsonify({'location': location})


@uploader_bp.route('/upload/style', methods=['GET'])
@login_required
def style_select():
    if 'draft_id' not in session:
        return redirect(url_for('uploader.upload'))
    # Peek at draft for title display (don't delete yet)
    draft_path = os.path.join(DRAFT_DIR, f"{session['draft_id']}.json")
    title = ''
    if os.path.isfile(draft_path):
        with open(draft_path, 'r', encoding='utf-8') as f:
            title = json.load(f).get('title', '')
    return render_template('style_select.html', styles=STYLES, title=title)


@uploader_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Submit an async generation job and redirect to the status page."""
    draft_id = session.pop('draft_id', '')
    draft = _load_draft(draft_id)
    if not draft:
        flash('没有可生成的内容。', 'error')
        return redirect(url_for('uploader.upload'))

    content = draft['content']
    title = draft['title'] or '无标题'
    tags = draft['tags']
    description = draft['description']
    inserted_images = draft.get('inserted_images') or []
    revision_instruction = draft.get('revision_instruction', '')
    rewrite_rate = _parse_rewrite_rate(draft.get('rewrite_rate'))
    style = request.form.get('style', 'deep-technical')

    if not content:
        flash('没有可生成的内容。', 'error')
        return redirect(url_for('uploader.upload'))

    # Capture data needed by the background thread (no Flask context in thread)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    theme = _get_theme()
    payload = {
        'content': content,
        'title': title,
        'tags': tags,
        'description': description,
        'inserted_images': inserted_images,
        'revision_instruction': revision_instruction,
        'rewrite_rate': rewrite_rate,
        'preserve_original_media': draft.get('preserve_original_media', False),
        'original_media': draft.get('original_media') or [],
        'style': style,
        'theme': theme,
        'project_root': project_root,
    }

    job_id = jobs.create_job(kind='generate', user_id=session.get('user_id'), title=title)
    jobs.submit(_run_generate_job, job_id, payload)

    return redirect(url_for('uploader.generate_status', job_id=job_id))


def _run_generate_job(job_id: str, p: dict):
    """Background worker: LLM rewrite → build post → write file → safe git sync.

    Runs in a daemon thread, owns no Flask context, updates job state via
    the `jobs` module for the polling UI.
    """
    content = p['content']
    title = p['title']
    tags = p['tags']
    description = p['description']
    inserted_images = p.get('inserted_images') or []
    revision_instruction = p.get('revision_instruction', '')
    rewrite_rate = _parse_rewrite_rate(p.get('rewrite_rate'))
    preserve_original_media = bool(p.get('preserve_original_media'))
    original_media = p.get('original_media') or []
    style = p['style']
    theme = p['theme']
    project_root = p['project_root']

    jobs.update_job(job_id, status=jobs.RUNNING, stage='加载草稿内容…', progress=5)

    # ── LLM skill rewriting ──────────────────────────────────
    skill_prompt = _get_style_prompt(style)
    if rewrite_rate <= 0:
        jobs.update_job(job_id, stage='AI 改写率 0%，跳过文本重写…', progress=15)
        jobs.append_message(job_id, 'info', 'AI 改写率为 0%，已跳过文本重写，将继续生成/插入图片。')
    elif skill_prompt:
        jobs.update_job(job_id, stage=f'LLM 正在以「{style}」风格按 {rewrite_rate}% 改写…', progress=15)
        rewritten = _call_llm_rewrite(
            content,
            title,
            skill_prompt,
            revision_instruction=revision_instruction,
            rewrite_rate=rewrite_rate,
        )
        if rewritten:
            content = rewritten
            jobs.append_message(job_id, 'info', f'已使用 LLM 技能按 {rewrite_rate}% 改写内容（风格：{style}）。')
            if revision_instruction:
                jobs.append_message(job_id, 'info', '已根据「修改建议简述」调整文章。')
        else:
            jobs.append_message(job_id, 'warning', 'LLM 重写失败，将使用原始内容。')

    if preserve_original_media and original_media:
        before_len = len(content)
        content = _ensure_original_media(content, original_media)
        if len(content) != before_len:
            jobs.append_message(job_id, 'info', '已保留原文图片/视频媒体，防止风格重写时丢失。')

    # ── Ghibli-style illustrations ───────────────────────────
    # Keep the public article slug short because Jekyll uses it as the HTML path.
    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = _article_short_slug(title, date_str)

    uploaded_images = []
    if inserted_images:
        jobs.update_job(job_id, stage='正在处理用户配图并去除水印…', progress=38)
        uploaded_images = _prepare_uploaded_illustrations(inserted_images, title, content, slug, project_root)
        if uploaded_images:
            cleaned_count = sum(
                1 for img in uploaded_images
                if (img.get('watermark_cleanup') or {}).get('changed')
            )
            jobs.append_message(
                job_id, 'success',
                f'已接收 {len(uploaded_images)} 张用户配图，其中 {cleaned_count} 张检测到疑似边角水印并做了局部清理。'
            )
        else:
            jobs.append_message(job_id, 'warning', '用户配图处理失败，将继续生成文章。')

    jobs.update_job(job_id, stage='正在生成吉卜力风格插画…', progress=45)
    try:
        images = _generate_illustrations(title, content, slug, project_root)
    except Exception as e:
        logger.exception('Illustration generation crashed')
        images = []

    merged_images = _merge_article_images(images, uploaded_images)
    if merged_images:
        content = _inject_illustrations(content, merged_images)
        if uploaded_images and images:
            replaced = len(images) + len(uploaded_images) - len(merged_images)
            if replaced > 0:
                jobs.append_message(
                    job_id, 'info',
                    f'用户配图与 {replaced} 张生成图位置接近，已优先使用用户配图替换。'
                )
    if images:
        jobs.append_message(job_id, 'success',
                            f'已生成 {len(images)} 张吉卜力风格插画。')
    elif uploaded_images:
        jobs.append_message(job_id, 'info', '未生成 AI 插画，已使用用户上传配图完成图文排版。')
    else:
        jobs.append_message(job_id, 'warning',
                            '未生成插画（API 密钥缺失或调用失败），文章将无插图。')
    _cleanup_draft_illustrations(inserted_images)

    jobs.update_job(job_id, stage='正在构建 Jekyll 文章…', progress=70)

    # Build Jekyll post
    posts_dir = os.path.join(project_root, '_posts')
    os.makedirs(posts_dir, exist_ok=True)
    filename = _unique_post_filename(posts_dir, date_str, slug)

    # Front matter
    tag_list = _auto_article_tags(title, content, tags)
    summary = _generate_summary(content)
    seo_description = (description or summary or _generate_summary(content, max_chars=160)).strip()
    if len(seo_description) > 180:
        seo_description = seo_description[:180].rstrip(' ，。；、,.') + '。'
    cover_image = ''
    for item in merged_images:
        if item.get('role') == 'cover' and item.get('relpath'):
            cover_image = '/' + item['relpath'].lstrip('/')
            break
    if not cover_image:
        first_image_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', content)
        if first_image_match:
            cover_image = first_image_match.group(1).replace('{{ site.baseurl }}', '').strip()
    if not cover_image:
        cover_image = '/assets/images/test_cover.jpg'

    front_matter = f"""---
layout: {style}
theme: {theme}
title: "{title}"
date: {date_str}
image: "{cover_image}"
tags: [{', '.join(tag_list)}]"""

    if seo_description:
        front_matter += f'\ndescription: "{seo_description.replace(chr(34), chr(92) + chr(34))}"'

    if summary:
        safe_summary = summary.replace('"', '\\"')
        front_matter += f'\nsummary: "{safe_summary}"'

    front_matter += '\n---\n\n'

    # Write to _posts/
    post_path = os.path.join(posts_dir, filename)
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)

    # Auto-sync to GitHub
    jobs.update_job(job_id, stage='正在同步到 GitHub…', progress=85)
    try:
        commit_msg = f'Add article: {title} - {date_str}'
        deploy_result = guarded_commit_and_push(
            project_root,
            commit_msg,
            push_args=['push', '-u', 'origin', 'main'],
        )
        if deploy_result.pushed:
            jobs.append_message(job_id, 'success',
                                f'文章「{title}」已以 {style} 风格创建，并已同步到 GitHub。')
        else:
            jobs.append_message(job_id, 'info',
                                f'文章「{title}」已创建，无需同步新的文章文件。')
    except GitSafetyError as e:
        jobs.append_message(job_id, 'warning', f'文章「{title}」已创建，但同步被安全规则阻止：{e}')
    except Exception as e:
        jobs.append_message(job_id, 'warning', f'文章「{title}」已创建，但同步出错：{e}')

    jobs.update_job(job_id, status=jobs.DONE, stage='已完成', progress=100,
                    result_filename=filename)


@uploader_bp.route('/generate/status/<job_id>')
@login_required
def generate_status(job_id):
    """Render the HTML status page that polls for progress."""
    job = jobs.get_job(job_id)
    if not job:
        flash('任务不存在或已过期。', 'error')
        return redirect(url_for('uploader.articles'))
    return render_template('status.html', job=job, job_id=job_id)


@uploader_bp.route('/generate/progress/<job_id>')
@login_required
def generate_progress(job_id):
    """JSON endpoint polled by the status page. Messages are shown inline on
    the status page itself (not flashed) to avoid duplication across polls."""
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({'status': 'not_found'}), 404

    result_filename = job.get('result_filename') or ''
    article_url = ''
    if result_filename:
        article_url = url_for('uploader.view_article',
                              filename=_article_admin_filename(result_filename))

    return jsonify({
        'status': job['status'],
        'stage': job.get('stage') or '',
        'progress': job.get('progress') or 0,
        'error': job.get('error'),
        'messages': job.get('messages') or [],
        'article_url': article_url,
        'articles_url': url_for('uploader.articles'),
    })


@uploader_bp.route('/articles')
def articles():
    if not _is_admin_session():
        return _render_public_articles()

    posts = _scan_posts()
    # Load in-flight generation jobs so users see a "生成中" placeholder
    # in the list immediately after submission.
    pending_jobs = jobs.list_active_jobs(kind='generate', limit=20)
    # Parse messages JSON for template-side rendering (optional).
    for j in pending_jobs:
        try:
            j['messages'] = json.loads(j.get('messages') or '[]')
        except Exception:
            j['messages'] = []
    return render_template('articles.html', posts=posts, styles=STYLES,
                           pending_jobs=pending_jobs)


@public_articles_bp.route('/articles')
def public_article_index():
    """Public read-only article list."""
    return _render_public_articles()


def _render_public_articles():
    posts = _scan_posts()
    summaries = []
    for post in posts:
        filename = post.get('filename', '')
        fpath = post.get('path', '')
        if not filename or not fpath or not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()
        except OSError:
            continue
        body = raw
        meta = dict(post)
        if raw.startswith('---'):
            parts = raw.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
        summaries.append(_post_public_summary(filename, meta, body))
    homepage = _public_article_home_context(summaries)
    return render_template('public_articles.html', posts=summaries,
                           featured_post=homepage['featured_post'],
                           topic_filters=homepage['topic_filters'],
                           keyword_filters=homepage['keyword_filters'],
                           article_stats=homepage['article_stats'],
                           show_admin_nav=False)


GITHUB_REPO = 'PolarisW007/PolaZhenJing'
GITHUB_BRANCH = 'main'
GITHUB_PAGES_BASE = 'https://polarisw007.github.io/PolaZhenJing'

import re as _re

def _build_pages_url(filename):
    """Build GitHub Pages article URL from Jekyll post filename.
    Filename format: YYYY-MM-DD-slug.md  →  /YYYY/MM/DD/slug/
    """
    m = _re.match(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$', filename)
    if m:
        year, month, day, slug = m.groups()
        return f'{GITHUB_PAGES_BASE}/{year}/{month}/{day}/{slug}/'
    return GITHUB_PAGES_BASE + '/'


def _safe_post_path(filename: str) -> str | None:
    """Return an absolute post path only for safe _posts markdown filenames."""
    return repo_safe_post_path(filename, POSTS_DIR)


def _parse_post(raw: str) -> tuple[dict, list[str], str]:
    """Parse the simple Jekyll front matter used by this project."""
    return repo_parse_post(raw)


def _yaml_quote(value: str) -> str:
    """Quote a simple YAML string value for front matter."""
    value = (value or '').replace('\\', '\\\\').replace('"', '\\"')
    return f'"{value}"'


def _tags_front_matter(raw_tags: str) -> str:
    """Convert comma-separated tags to an inline YAML list."""
    tags = [tag.strip() for tag in (raw_tags or '').split(',') if tag.strip()]
    return '[' + ', '.join(json.dumps(tag, ensure_ascii=False) for tag in tags) + ']'


def _tags_input_value(meta_tags: str) -> str:
    """Convert existing inline tags to a friendly comma-separated input value."""
    value = (meta_tags or '').strip()
    if not value or value == '[]':
        return ''
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1].strip()
        if not inner:
            return ''
        try:
            parsed = json.loads(value.replace("'", '"'))
            if isinstance(parsed, list):
                return ', '.join(str(item) for item in parsed)
        except Exception:
            pass
        return ', '.join(item.strip().strip('"').strip("'") for item in inner.split(',') if item.strip())
    return value


def _article_keywords(meta_tags: str) -> list[str]:
    """Return article tags as clean keyword strings."""
    value = (meta_tags or '').strip()
    if not value or value == '[]':
        return []
    if value.startswith('[') and value.endswith(']'):
        try:
            parsed = json.loads(value.replace("'", '"'))
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            inner = value[1:-1]
            return [item.strip().strip('"').strip("'") for item in inner.split(',') if item.strip()]
    return [item.strip() for item in value.split(',') if item.strip()]


ARTICLE_PRIMARY_TAGS = {
    'agent-systems': [
        'agent', 'agents', 'agentic', 'multi-agent', 'a2a', 'mcp', 'harness',
        'workflow', 'workflows', 'autonomous', 'tool use', 'tools', '智能体',
        '代理', '工作流', '多智能体', '工具调用', '自动化',
    ],
    'ai-engineering': [
        'engineering', 'context engineering', 'prompt', 'rag', 'embedding',
        'embeddings', 'retrieval', 'eval', 'evaluation', 'observability',
        'production', 'pipeline', '架构', '工程', '提示词', '上下文工程',
        '检索', '评测', '向量', '知识库',
    ],
    'model-research': [
        'llm', 'large language model', 'transformer', 'attention', 'reasoning',
        'scaling', 'training', 'deep learning', 'model', 'inference', 'research',
        '大模型', '模型', '训练', '推理', '注意力', '研究', '深度学习',
    ],
    'product-design': [
        'product', 'design', 'linear', 'interface', 'ux', 'user experience',
        'saas', 'native', '产品', '设计', '交互', '体验', '用户', '三层架构',
    ],
    'data-infrastructure': [
        'data', 'database', 'databricks', 'snowflake', 'fde', 'palantir',
        'warehouse', 'lakehouse', 'analytics', '数据', '数据库', '数据仓库',
        '数据基础设施', '数据平台',
    ],
    'coding-tools': [
        'codex', 'claude code', 'cursor', 'cli', 'typescript', 'javascript',
        'sdk', 'github', 'developer', 'programming', '代码', '编程', '开发者',
        '命令行', '工具',
    ],
    'media-generation': [
        'video', 'image', 'multimodal', 'vision', 'seedance', '生成模型',
        '视频', '图像', '视觉', '多模态', '影像', '叙事引擎',
    ],
    'industry-analysis': [
        'industry', 'market', 'company', 'startup', 'anthropic', 'openai',
        'deepseek', 'karpathy', 'sam bowman', 'future', 'prediction', 'reshape',
        '行业', '公司', '创业', '团队', '商业', '趋势',
    ],
    'personal-knowledge': [
        'knowledge', 'learning', 'notes', 'practice', 'writing', 'memory',
        '个人', '知识', '学习', '笔记', '写作', '实践', '认知',
    ],
    'testing-harness': [
        'test', 'testing', 'regression', 'harness', 'qa', '验证', '测试',
        '回归', '门禁',
    ],
}

ARTICLE_SECONDARY_TAGS = {
    'openai': ['openai', 'chatgpt', 'gpt'],
    'anthropic': ['anthropic'],
    'claude': ['claude'],
    'codex': ['codex'],
    'deepseek': ['deepseek'],
    'langchain': ['langchain'],
    'palantir': ['palantir'],
    'databricks': ['databricks'],
    'snowflake': ['snowflake'],
    'fde': ['fde', 'forward deployed engineer', '前线部署工程师'],
    'llm': ['llm', 'large language model', '大语言模型', '大模型'],
    'transformer': ['transformer', 'attention', 'self-attention', '注意力'],
    'deep-learning': ['deep learning', 'deep-learning', '深度学习'],
    'rag': ['rag', 'retrieval augmented', '检索增强'],
    'context-engineering': ['context engineering', '上下文工程'],
    'prompt-engineering': ['prompt', '提示词'],
    'developer-tools': ['developer tool', 'developer tools', '开发者工具'],
    'workflow': ['workflow', 'workflows', '工作流'],
    'multimodal': ['multimodal', '多模态'],
    'video-generation': ['video generation', '视频生成', 'seedance'],
    'typescript': ['typescript', 'javascript'],
    'case-study': ['case study', '案例', '实战', '实践'],
    'guide': ['guide', '指南', '教程', '入门'],
    'research': ['research', '论文', '研究'],
    'opinion': ['opinion', '观点', '思考', '判断'],
}

STYLE_TAGS = {style['id'] for style in STYLES}


def _normalize_article_tag(tag: str) -> str:
    """Normalize tags to stable lowercase kebab-case tokens."""
    tag = (tag or '').strip().strip('"').strip("'")
    if not tag:
        return ''
    tag = tag.replace('_', '-').replace('/', '-')
    tag = re.sub(r'\s+', '-', tag)
    tag = re.sub(r'[^A-Za-z0-9\u4e00-\u9fff-]+', '', tag)
    tag = re.sub(r'-{2,}', '-', tag).strip('-')
    return tag.lower()


def _dedupe_article_tags(tags: list[str], limit: int = 6) -> list[str]:
    """Return normalized unique tags, dropping empty values and style-only tags."""
    result = []
    seen = set()
    for raw in tags:
        tag = _normalize_article_tag(str(raw))
        if not tag or tag in seen or tag in STYLE_TAGS:
            continue
        seen.add(tag)
        result.append(tag)
        if len(result) >= limit:
            break
    return result


def _tag_score(text: str, needles: list[str]) -> int:
    """Score tag keywords against normalized text."""
    score = 0
    for needle in needles:
        needle = needle.lower()
        if needle and needle in text:
            score += 3 if len(needle) > 3 else 1
    return score


def _auto_article_tags(title: str, content: str, existing_tags: str = '') -> list[str]:
    """Generate stable article tags from title/body when users leave tags blank."""
    existing = _dedupe_article_tags(_article_keywords(existing_tags))
    if existing:
        return existing

    title_searchable = _strip_markdown_media(title or '').lower()
    body_searchable = _strip_markdown_media(content or '').lower()
    searchable = f'{title_searchable}\n{body_searchable}'
    scored_primary = []
    for tag, needles in ARTICLE_PRIMARY_TAGS.items():
        score = (_tag_score(title_searchable, needles) * 3) + _tag_score(body_searchable, needles)
        scored_primary.append((tag, score))
    scored_primary.sort(key=lambda item: (-item[1], item[0]))
    primary = scored_primary[0][0] if scored_primary and scored_primary[0][1] > 0 else 'personal-knowledge'

    tags = [primary]
    secondary = []
    for tag, needles in ARTICLE_SECONDARY_TAGS.items():
        score = (_tag_score(title_searchable, needles) * 2) + _tag_score(body_searchable, needles)
        if score > 0:
            secondary.append((tag, score))
    secondary.sort(key=lambda item: (-item[1], item[0]))
    tags.extend(tag for tag, _ in secondary)

    if primary == 'testing-harness' and 'test' not in tags:
        tags.append('test')
    if primary in {'agent-systems', 'ai-engineering', 'coding-tools'} and 'ai' not in tags:
        tags.append('ai')
    if primary in {'model-research', 'industry-analysis'} and 'ai' not in tags:
        tags.append('ai')
    if 'guide' not in tags and any(token in searchable for token in ['指南', '教程', '入门', 'guide']):
        tags.append('guide')
    if len(tags) < 3:
        tags.append('ai')
    if len(tags) < 3:
        tags.append('knowledge')
    result = _dedupe_article_tags(tags, limit=6)
    for fallback in ['ai', 'knowledge']:
        if len(result) >= 3:
            break
        if fallback not in result:
            result.append(fallback)
    return result


def _format_article_tags(tags: list[str]) -> str:
    """Format tags for Jekyll front matter."""
    return ', '.join(_dedupe_article_tags(tags))


def _strip_markdown_media(text: str) -> str:
    """Remove markdown media and collapse text for metadata summaries."""
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text or '')
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[*_`>#-]+', '', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _article_word_count(text: str) -> int:
    """Estimate visible article word count for structured data."""
    visible = _strip_markdown_media(text)
    cjk_count = sum(1 for char in visible if '\u4e00' <= char <= '\u9fff')
    latin_words = len(re.findall(r'[A-Za-z0-9]+', visible))
    return cjk_count + latin_words


def _clamp_description(text: str, max_chars: int = 180) -> str:
    """Keep social card descriptions compact enough for crawlers."""
    text = _strip_markdown_media(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip(' ，。；、,.') + '。'


def _article_first_image(body: str) -> str:
    match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', body or '')
    return match.group(1).strip() if match else ''


def _normalize_heading_text(text: str) -> str:
    return re.sub(r'\s+', '', _strip_markdown_media(text)).lower()


def _remove_duplicate_leading_heading(body_html: str, title: str) -> str:
    """Drop a body-leading h1/h2 when it duplicates the page title."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(body_html, 'html.parser')
        normalized_title = _normalize_heading_text(title)
        first_content = next((node for node in soup.contents
                              if getattr(node, 'name', None) or str(node).strip()), None)
        candidates = []
        if getattr(first_content, 'name', None) in {'h1', 'h2'}:
            candidates.append(first_content)
        candidates.extend(soup.find_all(['h1', 'h2'], limit=3))
        for heading in candidates:
            if _normalize_heading_text(heading.get_text(' ', strip=True)) == normalized_title:
                heading.decompose()
                break
        if candidates:
            return str(soup)
    except Exception:
        pass
    return body_html


def _force_public_https(raw_url: str) -> str:
    """Normalize public aipd.me URLs for external crawlers."""
    if raw_url.startswith('http://aipd.me/'):
        return 'https://' + raw_url[len('http://'):]
    return raw_url


def _absolute_asset_url(raw_url: str) -> str:
    """Convert article image paths to externally crawlable absolute URLs."""
    raw_url = (raw_url or '').strip().strip('"').strip("'")
    if not raw_url:
        return ''
    raw_url = raw_url.replace('{{ site.baseurl }}', '').strip()
    if raw_url.startswith(('http://', 'https://')):
        return _force_public_https(raw_url)
    if raw_url.startswith('/assets/'):
        path = raw_url[len('/assets/'):]
        return _force_public_https(urljoin(request.host_url, f'{_article_asset_base()}/assets/{path}'.lstrip('/')))
    if raw_url.startswith('assets/'):
        path = raw_url[len('assets/'):]
        return _force_public_https(urljoin(request.host_url, f'{_article_asset_base()}/assets/{path}'.lstrip('/')))
    return _force_public_https(urljoin(request.url_root, raw_url.lstrip('/')))


def _local_asset_path(raw_url: str) -> str | None:
    """Resolve a public article image URL/path to a local file under assets/."""
    raw_url = (raw_url or '').strip().strip('"').strip("'")
    if not raw_url:
        return None
    raw_url = raw_url.replace('{{ site.baseurl }}', '').strip()
    parsed_path = urlparse(raw_url).path if raw_url.startswith(('http://', 'https://')) else raw_url
    if parsed_path.startswith('/PolaZhenjing/assets/'):
        rel = parsed_path[len('/PolaZhenjing/assets/'):]
    elif parsed_path.startswith('/assets/'):
        rel = parsed_path[len('/assets/'):]
    elif parsed_path.startswith('assets/'):
        rel = parsed_path[len('assets/'):]
    else:
        return None
    rel = rel.lstrip('/')
    asset_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
    candidate = os.path.abspath(os.path.join(asset_root, rel))
    if not candidate.startswith(asset_root + os.sep):
        return None
    return candidate if os.path.isfile(candidate) else None


def _article_section(layout: str, keywords: list[str]) -> str:
    """Return a stable article section label for JSON-LD and feeds."""
    if keywords:
        return keywords[0]
    return layout or 'AI Articles'


def _share_image_url(raw_url: str, actual_filename: str, preset_name: str) -> str:
    """Return a generated JPEG share image URL for the requested preset."""
    preset = SHARE_IMAGE_PRESETS[preset_name]
    source_path = _local_asset_path(raw_url)
    if not source_path:
        return _absolute_asset_url(raw_url)
    short_code = _article_short_code(actual_filename)
    out_name = f'{os.path.splitext(actual_filename)[0]}-{short_code}-{preset["suffix"]}.jpg'
    out_path = os.path.join(SHARE_IMAGE_DIR, out_name)
    try:
        should_generate = (
            not os.path.isfile(out_path)
            or os.path.getmtime(out_path) < os.path.getmtime(source_path)
        )
        if should_generate:
            from PIL import Image, ImageOps
            os.makedirs(SHARE_IMAGE_DIR, exist_ok=True)
            with Image.open(source_path) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                resample = getattr(getattr(Image, 'Resampling', Image), 'LANCZOS')
                thumb = ImageOps.fit(image, preset['size'], method=resample, centering=(0.5, 0.5))
                thumb.save(
                    out_path,
                    format='JPEG',
                    quality=preset['quality'],
                    optimize=True,
                    progressive=True,
                )
        return _absolute_asset_url(f'{SHARE_IMAGE_URL_PREFIX}/{out_name}')
    except Exception as exc:
        current_app.logger.warning('Share thumbnail generation failed: %s', exc)
        return _absolute_asset_url(raw_url)


def _wechat_share_image_url(raw_url: str, actual_filename: str) -> str:
    """Return the WeChat-friendly square share image."""
    return _share_image_url(raw_url, actual_filename, 'wechat')


def _og_share_image_url(raw_url: str, actual_filename: str) -> str:
    """Return the Open Graph large-card share image."""
    return _share_image_url(raw_url, actual_filename, 'og')


def _build_article_share_context(actual_filename: str, meta: dict, body: str, fpath: str) -> dict:
    """Build public sharing metadata used by full article and card pages."""
    admin_filename = _article_admin_filename(actual_filename)
    short_code = _article_short_code(actual_filename)
    title = meta.get('title') or actual_filename.replace('.md', '')
    share_title = meta.get('share_title') or title
    canonical_url = _public_article_url(admin_filename)
    short_url = _public_short_url(short_code)
    share_card_url = _public_card_url(short_code)
    share_description = _clamp_description(
        meta.get('share_summary') or meta.get('description')
        or meta.get('summary') or _generate_summary(body, max_chars=160)
    )
    raw_share_image = (
        meta.get('share_image') or meta.get('image') or meta.get('cover') or _article_first_image(body)
        or '/assets/images/test_cover.jpg'
    )
    wechat_share_image = _wechat_share_image_url(raw_share_image, actual_filename)
    og_share_image = _og_share_image_url(raw_share_image, actual_filename)
    keywords = _article_keywords(meta.get('tags', ''))
    layout = meta.get('layout', 'deep-technical')
    date_published = meta.get('date') or actual_filename[:10]
    date_modified = _article_modified_time(fpath) or date_published
    read_time = _calc_read_time(body)
    word_count = _article_word_count(body)
    return {
        'actual_filename': actual_filename,
        'admin_filename': admin_filename,
        'title': title,
        'share_title': share_title,
        'share_description': share_description,
        'short_code': short_code,
        'canonical_url': canonical_url,
        'short_url': short_url,
        'share_card_url': share_card_url,
        'wechat_share_image': wechat_share_image,
        'og_share_image': og_share_image,
        'article_keywords': keywords,
        'article_section': _article_section(layout, keywords),
        'article_published_time': date_published,
        'article_modified_time': date_modified,
        'read_time': read_time,
        'article_word_count': word_count,
        'layout': layout,
    }


def _article_modified_time(path: str) -> str:
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat()
    except OSError:
        return ''


def _public_article_records(limit: int | None = None) -> list[dict]:
    """Build public article records for sitemap and llms.txt."""
    records = []
    for post in _scan_posts():
        filename = post.get('filename', '')
        fpath = post.get('path', '')
        if not filename or not fpath or not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()
        except OSError:
            continue
        meta, _, body = _parse_post(raw)
        meta = {**post, **meta}
        admin_filename = _article_admin_filename(filename)
        short_code = _article_short_code(filename)
        title = meta.get('title') or filename.replace('.md', '')
        summary = _clamp_description(
            meta.get('share_summary') or meta.get('description')
            or meta.get('summary') or _generate_summary(body, max_chars=160)
        )
        keywords = _article_keywords(meta.get('tags', ''))
        lastmod = _article_modified_time(fpath) or meta.get('date') or filename[:10]
        records.append({
            'filename': filename,
            'admin_filename': admin_filename,
            'title': title,
            'date': meta.get('date') or filename[:10],
            'summary': summary,
            'canonical_url': _public_article_url(admin_filename),
            'short_url': _public_short_url(short_code),
            'lastmod': lastmod[:10],
            'lastmod_iso': lastmod,
            'keywords': keywords,
            'section': _article_section(meta.get('layout', ''), keywords),
            'read_time': _calc_read_time(body),
            'word_count': _article_word_count(body),
        })
        if limit and len(records) >= limit:
            break
    return records


def _article_json_ld_graph(
        *,
        title: str,
        description: str,
        canonical_url: str,
        short_url: str,
        share_card_url: str,
        og_image: str,
        wechat_image: str,
        keywords: list[str],
        section: str,
        date_published: str,
        date_modified: str,
        word_count: int,
        read_time: int) -> dict:
    """Build article JSON-LD as a graph, so crawlers see page/site/author context."""
    site_url = _absolute_public_url('/')
    about_url = _absolute_public_url('/about.html')
    website_id = f'{site_url}#website'
    organization_id = f'{site_url}#organization'
    person_id = f'{about_url}#person'
    webpage_id = f'{canonical_url}#webpage'
    article_id = f'{canonical_url}#article'
    breadcrumb_id = f'{canonical_url}#breadcrumb'
    image_objects = [
        {'@type': 'ImageObject', 'url': og_image, 'width': 1200, 'height': 630},
        {'@type': 'ImageObject', 'url': wechat_image, 'width': 300, 'height': 300},
    ]
    return {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'WebSite',
                '@id': website_id,
                'url': site_url,
                'name': '织梦空间 / PolaZhenJing',
                'alternateName': ['织梦空间', 'Pola 真经'],
                'inLanguage': 'zh-CN',
                'publisher': {'@id': organization_id},
            },
            {
                '@type': 'Organization',
                '@id': organization_id,
                'name': '织梦空间',
                'url': site_url,
                'logo': {'@type': 'ImageObject', 'url': _absolute_asset_url('/assets/images/test_cover.jpg')},
            },
            {
                '@type': 'Person',
                '@id': person_id,
                'name': '炽驹 Polaris',
                'url': about_url,
                'affiliation': {'@id': organization_id},
            },
            {
                '@type': 'BreadcrumbList',
                '@id': breadcrumb_id,
                'itemListElement': [
                    {
                        '@type': 'ListItem',
                        'position': 1,
                        'name': '织梦空间',
                        'item': site_url,
                    },
                    {
                        '@type': 'ListItem',
                        'position': 2,
                        'name': '文章',
                        'item': _absolute_public_url('/articles'),
                    },
                    {
                        '@type': 'ListItem',
                        'position': 3,
                        'name': title,
                        'item': canonical_url,
                    },
                ],
            },
            {
                '@type': 'WebPage',
                '@id': webpage_id,
                'url': canonical_url,
                'name': title,
                'description': description,
                'isPartOf': {'@id': website_id},
                'breadcrumb': {'@id': breadcrumb_id},
                'primaryImageOfPage': image_objects[0],
                'inLanguage': 'zh-CN',
            },
            {
                '@type': 'Article',
                '@id': article_id,
                'headline': title,
                'description': description,
                'url': canonical_url,
                'mainEntityOfPage': {'@id': webpage_id},
                'sameAs': [short_url, share_card_url],
                'image': image_objects,
                'inLanguage': 'zh-CN',
                'datePublished': date_published,
                'dateModified': date_modified,
                'keywords': keywords,
                'articleSection': section,
                'wordCount': word_count,
                'timeRequired': f'PT{read_time}M',
                'author': {'@id': person_id},
                'publisher': {'@id': organization_id},
                'about': [{'@type': 'Thing', 'name': keyword} for keyword in keywords],
            },
        ],
    }


def _wechat_nonce() -> str:
    return hashlib.sha1(f'{time.time()}:{os.urandom(8).hex()}'.encode()).hexdigest()[:16]


def _wechat_get_json(url: str) -> dict:
    import requests
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    data = resp.json()
    if data.get('errcode'):
        raise RuntimeError(data.get('errmsg') or f'WeChat API error {data.get("errcode")}')
    return data


def _wechat_jsapi_ticket() -> str:
    """Fetch and cache JS-SDK ticket when official account env vars exist."""
    now_ts = int(time.time())
    app_id = os.getenv('WECHAT_MP_APP_ID', '').strip()
    app_secret = os.getenv('WECHAT_MP_APP_SECRET', '').strip()
    if not app_id or not app_secret:
        return ''
    if WECHAT_TICKET_CACHE['jsapi_ticket_expires_at'] > now_ts + 60:
        return WECHAT_TICKET_CACHE['jsapi_ticket']
    if WECHAT_TICKET_CACHE['access_token_expires_at'] <= now_ts + 60:
        token_url = (
            'https://api.weixin.qq.com/cgi-bin/token'
            f'?grant_type=client_credential&appid={app_id}&secret={app_secret}'
        )
        token_data = _wechat_get_json(token_url)
        WECHAT_TICKET_CACHE['access_token'] = token_data.get('access_token', '')
        WECHAT_TICKET_CACHE['access_token_expires_at'] = now_ts + int(token_data.get('expires_in', 7200))
    ticket_url = (
        'https://api.weixin.qq.com/cgi-bin/ticket/getticket'
        f'?access_token={WECHAT_TICKET_CACHE["access_token"]}&type=jsapi'
    )
    ticket_data = _wechat_get_json(ticket_url)
    WECHAT_TICKET_CACHE['jsapi_ticket'] = ticket_data.get('ticket', '')
    WECHAT_TICKET_CACHE['jsapi_ticket_expires_at'] = now_ts + int(ticket_data.get('expires_in', 7200))
    return WECHAT_TICKET_CACHE['jsapi_ticket']


def _canonical_body_from_form(form, preserve_media: bool = True) -> str:
    """Return canonical Markdown body from the edit/upload form shape."""
    content_format = (form.get('content_format') or 'markdown').strip().lower()
    body = (form.get('body') or '').strip()
    rich_body = (form.get('rich_content') or '').strip()
    markdown_body = (form.get('content') or '').strip()
    if content_format == 'rich_html':
        body = body or rich_body or markdown_body
    else:
        body = body or markdown_body or rich_body

    return canonicalize_editor_content(
        body,
        content_format,
        preserve_media=preserve_media,
        image_localizer=_localize_rich_html_images if preserve_media else None,
    )


def _build_post_markdown(form, canonical_body: str | None = None) -> str:
    """Build a Jekyll post from edit form fields."""
    layout = form.get('layout', 'deep-technical').strip() or 'deep-technical'
    theme = form.get('theme', _get_theme()).strip() or _get_theme()
    title = form.get('title', '').strip() or '无标题'
    date_value = form.get('date', '').strip() or datetime.now().strftime('%Y-%m-%d')
    summary = form.get('summary', '').strip()
    description = form.get('description', '').strip()
    body = canonical_body if canonical_body is not None else _canonical_body_from_form(form)

    front = [
        '---',
        f'layout: {layout}',
        f'theme: {theme}',
        f'title: {_yaml_quote(title)}',
        f'date: {date_value}',
        f'tags: {_tags_front_matter(form.get("tags", ""))}',
    ]
    if description:
        front.append(f'description: {_yaml_quote(description)}')
    if summary:
        front.append(f'summary: {_yaml_quote(summary)}')
    extra_front_matter = form.get('extra_front_matter', '').strip()
    if extra_front_matter:
        front.extend(line for line in extra_front_matter.splitlines() if line.strip())
    front.append('---')
    return '\n'.join(front) + '\n\n' + body + '\n'


def _sync_project_to_github(project_root: str, commit_msg: str) -> tuple[bool, str]:
    """Commit and push current project changes."""
    subprocess.run(['git', 'add', '-A'], cwd=project_root,
                   capture_output=True, timeout=30)
    commit_result = subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_root,
                                   capture_output=True, timeout=30, text=True)
    push_result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=project_root,
                                 capture_output=True, timeout=120, text=True)
    if push_result.returncode == 0:
        return True, push_result.stdout
    detail = push_result.stderr or commit_result.stderr or push_result.stdout
    return False, detail


@uploader_bp.route('/api/check-pages-url')
def check_pages_url():
    """Check if a GitHub Pages URL is live (returns 200)."""
    import requests as _requests
    url = request.args.get('url', '')
    if not url.startswith(GITHUB_PAGES_BASE):
        return jsonify({'live': False, 'url': url})
    try:
        resp = _requests.head(url, timeout=8, allow_redirects=True)
        live = resp.status_code == 200
    except Exception:
        live = False
    return jsonify({'live': live, 'url': url})


@uploader_bp.route('/api/editor/convert', methods=['POST'])
@login_required
def editor_convert():
    """Convert article editor content between Markdown and rich HTML."""
    payload = request.get_json(silent=True) or request.form
    content = payload.get('content', '')
    source_format = (payload.get('source_format') or 'markdown').strip().lower()
    target_format = (payload.get('target_format') or 'markdown').strip().lower()
    try:
        if target_format in {'rich', 'rich_html', 'html'}:
            markdown_body = canonicalize_editor_content(
                content,
                source_format,
                preserve_media=True,
                image_localizer=_localize_rich_html_images if source_format == 'rich_html' else None,
            )
            converted = markdown_to_editor_html(markdown_body, asset_base=_article_asset_base())
            return jsonify({
                'ok': True,
                'content': converted,
                'canonical_markdown': markdown_body,
                'format': 'rich_html',
                'warnings': [],
            })
        markdown_body = canonicalize_editor_content(
            content,
            source_format,
            preserve_media=True,
            image_localizer=_localize_rich_html_images if source_format == 'rich_html' else None,
        )
        return jsonify({
            'ok': True,
            'content': markdown_body,
            'canonical_markdown': markdown_body,
            'format': 'markdown',
            'warnings': [],
        })
    except Exception as exc:
        logger.exception('Editor convert failed')
        return jsonify({'ok': False, 'error': f'转换失败：{exc}'}), 500


@uploader_bp.route('/api/editor/preview', methods=['POST'])
@login_required
def editor_preview():
    """Render a save-equivalent article preview for upload/edit editors."""
    payload = request.get_json(silent=True) or request.form
    content = payload.get('content') or payload.get('body') or ''
    content_format = (payload.get('content_format') or 'markdown').strip().lower()
    try:
        result = render_article_preview(
            content,
            content_format,
            asset_base=_article_asset_base(),
            preserve_media=True,
            image_localizer=_localize_rich_html_images if content_format == 'rich_html' else None,
        )
        return jsonify({
            'ok': True,
            'html': result.html,
            'canonical_markdown': result.canonical_markdown,
            'format': 'markdown',
            'warnings': result.warnings,
        })
    except Exception as exc:
        logger.exception('Editor preview failed')
        return jsonify({'ok': False, 'error': f'预览失败：{exc}'}), 500


@uploader_bp.route('/api/wechat/share-config')
def wechat_share_config():
    """Return optional WeChat JS-SDK signature for in-WeChat article sharing."""
    app_id = os.getenv('WECHAT_MP_APP_ID', '').strip()
    page_url = (request.args.get('url') or '').split('#', 1)[0].strip()
    if not app_id:
        return jsonify({'configured': False, 'reason': 'missing-wechat-app-id'})
    if not page_url.startswith(('https://aipd.me/', 'http://aipd.me/')):
        return jsonify({'configured': False, 'reason': 'invalid-url'}), 400
    try:
        ticket = _wechat_jsapi_ticket()
        if not ticket:
            return jsonify({'configured': False, 'reason': 'missing-wechat-ticket'})
        timestamp = int(time.time())
        nonce_str = _wechat_nonce()
        plain = (
            f'jsapi_ticket={ticket}&noncestr={nonce_str}'
            f'&timestamp={timestamp}&url={page_url}'
        )
        signature = hashlib.sha1(plain.encode('utf-8')).hexdigest()
        return jsonify({
            'configured': True,
            'appId': app_id,
            'timestamp': timestamp,
            'nonceStr': nonce_str,
            'signature': signature,
        })
    except Exception as exc:
        current_app.logger.warning('WeChat share config failed: %s', exc)
        return jsonify({'configured': False, 'reason': 'wechat-api-error'}), 502


@uploader_bp.route('/api/wechat/share-diagnostics', methods=['GET', 'POST'])
def wechat_share_diagnostics():
    """Record non-sensitive JS-SDK share status from real WeChat webviews."""
    payload = request.args if request.method == 'GET' else (request.get_json(silent=True) or {})

    def _clip(value: object, max_chars: int = 240) -> str:
        text = str(value or '').strip()
        return text[:max_chars]

    page_url = _clip(payload.get('page_url'))
    share_url = _clip(payload.get('share_url'))
    if not page_url.startswith(('https://aipd.me/', 'http://aipd.me/')):
        return jsonify({'ok': False, 'reason': 'invalid-page-url'}), 400
    if share_url and not share_url.startswith(('https://aipd.me/', 'http://aipd.me/')):
        return jsonify({'ok': False, 'reason': 'invalid-share-url'}), 400

    status = _clip(payload.get('status'), 32)
    log_method = current_app.logger.info if status == 'ready' else current_app.logger.warning
    log_method(
        'WeChat share diagnostics status=%s page=%s share=%s err=%s ua=%s',
        status,
        page_url,
        share_url,
        _clip(payload.get('err_msg')),
        _clip(request.headers.get('User-Agent'), 160),
    )
    if request.method == 'GET':
        return ('', 204)
    return jsonify({'ok': True})


@uploader_bp.route('/articles/<filename>')
def view_article(filename):
    """Preview a single article."""
    return _render_article(filename, public=not _is_admin_session())


@public_articles_bp.route('/articles/<filename>')
def public_article_view(filename):
    """Public read-only article detail."""
    return _render_article(filename, public=True)


@public_articles_bp.route('/articles/<filename>/like', methods=['GET', 'POST'])
def public_article_like(filename):
    """Return or update the lightweight public like count for an article."""
    fpath = _safe_post_path(filename)
    if not fpath or not os.path.isfile(fpath):
        return jsonify({'ok': False, 'error': 'not_found'}), 404

    actual_filename = os.path.basename(fpath)
    article_id = _article_admin_filename(actual_filename)
    db = get_db()

    if request.method == 'GET':
        return jsonify({
            'ok': True,
            'article_id': article_id,
            'like_count': _article_like_count(article_id),
        })

    payload = request.get_json(silent=True) or {}
    liked = bool(payload.get('liked', True))
    db.execute(
        'INSERT OR IGNORE INTO article_likes (article_id, like_count) VALUES (?, 0)',
        (article_id,),
    )
    if liked:
        db.execute(
            '''
            UPDATE article_likes
               SET like_count = like_count + 1,
                   updated_at = CURRENT_TIMESTAMP
             WHERE article_id = ?
            ''',
            (article_id,),
        )
    else:
        db.execute(
            '''
            UPDATE article_likes
               SET like_count = MAX(like_count - 1, 0),
                   updated_at = CURRENT_TIMESTAMP
             WHERE article_id = ?
            ''',
            (article_id,),
        )
    db.commit()
    return jsonify({
        'ok': True,
        'article_id': article_id,
        'liked': liked,
        'like_count': _article_like_count(article_id),
    })


@public_articles_bp.route('/s/<code>')
def public_article_short_link(code):
    """Render a public article from its stable short-link code."""
    actual_filename = _resolve_short_code(code)
    if not actual_filename:
        return render_template('public_article_404.html'), 404
    return _render_article(_article_admin_filename(actual_filename), public=True)


@public_articles_bp.route('/c/<code>')
def public_article_card_link(code):
    """Render a lightweight social-card page for crawlers and sharing apps."""
    actual_filename = _resolve_short_code(code)
    if not actual_filename:
        return render_template('public_article_404.html'), 404
    fpath = os.path.join(POSTS_DIR, actual_filename)
    if not os.path.isfile(fpath):
        return render_template('public_article_404.html'), 404
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    meta, _, body = _parse_post(raw)
    body = normalize_markdown(body).replace('{{ site.baseurl }}', _article_asset_base())
    share = _build_article_share_context(actual_filename, meta, body, fpath)
    response = current_app.response_class(
        render_template('article_share_card.html',
                        meta=meta,
                        share=share,
                        share_logo=_absolute_asset_url('/assets/images/test_cover.jpg')),
        mimetype='text/html; charset=utf-8',
    )
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response


@public_articles_bp.route('/sitemap.xml')
def public_sitemap():
    """Dynamic sitemap including public articles from the current server posts."""
    from xml.sax.saxutils import escape as xml_escape

    static_urls = [
        {'loc': _absolute_public_url('/'), 'changefreq': 'weekly', 'priority': '1.0'},
        {'loc': _absolute_public_url('/agent.html'), 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': _absolute_public_url('/about.html'), 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': _absolute_public_url('/articles'), 'changefreq': 'daily', 'priority': '0.8'},
        {'loc': _absolute_public_url('/feed.xml'), 'changefreq': 'daily', 'priority': '0.4'},
        {'loc': _absolute_public_url('/articles.json'), 'changefreq': 'daily', 'priority': '0.4'},
        {'loc': _absolute_public_url('/llms.txt'), 'changefreq': 'daily', 'priority': '0.3'},
    ]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for item in static_urls:
        lines.extend([
            '  <url>',
            f'    <loc>{xml_escape(item["loc"])}</loc>',
            f'    <changefreq>{item["changefreq"]}</changefreq>',
            f'    <priority>{item["priority"]}</priority>',
            '  </url>',
        ])
    for article in _public_article_records():
        lines.extend([
            '  <url>',
            f'    <loc>{xml_escape(article["canonical_url"])}</loc>',
            f'    <lastmod>{xml_escape(article["lastmod"])}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.7</priority>',
            '  </url>',
        ])
    lines.append('</urlset>')
    return current_app.response_class('\n'.join(lines) + '\n', mimetype='application/xml')


@public_articles_bp.route('/robots.txt')
def public_robots_txt():
    """Dynamic robots.txt with sitemap and admin exclusions."""
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /PolaZhenjing/admin/',
        '',
        f'Sitemap: {_absolute_public_url("/sitemap.xml")}',
        '',
    ]
    return current_app.response_class('\n'.join(lines), mimetype='text/plain; charset=utf-8')


@public_articles_bp.route('/feed.xml')
def public_feed_xml():
    """RSS feed for recent public articles."""
    from xml.sax.saxutils import escape as xml_escape

    articles = _public_article_records(limit=50)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '  <channel>',
        '    <title>织梦空间 / PolaZhenJing</title>',
        f'    <link>{xml_escape(_absolute_public_url("/articles"))}</link>',
        '    <description>AI 产品、Agent 工作流、企业软件、数据基础设施和个人知识生产实践。</description>',
        '    <language>zh-CN</language>',
        f'    <lastBuildDate>{datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>',
    ]
    for item in articles:
        lines.extend([
            '    <item>',
            f'      <title>{xml_escape(item["title"])}</title>',
            f'      <link>{xml_escape(item["canonical_url"])}</link>',
            f'      <guid isPermaLink="true">{xml_escape(item["canonical_url"])}</guid>',
            f'      <description>{xml_escape(item["summary"])}</description>',
            f'      <pubDate>{xml_escape(item["date"])}</pubDate>',
        ])
        for keyword in item.get('keywords') or []:
            lines.append(f'      <category>{xml_escape(keyword)}</category>')
        lines.extend([
            '    </item>',
        ])
    lines.extend(['  </channel>', '</rss>'])
    return current_app.response_class('\n'.join(lines) + '\n', mimetype='application/rss+xml')


@public_articles_bp.route('/articles.json')
def public_articles_json_feed():
    """Machine-readable article feed for agents and content discovery."""
    articles = _public_article_records(limit=80)
    payload = {
        'version': 'https://jsonfeed.org/version/1.1',
        'title': '织梦空间 / PolaZhenJing',
        'home_page_url': _absolute_public_url('/'),
        'feed_url': _absolute_public_url('/articles.json'),
        'description': 'AI 产品、Agent 工作流、企业软件、数据基础设施和个人知识生产实践。',
        'language': 'zh-CN',
        'items': [
            {
                'id': item['canonical_url'],
                'url': item['canonical_url'],
                'external_url': item['short_url'],
                'title': item['title'],
                'summary': item['summary'],
                'date_published': item['date'],
                'date_modified': item['lastmod_iso'],
                'tags': item.get('keywords') or [],
                'section': item.get('section') or '',
                'reading_time_minutes': item.get('read_time') or 1,
                'word_count': item.get('word_count') or 0,
            }
            for item in articles
        ],
    }
    return jsonify(payload)


@public_articles_bp.route('/llms.txt')
def public_llms_txt():
    """Dynamic llms.txt for AI search and generative engine discovery."""
    articles = _public_article_records(limit=30)
    lines = [
        '# 织梦空间 / PolaZhenJing',
        '',
        '> AI 产品、Agent 工作流、企业软件、数据基础设施和个人知识生产实践。',
        '',
        '## Canonical Entry Points',
        '',
        f'- Home: {_absolute_public_url("/")}',
        f'- Articles: {_absolute_public_url("/articles")}',
        f'- Agent: {_absolute_public_url("/agent.html")}',
        f'- About: {_absolute_public_url("/about.html")}',
        f'- Sitemap: {_absolute_public_url("/sitemap.xml")}',
        f'- RSS Feed: {_absolute_public_url("/feed.xml")}',
        f'- JSON Feed: {_absolute_public_url("/articles.json")}',
        f'- Robots: {_absolute_public_url("/robots.txt")}',
        '',
        '## Site Identity',
        '',
        '- Name: 织梦空间 / PolaZhenJing',
        '- Language: zh-CN',
        '- Author: 炽驹 Polaris',
        '- Topics: AI 产品, Agent 工作流, 企业软件, 数据基础设施, 个人知识生产',
        '',
        '## Share Metadata Contract',
        '',
        '- Canonical URLs under `/articles/*.md` are preferred for citation and indexing.',
        '- Shortlinks under `/s/<code>` are preferred for human sharing and social cards.',
        '- WeChat uses a 300x300 JPEG share image through JS-SDK `imgUrl`.',
        '- Jike, X, and generic crawlers should use Open Graph `og:title`, `og:description`, and 1200x630 `og:image`.',
        '',
        '## Article Index',
        '',
    ]
    for item in articles:
        keywords = ', '.join(item.get('keywords') or [])
        lines.extend([
            f'### {item["title"]}',
            '',
            f'- Date: {item["date"]}',
            f'- Canonical: {item["canonical_url"]}',
            f'- Shortlink: {item["short_url"]}',
            f'- Summary: {item["summary"]}',
            f'- Section: {item["section"]}',
            f'- Reading time: {item["read_time"]} minutes',
        ])
        if keywords:
            lines.append(f'- Keywords: {keywords}')
        lines.append('')
    lines.extend([
        '## AI Agent Guidance',
        '',
        '- Prefer canonical URLs for citation and shortlinks for human sharing.',
        '- Treat `/PolaZhenjing/admin/*` as authenticated admin content, not public content.',
        '- Use article summaries and JSON-LD metadata before inferring unstated claims.',
        '',
    ])
    return current_app.response_class('\n'.join(lines), mimetype='text/plain; charset=utf-8')


def _render_article(filename: str, public: bool = False):
    fpath = _safe_post_path(filename)
    if not fpath or not os.path.isfile(fpath):
        if public:
            return render_template('public_article_404.html'), 404
        flash('文章未找到。', 'error')
        return redirect(url_for('uploader.articles'))
    actual_filename = os.path.basename(fpath)
    admin_filename = _article_admin_filename(actual_filename)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    meta, _, body = _parse_post(raw)
    # Render markdown to HTML. Article media lives under the PolaZhenjing app
    # asset route even when the public article itself is mounted at /articles/.
    body = normalize_markdown(body).replace('{{ site.baseurl }}', _article_asset_base())
    share = _build_article_share_context(actual_filename, meta, body, fpath)
    title = share['title']
    share_title = share['share_title']
    body_html = md_lib.markdown(body, extensions=['extra', 'codehilite', 'toc', 'tables'])
    body_html = _remove_duplicate_leading_heading(body_html, title)
    github_url = f'https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/_posts/{actual_filename}'
    # Build GitHub Pages article URL from Jekyll permalink /:year/:month/:day/:title/
    pages_url = _build_pages_url(actual_filename)
    short_code = share['short_code']
    canonical_url = share['canonical_url']
    short_url = share['short_url']
    share_card_url = share['share_card_url']
    share_url = share_card_url
    read_time = share['read_time']
    # Get style accent color
    layout = share['layout']
    accent_color = STYLE_ACCENTS.get(layout, '#E4BF7A')
    share_description = share['share_description']
    wechat_share_image = share['wechat_share_image']
    og_share_image = share['og_share_image']
    wechat_share_config_url = _absolute_public_url('/PolaZhenjing/admin/api/wechat/share-config')
    wechat_share_diagnostics_url = _absolute_public_url('/PolaZhenjing/admin/api/wechat/share-diagnostics')
    share_logo = _absolute_asset_url('/assets/images/test_cover.jpg')
    article_asset_base = _article_asset_base()
    article_keywords = share['article_keywords']
    article_section = share['article_section']
    article_published_time = share['article_published_time']
    article_modified_time = share['article_modified_time']
    article_word_count = share['article_word_count']
    article_json_ld = _article_json_ld_graph(
        title=share_title,
        description=share_description,
        canonical_url=canonical_url,
        short_url=short_url,
        share_card_url=share_card_url,
        og_image=og_share_image,
        wechat_image=wechat_share_image,
        keywords=article_keywords,
        section=article_section,
        date_published=article_published_time,
        date_modified=article_modified_time,
        word_count=article_word_count,
        read_time=read_time,
    )
    article_navigation = _article_navigation_context(actual_filename)
    article_like_count = _article_like_count(admin_filename)
    article_like_url = url_for('public_articles.public_article_like', filename=admin_filename)
    admin_edit_url = _polazhenjing_admin_url('uploader.edit_article',
                                             filename=admin_filename)
    admin_publish_url = _polazhenjing_admin_url('social_publish.article',
                                                filename=admin_filename)
    admin_delete_url = _polazhenjing_admin_url('uploader.delete_article',
                                               filename=admin_filename)
    return render_template('article_view.html',
                           filename=filename, meta=meta,
                           admin_filename=admin_filename,
                           actual_filename=actual_filename,
                           body_html=body_html, github_url=github_url,
                           pages_url=pages_url, read_time=read_time,
                           canonical_url=canonical_url,
                           short_code=short_code,
                           short_url=short_url,
                           share_card_url=share_card_url,
                           share_url=share_url,
                           share_title=share_title,
                           share_description=share_description,
                           wechat_share_image=wechat_share_image,
                           og_share_image=og_share_image,
                           wechat_share_config_url=wechat_share_config_url,
                           wechat_share_diagnostics_url=wechat_share_diagnostics_url,
                           share_logo=share_logo,
                           article_json_ld=article_json_ld,
                           article_asset_base=article_asset_base,
                           article_keywords=article_keywords,
                           article_section=article_section,
                           article_published_time=article_published_time,
                           article_modified_time=article_modified_time,
                           article_word_count=article_word_count,
                           article_navigation=article_navigation,
                           article_like_count=article_like_count,
                           article_like_url=article_like_url,
                           admin_edit_url=admin_edit_url,
                           admin_publish_url=admin_publish_url,
                           admin_delete_url=admin_delete_url,
                           accent_color=accent_color,
                           is_public=public,
                           can_manage=_is_admin_session(),
                           show_admin_nav=_is_admin_session())


@uploader_bp.route('/articles/<filename>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(filename):
    """Edit an existing Markdown/Jekyll article."""
    post = load_post(filename, POSTS_DIR)
    if not post:
        flash('文章未找到。', 'error')
        return redirect(url_for('uploader.articles'))
    fpath = post.path
    actual_filename = post.actual_filename
    admin_filename = post.admin_filename

    if request.method == 'POST':
        form_data = request.form.copy()
        ai_revision_enabled = _form_flag(form_data.get('enable_ai_revision'))
        revision_instruction = form_data.get('revision_instruction', '').strip() if ai_revision_enabled else ''
        rewrite_rate = _parse_rewrite_rate(form_data.get('rewrite_rate'), default=50)
        canonical_body = _canonical_body_from_form(form_data, preserve_media=True)
        if ai_revision_enabled and revision_instruction:
            revised_body = _apply_revision_instruction(
                canonical_body,
                form_data.get('title', filename).strip() or filename,
                revision_instruction,
                form_data.get('layout', ''),
                rewrite_rate=rewrite_rate,
            )
            if revised_body:
                canonical_body = normalize_markdown(
                    _ensure_original_media(revised_body, _extract_markdown_media_blocks(canonical_body))
                )
                form_data['body'] = canonical_body
                form_data['content_format'] = 'markdown'
                flash('已根据修改建议简述完成正文调整。', 'success')
            else:
                if rewrite_rate <= 0:
                    flash('AI 改写率为 0%，已跳过修改建议并保存当前正文。', 'info')
                else:
                    flash('修改建议未能自动应用，已保存当前正文。', 'warning')
        post_markdown = _build_post_markdown(form_data, canonical_body=canonical_body)
        write_post(fpath, post_markdown)
        if request.form.get('save_mode') == 'sync':
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            ok, detail = _sync_project_to_github(
                project_root,
                f'Edit article: {request.form.get("title", filename).strip() or filename}',
            )
            if ok:
                flash('文章已保存并同步到 GitHub。', 'success')
            else:
                flash(f'文章已保存，但同步失败：{detail}', 'warning')
        else:
            flash('文章已保存。', 'success')
        return redirect(url_for('uploader.view_article', filename=admin_filename))

    meta, front_lines, body = post.meta, post.front_lines, post.body
    known_front_keys = {'layout', 'theme', 'title', 'date', 'tags', 'description', 'summary'}
    extra_front_matter = '\n'.join(
        line for line in front_lines
        if (line.split(':', 1)[0].strip() if ':' in line else line.strip()) not in known_front_keys
    )
    return render_template(
        'article_edit.html',
        filename=admin_filename,
        actual_filename=actual_filename,
        meta=meta,
        body=body,
        tag_value=_tags_input_value(meta.get('tags', '')),
        extra_front_matter=extra_front_matter,
        styles=STYLES,
        themes=THEMES,
        pages_url=_build_pages_url(actual_filename),
    )


@uploader_bp.route('/articles/<filename>/preview', methods=['POST'])
@login_required
def preview_article_markdown(filename):
    """Render the edited body through the same canonical Markdown pipeline as save."""
    post = load_post(filename, POSTS_DIR)
    if not post:
        return jsonify({'ok': False, 'error': '文章未找到。'}), 404
    body = request.form.get('body', '')
    content_format = (request.form.get('content_format') or 'markdown').strip().lower()
    try:
        result = render_article_preview(
            body,
            content_format,
            asset_base=_article_asset_base(),
            preserve_media=True,
            image_localizer=_localize_rich_html_images if content_format == 'rich_html' else None,
        )
    except Exception as exc:
        logger.exception('Article edit preview failed')
        return jsonify({'ok': False, 'error': f'预览失败：{exc}'}), 500
    return jsonify({
        'ok': True,
        'html': result.html,
        'canonical_markdown': result.canonical_markdown,
        'format': 'markdown',
        'warnings': result.warnings,
    })


@uploader_bp.route('/articles/<filename>/delete', methods=['POST'])
@login_required
def delete_article(filename):
    fpath = _safe_post_path(filename)
    if fpath and os.path.isfile(fpath):
        actual_filename = os.path.basename(fpath)
        os.remove(fpath)
        flash(f'已删除 {_article_admin_filename(actual_filename)}。', 'info')
    else:
        flash('文章未找到。', 'error')
    return redirect(url_for('uploader.articles'))


@uploader_bp.route('/sync', methods=['POST'])
@login_required
def sync():
    """Safely commit article assets and push to deploy."""
    project_root = os.path.join(os.path.dirname(__file__), '..')
    try:
        msg = f'Update articles - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        result = guarded_commit_and_push(
            project_root,
            msg,
            push_args=['push', '-u', 'origin', 'main'],
        )
        if result.pushed:
            flash('已成功同步到 GitHub。', 'success')
        else:
            flash('没有可同步的文章或图片变更。', 'info')
    except GitSafetyError as e:
        flash(f'同步被安全规则阻止：{e}', 'error')
    except Exception as e:
        flash(f'同步错误：{e}', 'error')
    return redirect(url_for('uploader.articles'))


@uploader_bp.route('/theme', methods=['GET', 'POST'])
@login_required
def theme_select_page():
    """UI theme switcher — wukong / claude / pmframe."""
    if request.method == 'POST':
        theme_id = request.form.get('theme', 'wukong')
        valid_ids = {t['id'] for t in THEMES}
        if theme_id in valid_ids:
            _set_theme(theme_id)
            theme_name = next(t['name'] for t in THEMES if t['id'] == theme_id)
            flash(f'UI 主题已切换为「{theme_name}」。', 'success')
        else:
            flash('无效的主题。', 'error')
        return redirect(url_for('uploader.theme_select_page'))
    return render_template('theme_select.html', themes=THEMES,
                           current_theme=_get_theme())
