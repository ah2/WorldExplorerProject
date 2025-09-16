import os
import json
import time
import requests
from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, url_for, session, flash, logging
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

# Import our DB helper
from db import *

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OVERTURE_API_KEY", "")
OVERTURE_URL = os.getenv("OVERTURE_API_URL", "")
OVERTURE_countries_URL = os.getenv("OVERTURE_API_countries_URL", "")


# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_key")
debug_mode = os.getenv('debug_mode', 'False').lower() in ['true', '1', 't']

# Initialize DB on startup
init_db()


# -----------------------------
# Routes
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
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
            session['username'] = username
            conn.close()

            #app.logger.info( f"logged in as: { session['username'] }" )

            return render_template("index.html")
        else:
            flash("Invalid username or password.")
        conn.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    app.logger.info( f"{session ['username'] } logged out")
    session['username'] = "Guest"
    return redirect(url_for("home"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
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
        return redirect(url_for("home"))

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
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    limit = request.args.get("limit", 50)


    #coords = [round(float(x), 5) for x in bbox.split(",")]

    if bbox:
        # bbox = "minLon,minLat,maxLon,maxLat"
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
        center_lat = round((min_lat + max_lat) / 2, 6)
        center_lon = round((min_lon + max_lon) / 2, 6)
        # approximate radius in meters from bbox size (Haversine would be better)
        lat_radius = (max_lat - min_lat) * 111_000 / 2
        lon_radius = (max_lon - min_lon) * 111_000 / 2
        radius = int(max(lat_radius, lon_radius))
        params = {"lat": center_lat, "lng": center_lon, "radius": radius } #"limit": limit
    elif lat and lng:
        params = {"lat": lat, "lng": lng, "radius": radius } #"limit": limit

        #params = {"lat": center_lat, "lng": center_lon, "radius": radius, "limit": limit}
    

    if not bbox:
        return jsonify({"error": "Missing bbox"}), 400

    #centerLat = ((parseFloat(minLat) + parseFloat(maxLat)) / 2).toFixed(6)
    #centerLon = ((parseFloat(minLon) + parseFloat(maxLon)) / 2).toFixed(6)

    #params = {"limit": limit, "bbox": ",".join(map(str, coords))}


    try:
        r = requests.get(
            OVERTURE_URL,
            headers={"x-api-key": API_KEY},
            params=params,
            timeout=10
        )
        data = r.json()

        # API logs (for debugging/replay)
        insert_log("places", json.dumps(params), json.dumps(data))

        return jsonify(data)

    except Exception as e:
        app.logger.error(f"Error fetching places: {e}")
        return jsonify({"error": "Failed to fetch places"}), 500

@app.route("/api/search")
def api_search():
    """Proxy to Nominatim to avoid CORS issues"""
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 5
    }

    try:
        r = requests.get(url, params=params, headers={"User-Agent": "YourApp/1.0"})
        data = r.json()
        
        # API logs (for debugging/replay)
        insert_log("city_search", json.dumps(params), json.dumps(data))

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.before_request
def ensure_guest():
    if "username" not in session:
        session["username"] = "Guest"

@app.route("/")
def home():
    print(str(session))
    if 'username' not in session:
        session['username'] = "Guest"

    app.logger.info(f"logged in as: {session['username']}")
    return render_template("index.html", user=session['username'])


@app.route("/admin")
def admin():
    if 'username' not in session or session['username'] != "admin":
        flash("Access denied.")
        return redirect(url_for("home"))

    conn = get_db()
    if conn is None:
        flash("Database unavailable.")
        return redirect(url_for("home"))

    cur = conn.cursor()
    users = cur.execute("SELECT id, username FROM users").fetchall()
    logs = cur.execute("SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 10").fetchall()
    conn.close()

    return render_template("admin.html", users=users, logs=logs)



# --- SESSION ENDPOINT ---
@app.route("/api/session")
def api_session():
    """
    Returns the current logged-in user.
    If no user in session, return Guest.
    """
    user = session.get("username", "Guest")
    return jsonify({"user": user})


# --- COUNTRIES ENDPOINT ---
@app.route("/api/countries")
def api_countries():
    """
    Fetch all countries from Overture Maps.
    """
    try:
        res = requests.get(
            OVERTURE_countries_URL,
            headers={"x-api-key": API_KEY},
            timeout=10
        )

        res.raise_for_status()
        data = res.json()

        app.logger.info(f"countries:\n\n{data}\n\n\n")

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        # Convert response into a cleaner list
        countries = []

        def get_iso(iso):            
            cur.execute("SELECT name FROM iso_countries WHERE iso_code=?", (iso,))
            row = cur.fetchone()
            name = row[0] if row else iso
            return {"iso_code": iso, "name": name}

        # Case 1: Response is a list
        if isinstance(data, list):
            for c in data:
                props = c.get("country", {})
                countries.append(get_iso(props))

        # Case 2: Response is a FeatureCollection { "features": [...] }
        elif isinstance(data, dict) and "features" in data:
            for c in data["features"]:
                props = c.get("country", {})
                countries.append(get_iso(props))

        return jsonify(countries)
    except Exception as e:
        app.logger.error(f"Error fetching countries: {e}")
        return jsonify([]), 500

ISO_MAPPING_URL = "https://gist.githubusercontent.com/ssskip/5a94bfcd2835bf1dea52/raw/ISO3166-1.alpha2.json"

def init_iso_countries():
    try:
        resp = requests.get(ISO_MAPPING_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()  # { "US": "United States", ... }

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        for code, name in data.items():
            cur.execute(
                "INSERT OR REPLACE INTO iso_countries (iso_code, name) VALUES (?, ?)",
                (code.upper(), name)
            )

        conn.commit()
        conn.close()

        app.logger.info("✅ ISO country codes loaded into DB.")
    
    except Exception as e:
        app.logger.info(f"❌ Failed to load ISO countries: {e}")

# --- CITIES ENDPOINT ---
@app.route("/api/cities")
def api_cities():
    """
    Fetch cities in a given country.
    Expects ?country=ISO_CODE
    """
    country = request.args.get("country")
    if not country:
        return jsonify({"error": "country parameter required"}), 400
    

    try:
        res = requests.get(
            f"https://api.overturemapsapi.com/places/categories?country={country}&category=locality",
            headers={"x-api-key": API_KEY},
            timeout=10
        )

        res.raise_for_status()
        data = res.json()

        app.logger.error(data)

        cities = []
        for c in data:
            props = c.get("properties", {})
            geom = c.get("geometry", {}).get("coordinates", [])
            if len(geom) >= 2:
                cities.append({
                    "name": props.get("names", {}).get("primary", "Unknown"),
                    "lat": geom[1],
                    "lng": geom[0],
                })

        return jsonify(cities)
    except Exception as e:
        app.logger.error(f"Error fetching cities: {e}")
        return jsonify([]), 500

@app.route("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return {"status": "ok"}

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                                'favicon.ico',
                                mimetype='image/vnd.microsoft.icon')




# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":

    if (API_KEY != 'DEMO-API-KEY'):
        init_iso_countries()
        app.run(debug=debug_mode)
    else:
        print('please update .env with an api key')

    print('exiting....')
