import functools
import random
import string
import time

from flask import (Blueprint, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from . import get_db
from .mailer import send_verification_code

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')


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
    display_name = (
        (user['nickname'] if 'nickname' in user.keys() else '')
        or user['username']
        or user['email']
    )
    role = 'admin' if _is_admin_user(user) else (user['role'] if 'role' in user.keys() else 'user')
    permissions = ['articles.read', 'skills.read', 'polaread.use', 'polanews.use']
    if role == 'admin':
        permissions.extend(['articles.manage', 'skills.manage', 'users.manage', 'projects.manage'])
    return {
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'nickname': display_name,
        'avatar_url': user['avatar_url'] if 'avatar_url' in user.keys() else '',
        'role': role,
        'permissions': permissions,
    }


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

            except db.IntegrityError:
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
        nickname = request.form.get('nickname', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip()
        db.execute(
            'UPDATE users SET nickname = ?, avatar_url = ? WHERE id = ?',
            (nickname or user['username'], avatar_url, user['id'])
        )
        db.commit()
        session['nickname'] = nickname or user['username']
        session['avatar_url'] = avatar_url
        flash('账户信息已更新。', 'success')
        return redirect(url_for('auth.account'))

    return render_template('account.html', user=user, profile=user_payload(user))


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


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
