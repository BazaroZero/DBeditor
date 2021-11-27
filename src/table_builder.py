from typing import Optional

from sqlalchemy import Column, Table, MetaData


class TableBuilder:
    def __init__(self):
        self._columns = {}

    def add_column(self, name: str, *args, **kwargs) -> None:
        if name in self._columns:
            raise ValueError("Column with this name already exists.")
        self._columns[name] = Column(name, *args, **kwargs)

    def as_table(self, table_name: str, meta: Optional[MetaData] = None) -> Table:
        if meta is None:
            meta = MetaData()
        return Table(table_name, meta, *self._columns.values())
