from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.gui.main_window import MainWindow
import sys


def main():
    app = QApplication(sys.argv)
    font = QFont('Segoe UI', 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
