import logging
from typing import Optional
from datetime import datetime

from app.database.models import Database


class LogManager:
    def __init__(self, db: Database):
        self._db = db
        self._logger = logging.getLogger('nebulaforge')
        self._logger.setLevel(logging.DEBUG)
        self._setup_file_handler()

    def _setup_file_handler(self):
        import os
        log_path = os.path.join(os.path.dirname(self._db._path), '..', 'logs', 'app.log')
        log_path = os.path.abspath(log_path)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def info(self, message: str, meta: Optional[str] = None):
        self._logger.info(message)
        self._store('info', message, meta)

    def warning(self, message: str, meta: Optional[str] = None):
        self._logger.warning(message)
        self._store('warning', message, meta)

    def error(self, message: str, meta: Optional[str] = None):
        self._logger.error(message)
        self._store('error', message, meta)

    def _store(self, level: str, message: str, meta: Optional[str]):
        try:
            self._db.execute(
                'INSERT INTO logs (category, level, message, meta, created_at) VALUES (?, ?, ?, ?, ?)',
                ('application', level, message, meta, datetime.now().isoformat())
            )
            self._db.commit()
        except Exception:
            pass
