import functools
import base64
import binascii
import io
import random
import sqlite3
import string
import time
import uuid
from pathlib import Path

from flask import (Blueprint, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from . import get_db
from .mailer import send_verification_code

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')

ALLOWED_AVATAR_FORMATS = {'JPEG': 'jpg', 'PNG': 'png'}
AVATAR_SIZE = (300, 300)
AVATAR_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'avatars'

DEFAULT_PREFERENCES = {
    'theme': 'dream-gold',
    'font_family': 'system',
    'font_scale': 'normal',
    'density': 'comfortable',
}

THEME_OPTIONS = [
    {'id': 'dream-gold', 'name': '织梦黑金'},
    {'id': 'zhenjing', 'name': '真境玄金'},
    {'id': 'dark', 'name': '深色'},
    {'id': 'light', 'name': '清昼'},
    {'id': 'system', 'name': '跟随系统'},
]

FONT_OPTIONS = [
    {'id': 'system', 'name': '系统默认'},
    {'id': 'MFYaYun', 'name': '造字工坊雅韵'},
    {'id': 'serif', 'name': '宋体 / 衬线'},
    {'id': 'sans', 'name': '苹方 / 无衬线'},
]

PERMISSION_CATALOG = {
    'articles.read': {'name': '查看文章', 'app': 'PolaZhenjing'},
    'articles.manage': {'name': '管理文章', 'app': 'PolaZhenjing'},
    'skills.read': {'name': '查看 Skills', 'app': 'Skill Hub'},
    'skills.manage': {'name': '管理 Skills', 'app': 'Skill Hub'},
    'polaread.use': {'name': '使用 PolaRead', 'app': 'PolaRead'},
    'polanews.use': {'name': '使用 PolaNews', 'app': 'PolaNews'},
    'agent.use': {'name': '使用 AI 分身', 'app': 'AI Avatar'},
    'projects.manage': {'name': '管理项目', 'app': 'AIPD'},
    'users.manage': {'name': '管理用户与权限', 'app': 'AIPD'},
}

DEFAULT_USER_PERMISSIONS = {
    'articles.read',
    'skills.read',
    'polaread.use',
    'polanews.use',
    'agent.use',
}
ADMIN_PERMISSIONS = set(PERMISSION_CATALOG)


def _valid_preference(field, value):
    value = (value or '').strip()
    if field == 'theme':
        allowed = {item['id'] for item in THEME_OPTIONS}
    elif field == 'font_family':
        allowed = {item['id'] for item in FONT_OPTIONS}
    elif field == 'font_scale':
        allowed = {'small', 'normal', 'large'}
    elif field == 'density':
        allowed = {'compact', 'comfortable', 'spacious'}
    else:
        allowed = set()
    return value if value in allowed else DEFAULT_PREFERENCES[field]


def _ensure_preferences(db, user_id):
    row = db.execute(
        'SELECT * FROM user_preferences WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    if row:
        return dict(row)
    db.execute(
        'INSERT OR IGNORE INTO user_preferences '
        '(user_id, theme, font_family, font_scale, density) VALUES (?, ?, ?, ?, ?)',
        (
            user_id,
            DEFAULT_PREFERENCES['theme'],
            DEFAULT_PREFERENCES['font_family'],
            DEFAULT_PREFERENCES['font_scale'],
            DEFAULT_PREFERENCES['density'],
        )
    )
    db.commit()
    row = db.execute(
        'SELECT * FROM user_preferences WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    return dict(row) if row else DEFAULT_PREFERENCES.copy()


def _stored_permissions(db, user_id):
    rows = db.execute(
        'SELECT permission FROM user_permissions WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    return {row['permission'] for row in rows}


def _permissions_for(user):
    db = get_db()
    role = 'admin' if _is_admin_user(user) else (user['role'] if 'role' in user.keys() else 'user')
    if role == 'admin':
        return sorted(ADMIN_PERMISSIONS)
    return sorted(DEFAULT_USER_PERMISSIONS | _stored_permissions(db, user['id']))


def _grant_permission(db, user_id, permission, source='manual'):
    if permission not in PERMISSION_CATALOG:
        raise ValueError('未知权限。')
    db.execute(
        'INSERT OR IGNORE INTO user_permissions (user_id, permission, source) VALUES (?, ?, ?)',
        (user_id, permission, source),
    )


def _account_admin_context(db):
    users = db.execute(
        'SELECT id, username, email, nickname, avatar_url, role, created_at FROM users ORDER BY id DESC'
    ).fetchall()
    requests = db.execute(
        '''
        SELECT pr.*, u.username, u.email, u.nickname
        FROM permission_requests pr
        JOIN users u ON u.id = pr.user_id
        ORDER BY CASE pr.status WHEN 'pending' THEN 0 ELSE 1 END, pr.created_at DESC
        LIMIT 80
        '''
    ).fetchall()
    user_permissions = {}
    for row in db.execute('SELECT user_id, permission FROM user_permissions ORDER BY permission').fetchall():
        user_permissions.setdefault(row['user_id'], []).append(row['permission'])
    return {
        'users': users,
        'permission_requests': requests,
        'user_permissions': user_permissions,
        'permission_catalog': PERMISSION_CATALOG,
    }


def _render_account(user, **extra):
    profile = user_payload(user)
    db = get_db()
    context = {
        'user': user,
        'profile': profile,
        'theme_options': THEME_OPTIONS,
        'font_options': FONT_OPTIONS,
        'permission_catalog': PERMISSION_CATALOG,
        'admin_context': _account_admin_context(db) if profile['role'] == 'admin' else None,
    }
    context.update(extra)
    return render_template('account.html', **context)


def _safe_next(default_endpoint='uploader.upload'):
    next_url = request.args.get('next') or request.form.get('next') or ''
    if next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return url_for(default_endpoint)


def _is_admin_user(user):
    role = user['role'] if 'role' in user.keys() else ''
    if role == 'admin':
        return True
    email = (user['email'] or '').lower()
    username = (user['username'] or '').lower()
    return email == 'wsyxjer@gmail.com' or username in {'admin', 'sirius'}


def user_payload(user):
    db = get_db()
    display_name = (
        (user['nickname'] if 'nickname' in user.keys() else '')
        or user['username']
        or user['email']
    )
    role = 'admin' if _is_admin_user(user) else (user['role'] if 'role' in user.keys() else 'user')
    preferences = _ensure_preferences(db, user['id'])
    permissions = _permissions_for(user)
    return {
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'nickname': display_name,
        'avatar_url': user['avatar_url'] if 'avatar_url' in user.keys() else '',
        'role': role,
        'permissions': permissions,
        'preferences': {
            'theme': preferences.get('theme') or DEFAULT_PREFERENCES['theme'],
            'font_family': preferences.get('font_family') or DEFAULT_PREFERENCES['font_family'],
            'font_scale': preferences.get('font_scale') or DEFAULT_PREFERENCES['font_scale'],
            'density': preferences.get('density') or DEFAULT_PREFERENCES['density'],
        },
    }


def _save_avatar_image(image, user_id):
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    image = ImageOps.exif_transpose(image).convert('RGBA')
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)

    mask = Image.new('L', AVATAR_SIZE, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, AVATAR_SIZE[0] - 1, AVATAR_SIZE[1] - 1), fill=255)
    image.putalpha(mask)

    stored_name = f'user-{user_id}-{uuid.uuid4().hex[:12]}.png'
    stored_path = AVATAR_DIR / stored_name
    image.save(stored_path, format='PNG', optimize=True)
    return f'/PolaZhenjing/assets/avatars/{stored_name}'


def _save_avatar_upload(file_storage, user_id):
    filename = secure_filename(file_storage.filename or '')
    if not filename:
        raise ValueError('请选择要上传的头像。')
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in {'jpg', 'jpeg', 'png'}:
        raise ValueError('头像仅支持 JPG 或 PNG 格式。')

    try:
        with Image.open(file_storage.stream) as image:
            if image.format not in ALLOWED_AVATAR_FORMATS:
                raise ValueError('头像仅支持 JPG 或 PNG 格式。')
            return _save_avatar_image(image, user_id)
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError):
        raise ValueError('头像文件无法识别，请上传有效的 JPG 或 PNG 图片。')


def _save_avatar_data(data_url, user_id):
    if not data_url:
        raise ValueError('头像裁剪数据为空，请重新选择图片。')
    try:
        header, encoded = data_url.split(',', 1)
    except ValueError:
        raise ValueError('头像裁剪数据格式错误，请重新选择图片。')
    if 'image/png' not in header and 'image/jpeg' not in header:
        raise ValueError('头像仅支持 JPG 或 PNG 格式。')
    try:
        raw = base64.b64decode(encoded, validate=True)
        with Image.open(io.BytesIO(raw)) as image:
            return _save_avatar_image(image, user_id)
    except (UnidentifiedImageError, OSError, ValueError, binascii.Error):
        raise ValueError('头像裁剪数据无法识别，请重新选择图片。')


def login_required(view):
    """Decorator that redirects anonymous users to login."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        error = None

        user = db.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()
        if user is None:
            error = '账号不存在。'
        elif not check_password_hash(user['password_hash'], password):
            error = '密码错误。'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['nickname'] = (
                (user['nickname'] if 'nickname' in user.keys() else '')
                or user['username']
            )
            session['avatar_url'] = user['avatar_url'] if 'avatar_url' in user.keys() else ''
            session['role'] = 'admin' if _is_admin_user(user) else (user['role'] if 'role' in user.keys() else 'user')
            return redirect(_safe_next())

        flash(error, 'error')
    return render_template('login.html', next_url=request.args.get('next', ''))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        error = None

        if not username:
            error = '请输入用户名。'
        elif not email:
            error = '请输入邮箱。'
        elif not password or len(password) < 6:
            error = '密码至少6位。'
        if error is None:
            try:
                db.execute(
                    'INSERT INTO users (username, email, password_hash, nickname, role) VALUES (?, ?, ?, ?, ?)',
                    (username, email, generate_password_hash(password), username, 'user')
                )
                db.commit()

                # Generate and send verification code
                code = ''.join(random.choices(string.digits, k=6))
                session['verify_code'] = code
                session['verify_code_time'] = time.time()
                session['verify_email'] = email
                session['pending_user'] = username
                session['verify_next'] = request.form.get('next', '')

                sent = send_verification_code(email, code)
                if sent:
                    flash('验证码已发送到您的邮箱。', 'info')
                    return redirect(url_for('auth.verify'))
                else:
                    flash('注册成功。邮件发送失败，请直接登录。', 'warning')
                    return redirect(url_for('auth.login', next=request.form.get('next', '')))

            except sqlite3.IntegrityError:
                error = f'用户 {username} 或邮箱 {email} 已被注册。'

        flash(error, 'error')
    return render_template('register.html', next_url=request.args.get('next', ''))


@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        stored_code = session.get('verify_code')
        code_time = session.get('verify_code_time', 0)
        email = session.get('verify_email')

        if not stored_code or not email:
            flash('没有待验证的请求。', 'error')
            return redirect(url_for('auth.register'))

        if time.time() - code_time > 300:  # 5 min expiry
            flash('验证码已过期，请重新注册。', 'error')
            return redirect(url_for('auth.register'))

        if code != stored_code:
            flash('验证码错误。', 'error')
            return render_template('verify.html')

        # Mark email as verified
        db = get_db()
        db.execute('UPDATE users SET email_verified = 1 WHERE email = ?', (email,))
        db.commit()

        next_url = session.get('verify_next', '')

        # Clean up session
        session.pop('verify_code', None)
        session.pop('verify_code_time', None)
        session.pop('verify_email', None)
        session.pop('pending_user', None)
        session.pop('verify_next', None)

        flash('邮箱验证成功！请登录。', 'success')
        return redirect(url_for('auth.login', next=next_url))

    return render_template('verify.html')


@auth_bp.route('/password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        db = get_db()

        user = db.execute('SELECT * FROM users WHERE id = ?',
                          (session['user_id'],)).fetchone()

        if not check_password_hash(user['password_hash'], current):
            flash('当前密码错误。', 'error')
        elif len(new_pw) < 6:
            flash('新密码至少6位。', 'error')
        elif new_pw != confirm:
            flash('两次输入的新密码不一致。', 'error')
        else:
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                       (generate_password_hash(new_pw), session['user_id']))
            db.commit()
            flash('密码已更新。', 'success')
            return redirect(url_for('uploader.upload'))

    return render_template('password.html')


@auth_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user is None:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        form_action = request.form.get('form_action', 'profile')
        if form_action == 'grant_permission':
            if not _is_admin_user(user):
                flash('只有管理员可以授权。', 'error')
                return _render_account(user)
            target_user_id = request.form.get('target_user_id', type=int)
            permission = request.form.get('permission', '').strip()
            try:
                _grant_permission(db, target_user_id, permission, 'admin-ui')
                db.commit()
                flash('权限已授予。', 'success')
            except ValueError as exc:
                flash(str(exc), 'error')
            return redirect(url_for('auth.account'))

        if form_action == 'review_permission':
            if not _is_admin_user(user):
                flash('只有管理员可以审批申请。', 'error')
                return _render_account(user)
            request_id = request.form.get('request_id', type=int)
            action = request.form.get('review_action', '').strip()
            item = db.execute(
                'SELECT * FROM permission_requests WHERE id = ?',
                (request_id,)
            ).fetchone()
            if not item:
                flash('申请不存在。', 'error')
                return redirect(url_for('auth.account'))
            if action == 'approve':
                try:
                    _grant_permission(db, item['user_id'], item['permission'], 'request-approved')
                    db.execute(
                        'UPDATE permission_requests SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ? WHERE id = ?',
                        ('approved', user['id'], request_id),
                    )
                    db.commit()
                    flash('申请已通过。', 'success')
                except ValueError as exc:
                    flash(str(exc), 'error')
            elif action == 'reject':
                db.execute(
                    'UPDATE permission_requests SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ? WHERE id = ?',
                    ('rejected', user['id'], request_id),
                )
                db.commit()
                flash('申请已拒绝。', 'success')
            return redirect(url_for('auth.account'))

        nickname = request.form.get('nickname', '').strip()
        avatar_url = user['avatar_url'] if 'avatar_url' in user.keys() else ''
        avatar_data = request.form.get('avatar_data', '').strip()
        avatar_file = request.files.get('avatar')
        if avatar_data:
            try:
                avatar_url = _save_avatar_data(avatar_data, user['id'])
            except ValueError as exc:
                flash(str(exc), 'error')
                return _render_account(user)
        elif avatar_file and avatar_file.filename:
            try:
                avatar_url = _save_avatar_upload(avatar_file, user['id'])
            except ValueError as exc:
                flash(str(exc), 'error')
                return _render_account(user)
        db.execute(
            'UPDATE users SET nickname = ?, avatar_url = ? WHERE id = ?',
            (nickname or user['username'], avatar_url, user['id'])
        )
        prefs = {
            field: _valid_preference(field, request.form.get(field, ''))
            for field in DEFAULT_PREFERENCES
        }
        db.execute(
            '''
            INSERT INTO user_preferences (user_id, theme, font_family, font_scale, density, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                theme = excluded.theme,
                font_family = excluded.font_family,
                font_scale = excluded.font_scale,
                density = excluded.density,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (
                user['id'],
                prefs['theme'],
                prefs['font_family'],
                prefs['font_scale'],
                prefs['density'],
            )
        )
        db.commit()
        session['nickname'] = nickname or user['username']
        session['avatar_url'] = avatar_url
        flash('账户信息已更新。', 'success')
        return redirect(url_for('auth.account'))

    return _render_account(user)


@auth_bp.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'authenticated': False, 'user': None, 'permissions': []}), 401
    user = get_db().execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user is None:
        session.clear()
        return jsonify({'authenticated': False, 'user': None, 'permissions': []}), 401
    profile = user_payload(user)
    return jsonify({
        'authenticated': True,
        'user': profile,
        'permissions': profile['permissions'],
    })


@auth_bp.route('/api/preferences', methods=['POST'])
@login_required
def api_preferences():
    db = get_db()
    user_id = session['user_id']
    payload = request.get_json(silent=True) or {}
    prefs = {
        field: _valid_preference(field, payload.get(field, ''))
        for field in DEFAULT_PREFERENCES
    }
    db.execute(
        '''
        INSERT INTO user_preferences (user_id, theme, font_family, font_scale, density, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            theme = excluded.theme,
            font_family = excluded.font_family,
            font_scale = excluded.font_scale,
            density = excluded.density,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (user_id, prefs['theme'], prefs['font_family'], prefs['font_scale'], prefs['density']),
    )
    db.commit()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return jsonify({'ok': True, 'user': user_payload(user)})


@auth_bp.route('/api/permissions/request', methods=['POST'])
@login_required
def api_permission_request():
    payload = request.get_json(silent=True) or {}
    permission = (payload.get('permission') or '').strip()
    app_id = (payload.get('app_id') or PERMISSION_CATALOG.get(permission, {}).get('app') or 'AIPD').strip()
    reason = (payload.get('reason') or '').strip()[:1000]
    if permission not in PERMISSION_CATALOG:
        return jsonify({'ok': False, 'error': '未知权限。'}), 400
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if permission in _permissions_for(user):
        return jsonify({'ok': True, 'status': 'already_granted'})
    try:
        db.execute(
            '''
            INSERT INTO permission_requests (user_id, app_id, permission, reason, status)
            VALUES (?, ?, ?, ?, 'pending')
            ''',
            (session['user_id'], app_id, permission, reason),
        )
        db.commit()
    except sqlite3.IntegrityError:
        pass
    return jsonify({'ok': True, 'status': 'pending'})


@auth_bp.route('/api/sso/check', methods=['POST'])
def api_sso_check():
    if 'user_id' not in session:
        return jsonify({'ok': False, 'authenticated': False, 'authorized': False}), 401
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user is None:
        session.clear()
        return jsonify({'ok': False, 'authenticated': False, 'authorized': False}), 401
    payload = request.get_json(silent=True) or {}
    permission = (payload.get('permission') or '').strip()
    profile = user_payload(user)
    authorized = not permission or permission in profile['permissions']
    return jsonify({
        'ok': True,
        'authenticated': True,
        'authorized': authorized,
        'user': profile,
        'permissions': profile['permissions'],
        'missing_permission': '' if authorized else permission,
    })


@auth_bp.route('/api/admin/users')
@login_required
def api_admin_users():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not _is_admin_user(user):
        return jsonify({'ok': False, 'error': '无权限'}), 403
    rows = db.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    return jsonify({'ok': True, 'users': [user_payload(row) for row in rows]})


@auth_bp.route('/api/admin/permission-requests')
@login_required
def api_admin_permission_requests():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not _is_admin_user(user):
        return jsonify({'ok': False, 'error': '无权限'}), 403
    rows = db.execute(
        '''
        SELECT pr.*, u.username, u.email, u.nickname
        FROM permission_requests pr
        JOIN users u ON u.id = pr.user_id
        ORDER BY pr.created_at DESC
        LIMIT 100
        '''
    ).fetchall()
    return jsonify({'ok': True, 'requests': [dict(row) for row in rows]})


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
