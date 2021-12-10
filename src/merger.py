from typing import List

from sqlalchemy import Table
from sqlalchemy.orm import Session, sessionmaker

from src.loaders.abstract_loader import AbstractLoader, Row

Batch = List[Row]


class Merger:
    def __init__(
        self, session: sessionmaker, table: Table, batch_size: int = 1024
    ) -> None:
        self._session = session
        self._table = table
        self._batch_size = batch_size

    @property
    def session(self) -> Session:
        return self._session()

    def merge(self, loader: AbstractLoader) -> None:
        # TODO: add batching
        ins = self._table.insert()
        with self.session as session:
            for row in loader:
                session.execute(ins.values(**row))
            session.commit()
