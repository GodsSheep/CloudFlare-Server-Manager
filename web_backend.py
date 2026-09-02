#!/usr/bin/env python3
"""
NebulaForge X300 - Web Control Center Backend
Serves the web interface and provides API endpoints for project/tunnel management.
"""

import os
import sys
import json
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.state.machine import ProjectState, ProcessState, TunnelState, DesiredState
from app.database.models import Database
from app.runtime.manager import RuntimeManager
from app.server.port import PortManager
from app.files.manager import ProjectManager
from app.tunnels.manager import TunnelManager
from app.core.events.bus import EventBus
from app.core.jobs.manager import JobManager
from app.core.state.app_state import AppState
from app.diagnostics.center import DiagnosticsCenter
from app.monitoring.requests import RequestMonitor


class NebulaForgeHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for NebulaForge Web Control Center"""

    def __init__(self, *args, web_app=None, **kwargs):
        self.web_app = web_app
        super().__init__(*args, directory=str(Path(__file__).resolve().parent / 'web'), **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API routes
        if path.startswith('/api/'):
            self.handle_api_get(path, parsed.query)
        # File download
        elif path.startswith('/api/files/download'):
            self.handle_file_download(parse_qs(parsed.query))
        else:
            # Serve static files from web/ directory
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}
            self.handle_api_post(path, data)
        else:
            self.send_error(404)

    def handle_api_get(self, path, query):
        params = parse_qs(query)
        app = self.web_app

        try:
            if path == '/api/stats':
                self.json_response(app.get_stats())
            elif path == '/api/projects':
                self.json_response(app.get_projects())
            elif path.startswith('/api/projects/'):
                parts = path.split('/')
                if len(parts) >= 4 and parts[3] == 'start':
                    self.json_response(app.start_project(parts[2]))
                elif len(parts) >= 4 and parts[3] == 'stop':
                    self.json_response(app.stop_project(parts[2]))
                elif len(parts) >= 4 and parts[3] == 'restart':
                    self.json_response(app.restart_project(parts[2]))
                else:
                    self.json_response(app.get_project(parts[2]))
            elif path == '/api/files':
                self.json_response(app.get_files())
            elif path == '/api/tunnels':
                self.json_response(app.get_tunnels())
            elif path.startswith('/api/tunnels/') and path.endswith('/stop'):
                tunnel_id = path.split('/')[3]
                self.json_response(app.stop_tunnel(tunnel_id))
            elif path == '/api/diagnostics':
                self.json_response(app.get_diagnostics())
            elif path == '/api/settings':
                self.json_response(app.get_settings())
            else:
                self.json_response({'error': 'Not found'}, 404)
        except Exception as e:
            self.json_response({'error': str(e)}, 500)

    def handle_api_post(self, path, data):
        app = self.web_app

        try:
            if path == '/api/projects':
                self.json_response(app.create_project(data))
            elif path == '/api/projects/import':
                self.json_response(app.import_project(data))
            elif path == '/api/tunnels':
                self.json_response(app.create_tunnel(data))
            elif path == '/api/settings':
                self.json_response(app.save_settings(data))
            else:
                self.json_response({'error': 'Not found'}, 404)
        except Exception as e:
            self.json_response({'error': str(e)}, 500)

    def handle_file_download(self, params):
        file_path = params.get('path', [''])[0]
        if not file_path or not os.path.exists(file_path):
            self.send_error(404, 'File not found')
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
        self.send_header('Content-Length', str(os.path.getsize(file_path)))
        self.end_headers()
        
        with open(file_path, 'rb') as f:
            shutil.copyfileobj(f, self.wfile)

    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


class NebulaForgeWebApp:
    """Web application backend integrating with NebulaForge core"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize core components
        self.db = Database(str(self.data_dir / 'database' / 'nebulaforge.db'))
        self.events = EventBus()
        self.jobs = JobManager()
        self.runtime = RuntimeManager()
        self.port_mgr = PortManager()
        self.projects = ProjectManager(self.db, self.runtime, self.port_mgr, self.jobs, self.events)
        self.tunnels = TunnelManager(self.db, self.events)
        self.monitor = RequestMonitor()
        self.diagnostics = DiagnosticsCenter()
        
        # Active tunnel processes
        self._tunnel_procs: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()

    def get_stats(self) -> Dict[str, Any]:
        projects = self.projects.list_projects()
        tunnels = self.db.fetchall("SELECT * FROM tunnels WHERE status = 'CONNECTED'")
        
        return {
            'servers': 1,
            'projects': len(projects),
            'tunnels': len(tunnels),
            'processes': len([p for p in projects if p.status == 'ONLINE'])
        }

    def get_projects(self) -> List[Dict[str, Any]]:
        projects = self.projects.list_projects()
        return [self._project_to_dict(p) for p in projects]

    def get_project(self, project_id: str) -> Dict[str, Any]:
        project = self.projects.get_project(project_id)
        return self._project_to_dict(project) if project else {'error': 'Not found'}

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        name = data.get('name', 'Untitled Project')
        runtime = data.get('runtime', 'static')
        source = data.get('source', '')
        
        if source and os.path.exists(source):
            project = self.projects.create_project(name, source, runtime)
        else:
            # Create empty project
            project_id = str(uuid.uuid4())
            port = self.port_mgr.suggest_available()[0] if self.port_mgr.suggest_available() else 8080
            now = datetime.now().isoformat()
            self.db.execute(
                'INSERT INTO projects (id, name, source_path, project_path, runtime, host, port, status, desired_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (project_id, name, '', '', runtime, '127.0.0.1', port, ProjectState.READY.value, DesiredState.STOPPED.value, now, now)
            )
            self.db.commit()
            project = self.projects.get_project(project_id)
        
        return self._project_to_dict(project) if project else {'error': 'Failed to create project'}

    def import_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        path = data.get('path', '')
        if not path or not os.path.exists(path):
            return {'error': 'Invalid path'}
        
        name = os.path.basename(path)
        project = self.projects.create_project(name, path)
        return self._project_to_dict(project) if project else {'error': 'Import failed'}

    def start_project(self, project_id: str) -> Dict[str, Any]:
        success, error = self.projects.start_project(project_id)
        if success:
            project = self.projects.get_project(project_id)
            return self._project_to_dict(project)
        return {'error': error or 'Failed to start project'}

    def stop_project(self, project_id: str) -> Dict[str, Any]:
        success = self.projects.stop_project(project_id)
        if success:
            project = self.projects.get_project(project_id)
            return self._project_to_dict(project)
        return {'error': 'Failed to stop project'}

    def restart_project(self, project_id: str) -> Dict[str, Any]:
        success, error = self.projects.restart_project(project_id)
        if success:
            project = self.projects.get_project(project_id)
            return self._project_to_dict(project)
        return {'error': error or 'Failed to restart project'}

    def get_tunnels(self) -> List[Dict[str, Any]]:
        tunnels = self.db.fetchall("SELECT * FROM tunnels ORDER BY created_at DESC")
        result = []
        for t in tunnels:
            tunnel_dict = dict(t)
            # Check if process is still running
            if tunnel_dict.get('pid'):
                try:
                    os.kill(tunnel_dict['pid'], 0)
                    tunnel_dict['status'] = TunnelState.CONNECTED.value
                except (ProcessLookupError, PermissionError):
                    tunnel_dict['status'] = TunnelState.DISABLED.value
            result.append(tunnel_dict)
        return result

    def create_tunnel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        provider = data.get('provider', 'cloudflare')
        project_id = data.get('project_id')
        local_port = 8080
        
        if project_id:
            project = self.projects.get_project(project_id)
            if project:
                local_port = project.port
        
        # Start tunnel in background
        success, error, public_url = self._start_tunnel_process(provider, local_port)
        if success:
            return {
                'id': str(uuid.uuid4()),
                'provider': provider,
                'status': 'CONNECTING',
                'public_url': public_url,
                'local_port': local_port
            }
        return {'error': error or 'Failed to start tunnel'}

    def stop_tunnel(self, tunnel_id: str) -> Dict[str, Any]:
        with self._lock:
            proc = self._tunnel_procs.pop(tunnel_id, None)
        
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        
        self.db.execute("UPDATE tunnels SET status = 'DISABLED' WHERE id = ?", (tunnel_id,))
        self.db.commit()
        return {'success': True}

    def _start_tunnel_process(self, provider: str, local_port: int) -> tuple[bool, Optional[str], Optional[str]]:
        """Start a tunnel process and return (success, error, public_url)"""
        try:
            if provider == 'cloudflare':
                binary = self._find_binary('cloudflared')
                if not binary:
                    return False, 'cloudflared not found', None
                cmd = [binary, 'tunnel', '--url', f'http://127.0.0.1:{local_port}']
            elif provider == 'ngrok':
                binary = self._find_binary('ngrok')
                if not binary:
                    return False, 'ngrok not found', None
                cmd = [binary, 'http', str(local_port)]
            elif provider == 'localtunnel':
                lt_bin = self._find_binary('lt')
                if not lt_bin:
                    # Try node
                    node = self._find_binary('node')
                    lt_js = Path(__file__).resolve().parent.parent / 'bin' / 'localtunnel' / 'node_modules' / 'localtunnel' / 'bin' / 'lt.js'
                    if lt_js.exists():
                        cmd = [node, str(lt_js), '--port', str(local_port)]
                    else:
                        return False, 'localtunnel not found', None
                else:
                    cmd = [lt_bin, '--port', str(local_port)]
            else:
                return False, f'Unknown provider: {provider}', None

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
            
            # Store process
            tunnel_id = str(uuid.uuid4())
            with self._lock:
                self._tunnel_procs[tunnel_id] = proc
            
            # Wait for URL
            public_url = self._extract_url(proc, provider)
            if public_url:
                self.db.execute(
                    'INSERT INTO tunnels (id, provider, status, public_url, local_port, pid, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (tunnel_id, provider, TunnelState.CONNECTED.value, public_url, local_port, proc.pid, datetime.now().isoformat(), datetime.now().isoformat())
                )
                self.db.commit()
                return True, None, public_url
            else:
                return False, 'Failed to get tunnel URL', None
                
        except Exception as e:
            return False, str(e), None

    def _find_binary(self, name: str) -> Optional[str]:
        """Find binary in bundled bin/ or system PATH"""
        bundled = Path(__file__).resolve().parent.parent / 'bin' / name
        if bundled.exists() and os.access(bundled, os.X_OK):
            return str(bundled)
        return shutil.which(name)

    def _extract_url(self, proc: subprocess.Popen, provider: str) -> Optional[str]:
        """Extract public URL from tunnel process output"""
        import re
        
        patterns = {
            'cloudflare': r'https://[a-zA-Z0-9-]+\.trycloudflare\.com',
            'ngrok': r'https://[a-zA-Z0-9-]+\.ngrok(-free)?\.(io|app)',
            'localtunnel': r'https://[a-zA-Z0-9-]+\.loca\.lt'
        }
        
        pattern = patterns.get(provider, r'https://[^\s]+')
        
        # Read from stderr/stdout for a few seconds
        for _ in range(20):
            line = proc.stderr.readline() or proc.stdout.readline()
            if not line:
                time.sleep(0.5)
                continue
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        return None

    def get_files(self) -> List[Dict[str, Any]]:
        files = []
        projects = self.projects.list_projects()
        
        for project in projects[:5]:  # Limit to first 5 projects
            if project.project_path and os.path.exists(project.project_path):
                try:
                    for item in os.listdir(project.project_path)[:20]:
                        item_path = os.path.join(project.project_path, item)
                        stat = os.stat(item_path)
                        files.append({
                            'name': item,
                            'path': item_path,
                            'type': 'directory' if os.path.isdir(item_path) else 'file',
                            'size': self._format_size(stat.st_size) if os.path.isfile(item_path) else '-',
                            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                        })
                except Exception:
                    pass
        
        return files

    def get_diagnostics(self) -> List[Dict[str, Any]]:
        center = DiagnosticsCenter()
        results = center.run_all()
        return [{'component': r.component, 'status': r.status, 'details': r.details} for r in results]

    def get_settings(self) -> Dict[str, Any]:
        return {
            'theme': 'dark',
            'host': '127.0.0.1',
            'port': 8080,
            'provider': 'cloudflare',
            'autostart': True
        }

    def save_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Save settings to database or config file
        for key, value in data.items():
            self.db.execute(
                'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)',
                (key, json.dumps(value), datetime.now().isoformat())
            )
        self.db.commit()
        return {'success': True}

    def _project_to_dict(self, project) -> Dict[str, Any]:
        if not project:
            return {}
        return {
            'id': project.id,
            'name': project.name,
            'runtime': project.runtime,
            'host': project.host,
            'port': project.port,
            'status': project.status,
            'public_url': project.public_url or None
        }

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class WebServer:
    """HTTP server for NebulaForge Web Control Center"""

    def __init__(self, host: str = '0.0.0.0', port: int = 8080, data_dir: str = None):
        self.host = host
        self.port = port
        self.data_dir = data_dir or str(Path(__file__).resolve().parent / 'data')
        self.app = NebulaForgeWebApp(self.data_dir)
        self.server: Optional[HTTPServer] = None

    def start(self):
        handler = lambda *args, **kwargs: NebulaForgeHandler(*args, web_app=self.app, **kwargs)
        self.server = HTTPServer((self.host, self.port), handler)
        print(f"Web server running at http://{self.host}:{self.port}")
        print(f"Web Control Center: http://127.0.0.1:{self.port}/")
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='NebulaForge Web Control Center')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--data-dir', help='Data directory')
    args = parser.parse_args()

    server = WebServer(args.host, args.port, args.data_dir)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()


if __name__ == '__main__':
    main()
