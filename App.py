import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OVERTURE_API_KEY")
API_URL = os.getenv("OVERTURE_API_URL","https://api.overturemaps.com/places")
SECRET_KEY = os.getenv("FLASK_SECRET","supersecret")

# Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Setup logging to file
if not os.path.exists("app.log"):
    open("app.log","w").close()
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

# Database
DB_FILE = "world_adventure.db"

def get_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        app.logger.error("DB connection failed: %s", e)
        return None

def init_db():
    conn = get_db()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        # Users table
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password TEXT
                    )""")
        # Player table
        cur.execute("""CREATE TABLE IF NOT EXISTS player (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        lat REAL,
                        lng REAL,
                        score INTEGER
                    )""")
        # Visited places table
        cur.execute("""CREATE TABLE IF NOT EXISTS visited_places (
                        name TEXT,
                        category TEXT,
                        lat REAL,
                        lng REAL
                    )""")
        # Default player if empty
        cur.execute("SELECT COUNT(*) FROM player")
        if cur.fetchone()[0]==0:
            cur.execute("INSERT INTO player(username, lat, lng, score) VALUES (?,?,?,?)",
                        ("default",0,0,0))
        # Default user if empty
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0]==0:
            cur.execute("INSERT INTO users(username,password) VALUES (?,?)", ("testuser","password"))
        conn.commit()
    except sqlite3.Error as e:
        app.logger.error("DB init failed: %s", e)
    finally:
        conn.close()

init_db()

# ------------------- Routes -------------------

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method=="POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
                user = cur.fetchone()
                if user:
                    session["user"] = username
                    return redirect(url_for("home"))
                else:
                    error = "Invalid credentials"
            except sqlite3.Error as e:
                app.logger.error("Login DB error: %s", e)
                error = "Database error, please try again."
            finally:
                conn.close()
        else:
            error = "Database connection failed."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    players = []
    places = []
    logs = ""
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM player")
            players = cur.fetchall()
            cur.execute("SELECT * FROM visited_places")
            places = cur.fetchall()
            # Load last 50 log lines
            if os.path.exists("app.log"):
                with open("app.log","r") as f:
                    logs = "".join(f.readlines()[-50:])
        except sqlite3.Error as e:
            app.logger.error("Admin DB error: %s", e)
        finally:
            conn.close()
    return render_template("admin.html", players=players, places=places, logs=logs)

@app.route("/scoreboard")
def scoreboard():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    player = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM player WHERE username=?",(session["user"],))
            player = cur.fetchone()
        except sqlite3.Error as e:
            app.logger.error("Scoreboard DB error: %s", e)
        finally:
            conn.close()
    return render_template("scoreboard.html", player=player)

@app.route("/gallery")
def gallery():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    places = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM visited_places")
            places = cur.fetchall()
        except sqlite3.Error as e:
            app.logger.error("Gallery DB error: %s", e)
        finally:
            conn.close()
    return render_template("gallery.html", places=places)

# ------------------- API -------------------

@app.route("/api/move")
def move_api():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    if lat is None or lng is None:
        return jsonify({"error":"Missing coordinates"}),400

    headers = {"x-api-key": API_KEY}
    params = {"lat": lat, "lng": lng, "radius": 5000, "limit": 100}

    try:
        resp = requests.get(API_URL, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Handle both dict and list responses
        if isinstance(data, dict):
            features = data.get("features", [])
        elif isinstance(data, list):
            features = data
        else:
            features = []
        return jsonify({"places": features})
    except requests.exceptions.RequestException as e:
        app.logger.error("API call failed: %s", e)
        return jsonify({"places": [], "error": "Could not fetch nearby places. You can still explore the map."}), 200

@app.route("/api/score")
def api_score():
    conn = get_db()
    player = None
    visited = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM player WHERE username=?",(session.get("user","default"),))
            player = cur.fetchone()
            cur.execute("SELECT * FROM visited_places")
            visited = [dict(p) for p in cur.fetchall()]
        except sqlite3.Error as e:
            app.logger.error("API score DB error: %s", e)
        finally:
            conn.close()
    return jsonify({"player": dict(player) if player else {}, "visited": visited})

@app.route("/signup", methods=["GET","POST"])
def signup():
    error=None
    if request.method=="POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO users(username,password) VALUES (?,?)",(username,password))
                conn.commit()
                session["user"]=username
                return redirect(url_for("home"))
            except sqlite3.IntegrityError:
                error="Username already exists"
            except sqlite3.Error as e:
                app.logger.error("Signup DB error: %s", e)
                error="Database error"
            finally:
                conn.close()
        else:
            error="Database connection failed"
    return render_template("signup.html", error=error)


@app.route("/api/remove_place")
def remove_place():
    name = request.args.get("name")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    if not name or lat is None or lng is None:
        return jsonify({"error":"Missing parameters"}),400
    conn = get_db()
    success=False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM visited_places WHERE name=? AND lat=? AND lng=?", (name,lat,lng))
            conn.commit()
            success=True
        except sqlite3.Error as e:
            app.logger.error("Remove place DB error: %s", e)
        finally:
            conn.close()
    return jsonify({"success": success})

if __name__=="__main__":
    app.run(debug=True)
