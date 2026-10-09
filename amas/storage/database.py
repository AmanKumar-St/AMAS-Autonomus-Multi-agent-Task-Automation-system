"""
AMAS SQLite Persistence Layer
=============================
Provides structured persistence for runs, tasks, events, tool calls, and artifacts.
Uses native sqlite3 with thread-safe connection pooling.
"""

from __future__ import annotations
import sqlite3
import json
import time
import os
import threading
from typing import Dict, List, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.getcwd(), "amas", "storage", "amas.db")


class AMASDatabase:
    """SQLite repository for all AMAS operational data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. Runs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                status TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                start_time REAL,
                end_time REAL,
                duration_ms REAL,
                metrics_json TEXT,
                blackboard_json TEXT
            );
            """)

            # 2. Tasks table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT,
                run_id TEXT,
                title TEXT,
                description TEXT,
                agent TEXT,
                status TEXT,
                dependencies_json TEXT,
                tool_required TEXT,
                result TEXT,
                verification_json TEXT,
                duration_ms REAL,
                PRIMARY KEY (task_id, run_id)
            );
            """)

            # 3. Events table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT,
                timestamp REAL,
                event_type TEXT,
                agent TEXT,
                tool TEXT,
                duration_ms REAL,
                payload_json TEXT
            );
            """)

            # 4. Tool calls table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                call_id TEXT PRIMARY KEY,
                run_id TEXT,
                tool_name TEXT,
                source TEXT,
                arguments_json TEXT,
                output_json TEXT,
                success INTEGER,
                duration_ms REAL,
                error TEXT
            );
            """)

            # 5. Artifacts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                run_id TEXT,
                filename TEXT,
                file_type TEXT,
                file_path TEXT,
                size_bytes INTEGER,
                created_at REAL
            );
            """)

            # 6. Approvals table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                req_id TEXT PRIMARY KEY,
                run_id TEXT,
                task_id TEXT,
                tool_id TEXT,
                kwargs_json TEXT,
                status TEXT,
                created_at REAL,
                resolved_at REAL
            );
            """)

            conn.commit()
            conn.close()

    def save_run(self, run_id: str, objective: str, status: str, provider: str = "", model: str = "", blackboard: Dict = None):
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
            INSERT INTO runs (run_id, objective, status, provider, model, start_time, blackboard_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status=excluded.status,
                blackboard_json=excluded.blackboard_json;
            """, (run_id, objective, status, provider, model, time.time(), json.dumps(blackboard or {}, default=str)))
            conn.commit()
            conn.close()

    def update_run_completed(self, run_id: str, status: str, duration_ms: float, metrics: Dict, blackboard: Dict):
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
            UPDATE runs SET
                status = ?,
                end_time = ?,
                duration_ms = ?,
                metrics_json = ?,
                blackboard_json = ?
            WHERE run_id = ?;
            """, (status, time.time(), duration_ms, json.dumps(metrics, default=str), json.dumps(blackboard, default=str), run_id))
            conn.commit()
            conn.close()

    def save_task(self, task_data: Dict[str, Any], run_id: str):
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
            INSERT INTO tasks (task_id, run_id, title, description, agent, status, dependencies_json, tool_required, result, verification_json, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id, run_id) DO UPDATE SET
                status=excluded.status,
                result=excluded.result,
                verification_json=excluded.verification_json,
                duration_ms=excluded.duration_ms;
            """, (
                task_data["id"],
                run_id,
                task_data.get("title", ""),
                task_data.get("description", ""),
                task_data.get("agent", ""),
                task_data.get("status", "PENDING"),
                json.dumps(task_data.get("dependencies", [])),
                task_data.get("tool_required"),
                task_data.get("result"),
                json.dumps(task_data.get("verification") or {}),
                task_data.get("execution_time_ms", 0.0)
            ))
            conn.commit()
            conn.close()

    def save_event(self, event_data: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
            INSERT OR REPLACE INTO events (event_id, run_id, timestamp, event_type, agent, tool, duration_ms, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                event_data.get("event_id", str(time.time())),
                event_data.get("run_id", ""),
                event_data.get("timestamp", time.time()),
                event_data.get("event_type", ""),
                event_data.get("agent", ""),
                event_data.get("tool", ""),
                event_data.get("duration_ms", 0.0),
                json.dumps(event_data.get("payload", {}), default=str)
            ))
            conn.commit()
            conn.close()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if not row:
                conn.close()
                return None
            run_dict = dict(row)
            task_rows = conn.execute("SELECT * FROM tasks WHERE run_id = ?", (run_id,)).fetchall()
            run_dict["tasks"] = [dict(r) for r in task_rows]
            conn.close()
            return run_dict

    def list_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            rows = conn.execute("SELECT * FROM runs ORDER BY start_time DESC LIMIT ?", (limit,)).fetchall()
            conn.close()
            return [dict(r) for r in rows]

    def save_approval(self, approval_data: Dict[str, Any]):
        """Save or update an approval request."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
            INSERT INTO approvals (req_id, run_id, task_id, tool_id, kwargs_json, status, created_at, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(req_id) DO UPDATE SET
                status=excluded.status,
                resolved_at=excluded.resolved_at;
            """, (
                approval_data["req_id"],
                approval_data["run_id"],
                approval_data["task_id"],
                approval_data["tool_id"],
                json.dumps(approval_data.get("kwargs", {}), default=str),
                approval_data["status"],
                approval_data["created_at"],
                approval_data.get("resolved_at")
            ))
            conn.commit()
            conn.close()

    def update_approval(self, req_id: str, status: str, resolved_at: float):
        """Update approval status and resolution time."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
            UPDATE approvals SET
                status = ?,
                resolved_at = ?
            WHERE req_id = ?;
            """, (status, resolved_at, req_id))
            conn.commit()
            conn.close()

    def get_pending_approvals(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending approvals, optionally filtered by run_id."""
        with self._lock:
            conn = self._get_connection()
            if run_id:
                rows = conn.execute("SELECT * FROM approvals WHERE run_id = ? AND status = 'PENDING'", (run_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM approvals WHERE status = 'PENDING'").fetchall()
            conn.close()
            return [dict(r) for r in rows]

    def get_approval(self, req_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific approval by ID."""
        with self._lock:
            conn = self._get_connection()
            row = conn.execute("SELECT * FROM approvals WHERE req_id = ?", (req_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
