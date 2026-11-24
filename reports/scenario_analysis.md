# Scenario and Risk Stress Analysis

## Objective

Determine whether the relative performance of the three quoted policies changes when the synthetic USD/SGD mid-rate follows a calm process, rising drift, falling drift or a temporary volatility shock. The same 50 seeds (42-91), quote policy settings and potential client requests are used in each scenario.

## Scenario definitions

- **Calm:** zero drift, Gaussian step noise with 5-pip standard deviation.
- **Trending USD up:** +0.8-pip mean step change with 5-pip Gaussian standard deviation.
- **Trending USD down:** -0.8-pip mean step change with 5-pip Gaussian standard deviation.
- **Volatility shock:** no drift, but the synthetic step noise in the middle third of the 250-step session is multiplied by three.

These are not calibrated historical regimes. The prices are exogenous; they do not react to customer transactions or dealer hedging.

## Cross-scenario findings

| Scenario | Policy | Mean P&L (S$) | Mean max DD (S$) | Worst P&L (S$) | Positive sessions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Calm | Fixed | 297.24 | 430.31 | -587.54 | 74% |
| Calm | Skew | 241.63 | 418.90 | -624.17 | 72% |
| Calm | Skew + hedge | 251.78 | 264.74 | -232.90 | 76% |
| Trending USD up | Fixed | 358.37 | 540.58 | -1,582.92 | 70% |
| Trending USD up | Skew | 307.23 | 510.32 | -983.53 | 68% |
| Trending USD up | Skew + hedge | 263.28 | 302.80 | -311.03 | 78% |
| Trending USD down | Fixed | 236.10 | 507.98 | -933.18 | 64% |
| Trending USD down | Skew | 176.02 | 481.75 | -860.91 | 66% |
| Trending USD down | Skew + hedge | 240.28 | 307.95 | -519.97 | 76% |
| Volatility shock | Fixed | 385.66 | 896.16 | -1,832.12 | 66% |
| Volatility shock | Skew | 329.25 | 857.92 | -1,149.79 | 68% |
| Volatility shock | Skew + hedge | 273.41 | 595.40 | -699.99 | 72% |


Across **all four** scenarios, the hedged policy has the lowest mean maximum drawdown and mean peak inventory. Its reduction in mean maximum drawdown versus fixed quoting is **38.5%** in calm markets, **44.0%** in rising USD markets, **39.4%** in falling USD markets and **33.6%** under the volatility shock.

The hedged policy does **not** consistently maximise final marked P&L. It is slightly ahead of fixed quoting under falling USD (**S$240.28** versus **S$236.10**), but behind fixed quotes in the other three conditions. These differences are sample- and model-dependent.

The volatility-shock scenario has materially larger average maximum drawdowns than calm conditions for all three policies. For example, fixed quoting increases from **S$430.31** to **S$896.16**, even though its average marked P&L is positive in both samples. Drawdown measures the path-dependent downside, not simply the terminal result.

## Model-design finding: mechanically unchanged fills

Average fill rates are identical **across all four scenarios** for each policy (fixed **55.12%**, inventory-aware **58.04%**, hedged **62.40%**). Average peak inventory and external hedge cost are also identical across scenarios. This is not proof that FX dealer flow is insensitive to volatility. It happens because customer orders, quote concessions relative to the mid, acceptance uniforms and hard inventory rules are unchanged when the exogenous price path changes.

**Consequently, this stress test examines mark-to-market exposure conditional on unchanged simulated flow.** It does not model crisis-time spreads, changing client demand, informed flow, bid/ask competition or worsening hedge liquidity.

## Limitations and next research steps

This is a controlled engineering comparison, not a statistically validated live strategy. A stronger desk-style follow-up would stress the acceptance curve and order-size distribution, widen both client and interdealer spreads in volatile periods, impose execution delays and terminal liquidation, and compare risk-adjusted P&L using more seeds and realistic market calibration. Do not treat the present 50-seed output as proof of robust policy superiority.

## Data

- [Calm sessions](data/baseline_sessions.csv) · [summary](data/baseline_summary.csv)
- [Trending USD up sessions](data/usd_up_sessions.csv) · [summary](data/usd_up_summary.csv)
- [Trending USD down sessions](data/usd_down_sessions.csv) · [summary](data/usd_down_summary.csv)
- [Volatility shock sessions](data/volatility_shock_sessions.csv) · [summary](data/volatility_shock_summary.csv)

Detailed definitions and reproducibility: [Methodology and Validation](methodology_and_validation.md).
