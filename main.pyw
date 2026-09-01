import sys
from pathlib import Path


def main():
    try:
        from app.core.state.app_state import AppState
        from app.gui.main_window import MainWindow

        state = AppState()
        state.initialize(str(Path(__file__).resolve().parent / 'data'))
        window = MainWindow()
        window.show()
        return window
    except Exception as exc:
        import traceback
        import tkinter.messagebox as mb
        try:
            mb.showerror('NebulaForge', f'Failed to start:\n{exc}\n\n{traceback.format_exc()}')
        except Exception:
            print(f'Failed to start: {exc}')
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
