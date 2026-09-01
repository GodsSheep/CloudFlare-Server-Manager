import sqlite3
from pathlib import Path
from app.database.models import Database

db = Database(str(Path(__file__).resolve().parent.parent.parent / 'data' / 'database' / 'nebulaforge.db'))
