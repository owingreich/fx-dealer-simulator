# Market-Making Policy Comparison

## Research question

Under the simulator's synthetic USD/SGD market and customer-acceptance assumptions, how do fixed quotes, inventory-aware quotes and inventory-aware quoting with external hedging compare on marked P&L, client fill rates and inventory risk?

## Executive findings

- In 50 calm-market sessions, fixed quotes produced the highest mean marked P&L proxy: **S$297.24**, compared with **S$241.63** for inventory-sensitive quotes and **S$251.78** for inventory-aware quoting with hedging.
- The hedged policy reduced mean maximum drawdown from **S$430.31** to **S$264.74** (**38.5%** lower) and mean session peak inventory from **US$95,006** to **US$67,009** (**29.5%** lower).
- Relative to fixed quotes, hedging had lower maximum drawdown in **92%** of matched calm sessions, but higher final P&L in only **42%**. The strategy's value is chiefly its **inventory risk reduction**, not consistently superior simulated profits.
- All figures describe synthetic, mark-to-mid outcomes. No inference of live dealer profitability or causal real-market performance is justified.

## Baseline design

Four-pip USD/SGD full spread; US$100,000 inventory limit; two-pip skew at the limit; 1-pip external hedge spread; hedging triggered at 70% and returned to 25% of limit; 50 potential requests per 250-step session; 75% baseline acceptance with sensitivity 0.4/pip; seeds 42-91. See [full methodology](methodology_and_validation.md).

## Baseline results: 50 paired sessions

| Policy | Mean P&L (S$) | Median (S$) | Worst (S$) | Positive sessions | Mean max DD (S$) | Peak inv. (US$) | Fill rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fixed | 297.24 | 240.61 | -587.54 | 74% | 430.31 | 95,006 | 55.12% |
| Skew | 241.63 | 209.95 | -624.17 | 72% | 418.90 | 94,767 | 58.04% |
| Skew + hedge | 251.78 | 279.49 | -232.90 | 76% | 264.74 | 67,009 | 62.40% |

All P&L and drawdown figures are SGD; inventory is USD. **Mean max DD** means the mean of per-session maximum drawdowns, not the maximum loss across all sessions. A positive marked P&L is not a realised, fully liquidated net return.

## Paired policy differences

| Compared with fixed | Mean delta P&L (S$) | Paired sessions with higher P&L | Mean delta drawdown (S$) | Sessions with lower drawdown |
| --- | ---: | ---: | ---: | ---: |
| Skew | -55.61 | 34% | -11.41 | 44% |
| Skew + hedge | -45.46 | 42% | -165.57 | 92% |

The paired comparison uses the same random seeds and customer opportunities within each scenario. Negative P&L or drawdown differences mean the alternative policy is lower than fixed quotes. A negative drawdown difference is generally preferable; a negative P&L difference is not.

Inventory-aware quoting increased average client fill rates from **55.12%** to **58.04%**, but the mean marked P&L fell by **S$55.61** per simulated session. Adding hedging increased fill rates to **62.40%** while the average recorded external hedge spread expense was **S$19.65** per session. This cost is already included in marked P&L and must not be deducted again.

## Interpretation

The policy with the highest average simulated marked P&L does not have the smallest drawdown. In these artificial sessions, the hedged policy produced lower inventory exposure and a less adverse worst session, while fixed quoting had the highest average terminal marked equity. This is compatible with a risk/revenue trade-off, but the precise values are driven by the assumed customer-price sensitivity, request sizes, market paths and execution costs.

The hedged policy's higher fill rate arises from its ability to reduce inventory and subsequently accommodate additional client requests under the hard limit. The simulator does not model actual institutional RFQ competition or flow toxicity, so the result is not an empirical liquidity-quality measurement.

## Questions left open

- Would the ranking hold with larger independent samples or realistically calibrated client acceptance?
- How would adding adverse selection, financing, market impact and terminal liquidation costs affect the P&L distribution?
- How sensitive are conclusions to the skew coefficient, hedge threshold, spread and maximum inventory?

## Evidence and reproducibility

Data: [`data/baseline_sessions.csv`](data/baseline_sessions.csv) and [`data/baseline_summary.csv`](data/baseline_summary.csv). Additional scenarios: [Scenario Analysis](scenario_analysis.md). Exact data provenance and calculations: [Methodology and Validation](methodology_and_validation.md).
