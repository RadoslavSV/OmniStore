import sqlite3
from pathlib import Path
from typing import Iterable, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omnistore.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Returns a configured SQLite connection.
    Foreign keys are enabled by default.
    """
    path = db_path or DB_PATH
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    # Enable FK constraints in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def execute_script(conn: sqlite3.Connection, sql: str) -> None:
    conn.executescript(sql)
    conn.commit()


def execute_many(
    conn: sqlite3.Connection,
    sql: str,
    params: Iterable[tuple],
) -> None:
    conn.executemany(sql, params)
    conn.commit()
