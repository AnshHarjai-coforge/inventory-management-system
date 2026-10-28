import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).with_name("inventory.db")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path=None):
    """Open the database with foreign keys on and rows readable by column name."""
    if db_path is None:
        db_path = os.environ.get("INVENTORY_DB")
    if db_path is None:
        db_path = DEFAULT_DB

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # This has to happen on every connection. It is not saved in the file.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    """Create any missing tables. Running this again leaves existing data in place."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
