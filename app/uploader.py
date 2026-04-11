"""Upload and article management blueprint."""
import os
import re
import subprocess
import tempfile
import json
import hashlib
import logging
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

import markdown as md_lib

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for, current_app)

from .auth import login_required
from .converter import detect_and_convert, extract_title

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

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
DRAFT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'drafts')
ALLOWED_EXT = {'md', 'markdown', 'txt', 'pdf', 'docx', 'doc', 'html', 'htm'}

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


def _get_minimax_api_key() -> str | None:
    """Read MINIMAX_TOKEN_PLAN_API_KEY from environment."""
    key = os.environ.get('MINIMAX_TOKEN_PLAN_API_KEY')
    if not key:
        # Try sourcing from ~/.zshrc
        try:
            result = subprocess.run(
                ['zsh', '-c', 'source ~/.zshrc 2>/dev/null && echo $MINIMAX_TOKEN_PLAN_API_KEY'],
                capture_output=True, text=True, timeout=10)
            key = result.stdout.strip()
        except Exception:
            pass
    return key or None


def _call_llm_rewrite(content: str, title: str, system_prompt: str) -> str | None:
    """Call MiniMax LLM to rewrite content using the given skill prompt.

    Returns rewritten content string, or None on failure.
    """
    api_key = _get_minimax_api_key()
    if not api_key:
        logger.warning('MINIMAX_TOKEN_PLAN_API_KEY not found, skipping LLM rewrite')
        return None

    user_msg = f'请根据以下素材，以你的风格写一篇公众号长文。标题是「{title}」。\n\n素材内容：\n{content}'

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


def _save_draft(content: str, title: str, tags: str, description: str) -> str:
    """Save draft to temp file, return draft ID."""
    os.makedirs(DRAFT_DIR, exist_ok=True)
    draft_id = hashlib.md5(f'{title}{datetime.now().isoformat()}'.encode()).hexdigest()[:12]
    draft_path = os.path.join(DRAFT_DIR, f'{draft_id}.json')
    with open(draft_path, 'w', encoding='utf-8') as f:
        json.dump({'content': content, 'title': title, 'tags': tags, 'description': description}, f, ensure_ascii=False)
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

        else:
            flash('请上传文件或粘贴内容。', 'error')
            return render_template('upload.html')

        # Store in temp file (avoid session cookie size limit)
        draft_id = _save_draft(content,
                               request.form.get('title', '').strip() or title,
                               request.form.get('tags', '').strip(),
                               request.form.get('description', '').strip())
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
    draft_id = session.pop('draft_id', '')
    draft = _load_draft(draft_id)
    if not draft:
        flash('没有可生成的内容。', 'error')
        return redirect(url_for('uploader.upload'))

    content = draft['content']
    title = draft['title'] or '无标题'
    tags = draft['tags']
    description = draft['description']
    style = request.form.get('style', 'deep-technical')

    if not content:
        flash('没有可生成的内容。', 'error')
        return redirect(url_for('uploader.upload'))

    # ── LLM skill rewriting ──────────────────────────────────
    skill_prompt = _get_style_prompt(style)
    if skill_prompt:
        rewritten = _call_llm_rewrite(content, title, skill_prompt)
        if rewritten:
            content = rewritten
            flash(f'已使用 LLM 技能重写内容（风格：{style}）。', 'info')
        else:
            flash('LLM 重写失败，将使用原始内容。', 'warning')

    # Build Jekyll post
    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = _slugify(title) or 'untitled'
    filename = f'{date_str}-{slug}.md'

    # Front matter
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
    front_matter = f"""---
layout: {style}
title: "{title}"
date: {date_str}
tags: [{', '.join(tag_list)}]"""

    if description:
        front_matter += f'\ndescription: "{description}"'

    # Generate summary
    summary = _generate_summary(content)
    if summary:
        # Escape quotes in summary for YAML
        safe_summary = summary.replace('"', '\\"')
        front_matter += f'\nsummary: "{safe_summary}"'

    front_matter += '\n---\n\n'

    # Write to _posts/
    os.makedirs(POSTS_DIR, exist_ok=True)
    post_path = os.path.join(POSTS_DIR, filename)
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)

    # Auto-sync to GitHub after generating
    try:
        project_root = os.path.join(os.path.dirname(__file__), '..')
        subprocess.run(['git', 'add', '-A'], cwd=project_root,
                       capture_output=True, timeout=30)
        commit_msg = f'Add article: {title} - {date_str}'
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_root,
                       capture_output=True, timeout=30)
        push_result = subprocess.run(
            ['git', 'push', '-u', 'origin', 'main'], cwd=project_root,
            capture_output=True, timeout=120, text=True)
        if push_result.returncode == 0:
            flash(f'文章「{title}」已以 {style} 风格创建，并已同步到 GitHub。', 'success')
        else:
            flash(f'文章「{title}」已创建，但推送失败：{push_result.stderr}', 'warning')
    except Exception as e:
        flash(f'文章「{title}」已创建，但同步出错：{e}', 'warning')
    return redirect(url_for('uploader.articles'))


@uploader_bp.route('/articles')
@login_required
def articles():
    posts = _scan_posts()
    return render_template('articles.html', posts=posts, styles=STYLES)


GITHUB_REPO = 'PolarisW007/PolaZhenJing'
GITHUB_BRANCH = 'main'


@uploader_bp.route('/articles/<filename>')
@login_required
def view_article(filename):
    """Preview a single article."""
    fpath = os.path.join(POSTS_DIR, filename)
    if not os.path.isfile(fpath):
        flash('文章未找到。', 'error')
        return redirect(url_for('uploader.articles'))
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    # Split front matter and body
    body = raw
    meta = {}
    if raw.startswith('---'):
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            body = parts[2].strip()
    # Render markdown to HTML
    # Strip Jekyll Liquid tags (e.g. {{ site.baseurl }}) for local preview
    body = body.replace('{{ site.baseurl }}', '')
    body_html = md_lib.markdown(body, extensions=['extra', 'codehilite', 'toc', 'tables'])
    github_url = f'https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/_posts/{filename}'
    pages_url = f'https://polarisw007.github.io/PolaZhenJing/'
    read_time = _calc_read_time(body)
    # Get style accent color
    layout = meta.get('layout', 'deep-technical')
    accent_color = STYLE_ACCENTS.get(layout, '#E4BF7A')
    return render_template('article_view.html',
                           filename=filename, meta=meta,
                           body_html=body_html, github_url=github_url,
                           pages_url=pages_url, read_time=read_time,
                           accent_color=accent_color)


@uploader_bp.route('/articles/<filename>/delete', methods=['POST'])
@login_required
def delete_article(filename):
    fpath = os.path.join(POSTS_DIR, filename)
    if os.path.isfile(fpath):
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
