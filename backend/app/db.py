import duckdb
from pathlib import Path
from threading import RLock

from app.config import settings


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = duckdb.connect(str(path))
        self._lock = RLock()
        self._reset_all_tables()

    def _reset_all_tables(self) -> None:
        tables = self._connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_type = 'BASE TABLE'
            """
        ).fetchall()
        for (table_name,) in tables:
            escaped_name = table_name.replace('"', '""')
            self._connection.execute(f'DROP TABLE IF EXISTS "{escaped_name}"')

    def execute(self, query: str, params: tuple | None = None):
        with self._lock:
            if params is None:
                return self._connection.execute(query)
            return self._connection.execute(query, params)


db = Database(settings.database_path)
