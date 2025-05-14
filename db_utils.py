
import sqlite3
from datetime import datetime

DB_NAME = "biocontrol.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            score INTEGER,
            traits TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_report(filename, score, traits_list):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reports (filename, score, traits, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        filename,
        score,
        ",".join([t["trait"] for t in traits_list if t["status"] == "Detected"]),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def fetch_recent_reports(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT filename, score, traits, created_at
        FROM reports
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
