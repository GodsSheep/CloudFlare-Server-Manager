import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

print("Testing NebulaForge core modules...")

try:
    from app.core.state.machine import ProjectState, ProcessState, TunnelState, DesiredState
    print("  [OK] State machine")
except Exception as e:
    print(f"  [FAIL] State machine: {e}")

try:
    from app.core.events.bus import EventBus
    print("  [OK] Event bus")
except Exception as e:
    print(f"  [FAIL] Event bus: {e}")

try:
    from app.core.jobs.manager import JobManager, Job, JobStatus
    print("  [OK] Job manager")
except Exception as e:
    print(f"  [FAIL] Job manager: {e}")

try:
    from app.database.models import Database
    print("  [OK] Database models")
except Exception as e:
    print(f"  [FAIL] Database models: {e}")

try:
    from app.server.process import ProcessSupervisor, ProcessInfo
    print("  [OK] Process supervisor")
except Exception as e:
    print(f"  [FAIL] Process supervisor: {e}")

try:
    from app.server.port import PortManager
    print("  [OK] Port manager")
except Exception as e:
    print(f"  [FAIL] Port manager: {e}")

try:
    from app.runtime.manager import RuntimeManager, StaticRuntime, PythonRuntime, NodeRuntime, PHPRuntime, DockerRuntime, CustomRuntime
    print("  [OK] Runtime manager")
except Exception as e:
    print(f"  [FAIL] Runtime manager: {e}")

try:
    from app.tunnels.manager import TunnelManager, CloudflareTunnel, NgrokTunnel, LocalTunnel
    print("  [OK] Tunnel manager")
except Exception as e:
    print(f"  [FAIL] Tunnel manager: {e}")

try:
    from app.files.manager import ProjectManager
    print("  [OK] File manager")
except Exception as e:
    print(f"  [FAIL] File manager: {e}")

try:
    from app.diagnostics.center import DiagnosticsCenter
    print("  [OK] Diagnostics center")
except Exception as e:
    print(f"  [FAIL] Diagnostics center: {e}")

try:
    from app.monitoring.requests import RequestMonitor
    print("  [OK] Request monitor")
except Exception as e:
    print(f"  [FAIL] Request monitor: {e}")

try:
    from app.utils.helpers import which_cloudflared, which_ngrok, which_node, which_php, which_docker
    print("  [OK] Utility helpers")
except Exception as e:
    print(f"  [FAIL] Utility helpers: {e}")

try:
    from app.utils.log_manager import LogManager
    print("  [OK] Log manager")
except Exception as e:
    print(f"  [FAIL] Log manager: {e}")

try:
    from app.core.state.repair import StartupRepair
    print("  [OK] Startup repair")
except Exception as e:
    print(f"  [FAIL] Startup repair: {e}")

try:
    from app.core.state.app_state import AppState
    print("  [OK] App state")
except Exception as e:
    print(f"  [FAIL] App state: {e}")

print("\nAll core module tests completed.")
