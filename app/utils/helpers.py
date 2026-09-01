import shutil
import os
from pathlib import Path
from typing import Optional


def _bundled_bin(name: str) -> Optional[str]:
    base = Path(__file__).resolve().parent.parent.parent / 'bin'
    p = base / name
    if p.exists() and os.access(p, os.X_OK):
        return str(p)
    return None


def which_cloudflared() -> Optional[str]:
    return _bundled_bin('cloudflared') or shutil.which('cloudflared')


def which_ngrok() -> Optional[str]:
    return _bundled_bin('ngrok') or shutil.which('ngrok')


def which_lt() -> Optional[str]:
    return _bundled_bin('lt') or shutil.which('lt')


def which_node() -> Optional[str]:
    return shutil.which('node')


def which_php() -> Optional[str]:
    return shutil.which('php')


def which_docker() -> Optional[str]:
    return shutil.which('docker')


def safe_read_file(path: str, max_bytes: int = 1024 * 1024) -> str:
    try:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return ''
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(max_bytes)
    except Exception:
        return ''


def safe_copy(src: str, dst: str) -> bool:
    try:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False
