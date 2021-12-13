from sqlite3 import connect

import pytest

from dbeditor.database import Database
from dbeditor.uri_builder import build_uri, DatabaseKind

_SCRIPT = """
CREATE TABLE first (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

CREATE TABLE second (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INT,
    name TEXT
);

INSERT INTO first(name) VALUES ('lorem'), ('ipsum');
"""


@pytest.fixture
def database() -> Database:
    conn = connect(":memory:")
    conn.executescript(_SCRIPT)
    uri = build_uri(DatabaseKind.SQLITE, "")
    return Database(uri, creator=lambda: conn)
