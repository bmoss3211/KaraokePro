"""SQLite database setup and access."""
import sqlite3
import os
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "karaokepro.db")

_local = threading.local()


def get_db() -> sqlite3.Connection:
    """Get a thread-local database connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            venue TEXT NOT NULL DEFAULT 'Chaplins'
        );

        CREATE TABLE IF NOT EXISTS singers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            signup_time TEXT NOT NULL,
            songs_sung INTEGER NOT NULL DEFAULT 0,
            tip_total REAL NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS song_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            singer_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            song_title TEXT NOT NULL,
            song_artist TEXT NOT NULL DEFAULT 'Unknown',
            file_path TEXT,
            sung_at TEXT,
            tip_amount REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (singer_id) REFERENCES singers(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_singers_session ON singers(session_id);
        CREATE INDEX IF NOT EXISTS idx_song_history_session ON song_history(session_id);
        CREATE INDEX IF NOT EXISTS idx_song_history_singer ON song_history(singer_id);
    """)
    db.commit()
