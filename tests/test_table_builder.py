from sqlalchemy import Integer, String

from src.table_builder import TableBuilder


def test_empty_table():
    tb = TableBuilder()
    assert tb.as_table("example").columns.values() == []


def test_():
    tb = TableBuilder()
    tb.add_column("id", Integer, primary_key=True, autoincrement=True)
    tb.add_column("str", String(16))
    columns = tb.as_table("example").columns.values()
    assert list(map(str, columns)) == [
        "example.id", "example.str"
    ]
