from typing import List

from sqlalchemy import Table
from sqlalchemy.engine import Connection

from loaders.abstract_loader import AbstractLoader, Row

Batch = List[Row]


class Merger:
    def __init__(
        self, connection: Connection, table: Table, batch_size: int = 1024
    ) -> None:
        self._connection = connection
        self._table = table
        self._batch_size = batch_size

    def merge(self, loader: AbstractLoader) -> None:
        # TODO: add batching
        ins = self._table.insert()
        for row in loader:
            self._connection.execute(ins, row)
