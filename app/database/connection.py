import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "verificaciones.db"
)

@contextmanager
def get_cursor():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()