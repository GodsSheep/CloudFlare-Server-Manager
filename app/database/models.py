import sqlite3
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    def __init__(self, db_path: str):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialize()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(
                str(self._path),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA foreign_keys=ON')
            self._local.conn = conn
        return self._local.conn

    def _initialize(self):
        with self._lock:
            conn = self._get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    runtime TEXT DEFAULT 'static',
                    entry_file TEXT,
                    host TEXT DEFAULT '127.0.0.1',
                    port INTEGER,
                    status TEXT DEFAULT 'NEW',
                    desired_state TEXT DEFAULT 'STOPPED',
                    tunnel_provider TEXT,
                    public_url TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS processes (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    pid INTEGER,
                    command TEXT,
                    runtime TEXT,
                    port INTEGER,
                    cpu REAL DEFAULT 0,
                    ram INTEGER DEFAULT 0,
                    uptime INTEGER DEFAULT 0,
                    stdout TEXT DEFAULT '',
                    stderr TEXT DEFAULT '',
                    exit_code INTEGER,
                    status TEXT DEFAULT 'CREATED',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tunnels (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT DEFAULT 'DISABLED',
                    public_url TEXT,
                    local_port INTEGER,
                    pid INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS routes (
                    id TEXT PRIMARY KEY,
                    tunnel_id TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    local_port INTEGER NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    FOREIGN KEY (tunnel_id) REFERENCES tunnels(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    version TEXT,
                    status TEXT DEFAULT 'PENDING',
                    source_type TEXT,
                    source_path TEXT,
                    build_log TEXT,
                    health_status TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    finished_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'QUEUED',
                    payload TEXT,
                    progress REAL DEFAULT 0,
                    result TEXT,
                    error TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    started_at TEXT,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT DEFAULT 'application',
                    level TEXT DEFAULT 'info',
                    message TEXT NOT NULL,
                    meta TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS backups (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'COMPLETED',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency INTEGER,
                    error TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
                CREATE INDEX IF NOT EXISTS idx_processes_project ON processes(project_id);
                CREATE INDEX IF NOT EXISTS idx_tunnels_project ON tunnels(project_id);
                CREATE INDEX IF NOT EXISTS idx_logs_category ON logs(category);
                CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at);
            """)
            conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._get_conn().execute(sql, params)

    def executemany(self, sql: str, params: List[tuple]) -> sqlite3.Cursor:
        with self._lock:
            return self._get_conn().executemany(sql, params)

    def executescript(self, sql: str):
        with self._lock:
            self._get_conn().executescript(sql)

    def commit(self):
        with self._lock:
            self._get_conn().commit()

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._get_conn().execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._get_conn().execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn:
            with self._lock:
                self._local.conn.close()
                self._local.conn = None
