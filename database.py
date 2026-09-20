"""
Coco OS — Database & Signal Logger  (Layer L)
=================================================
Every signal Coco ever sends gets logged here: pair,
direction, confidence, the reasons behind it, and (later)
the outcome once enough time has passed.

This is what makes Coco a production system rather than a
toy — it's how Coco proves its own accuracy and how the
self-improvement loop (config.REWEIGHT_EVERY_N_SIGNALS)
knows which data sources to trust more or less over time.

Uses SQLite — a single file, zero setup, completely free.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

from config import DATABASE_PATH


@contextmanager
def get_connection():
    """
    A safe way to open/close the database connection so a
    crash never leaves a connection hanging open.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """
    Creates the signals table if it doesn't already exist.
    Safe to call every time Coco starts up.
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pair TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                source_tag TEXT NOT NULL,
                pip_low REAL,
                pip_high REAL,
                stop_loss_pips REAL,
                reasons TEXT,
                entry_price REAL,
                outcome TEXT DEFAULT 'pending',
                sources_json TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS source_accuracy (
                source_name TEXT PRIMARY KEY,
                total_signals INTEGER DEFAULT 0,
                correct_signals INTEGER DEFAULT 0,
                current_weight REAL DEFAULT 1.0
            )
        """)
    print("  > Database ready.")


def log_signal(pair, direction, confidence, source_tag,
                pip_low=None, pip_high=None, stop_loss_pips=None,
                reasons=None, entry_price=None, sources_json=None):
    """
    Saves one signal to the database. Returns the new
    signal's row ID, or None if saving failed.
    """
    reasons_str = " | ".join(reasons) if reasons else ""

    try:
        with get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO signals
                (timestamp, pair, direction, confidence, source_tag,
                 pip_low, pip_high, stop_loss_pips, reasons,
                 entry_price, sources_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), pair, direction, confidence,
                source_tag, pip_low, pip_high, stop_loss_pips,
                reasons_str, entry_price, sources_json,
            ))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"  ! Database error while logging signal: {e}")
        return None


def update_outcome(signal_id, outcome):
    """
    outcome should be one of: 'win', 'loss', 'breakeven', 'pending'
    """
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE signals SET outcome = ? WHERE id = ?",
                (outcome, signal_id),
            )
    except sqlite3.Error as e:
        print(f"  ! Database error while updating outcome: {e}")


def get_recent_signals(limit=200):
    """Returns the most recent N signals as a list of dicts."""
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"  ! Database error while reading signals: {e}")
        return []


def get_signal_count():
    """Total number of signals ever logged."""
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM signals").fetchone()
            return row[0] if row else 0
    except sqlite3.Error:
        return 0


def get_accuracy_stats():
    """
    Returns a simple accuracy summary dict used for the
    public accuracy report Coco sends every N signals.
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute(
                "SELECT COUNT(*) as c FROM signals WHERE outcome != 'pending'"
            ).fetchone()["c"]
            wins = conn.execute(
                "SELECT COUNT(*) as c FROM signals WHERE outcome = 'win'"
            ).fetchone()["c"]

            win_rate = round((wins / total) * 100, 1) if total > 0 else 0.0

            return {"total_scored": total, "wins": wins, "win_rate": win_rate}
    except sqlite3.Error as e:
        print(f"  ! Database error while computing accuracy: {e}")
        return {"total_scored": 0, "wins": 0, "win_rate": 0.0}
