import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

DB_PATH = Path("data") / "bot.sqlite3"

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH.as_posix())
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            model TEXT NOT NULL,
            text TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            telegram_user_id INTEGER,
            mode TEXT,
            model TEXT,
            score INTEGER NOT NULL, -- 1=like, -1=dislike
            created_at TEXT NOT NULL
        );
        """)
        conn.commit()

def make_cache_key(text: str, mode: str) -> str:
    # стабильный ключ: (mode + \n + text) -> sha256
    raw = (mode + "\n" + text).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()

def cache_get(key: str) -> Optional[Tuple[str, str, str]]:
    """
    returns (result, model, created_at) or None
    """
    with _connect() as conn:
        row = conn.execute("SELECT result, model, created_at FROM cache WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return (row["result"], row["model"], row["created_at"])

def cache_set(key: str, mode: str, model: str, text: str, result: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache(key, mode, model, text, result, created_at) VALUES(?,?,?,?,?,?)",
            (key, mode, model, text, result, datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()

def feedback_add(
    key: Optional[str],
    telegram_user_id: int,
    mode: Optional[str],
    model: Optional[str],
    score: int
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO feedback(key, telegram_user_id, mode, model, score, created_at) VALUES(?,?,?,?,?,?)",
            (key, telegram_user_id, mode, model, score, datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()
