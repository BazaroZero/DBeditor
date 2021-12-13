import pytest
from sqlalchemy import Integer, String, Column

from dbeditor.database import Database
from dbeditor.table_builder import TableBuilder


@pytest.fixture
def builder() -> TableBuilder:
    tb = TableBuilder("example")
    for index in range(3):
        tb.add_column(Column(f"c{index}", String(32)))
    return tb


def test_table_builder_with_no_columns() -> None:
    tb = TableBuilder("example")
    assert tb.build_table().columns.values() == []


def test_table_builder_with_columns() -> None:
    tb = TableBuilder("example")
    tb.add_column(Column("id", Integer, primary_key=True, autoincrement=True))
    tb.add_column(Column("str", String(32)))
    columns = tb.build_table().columns.values()
    assert list(map(str, columns)) == ["example.id", "example.str"]


# TODO: depend on get_tables
def test_table_builder_with_meta(
    builder: TableBuilder, database: Database
) -> None:
    meta = database.metadata
    builder.build_table(meta)
    assert database.get_tables() == ["first", "second", "example"]


def test_table_builder_add_column_exception() -> None:
    tb = TableBuilder("example")
    tb.add_column(Column("str", String(32)))
    with pytest.raises(ValueError):
        tb.add_column(Column("str", String(32)))


def test_table_builder_len(builder: TableBuilder) -> None:
    assert len(builder) == 3


def test_table_builder_iter(builder: TableBuilder) -> None:
    assert list(builder) == ["c0", "c1", "c2"]
