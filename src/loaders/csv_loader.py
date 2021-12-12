from typing import Any
from csv import DictReader

from src.loaders import ContentOrFilename
from src.loaders.abstract_loader import AbstractLoader, Row


class CSVLoader(AbstractLoader):
    def __init__(
        self, fp: ContentOrFilename, *args: Any, **kwargs: Any
    ) -> None:
        self._reader = DictReader(fp, *args, **kwargs)

    def load_next(self) -> Row:
        return next(self._reader)
