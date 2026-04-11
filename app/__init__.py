import os
import sqlite3
from flask import Flask, g, redirect, url_for, session, send_from_directory
from dotenv import load_dotenv

load_dotenv()


def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'wiki.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db.commit()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder=None)

    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

    # Register teardown
    app.teardown_appcontext(close_db)

    # Initialize database
    init_db(app)

    # Register blueprints
    from .auth import auth_bp
    from .uploader import uploader_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(uploader_bp)

    # Serve static assets (CSS, images, etc.) from project root /assets/
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(assets_dir, filename)

    @app.route('/')
    @app.route('/admin/')
    def index():
        if session.get('user_id'):
            return redirect(url_for('uploader.upload'))
        return redirect(url_for('auth.login'))

    return app
