"""Cash/inventory bookkeeping for hypothetical filled USD/SGD client orders."""
from dataclasses import dataclass
import math
import pandas as pd
from fx_engine.orders import ClientOrder
from fx_engine.quotes import FXQuote, make_quote

@dataclass
class DealerBook:
    usd_inventory: float = 0.0
    sgd_cash: float = 0.0

    def equity_sgd(self, reference_mid: float) -> float:
        return self.sgd_cash + self.usd_inventory * reference_mid

    def execute(self, order: ClientOrder, quote: FXQuote) -> dict:
        if not math.isfinite(order.usd_amount) or order.usd_amount <= 0:
            raise ValueError('USD amount must be finite and positive')
        if order.side == 'Client buys USD':
            # Dealer sells USD at ask; receives SGD.
            dealer_change_usd, price = -order.usd_amount, quote.ask
        elif order.side == 'Client sells USD':
            # Dealer buys USD at bid; pays SGD.
            dealer_change_usd, price = order.usd_amount, quote.bid
        else:
            raise ValueError('Unknown client side')
        sgd_change = -dealer_change_usd * price
        self.usd_inventory += dealer_change_usd
        self.sgd_cash += sgd_change
        return {'step': order.step, 'client_side': order.side, 'usd_amount': order.usd_amount,
                'fill_rate': price, 'dealer_usd_change': dealer_change_usd,
                'sgd_cash_change': sgd_change, 'usd_inventory': self.usd_inventory,
                'sgd_cash': self.sgd_cash, 'mark_mid': quote.mid,
                'equity_sgd': self.equity_sgd(quote.mid)}


def run_dealer(market: pd.DataFrame, orders: list[ClientOrder], spread_pips: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run transactions in ascending time; MTM marks positions to mid after each step.

    Initial USD and SGD holdings are zero. Marked equity is P&L before external
    financing and hedge costs. It includes spread capture and currency risk.
    """
    book = DealerBook()
    by_step = {o.step: o for o in orders}
    if len(by_step) != len(orders):
        raise ValueError('At most one client order per step in milestone 2')
    valid_steps = set(int(s) for s in market['step'])
    if not set(by_step).issubset(valid_steps):
        raise ValueError('Order refers to a missing market step')
    ledger, timeline = [], []
    for point in market.itertuples(index=False):
        mid = float(point.mid)
        if int(point.step) in by_step:
            ledger.append(book.execute(by_step[int(point.step)], make_quote(mid, spread_pips)))
        timeline.append({'step': int(point.step), 'mid': mid,
                         'usd_inventory': book.usd_inventory, 'sgd_cash': book.sgd_cash,
                         'marked_equity_sgd': book.equity_sgd(mid)})
    return pd.DataFrame(ledger), pd.DataFrame(timeline)
