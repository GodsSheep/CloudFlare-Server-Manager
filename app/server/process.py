try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

import threading
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from app.core.state.machine import ProcessState


@dataclass
class ProcessInfo:
    pid: Optional[int] = None
    command: str = ''
    runtime: str = ''
    port: Optional[int] = None
    cpu: float = 0.0
    ram: int = 0
    uptime: int = 0
    stdout: str = ''
    stderr: str = ''
    exit_code: Optional[int] = None
    state: ProcessState = ProcessState.CREATED
    created_at: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pid': self.pid,
            'command': self.command,
            'runtime': self.runtime,
            'port': self.port,
            'cpu': self.cpu,
            'ram': self.ram,
            'uptime': self.uptime,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'state': self.state.value,
            'created_at': self.created_at,
        }


class ProcessSupervisor:
    def __init__(self, on_state_change: Optional[Callable[[str, ProcessState], None]] = None):
        self._processes: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._on_state_change = on_state_change
        self._monitors: Dict[str, threading.Thread] = {}

    def register(self, process_id: str, proc: Any):
        with self._lock:
            self._processes[process_id] = proc
            if process_id not in self._monitors:
                t = threading.Thread(target=self._monitor_loop, args=(process_id,), daemon=True)
                self._monitors[process_id] = t
                t.start()

    def unregister(self, process_id: str):
        with self._lock:
            self._processes.pop(process_id, None)

    def get(self, process_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._processes.get(process_id)

    def _monitor_loop(self, process_id: str):
        while True:
            proc = self.get(process_id)
            if not proc:
                break
            try:
                if proc.get('pid') and psutil.pid_exists(proc['pid']):
                    p = psutil.Process(proc['pid'])
                    info = ProcessInfo(
                        pid=proc['pid'],
                        command=proc.get('command', ''),
                        runtime=proc.get('runtime', ''),
                        port=proc.get('port'),
                        cpu=p.cpu_percent(interval=0.1),
                        ram=p.memory_info().rss,
                        uptime=int((datetime.now() - datetime.fromisoformat(proc.get('started_at', datetime.now().isoformat()))).total_seconds()),
                        state=ProcessState.ONLINE,
                    )
                    with self._lock:
                        self._processes[process_id].update(info.to_dict())
                    if self._on_state_change:
                        self._on_state_change(process_id, ProcessState.ONLINE)
                else:
                    if proc.get('state') not in (ProcessState.STOPPED, ProcessState.FAILED, ProcessState.CRASHED):
                        with self._lock:
                            self._processes[process_id]['state'] = ProcessState.CRASHED.value
                        if self._on_state_change:
                            self._on_state_change(process_id, ProcessState.CRASHED)
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            time.sleep(2)

    def update_state(self, process_id: str, state: ProcessState):
        with self._lock:
            if process_id in self._processes:
                self._processes[process_id]['state'] = state.value
        if self._on_state_change:
            self._on_state_change(process_id, state)
