"""Repository helpers for Markdown articles stored in _posts."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
import tempfile


POST_FILENAME_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$')


@dataclass
class ArticlePost:
    """Parsed article post file."""

    path: str
    actual_filename: str
    admin_filename: str
    raw: str
    meta: dict
    front_lines: list[str]
    body: str


def article_admin_filename(filename: str) -> str:
    """Return the short admin URL filename for a Jekyll post filename."""
    match = POST_FILENAME_RE.match(filename or '')
    if not match:
        return filename
    return f'{match.group(4)}.md'


def resolve_post_filename(filename: str, posts_dir: str) -> str | None:
    """Resolve either a real Jekyll filename or a short admin filename."""
    if not filename or '/' in filename or '\\' in filename or not filename.endswith('.md'):
        return None
    direct = os.path.join(posts_dir, filename)
    if os.path.isfile(direct):
        return filename

    wanted = filename.strip()
    for fname in os.listdir(posts_dir) if os.path.isdir(posts_dir) else []:
        if fname.endswith('.md') and article_admin_filename(fname) == wanted:
            return fname
    return None


def safe_post_path(filename: str, posts_dir: str) -> str | None:
    """Return an absolute post path only for safe Markdown post filenames."""
    resolved = resolve_post_filename(filename, posts_dir)
    if not resolved:
        return None
    fpath = os.path.abspath(os.path.join(posts_dir, resolved))
    posts_root = os.path.abspath(posts_dir)
    if not fpath.startswith(posts_root + os.sep):
        return None
    return fpath


def parse_post(raw: str) -> tuple[dict, list[str], str]:
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


def load_post(filename: str, posts_dir: str) -> ArticlePost | None:
    """Load and parse an article post."""
    fpath = safe_post_path(filename, posts_dir)
    if not fpath or not os.path.isfile(fpath):
        return None
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    meta, front_lines, body = parse_post(raw)
    actual_filename = os.path.basename(fpath)
    return ArticlePost(
        path=fpath,
        actual_filename=actual_filename,
        admin_filename=article_admin_filename(actual_filename),
        raw=raw,
        meta=meta,
        front_lines=front_lines,
        body=body,
    )


def write_post(path: str, content: str):
    """Atomically write a Markdown post file."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.post-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
