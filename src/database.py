from typing import List, Any
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self, path: str, *args: Any, **kwargs: Any) -> None:
        self._engine = create_engine(f"sqlite:///{path}", *args, **kwargs)
        self._metadata = MetaData()
        self._metadata.reflect(bind=self._engine)
        self._session = sessionmaker(self._engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    def get_tables(self) -> List[str]:
        user_tables = filter(
            lambda x: x != "sqlite_sequence", self._metadata.tables.keys()
        )
        return list(user_tables)

    def get_table_column_names(self, table_name: str) -> List[str]:
        table: Table = self._metadata.tables[table_name]
        return table.columns.keys()  # type: ignore

    def get_table(self, name: str) -> Table:
        return self._metadata.tables[name]

    def execute_raw(self, query: str, **args: Any) -> Any:
        statement = text(query)
        with self.engine.connect() as connection:
            return connection.execute(statement, **args)
