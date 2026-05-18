"""Skill Hub blueprint.

模块名称：Skill Hub
功能描述：展示、搜索、分类、下载和管理员添加 Codex skill 包
创建日期：2026-05-18
作者：Codex
主要变更：2026-05-18 初始创建
依赖模块：Flask、ZipFile、urllib、app.auth
"""
import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   jsonify, send_file, session, url_for)
from werkzeug.utils import secure_filename

from .auth import login_required

skillhub_bp = Blueprint('skillhub', __name__, url_prefix='/skills')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLHUB_DIR = PROJECT_ROOT / 'data' / 'skillhub'
SKILL_STORE_DIR = SKILLHUB_DIR / 'skills'
REGISTRY_FILE = SKILLHUB_DIR / 'registry.json'
ALLOWED_ARCHIVE_EXT = {'zip'}

DEFAULT_SKILL_ROOTS = [
    Path('/Users/wangchang/.codex/skills'),
    Path('/Users/wangchang/.agents/skills'),
    Path('/PolaZhenjing/data/skillhub/skills'),
    SKILL_STORE_DIR,
]

CATEGORY_KEYWORDS = {
    '交付': ['delivery', 'pola-', 'deploy', 'ship', 'release', 'test', 'review'],
    '设计': ['design', 'ui', 'frontend', 'wukong'],
    '浏览器': ['browse', 'browser', 'chrome', 'scrape', 'qa'],
    '文档': ['document', 'pdf', 'presentation', 'spreadsheet', 'devlog'],
    '数据': ['dingtalk', 'dws', 'keen', 'meeting', 'report'],
    '工程': ['codex', 'health', 'investigate', 'guard', 'careful'],
}


def _now() -> str:
    """Return an ISO timestamp for registry records."""
    return datetime.now().isoformat(timespec='seconds')


def _slugify(value: str) -> str:
    """Create a filesystem and URL friendly id."""
    value = re.sub(r'[^a-zA-Z0-9_.-]+', '-', value.strip().lower())
    return re.sub(r'-+', '-', value).strip('-') or 'skill'


def _read_frontmatter(skill_md: Path) -> dict:
    """Parse simple YAML-like frontmatter from SKILL.md."""
    text = skill_md.read_text(encoding='utf-8', errors='ignore')
    if not text.startswith('---'):
        return {'name': skill_md.parent.name, 'description': ''}
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {'name': skill_md.parent.name, 'description': ''}
    meta = {}
    for line in parts[1].splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        meta[key.strip()] = value.strip().strip('"\'')
    meta.setdefault('name', skill_md.parent.name)
    meta.setdefault('description', '')
    return meta


def _infer_category(name: str, description: str) -> str:
    """Infer a broad category from skill name and description."""
    haystack = f'{name} {description}'.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return category
    return '通用'


def _configured_roots() -> list[Path]:
    """Resolve skill roots from env plus built-in defaults."""
    raw = os.environ.get('SKILL_ROOTS', '')
    roots = [Path(item).expanduser() for item in raw.split(':') if item.strip()]
    roots.extend(DEFAULT_SKILL_ROOTS)
    seen = set()
    unique = []
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def _load_registry() -> list[dict]:
    """Load persistent registry entries."""
    if not REGISTRY_FILE.is_file():
        return []
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return []


def _save_registry(entries: list[dict]) -> None:
    """Persist registry entries for uploaded or imported skills."""
    SKILLHUB_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def _entry_from_skill_md(skill_md: Path, source_type: str = 'local',
                         source_url: str = '') -> dict:
    """Create a registry entry from a SKILL.md file."""
    meta = _read_frontmatter(skill_md)
    name = meta.get('name') or skill_md.parent.name
    description = meta.get('description') or ''
    return {
        'id': _slugify(name),
        'name': name,
        'description': description,
        'category': _infer_category(name, description),
        'source_type': source_type,
        'source_url': source_url,
        'skill_md': str(skill_md),
        'package_dir': str(skill_md.parent),
        'updated_at': _now(),
    }


def _scan_skill_roots() -> list[dict]:
    """Scan configured roots for SKILL.md files."""
    entries = []
    for root in _configured_roots():
        if not root.exists():
            continue
        for skill_md in root.rglob('SKILL.md'):
            if any(part.startswith('.') for part in skill_md.relative_to(root).parts[:-1]):
                continue
            entries.append(_entry_from_skill_md(skill_md))
    return entries


def _all_skills() -> list[dict]:
    """Merge persistent registry and live filesystem scan."""
    merged = {}
    for entry in _scan_skill_roots() + _load_registry():
        skill_md = Path(entry.get('skill_md', ''))
        if not skill_md.is_file():
            continue
        entry.setdefault('category', _infer_category(
            entry.get('name', ''), entry.get('description', '')
        ))
        base_id = entry.get('id') or _slugify(entry.get('name', 'skill'))
        unique_id = base_id
        index = 2
        while unique_id in merged and merged[unique_id].get('skill_md') != str(skill_md):
            unique_id = f'{base_id}-{index}'
            index += 1
        entry['id'] = unique_id
        merged[unique_id] = entry
    return sorted(merged.values(), key=lambda item: item.get('name', '').lower())


def _is_skill_admin() -> bool:
    """Return whether the current logged-in user can manage skills."""
    username = session.get('username')
    if not username:
        return False
    raw = os.environ.get('SKILL_ADMIN_USERS', 'admin,sirius')
    admins = {item.strip() for item in raw.split(',') if item.strip()}
    return username in admins


def _require_skill_admin() -> None:
    """Abort when a logged-in user is not a skill admin."""
    if not _is_skill_admin():
        abort(403)


def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    """Extract a zip archive without allowing path traversal."""
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise ValueError('压缩包包含非法路径。')
        archive.extractall(destination)


def _register_package(package_dir: Path, source_type: str,
                      source_url: str = '') -> int:
    """Register all SKILL.md files found under a package directory."""
    entries = _load_registry()
    existing_paths = {item.get('skill_md') for item in entries}
    added = 0
    for skill_md in package_dir.rglob('SKILL.md'):
        entry = _entry_from_skill_md(skill_md, source_type, source_url)
        if entry['skill_md'] in existing_paths:
            continue
        entries.append(entry)
        existing_paths.add(entry['skill_md'])
        added += 1
    _save_registry(entries)
    return added


def _github_zip_url(repo_url: str) -> tuple[str, str]:
    """Convert a GitHub repo URL into an API zipball URL and package name."""
    parsed = urlparse(repo_url.strip())
    if parsed.netloc not in {'github.com', 'www.github.com'}:
        raise ValueError('仅支持 github.com 仓库地址。')
    parts = [part for part in parsed.path.strip('/').split('/') if part]
    if len(parts) < 2:
        raise ValueError('请输入形如 https://github.com/owner/repo 的地址。')
    owner, repo = parts[0], parts[1].removesuffix('.git')
    if not re.match(r'^[A-Za-z0-9_.-]+$', owner + repo):
        raise ValueError('仓库 owner 或 repo 名称不合法。')
    return f'https://api.github.com/repos/{owner}/{repo}/zipball', f'{owner}-{repo}'


def _fetch_github_repo(repo_url: str, destination: Path) -> tuple[Path, str]:
    """Download and extract a GitHub repository zipball into destination."""
    zip_url, package_name = _github_zip_url(repo_url)
    request_obj = Request(zip_url, headers={'User-Agent': 'PolaZhenjing-SkillHub'})
    zip_path = destination / 'repo.zip'
    with urlopen(request_obj, timeout=30) as response:
        zip_path.write_bytes(response.read())
    extract_dir = destination / 'extract'
    _safe_extract_zip(zip_path, extract_dir)
    children = [child for child in extract_dir.iterdir() if child.is_dir()]
    source_dir = children[0] if len(children) == 1 else extract_dir
    return source_dir, package_name


def _preview_package(source_dir: Path) -> list[dict]:
    """Return readonly skill metadata found in a package directory."""
    preview = []
    for skill_md in source_dir.rglob('SKILL.md'):
        entry = _entry_from_skill_md(skill_md)
        preview.append({
            'name': entry['name'],
            'description': entry['description'],
            'category': entry['category'],
            'path': str(skill_md.relative_to(source_dir)),
        })
    return sorted(preview, key=lambda item: item['name'].lower())


@skillhub_bp.app_context_processor
def inject_skillhub_admin():
    """Expose Skill Hub admin status to templates."""
    return {'is_skill_admin': _is_skill_admin()}


@skillhub_bp.route('/')
def index():
    """Render the public Skill Hub with search and category filters."""
    query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip()
    skills = _all_skills()
    categories = sorted({skill.get('category', '通用') for skill in skills})
    if category:
        skills = [skill for skill in skills if skill.get('category') == category]
    if query:
        skills = [
            skill for skill in skills
            if query in f"{skill.get('name', '')} {skill.get('description', '')}".lower()
        ]
    return render_template(
        'skillhub.html',
        skills=skills,
        categories=categories,
        selected_category=category,
        query=request.args.get('q', '').strip(),
    )


@skillhub_bp.route('/<skill_id>/download')
def download(skill_id):
    """Download a skill directory as a zip file."""
    skill = next((item for item in _all_skills() if item['id'] == skill_id), None)
    if not skill:
        abort(404)
    package_dir = Path(skill['package_dir'])
    if not package_dir.is_dir():
        abort(404)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in package_dir.rglob('*'):
            if path.is_file():
                archive.write(path, arcname=str(Path(package_dir.name) / path.relative_to(package_dir)))
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{skill['id']}.zip",
    )


@skillhub_bp.route('/admin/upload', methods=['POST'])
@login_required
def upload_skill():
    """Allow skill admins to upload a zip package containing SKILL.md."""
    _require_skill_admin()
    file = request.files.get('skill_zip')
    if not file or not file.filename:
        flash('请选择 skill zip 文件。', 'error')
        return redirect(url_for('skillhub.index'))
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_ARCHIVE_EXT:
        flash('仅支持 zip 文件。', 'error')
        return redirect(url_for('skillhub.index'))
    package_name = _slugify(Path(secure_filename(file.filename)).stem)
    target_dir = SKILL_STORE_DIR / f'{package_name}-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / 'skill.zip'
        file.save(zip_path)
        _safe_extract_zip(zip_path, target_dir)
    added = _register_package(target_dir, 'upload')
    flash(f'已添加 {added} 个 skill。' if added else '未找到 SKILL.md。', 'success' if added else 'warning')
    return redirect(url_for('skillhub.index'))


@skillhub_bp.route('/admin/add-github', methods=['POST'])
@login_required
def add_github():
    """Allow skill admins to import a GitHub repo as a skill package."""
    _require_skill_admin()
    repo_url = request.form.get('repo_url', '').strip()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            source_dir, package_name = _fetch_github_repo(repo_url, Path(tmp))
            target_dir = SKILL_STORE_DIR / f'{_slugify(package_name)}-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            shutil.copytree(source_dir, target_dir)
        added = _register_package(target_dir, 'github', repo_url)
        flash(f'已从 GitHub 添加 {added} 个 skill。' if added else '仓库中未找到 SKILL.md。',
              'success' if added else 'warning')
    except (ValueError, URLError, OSError, zipfile.BadZipFile) as exc:
        flash(f'添加失败：{exc}', 'error')
    return redirect(url_for('skillhub.index'))


@skillhub_bp.route('/admin/github-preview', methods=['POST'])
@login_required
def github_preview():
    """Preview a GitHub repo before importing it into Skill Hub."""
    _require_skill_admin()
    payload = request.get_json(silent=True) or {}
    repo_url = payload.get('repo_url', '').strip()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            source_dir, package_name = _fetch_github_repo(repo_url, Path(tmp))
            skills = _preview_package(source_dir)
        return jsonify({
            'ok': True,
            'package_name': package_name,
            'skill_count': len(skills),
            'skills': skills,
        })
    except (ValueError, URLError, OSError, zipfile.BadZipFile) as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
