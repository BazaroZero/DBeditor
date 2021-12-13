from dbeditor.database import Database
from dbeditor.loaders import import_to_table
from dbeditor.loaders.csv_loader import CSVLoader


def test_import_to_table(database: Database, csv_loader: CSVLoader) -> None:
    table = database.get_table("second")
    import_to_table(table, database.session, csv_loader)
    with database.session as s:
        assert s.query(table).all() == [
            (1, 42, "example"),
            (2, 7, "lorem ipsum"),
        ]
