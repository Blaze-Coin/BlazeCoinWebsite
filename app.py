import os
import sqlite3
import hashlib
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.cli.command('init-db')
def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        balance INTEGER DEFAULT 0
    );
    ''')
    db.commit()
    print("Initialized the database.")

@app.route('/')
def index():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    u = request.form['username']
    p = request.form['password']
    if not u or not p:
        return "Missing credentials", 400
    h = hashlib.sha256(p.encode()).hexdigest()
    try:
        db = get_db()
        db.execute('INSERT INTO users (username,password_hash) VALUES (?,?)', (u,h))
        db.commit()
    except sqlite3.IntegrityError:
        return "Username taken", 400
    return "Registration successful", 200

@app.route('/auth_miner', methods=['POST'])
def auth_miner():
    data = request.get_json()
    u = data.get('username')
    p = data.get('password')
    if not u or not p:
        return jsonify(status='error', message='Missing credentials'), 400
    h = hashlib.sha256(p.encode()).hexdigest()
    row = get_db().execute(
        'SELECT 1 FROM users WHERE username=? AND password_hash=?',
        (u,h)
    ).fetchone()
    if not row:
        return jsonify(status='error', message='Invalid username/password'), 401
    return jsonify(status='success'), 200

if __name__ == '__main__':
    app.run()
