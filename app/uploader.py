"""Upload and article management blueprint."""
import os
import re
import subprocess
import tempfile
import json
import hashlib
import logging
import shutil
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

import markdown as md_lib
from werkzeug.utils import secure_filename

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for, current_app)

from .auth import login_required
from .converter import (detect_and_convert, extract_title,
                        fetch_url_as_markdown, URLFetchBlocked)
from . import jobs

logger = logging.getLogger(__name__)

uploader_bp = Blueprint('uploader', __name__, url_prefix='/admin')

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


def _get_theme() -> str:
    """Read current UI theme from data/theme.json. Default: wukong."""
    try:
        if os.path.isfile(THEME_FILE):
            with open(THEME_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('theme', 'wukong')
    except Exception:
        pass
    return 'wukong'


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
MINIMAX_MODEL = 'MiniMax-M2.7'

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


def _call_llm_rewrite(content: str, title: str, system_prompt: str) -> str | None:
    """Call MiniMax LLM to rewrite content using the given skill prompt.

    Returns rewritten content string, or None on failure.
    """
    api_key = _get_minimax_api_key()
    if not api_key:
        logger.warning('MINIMAX_TOKEN_PLAN_API_KEY not found, skipping LLM rewrite')
        return None

    user_msg = (
        f'请根据以下素材，以你的风格写一篇公众号长文。必须严格围绕素材的实际论点与主题展开，'
        f'不要自行替换主题、混入无关个人经历或凭空构造事实。如果素材是个人博客/技术解读，'
        f'保留原文的代码例子、术语和数据。标题是「{title}」，保持标题与正文语义一致。\n\n'
        f'素材内容：\n{content}'
    )

    payload = json.dumps({
        'model': MINIMAX_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_msg},
        ],
        'temperature': 0.8,
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


def _save_draft(content: str, title: str, tags: str, description: str,
                illustration_files=None) -> str:
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
        meta = {'filename': fname, 'path': fpath}
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
    parts = filename.replace('.md', '').split('-', 3)
    pages_url = _build_pages_url(filename) if len(parts) >= 4 else url_for('uploader.articles')
    return {
        'filename': filename,
        'title': title,
        'date': date,
        'summary': summary,
        'layout': meta.get('layout', ''),
        'theme': meta.get('theme', ''),
        'cover': cover,
        'url': pages_url,
        'admin_url': url_for('uploader.view_article', filename=filename),
    }


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
                title = extract_title(content)
            except Exception as e:
                flash(f'转换错误：{e}', 'error')
                return render_template('upload.html')

        # Handle paste content
        elif request.form.get('content', '').strip():
            content = request.form['content'].strip()
            title = extract_title(content)

        # Handle URL input
        elif request.form.get('url', '').strip():
            url = request.form['url'].strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                flash('请输入以 http:// 或 https:// 开头的 URL。', 'error')
                return render_template('upload.html')
            try:
                content, fetched_title = fetch_url_as_markdown(url)
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
        draft_id = _save_draft(content,
                               request.form.get('title', '').strip() or title,
                               request.form.get('tags', '').strip(),
                               request.form.get('description', '').strip(),
                               request.files.getlist('illustrations'))
        session['draft_id'] = draft_id
        return redirect(url_for('uploader.style_select'))

    return render_template('upload.html')


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
        'style': style,
        'theme': theme,
        'project_root': project_root,
    }

    job_id = jobs.create_job(kind='generate', user_id=session.get('user_id'), title=title)
    jobs.submit(_run_generate_job, job_id, payload)

    return redirect(url_for('uploader.generate_status', job_id=job_id))


def _run_generate_job(job_id: str, p: dict):
    """Background worker: LLM rewrite → build post → write file → git push.

    Runs in a daemon thread, owns no Flask context, updates job state via
    the `jobs` module for the polling UI.
    """
    content = p['content']
    title = p['title']
    tags = p['tags']
    description = p['description']
    inserted_images = p.get('inserted_images') or []
    style = p['style']
    theme = p['theme']
    project_root = p['project_root']

    jobs.update_job(job_id, status=jobs.RUNNING, stage='加载草稿内容…', progress=5)

    # ── LLM skill rewriting ──────────────────────────────────
    skill_prompt = _get_style_prompt(style)
    if skill_prompt:
        jobs.update_job(job_id, stage=f'LLM 正在以「{style}」风格重写…', progress=15)
        rewritten = _call_llm_rewrite(content, title, skill_prompt)
        if rewritten:
            content = rewritten
            jobs.append_message(job_id, 'info', f'已使用 LLM 技能重写内容（风格：{style}）。')
        else:
            jobs.append_message(job_id, 'warning', 'LLM 重写失败，将使用原始内容。')

    # ── Ghibli-style illustrations ───────────────────────────
    # Derive slug early so illustration files and post file share the same name.
    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = _slugify(title) or 'untitled'

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
    filename = f'{date_str}-{slug}.md'

    # Front matter
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
    front_matter = f"""---
layout: {style}
theme: {theme}
title: "{title}"
date: {date_str}
tags: [{', '.join(tag_list)}]"""

    if description:
        front_matter += f'\ndescription: "{description}"'

    # Generate summary
    summary = _generate_summary(content)
    if summary:
        safe_summary = summary.replace('"', '\\"')
        front_matter += f'\nsummary: "{safe_summary}"'

    front_matter += '\n---\n\n'

    # Write to _posts/
    posts_dir = os.path.join(project_root, '_posts')
    os.makedirs(posts_dir, exist_ok=True)
    post_path = os.path.join(posts_dir, filename)
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)

    # Auto-sync to GitHub
    jobs.update_job(job_id, stage='正在同步到 GitHub…', progress=85)
    try:
        subprocess.run(['git', 'add', '-A'], cwd=project_root,
                       capture_output=True, timeout=30)
        commit_msg = f'Add article: {title} - {date_str}'
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_root,
                       capture_output=True, timeout=30)
        push_result = subprocess.run(
            ['git', 'push', '-u', 'origin', 'main'], cwd=project_root,
            capture_output=True, timeout=120, text=True)
        if push_result.returncode == 0:
            jobs.append_message(job_id, 'success',
                                f'文章「{title}」已以 {style} 风格创建，并已同步到 GitHub。')
        else:
            jobs.append_message(job_id, 'warning',
                                f'文章「{title}」已创建，但推送失败：{push_result.stderr}')
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

    return jsonify({
        'status': job['status'],
        'stage': job.get('stage') or '',
        'progress': job.get('progress') or 0,
        'error': job.get('error'),
        'messages': job.get('messages') or [],
        'articles_url': url_for('uploader.articles'),
    })


@uploader_bp.route('/articles')
@login_required
def articles():
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
    if not filename or '/' in filename or '\\' in filename or not filename.endswith('.md'):
        return None
    fpath = os.path.abspath(os.path.join(POSTS_DIR, filename))
    posts_root = os.path.abspath(POSTS_DIR)
    if not fpath.startswith(posts_root + os.sep):
        return None
    return fpath


def _parse_post(raw: str) -> tuple[dict, list[str], str]:
    """Parse the simple Jekyll front matter used by this project."""
    meta: dict = {}
    front_lines: list[str] = []
    body = raw
    if raw.startswith('---'):
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            front_lines = parts[1].strip().split('\n')
            body = parts[2].strip()
            for line in front_lines:
                if ':' not in line:
                    continue
                key, value = line.split(':', 1)
                meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, front_lines, body


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


def _build_post_markdown(form) -> str:
    """Build a Jekyll post from edit form fields."""
    layout = form.get('layout', 'deep-technical').strip() or 'deep-technical'
    theme = form.get('theme', _get_theme()).strip() or _get_theme()
    title = form.get('title', '').strip() or '无标题'
    date_value = form.get('date', '').strip() or datetime.now().strftime('%Y-%m-%d')
    summary = form.get('summary', '').strip()
    description = form.get('description', '').strip()
    body = form.get('body', '').strip()

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
@login_required
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


@uploader_bp.route('/articles/<filename>')
@login_required
def view_article(filename):
    """Preview a single article."""
    fpath = _safe_post_path(filename)
    if not fpath or not os.path.isfile(fpath):
        flash('文章未找到。', 'error')
        return redirect(url_for('uploader.articles'))
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    meta, _, body = _parse_post(raw)
    # Render markdown to HTML
    # Replace Jekyll's {{ site.baseurl }} with the current Flask script root.
    # In dev (root path) this is ''. Behind Nginx at /PolaZhenjing/ the
    # ReverseProxied middleware exposes it as request.script_root so image
    # URLs like /assets/images/generated/... still resolve.
    body = body.replace('{{ site.baseurl }}', request.script_root or '')
    body_html = md_lib.markdown(body, extensions=['extra', 'codehilite', 'toc', 'tables'])
    github_url = f'https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/_posts/{filename}'
    # Build GitHub Pages article URL from Jekyll permalink /:year/:month/:day/:title/
    pages_url = _build_pages_url(filename)
    read_time = _calc_read_time(body)
    # Get style accent color
    layout = meta.get('layout', 'deep-technical')
    accent_color = STYLE_ACCENTS.get(layout, '#E4BF7A')
    return render_template('article_view.html',
                           filename=filename, meta=meta,
                           body_html=body_html, github_url=github_url,
                           pages_url=pages_url, read_time=read_time,
                           accent_color=accent_color)


@uploader_bp.route('/articles/<filename>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(filename):
    """Edit an existing Markdown/Jekyll article."""
    fpath = _safe_post_path(filename)
    if not fpath or not os.path.isfile(fpath):
        flash('文章未找到。', 'error')
        return redirect(url_for('uploader.articles'))

    if request.method == 'POST':
        post_markdown = _build_post_markdown(request.form)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(post_markdown)
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
        return redirect(url_for('uploader.view_article', filename=filename))

    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    meta, front_lines, body = _parse_post(raw)
    known_front_keys = {'layout', 'theme', 'title', 'date', 'tags', 'description', 'summary'}
    extra_front_matter = '\n'.join(
        line for line in front_lines
        if (line.split(':', 1)[0].strip() if ':' in line else line.strip()) not in known_front_keys
    )
    return render_template(
        'article_edit.html',
        filename=filename,
        meta=meta,
        body=body,
        tag_value=_tags_input_value(meta.get('tags', '')),
        extra_front_matter=extra_front_matter,
        styles=STYLES,
        themes=THEMES,
        pages_url=_build_pages_url(filename),
    )


@uploader_bp.route('/articles/<filename>/preview', methods=['POST'])
@login_required
def preview_article_markdown(filename):
    """Render edited Markdown body for the split preview panel."""
    fpath = _safe_post_path(filename)
    if not fpath or not os.path.isfile(fpath):
        return jsonify({'ok': False, 'error': '文章未找到。'}), 404
    body = request.form.get('body', '')
    body = body.replace('{{ site.baseurl }}', request.script_root or '')
    body_html = md_lib.markdown(body, extensions=['extra', 'codehilite', 'toc', 'tables'])
    return jsonify({'ok': True, 'html': body_html})


@uploader_bp.route('/articles/<filename>/delete', methods=['POST'])
@login_required
def delete_article(filename):
    fpath = _safe_post_path(filename)
    if fpath and os.path.isfile(fpath):
        os.remove(fpath)
        flash(f'已删除 {filename}。', 'info')
    else:
        flash('文章未找到。', 'error')
    return redirect(url_for('uploader.articles'))


@uploader_bp.route('/sync', methods=['POST'])
@login_required
def sync():
    """Git add + commit + push to deploy."""
    project_root = os.path.join(os.path.dirname(__file__), '..')
    try:
        subprocess.run(['git', 'add', '-A'], cwd=project_root,
                       capture_output=True, timeout=30)
        msg = f'Update articles - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        subprocess.run(['git', 'commit', '-m', msg], cwd=project_root,
                       capture_output=True, timeout=30)
        result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=project_root,
                                capture_output=True, timeout=120, text=True)
        if result.returncode == 0:
            flash('已成功同步到 GitHub。', 'success')
        else:
            flash(f'推送失败：{result.stderr}', 'error')
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
