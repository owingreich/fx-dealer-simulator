"""Synthetic USD/SGD mid-market paths. All output is simulation, not tradable quotes."""
from dataclasses import dataclass
from typing import Literal
import numpy as np
import pandas as pd

Scenario = Literal["Calm", "Trending USD up", "Trending USD down", "Volatility shock"]
SCENARIOS = ("Calm", "Trending USD up", "Trending USD down", "Volatility shock")

@dataclass(frozen=True)
class MarketConfig:
    initial_mid: float = 1.35
    steps: int = 250
    seed: int = 42
    volatility_pips: float = 5.0
    scenario: Scenario = "Calm"

    def validate(self) -> None:
        if not (0.1 <= self.initial_mid <= 10):
            raise ValueError("initial_mid must be a positive, plausible SGD-per-USD FX rate")
        if not 2 <= self.steps <= 10000:
            raise ValueError("steps must be between 2 and 10000")
        if not 0 <= self.volatility_pips <= 100:
            raise ValueError("volatility_pips must be between 0 and 100")
        if self.scenario not in SCENARIOS:
            raise ValueError(f"scenario must be one of {SCENARIOS}")


def generate_market(config: MarketConfig) -> pd.DataFrame:
    """Generate one simulated mid-rate observation per step.

    Model: additive random changes in pip units (1 pip = 0.0001 SGD/USD).
    The market scenarios are illustrative, not calibrated probabilistic forecasts.
    """
    config.validate()
    rng = np.random.default_rng(config.seed)
    drift = {"Calm": 0.0, "Trending USD up": 0.8,
             "Trending USD down": -0.8, "Volatility shock": 0.0}[config.scenario]
    noise = rng.normal(loc=drift, scale=config.volatility_pips, size=config.steps)
    if config.scenario == "Volatility shock":
        begin, end = config.steps // 3, 2 * config.steps // 3
        noise[begin:end] *= 3.0
    mid = config.initial_mid + np.cumsum(np.r_[0.0, noise]) * 0.0001
    if np.any(mid <= 0):
        raise ValueError("Synthetic market path produced a nonpositive FX rate")
    steps = np.arange(config.steps + 1)
    return pd.DataFrame({"step": steps, "mid": mid,
                         "change_pips": np.r_[0.0, noise]})
