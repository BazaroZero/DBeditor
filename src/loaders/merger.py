from typing import List

from sqlalchemy import Table
from sqlalchemy.orm import Session

from src.loaders.abstract_loader import AbstractLoader, Row

Batch = List[Row]


class Merger:
    def __init__(self, table: Table, batch_size: int = 1024) -> None:
        self._table = table
        self._batch_size = batch_size

    def merge(self, session: Session, loader: AbstractLoader) -> None:
        # TODO: add batching
        ins = self._table.insert()
        for row in loader:
            session.execute(ins.values(**row))
        session.commit()
