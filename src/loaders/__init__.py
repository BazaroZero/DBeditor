from io import StringIO
from os import PathLike
from typing import Union

from sqlalchemy import Table
from sqlalchemy.orm import Session

from src.loaders.abstract_loader import AbstractLoader
from src.loaders.merger import Merger

ContentOrFilename = Union[PathLike, StringIO]


def import_to_table(
    table: Table, session: Session, loader: AbstractLoader
) -> None:
    merger = Merger(table)
    merger.merge(session, loader)

