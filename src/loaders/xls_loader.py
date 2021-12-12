from openpyxl import load_workbook

from src.loaders import ContentOrFilename
from src.loaders.abstract_loader import AbstractLoader, Row


class XLSLoader(AbstractLoader):
    def __init__(self, file: ContentOrFilename, worksheet: str) -> None:
        self._workbook_iterator = iter(load_workbook(file)[worksheet])
        self._header = list(
            map(lambda x: str(x.value), next(self._workbook_iterator))
        )

    def load_next(self) -> Row:
        line = next(self._workbook_iterator)
        kw = zip(self._header, map(lambda x: str(x.value), line))
        return dict(kw)
