# FX Dealer Simulator: Market-Making Policy Study

## Research question

Under an assumed synthetic USD/SGD market and customer-demand model, how do fixed quotations, inventory-sensitive quotations, and inventory-sensitive quotations with external hedging compare in spread capture, risk, and client execution?

## Simulation design

The simulator models a hypothetical dealer quoting SGD per USD. One pip equals 0.0001 SGD per USD. Client purchases of USD reduce dealer USD inventory; client sales of USD increase it. The dealer records SGD cash and reports marked equity as `SGD cash + USD inventory × synthetic mid` from a zero-balance starting book. It is a *simulation P&L proxy*, not actual bank accounting or a live brokerage statement.

Each quoting policy faces the same synthetic price path, potential customer request sizes/directions and pre-drawn client acceptance uniforms within each seed. The hypothetical acceptance probability varies with the price quoted relative to the mid-price. Different policies therefore generate different *accepted* transactions. A hard inventory limit applies to all policies. The hedge policy trades externally at an assumed spread when inventory crosses a trigger.

### Reproducible baseline settings

| Parameter | Value |
|---|---:|
| Synthetic market scenario | Calm |
| Initial USD/SGD mid | 1.3500 |
| Steps per simulated session | 250 |
| Step volatility | 5 pips |
| Dealer spread | 4 pips |
| Potential client orders | 50 per session |
| Client buy-USD probability | 50% |
| Customer order-size range | US$10,000 to US$100,000 |
| Dealer hard inventory limit | US$100,000 |
| Inventory skew at full limit | 2 pips |
| External hedge spread | 1 pip |
| Hedge trigger / target | 70% / 25% of inventory limit |
| Baseline client quote acceptance | 75% |
| Sensitivity to quote concession | 0.4 per pip |
| Seed range for comparison | 42 to 56 (15 sessions) |

## Results: paired 15-session simulation

| Policy | Mean marked P&L (SGD) | Median P&L (SGD) | Worst session (SGD) | Mean maximum drawdown (SGD) | Mean peak absolute USD inventory | Mean client fill rate |
|---|---:|---:|---:|---:|---:|---:|
| Fixed quotes | +370.61 | +443.64 | -587.54 | 409.13 | 95,195 | 56.93% |
| Inventory-aware quotes | +337.97 | +271.81 | -624.17 | 380.02 | 94,756 | 60.53% |
| Inventory-aware + hedging | +285.18 | +413.09 | -229.36 | 268.69 | 66,738 | 62.00% |

*Figures are deterministic outputs of the baseline simulator code, rounded to two decimals. Mean hedge spread cost was S$16.14 per hedged session (zero for other policies).* 

### One illustrative session (seed 42)

| Policy | Final marked P&L | Max drawdown | Peak USD inventory | Client fill rate |
|---|---:|---:|---:|---:|
| Fixed quotes | -S$382.92 | S$623.96 | US$95,024 | 54% |
| Inventory-aware quotes | -S$624.17 | S$730.31 | US$92,403 | 60% |
| Inventory-aware + hedging | -S$229.36 | S$403.94 | US$59,941 | 64% |

## Interpretation

Across these 15 synthetic sessions, the unhedged fixed-quote policy had the highest **mean** P&L, while the hedge policy had lower mean P&L but a smaller worst-session loss, smaller average drawdown, lower peak USD inventory, and a higher client fill rate. Inventory-sensitive quotes alone increased the simulated client fill rate, without improving average P&L. Hedging therefore exchanged some average revenue for reduced simulated inventory risk under these particular parameters.

The result is conditional on the assumed market paths, price acceptance function, hedge execution assumptions and inventory restrictions. Fifteen sessions are too few to support broad claims about superior market making. Median outcomes and individual sessions differ from means; the fixed-quote policy did not dominate every outcome.

## Important limitations and next validation steps

- **No real transactions or live prices.** Synthetic steps are not seconds or ticks, and prices are not executable FX quotes.
- **Invented customer-demand function.** Acceptance probability and potential customer arrivals are not calibrated to institutional RFQ data. Results may reverse under different assumptions.
- **No market impact, adverse selection, informed flow or venue execution frictions.** The market follows an exogenous price path independently of dealer actions.
- **Incomplete banking economics.** The model omits funding, carry, credit exposure, capital usage, collateral requirements, balance-sheet charges, financing and full inventory liquidation costs.
- **Risk-aware quotes are simplified.** There is no queue position, competitive counterparty order book or dynamic risk transfer.
- **Not an empirical statistical test.** Pairing random seeds improves comparability; it does not validate the market model.

For a stronger future study, estimate customer price sensitivity from permissioned order/RFQ data, stress different inventory limits and trends, and report confidence intervals over many paired scenarios. This is beyond the scope of the initial portfolio demonstration.

## Reproduction

From the repository root, install `requirements.txt`, run `python -m pytest -q`, and start `python -m streamlit run app.py`. In **Policy experiments**, use the settings above and download the comparison CSV. The figures in this report are from the code's `multi_seed_comparison` function with seeds 42–56.
