import pytest
from fx_engine.quotes import PIP, make_quote


def test_bid_ask_and_spread():
    q = make_quote(1.35, 4)
    assert q.bid == pytest.approx(1.3498)
    assert q.ask == pytest.approx(1.3502)
    assert (q.ask - q.bid) / PIP == pytest.approx(4)
    assert (q.bid + q.ask) / 2 == pytest.approx(q.mid)


def test_invalid_quote_fails():
    with pytest.raises(ValueError):
        make_quote(1.35, -1)
