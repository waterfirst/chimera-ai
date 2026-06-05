"""
Round-number sell-side sidecar risk model.

This script is designed as a research/backtest tool. It can download market data
through yfinance when internet access is available. If download fails, it creates
synthetic data so that the full pipeline and dashboard logic can still be tested.

The model separates three ideas:
1. Round-number barrier pressure: distance to psychological index levels.
2. Volatility / drawdown state: market stress context.
3. Sidecar proxy probability: daily approximation unless true KOSPI200 futures
   intraday data are provided.

Author: generated for waterfirst/chimera-ai
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


@dataclass
class ModelConfig:
    ticker: str = "^KS11"
    name: str = "KOSPI"
    barrier: int = 1000
    barrier_width: float = 0.025
    start: str = "2000-01-01"
    proxy_drop_threshold: float = -0.04
    output_dir: str = "outputs"


def sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


def load_market_data(config: ModelConfig) -> pd.DataFrame:
    """Load OHLCV data. Falls back to synthetic data if online download fails."""
    if yf is not None:
        try:
            data = yf.download(config.ticker, start=config.start, auto_adjust=False, progress=False)
            if data is not None and len(data) > 200:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                data = data.rename(columns=str.title)
                return data[["Open", "High", "Low", "Close", "Volume"]].dropna()
        except Exception as exc:
            print(f"[WARN] yfinance download failed; using synthetic data. Reason: {exc}")

    return make_synthetic_market_data(config)


def make_synthetic_market_data(config: ModelConfig, n: int = 1500, seed: int = 7) -> pd.DataFrame:
    """Create data with soft round-number barrier effects for pipeline testing."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    level = 2500 if config.name.upper() == "KOSPI" else 4500
    close = []
    vol = []
    for i in range(n):
        nearest = round(level / config.barrier) * config.barrier
        dist = abs(level - nearest) / max(nearest, 1)
        pressure = np.exp(-0.5 * (dist / config.barrier_width) ** 2)
        shock = rng.normal(0.00035, 0.011 + 0.012 * pressure)
        if pressure > 0.65 and rng.random() < 0.035:
            shock += rng.normal(-0.045, 0.02)
        level *= 1 + shock
        close.append(level)
        vol.append(1_000_000 * (1 + 4 * pressure + rng.lognormal(0, 0.5)))
    close = pd.Series(close, index=dates)
    data = pd.DataFrame(index=dates)
    data["Close"] = close
    data["Open"] = close.shift(1).fillna(close.iloc[0]) * (1 + rng.normal(0, 0.004, n))
    data["High"] = np.maximum(data["Open"], data["Close"]) * (1 + rng.random(n) * 0.01)
    data["Low"] = np.minimum(data["Open"], data["Close"]) * (1 - rng.random(n) * 0.012)
    data["Volume"] = vol
    return data.dropna()


def add_features(data: pd.DataFrame, config: ModelConfig) -> pd.DataFrame:
    df = data.copy()
    df["ret_1d"] = df["Close"].pct_change()
    df["ret_5d"] = df["Close"].pct_change(5)
    df["realized_vol_5d"] = df["ret_1d"].rolling(5).std() * np.sqrt(252)
    df["realized_vol_20d"] = df["ret_1d"].rolling(20).std() * np.sqrt(252)
    df["drawdown_20d"] = df["Close"] / df["Close"].rolling(20).max() - 1
    df["volume_zscore"] = (df["Volume"] - df["Volume"].rolling(20).mean()) / df["Volume"].rolling(20).std()

    nearest = (df["Close"] / config.barrier).round() * config.barrier
    upper = np.ceil(df["Close"] / config.barrier) * config.barrier
    lower = np.floor(df["Close"] / config.barrier) * config.barrier

    df["nearest_barrier"] = nearest
    df["distance_to_nearest"] = (df["Close"] - nearest).abs() / nearest.replace(0, np.nan)
    df["distance_to_upper"] = (upper - df["Close"]) / df["Close"]
    df["distance_to_lower"] = (df["Close"] - lower) / df["Close"]
    df["round_pressure"] = np.exp(-0.5 * (df["distance_to_nearest"] / config.barrier_width) ** 2)

    # Energy-like variables for the physical analogy.
    df["kinetic_energy"] = 0.5 * (df["ret_5d"] / df["realized_vol_20d"].replace(0, np.nan)) ** 2
    df["potential_energy"] = df["round_pressure"]
    df["barrier_reflection_score"] = sigmoid(2.5 * df["potential_energy"] + 1.2 * df["realized_vol_5d"] + 8 * (-df["ret_1d"]))

    # Daily proxy label. Replace with actual intraday futures sidecar labels when available.
    df["sidecar_proxy_next_day"] = (df["ret_1d"].shift(-1) <= config.proxy_drop_threshold).astype(int)
    return df.dropna()


def fit_sidecar_proxy_model(df: pd.DataFrame) -> tuple[Pipeline, dict]:
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
    X = df[features].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = df["sidecar_proxy_next_day"].astype(int)

    # If labels are too rare, logistic regression can fail. Add a clear warning.
    if y.nunique() < 2 or y.sum() < 5:
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ])
        model.fit(X, np.where(np.arange(len(y)) % 97 == 0, 1, y))
        return model, {"warning": "Proxy crash labels are too rare; model fitted with sparse synthetic positives for plumbing test."}

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    aucs = []
    tscv = TimeSeriesSplit(n_splits=5)
    for train_idx, test_idx in tscv.split(X):
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        proba = model.predict_proba(X.iloc[test_idx])[:, 1]
        if y.iloc[test_idx].nunique() > 1:
            aucs.append(roc_auc_score(y.iloc[test_idx], proba))

    model.fit(X, y)
    p = model.predict_proba(X)[:, 1]
    pred = (p >= 0.5).astype(int)
    report = classification_report(y, pred, output_dict=True, zero_division=0)

    clf = model.named_steps["clf"]
    coefs = dict(zip(features, clf.coef_[0].round(4).tolist()))
    metrics = {
        "time_series_cv_auc_mean": float(np.mean(aucs)) if aucs else None,
        "time_series_cv_auc_values": [float(v) for v in aucs],
        "in_sample_auc": float(roc_auc_score(y, p)) if y.nunique() > 1 else None,
        "classification_report": report,
        "coefficients": coefs,
        "positive_rate": float(y.mean()),
        "n_rows": int(len(df)),
    }
    return model, metrics


def calculate_today_risk(df: pd.DataFrame, model: Pipeline) -> dict:
    latest = df.iloc[-1]
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
    x = latest[features].to_frame().T.replace([np.inf, -np.inf], np.nan).fillna(0)
    prob = float(model.predict_proba(x)[0, 1])
    level = "normal"
    if prob >= 0.75:
        level = "stress"
    elif prob >= 0.55:
        level = "warning"
    elif prob >= 0.30:
        level = "watch"
    return {
        "date": str(df.index[-1].date()),
        "close": float(latest["Close"]),
        "nearest_barrier": float(latest["nearest_barrier"]),
        "distance_to_nearest_pct": float(latest["distance_to_nearest"] * 100),
        "round_pressure": float(latest["round_pressure"]),
        "realized_vol_5d": float(latest["realized_vol_5d"]),
        "drawdown_20d_pct": float(latest["drawdown_20d"] * 100),
        "sidecar_proxy_probability": prob,
        "risk_level": level,
    }


def run(config: ModelConfig) -> dict:
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = load_market_data(config)
    df = add_features(data, config)
    model, metrics = fit_sidecar_proxy_model(df)
    today = calculate_today_risk(df, model)

    df.to_csv(out / f"{config.name.lower()}_features.csv")
    result = {
        "config": asdict(config),
        "today": today,
        "metrics": metrics,
        "note": "Use true KOSPI200 futures intraday labels for production sidecar prediction. Daily label is only a stress proxy.",
    }
    (out / f"{config.name.lower()}_model_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def parse_args() -> ModelConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="^KS11")
    parser.add_argument("--name", default="KOSPI")
    parser.add_argument("--barrier", type=int, default=1000)
    parser.add_argument("--barrier-width", type=float, default=0.025)
    parser.add_argument("--start", default="2000-01-01")
    parser.add_argument("--proxy-drop-threshold", type=float, default=-0.04)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    return ModelConfig(
        ticker=args.ticker,
        name=args.name,
        barrier=args.barrier,
        barrier_width=args.barrier_width,
        start=args.start,
        proxy_drop_threshold=args.proxy_drop_threshold,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    run(parse_args())
