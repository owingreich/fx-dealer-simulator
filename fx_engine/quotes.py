"""Dealer quote primitives. USD/SGD is quoted SGD for one USD."""
from dataclasses import dataclass

PIP = 0.0001

@dataclass(frozen=True)
class FXQuote:
    bid: float
    ask: float
    mid: float
    spread_pips: float


def make_quote(mid: float, spread_pips: float = 4.0) -> FXQuote:
    """Two-way quote; dealer buys USD at bid and sells USD at ask.

    Quote prices remain unrounded internally. UI can display extra decimals to
    avoid misleading spreads for fractional-pip parameters.
    """
    if not (0 < mid < 10):
        raise ValueError("mid must be positive")
    if not (0 < spread_pips <= 100):
        raise ValueError("spread_pips must be within (0, 100]")
    half = spread_pips * PIP / 2
    bid, ask = mid - half, mid + half
    if bid <= 0:
        raise ValueError("bid must be positive")
    return FXQuote(bid=bid, ask=ask, mid=mid, spread_pips=spread_pips)
