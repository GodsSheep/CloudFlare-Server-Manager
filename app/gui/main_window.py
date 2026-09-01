import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel, QPushButton, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from app.core.state.app_state import AppState
from app.gui.themes import Theme
from app.gui.pages.control_center import ControlCenterPage
from app.gui.pages.projects import ProjectsPage
from app.gui.pages.files import FilesPage
from app.gui.pages.servers import ServersPage
from app.gui.pages.tunnels import TunnelsPage
from app.gui.pages.processes import ProcessesPage
from app.gui.pages.deployments import DeploymentsPage
from app.gui.pages.monitoring import MonitoringPage
from app.gui.pages.logs import LogsPage
from app.gui.pages.network import NetworkPage
from app.gui.pages.diagnostics import DiagnosticsPage
from app.gui.pages.settings import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.setWindowTitle('NebulaForge Server Manager')
        self.setMinimumSize(1280, 800)
        self.setup_ui()
        self.apply_theme('dark')

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = self._build_sidebar()
        layout.addWidget(sidebar, stretch=0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, stretch=1)

        self.pages = {
            'control': ControlCenterPage,
            'projects': ProjectsPage,
            'files': FilesPage,
            'servers': ServersPage,
            'tunnels': TunnelsPage,
            'processes': ProcessesPage,
            'deployments': DeploymentsPage,
            'monitoring': MonitoringPage,
            'logs': LogsPage,
            'network': NetworkPage,
            'diagnostics': DiagnosticsPage,
            'settings': SettingsPage,
        }
        for key, page_cls in self.pages.items():
            page = page_cls(self.state)
            self.stack.addWidget(page)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage('System Online')

    def _build_sidebar(self) -> QWidget:
        container = QFrame()
        container.setFixedWidth(220)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(4)

        logo = QLabel('NebulaForge')
        logo.setObjectName('logo')
        layout.addWidget(logo)
        layout.addSpacing(16)

        items = [
            ('control', '⌂', 'Control Center'),
            ('projects', '▣', 'Live Projects'),
            ('files', '▤', 'Files'),
            ('servers', '◈', 'Servers'),
            ('tunnels', '☁', 'Tunnels'),
            ('processes', '⚡', 'Processes'),
            ('deployments', '▥', 'Deployments'),
            ('monitoring', '◉', 'Monitoring'),
            ('logs', '▤', 'Logs'),
            ('network', '⌁', 'Network'),
            ('diagnostics', '⌘', 'Diagnostics'),
            ('settings', '⚙', 'Settings'),
        ]

        self._nav_buttons = {}
        for key, icon, label in items:
            btn = QPushButton(f'{icon}  {label}')
            btn.setObjectName('navButton')
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            layout.addWidget(btn)
            self._nav_buttons[key] = btn

        layout.addStretch()
        status = QLabel('● SYSTEM ONLINE')
        status.setObjectName('statusLabel')
        layout.addWidget(status)
        return container

    def _navigate(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)
        idx = list(self.pages.keys()).index(key)
        self.stack.setCurrentIndex(idx)

    def apply_theme(self, name: str):
        palette = self.palette()
        if name == 'dark':
            palette.setColor(QPalette.Window, QColor(30, 30, 30))
            palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
            palette.setColor(QPalette.Base, QColor(24, 24, 24))
            palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
            palette.setColor(QPalette.Text, QColor(220, 220, 220))
            palette.setColor(QPalette.Button, QColor(45, 45, 45))
            palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        else:
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, QColor(20, 20, 20))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.Text, QColor(20, 20, 20))
            palette.setColor(QPalette.Button, QColor(230, 230, 230))
            palette.setColor(QPalette.ButtonText, QColor(20, 20, 20))
            palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setStyleSheet(Theme.get_stylesheet(name))
