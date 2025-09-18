import sqlite3
import os
import time
from werkzeug.security import generate_password_hash
from flask import current_app

DB_FILE_name = "world_adventure.sqlite"


def get_db():
    """Get a DB connection with row factory."""
    try:
        conn = sqlite3.connect(DB_FILE_name)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        if current_app:
            current_app.logger.error("DB connection failed: %s", e)
        else:
            print(f"DB connection failed: {e}")
        return None

def get_curr():
     return get_db().cursor()

def insert_log(end_point, params, data):
        db_conn = get_db()
        if db_conn:
            cur = db_conn.cursor()
            cur.execute(
                "INSERT INTO api_logs(endpoint, params, response, timestamp) VALUES (?,?,?,?)",
                (end_point, params, data, int(time.time()))
            )
            db_conn.commit()
            db_conn.close()

def get_user(username):
        try:
            conn = get_db()
            if conn is None:
                return None
        
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cur.fetchone()
            conn.close()
            return user
        

        except Exception as e:
            conn.close()
            return e

def insert_user(username, hashed_pw):
    try:
        conn = get_db()
        if conn is None:
            return None

        cur = conn.cursor()

        
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return username

    except Exception as e:
        return None

def init_db(name):
    """Initialize the database with required tables and seed data."""
    DB_FILE_name = name
    create_new = not os.path.exists(DB_FILE_name)


    conn = get_db()
    if conn is None:
        return
    cur = conn.cursor()

    # API logs (for debugging/replay)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            params TEXT,
            response TEXT,
            timestamp INTEGER
        )
    """)

    # countries map iso code to name
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iso_countries (
            iso_code TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    # cashe city
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT NOT NULL,
        name TEXT NOT NULL,
        lat REAL,
        lon REAL,
        UNIQUE(country_code, name)
    );
    """)

    

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Player table (one per user ideally)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            lat REAL DEFAULT 0,
            lng REAL DEFAULT 0,
            score INTEGER DEFAULT 0
        )
    """)

    # Visited places table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visited_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            category TEXT,
            lat REAL,
            lng REAL
        )
    """)

    # Seed default data only if fresh DB
    if create_new:
        print(f"\033[31mCreating new database at {DB_FILE_name}.\033[0m")
        # Test users
        test_users = [
            ("admin", generate_password_hash("admin123")),
            ("john", generate_password_hash("johnpass")),
            ("alice", generate_password_hash("alicepass")),
            ("bob", generate_password_hash("bobpass")),
        ]
        cur.executemany("INSERT INTO users (username,password) VALUES (?,?)", test_users)

        # Default player linked to admin
        cur.execute(
            "INSERT INTO player (username, lat, lng, score) VALUES (?,?,?,?)",
            ("admin", 25.276987, 55.296249, 0)
        )

    conn.commit()
    conn.close()

    return True
