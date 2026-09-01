import socket
import threading
from typing import Optional, List
from dataclasses import dataclass

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None


@dataclass
class PortInfo:
    port: int
    available: bool
    pid: Optional[int] = None
    process_name: str = ''


class PortManager:
    def __init__(self):
        self._reserved: Dict[int, str] = {}
        self._lock = threading.Lock()

    def reserve(self, port: int, project_id: str) -> bool:
        with self._lock:
            if port in self._reserved:
                return False
            self._reserved[port] = project_id
            return True

    def release(self, port: int):
        with self._lock:
            self._reserved.pop(port, None)

    def is_available(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False

    def check(self, port: int) -> PortInfo:
        available = self.is_available(port)
        info = PortInfo(port=port, available=available)
        if not available and HAS_PSUTIL:
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.laddr.port == port and conn.pid:
                        info.pid = conn.pid
                        try:
                            info.process_name = psutil.Process(conn.pid).name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            info.process_name = 'Unknown'
                        break
            except Exception:
                pass
        return info

    def suggest_available(self, start: int = 8080, count: int = 5) -> List[int]:
        suggested = []
        port = start
        while len(suggested) < count and port < 65535:
            if self.is_available(port):
                suggested.append(port)
            port += 1
        return suggested

    def find_by_pid(self, pid: int) -> Optional[int]:
        if not HAS_PSUTIL:
            return None
        try:
            p = psutil.Process(pid)
            for conn in p.connections(kind='inet'):
                if conn.status == psutil.CONN_LISTEN:
                    return conn.laddr.port
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
