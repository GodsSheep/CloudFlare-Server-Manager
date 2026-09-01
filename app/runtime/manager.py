import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

from app.core.state.machine import ProcessState, ProjectState
from app.server.process import ProcessSupervisor, ProcessInfo
from app.server.port import PortManager
from app.core.events.bus import EventBus
from app.core.jobs.manager import JobManager, Job


@dataclass
class RuntimeConfig:
    runtime_type: str
    entry_file: str
    host: str = '127.0.0.1'
    port: int = 8080
    env: Dict[str, str] = None
    cwd: str = ''

    def __post_init__(self):
        if self.env is None:
            self.env = {}


class BaseRuntime(ABC):
    name: str = 'base'
    command_name: str = ''

    def detect(self, path: Path) -> bool:
        return False

    def validate(self, path: Path) -> List[str]:
        return []

    def prepare(self, config: RuntimeConfig) -> bool:
        return True

    @abstractmethod
    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        pass

    def stop(self, process: subprocess.Popen) -> bool:
        try:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            return True
        except Exception:
            return False

    def restart(self, process: subprocess.Popen, config: RuntimeConfig) -> Optional[subprocess.Popen]:
        self.stop(process)
        time.sleep(0.5)
        return self.start(config)

    def health(self, process: subprocess.Popen, port: int) -> bool:
        return True

    def logs(self, process: subprocess.Popen) -> str:
        return ''


class StaticRuntime(BaseRuntime):
    name = 'static'
    command_name = 'python'

    def detect(self, path: Path) -> bool:
        return any(
            (path / f).exists()
            for f in ['index.html', 'index.htm']
        )

    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        http_server = shutil.which('python') or shutil.which('python3') or sys.executable
        cmd = [http_server, '-m', 'http.server', str(config.port)]
        return subprocess.Popen(
            cmd,
            cwd=config.cwd or str(config.entry_file),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


class PythonRuntime(BaseRuntime):
    name = 'python'
    command_name = 'python'

    def detect(self, path: Path) -> bool:
        return any(
            (path / f).exists()
            for f in ['app.py', 'main.py', 'manage.py', 'server.py']
        )

    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        entry = Path(config.entry_file)
        cmd = [sys.executable, str(entry.name)]
        return subprocess.Popen(
            cmd,
            cwd=str(entry.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **config.env},
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


class NodeRuntime(BaseRuntime):
    name = 'node'
    command_name = 'node'

    def detect(self, path: Path) -> bool:
        if (path / 'package.json').exists():
            return True
        return any(
            (path / f).exists()
            for f in ['server.js', 'app.js', 'index.js', 'main.js']
        )

    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        entry = Path(config.entry_file)
        package_dir = entry.parent if entry.name != 'package.json' else entry
        if (package_dir / 'package.json').exists():
            cmd = [shutil.which('node') or 'node', str(entry.name)]
        else:
            cmd = [shutil.which('node') or 'node', str(entry.name)]
        return subprocess.Popen(
            cmd,
            cwd=str(package_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **config.env},
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


class PHPRuntime(BaseRuntime):
    name = 'php'
    command_name = 'php'

    def detect(self, path: Path) -> bool:
        return any(
            (path / f).exists()
            for f in ['index.php', 'app.php', 'server.php']
        )

    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        entry = Path(config.entry_file)
        php = shutil.which('php') or 'php'
        cmd = [php, '-S', f"{config.host}:{config.port}", '-t', str(entry.parent)]
        return subprocess.Popen(
            cmd,
            cwd=str(entry.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


class DockerRuntime(BaseRuntime):
    name = 'docker'
    command_name = 'docker'

    def detect(self, path: Path) -> bool:
        return (path / 'Dockerfile').exists() or (path / 'docker-compose.yml').exists()

    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        docker = shutil.which('docker') or 'docker'
        entry = Path(config.entry_file)
        cmd = [docker, 'run', '--rm', '-p', f"{config.port}:80", str(entry.parent.name)]
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


class CustomRuntime(BaseRuntime):
    name = 'custom'
    command_name = ''

    def detect(self, path: Path) -> bool:
        return False

    def start(self, config: RuntimeConfig) -> subprocess.Popen:
        if not config.entry_file:
            raise ValueError('Custom runtime requires entry_file (command)')
        cmd = config.entry_file.split()
        return subprocess.Popen(
            cmd,
            cwd=config.cwd or '.',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **config.env},
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


class RuntimeManager:
    def __init__(self):
        self._runtimes = [
            StaticRuntime(),
            PythonRuntime(),
            NodeRuntime(),
            PHPRuntime(),
            DockerRuntime(),
            CustomRuntime(),
        ]
        self._processes: Dict[str, subprocess.Popen] = {}
        self._supervisor = ProcessSupervisor()
        self._lock = threading.Lock()

    def detect_runtime(self, path: str) -> Optional[str]:
        p = Path(path)
        for rt in self._runtimes:
            if rt.detect(p):
                return rt.name
        return None

    def get_runtime(self, name: str) -> Optional[BaseRuntime]:
        for rt in self._runtimes:
            if rt.name == name:
                return rt
        return None

    def start_project(self, project_id: str, config: RuntimeConfig) -> tuple[bool, Optional[str]]:
        rt = self.get_runtime(config.runtime_type)
        if not rt:
            return False, f"Runtime '{config.runtime_type}' not found"
        try:
            proc = rt.start(config)
            with self._lock:
                self._processes[project_id] = proc
            self._supervisor.register(project_id, {
                'pid': proc.pid,
                'command': ' '.join(proc.args),
                'runtime': config.runtime_type,
                'port': config.port,
                'started_at': datetime.now().isoformat(),
                'state': ProcessState.STARTING.value,
            })
            return True, None
        except Exception as exc:
            return False, str(exc)

    def stop_project(self, project_id: str) -> bool:
        with self._lock:
            proc = self._processes.get(project_id)
        if not proc:
            return False
        rt = self.get_runtime(project_id.split('_')[0] if '_' in project_id else 'static')
        if rt:
            rt.stop(proc)
        else:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self._supervisor.unregister(project_id)
        with self._lock:
            self._processes.pop(project_id, None)
        return True

    def get_process(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self._supervisor.get(project_id)

    def list_runtimes(self) -> List[str]:
        return [rt.name for rt in self._runtimes]
