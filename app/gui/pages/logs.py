from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QComboBox, QHBoxLayout
from app.gui.themes import Theme


class LogsPage(QWidget):
    page_name = 'logs'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        header = QLabel('Logs')
        header.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(header)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('Server:'))
        self.server = QComboBox()
        toolbar.addWidget(self.server)
        refresh = QPushButton('Refresh')
        toolbar.addWidget(refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        filters = QHBoxLayout()
        for label in ['All', 'Info', 'Warning', 'Error', 'Crash', 'Tunnel', 'Request', 'Deployment', 'System']:
            btn = QPushButton(label)
            btn.setCheckable(True)
            filters.addWidget(btn)
        layout.addLayout(filters)
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        layout.addWidget(self.viewer)
        actions = QHBoxLayout()
        for text in ['Copy', 'Save', 'Clear View', 'Open Folder']:
            actions.addWidget(QPushButton(text))
        layout.addLayout(actions)
