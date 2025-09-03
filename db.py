import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_FILE = "game.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_FILE):
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE player (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lng REAL,
            score INTEGER DEFAULT 0
        )
        """)

        cur.execute("""
        CREATE TABLE visited_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            lat REAL,
            lng REAL
        )
        """)

        cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        # Visited places table
        cur.execute("""CREATE TABLE IF NOT EXISTS visited_places (
                        name TEXT, category TEXT, lat REAL, lng REAL
                    )""")

        # Player table
        cur.execute("""CREATE TABLE IF NOT EXISTS player (
                        id INTEGER PRIMARY KEY, username TEXT, lat REAL, lng REAL, score INTEGER
                    )""")

        # Users table
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password TEXT
                    )""")

        # Insert default player if empty
        cur.execute("SELECT COUNT(*) FROM player")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO player(username, lat, lng, score) VALUES (?, ?, ?, ?)",
                        ("default", 0, 0, 0))

        # Initialize default player
        cur.execute("INSERT INTO player (lat,lng,score) VALUES (?,?,?)",
                    (25.276987,55.296249,0))

        # Default admin
        hashed = generate_password_hash("admin123")
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)", ("admin",hashed))

        # Create admin and test users
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO users(username,password) VALUES (?,?)", ("john", "johnpass"))
            cur.execute("INSERT INTO users(username,password) VALUES (?,?)", ("alice", "alicepass"))
            cur.execute("INSERT INTO users(username,password) VALUES (?,?)", ("bob", "bobpass"))

        conn.commit()
        conn.close()
