from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


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


@dataclass
class Netloc:
    username: str
    password: str
    host: str = "localhost"
    port: Optional[Union[str, int]] = None

    def __str__(self) -> str:
        uri = f"{self.username}:{self.password}@{self.host}"
        if self.port:
            uri += f":{self.port}"
        return uri


def build_uri(
    db_kind: DatabaseKind,
    path: str,
    netloc: Optional[Netloc] = None,
    driver: Optional[str] = None,
) -> str:
    if db_kind == DatabaseKind.SQLITE and netloc:
        raise ValueError("SQLite does not supporting remote databases.")

    # TODO: use polymorphism
    proto = _get_protocol(db_kind, driver)
    if netloc is None:
        return f"{proto}:///{path}"
    return f"{proto}://{netloc}/{path}"
