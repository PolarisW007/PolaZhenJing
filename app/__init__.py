import json
import os
import sqlite3
from functools import lru_cache
from flask import Flask, current_app, g, redirect, url_for, session, send_from_directory
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TINYMCE_MANIFEST_PATH = os.path.join(
    PROJECT_ROOT, 'assets', 'vendor', 'tinymce', 'tinymce-manifest.json'
)
DEFAULT_TINYMCE_ASSET_VERSION = '6.8.5-pzj-20260602'


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _env_csv(name, default=''):
    return {
        item.strip().lower()
        for item in os.getenv(name, default).split(',')
        if item.strip()
    }


class ReverseProxied:
    """WSGI middleware that handles SCRIPT_NAME from reverse proxy.

    When deployed behind Nginx at a sub-path (e.g. /PolaZhenjing/),
    Nginx sends X-Script-Name header so Flask's url_for() generates
    correct URLs with the prefix.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
        return self.app(environ, start_response)


def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        db_path = current_app.config.get(
            'POLAUUH_DATABASE_PATH',
            os.path.join(PROJECT_ROOT, 'data', 'wiki.db'),
        )
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
        g.db.execute('PRAGMA busy_timeout=5000')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@lru_cache(maxsize=1)
def get_tinymce_asset_manifest():
    """Return TinyMCE vendor metadata used for cache-busted asset URLs."""
    fallback = {
        'name': 'tinymce',
        'version': '6.8.5',
        'asset_version': DEFAULT_TINYMCE_ASSET_VERSION,
    }
    try:
        with open(TINYMCE_MANIFEST_PATH, 'r', encoding='utf-8') as manifest_file:
            manifest = json.load(manifest_file)
    except (OSError, json.JSONDecodeError):
        return fallback
    if not isinstance(manifest, dict):
        return fallback
    asset_version = str(
        manifest.get('asset_version')
        or manifest.get('version')
        or DEFAULT_TINYMCE_ASSET_VERSION
    )
    return {**manifest, 'asset_version': asset_version}


def _ensure_column(db, table, column, ddl):
    columns = {
        row['name'] for row in db.execute(f'PRAGMA table_info({table})').fetchall()
    }
    if column not in columns:
        db.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')


def init_db(app):
    """Initialize database tables."""
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email_verified INTEGER DEFAULT 0,
                password_enabled INTEGER NOT NULL DEFAULT 1,
                status TEXT DEFAULT 'active',
                primary_email_contact_id INTEGER,
                primary_phone_contact_id INTEGER,
                last_login_at TIMESTAMP,
                updated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        _ensure_column(db, 'users', 'nickname', 'nickname TEXT')
        _ensure_column(db, 'users', 'avatar_url', 'avatar_url TEXT')
        _ensure_column(db, 'users', 'role', "role TEXT DEFAULT 'user'")
        _ensure_column(db, 'users', 'password_enabled', 'password_enabled INTEGER NOT NULL DEFAULT 1')
        _ensure_column(db, 'users', 'status', "status TEXT DEFAULT 'active'")
        _ensure_column(db, 'users', 'primary_email_contact_id', 'primary_email_contact_id INTEGER')
        _ensure_column(db, 'users', 'primary_phone_contact_id', 'primary_phone_contact_id INTEGER')
        _ensure_column(db, 'users', 'last_login_at', 'last_login_at TIMESTAMP')
        _ensure_column(db, 'users', 'updated_at', 'updated_at TIMESTAMP')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'dream-gold',
                font_family TEXT DEFAULT 'system',
                font_scale TEXT DEFAULT 'normal',
                density TEXT DEFAULT 'comfortable',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, permission),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS permission_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                app_id TEXT NOT NULL,
                permission TEXT NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewed_by INTEGER,
                review_note TEXT,
                UNIQUE(user_id, permission, status),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS app_user_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                app_id TEXT NOT NULL,
                external_user_id TEXT,
                linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, app_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS user_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                contact_type TEXT NOT NULL,
                contact_value TEXT NOT NULL,
                contact_value_hash TEXT NOT NULL,
                display_value TEXT,
                verified_at TIMESTAMP,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contact_type, contact_value_hash),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_user_contacts_user_type
                ON user_contacts(user_id, contact_type);
            CREATE TABLE IF NOT EXISTS user_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                provider_subject TEXT NOT NULL,
                provider_union_id TEXT,
                provider_email TEXT,
                provider_email_verified INTEGER DEFAULT 0,
                provider_phone TEXT,
                display_name TEXT,
                avatar_url TEXT,
                raw_profile_json TEXT,
                linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, provider_subject),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_user_identities_user_provider
                ON user_identities(user_id, provider);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_identities_provider_union
                ON user_identities(provider, provider_union_id)
                WHERE provider_union_id IS NOT NULL AND provider_union_id <> '';
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                purpose TEXT NOT NULL,
                target_hash TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP,
                attempt_count INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 5,
                request_ip_hash TEXT,
                request_user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_verification_codes_lookup
                ON verification_codes(channel, purpose, target_hash, created_at);
            CREATE INDEX IF NOT EXISTS idx_verification_codes_ip_created
                ON verification_codes(request_ip_hash, created_at);
            CREATE TABLE IF NOT EXISTS auth_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                state_hash TEXT NOT NULL UNIQUE,
                nonce_hash TEXT,
                next_url TEXT,
                bind_user_id INTEGER,
                expires_at TIMESTAMP NOT NULL,
                consumed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(bind_user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS auth_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                provider TEXT,
                result TEXT NOT NULL,
                reason TEXT,
                request_ip_hash TEXT,
                request_user_agent TEXT,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_user_created
                ON auth_audit_logs(user_id, created_at);
            CREATE TABLE IF NOT EXISTS article_likes (
                article_id TEXT PRIMARY KEY,
                like_count INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        from .identity.contacts import contact_hash, mask_contact

        users = db.execute(
            'SELECT id, email, email_verified FROM users WHERE email IS NOT NULL'
        ).fetchall()
        for user in users:
            value = (user['email'] or '').strip().lower()
            if not value or value.endswith('@polauuh.local'):
                continue
            value_hash = contact_hash('email', value)
            existing = db.execute(
                "SELECT id, user_id FROM user_contacts WHERE contact_type = 'email' "
                'AND contact_value_hash = ?',
                (value_hash,),
            ).fetchone()
            if existing:
                if existing['user_id'] == user['id']:
                    db.execute(
                        'UPDATE users SET primary_email_contact_id = '
                        'COALESCE(primary_email_contact_id, ?) WHERE id = ?',
                        (existing['id'], user['id']),
                    )
                continue
            cursor = db.execute(
                '''
                INSERT INTO user_contacts
                (user_id, contact_type, contact_value, contact_value_hash,
                 display_value, verified_at, is_primary)
                VALUES (?, 'email', ?, ?, ?,
                        CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END, 1)
                ''',
                (
                    user['id'],
                    value,
                    value_hash,
                    mask_contact('email', value),
                    1 if user['email_verified'] else 0,
                ),
            )
            db.execute(
                'UPDATE users SET primary_email_contact_id = ? WHERE id = ?',
                (cursor.lastrowid, user['id']),
            )
        db.commit()


def create_app(test_config=None):
    app = Flask(__name__, template_folder='templates', static_folder=None)

    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    app.config.update(
        POLAUUH_DATABASE_PATH=os.getenv(
            'POLAUUH_DATABASE_PATH', os.path.join(PROJECT_ROOT, 'data', 'wiki.db')
        ),
        POLAUUH_ADMIN_EMAILS=_env_csv('POLAUUH_ADMIN_EMAILS', 'wsyxjer@gmail.com'),
        POLAUUH_ADMIN_USERNAMES=_env_csv('POLAUUH_ADMIN_USERNAMES', 'admin,sirius'),
        POLAUUH_EMAIL_VERIFICATION_REQUIRED=_env_bool(
            'POLAUUH_EMAIL_VERIFICATION_REQUIRED', True
        ),
        POLAUUH_MAIL_ENABLED=_env_bool(
            'POLAUUH_MAIL_ENABLED', bool(os.getenv('QQ_EMAIL') and os.getenv('QQ_EMAIL_AUTH_CODE'))
        ),
        POLAUUH_SMS_ENABLED=_env_bool('POLAUUH_SMS_ENABLED', False),
        POLAUUH_OTP_TTL_SECONDS=int(os.getenv('POLAUUH_OTP_TTL_SECONDS', '300')),
        POLAUUH_OTP_RESEND_SECONDS=int(os.getenv('POLAUUH_OTP_RESEND_SECONDS', '60')),
        POLAUUH_OTP_MAX_ATTEMPTS=int(os.getenv('POLAUUH_OTP_MAX_ATTEMPTS', '5')),
        POLAUUH_OTP_TARGET_HOURLY_LIMIT=int(
            os.getenv('POLAUUH_OTP_TARGET_HOURLY_LIMIT', '6')
        ),
        POLAUUH_OTP_IP_HOURLY_LIMIT=int(os.getenv('POLAUUH_OTP_IP_HOURLY_LIMIT', '20')),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=_env_bool('POLAUUH_COOKIE_SECURE', False),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )
    for provider in ['GOOGLE', 'APPLE', 'WECHAT', 'ALIPAY', 'HUAWEI']:
        app.config[f'POLAUUH_{provider}_ENABLED'] = _env_bool(
            f'POLAUUH_{provider}_ENABLED', False
        )
    for key in [
        'POLAUUH_ALIYUN_CAPTCHA_SCENE_ID',
        'POLAUUH_ALIYUN_CAPTCHA_PREFIX',
        'POLAUUH_ALIYUN_CAPTCHA_REGION',
        'POLAUUH_GOOGLE_CLIENT_ID',
        'POLAUUH_GOOGLE_CLIENT_SECRET',
        'POLAUUH_GOOGLE_REDIRECT_URI',
        'POLAUUH_APPLE_CLIENT_ID',
        'POLAUUH_APPLE_TEAM_ID',
        'POLAUUH_APPLE_KEY_ID',
        'POLAUUH_APPLE_PRIVATE_KEY_PATH',
        'POLAUUH_APPLE_REDIRECT_URI',
        'POLAUUH_WECHAT_APP_ID',
        'POLAUUH_WECHAT_APP_SECRET',
        'POLAUUH_WECHAT_REDIRECT_URI',
        'POLAUUH_ALIPAY_APP_ID',
        'POLAUUH_ALIPAY_PRIVATE_KEY_PATH',
        'POLAUUH_ALIPAY_PUBLIC_KEY_PATH',
        'POLAUUH_ALIPAY_REDIRECT_URI',
        'POLAUUH_HUAWEI_CLIENT_ID',
        'POLAUUH_HUAWEI_CLIENT_SECRET',
        'POLAUUH_HUAWEI_REDIRECT_URI',
    ]:
        app.config[key] = os.getenv(key, '')
    app.config['POLAUUH_ALIYUN_CAPTCHA_ENABLED'] = _env_bool(
        'POLAUUH_ALIYUN_CAPTCHA_ENABLED', False
    )
    if test_config:
        app.config.update(test_config)

    # Werkzeug 3.x 默认 max_form_memory_size = 500KB,富文本编辑后的 body
    # 经常 1.5-2x 膨胀,粘贴图片 / 重排样式后超过 500KB 即触发 413。
    # 提到 16MB,和 MAX_CONTENT_LENGTH 对齐,允许一篇文章最大 16MB 富文本。
    app.config['MAX_FORM_MEMORY_SIZE'] = 16 * 1024 * 1024  # 16 MB form field

    # Apply reverse proxy middleware for sub-path deployment
    app.wsgi_app = ProxyFix(
        ReverseProxied(app.wsgi_app),
        x_for=1,
        x_proto=1,
        x_host=1,
    )

    # Register teardown
    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_vendor_manifests():
        return {
            'tinymce_asset_manifest': get_tinymce_asset_manifest,
        }

    # Initialize database
    init_db(app)

    # Initialize async jobs table
    from . import jobs
    jobs.init_schema()
    from .social_publish import init_schema as init_social_publish_schema
    init_social_publish_schema()

    # Register blueprints
    from .auth import auth_bp
    from .admin_workbench import admin_workbench_bp
    from .uploader import public_articles_bp, uploader_bp
    from .social_publish import social_publish_bp
    from .skillhub import skillhub_bp
    from .agent import agent_admin_bp, agent_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_workbench_bp)
    app.register_blueprint(public_articles_bp)
    app.register_blueprint(uploader_bp)
    app.register_blueprint(social_publish_bp)
    app.register_blueprint(skillhub_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(agent_admin_bp)

    # Serve static assets (CSS, images, etc.) from project root /assets/
    assets_dir = os.path.join(PROJECT_ROOT, 'assets')

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(assets_dir, filename)

    @app.route('/')
    @app.route('/admin/')
    def index():
        if session.get('user_id'):
            if session.get('role') == 'admin':
                return redirect(url_for('admin_workbench.workbench'))
            return redirect(url_for('auth.account'))
        return redirect(url_for('auth.login'))

    @app.route('/healthz')
    def healthz():
        return {'ok': True, 'service': 'PolaZhenjing/PolaUUH'}

    return app
