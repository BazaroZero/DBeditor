from sqlalchemy import Table
from sqlalchemy.orm import Session

from dbeditor.loaders.abstract_loader import AbstractLoader
from dbeditor.loaders.merger import Merger


def import_to_table(
    table: Table, session: Session, loader: AbstractLoader
) -> None:
    merger = Merger(table)
    merger.merge(session, loader)
