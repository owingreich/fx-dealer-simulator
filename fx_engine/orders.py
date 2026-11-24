"""Reproducible hypothetical client requests; all orders are filled in milestone 2."""
from dataclasses import dataclass
from typing import Literal
import numpy as np
import pandas as pd

Side = Literal['Client buys USD', 'Client sells USD']

@dataclass(frozen=True)
class ClientOrder:
    step: int
    side: Side
    usd_amount: float


def generate_orders(steps: int, count: int, seed: int, min_usd: float = 10000,
                    max_usd: float = 100000, buy_probability: float = 0.5) -> list[ClientOrder]:
    if not (1 <= count <= steps):
        raise ValueError('order count must be between 1 and the number of market steps')
    if not (0 < min_usd <= max_usd) or not 0 <= buy_probability <= 1:
        raise ValueError('invalid client order parameters')
    rng = np.random.default_rng(seed)
    ticks = sorted(rng.choice(np.arange(1, steps + 1), size=count, replace=False).tolist())
    result = []
    for tick in ticks:
        side: Side = 'Client buys USD' if rng.random() < buy_probability else 'Client sells USD'
        amount = float(rng.uniform(min_usd, max_usd))
        result.append(ClientOrder(step=int(tick), side=side, usd_amount=round(amount, 2)))
    return result
