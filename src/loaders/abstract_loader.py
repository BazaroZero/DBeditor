from abc import ABC, abstractmethod
from typing import Any, List, Generator


class AbstractLoader(ABC):
    @abstractmethod
    def load_next(self) -> Generator[List[Any], None, None]:
        pass

    def __next__(self) -> Generator[List[Any], None, None]:
        yield from self.load_next()
