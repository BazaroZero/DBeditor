from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator

Row = Dict[str, Any]


class AbstractLoader(ABC, Iterator[Row]):
    @abstractmethod
    def load_next(self) -> Row:
        pass

    def __next__(self) -> Row:
        return self.load_next()
