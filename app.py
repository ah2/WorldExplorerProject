import os
import json
import time
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, logging
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

# Import our DB helper
from db import get_db, init_db

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OVERTURE_API_KEY", "")
OVERTURE_URL = os.getenv("OVERTURE_API_URL", "https://api.overturemaps.com")

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_key")

# Initialize DB on startup
init_db()


# -----------------------------
# Routes
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        if conn is None:
            flash("Database unavailable.")
            return redirect(url_for("login"))

        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cur.fetchone()
        except Exception as e:
            app.logger.error(f"DB error on login: {e}")
            flash("Login failed due to database error.")
            conn.close()
            return redirect(url_for("login"))

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            conn.close()

            return render_template("index.html")
        else:
            flash("Invalid username or password.")
        conn.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    session["username"] = "Guest"
    return redirect(url_for("home"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Both username and password are required.")
            return redirect(url_for("signup"))

        conn = get_db()
        if conn is None:
            flash("Database unavailable.")
            return redirect(url_for("signup"))

        cur = conn.cursor()
        from werkzeug.security import generate_password_hash
        hashed_pw = generate_password_hash(password)

        try:
            cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (username, hashed_pw))
            conn.commit()
            flash("Signup successful. Please log in.")
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            app.logger.error(f"DB error on signup: {e}")
            flash("Signup failed. Username may already exist.")
            conn.close()
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/gallery")
def gallery():
    conn = get_db()
    if conn is None:
        flash("Database unavailable.")
        return redirect(url_for("index"))

    cur = conn.cursor()
    places = cur.execute("SELECT * FROM visited_places").fetchall()
    conn.close()

    return render_template("gallery.html", places=places)


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()

    # Expecting { "name": "...", "lat": ..., "lng": ... }
    city_name = data.get("name")
    lat = data.get("lat")
    lng = data.get("lng")

    if not city_name or lat is None or lng is None:
        return jsonify({"error": "Invalid city data"}), 400

    # Example: create a session or game state
    session = {
        "city": city_name,
        "lat": lat,
        "lng": lng,
        "status": "started"
    }

    # TODO: Add your own game/session initialization logic here
    return jsonify(session), 200


@app.route("/api/places")
def api_places():
    """Proxy call to Overture API using bounding box, save JSON in DB, return to frontend."""
    bbox = request.args.get("bbox")  # expected format: minLon,minLat,maxLon,maxLat
    limit = request.args.get("limit", 50)

    coords = [round(float(x), 6) for x in bbox.split(",")]

    print(f"/places got: {bbox}")
    print (f"/places sent: {",".join(map(str, coords))}")

    if not bbox:
        return jsonify({"error": "Missing bbox"}), 400

    #centerLat = ((parseFloat(minLat) + parseFloat(maxLat)) / 2).toFixed(6)
    #centerLon = ((parseFloat(minLon) + parseFloat(maxLon)) / 2).toFixed(6)

    params = {"limit": limit, "bbox": ",".join(map(str, coords))}


    try:
        r = requests.get(
            OVERTURE_URL,
            headers={"x-api-key": API_KEY},
            params=params,
            timeout=10
        )
        data = r.json()
        print (json.dumps(data))
        # Save raw JSON into api_logs
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO api_logs(endpoint, params, response, timestamp) VALUES (?,?,?,?)",
                ("places", json.dumps(params), json.dumps(data), int(time.time()))
            )
            conn.commit()
            conn.close()

            app.logger.info(f"Fetched bbox {bbox} at {int(time.time())}")

        return jsonify(data)

    except Exception as e:
        app.logger.error(f"Error fetching places: {e}")
        return jsonify({"error": "Failed to fetch places"}), 500


@app.route("/")
def home():
    if "username" not in session:
        session["username"] = "Guest"

    app.logger.info(f"logged in as: {session["username"]}")
    return render_template("index.html", user=session["username"])


@app.route("/admin")
def admin():
    if "username" not in session or session["username"] != "admin":
        flash("Access denied.")
        return redirect(url_for("index"))

    conn = get_db()
    if conn is None:
        flash("Database unavailable.")
        return redirect(url_for("index"))

    cur = conn.cursor()
    users = cur.execute("SELECT id, username FROM users").fetchall()
    logs = cur.execute("SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 10").fetchall()
    conn.close()

    return render_template("admin.html", users=users, logs=logs)


@app.route("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return {"status": "ok"}


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
