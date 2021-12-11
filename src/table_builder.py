from typing import Optional, Any, Dict

from sqlalchemy import Column, Table, MetaData


class TableBuilder:
    def __init__(self) -> None:
        self._columns: Dict[str, Column] = {}

    def add_column(
        self, table: str, name: str, *args: Any, **kwargs: Any
    ) -> None:
        if table not in self._columns:
            self._columns[table] = [Column(name, *args, **kwargs)]
        else:
            self._columns[table].append(Column(name, *args, **kwargs))

    def add_table(self, meta: Optional[MetaData] = None):
        if meta is None:
            meta = MetaData()
        for table in self._columns:
            print(self._columns[table])
            Table(table, meta, *self._columns[table])
