from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.gui.themes import Theme


class NetworkPage(QWidget):
    page_name = 'network'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        header = QLabel('Network')
        header.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(header)
