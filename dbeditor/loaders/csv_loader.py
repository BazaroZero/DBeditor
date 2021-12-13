from typing import Any, Iterable
from csv import DictReader

from dbeditor.loaders.abstract_loader import AbstractLoader, Row


class CSVLoader(AbstractLoader):
    def __init__(self, fp: Iterable[str], *args: Any, **kwargs: Any) -> None:
        self._reader = DictReader(fp, *args, **kwargs)

    def load_next(self) -> Row:
        return next(self._reader)
