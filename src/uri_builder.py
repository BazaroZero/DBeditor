from enum import Enum
from typing import Optional


class DatabaseKind(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


_DRIVER = {
    DatabaseKind.SQLITE: None,
    DatabaseKind.MYSQL: "pymysql",
    DatabaseKind.POSTGRESQL: "psycopg2",
}


def _get_protocol(db_kind: DatabaseKind, driver: Optional[str] = None) -> str:
    if db_kind == DatabaseKind.SQLITE and driver:
        raise ValueError("Sqlite does not support any drivers.")

    if driver is None:
        driver = _DRIVER.get(db_kind)

    if driver:
        return f"{db_kind.value}+{driver}"
    return db_kind.value


def build_uri(
    db_kind: DatabaseKind,
    path: str,
    netloc: str = "",
    driver: Optional[str] = None,
) -> str:
    if db_kind == DatabaseKind.SQLITE and netloc:
        raise ValueError("SQLite does not supporting remote databases.")

    proto = _get_protocol(db_kind, driver)
    return f"{proto}://{netloc}/{path}"
