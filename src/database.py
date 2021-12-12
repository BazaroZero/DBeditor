from typing import List, Any, Dict, Tuple

from sqlalchemy import create_engine, MetaData, Table, text, inspect
from sqlalchemy.engine import Engine, Result
from sqlalchemy.engine.result import RMKeyView
from sqlalchemy.orm import sessionmaker, Session


class Database:
    def __init__(self, path: str, *args: Any, **kwargs: Any) -> None:
        self._engine = create_engine(path, *args, **kwargs)
        self._metadata = MetaData()
        self._metadata.reflect(self._engine)
        self._session = sessionmaker(self._engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def metadata(self) -> MetaData:
        return self._metadata

    @property
    def session(self) -> Session:
        return self._session()

    def get_tables(self) -> List[str]:
        user_tables = filter(
            lambda x: x != "sqlite_sequence", self._metadata.tables.keys()
        )
        return list(user_tables)

    def get_table_column_names(self, table_name: str) -> List[str]:
        table: Table = self._metadata.tables[table_name]
        return table.columns.keys()  # type: ignore

    def get_pk_column_names(self, name: str) -> List[str]:
        return [key.name for key in inspect(self.get_table(name)).primary_key]

    def get_table(self, name: str) -> Table:
        return self._metadata.tables[name]

    # TODO: create class for this operations
    def select_all(self, table_name: str) -> List[Any]:
        table = self.get_table(table_name)
        with self.session as session:
            return session.query(table).all()  # type: ignore

    def insert_row(self, table_name: str, row: Dict[str, Any]) -> None:
        table = self.get_table(table_name)
        with self.session as session:
            session.execute(table.insert().values(**row))
            session.commit()

    def delete_row(self, table_name: str, pks: Dict[str, Any]) -> None:
        table = self.get_table(table_name)
        with self.session as session:
            session.query(table).filter_by(**pks).delete()
            session.commit()

    def update_row(
        self, table_name: str, pks: Dict[str, Any], new_values: Dict[str, Any]
    ) -> None:
        table = self.get_table(table_name)
        with self.session as session:
            session.query(table).filter_by(**pks).update(new_values)
            session.commit()

    def execute_raw(
        self, query: str, **kwargs: Any
    ) -> Tuple[RMKeyView, List[Any]]:
        statement = text(query).execution_options(autocommit=True)
        with self.session as session:
            data: Result = session.execute(statement, kwargs)
            return data.keys(), data.fetchall()
