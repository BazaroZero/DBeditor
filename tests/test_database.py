from sqlite3 import connect

import pytest

from src.database import Database

_SCRIPT = """
CREATE TABLE first (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

CREATE TABLE second (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data INT,
    date DATE
);
"""


@pytest.fixture
def database() -> Database:
    conn = connect(":memory:")
    conn.executescript(_SCRIPT)
    return Database("", creator=lambda: conn)


def test_get_tables(database: Database) -> None:
    assert database.get_tables() == ["first", "second"]


def test_get_table_column_names(database: Database) -> None:
    assert database.get_table_column_names("first") == ["id", "name"]
