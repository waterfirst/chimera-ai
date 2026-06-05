from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from round_number_sidecar_model import ModelConfig, add_features, fit_sidecar_proxy_model, load_market_data, calculate_today_risk


st.set_page_config(page_title="Round-Number Sidecar Risk", layout="wide")
st.title("KOSPI Round-Number Sell-Side Sidecar Risk Monitor")

st.markdown(
    """
This dashboard tests whether index round numbers act as volatility-amplifying soft barriers.
For KOSPI, this is a **risk feature**, not the official sidecar trigger. Production use requires KOSPI200 futures intraday data.
"""
)

with st.sidebar:
    preset = st.selectbox("Market preset", ["KOSPI", "S&P500", "NASDAQ100"])
    if preset == "KOSPI":
        ticker, barrier = "^KS11", 1000
    elif preset == "S&P500":
        ticker, barrier = "^GSPC", 500
    else:
        ticker, barrier = "^NDX", 1000
    ticker = st.text_input("Ticker", ticker)
    barrier = st.number_input("Barrier interval", min_value=100, max_value=10000, value=barrier, step=100)
    width = st.slider("Barrier width", min_value=0.005, max_value=0.08, value=0.025, step=0.005)
    start = st.text_input("Start date", "2000-01-01")
    threshold = st.slider("Daily proxy crash label", min_value=-0.10, max_value=-0.02, value=-0.04, step=0.005)
    run_button = st.button("Run model")

if run_button:
    cfg = ModelConfig(ticker=ticker, name=preset, barrier=int(barrier), barrier_width=width, start=start, proxy_drop_threshold=threshold)
    data = load_market_data(cfg)
    df = add_features(data, cfg)
    model, metrics = fit_sidecar_proxy_model(df)
    today = calculate_today_risk(df, model)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Close", f"{today['close']:,.2f}")
    c2.metric("Nearest barrier", f"{today['nearest_barrier']:,.0f}")
    c3.metric("Distance", f"{today['distance_to_nearest_pct']:.2f}%")
    c4.metric("Risk", f"{today['sidecar_proxy_probability']:.1%}", today["risk_level"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close"))
    min_b = int(np.floor(df["Close"].min() / cfg.barrier) * cfg.barrier)
    max_b = int(np.ceil(df["Close"].max() / cfg.barrier) * cfg.barrier)
    for b in range(min_b, max_b + cfg.barrier, cfg.barrier):
        fig.add_hline(y=b, line_dash="dash", opacity=0.25)
    fig.update_layout(title="Index level and round-number barriers", height=450)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df["round_pressure"], mode="lines", name="Round pressure"))
    fig2.add_trace(go.Scatter(x=df.index, y=df["barrier_reflection_score"], mode="lines", name="Reflection score"))
    fig2.update_layout(title="Physical barrier scores", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    features = [
        "round_pressure",
        "distance_to_nearest",
        "realized_vol_5d",
        "realized_vol_20d",
        "ret_1d",
        "ret_5d",
        "drawdown_20d",
        "volume_zscore",
        "barrier_reflection_score",
    ]
    proba = model.predict_proba(df[features].replace([np.inf, -np.inf], np.nan).fillna(0))[:, 1]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df.index, y=proba, mode="lines", name="Sidecar proxy probability"))
    fig3.add_hline(y=0.30, line_dash="dot")
    fig3.add_hline(y=0.55, line_dash="dash")
    fig3.add_hline(y=0.75, line_dash="dash")
    fig3.update_layout(title="Sell-side stress probability", height=350, yaxis_tickformat=".0%")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Model metrics")
    st.json(metrics)

    result = {"today": today, "metrics": metrics, "config": cfg.__dict__}
    st.download_button("Download model result JSON", json.dumps(result, ensure_ascii=False, indent=2), file_name="round_number_sidecar_result.json")
else:
    st.info("Choose a preset and press Run model.")
