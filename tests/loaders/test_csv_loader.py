from io import StringIO
import pytest

from src.loaders.csv_loader import CSVLoader

ANSWER = [{"a": "a", "b": "123", "c": "b"}, {"a": "c", "b": "456", "c": "d"}]
INPUT = "a,b,c\n" + "\n".join(map(lambda x: ",".join(x.values()), ANSWER))


@pytest.fixture
def loader() -> CSVLoader:
    data = StringIO(INPUT)
    return CSVLoader(data)


def test_load_next(loader: CSVLoader) -> None:
    for r, a in zip(loader, ANSWER):
        assert r == a
