import os, sqlite3
from flask import (Flask, render_template, request,
                   redirect, url_for, flash,
                   session, jsonify)
from werkzeug.security import (
    generate_password_hash, check_password_hash)

# ——— App & config —————————————————————————————
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',  # change this!
    DATABASE=os.path.join(app.instance_path, 'blazecoin.sqlite'),
)
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS user (
      id INTEGER PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL
    );
    """)
    db.commit()

@app.before_first_request
def setup():
    init_db()

# ——— In‑memory counter ————————————————————————
active_miners = 0

# ——— Auth for miner ————————————————————————
@app.route('/auth_miner', methods=['POST'])
def auth_miner():
    nonlocal_vars = globals()
    data = request.get_json() or {}
    u = data.get('username','')
    p = data.get('password','')
    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE username=?',
        (u,)
    ).fetchone()
    if user and check_password_hash(user['password'], p):
        nonlocal_vars['active_miners'] += 1
        return jsonify(status='success'), 200
    return jsonify(status='fail'), 401

@app.route('/miner_disconnect', methods=['POST'])
def miner_disconnect():
    nonlocal_vars = globals()
    if nonlocal_vars['active_miners']>0:
        nonlocal_vars['active_miners'] -= 1
    return jsonify(status='ok'), 200

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify(active_miners=globals()['active_miners']), 200

# ——— Registration & login —————————————————————
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        u=request.form['username']
        p=request.form['password']
        db=get_db(); err=None
        if not u or not p:
            err='Required.'
        else:
            try:
                db.execute(
                    'INSERT INTO user (username,password) VALUES (?,?)',
                    (u, generate_password_hash(p))
                )
                db.commit()
            except sqlite3.IntegrityError:
                err='User exists.'
        if err:
            flash(err)
        else:
            flash('Registered! Please log in.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form['username']
        p=request.form['password']
        db=get_db()
        user=db.execute(
          'SELECT * FROM user WHERE username=?',(u,)
        ).fetchone()
        if user and check_password_hash(user['password'],p):
            session.clear()
            session['username']=u
            return redirect(url_for('wallet'))
        flash('Bad credentials')
    return render_template('login.html')

@app.route('/wallet')
def wallet():
    if 'username' not in session:
        return redirect(url_for('login'))
    return f"Hello, {session['username']}! This is your wallet."

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
