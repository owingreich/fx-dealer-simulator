import math
import pandas as pd
import pytest
from fx_engine.dealer import DealerBook, run_dealer
from fx_engine.orders import ClientOrder, generate_orders
from fx_engine.quotes import make_quote


def test_client_buy_reduces_dealer_inventory_and_receives_sgd():
    book=DealerBook(); q=make_quote(1.35,4)
    r=book.execute(ClientOrder(1,'Client buys USD',100000),q)
    assert r['usd_inventory']==-100000
    assert math.isclose(r['sgd_cash'],135020)
    assert math.isclose(r['equity_sgd'],20)


def test_client_sell_increases_inventory_and_spends_sgd():
    book=DealerBook(); q=make_quote(1.35,4)
    r=book.execute(ClientOrder(1,'Client sells USD',100000),q)
    assert r['usd_inventory']==100000
    assert math.isclose(r['sgd_cash'],-134980)
    assert math.isclose(r['equity_sgd'],20)


def test_roundtrip_at_unchanged_mid_captures_spread():
    book=DealerBook(); q=make_quote(1.35,4)
    book.execute(ClientOrder(1,'Client buys USD',100000),q)
    book.execute(ClientOrder(2,'Client sells USD',100000),q)
    assert math.isclose(book.usd_inventory,0)
    assert math.isclose(book.equity_sgd(1.35),40)


def test_flat_inventory_has_no_fx_directional_pnl():
    book=DealerBook(0,120)
    assert book.equity_sgd(1.30)==book.equity_sgd(1.45)==120


def test_invalid_order_rejected():
    with pytest.raises(ValueError):
        DealerBook().execute(ClientOrder(1,'Client buys USD',-1),make_quote(1.35))


def test_order_generation_is_deterministic_and_one_per_step():
    a=generate_orders(100,20,42); b=generate_orders(100,20,42)
    assert a==b
    assert len(set(x.step for x in a))==20


def test_timeline_reconciles():
    market=pd.DataFrame({'step':[0,1,2],'mid':[1.35,1.36,1.34]})
    orders=[ClientOrder(1,'Client buys USD',100000)]
    ledger,timeline=run_dealer(market,orders,4)
    assert len(ledger)==1
    assert math.isclose(timeline.iloc[-1].marked_equity_sgd,timeline.iloc[-1].sgd_cash+timeline.iloc[-1].usd_inventory*1.34)
    assert math.isclose(timeline.iloc[1].marked_equity_sgd,20)
    assert math.isclose(timeline.iloc[-1].marked_equity_sgd,2020)
