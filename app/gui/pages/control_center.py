from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt
from app.gui.themes import Theme


class ControlCenterPage(QWidget):
    page_name = 'control'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel('Control Center')
        header.setStyleSheet('font-size: 28px; font-weight: bold; color: #ffffff;')
        layout.addWidget(header)

        stats = QGridLayout()
        stats.setSpacing(12)
        for i, (title, value) in enumerate([('Servers', '4'), ('Projects', '12'), ('Tunnels', '8'), ('Processes', '17')]):
            card = QFrame()
            card.setObjectName('card')
            l = QVBoxLayout(card)
            l.setContentsMargins(16, 16, 16, 16)
            t = QLabel(title)
            t.setStyleSheet('color: #888888; font-size: 12px;')
            v = QLabel(value)
            v.setStyleSheet('font-size: 24px; font-weight: bold; color: #ffffff;')
            l.addWidget(t)
            l.addWidget(v)
            stats.addWidget(card, 0, i)
        layout.addLayout(stats)

        quick = QFrame()
        quick.setObjectName('card')
        ql = QVBoxLayout(quick)
        ql.setContentsMargins(16, 16, 16, 16)
        ql.addWidget(QLabel('Quick Actions'))
        actions = QHBoxLayout()
        for text in ['+ Project', 'Import', '+ Server', '+ Tunnel']:
            btn = QPushButton(text)
            btn.setObjectName('primary')
            actions.addWidget(btn)
        ql.addLayout(actions)
        layout.addWidget(quick)

        system = QFrame()
        system.setObjectName('card')
        sl = QVBoxLayout(system)
        sl.setContentsMargins(16, 16, 16, 16)
        sl.addWidget(QLabel('System'))
        grid = QGridLayout()
        for i, (label, value) in enumerate([('CPU', '21%'), ('RAM', '42%'), ('Disk', '34%'), ('Network', '18 Mbps'), ('Uptime', '04:21:17')]):
            l = QLabel(label)
            l.setStyleSheet('color: #888888;')
            v = QLabel(value)
            v.setStyleSheet('font-weight: bold;')
            grid.addWidget(l, i // 3, (i % 3) * 2)
            grid.addWidget(v, i // 3, (i % 3) * 2 + 1)
        sl.addLayout(grid)
        layout.addWidget(system)
        layout.addStretch()
