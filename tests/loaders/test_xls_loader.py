from src.loaders.xls_loader import XLSLoader

ANSWER = [{"a": "a", "b": "123", "c": "b"}, {"a": "c", "b": "456", "c": "d"}]


def test_load_next(xls_loader: XLSLoader) -> None:
    for r, a in zip(xls_loader, ANSWER):
        assert r == a
