from io import StringIO
import pytest

from src.loaders.csv_loader import CSVLoader

ANSWER = [["a", "123", "b"], ["c", "456", "d"]]
INPUT = "\n".join(map(lambda x: ",".join(x), ANSWER))


@pytest.fixture
def loader() -> CSVLoader:
    data = StringIO(INPUT)
    return CSVLoader(data)


def test_load_next(loader):
    for r, a in zip(loader.load_next(), ANSWER):
        assert r == a
