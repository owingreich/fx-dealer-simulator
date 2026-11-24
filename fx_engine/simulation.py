"""Milestone 3: client fills, hard inventory limits and optional hedging.

No simulated execution here is an institutional market quote or a real fill.
"""
import math
import pandas as pd
from fx_engine.dealer import DealerBook
from fx_engine.quotes import PIP
from fx_engine.orders import ClientOrder
from fx_engine.risk import RiskSettings, adjusted_quote


def run_risk_simulation(market: pd.DataFrame, orders: list[ClientOrder], spread_pips: float,
                        settings: RiskSettings, hedge_enabled: bool = True,
                        base_volatility_pips: float = 5.0, rolling_window: int = 20):
    settings.validate()
    if market.empty or any(c not in market.columns for c in ('step','mid')):
        raise ValueError('Market must contain step and mid columns')
    if not market['step'].is_unique or not market['step'].is_monotonic_increasing:
        raise ValueError('Market steps must be strictly increasing')
    if not all(math.isfinite(float(v)) and float(v)>0 for v in market['mid']):
        raise ValueError('Market mids must be finite and positive')
    if not (0 < spread_pips <= 100) or base_volatility_pips < 0 or rolling_window < 2:
        raise ValueError('Invalid spread or volatility configuration')
    by_step={o.step:o for o in orders}
    if len(by_step)!=len(orders) or not set(by_step).issubset(set(market['step'])):
        raise ValueError('Orders must have distinct, valid steps')
    book=DealerBook()
    events=[]; history=[]; mids=[]
    total_orders=0; accepted=0; rejected=0; hedges=0; hedge_cost=0.0
    for p in market.itertuples(index=False):
        step=int(p.step); mid=float(p.mid)
        # Use only past price changes for quote volatility, excluding current step.
        if len(mids)>=3:
            changes=[(mids[i]-mids[i-1])/PIP for i in range(1,len(mids))]
            past_vol=float(pd.Series(changes[-rolling_window:]).std(ddof=0)) if len(changes)>=2 else base_volatility_pips
        else:
            past_vol=base_volatility_pips
        quote=adjusted_quote(mid,spread_pips,book.usd_inventory,past_vol,base_volatility_pips,settings)
        if step in by_step:
            total_orders+=1
            order=by_step[step]
            if not math.isfinite(order.usd_amount) or order.usd_amount<=0:
                raise ValueError('Order size must be positive and finite')
            delta=-order.usd_amount if order.side=='Client buys USD' else order.usd_amount if order.side=='Client sells USD' else None
            if delta is None: raise ValueError('Invalid client side')
            if abs(book.usd_inventory+delta) > settings.inventory_limit_usd+1e-9:
                rejected+=1
                events.append({'step':step,'event':'Client rejected: inventory limit','side':order.side,
                               'usd_amount':order.usd_amount,'price':float('nan'),
                               'usd_change':0.0,'sgd_change':0.0,'equity_sgd':book.equity_sgd(mid)})
            else:
                accepted+=1
                trade=book.execute(order,quote)
                events.append({'step':step,'event':'Client filled','side':order.side,'usd_amount':order.usd_amount,
                               'price':trade['fill_rate'],'usd_change':trade['dealer_usd_change'],
                               'sgd_change':trade['sgd_cash_change'],'equity_sgd':book.equity_sgd(mid)})
        # Hedging is performed after the client interaction, at adverse external bid/ask.
        trigger=settings.inventory_limit_usd*settings.hedge_trigger_fraction
        if hedge_enabled and abs(book.usd_inventory)>trigger:
            target=math.copysign(settings.inventory_limit_usd*settings.hedge_target_fraction,book.usd_inventory)
            delta=target-book.usd_inventory
            # Dealer buys USD at external ask or sells at external bid.
            external_price=mid+math.copysign(settings.hedge_spread_pips*PIP/2,delta)
            sgd_change=-delta*external_price
            book.usd_inventory+=delta; book.sgd_cash+=sgd_change
            hedges+=1
            hedge_cost+=abs(delta)*settings.hedge_spread_pips*PIP/2
            events.append({'step':step,'event':'Interdealer hedge','side':'Buy USD' if delta>0 else 'Sell USD',
                           'usd_amount':abs(delta),'price':external_price,'usd_change':delta,
                           'sgd_change':sgd_change,'equity_sgd':book.equity_sgd(mid)})
        equity=book.equity_sgd(mid)
        history.append({'step':step,'mid':mid,'bid':quote.bid,'ask':quote.ask,
                        'quote_spread_pips':quote.spread_pips,'estimated_prior_vol_pips':past_vol,
                        'usd_inventory':book.usd_inventory,'sgd_cash':book.sgd_cash,
                        'marked_equity_sgd':equity,'inventory_utilization_pct':100*abs(book.usd_inventory)/settings.inventory_limit_usd,
                        'orders_filled_cumulative':accepted,'orders_rejected_cumulative':rejected,
                        'hedges_cumulative':hedges,'hedging_cost_proxy_sgd':hedge_cost})
        mids.append(mid)
    timeline=pd.DataFrame(history)
    events=pd.DataFrame(events,columns=['step','event','side','usd_amount','price','usd_change','sgd_change','equity_sgd'])
    running_high=timeline['marked_equity_sgd'].cummax().clip(lower=0)
    drawdown=timeline['marked_equity_sgd']-running_high
    metrics={'client_requests':total_orders,'client_fills':accepted,'rejections':rejected,'hedges':hedges,
             'fill_rate_pct':100*accepted/total_orders if total_orders else 0,
             'final_pnl_sgd':float(timeline['marked_equity_sgd'].iloc[-1]),
             'max_drawdown_sgd':float(-drawdown.min()),
             'peak_abs_inventory_usd':float(timeline['usd_inventory'].abs().max()),
             'hedge_execution_cost_sgd':float(hedge_cost)}
    return events,timeline,metrics
