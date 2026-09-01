from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
from app.gui.themes import Theme
from app.diagnostics.center import DiagnosticsCenter, DiagnosticResult


class DiagnosticsWorker(QThread):
    finished = Signal(list)

    def run(self):
        center = DiagnosticsCenter()
        results = center.run_all()
        self.finished.emit(results)


class DiagnosticsPage(QWidget):
    page_name = 'diagnostics'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        header = QLabel('Diagnostics')
        header.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(header)
        toolbar = QHBoxLayout()
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self._run)
        toolbar.addWidget(self.refresh_btn)
        self.test_btn = QPushButton('Test Everything')
        toolbar.addWidget(self.test_btn)
        self.export_btn = QPushButton('Export Report')
        toolbar.addWidget(self.export_btn)
        self.logs_btn = QPushButton('Open Logs')
        toolbar.addWidget(self.logs_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Component', 'Status', 'Details'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self._run()

    def _run(self):
        self.worker = DiagnosticsWorker()
        self.worker.finished.connect(self._populate)
        self.worker.start()

    def _populate(self, results):
        self.table.setRowCount(len(results))
        for i, r in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(r.component))
            status_item = QTableWidgetItem(r.status)
            if r.status == 'PASS':
                status_item.setForeground(Qt.green)
            elif r.status == 'WARNING':
                status_item.setForeground(Qt.yellow)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(i, 1, status_item)
            self.table.setItem(i, 2, QTableWidgetItem(r.details))
