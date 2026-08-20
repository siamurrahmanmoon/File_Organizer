"""
core/rollback_manager.py - SQLite Operation Journaling, Checkpointing & 1-Click Rollback/Undo.
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from utils.file_utils import safe_move, safe_delete


class RollbackManager:
    """
    Tracks all file operations in an SQLite journal.
    Enables instant 1-click Undo / Rollback and Checkpoint resumption.
    """

    def __init__(self, db_path: str = "logs/operations_journal.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Creates the operations and sessions tables."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT,
                    end_time TEXT,
                    source_dir TEXT,
                    output_dir TEXT,
                    status TEXT,
                    total_files INTEGER,
                    processed_files INTEGER,
                    error_count INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT,
                    source_path TEXT,
                    target_path TEXT,
                    operation_type TEXT, -- 'move', 'copy', 'quarantine'
                    file_hash TEXT,
                    status TEXT,         -- 'completed', 'rolled_back', 'failed'
                    details TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()

    def start_session(self, source_dir: str, output_dir: str, total_files: int = 0) -> str:
        """Starts a new tracking session and returns the session_id."""
        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, start_time, source_dir, output_dir, status, total_files, processed_files, error_count)
                VALUES (?, ?, ?, ?, 'running', ?, 0, 0)
            """, (session_id, datetime.now().isoformat(), str(source_dir), str(output_dir), total_files))
            conn.commit()
        return session_id

    def log_operation(
        self,
        session_id: str,
        source_path: str,
        target_path: str,
        operation_type: str = "move",
        file_hash: str = "",
        details: str = ""
    ):
        """Records a successful file operation in the journal."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO operations (session_id, timestamp, source_path, target_path, operation_type, file_hash, status, details)
                VALUES (?, ?, ?, ?, ?, ?, 'completed', ?)
            """, (
                session_id,
                datetime.now().isoformat(),
                str(source_path),
                str(target_path),
                operation_type,
                file_hash,
                details
            ))
            cursor.execute("""
                UPDATE sessions SET processed_files = processed_files + 1 WHERE session_id = ?
            """, (session_id,))
            conn.commit()

    def complete_session(self, session_id: str, status: str = "completed", error_count: int = 0):
        """Marks a session as finished."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions
                SET end_time = ?, status = ?, error_count = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), status, error_count, session_id))
            conn.commit()

    def get_processed_files_in_session(self, session_id: str) -> List[str]:
        """Returns list of source paths already processed in the given session for checkpointing."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source_path FROM operations WHERE session_id = ? AND status = 'completed'", (session_id,))
            rows = cursor.fetchall()
            return [r[0] for r in rows]

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns recent sessions for UI display."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def rollback_session(self, session_id: str) -> Tuple[int, int, List[str]]:
        """
        Reverses all operations in a session: moves files back from target to source!
        Returns (success_count, error_count, error_messages).
        """
        success_count = 0
        error_count = 0
        errors = []

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM operations
                WHERE session_id = ? AND status = 'completed'
                ORDER BY id DESC
            """, (session_id,))
            operations = cursor.fetchall()

            for op in operations:
                op_id = op["id"]
                src = Path(op["source_path"])
                dst = Path(op["target_path"])
                op_type = op["operation_type"]

                try:
                    if dst.exists():
                        if op_type == "move" or op_type == "quarantine":
                            # Move file back to source
                            safe_move(str(dst), str(src))
                        elif op_type == "copy":
                            # Delete the copied target
                            safe_delete(str(dst))

                        cursor.execute("UPDATE operations SET status = 'rolled_back' WHERE id = ?", (op_id,))
                        success_count += 1
                    else:
                        errors.append(f"Target file missing: {dst}")
                        error_count += 1
                except Exception as e:
                    errors.append(f"Failed to restore {dst} -> {src}: {e}")
                    error_count += 1

            cursor.execute("UPDATE sessions SET status = 'rolled_back' WHERE session_id = ?", (session_id,))
            conn.commit()

        return success_count, error_count, errors
