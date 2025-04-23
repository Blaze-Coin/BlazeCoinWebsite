import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","change_this!")

# put your DB file next to app.py
DATABASE = os.path.join(os.path.dirname(__file__), "blazecoin.db")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db()
        conn.execute("""
          CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
          );
        """)
        conn.commit()
        conn.close()

# call it at import time so you never have to run it manually
init_db()

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method=="POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)", (u,p))
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Username already taken"
        finally:
            conn.close()
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method=="POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = get_db()
        cur = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = cur.fetchone()
        conn.close()
        if user:
            session["username"] = u
            return redirect(url_for("wallet"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/wallet")
def wallet():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("wallet.html", username=session["username"])

@app.route("/auth_miner", methods=["POST"])
def auth_miner():
    data = request.get_json(force=True)
    u = data.get("username")
    p = data.get("password")
    conn = get_db()
    cur = conn.execute("SELECT 1 FROM users WHERE username=? AND password=?", (u,p))
    ok = cur.fetchone() is not None
    conn.close()
    if ok:
        return jsonify(status="success")
    else:
        return jsonify(status="fail", message="Invalid credentials"), 401

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
