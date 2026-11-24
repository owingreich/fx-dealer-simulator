# FX Dealer Simulator

**Python research project exploring USD/SGD dealer quoting, customer order flow, inventory exposure, and market-making risk.**

This is a **synthetic educational simulation**. It is not a trading application, live price feed, calibrated institutional market model or evidence of executable profitability.

## What it does

- Creates repeatable USD/SGD mid-price scenarios: calm markets, USD appreciation/depreciation trends and volatility shocks.
- Generates hypothetical client requests to buy or sell USD and derives dealer bid/ask prices.
- Records accepted simulated trades, dealer USD inventory, SGD cash and marked equity.
- Enforces inventory limits, optionally hedges externally at an assumed spread and tracks risk metrics.
- Evaluates three policies under paired simulated scenarios: fixed quotes, inventory-aware quotes, and inventory-aware quotes with hedging.
- Compares client acceptance, fills, drawdowns, inventory exposure and synthetic marked P&L.

The Streamlit app has five tabs: **Market & client orders**, **Inventory & accounting**, **Trade ledger**, **Risk diagnostics**, and **Policy experiments**.

## Research Reports

- [FX Market-Making Research Report (PDF)](reports/FX_Market_Making_Research_Report.pdf)
- [Market-Making Policy Comparison](reports/findings.md)
- [Scenario and Risk Analysis](reports/scenario_analysis.md)
- [Methodology and Validation](reports/methodology_and_validation.md)

## Quick start

Requires Python 3.12 or 3.13.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Run `python -m pytest -q` after changes to validate the core simulation and accounting rules. The baseline release contains **29 passing tests**.

## Findings

A 15-session synthetic experiment compared the three policies using identical potential market moves and client-order opportunities within each seed. In this selected setting, external hedging reduced average drawdown and inventory exposure but also reduced mean simulated marked P&L relative to fixed quotes.

See **[Research findings and reproducible parameter settings](reports/findings.md)** for full results, all assumptions, a one-session example and limitations. Please do not interpret a profitable synthetic sample as evidence of a real FX trading edge.

## Architecture

```text
app.py                  Streamlit interface
fx_engine/market.py     Synthetic reference market
fx_engine/orders.py     Potential client order generation
fx_engine/quotes.py     Two-way FX bid/ask quotations
fx_engine/dealer.py     USD/SGD accounting and execution
fx_engine/risk.py       Inventory-based quotes and hedging settings
fx_engine/simulation.py  Single-policy accounting/risk simulation
fx_engine/experiments.py Paired policy experiments and multi-seed comparison
tests/                  Automated invariants and regression tests
reports/findings.md     Results and methodology
```

## Core conventions

- The FX quotation is **SGD per USD**. One pip is **0.0001 SGD per USD**.
- The dealer **buys USD at the bid** and **sells USD at the ask**.
- A client buy-USD fill makes dealer USD inventory more negative; a client sell-USD fill makes it more positive.
- Marked equity from a zero-initial-balance book is `SGD cash + USD inventory × synthetic mid`, excluding full real-world funding and liquidation costs.
- Quoted prices change with current inventory under the inventory-aware policy; client acceptance is a **hypothetical** function of quote attractiveness, not estimated from client data.

## Research limitations

No live FX prices, real client executions, market impact, dealer competition, order-book liquidity, funding, carry, settlement risk, credit charges, balance-sheet constraints or calibrated client acceptance. Synthetic market steps do not represent fixed real-world clock intervals. No brokerage connection is implemented. See the research report for further detail.

## Portfolio demonstration

1. Change the market scenario and volatility in the sidebar.
2. Inspect dealer bid/ask and client transaction outcomes.
3. Review USD inventory, cash and risk diagnostics.
4. Compare the three policies in **Policy experiments**, keeping the same seed and scenario.
5. Vary the hedge trigger, inventory skew or client price sensitivity to explore trade-offs, then download the CSV results.

All outputs are illustrative and should be described as simulations.
