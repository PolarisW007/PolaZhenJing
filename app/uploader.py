"""Upload and article management blueprint."""
import os
import re
import subprocess
import tempfile
import json
import hashlib
from datetime import datetime

import markdown as md_lib

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for, current_app)

from .auth import login_required
from .converter import detect_and_convert, extract_title

uploader_bp = Blueprint('uploader', __name__, url_prefix='/admin')

STYLES = [
    {'id': 'deep-technical', 'name': '深度技术', 'color': '#1a1a2e',
     'desc': '代码密集，技术深度。灵感来源：Andrej Karpathy。'},
    {'id': 'academic-insight', 'name': '学术洞察', 'color': '#2d6a4f',
     'desc': '学术风格，引用丰富。灵感来源：Yann LeCun。'},
    {'id': 'industry-vision', 'name': '产业视野', 'color': '#e63946',
     'desc': '大胆观点，行业趋势。灵感来源：李开复。'},
    {'id': 'friendly-explainer', 'name': '亲和讲解', 'color': '#f4a261',
     'desc': '温暖亲切，通俗易懂。灵感来源：Andrew Ng。'},
    {'id': 'creative-visual', 'name': '创意视觉', 'color': '#7b2cbf',
     'desc': '视觉叙事，富媒体。灵感来源：Jim Fan。'},
]

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
DRAFT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'drafts')
ALLOWED_EXT = {'md', 'markdown', 'txt', 'pdf', 'docx', 'doc', 'html', 'htm'}


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

    front_matter += '\n---\n\n'

    # Write to _posts/
    os.makedirs(POSTS_DIR, exist_ok=True)
    post_path = os.path.join(POSTS_DIR, filename)
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)

    flash(f'文章「{title}」已以 {style} 风格创建。', 'success')
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
    body_html = md_lib.markdown(body, extensions=['extra', 'codehilite', 'toc', 'tables'])
    github_url = f'https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/_posts/{filename}'
    return render_template('article_view.html', filename=filename, meta=meta, body_html=body_html, github_url=github_url)


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
