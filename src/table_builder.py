from typing import Optional, Any, Dict

from sqlalchemy import Column, Table, MetaData


class TableBuilder:
    def __init__(self) -> None:
        self._columns: Dict[str, Column] = {}

    def add_column(self, name: str, *args: Any, **kwargs: Any) -> None:
        if name in self._columns:
            raise ValueError("Column with this name already exists.")
        self._columns[name] = Column(name, *args, **kwargs)

    def as_table(
        self, table_name: str, meta: Optional[MetaData] = None
    ) -> Table:
        if meta is None:
            meta = MetaData()
        return Table(table_name, meta, *self._columns.values())
