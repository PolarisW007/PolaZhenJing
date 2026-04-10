#!/usr/bin/env python3
"""PolaZhenjing v2 — CLI management tool.

Usage:
    python wiki.py serve          Run Jekyll local preview
    python wiki.py build          Build Jekyll site
    python wiki.py admin          Run Flask management server
    python wiki.py new "Title"    Create a new post
    python wiki.py list           List all posts
    python wiki.py deploy         Git add + commit + push
"""
import os
import re
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(PROJECT_ROOT, '_posts')

STYLES = ['deep-technical', 'academic-insight', 'industry-vision',
          'friendly-explainer', 'creative-visual']


def slugify(text: str) -> str:
    """Simple slug generator."""
    try:
        from slugify import slugify as _slugify
        return _slugify(text, max_length=60)
    except ImportError:
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        return re.sub(r'[\s_]+', '-', slug).strip('-')[:60]


def cmd_serve():
    """Run Jekyll local development server."""
    print('[wiki] Starting Jekyll serve...')
    subprocess.run(['bundle', 'exec', 'jekyll', 'serve', '--livereload'],
                   cwd=PROJECT_ROOT)


def cmd_build():
    """Build Jekyll site."""
    print('[wiki] Building Jekyll site...')
    result = subprocess.run(['bundle', 'exec', 'jekyll', 'build'],
                            cwd=PROJECT_ROOT, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    print('[wiki] Build complete → _site/')


def cmd_admin():
    """Run Flask management server."""
    print('[wiki] Starting Flask admin server on http://127.0.0.1:5000/admin/')
    from app import create_app
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)


def cmd_new(title: str, style: str = 'deep-technical'):
    """Create a new post from CLI."""
    if style not in STYLES:
        print(f'[wiki] Unknown style: {style}')
        print(f'       Available: {", ".join(STYLES)}')
        sys.exit(1)

    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = slugify(title) or 'untitled'
    filename = f'{date_str}-{slug}.md'
    os.makedirs(POSTS_DIR, exist_ok=True)
    filepath = os.path.join(POSTS_DIR, filename)

    front_matter = f"""---
layout: {style}
title: "{title}"
date: {date_str}
tags: []
---

# {title}

Write your content here.
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    print(f'[wiki] Created: _posts/{filename}')


def cmd_list():
    """List all posts."""
    if not os.path.isdir(POSTS_DIR):
        print('[wiki] No posts directory found.')
        return

    files = sorted(os.listdir(POSTS_DIR), reverse=True)
    md_files = [f for f in files if f.endswith('.md')]

    if not md_files:
        print('[wiki] No posts found.')
        return

    print(f'[wiki] {len(md_files)} post(s):')
    for f in md_files:
        # Quick parse for layout
        fpath = os.path.join(POSTS_DIR, f)
        style = '?'
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                if line.startswith('layout:'):
                    style = line.split(':', 1)[1].strip()
                    break
        print(f'  [{style}] {f}')


def cmd_deploy():
    """Git add, commit, and push."""
    print('[wiki] Deploying...')
    subprocess.run(['git', 'add', '-A'], cwd=PROJECT_ROOT)
    msg = f'Update articles - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    subprocess.run(['git', 'commit', '-m', msg], cwd=PROJECT_ROOT)
    result = subprocess.run(['git', 'push'], cwd=PROJECT_ROOT,
                            capture_output=True, text=True)
    if result.returncode == 0:
        print('[wiki] Pushed to remote successfully.')
    else:
        print(f'[wiki] Push failed: {result.stderr}')
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == 'serve':
        cmd_serve()
    elif command == 'build':
        cmd_build()
    elif command == 'admin':
        cmd_admin()
    elif command == 'new':
        title = sys.argv[2] if len(sys.argv) > 2 else 'Untitled'
        style = 'deep-technical'
        if '--style' in sys.argv:
            idx = sys.argv.index('--style')
            if idx + 1 < len(sys.argv):
                style = sys.argv[idx + 1]
        cmd_new(title, style)
    elif command == 'list':
        cmd_list()
    elif command == 'deploy':
        cmd_deploy()
    else:
        print(f'[wiki] Unknown command: {command}')
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
