"""Upload and article management blueprint."""
import os
import re
import subprocess
import tempfile
from datetime import datetime

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for, current_app)

from .auth import login_required
from .converter import detect_and_convert, extract_title

uploader_bp = Blueprint('uploader', __name__, url_prefix='/admin')

STYLES = [
    {'id': 'deep-technical', 'name': 'Deep Technical', 'color': '#1a1a2e',
     'desc': 'Code-heavy, technical depth. Inspired by Andrej Karpathy.'},
    {'id': 'academic-insight', 'name': 'Academic Insight', 'color': '#2d6a4f',
     'desc': 'Scholarly, citation-heavy. Inspired by Yann LeCun.'},
    {'id': 'industry-vision', 'name': 'Industry Vision', 'color': '#e63946',
     'desc': 'Bold opinions, industry trends. Inspired by Kai-Fu Lee.'},
    {'id': 'friendly-explainer', 'name': 'Friendly Explainer', 'color': '#f4a261',
     'desc': 'Warm, approachable, clear. Inspired by Andrew Ng.'},
    {'id': 'creative-visual', 'name': 'Creative Visual', 'color': '#7b2cbf',
     'desc': 'Visual storytelling, rich media. Inspired by Jim Fan.'},
]

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
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
                flash(f'Unsupported file type: .{ext}', 'error')
                return render_template('upload.html')

            os.makedirs(UPLOAD_DIR, exist_ok=True)
            tmp_path = os.path.join(UPLOAD_DIR, f.filename)
            f.save(tmp_path)

            try:
                content = detect_and_convert(tmp_path, ext)
                title = extract_title(content)
            except Exception as e:
                flash(f'Conversion error: {e}', 'error')
                return render_template('upload.html')

        # Handle paste content
        elif request.form.get('content', '').strip():
            content = request.form['content'].strip()
            title = extract_title(content)

        else:
            flash('Please upload a file or paste content.', 'error')
            return render_template('upload.html')

        # Store in session for style selection step
        session['draft_content'] = content
        session['draft_title'] = request.form.get('title', '').strip() or title
        session['draft_tags'] = request.form.get('tags', '').strip()
        session['draft_description'] = request.form.get('description', '').strip()
        return redirect(url_for('uploader.style_select'))

    return render_template('upload.html')


@uploader_bp.route('/upload/style', methods=['GET'])
@login_required
def style_select():
    if 'draft_content' not in session:
        return redirect(url_for('uploader.upload'))
    return render_template('style_select.html', styles=STYLES,
                           title=session.get('draft_title', ''))


@uploader_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    content = session.pop('draft_content', '')
    title = session.pop('draft_title', 'Untitled')
    tags = session.pop('draft_tags', '')
    description = session.pop('draft_description', '')
    style = request.form.get('style', 'deep-technical')

    if not content:
        flash('No content to generate.', 'error')
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

    flash(f'Article "{title}" created with {style} style.', 'success')
    return redirect(url_for('uploader.articles'))


@uploader_bp.route('/articles')
@login_required
def articles():
    posts = _scan_posts()
    return render_template('articles.html', posts=posts, styles=STYLES)


@uploader_bp.route('/articles/<filename>/delete', methods=['POST'])
@login_required
def delete_article(filename):
    fpath = os.path.join(POSTS_DIR, filename)
    if os.path.isfile(fpath):
        os.remove(fpath)
        flash(f'Deleted {filename}.', 'info')
    else:
        flash('Article not found.', 'error')
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
        result = subprocess.run(['git', 'push'], cwd=project_root,
                                capture_output=True, timeout=60, text=True)
        if result.returncode == 0:
            flash('Synced to GitHub successfully.', 'success')
        else:
            flash(f'Push failed: {result.stderr}', 'error')
    except Exception as e:
        flash(f'Sync error: {e}', 'error')
    return redirect(url_for('uploader.articles'))
