from typing import Optional

import pytest

from src.uri_builder import _get_protocol, DatabaseKind, build_uri, Netloc


@pytest.mark.parametrize(
    "kind, expected",
    [
        (DatabaseKind.SQLITE, "sqlite"),
        (DatabaseKind.MYSQL, "mysql+pymysql"),
        (DatabaseKind.POSTGRESQL, "postgresql+psycopg2"),
    ],
)
def test_get_protocol(kind: DatabaseKind, expected: str) -> None:
    assert _get_protocol(kind) == expected


def test_get_protocol_sqlite_with_driver() -> None:
    with pytest.raises(ValueError):
        _get_protocol(DatabaseKind.SQLITE, "sqlite")


@pytest.mark.parametrize(
    "kind, path, netloc, expected",
    [
        (DatabaseKind.SQLITE, "", None, "sqlite:///"),
        (DatabaseKind.SQLITE, r"C:\db.sqlite", None, r"sqlite:///C:\db.sqlite"),
        (
            DatabaseKind.SQLITE,
            "/tmp/db.sqlite",
            None,
            "sqlite:////tmp/db.sqlite",
        ),
        (
            DatabaseKind.POSTGRESQL,
            "dir",
            Netloc(username="john", password="doe", host="localhost"),
            "postgresql+psycopg2://john:doe@localhost/dir",
        ),
        (
            DatabaseKind.POSTGRESQL,
            "dir",
            Netloc(username="john", password="doe", host="localhost", port=999),
            "postgresql+psycopg2://john:doe@localhost:999/dir",
        ),
    ],
)
def test_build_url(
    kind: DatabaseKind, path: str, netloc: Optional[Netloc], expected: str
) -> None:
    assert build_uri(kind, path, netloc) == expected


def test_build_uri_sqlite_with_netloc() -> None:
    netloc = Netloc("a", "b", "c")
    with pytest.raises(ValueError):
        build_uri(DatabaseKind.SQLITE, "db.sqlite", netloc)
