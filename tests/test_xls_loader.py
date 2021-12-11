from pathlib import Path

import pytest

from src.loaders.xls_loader import XLSLoader

ANSWER = [{"a": "a", "b": "123", "c": "b"}, {"a": "c", "b": "456", "c": "d"}]


@pytest.fixture
def loader() -> XLSLoader:
    test_root = Path(__file__).parent / "testcase.xlsx"
    return XLSLoader(str(test_root), "Sheet1")


def test_load_next(loader: XLSLoader) -> None:
    for r, a in zip(loader, ANSWER):
        assert r == a
