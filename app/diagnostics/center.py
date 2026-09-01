import os
import shutil
import sys
import socket
import threading
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiagnosticResult:
    component: str
    status: str  # PASS, WARNING, FAIL
    details: str


class DiagnosticsCenter:
    def __init__(self):
        self._results: List[DiagnosticResult] = []

    def run_all(self) -> List[DiagnosticResult]:
        self._results = []
        self._check_windows()
        self._check_python()
        self._check_storage()
        self._check_network()
        self._check_cloudflare()
        self._check_ngrok()
        self._check_localtunnel()
        self._check_node()
        self._check_php()
        self._check_docker()
        return self._results

    def _check_windows(self):
        self._results.append(DiagnosticResult('Windows', 'PASS', 'OK'))

    def _check_python(self):
        self._results.append(DiagnosticResult('Python', 'PASS', f'{sys.version}'))

    def _check_storage(self):
        try:
            total, used, free = shutil.disk_usage('/')
            self._results.append(DiagnosticResult('Storage', 'PASS', f'Free: {free // (2**30)} GB'))
        except Exception as exc:
            self._results.append(DiagnosticResult('Storage', 'WARNING', str(exc)))

    def _check_network(self):
        try:
            socket.create_connection(('8.8.8.8', 53), timeout=3)
            self._results.append(DiagnosticResult('Network', 'PASS', 'Internet reachable'))
        except Exception:
            self._results.append(DiagnosticResult('Network', 'FAIL', 'No internet'))

    def _check_cloudflare(self):
        path = shutil.which('cloudflared')
        if path:
            self._results.append(DiagnosticResult('Cloudflare', 'PASS', f'Found: {path}'))
        else:
            self._results.append(DiagnosticResult('Cloudflare', 'WARNING', 'Not installed'))

    def _check_ngrok(self):
        path = shutil.which('ngrok')
        if path:
            self._results.append(DiagnosticResult('ngrok', 'PASS', f'Found: {path}'))
        else:
            self._results.append(DiagnosticResult('ngrok', 'WARNING', 'Not installed'))

    def _check_localtunnel(self):
        path = shutil.which('lt')
        if path:
            self._results.append(DiagnosticResult('LocalTunnel', 'PASS', f'Found: {path}'))
        else:
            self._results.append(DiagnosticResult('LocalTunnel', 'WARNING', 'Not installed'))

    def _check_node(self):
        path = shutil.which('node')
        if path:
            self._results.append(DiagnosticResult('Node.js', 'PASS', f'Found: {path}'))
        else:
            self._results.append(DiagnosticResult('Node.js', 'WARNING', 'Not installed'))

    def _check_php(self):
        path = shutil.which('php')
        if path:
            self._results.append(DiagnosticResult('PHP', 'PASS', f'Found: {path}'))
        else:
            self._results.append(DiagnosticResult('PHP', 'FAIL', 'Not installed'))

    def _check_docker(self):
        path = shutil.which('docker')
        if path:
            self._results.append(DiagnosticResult('Docker', 'PASS', f'Found: {path}'))
        else:
            self._results.append(DiagnosticResult('Docker', 'WARNING', 'Not installed'))
