"""Risk rules and quote adjustments for simulated SGD-per-USD dealer flow."""
from dataclasses import dataclass
import math
from fx_engine.quotes import make_quote, FXQuote, PIP

@dataclass(frozen=True)
class RiskSettings:
    inventory_limit_usd: float = 1_000_000.0
    hedge_trigger_fraction: float = 0.7
    hedge_target_fraction: float = 0.25
    hedge_spread_pips: float = 1.0
    volatility_spread_multiplier: float = 0.0
    inventory_skew_pips: float = 0.0
    def validate(self):
        if not math.isfinite(self.inventory_limit_usd) or self.inventory_limit_usd <= 0:
            raise ValueError('Inventory limit must be positive')
        if not (0 <= self.hedge_target_fraction < self.hedge_trigger_fraction <= 1):
            raise ValueError('Hedge target must be below the trigger')
        if not (0 <= self.hedge_spread_pips <= 100):
            raise ValueError('Hedge spread must be 0 to 100 pips')
        if not (0 <= self.volatility_spread_multiplier <= 5):
            raise ValueError('Volatility spread multiplier must be 0 to 5')
        if not (0 <= self.inventory_skew_pips <= 20):
            raise ValueError('Inventory skew must be 0 to 20 pips')


def adjusted_quote(mid: float, base_spread_pips: float, inventory_usd: float,
                   volatility_pips: float, base_volatility_pips: float,
                   settings: RiskSettings) -> FXQuote:
    """Shift both quotes downward when long USD, upward when short USD.

    Wider volatility quote is an illustrative dealer risk rule, not a market calibration.
    """
    settings.validate()
    vol_extra = settings.volatility_spread_multiplier * max(0.0, volatility_pips - base_volatility_pips)
    spread = base_spread_pips + vol_extra
    skew = -settings.inventory_skew_pips * (inventory_usd / settings.inventory_limit_usd) * PIP
    return make_quote(mid + skew, spread)
