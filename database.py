"""
Database SQLite — gestione annunci e deduplicazione
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "subbuteo.db"

class Database:
    def __init__(self):
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    price       TEXT,
                    url         TEXT NOT NULL,
                    image_url   TEXT,
                    site        TEXT NOT NULL,
                    country     TEXT NOT NULL,
                    country_flag TEXT,
                    found_at    TEXT NOT NULL,
                    notified    INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    scanned_at  TEXT NOT NULL,
                    new_found   INTEGER DEFAULT 0,
                    total_sites INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def exists(self, listing_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM listings WHERE id = ?", (listing_id,)
            ).fetchone()
            return row is not None

    def insert(self, listing: dict) -> bool:
        """Inserisce un annuncio. Ritorna True se è nuovo."""
        if self.exists(listing["id"]):
            return False
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO listings (id, title, price, url, image_url, site, country, country_flag, found_at, notified)
                VALUES (:id, :title, :price, :url, :image_url, :site, :country, :country_flag, :found_at, 0)
            """, listing)
            conn.commit()
        return True

    def mark_notified(self, listing_id: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE listings SET notified = 1 WHERE id = ?", (listing_id,)
            )
            conn.commit()

    def get_unnotified(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM listings WHERE notified = 0 ORDER BY found_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_listings(self, limit: int = 200) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM listings ORDER BY found_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
            today = conn.execute(
                "SELECT COUNT(*) FROM listings WHERE found_at >= date('now')"
            ).fetchone()[0]
            by_country = conn.execute(
                "SELECT country, country_flag, COUNT(*) as cnt FROM listings GROUP BY country ORDER BY cnt DESC"
            ).fetchall()
            last_scan = conn.execute(
                "SELECT scanned_at FROM scan_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return {
                "total": total,
                "today": today,
                "by_country": [dict(r) for r in by_country],
                "last_scan": last_scan[0] if last_scan else None,
            }

    def log_scan(self, new_found: int, total_sites: int):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO scan_log (scanned_at, new_found, total_sites) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), new_found, total_sites)
            )
            conn.commit()
