# KOSPI Round-Number Sell-Side Sidecar Risk Model

This module models the hypothesis that large index round numbers create order-flow clustering and volatility amplification, then connects that signal to a sell-side sidecar risk score.

## Important distinction

KRX sidecar is not triggered by the KOSPI spot index touching a 1,000-point level. For KOSPI, the official trigger is when the KOSPI200 futures price changes by 5% or more from the base price and the move lasts for one minute. The round-number model is therefore a **risk feature**, not the legal trigger itself.

## Model structure

### 1. Round-number distance

For index level `S_t` and barrier interval `B`, e.g. KOSPI 1000, S&P 500 500, Nasdaq 100 1000:

```text
nearest_barrier = round(S_t / B) * B
round_distance = |S_t - nearest_barrier| / nearest_barrier
signed_distance_to_upper = (ceil(S_t / B) * B - S_t) / S_t
```

### 2. Physical barrier pressure

```text
Phi_t = sum_k exp(-0.5 * ((S_t - B_k) / (w * B_k))^2)
```

where `w` is the barrier width, normally 1% to 3%.

### 3. Damped barrier dynamics

```text
dx_t = mu_t dt - dV(x)/dx dt - gamma v_t dt + sigma_t dW_t + J_t
V(x) = sum_k A_k exp(-0.5 * ((x - B_k) / w_k)^2)
```

The model treats round numbers as soft potential barriers. They do not cause crashes by themselves. They can amplify moves when combined with high volatility, negative futures pressure, and concentrated program trading.

### 4. Sell-side sidecar hazard

```text
P(sidecar_next_day) = sigmoid(
    beta0
  + beta1 * round_pressure
  + beta2 * realized_vol_5d
  + beta3 * gap_down
  + beta4 * drawdown_from_20d_high
  + beta5 * futures_return_proxy
  + beta6 * volume_zscore
)
```

With true intraday KOSPI200 futures data, the label should be:

```text
1 if KOSPI200 futures <= -5% from base price for >= 1 minute, else 0
```

With daily public data only, use a proxy label such as next-day return below `-4%` or realized intraday low below `-5%` if OHLC data are available.

## Files

- `round_number_sidecar_model.py` — research/backtest script with synthetic fallback data.
- `streamlit_app.py` — dashboard and daily risk monitor.
- `requirements.txt` — Python dependencies.

## Suggested workflow

```bash
cd quant/round_number_sidecar
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python round_number_sidecar_model.py --ticker ^KS11 --barrier 1000 --name KOSPI
streamlit run streamlit_app.py
```

For cross-market comparison:

```bash
python round_number_sidecar_model.py --ticker ^GSPC --barrier 500 --name SP500
python round_number_sidecar_model.py --ticker ^NDX --barrier 1000 --name NASDAQ100
```

## Interpretation rule

Use the result as a warning system:

- `0.00 - 0.30`: normal
- `0.30 - 0.55`: watch zone
- `0.55 - 0.75`: high-volatility warning
- `0.75+`: sell-side stress regime; reduce aggressive rebalance orders and wait for confirmation

## Research notes

The hypothesis is testable by comparing event windows near round numbers against matched non-round windows with similar volatility, trend, and macro conditions. The key test is whether `round_pressure` remains significant after controlling for volatility and momentum.
