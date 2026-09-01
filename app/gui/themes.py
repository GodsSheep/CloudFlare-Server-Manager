class Theme:
    @staticmethod
    def get_stylesheet(mode: str) -> str:
        if mode == 'dark':
            return '''
            QMainWindow { background: #1e1e1e; }
            QFrame#sidebar { background: #252525; border-right: 1px solid #333; }
            QLabel#logo { color: #ffffff; font-size: 18px; font-weight: bold; padding: 4px 8px; }
            QPushButton#navButton {
                background: transparent; border: none; color: #cccccc;
                padding: 10px 16px; text-align: left; font-size: 13px; border-radius: 6px;
            }
            QPushButton#navButton:hover { background: #333333; color: #ffffff; }
            QPushButton#navButton:checked { background: #2d2d2d; color: #4da6ff; font-weight: 600; }
            QLabel#statusLabel { color: #4caf50; font-size: 11px; padding: 4px 8px; }
            QWidget#page { background: #1e1e1e; color: #e0e0e0; }
            QPushButton {
                background: #333333; color: #e0e0e0; border: 1px solid #444;
                padding: 8px 16px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #404040; }
            QPushButton:pressed { background: #4da6ff; color: #000; }
            QPushButton#primary { background: #4da6ff; color: #000; font-weight: 600; border: none; }
            QPushButton#primary:hover { background: #66b8ff; }
            QFrame#card {
                background: #252525; border: 1px solid #333; border-radius: 10px;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background: #2d2d2d; color: #e0e0e0; border: 1px solid #444;
                padding: 6px 10px; border-radius: 6px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QHeaderView::section { background: #2d2d2d; color: #e0e0e0; padding: 6px; border: 1px solid #333; }
            QTableWidget { background: #252525; color: #e0e0e0; gridline-color: #333; border: none; }
            QTableWidget::item { padding: 6px; }
            QProgressBar { background: #2d2d2d; border: 1px solid #444; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: #4da6ff; border-radius: 4px; }
            QStatusBar { background: #252525; color: #aaaaaa; }
            QScrollBar:vertical { background: #2d2d2d; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #555; border-radius: 5px; }
            '''
        return '''
            QMainWindow { background: #f5f5f5; }
            QFrame#sidebar { background: #ffffff; border-right: 1px solid #e0e0e0; }
            QLabel#logo { color: #1a1a1a; font-size: 18px; font-weight: bold; padding: 4px 8px; }
            QPushButton#navButton {
                background: transparent; border: none; color: #555555;
                padding: 10px 16px; text-align: left; font-size: 13px; border-radius: 6px;
            }
            QPushButton#navButton:hover { background: #f0f0f0; color: #1a1a1a; }
            QPushButton#navButton:checked { background: #e8f0fe; color: #1a73e8; font-weight: 600; }
            QLabel#statusLabel { color: #34a853; font-size: 11px; padding: 4px 8px; }
            QWidget#page { background: #f5f5f5; color: #1a1a1a; }
            QPushButton {
                background: #ffffff; color: #1a1a1a; border: 1px solid #dadce0;
                padding: 8px 16px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #f1f3f4; }
            QPushButton:pressed { background: #e8f0fe; color: #1a73e8; }
            QPushButton#primary { background: #1a73e8; color: #ffffff; font-weight: 600; border: none; }
            QPushButton#primary:hover { background: #1557b0; }
            QFrame#card {
                background: #ffffff; border: 1px solid #e0e0e0; border-radius: 10px;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background: #ffffff; color: #1a1a1a; border: 1px solid #dadce0;
                padding: 6px 10px; border-radius: 6px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QHeaderView::section { background: #f8f9fa; color: #1a1a1a; padding: 6px; border: 1px solid #e0e0e0; }
            QTableWidget { background: #ffffff; color: #1a1a1a; gridline-color: #e0e0e0; border: none; }
            QTableWidget::item { padding: 6px; }
            QProgressBar { background: #f1f3f4; border: 1px solid #dadce0; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: #1a73e8; border-radius: 4px; }
            QStatusBar { background: #ffffff; color: #5f6368; }
            QScrollBar:vertical { background: #f1f3f4; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #dadce0; border-radius: 5px; }
            '''
