"""FX Dealer Simulator: synthetic market making and dealer-risk research."""
import plotly.graph_objects as go
import streamlit as st
from fx_engine.market import MarketConfig, SCENARIOS, generate_market
from fx_engine.orders import generate_orders
from fx_engine.quotes import make_quote
from fx_engine.risk import RiskSettings, adjusted_quote
from fx_engine.simulation import run_risk_simulation
from fx_engine.experiments import ExperimentConfig, POLICIES, compare_policies, multi_seed_comparison
import pandas as pd

st.set_page_config(page_title='FX Dealer Simulator | Research Edition', layout='wide')
st.title('FX Dealer Simulator')
st.caption('Synthetic USD/SGD dealing, inventory risk and controlled quote-policy experiments. No live execution.')

with st.sidebar:
    st.header('Market setup')
    scenario = st.selectbox('Scenario', SCENARIOS)
    initial_mid = st.number_input('Initial USD/SGD mid (SGD per USD)', 0.5, 3.0, 1.35, step=0.0001, format='%.4f')
    steps = st.slider('Simulation steps', 50, 1000, 250, step=50)
    volatility = st.slider('Step volatility (pips)', 0.0, 20.0, 5.0, step=0.5)
    spread = st.slider('Dealer spread (pips)', 0.5, 10.0, 4.0, step=0.5)
    seed = st.number_input('Random seed', 0, 1000000, 42)
    st.divider()
    st.header('Client flow')
    order_count = st.slider('Number of client orders', 1, steps, min(50, steps))
    buy_percent = st.slider('Client buy-USD probability (%)', 0, 100, 50, step=5)
    min_amount = st.number_input('Minimum USD order', min_value=1000.0, max_value=1000000.0, value=10000.0, step=1000.0)
    max_amount = st.number_input('Maximum USD order', min_value=1000.0, max_value=10000000.0, value=100000.0, step=1000.0)
    st.divider()
    st.header('Dealer risk settings')
    inventory_limit = st.number_input('Hard USD inventory limit', min_value=100000.0, max_value=50000000.0, value=1000000.0, step=100000.0)
    hedge_enabled = st.checkbox('Enable hedging after client fills', value=True)
    trigger_percent = st.slider('Hedge trigger (% of limit)', 30, 100, 70, 5)
    target_percent = st.slider('Hedge target (% of limit)', 0, trigger_percent-5, min(25,trigger_percent-5), 5)
    hedge_spread = st.slider('External hedge spread (pips)',0.0,10.0,1.0,0.5)
    vol_mult = st.slider('Volatility spread multiplier',0.0,2.0,0.0,0.1)
    skew_pips = st.slider('Inventory skew at full limit (pips)',0.0,10.0,0.0,0.5)

try:
    market = generate_market(MarketConfig(initial_mid=initial_mid, steps=steps, seed=int(seed), volatility_pips=volatility, scenario=scenario))
    orders = generate_orders(steps, order_count, int(seed) + 1, min_amount, max_amount, buy_percent / 100)
    risk_settings = RiskSettings(inventory_limit_usd=inventory_limit,
        hedge_trigger_fraction=trigger_percent/100, hedge_target_fraction=target_percent/100,
        hedge_spread_pips=hedge_spread, volatility_spread_multiplier=vol_mult, inventory_skew_pips=skew_pips)
    ledger, timeline, risk_metrics = run_risk_simulation(market, orders, spread, risk_settings,
        hedge_enabled=hedge_enabled, base_volatility_pips=volatility)
    last_mid = float(market['mid'].iloc[-1])
    quote = adjusted_quote(last_mid,spread,float(timeline.iloc[-1]["usd_inventory"]),
        float(timeline.iloc[-1]["estimated_prior_vol_pips"]),volatility,risk_settings)
except ValueError as exc:
    st.error(str(exc)); st.stop()

c1,c2,c3 = st.columns(3)
c1.metric('Dealer BID (buys USD)',f'{quote.bid:.5f}')
c2.metric('Latest synthetic mid',f'{quote.mid:.5f}')
c3.metric('Dealer ASK (sells USD)',f'{quote.ask:.5f}')
st.caption('The quote at the top is an indicative quote based on final inventory. Rejected orders do not execute. Spreads and hedge prices are simulated.')

t1,t2,t3,t4,t5 = st.tabs(['Market & client orders','Inventory & accounting','Trade ledger','Risk diagnostics','Policy experiments'])
with t1:
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=market['step'],y=market['mid'],mode='lines',name='Synthetic mid'))
    if not ledger.empty:
        filled=ledger[ledger['event']=='Client filled']
        buys=filled[filled['side']=='Client buys USD']
        sells=filled[filled['side']=='Client sells USD']
        fig.add_trace(go.Scatter(x=buys['step'], y=buys['step'].map(market.set_index('step')['mid']), mode='markers',name='Client buys USD',marker_symbol='triangle-up',marker_size=9))
        fig.add_trace(go.Scatter(x=sells['step'], y=sells['step'].map(market.set_index('step')['mid']), mode='markers',name='Client sells USD',marker_symbol='triangle-down',marker_size=9))
    fig.update_layout(title='Synthetic USD/SGD mid and client fills',xaxis_title='Simulation step (not real time)',yaxis_title='SGD per USD',height=440)
    st.plotly_chart(fig,use_container_width=True)
    with st.expander('Inspect generated market observations'):
        st.dataframe(market,hide_index=True,use_container_width=True)
        st.download_button('Download synthetic market (CSV)',market.to_csv(index=False).encode(),'synthetic_usdsgd.csv','text/csv')
with t2:
    last=timeline.iloc[-1]
    a,b,c=st.columns(3)
    a.metric('USD inventory', f"{last['usd_inventory']:,.2f} USD")
    b.metric('SGD cash', f"S${last['sgd_cash']:,.2f}")
    c.metric('Marked equity / P&L proxy', f"S${last['marked_equity_sgd']:,.2f}")
    st.caption('Marked equity = SGD cash + USD inventory × synthetic mid; includes hypothetical hedge execution prices. Excludes financing, market impact and liquidation costs. Order requests are still exogenous.')
    f1=go.Figure(); f1.add_trace(go.Scatter(x=timeline['step'],y=timeline['usd_inventory'],mode='lines',name='USD inventory'))
    f1.add_hline(y=0,line_dash='dash'); f1.update_layout(title='Dealer USD inventory',xaxis_title='Step',yaxis_title='USD',height=330)
    st.plotly_chart(f1,use_container_width=True)
    f2=go.Figure(); f2.add_trace(go.Scatter(x=timeline['step'],y=timeline['marked_equity_sgd'],mode='lines',name='Marked equity'))
    f2.add_hline(y=0,line_dash='dash'); f2.update_layout(title='Simulated marked equity',xaxis_title='Step',yaxis_title='SGD',height=330)
    st.plotly_chart(f2,use_container_width=True)
with t3:
    st.dataframe(ledger,hide_index=True,use_container_width=True)
    st.download_button('Download trade ledger (CSV)',ledger.to_csv(index=False).encode(),'fx_dealer_trade_ledger.csv','text/csv')
    st.dataframe(timeline,hide_index=True,use_container_width=True)
    st.download_button('Download step-by-step accounting (CSV)',timeline.to_csv(index=False).encode(),'fx_dealer_accounting.csv','text/csv')
with t4:
    a,b,c,d=st.columns(4)
    a.metric('Client fill rate',f"{risk_metrics['fill_rate_pct']:.1f}%")
    b.metric('Risk-limit rejections',risk_metrics['rejections'])
    c.metric('Hedge count',risk_metrics['hedges'])
    d.metric('Max drawdown',f"S${risk_metrics['max_drawdown_sgd']:,.2f}")
    a,b,c=st.columns(3)
    a.metric('Peak absolute inventory',f"US${risk_metrics['peak_abs_inventory_usd']:,.0f}")
    b.metric('Final marked P&L',f"S${risk_metrics['final_pnl_sgd']:,.2f}")
    c.metric('External hedge spread cost',f"S${risk_metrics['hedge_execution_cost_sgd']:,.2f}")
    r=go.Figure()
    r.add_trace(go.Scatter(x=timeline['step'],y=timeline['inventory_utilization_pct'],name='Inventory utilisation'))
    r.add_hline(y=100,line_dash='dash',annotation_text='Hard limit')
    r.update_layout(title='Absolute USD inventory as a share of the risk limit',xaxis_title='Step',yaxis_title='Utilisation (%)',height=350)
    st.plotly_chart(r,use_container_width=True)
    q=go.Figure()
    q.add_trace(go.Scatter(x=timeline['step'],y=timeline['quote_spread_pips'],name='Dealer spread'))
    q.update_layout(title='Spread adjustment across the session',xaxis_title='Step',yaxis_title='Pips',height=320)
    st.plotly_chart(q,use_container_width=True)
with t5:
    st.subheader('Do inventory-aware quotes improve dealer outcomes?')
    st.caption('Controlled synthetic experiments: every policy sees the same market path, client order requests and pre-generated acceptance random numbers for each seed. Actual fills differ because prices and inventory limits differ. Model assumptions are not calibrated to observed client behaviour.')
    x1,x2,x3=st.columns(3)
    with x1:
        n_sessions=st.slider('Independent synthetic sessions',5,50,15,5)
    with x2:
        baseline_prob=st.slider('Baseline client quote acceptance (%)',20,95,75,5)
    with x3:
        price_sensitivity=st.slider('Client sensitivity to quote (per pip)',0.0,1.5,0.4,0.1)
    exp_config=ExperimentConfig(market=MarketConfig(initial_mid=initial_mid,steps=steps,
                                seed=int(seed),volatility_pips=volatility,scenario=scenario),
                                order_count=order_count,buy_probability=buy_percent/100,
                                min_order_usd=min_amount,max_order_usd=max_amount,
                                dealer_spread_pips=spread,inventory_limit_usd=inventory_limit,
                                inventory_skew_pips=skew_pips,hedge_spread_pips=hedge_spread,
                                hedge_trigger_fraction=trigger_percent/100,
                                hedge_target_fraction=target_percent/100,
                                acceptance_baseline=baseline_prob/100,
                                acceptance_sensitivity=price_sensitivity)
    runs=compare_policies(exp_config,int(seed))
    metrics_df=pd.DataFrame([m for _,_,m in runs.values()])
    st.markdown('**Single-session comparison**')
    st.dataframe(metrics_df[['policy','final_pnl_sgd','max_drawdown_sgd','peak_inventory_usd','fill_rate_pct','hedge_count','hedge_cost_sgd','limit_rejections','customer_declines']].round(2),hide_index=True,use_container_width=True)
    fig=go.Figure()
    for policy,(_,t,_) in runs.items():
        fig.add_trace(go.Scatter(x=t['step'],y=t['marked_pnl_sgd'],mode='lines',name=policy))
    fig.update_layout(title='Marked P&L by policy: same synthetic market and client opportunities',xaxis_title='Simulation step',yaxis_title='SGD',height=380)
    st.plotly_chart(fig,use_container_width=True)
    fig_inv=go.Figure()
    for policy,(_,t,_) in runs.items():
        fig_inv.add_trace(go.Scatter(x=t['step'],y=t['usd_inventory'],mode='lines',name=policy))
    fig_inv.update_layout(title='Inventory by policy',xaxis_title='Simulation step',yaxis_title='USD',height=330)
    st.plotly_chart(fig_inv,use_container_width=True)
    st.markdown('**Multiple-session robustness check**')
    with st.spinner('Running paired policy comparisons...'):
        samples,summary=multi_seed_comparison(exp_config,int(seed),n_sessions)
    st.dataframe(summary.round(2),hide_index=True,use_container_width=True)
    st.caption('Mean P&L and drawdown compare absolute simulated SGD amounts. No live execution or forecasting claims; order-arrival and price-acceptance models are hypothetical. The same candidate requests and random numbers are reused within each seed, while subsequent actual fills remain policy-dependent.')
    st.download_button('Download session-level comparison CSV',samples.to_csv(index=False).encode(),'fx_policy_comparison.csv','text/csv')
    st.download_button('Download summary CSV',summary.to_csv(index=False).encode(),'fx_policy_summary.csv','text/csv')
    with st.expander('Model and methodological limitations'):
        st.write('Each potential client request has an independent acceptance draw. Acceptance probability decreases with the client\'s worse quote relative to the synthetic mid. The shared draws are a variance-reduction device, not an empirical model of clients. No market impact, adverse selection, dynamic order arrival, financing, venue fees or capital charges are modelled. Inventory hedges execute at an assumed external half-spread. All marked P&L is synthetic SGD equity from zero initial holdings.')

st.info('Research simulator only. Prices, order arrivals, client acceptance and execution are synthetic; results are not evidence of live trading profitability.')
