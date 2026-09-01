import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database.models import Database
from app.core.state.machine import ProjectState, ProcessState, TunnelState, DesiredState


logger = logging.getLogger('nebulaforge')


class StartupRepair:
    def __init__(self, db: Database):
        self._db = db

    def repair(self) -> List[str]:
        issues = []
        issues.extend(self._repair_projects())
        issues.extend(self._repair_processes())
        issues.extend(self._repair_tunnels())
        return issues

    def _repair_projects(self) -> List[str]:
        issues = []
        rows = self._db.fetchall("SELECT id, status, desired_state, project_path FROM projects")
        for row in rows:
            if row['status'] == ProjectState.ONLINE.value:
                import os
                if not os.path.exists(row.get('project_path', '')):
                    self._db.execute(
                        'UPDATE projects SET status = ?, desired_state = ? WHERE id = ?',
                        (ProjectState.STOPPED.value, DesiredState.STOPPED.value, row['id'])
                    )
                    issues.append(f"Project {row['id']} path missing, set to STOPPED")
        self._db.commit()
        return issues

    def _repair_processes(self) -> List[str]:
        issues = []
        rows = self._db.fetchall("SELECT id, pid, status FROM processes")
        for row in rows:
            pid = row.get('pid')
            if pid:
                try:
                    import psutil
                    if not psutil.pid_exists(pid):
                        self._db.execute('UPDATE processes SET status = ? WHERE id = ?', (ProcessState.CRASHED.value, row['id']))
                        issues.append(f"Process {row['id']} (PID {pid}) no longer exists")
                except ImportError:
                    pass
                except Exception:
                    pass
        self._db.commit()
        return issues

    def _repair_tunnels(self) -> List[str]:
        issues = []
        rows = self._db.fetchall("SELECT id, pid, status FROM tunnels")
        for row in rows:
            pid = row.get('pid')
            if pid:
                try:
                    import psutil
                    if not psutil.pid_exists(pid):
                        self._db.execute('UPDATE tunnels SET status = ? WHERE id = ?', (TunnelState.DISABLED.value, row['id']))
                        issues.append(f"Tunnel {row['id']} (PID {pid}) no longer exists")
                except ImportError:
                    pass
                except Exception:
                    pass
        self._db.commit()
        return issues
