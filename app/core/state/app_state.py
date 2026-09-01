from pathlib import Path
from app.database.models import Database
from app.core.jobs.manager import JobManager
from app.core.events.bus import EventBus
from app.runtime.manager import RuntimeManager
from app.server.port import PortManager
from app.files.manager import ProjectManager
from app.tunnels.manager import TunnelManager
from app.utils.helpers import which_cloudflared, which_ngrok, which_node, which_php, which_docker
from app.utils.log_manager import LogManager
from app.core.state.repair import StartupRepair


class AppState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, data_dir: str):
        if self._initialized:
            return
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db = Database(str(self.data_dir / 'database' / 'nebulaforge.db'))
        self.events = EventBus()
        self.jobs = JobManager()
        self.runtime = RuntimeManager()
        self.port_mgr = PortManager()
        self.projects = ProjectManager(self.db, self.runtime, self.port_mgr, self.jobs, self.events)
        self.tunnels = TunnelManager(self.db, self.events)
        self.logs = LogManager(self.db)
        self.repair = StartupRepair(self.db)
        self._run_startup_repair()
        self._initialized = True

    def _run_startup_repair(self):
        try:
            issues = self.repair.repair()
            for issue in issues:
                self.logs.warning(f'Startup repair: {issue}')
        except Exception as exc:
            self.logs.error(f'Startup repair failed: {exc}')

    @property
    def is_initialized(self) -> bool:
        return getattr(self, '_initialized', False)

    def shutdown(self):
        if hasattr(self, 'db'):
            self.db.close()
