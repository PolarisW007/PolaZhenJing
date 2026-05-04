#!/usr/bin/env python3
"""Initialize admin user on production server."""
import sqlite3
import sys
sys.path.insert(0, '/PolaZhenjing')

from werkzeug.security import generate_password_hash

conn = sqlite3.connect('/PolaZhenjing/data/wiki.db')
cursor = conn.cursor()
try:
    cursor.execute(
        'INSERT INTO users (username, email, password_hash, email_verified) VALUES (?, ?, ?, ?)',
        ('admin', 'admin@qq.com', generate_password_hash('admin123'), 1)
    )
    conn.commit()
    print('Admin user created: admin / admin123')
except Exception as e:
    print(f'User may already exist: {e}')
conn.close()
