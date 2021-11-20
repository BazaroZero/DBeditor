from typing import Any, Generator, List, Iterable
from csv import reader

from src.loaders.abstract_loader import AbstractLoader


class CSVLoader(AbstractLoader):
    def __init__(self, fp: Iterable[str], *args: Any, **kwargs: Any) -> None:
        self._reader = reader(fp, *args, **kwargs)

    def load_next(self) -> Generator[List[Any], None, None]:
        yield from self._reader
