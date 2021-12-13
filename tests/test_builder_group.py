import pytest
from sqlalchemy import Column, Integer

from dbeditor.database import Database
from dbeditor.table_builder import BuilderGroup


@pytest.fixture
def group(database: Database) -> BuilderGroup:
    g = BuilderGroup(database.engine)
    g.start_building("example")  # FIXME: fixture based on testing code
    c = Column("id", Integer, primary_key=True, autoincrement=True)
    g["example"].add_column(c)
    return g


@pytest.mark.parametrize(
    "table_name, expected", [("example", True), ("Lorem", False)]
)
def test_builder_group_contains(
    group: BuilderGroup, table_name: str, expected: bool
) -> None:
    assert (table_name in group) == expected


def test_builder_group_getitem(group: BuilderGroup) -> None:
    assert group["example"] == group._builders["example"]
    with pytest.raises(KeyError):
        _ = group["item"]


# FIXME: depends on contains
def test_builder_group_delitem(group: BuilderGroup) -> None:
    del group["example"]
    assert "example" not in group


def test_builder_group_len(group: BuilderGroup) -> None:
    assert len(group) == 1


# FIXME: depends on contains
def test_builder_group_start_building(group: BuilderGroup) -> None:
    assert "new_table" not in group
    group.start_building("new_table")
    assert "new_table" in group
    assert list(group["new_table"]) == []


def test_builder_group_start_building_on_existing_table(
    group: BuilderGroup,
) -> None:
    assert "new_table" not in group
    group.start_building("new_table")
    assert "new_table" in group
    with pytest.raises(ValueError):
        group.start_building("new_table")


# FIXME: depends on contains
def test_builder_group_create_table(
    group: BuilderGroup, database: Database
) -> None:
    group.create_table("example", database.metadata)
    assert database.get_tables() == ["first", "second", "example"]
