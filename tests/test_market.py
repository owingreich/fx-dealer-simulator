import numpy as np
import pytest
from fx_engine.market import MarketConfig, generate_market


def test_reproducible_given_same_seed():
    config = MarketConfig(seed=11)
    assert generate_market(config).equals(generate_market(config))


def test_different_seed_generates_different_path():
    assert not generate_market(MarketConfig(seed=11)).equals(generate_market(MarketConfig(seed=12)))


def test_initial_mid_and_steps():
    m = generate_market(MarketConfig(initial_mid=1.37, steps=100))
    assert len(m) == 101
    assert m.loc[0, "mid"] == pytest.approx(1.37)
    assert np.isfinite(m["mid"]).all()
    assert (m["mid"] > 0).all()


def test_zero_volatility_calm_flat():
    m = generate_market(MarketConfig(volatility_pips=0.0, scenario="Calm"))
    assert (m["mid"] == 1.35).all()


def test_invalid_parameters_fail():
    with pytest.raises(ValueError):
        generate_market(MarketConfig(steps=1))
