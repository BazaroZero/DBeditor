from io import StringIO

import pytest
from sqlalchemy.orm import Session

from src.database import Database
from src.loaders.csv_loader import CSVLoader
from src.merger import Merger


@pytest.fixture
def csv_loader() -> CSVLoader:
    string = StringIO("amount,name\n42,example\n7,lorem ipsum")
    return CSVLoader(string)


def test_merge(database: Database, csv_loader: CSVLoader) -> None:
    table = database.get_table("second")
    merger = Merger(database.engine.connect(), table)
    merger.merge(csv_loader)
    with Session(database.engine) as s:
        assert s.query(table).all() == [
            (1, 42, "example"),
            (2, 7, "lorem ipsum"),
        ]
