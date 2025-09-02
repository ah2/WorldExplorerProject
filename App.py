import os
import sqlite3
import json
import tkinter as tk
from tkinter import messagebox
import webview
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
DEBUG_FLAG = (os.getenv('DEBUG_FLAG', 'False') == 'True')

DB_FILE = "urban_explorer.db"

# Predefined cities (name -> lat,lng)
CITIES = {
    "Dubai": (25.2048, 55.2708),
    "New York": (40.7128, -74.0060),
    "Paris": (48.8566, 2.3522),
    "Tokyo": (35.6762, 139.6503),
    "London": (51.5074, -0.1278),
    "San Francisco": (37.7749, -122.4194)
}

# ------------------------------
# Initialize database
# ------------------------------
def init_db():
    if os.path.exists(DB_FILE):
        try:
            # Test if file is a valid DB
            conn = sqlite3.connect(DB_FILE)
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            conn.close()
        except sqlite3.DatabaseError:
            os.remove(DB_FILE)  # Remove corrupted DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            total_score INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS fetched_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lng REAL,
            city TEXT,
            json_data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS collected_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            name TEXT,
            lat REAL,
            lng REAL,
            category TEXT,
            rare INTEGER,
            story_fragment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    conn.commit()
    conn.close()

# ------------------------------
# Database helpers
# ------------------------------
def get_player_id(name):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO players(name) VALUES(?)", (name,))
        conn.commit()
        c.execute("SELECT id FROM players WHERE name=?", (name,))
        player_id = c.fetchone()[0]
        conn.close()
        return player_id
    except Exception as e:
        print("DB Error (get_player_id):", e)
        return None

# ------------------------------
# API for pywebview
# ------------------------------
class Api:
    def __init__(self, api_key, base_url, player_id, lat, lng, city):
        self._api_key = api_key
        self._base_url = base_url
        self.player_id = player_id
        self.current_lat = lat
        self.current_lng = lng
        self.city = city
        self.collected_places = []

    def get_api_key(self):
        return self._api_key

    def get_base_url(self):
        return self._base_url

    def collect_place(self, place_json):
        try:
            place = json.loads(place_json)
            # Avoid duplicate collection
            if not any(p['lat'] == place['lat'] and p['lng'] == place['lng'] for p in self.collected_places):
                self.collected_places.append(place)
                story_fragment = place.get("story", "")
                points = 25 if place.get("rare") else 10
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO collected_places(player_id,name,lat,lng,category,rare,story_fragment)
                    VALUES(?,?,?,?,?,?,?)
                ''', (self.player_id, place.get("name"), place.get("lat"), place.get("lng"),
                      place.get("cat"), int(place.get("rare", False)), story_fragment))
                c.execute("UPDATE players SET total_score = total_score + ? WHERE id = ?", (points, self.player_id))
                conn.commit()
                conn.close()
            return json.dumps(self.collected_places)
        except Exception as e:
            print("Error collecting place:", e)
            return json.dumps(self.collected_places)

    def save_fetched_places(self, places_json):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO fetched_places(lat,lng,city,json_data) VALUES(?,?,?,?)",
                      (self.current_lat, self.current_lng, self.city, places_json))
            conn.commit()
            conn.close()
            return "ok"
        except Exception as e:
            print("Error saving fetched places:", e)
            return "error"

# ------------------------------
# Tkinter GUI
# ------------------------------
def start_gui():
    init_db()
    root = tk.Tk()
    root.title("🌍 Map-based Story Adventure")
    root.geometry("300x220")

    tk.Label(root, text="Enter your player name:").pack(pady=5)
    name_entry = tk.Entry(root)
    name_entry.pack(pady=5)

    tk.Label(root, text="Choose a city:").pack(pady=5)
    city_var = tk.StringVar(value="Dubai")
    tk.OptionMenu(root, city_var, *CITIES.keys()).pack(pady=5)

    def on_start():
        name = name_entry.get().strip()
        city_name = city_var.get()
        if not name:
            messagebox.showerror("Input Error", "Please enter a player name.")
            return
        player_id = get_player_id(name)
        if player_id is None:
            messagebox.showerror("Database Error", "Failed to access or create player in DB.")
            return
        lat, lng = CITIES[city_name]
        root.destroy()
        api = Api(API_KEY, BASE_URL, player_id, lat, lng, city_name)
        map_file = os.path.join(os.getcwd(), "interactive_map.html")
        window = webview.create_window(f"🌍 Story Adventure - {name}", map_file,
                                       width=1000, height=650, js_api=api)
        webview.start(gui="tk" ,debug=DEBUG_FLAG)

    tk.Button(root, text="Start Adventure!", command=on_start).pack(pady=15)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
