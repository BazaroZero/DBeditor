from src.database import Database
from src.loaders.csv_loader import CSVLoader
from src.loaders.merger import Merger


def test_merge(database: Database, csv_loader: CSVLoader) -> None:
    table = database.get_table("second")
    merger = Merger(table)
    with database.session as s:
        merger.merge(s, csv_loader)
        assert s.query(table).all() == [
            (1, 42, "example"),
            (2, 7, "lorem ipsum"),
        ]
