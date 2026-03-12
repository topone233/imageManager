from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_db(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            file_hash TEXT,
            phash TEXT,
            size INTEGER,
            mtime REAL,
            width INTEGER,
            height INTEGER,
            caption TEXT,
            ocr_text TEXT,
            tags TEXT,
            embedding BLOB,
            indexed_at TEXT,
            last_used TEXT,
            use_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY,
            image_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            query TEXT,
            ts TEXT NOT NULL,
            FOREIGN KEY(image_id) REFERENCES images(id)
        );

        CREATE INDEX IF NOT EXISTS idx_images_mtime ON images(mtime);
        CREATE INDEX IF NOT EXISTS idx_images_use_count ON images(use_count);
        CREATE INDEX IF NOT EXISTS idx_usage_logs_image_id ON usage_logs(image_id);
        """
    )
    conn.commit()
