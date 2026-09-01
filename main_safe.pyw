import sys
import os


def check_dependencies():
    missing = []
    
    try:
        import PySide6
    except ImportError:
        missing.append("PySide6")
    
    try:
        import psutil
    except ImportError:
        missing.append("psutil")
    
    try:
        import watchdog
    except ImportError:
        missing.append("watchdog")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    try:
        import aiohttp
    except ImportError:
        missing.append("aiohttp")
    
    try:
        import cryptography
    except ImportError:
        missing.append("cryptography")
    
    try:
        import packaging
    except ImportError:
        missing.append("packaging")
    
    return missing


def main():
    missing = check_dependencies()
    if missing:
        print("=" * 60)
        print("  NebulaForge X300 - Missing Dependencies")
        print("=" * 60)
        print()
        print("The following required packages are missing:")
        for pkg in missing:
            print(f"  - {pkg}")
        print()
        print("To install them, run:")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
        print()
        print("Or install individually:")
        print(f"  {sys.executable} -m pip install PySide6 psutil watchdog requests aiohttp cryptography packaging")
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    
    from app.core.state.app_state import AppState
    from app.gui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    state = AppState()
    state.initialize(str(os.path.dirname(os.path.abspath(__file__)) / 'data'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
