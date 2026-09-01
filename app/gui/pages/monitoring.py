from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
from app.gui.themes import Theme


class MonitoringPage(QWidget):
    page_name = 'monitoring'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        header = QLabel('Monitoring')
        header.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(header)
        toolbar = QHBoxLayout()
        refresh = QPushButton('Refresh')
        toolbar.addWidget(refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        stats = QHBoxLayout()
        for label in ['Requests: 0', 'Responses: 0', 'Errors: 0', 'Avg: 0ms', 'P95: 0ms', 'P99: 0ms']:
            card = QPushButton(label)
            card.setEnabled(False)
            card.setObjectName('card')
            stats.addWidget(card)
        layout.addLayout(stats)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['TIME', 'METHOD', 'PATH', 'STATUS', 'LATENCY', 'SIZE'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
