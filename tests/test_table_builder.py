from sqlalchemy import Integer, String, Column

from src.table_builder import TableBuilder


def test_table_builder_with_no_columns() -> None:
    tb = TableBuilder("example")
    assert tb.build_table().columns.values() == []


def test_table_builder_with_columns() -> None:
    tb = TableBuilder("example")
    tb.add_column(Column("id", Integer, primary_key=True, autoincrement=True))
    tb.add_column(Column("str", String(32)))
    columns = tb.build_table().columns.values()
    assert list(map(str, columns)) == ["example.id", "example.str"]
