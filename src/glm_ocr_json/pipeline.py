
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from .discovery import discover_images
from .ocr import OCRProcessor, OCRResult, OCRTask


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file to detect duplicates."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read items in chunks to avoid loading large files into memory
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class JobManager:
    """Manages the state of OCR jobs using a SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS images (
                    hash TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    metadata TEXT,
                    status TEXT DEFAULT 'PENDING',
                    result TEXT,
                    error TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Index on status for faster lookup of pending jobs
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON images(status)")

    def register_image(self, path: Path, root: Path) -> bool:
        """
        Register an image if it's new (based on hash).
        Returns True if new, False if already exists.
        """
        file_hash = compute_file_hash(path)
        
        # Calculate metadata from path relative to root
        try:
            rel_path = path.relative_to(root)
            # folder_names as parts of the path (excluding filename)
            folder_names = list(rel_path.parent.parts)
        except ValueError:
            folder_names = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT hash FROM images WHERE hash = ?", (file_hash,))
            if cursor.fetchone():
                return False  # Already exists

            conn.execute(
                "INSERT INTO images (hash, path, metadata, status) VALUES (?, ?, ?, ?)",
                (file_hash, str(path), json.dumps(folder_names), "PENDING"),
            )
        return True

    def get_next_pending(self) -> Optional[Tuple[str, str, List[str]]]:
        """Get the next PENDING job. Returns (hash, path, metadata_list)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT hash, path, metadata FROM images WHERE status = 'PENDING' ORDER BY path LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return row[0], row[1], json.loads(row[2])
        return None

    def mark_completed(self, file_hash: str, result: Dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE images SET status = 'DONE', result = ?, updated_at = ? WHERE hash = ?",
                (json.dumps(result, ensure_ascii=False), datetime.now(), file_hash),
            )

    def mark_failed(self, file_hash: str, error: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE images SET status = 'ERROR', error = ?, updated_at = ? WHERE hash = ?",
                (error, datetime.now(), file_hash),
            )

    def get_stats(self) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT status, COUNT(*) FROM images GROUP BY status")
            return dict(cursor.fetchall())
