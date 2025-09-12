import sqlite3
import os
import time
from werkzeug.security import generate_password_hash
from flask import current_app

DB_FILE = "world_adventure.db"


def get_db():
    """Get a DB connection with row factory."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        if current_app:
            current_app.logger.error("DB connection failed: %s", e)
        else:
            print(f"DB connection failed: {e}")
        return None


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

def init_db():
    """Initialize the database with required tables and seed data."""
    create_new = not os.path.exists(DB_FILE)
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
        # Insert admin (hashed password)
        admin_pass = generate_password_hash("admin123")
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)", ("admin", admin_pass))

        # Test users
        test_users = [
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
