from sqlalchemy.exc import IntegrityError

import pytest

from src.database import Database


def test_get_tables(database: Database) -> None:
    assert database.get_tables() == ["first", "second"]


def test_get_table_column_names(database: Database) -> None:
    assert database.get_table_column_names("first") == ["id", "name"]


def test_get_select_all(database: Database) -> None:
    assert database.select_all("first") == [(1, "lorem"), (2, "ipsum")]


def test_insert_row(database: Database) -> None:
    database.insert_row("first", {"name": "hello"})
    assert database.select_all("first") == [
        (1, "lorem"),
        (2, "ipsum"),
        (3, "hello"),
    ]


def test_delete_row(database: Database) -> None:
    database.delete_row("first", {"id": 1})
    assert database.select_all("first") == [(2, "ipsum")]


def test_update_row(database: Database) -> None:
    database.update_row("first", {"id": 1}, {"name": "test"})
    assert database.select_all("first") == [(1, "test"), (2, "ipsum")]


def test_update_row_exception(database: Database) -> None:
    with pytest.raises(IntegrityError):
        database.update_row("first", {"id": 1}, {"id": 2})


def test_get_pk_column_names(database: Database) -> None:
    assert database.get_pk_column_names("first") == ["id"]


def test_raw_execute_select(database: Database) -> None:
    result = database.execute_raw("SELECT name FROM first WHERE id = :id", id=2)
    assert result is not None
    keys, data = result
    assert list(data) == [("ipsum",)]
    assert keys == ["name"]


def test_raw_execute_update(database: Database) -> None:
    database.execute_raw(
        "UPDATE first SET name = :name WHERE id = :id", name="hello", id=2
    )
    assert database.select_all("first") == [
        (1, "lorem"),
        (2, "hello"),
    ]
