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

INSERT INTO first(name) VALUES ('lorem'), ('ipsum');
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


def test_raw_execute(database: Database) -> None:
    result = database.execute_raw("select name from first where id = :id", id=2)
    assert list(result) == [("ipsum",)]
