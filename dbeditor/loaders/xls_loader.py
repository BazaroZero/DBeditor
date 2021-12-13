from io import StringIO
from typing import Union
from pathlib import Path

from openpyxl import load_workbook

from dbeditor.loaders.abstract_loader import AbstractLoader, Row


ContentOrFilename = Union[str, Path, StringIO]


class XLSLoader(AbstractLoader):
    def __init__(self, file: ContentOrFilename, worksheet: str) -> None:
        self._workbook_iterator = iter(
            load_workbook(file, data_only=True)[worksheet]
        )
        self._header = list(
            map(lambda x: str(x.value), next(self._workbook_iterator))
        )

    def load_next(self) -> Row:
        line = next(self._workbook_iterator)
        kw = zip(self._header, map(lambda x: str(x.value), line))
        return dict(kw)
