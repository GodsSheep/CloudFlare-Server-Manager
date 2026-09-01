import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.core.state.machine import TunnelState
from app.core.events.bus import EventBus
from app.database.models import Database


class BaseTunnel(ABC):
    name: str = 'base'
    executable_name: str = ''

    def detect(self) -> bool:
        return shutil.which(self.executable_name) is not None

    def install_status(self) -> Dict[str, Any]:
        return {'installed': self.detect(), 'path': shutil.which(self.executable_name)}

    @abstractmethod
    def configure(self, local_port: int, **kwargs) -> bool:
        pass

    @abstractmethod
    def start(self, local_port: int) -> subprocess.Popen:
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

    def restart(self, process: subprocess.Popen, local_port: int) -> Optional[subprocess.Popen]:
        self.stop(process)
        time.sleep(0.5)
        return self.start(local_port)

    @abstractmethod
    def status(self, process: subprocess.Popen) -> TunnelState:
        pass

    @abstractmethod
    def get_public_url(self, process: subprocess.Popen) -> Optional[str]:
        pass

    def logs(self, process: subprocess.Popen) -> str:
        return ''


class CloudflareTunnel(BaseTunnel):
    name = 'cloudflare'
    executable_name = 'cloudflared'

    def configure(self, local_port: int, **kwargs) -> bool:
        return True

    def start(self, local_port: int) -> subprocess.Popen:
        cmd = [shutil.which('cloudflared') or 'cloudflared', 'tunnel', '--url', f'http://127.0.0.1:{local_port}']
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )

    def status(self, process: subprocess.Popen) -> TunnelState:
        if process.poll() is None:
            return TunnelState.CONNECTED
        return TunnelState.FAILED

    def get_public_url(self, process: subprocess.Popen) -> Optional[str]:
        import re
        try:
            for line in iter(process.stderr.readline, ''):
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    return match.group(0)
        except Exception:
            pass
        return None


class NgrokTunnel(BaseTunnel):
    name = 'ngrok'
    executable_name = 'ngrok'

    def configure(self, local_port: int, **kwargs) -> bool:
        return True

    def start(self, local_port: int) -> subprocess.Popen:
        cmd = [shutil.which('ngrok') or 'ngrok', 'http', str(local_port)]
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )

    def status(self, process: subprocess.Popen) -> TunnelState:
        return TunnelState.CONNECTED if process.poll() is None else TunnelState.FAILED

    def get_public_url(self, process: subprocess.Popen) -> Optional[str]:
        import re
        try:
            for line in iter(process.stderr.readline, ''):
                match = re.search(r'https://[a-zA-Z0-9-]+\.ngrok(-free)?\.(io|app)', line)
                if match:
                    return match.group(0)
        except Exception:
            pass
        return None


class LocalTunnel(BaseTunnel):
    name = 'localtunnel'
    executable_name = 'lt'

    def configure(self, local_port: int, **kwargs) -> bool:
        return True

    def start(self, local_port: int) -> subprocess.Popen:
        cmd = [shutil.which('lt') or 'lt', '--port', str(local_port)]
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )

    def status(self, process: subprocess.Popen) -> TunnelState:
        return TunnelState.CONNECTED if process.poll() is None else TunnelState.FAILED

    def get_public_url(self, process: subprocess.Popen) -> Optional[str]:
        import re
        try:
            for line in iter(process.stdout.readline, ''):
                match = re.search(r'https://[a-zA-Z0-9-]+\.loca\.lt', line)
                if match:
                    return match.group(0)
        except Exception:
            pass
        return None


class TunnelManager:
    def __init__(self, db: Database, events: EventBus):
        self._db = db
        self._events = events
        self._providers = [CloudflareTunnel(), NgrokTunnel(), LocalTunnel()]
        self._processes: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()

    def list_providers(self) -> List[str]:
        return [p.name for p in self._providers if p.detect()]

    def get_provider(self, name: str) -> Optional[BaseTunnel]:
        for p in self._providers:
            if p.name == name:
                return p
        return None

    def start_tunnel(self, project_id: str, provider_name: str, local_port: int) -> tuple[bool, Optional[str], Optional[str]]:
        provider = self.get_provider(provider_name)
        if not provider:
            return False, 'Provider not found', None
        if not provider.detect():
            return False, f'{provider_name} is not installed', None
        try:
            proc = provider.start(local_port)
            with self._lock:
                self._processes[project_id] = proc
            import uuid
            tunnel_id = str(uuid.uuid4())
            self._db.execute(
                'INSERT INTO tunnels (id, project_id, provider, status, local_port, pid, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (tunnel_id, project_id, provider_name, TunnelState.STARTING.value, local_port, proc.pid, datetime.now().isoformat(), datetime.now().isoformat())
            )
            self._db.commit()
            public_url = provider.get_public_url(proc)
            if public_url:
                self._db.execute('UPDATE tunnels SET public_url = ?, status = ? WHERE id = ?', (public_url, TunnelState.CONNECTED.value, tunnel_id))
                self._db.execute('UPDATE projects SET public_url = ? WHERE id = ?', (public_url, project_id))
                self._db.commit()
            return True, None, public_url
        except Exception as exc:
            return False, str(exc), None

    def stop_tunnel(self, project_id: str) -> bool:
        with self._lock:
            proc = self._processes.pop(project_id, None)
        if proc:
            provider = self._get_current_provider(project_id)
            if provider:
                provider.stop(proc)
            self._db.execute("UPDATE tunnels SET status = 'DISABLED' WHERE project_id = ?", (project_id,))
            self._db.execute("UPDATE projects SET tunnel_provider = NULL, public_url = NULL WHERE id = ?", (project_id,))
            self._db.commit()
            return True
        return False

    def _get_current_provider(self, project_id: str) -> Optional[BaseTunnel]:
        row = self._db.fetchone('SELECT provider FROM tunnels WHERE project_id = ? ORDER BY created_at DESC LIMIT 1', (project_id,))
        if row:
            return self.get_provider(row['provider'])
        return None
