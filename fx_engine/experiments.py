"""Controlled, synthetic USD/SGD dealer-policy experiments.

An exogenous stream of potential client requests and acceptance uniforms is
shared across policies. Accepted orders differ by policy because quote prices
differ. Results are a model exercise, never observed bank performance.
"""
from dataclasses import dataclass, replace
import math
import numpy as np
import pandas as pd
from fx_engine.market import MarketConfig, generate_market
from fx_engine.orders import ClientOrder, generate_orders
from fx_engine.dealer import DealerBook
from fx_engine.risk import RiskSettings, adjusted_quote
from fx_engine.quotes import PIP

POLICIES = ('Fixed quotes', 'Inventory-aware quotes', 'Inventory-aware + hedging')

@dataclass(frozen=True)
class ExperimentConfig:
    market: MarketConfig = MarketConfig()
    order_count: int = 50
    buy_probability: float = 0.5
    min_order_usd: float = 10000.0
    max_order_usd: float = 100000.0
    dealer_spread_pips: float = 4.0
    inventory_limit_usd: float = 100000.0
    inventory_skew_pips: float = 2.0
    hedge_spread_pips: float = 1.0
    hedge_trigger_fraction: float = 0.7
    hedge_target_fraction: float = 0.25
    acceptance_baseline: float = 0.75
    acceptance_sensitivity: float = 0.4

    def validate(self):
        self.market.validate()
        if not 1 <= self.order_count <= self.market.steps:
            raise ValueError('Order count must be between 1 and market steps')
        if not (0 <= self.buy_probability <= 1 and 0 < self.min_order_usd <= self.max_order_usd):
            raise ValueError('Invalid order demand settings')
        if not (0 < self.dealer_spread_pips <= 100):
            raise ValueError('Invalid dealer spread')
        if not (0 < self.acceptance_baseline < 1 and 0 <= self.acceptance_sensitivity <= 10):
            raise ValueError('Acceptance probabilities or price sensitivity invalid')
        self.risk_settings.validate()

    @property
    def risk_settings(self):
        return RiskSettings(inventory_limit_usd=self.inventory_limit_usd,
            hedge_trigger_fraction=self.hedge_trigger_fraction,
            hedge_target_fraction=self.hedge_target_fraction,
            hedge_spread_pips=self.hedge_spread_pips,
            inventory_skew_pips=self.inventory_skew_pips)


def acceptance_probability(side: str, bid: float, ask: float, reference_mid: float,
                           base_spread_pips: float, base_probability: float, sensitivity: float) -> float:
    """Illustrative, price-responsive acceptance, anchored at half the base spread.

    Customer buys USD: worse price is higher ask. Customer sells USD:
    worse price is lower bid. No claim of fitted empirical demand.
    """
    if side == 'Client buys USD':
        concession = (ask - reference_mid) / PIP
    elif side == 'Client sells USD':
        concession = (reference_mid - bid) / PIP
    else:
        raise ValueError('Invalid order direction')
    if not (0 < base_probability < 1 and sensitivity >= 0):
        raise ValueError('Invalid acceptance parameters')
    x = math.log(base_probability / (1-base_probability)) - sensitivity*(concession-base_spread_pips/2)
    return 1/(1+math.exp(-max(-60,min(60,x))))


def _inputs(config: ExperimentConfig, seed: int):
    market = generate_market(replace(config.market, seed=seed))
    orders = generate_orders(config.market.steps, config.order_count, seed+100001,
                            config.min_order_usd, config.max_order_usd, config.buy_probability)
    uniforms = np.random.default_rng(seed+200003).random(len(orders))
    return market, orders, {order.step:float(u) for order,u in zip(orders,uniforms)}


def simulate_policy(config: ExperimentConfig, policy: str, market: pd.DataFrame,
                    orders: list[ClientOrder], uniforms: dict[int,float]):
    config.validate()
    if policy not in POLICIES:
        raise ValueError('Unknown quoting policy')
    if list(market['step']) != list(range(config.market.steps + 1)):
        raise ValueError('Market steps must match the experiment configuration')
    if set(uniforms) != {o.step for o in orders} or len(orders) != len({o.step for o in orders}):
        raise ValueError('Acceptance uniforms must match unique order steps')
    risk=config.risk_settings
    if policy == POLICIES[0]:
        risk=replace(risk, inventory_skew_pips=0.0)
    hedge_enabled=policy == POLICIES[2]
    order_map={o.step:o for o in orders}
    book=DealerBook(); events=[]; timeline=[]
    requests=fills=customer_declines=limit_rejects=hedges=0
    hedge_cost=0.0; turnover=0.0
    for point in market.itertuples(index=False):
        step=int(point.step); mid=float(point.mid)
        quote=adjusted_quote(mid,config.dealer_spread_pips,book.usd_inventory,0,0,risk)
        if step in order_map:
            order=order_map[step]; requests+=1
            prob=acceptance_probability(order.side,quote.bid,quote.ask,mid,
                                        config.dealer_spread_pips,config.acceptance_baseline,
                                        config.acceptance_sensitivity)
            u=uniforms[step]
            inventory_delta=-order.usd_amount if order.side=='Client buys USD' else order.usd_amount
            if u>=prob:
                customer_declines+=1; outcome='Customer declined'
            elif abs(book.usd_inventory+inventory_delta)>config.inventory_limit_usd+1e-8:
                limit_rejects+=1; outcome='Risk limit rejected'
            else:
                transaction=book.execute(order,quote)
                fills+=1; turnover+=order.usd_amount
                outcome='Client filled'
            events.append({'step':step,'policy':policy,'event':outcome,
                           'client_side':order.side,'usd_amount':order.usd_amount,
                           'bid':quote.bid,'ask':quote.ask,'acceptance_probability':prob,
                           'acceptance_uniform':u,'usd_inventory':book.usd_inventory,
                           'marked_pnl_sgd':book.equity_sgd(mid)})
        if hedge_enabled and abs(book.usd_inventory) > risk.inventory_limit_usd*risk.hedge_trigger_fraction:
            target=math.copysign(risk.inventory_limit_usd*risk.hedge_target_fraction,book.usd_inventory)
            delta=target-book.usd_inventory
            execution_price=mid+math.copysign(risk.hedge_spread_pips*PIP/2,delta)
            book.usd_inventory+=delta
            book.sgd_cash-=delta*execution_price
            hedge_cost+=abs(delta)*risk.hedge_spread_pips*PIP/2
            hedges+=1
            events.append({'step':step,'policy':policy,'event':'Interdealer hedge',
                           'client_side':'Buy USD' if delta>0 else 'Sell USD','usd_amount':abs(delta),
                           'bid':float('nan'),'ask':float('nan'),'acceptance_probability':float('nan'),
                           'acceptance_uniform':float('nan'),'usd_inventory':book.usd_inventory,
                           'marked_pnl_sgd':book.equity_sgd(mid)})
        timeline.append({'step':step,'policy':policy,'mid':mid,
                         'usd_inventory':book.usd_inventory,'sgd_cash':book.sgd_cash,
                         'marked_pnl_sgd':book.equity_sgd(mid),
                         'inventory_utilization_pct':100*abs(book.usd_inventory)/config.inventory_limit_usd})
    t=pd.DataFrame(timeline); e=pd.DataFrame(events)
    # Include zero starting equity as drawdown high water mark.
    highs=t['marked_pnl_sgd'].cummax().clip(lower=0)
    max_dd=float((highs-t['marked_pnl_sgd']).max())
    metrics={'policy':policy,'requests':requests,'fills':fills,'customer_declines':customer_declines,
             'limit_rejections':limit_rejects,'fill_rate_pct':100*fills/requests if requests else 0,
             'final_pnl_sgd':float(t['marked_pnl_sgd'].iloc[-1]),
             'max_drawdown_sgd':max_dd,
             'peak_inventory_usd':float(t['usd_inventory'].abs().max()),
             'mean_abs_inventory_usd':float(t['usd_inventory'].abs().mean()),
             'hedge_count':hedges,'hedge_cost_sgd':float(hedge_cost),
             'client_turnover_usd':turnover}
    return e,t,metrics


def compare_policies(config: ExperimentConfig, seed: int):
    config.validate()
    market,orders,uniforms=_inputs(config,seed)
    results={p:simulate_policy(config,p,market,orders,uniforms) for p in POLICIES}
    return results


def multi_seed_comparison(config: ExperimentConfig, first_seed: int, sessions: int):
    if not 1 <= sessions <= 100:
        raise ValueError('Number of sessions must be from 1 to 100')
    records=[]
    for seed in range(first_seed,first_seed+sessions):
        for policy,(_,_,metrics) in compare_policies(config,seed).items():
            records.append({'seed':seed,**metrics})
    frame=pd.DataFrame(records)
    summary=(frame.groupby('policy',sort=False)
             .agg(sessions=('seed','size'),mean_pnl_sgd=('final_pnl_sgd','mean'),
                  median_pnl_sgd=('final_pnl_sgd','median'),
                  worst_pnl_sgd=('final_pnl_sgd','min'),
                  mean_drawdown_sgd=('max_drawdown_sgd','mean'),
                  mean_peak_inventory_usd=('peak_inventory_usd','mean'),
                  mean_fill_rate_pct=('fill_rate_pct','mean'),
                  mean_hedge_cost_sgd=('hedge_cost_sgd','mean'))
             .reset_index())
    return frame,summary
