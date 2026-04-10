import functools
import random
import string
import time

from flask import (Blueprint, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from . import get_db
from .mailer import send_verification_code

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')


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

        user = db.execute('SELECT * FROM users WHERE username = ?',
                          (username,)).fetchone()
        if user is None:
            error = '用户名不存在。'
        elif not check_password_hash(user['password_hash'], password):
            error = '密码错误。'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('uploader.upload'))

        flash(error, 'error')
    return render_template('login.html')


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
        elif not email.endswith('@qq.com'):
            error = '仅支持 QQ 邮箱（@qq.com）。'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, generate_password_hash(password))
                )
                db.commit()

                # Generate and send verification code
                code = ''.join(random.choices(string.digits, k=6))
                session['verify_code'] = code
                session['verify_code_time'] = time.time()
                session['verify_email'] = email
                session['pending_user'] = username

                sent = send_verification_code(email, code)
                if sent:
                    flash('验证码已发送到您的邮箱。', 'info')
                    return redirect(url_for('auth.verify'))
                else:
                    flash('注册成功。邮件发送失败，请直接登录。', 'warning')
                    return redirect(url_for('auth.login'))

            except db.IntegrityError:
                error = f'用户 {username} 或邮箱 {email} 已被注册。'

        flash(error, 'error')
    return render_template('register.html')


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

        # Clean up session
        session.pop('verify_code', None)
        session.pop('verify_code_time', None)
        session.pop('verify_email', None)
        session.pop('pending_user', None)

        flash('邮箱验证成功！请登录。', 'success')
        return redirect(url_for('auth.login'))

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


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
