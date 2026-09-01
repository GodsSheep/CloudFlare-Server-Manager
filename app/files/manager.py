import os
import shutil
import subprocess
import tempfile
import zipfile
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.core.jobs.manager import JobManager, Job
from app.core.events.bus import EventBus
from app.database.models import Database
from app.runtime.manager import RuntimeManager
from app.server.port import PortManager
from app.core.state.machine import ProjectState, DesiredState, TunnelState


@dataclass
class ProjectInfo:
    id: str
    name: str
    source_path: str
    project_path: str
    runtime: str
    entry_file: str
    host: str
    port: int
    status: str
    desired_state: str
    tunnel_provider: str
    public_url: str


class ProjectManager:
    def __init__(self, db: Database, runtime: RuntimeManager, port_mgr: PortManager, job_mgr: JobManager, events: EventBus):
        self._db = db
        self._runtime = runtime
        self._port_mgr = port_mgr
        self._jobs = job_mgr
        self._events = events
        self._auto_recovery_enabled = True

    def create_project(self, name: str, source: str, runtime_type: str = 'static') -> Optional[ProjectInfo]:
        import uuid
        project_id = str(uuid.uuid4())
        source_path = Path(source)
        project_path = source_path
        entry_file = self._detect_entry(project_path) or ''
        port = self._port_mgr.suggest_available()[0] if self._port_mgr.suggest_available() else 8080
        now = datetime.now().isoformat()
        self._db.execute(
            'INSERT INTO projects (id, name, source_path, project_path, runtime, entry_file, host, port, status, desired_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (project_id, name, str(source_path), str(project_path), runtime_type, entry_file, '127.0.0.1', port, ProjectState.READY.value, DesiredState.STOPPED.value, now, now)
        )
        self._db.commit()
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        row = self._db.fetchone('SELECT * FROM projects WHERE id = ?', (project_id,))
        if not row:
            return None
        return ProjectInfo(**row)

    def list_projects(self) -> List[ProjectInfo]:
        rows = self._db.fetchall('SELECT * FROM projects ORDER BY updated_at DESC')
        return [ProjectInfo(**r) for r in rows]

    def update_status(self, project_id: str, status: str):
        self._db.execute('UPDATE projects SET status = ?, updated_at = ? WHERE id = ?', (status, datetime.now().isoformat(), project_id))
        self._db.commit()
        self._events.publish('project.status_changed', project_id, status)

    def set_desired_state(self, project_id: str, desired: DesiredState):
        self._db.execute('UPDATE projects SET desired_state = ?, updated_at = ? WHERE id = ?', (desired.value, datetime.now().isoformat(), project_id))
        self._db.commit()

    def start_project(self, project_id: str) -> tuple[bool, Optional[str]]:
        project = self.get_project(project_id)
        if not project:
            return False, 'Project not found'
        self.set_desired_state(project_id, DesiredState.RUNNING)
        self.update_status(project_id, ProjectState.STARTING.value)
        from app.runtime.manager import RuntimeConfig
        config = RuntimeConfig(
            runtime_type=project.runtime,
            entry_file=project.entry_file,
            host=project.host,
            port=project.port,
            cwd=project.project_path,
        )
        if not self._port_mgr.reserve(project.port, project_id):
            alt = self._port_mgr.suggest_available(start=project.port + 1)[0]
            config.port = alt
            self._db.execute('UPDATE projects SET port = ? WHERE id = ?', (alt, project_id))
            self._db.commit()
        ok, err = self._runtime.start_project(project_id, config)
        if ok:
            self.update_status(project_id, ProjectState.ONLINE.value)
            return True, None
        else:
            self.update_status(project_id, ProjectState.FAILED.value)
            return False, err

    def stop_project(self, project_id: str) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        self.set_desired_state(project_id, DesiredState.STOPPED)
        self.update_status(project_id, ProjectState.STOPPING.value)
        ok = self._runtime.stop_project(project_id)
        if ok:
            self._port_mgr.release(project.port)
            self.update_status(project_id, ProjectState.STOPPED.value)
        else:
            self.update_status(project_id, ProjectState.FAILED.value)
        return ok

    def restart_project(self, project_id: str) -> tuple[bool, Optional[str]]:
        self.stop_project(project_id)
        time.sleep(0.5)
        return self.start_project(project_id)

    def _detect_entry(self, path: Path) -> Optional[str]:
        candidates = ['index.html', 'index.htm', 'app.py', 'main.py', 'server.py', 'manage.py', 'index.js', 'app.js', 'server.js', 'index.php', 'package.json']
        for c in candidates:
            if (path / c).exists():
                return c
        for f in path.rglob('*'):
            if f.is_file() and f.suffix in ['.html', '.py', '.js', '.php']:
                return str(f.relative_to(path))
        return None

    def import_folder(self, job: Job, project_name: str, source: str, target: str) -> Optional[ProjectInfo]:
        try:
            src = Path(source)
            dst = Path(target)
            dst.mkdir(parents=True, exist_ok=True)
            files = [f for f in src.rglob('*') if f.is_file()]
            total = len(files)
            for i, f in enumerate(files):
                if job.is_cancelled():
                    job.status = JobStatus.CANCELLED
                    return None
                rel = f.relative_to(src)
                dest = dst / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                job.update_progress((i + 1) / total)
            runtime = self._runtime.detect_runtime(str(dst)) or 'static'
            return self.create_project(project_name, str(dst), runtime)
        except Exception as exc:
            job.status = JobStatus.FAILED
            raise exc
