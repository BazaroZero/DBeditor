from typing import Optional, Dict, Iterator

from sqlalchemy import Column, Table, MetaData
from sqlalchemy.engine import Engine


class TableBuilder:
    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        self._columns: Dict[str, Column] = {}

    def __len__(self) -> int:
        return len(self._columns)

    def __iter__(self) -> Iterator[str]:
        return map(lambda x: x.name, self._columns.values())  # type: ignore

    def add_column(self, column: Column) -> None:
        """ Adds new column to table.

        :param column: new column to add
        :raises ValueError: if column with this name already exist.
        """
        if column.name in self._columns:
            raise ValueError(f"Column with name '{column.name}' already exist.")
        self._columns[column.name] = column

    def build_table(self, meta: Optional[MetaData] = None) -> Table:
        """ Creates a new table with columns that were added via
        :meth:`~.TableBuilder.add_column`.

        :param meta: metadata context
        :return: new table
        """
        if meta is None:
            meta = MetaData()
        return Table(self._table_name, meta, *self._columns.values())


# TODO: maybe inherit it from ``defaultdict``?
class BuilderGroup:
    """ Group of builder. Used for saving builder between operations. """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._builders: Dict[str, TableBuilder] = {}

    def __contains__(self, table_name: str) -> bool:
        return table_name in self._builders

    def __getitem__(self, table_name: str) -> TableBuilder:
        return self._builders[table_name]

    def __delitem__(self, table_name: str) -> None:
        del self._builders[table_name]

    def start_building(self, table_name: str) -> None:
        """ Creates new builder with ``table_name``. """

        if table_name in self or table_name in self._engine.table_names():
            raise ValueError(f"Table with name '{table_name}' already exist.")

        self._builders[table_name] = TableBuilder(table_name)

    def create_table(self, table_name: str, meta: MetaData) -> None:
        """ Creates table with name ``table_name``. """

        builder = self._builders.pop(table_name)
        builder.build_table(meta)
        meta.create_all(self._engine)
