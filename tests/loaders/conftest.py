from io import StringIO
from pathlib import Path

import pytest

from src.loaders.csv_loader import CSVLoader
from src.loaders.xls_loader import XLSLoader


@pytest.fixture
def xls_loader() -> XLSLoader:
    test_root = Path(__file__).parent / "testcase.xlsx"
    return XLSLoader(str(test_root), "Sheet1")


@pytest.fixture
def csv_loader() -> CSVLoader:
    string = StringIO("amount,name\n42,example\n7,lorem ipsum")
    return CSVLoader(string)
