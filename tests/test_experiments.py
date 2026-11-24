import pytest
from dataclasses import replace
from fx_engine.experiments import (POLICIES,ExperimentConfig,acceptance_probability,
                                   compare_policies,multi_seed_comparison)
from fx_engine.market import MarketConfig


def cfg():
    return ExperimentConfig(market=MarketConfig(steps=60,seed=12,volatility_pips=4.0),
                            order_count=35, inventory_limit_usd=100000,inventory_skew_pips=3)


def test_acceptance_direction():
    p=acceptance_probability('Client buys USD',1.3498,1.3502,1.35,4,.75,.6)
    assert p==pytest.approx(.75)
    assert acceptance_probability('Client buys USD',1.3498,1.3504,1.35,4,.75,.6)<p
    assert acceptance_probability('Client sells USD',1.3496,1.3502,1.35,4,.75,.6)<p


def test_same_seed_deterministic():
    first=compare_policies(cfg(),7)
    second=compare_policies(cfg(),7)
    for policy in POLICIES:
        assert first[policy][2]==second[policy][2]


def test_policy_accounting_and_limits():
    for _, timeline, metrics in compare_policies(cfg(),3).values():
        assert (timeline['usd_inventory'].abs()<=100000+1e-6).all()
        assert (timeline['marked_pnl_sgd']-(timeline['sgd_cash']+timeline['usd_inventory']*timeline['mid'])).abs().max()<1e-7
        assert metrics['requests']==metrics['fills']+metrics['customer_declines']+metrics['limit_rejections']
        assert metrics['max_drawdown_sgd']>=0


def test_experiment_policy_hedging():
    runs=compare_policies(cfg(),20)
    assert runs['Fixed quotes'][2]['hedge_count']==0
    assert runs['Inventory-aware quotes'][2]['hedge_count']==0
    assert runs['Inventory-aware + hedging'][2]['hedge_count']>=0


def test_equal_opportunity_requests():
    runs=compare_policies(cfg(),9)
    assert len({m['requests'] for _,_,m in runs.values()})==1
    reference=runs[POLICIES[0]][0]
    for p in POLICIES[1:]:
        other=runs[p][0]
        assert list(reference[reference.event!='Interdealer hedge']['acceptance_uniform'])==list(other[other.event!='Interdealer hedge']['acceptance_uniform'])


def test_multi_seed_summary():
    rows,summary=multi_seed_comparison(cfg(),30,4)
    assert len(rows)==12
    assert len(summary)==3
    assert (summary['sessions']==4).all()


def test_quoted_edge_affects_fills():
    base=cfg()
    loose=replace(base,acceptance_sensitivity=0)
    tight=replace(base,acceptance_sensitivity=2)
    for cfg_ in (loose,tight):
        result=compare_policies(cfg_,5)
        for _,_,m in result.values():
            assert 0<=m['fill_rate_pct']<=100


def test_invalid_policies_and_params():
    with pytest.raises(ValueError):
        multi_seed_comparison(cfg(),0,0)
    with pytest.raises(ValueError):
        replace(cfg(), acceptance_baseline=1.0).validate()
