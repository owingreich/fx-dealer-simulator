# Methodology and validation

## Scope and evidence

This study evaluates a deterministic implementation of a **synthetic** USD/SGD dealer simulator. The input files are eight CSVs from the corrected `Reports(1).zip` supplied on 24 November 2026. The code used for reconciliation is the locally available final release of `fx_engine/experiments.py`, `market.py`, `orders.py`, `quotes.py`, `risk.py` and `dealer.py`. No live bank quotes, actual RFQs, executable interdealer prices or real trading records are used.

## Reconstructed configuration (verified by full numerical reproduction)

| Parameter | Setting |
|---|---|
| Currency convention | USD/SGD = SGD per USD; 1 pip = SGD 0.0001 per USD |
| Synthetic session | 250 steps; initial mid 1.3500 |
| Market noise | Gaussian additive changes, standard deviation 5 pips/step |
| Scenarios | Calm; +0.8 pip/step drift; -0.8 pip/step drift; middle-third volatility x3 |
| Seeds | 42 through 91; 50 paired sessions for each scenario |
| Potential client requests | 50 per session; 50% request to buy USD |
| Request sizes | Uniform synthetic US$10,000 to US$100,000 |
| Dealer base spread | 4 pips, full bid-ask |
| Max inventory | US$100,000 absolute |
| Inventory quote skew | 2 pips at full inventory limit |
| Hedge trigger and target | 70% and 25% of inventory limit |
| External hedge spread | 1 pip total, with half-spread cost on each executed hedge |
| Baseline client acceptance | 75%; logistic price sensitivity 0.4 per pip |
| Policies | Fixed quotes; inventory-aware quotes; inventory-aware + hedging |

The CSVs do **not** store the complete configuration. These values are reconstructed by matching the corrected CSV rows against outputs of the final Python engine, using the settings above. Reproduction is exact to normal floating-point error. A future application improvement would export configuration metadata with every experiment.

## Market and client generation

For synthetic mid-price S at step t, `S[t] = S[t-1] + 0.0001 * noise[t]`, with scenario-dependent drift and volatility. The shock scenario multiplies the **entire** generated change (including drift, which is zero for the shock scenario) by three for the middle third of a session. These are artificial price paths and the step unit is **not** a specified real-world interval.

For a given seed, all policies face the same synthetic path, potential request order, request size and independent acceptance uniform. Each proposed client request has one side and quantity and occurs at a distinct step. This paired design reduces variation when comparing policies, but final fills differ between policies.

## Quotes and client acceptance

Fixed quotes are centred on the current synthetic mid-price with a 4-pip full spread. Inventory-aware policies shift the quote centre by `-2 pips * (USD inventory / US$100,000)`: a long USD inventory shifts both quotes downward; a short USD inventory shifts them upward.

Client acceptance is a **hypothetical** logistic function. Relative to a base half-spread of 2 pips, a worse client quote reduces the acceptance probability. At a 2-pip concession the model sets acceptance to 75%; the log-odds change by -0.4 per additional pip of concession. The customer decision is drawn before inventory-limit rejection.

## Inventory, cash, P&L and hedging

A client purchasing USD from the dealer decreases the dealer's USD inventory and increases its SGD cash at the dealer ask. A client selling USD to the dealer increases USD inventory and decreases SGD cash at the dealer bid. The dealer starts at zero inventory and zero cash.

`Marked equity (SGD) = SGD cash + USD inventory * synthetic mid`

`Final marked P&L proxy = marked equity at the last simulated step`

This is a **mark-to-mid accounting proxy**, not net liquidation proceeds. The final position is not necessarily flat; financing, capital charges, adverse selection, market impact and end-of-session liquidation costs are omitted.

The hedge policy, after processing client interest at each step, moves the inventory toward 25% of the limit whenever absolute inventory exceeds 70% of the limit. External hedges execute at the mid plus an adverse half-spread of 0.5 pip for buys, or minus 0.5 pip for sells; this cost is already reflected in SGD cash and marked P&L and must **not** be subtracted a second time. `hedge_cost_sgd` is a separate diagnostic of the embedded spread expense.

## Risk metrics

Max drawdown is the largest decline in marked equity from its running peak, with zero included as an initial high-water mark. Peak inventory is the maximum absolute USD inventory in a session; mean peak inventory is the mean of those 50 peak values. Fill rate is filled client requests / 50 possible requests. Worst-session P&L is the minimum observed final marked P&L among the 50 runs. These are synthetic accounting statistics rather than an institutional VaR or executable return series.

## Verification against user exports

- Four scenario exports; each contains 150 session-policy rows = 50 seeds x 3 policies. Across all scenarios: **600 rows**.
- All eight files present: four session CSVs and four summary CSVs. No missing fields in session tables.
- Seed coverage 42-91 is identical in each scenario.
- Re-running `multi_seed_comparison` with the reconstructed settings reproduces every numeric session column to within **2.4e-10** in original numeric units, which is floating-point precision.
- Exported aggregate summaries also reconcile with recomputed grouped values.

This checks **consistency between the supplied outputs and the implementation**, not whether its synthetic assumptions resemble real FX markets. Code-level tests passing does not establish realistic empirical calibration.

## Important design limitations

1. Market scenarios change prices but not the client request process. Under these parameters, per-policy fills, inventory and hedging expenses are identical across the four scenarios for each seed. Market changes affect the mark-to-mid P&L and drawdown. This substantially limits what can be inferred about trading in volatile markets.
2. The Policy Experiments engine does not apply the separate sidebar's volatility-spread multiplier, so it does not simulate automatic spread widening under volatility shocks.
3. The model does not include informed traders, adverse selection, market impact, order-book queueing, quote competition, variable interdealer liquidity, carry, inventory financing or default risk.
4. The fixed random-seed sweep represents synthetic repeated samples, not independent historical trading days.
5. Client demand and the quote-response function are assumed, not estimated from institutional RFQ data. Results could change materially with another acceptance rule.
6. The parameter choices and scenarios were reviewed during development, so there is no pristine out-of-sample holdout.

## Reproduction instructions

At the repository root run `python -m pytest -q`; then run `python -m streamlit run app.py`. Under Policy experiments, use the table above and export each scenario using 50 sessions, starting at random seed 42. The data used here are in `reports/data/`.
