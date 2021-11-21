from io import StringIO
from sqlite3 import connect

import pytest
from sqlalchemy.orm import Session

from src.database import Database
from src.loaders.csv_loader import CSVLoader
from src.merger import Merger

_SCRIPT = """
CREATE TABLE example(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INT,
    text TEXT
);
"""


@pytest.fixture
def db() -> Database:
    conn = connect(":memory:")
    conn.executescript(_SCRIPT)
    return Database("", creator=lambda: conn)


@pytest.fixture
def csv_loader() -> CSVLoader:
    string = StringIO("number,text\n42,example\n7,lorem ipsum")
    return CSVLoader(string)


def test_merge(db: Database, csv_loader: CSVLoader) -> None:
    table = db.get_table("example")
    merger = Merger(db.engine.connect(), table)
    merger.merge(csv_loader)
    with Session(db.engine) as s:
        assert s.query(table).all() == [
            (1, 42, "example"),
            (2, 7, "lorem ipsum"),
        ]
