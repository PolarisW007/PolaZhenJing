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
            error = 'Username not found.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

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
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password or len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif not email.endswith('@qq.com'):
            error = 'Only QQ email (@qq.com) is supported.'

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
                    flash('Verification code sent to your email.', 'info')
                    return redirect(url_for('auth.verify'))
                else:
                    flash('Registration successful. Email sending failed — please login directly.', 'warning')
                    return redirect(url_for('auth.login'))

            except db.IntegrityError:
                error = f'User {username} or email {email} is already registered.'

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
            flash('No pending verification.', 'error')
            return redirect(url_for('auth.register'))

        if time.time() - code_time > 300:  # 5 min expiry
            flash('Verification code expired. Please register again.', 'error')
            return redirect(url_for('auth.register'))

        if code != stored_code:
            flash('Invalid verification code.', 'error')
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

        flash('Email verified! Please log in.', 'success')
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
            flash('Current password is incorrect.', 'error')
        elif len(new_pw) < 6:
            flash('New password must be at least 6 characters.', 'error')
        elif new_pw != confirm:
            flash('New passwords do not match.', 'error')
        else:
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                       (generate_password_hash(new_pw), session['user_id']))
            db.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('uploader.upload'))

    return render_template('password.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
