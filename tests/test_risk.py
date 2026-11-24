import math
import pandas as pd
from fx_engine.orders import ClientOrder
from fx_engine.risk import RiskSettings, adjusted_quote
from fx_engine.simulation import run_risk_simulation

MARKET=pd.DataFrame({'step':[0,1,2,3],'mid':[1.35,1.35,1.35,1.35]})

def test_inventory_limit_rejects_order():
    es,tl,m=run_risk_simulation(MARKET,[ClientOrder(1,'Client buys USD',200000)],4,
                                RiskSettings(inventory_limit_usd=100000),False)
    assert m['rejections']==1 and m['client_fills']==0
    assert tl.iloc[-1].usd_inventory==0 and tl.iloc[-1].marked_equity_sgd==0

def test_hedging_reduces_inventory_and_costs_money():
    settings=RiskSettings(inventory_limit_usd=100000,hedge_trigger_fraction=.7,
                          hedge_target_fraction=.25,hedge_spread_pips=2)
    events,tl,m=run_risk_simulation(MARKET,[ClientOrder(1,'Client sells USD',80000)],4,settings,True)
    assert m['hedges']==1
    assert math.isclose(tl.iloc[-1].usd_inventory,25000)
    assert math.isclose(m['hedge_execution_cost_sgd'],5.5)
    assert math.isclose(tl.iloc[-1].marked_equity_sgd,16-5.5)

def test_hedging_disabled_keeps_inventory():
    settings=RiskSettings(inventory_limit_usd=100000)
    _,tl,m=run_risk_simulation(MARKET,[ClientOrder(1,'Client sells USD',80000)],4,settings,False)
    assert tl.iloc[-1].usd_inventory==80000 and m['hedges']==0

def test_quote_skew_direction():
    settings=RiskSettings(inventory_limit_usd=100000,inventory_skew_pips=2)
    long=adjusted_quote(1.35,4,50000,5,5,settings)
    short=adjusted_quote(1.35,4,-50000,5,5,settings)
    assert long.mid<1.35<short.mid
    assert math.isclose(long.ask-long.bid,.0004)

def test_wider_quotes_with_higher_prior_vol():
    settings=RiskSettings(volatility_spread_multiplier=.5)
    a=adjusted_quote(1.35,4,0,5,5,settings)
    b=adjusted_quote(1.35,4,0,15,5,settings)
    assert b.spread_pips>a.spread_pips

def test_accounting_reconciles_every_step():
    orders=[ClientOrder(1,'Client sells USD',80000),ClientOrder(2,'Client buys USD',20000)]
    _,tl,_=run_risk_simulation(MARKET,orders,4,RiskSettings(inventory_limit_usd=100000),True)
    for row in tl.itertuples():
        assert math.isclose(row.marked_equity_sgd,row.sgd_cash+row.usd_inventory*row.mid,abs_tol=1e-7)
        assert abs(row.usd_inventory)<=100000

def test_seed_independent_simulation_stable():
    args=(MARKET,[ClientOrder(1,'Client sells USD',80000)],4,RiskSettings(inventory_limit_usd=100000))
    e1,t1,m1=run_risk_simulation(*args)
    e2,t2,m2=run_risk_simulation(*args)
    assert e1.equals(e2) and t1.equals(t2) and m1==m2
