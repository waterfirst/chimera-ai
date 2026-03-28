#!/usr/bin/env python3
"""
Navier-Stokes Capital Flow Prediction System
Based on: "Capital as a Viscous Fluid" (Nakcho Choi, 2026)

∂u/∂t + (u·∇)u = -(1/ρ)∇p + ν∇²u + f

Variables:
  u = Capital Flow Velocity (VWAP delta / foreign net purchases)
  ρ = Capital Density (semiconductor sector weight in KOSPI)
  p = Pressure (Forward P/E ratio)
  ν = Viscosity (bid-ask spread proxy → volatility)
  f = External Force (VIX, Fed rate, geopolitical)
  Re_financial = (Capital Velocity × Market Depth) / Market Friction
"""

import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# --- Korean font setup ---
matplotlib.rcParams['font.family'] = 'NanumSquare'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. DATA FETCHING (Free APIs only)
# ============================================================

def fetch_market_data():
    """Fetch real-time market data via yfinance (free)"""
    end = datetime.now()
    start_1y = end - timedelta(days=365)
    start_3m = end - timedelta(days=90)

    print("[1/5] VIX 데이터 수집...")
    vix = yf.download("^VIX", start=start_1y, end=end, progress=False)

    print("[2/5] KOSPI 데이터 수집...")
    kospi = yf.download("^KS11", start=start_1y, end=end, progress=False)

    print("[3/5] 삼성전자 데이터 수집...")
    samsung = yf.download("005930.KS", start=start_1y, end=end, progress=False)

    print("[4/5] SK하이닉스 데이터 수집...")
    skhynix = yf.download("000660.KS", start=start_1y, end=end, progress=False)

    print("[5/5] 미국 국채 수익률 (Fed proxy)...")
    tnx = yf.download("^TNX", start=start_3m, end=end, progress=False)

    # Gold & USD/KRW for allocation
    gold = yf.download("GC=F", start=start_3m, end=end, progress=False)
    usdkrw = yf.download("KRW=X", start=start_3m, end=end, progress=False)

    return {
        'vix': vix, 'kospi': kospi, 'samsung': samsung,
        'skhynix': skhynix, 'tnx': tnx, 'gold': gold, 'usdkrw': usdkrw
    }


# ============================================================
# 2. HYDRODYNAMIC VARIABLE COMPUTATION
# ============================================================

def compute_flow_velocity(kospi_df):
    """u = Capital Flow Velocity (VWAP delta, daily returns as proxy)"""
    close = kospi_df['Close'].squeeze()
    # 5-day rolling return as flow velocity
    u = close.pct_change(5) * 100  # percentage
    # Acceleration (∂u/∂t)
    du_dt = u.diff()
    return u, du_dt


def compute_capital_density(kospi_df, samsung_df, skhynix_df):
    """ρ = Semiconductor sector concentration in KOSPI
    Paper: density > 35% → systemic turbulence risk elevated
    """
    kospi_close = kospi_df['Close'].squeeze()
    sam_close = samsung_df['Close'].squeeze()
    sk_close = skhynix_df['Close'].squeeze()

    # Approximate semiconductor weight using Samsung + SK Hynix market cap ratio
    # Samsung ~350T KRW, SK Hynix ~120T KRW, KOSPI total ~1800T KRW (approximate)
    # Use price ratios as proxy for weight changes
    sam_norm = sam_close / sam_close.iloc[0] if len(sam_close) > 0 else sam_close
    sk_norm = sk_close / sk_close.iloc[0] if len(sk_close) > 0 else sk_close
    kospi_norm = kospi_close / kospi_close.iloc[0] if len(kospi_close) > 0 else kospi_close

    # Base semiconductor density ~30% (historical average)
    base_density = 0.30
    # Adjust by relative performance
    aligned = pd.DataFrame({
        'sam': sam_norm, 'sk': sk_norm, 'kospi': kospi_norm
    }).dropna()

    if len(aligned) > 0:
        semi_perf = (aligned['sam'] * 0.7 + aligned['sk'] * 0.3)
        density = base_density * (semi_perf / aligned['kospi'])
    else:
        density = pd.Series([base_density])

    return density


def compute_pressure(kospi_df):
    """p = Valuation Pressure (P/E ratio proxy)
    Using price-to-200day-MA ratio as forward P/E proxy
    Paper thresholds:
      < 10x: Extreme High-Pressure (Buy +15pp)
      10-14x: High-Pressure (Maintain)
      14-18x: Neutral
      18-22x: Low-Pressure (Reduce -10pp)
      > 22x: Bubble Territory (Reduce -20pp)
    """
    close = kospi_df['Close'].squeeze()
    ma200 = close.rolling(200).mean()
    # Scale: KOSPI historical avg P/E ~12x, use price/MA200 * 12 as proxy
    pe_proxy = (close / ma200) * 12
    # Pressure gradient (∇p)
    grad_p = pe_proxy.diff(5)  # 5-day pressure change
    return pe_proxy, grad_p


def compute_viscosity(kospi_df):
    """ν = Market Friction / Liquidity
    Proxy: realized volatility (higher vol = higher friction)
    """
    close = kospi_df['Close'].squeeze()
    returns = close.pct_change()
    # 20-day realized volatility (annualized)
    vol_20d = returns.rolling(20).std() * np.sqrt(252) * 100
    return vol_20d


def compute_reynolds(u, density, viscosity):
    """Re_financial = (Capital Velocity × Market Depth) / Market Friction
    VIX > 30 ≈ turbulent threshold
    """
    # Normalize components
    aligned = pd.DataFrame({
        'u': u.abs(), 'rho': density, 'nu': viscosity
    }).dropna()

    if len(aligned) > 0 and (aligned['nu'] != 0).any():
        re = (aligned['u'] * aligned['rho'] * 100) / aligned['nu'].replace(0, np.nan)
    else:
        re = pd.Series([0])
    return re


# ============================================================
# 3. REGIME CLASSIFICATION (Table 5 from paper)
# ============================================================

def classify_regime(vix_current):
    """VIX-based regime classification"""
    if vix_current < 20:
        return "Laminar (층류)", "🟢"
    elif vix_current < 30:
        return "Transitional (천이)", "🟡"
    elif vix_current < 45:
        return "Turbulent (난류)", "🟠"
    else:
        return "Extreme Turbulence (극한 난류)", "🔴"


def get_etf_allocation(vix_current, pe_proxy_current):
    """Combined VIX-regime + P/E pressure allocation (Tables 5 + Section 6.2)"""

    # Base allocation from VIX regime (Table 5)
    if vix_current < 20:
        equity, bond, gold, cash = 70, 20, 10, 0
    elif vix_current < 30:
        equity, bond, gold, cash = 45, 30, 15, 10
    elif vix_current < 45:
        equity, bond, gold, cash = 20, 40, 20, 20
    else:
        equity, bond, gold, cash = 10, 30, 25, 35

    # P/E pressure-gradient adjustment (Section 6.2)
    pe_adj = 0
    pe_signal = ""
    if pe_proxy_current < 10:
        pe_adj = +15
        pe_signal = "극심한 고압 (저평가) → 매수 +15pp"
    elif pe_proxy_current < 14:
        pe_adj = 0
        pe_signal = "고압 (저평가) → 유지"
    elif pe_proxy_current < 18:
        pe_adj = 0
        pe_signal = "중립 → 기준선 유지"
    elif pe_proxy_current < 22:
        pe_adj = -10
        pe_signal = "저압 (고평가) → 감소 -10pp"
    else:
        pe_adj = -20
        pe_signal = "버블 구간 → 감소 -20pp"

    # Apply P/E adjustment to equity
    equity_final = max(5, min(85, equity + pe_adj))
    remainder = 100 - equity_final
    total_non_eq = bond + gold + cash
    if total_non_eq > 0:
        bond_final = int(remainder * bond / total_non_eq)
        gold_final = int(remainder * gold / total_non_eq)
        cash_final = remainder - bond_final - gold_final
    else:
        bond_final, gold_final, cash_final = remainder // 3, remainder // 3, remainder - 2 * (remainder // 3)

    return {
        'equity': equity_final, 'bond': bond_final,
        'gold': gold_final, 'cash': cash_final,
        'pe_signal': pe_signal, 'pe_adj': pe_adj
    }


# ============================================================
# 4. FLOW PREDICTION (Simplified Navier-Stokes)
# ============================================================

def predict_flow(u, du_dt, density, pressure, grad_p, viscosity, vix_series):
    """
    ∂u/∂t = -(u·∇)u - (1/ρ)∇p + ν∇²u + f

    Simplified 1D prediction:
    u(t+1) = u(t) + dt * [−advection − pressure_grad + diffusion + external]
    """
    aligned = pd.DataFrame({
        'u': u, 'du_dt': du_dt, 'rho': density,
        'p': pressure, 'grad_p': grad_p, 'nu': viscosity
    }).dropna()

    if len(aligned) < 5:
        return None, None

    latest = aligned.iloc[-1]

    # Component decomposition
    advection = -latest['u'] * latest['du_dt'] / 100  # nonlinear self-interaction
    pressure_force = -(1 / max(latest['rho'], 0.01)) * latest['grad_p']
    diffusion = latest['nu'] * latest['du_dt'] / 1000  # viscous smoothing

    # External force from VIX
    vix_clean = vix_series.dropna()
    if len(vix_clean) > 0:
        vix_last = float(vix_clean.iloc[-1].iloc[0]) if hasattr(vix_clean.iloc[-1], 'iloc') else float(vix_clean.iloc[-1])
        vix_change = float(vix_clean.diff().iloc[-1].iloc[0]) if hasattr(vix_clean.diff().iloc[-1], 'iloc') else float(vix_clean.diff().iloc[-1])
        external = -vix_change * 0.1  # VIX up → negative force on capital flow
    else:
        vix_last = 20
        external = 0

    # Predicted flow change
    dt = 1  # 1 day
    du_predicted = dt * (advection + pressure_force + diffusion + external)
    u_next = latest['u'] + du_predicted

    components = {
        'advection': advection,
        'pressure': pressure_force,
        'diffusion': diffusion,
        'external': external,
        'total_du': du_predicted,
        'u_current': latest['u'],
        'u_predicted': u_next
    }

    # 5-day outlook
    outlook = []
    u_t = latest['u']
    for i in range(5):
        decay = 0.9 ** i  # momentum decay
        u_t = u_t + du_predicted * decay
        outlook.append(u_t)

    return components, outlook


# ============================================================
# 5. DASHBOARD VISUALIZATION
# ============================================================

def create_dashboard(data, u, density, pressure, pe_proxy, viscosity,
                     vix_current, regime, emoji, allocation, components, outlook):
    """Create comprehensive Navier-Stokes dashboard"""

    fig = plt.figure(figsize=(16, 22), facecolor='#0a0a1a')
    fig.suptitle('Navier-Stokes 자본흐름 예측 시스템',
                 fontsize=24, fontweight='bold', color='white', y=0.98)
    fig.text(0.5, 0.965, 'Based on "Capital as a Viscous Fluid" (Choi, 2026)',
             ha='center', fontsize=11, color='#888888', style='italic')

    gs = fig.add_gridspec(5, 2, hspace=0.35, wspace=0.3,
                          left=0.08, right=0.95, top=0.94, bottom=0.03)

    dark_bg = '#0f1119'
    grid_color = '#1a1a2e'

    # --- Panel 1: KOSPI + Flow Velocity (u) ---
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor(dark_bg)
    kospi_close = data['kospi']['Close'].squeeze()
    ax1.plot(kospi_close.index[-120:], kospi_close.iloc[-120:],
             color='#00d4ff', linewidth=1.5, label='KOSPI')
    ax1_twin = ax1.twinx()
    u_plot = u.dropna()
    ax1_twin.fill_between(u_plot.index[-120:], 0, u_plot.iloc[-120:],
                          where=u_plot.iloc[-120:] > 0, color='#00ff88', alpha=0.3)
    ax1_twin.fill_between(u_plot.index[-120:], 0, u_plot.iloc[-120:],
                          where=u_plot.iloc[-120:] < 0, color='#ff4444', alpha=0.3)
    ax1_twin.plot(u_plot.index[-120:], u_plot.iloc[-120:],
                  color='#ffaa00', linewidth=1, alpha=0.7, label='Flow Velocity (u)')
    ax1.set_title('유동 속도 u = KOSPI 5일 변화율 (%)', color='white', fontsize=13)
    ax1.tick_params(colors='white')
    ax1_twin.tick_params(colors='#ffaa00')
    ax1.grid(True, color=grid_color, alpha=0.5)

    # --- Panel 2: Capital Density (ρ) ---
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor(dark_bg)
    density_plot = density.dropna()
    ax2.plot(density_plot.index[-120:], density_plot.iloc[-120:] * 100,
             color='#ff6b9d', linewidth=2)
    ax2.axhline(y=35, color='red', linestyle='--', alpha=0.7, label='위험 임계 35%')
    ax2.axhline(y=30, color='yellow', linestyle=':', alpha=0.5, label='평균 30%')
    ax2.set_title('밀도 ρ = 반도체 비중 (%)', color='white', fontsize=12)
    ax2.tick_params(colors='white')
    ax2.legend(fontsize=8, facecolor=dark_bg, edgecolor='gray', labelcolor='white')
    ax2.grid(True, color=grid_color, alpha=0.5)

    # --- Panel 3: Pressure (p = P/E proxy) ---
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor(dark_bg)
    pe_plot = pe_proxy.dropna()
    ax3.plot(pe_plot.index[-120:], pe_plot.iloc[-120:],
             color='#7b68ee', linewidth=2)
    ax3.axhspan(0, 10, alpha=0.1, color='green', label='<10x 저평가')
    ax3.axhspan(10, 14, alpha=0.05, color='green')
    ax3.axhspan(18, 22, alpha=0.05, color='red')
    ax3.axhspan(22, 30, alpha=0.1, color='red', label='>22x 버블')
    ax3.set_title('압력 p = Forward P/E (프록시)', color='white', fontsize=12)
    ax3.tick_params(colors='white')
    ax3.legend(fontsize=8, facecolor=dark_bg, edgecolor='gray', labelcolor='white')
    ax3.grid(True, color=grid_color, alpha=0.5)

    # --- Panel 4: Viscosity (ν) ---
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.set_facecolor(dark_bg)
    visc_plot = viscosity.dropna()
    ax4.fill_between(visc_plot.index[-120:], 0, visc_plot.iloc[-120:],
                     color='#ff8c00', alpha=0.4)
    ax4.plot(visc_plot.index[-120:], visc_plot.iloc[-120:],
             color='#ff8c00', linewidth=1.5)
    ax4.set_title('점성 ν = 20일 변동성 (%)', color='white', fontsize=12)
    ax4.tick_params(colors='white')
    ax4.grid(True, color=grid_color, alpha=0.5)

    # --- Panel 5: VIX (External Force f) ---
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.set_facecolor(dark_bg)
    vix_close = data['vix']['Close'].squeeze()
    vix_plot = vix_close.dropna()
    ax5.plot(vix_plot.index[-120:], vix_plot.iloc[-120:],
             color='#00ff88', linewidth=2)
    ax5.axhline(y=20, color='yellow', linestyle='--', alpha=0.5, label='천이 경계 20')
    ax5.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='난류 경계 30')
    ax5.axhline(y=45, color='red', linestyle='--', alpha=0.7, label='극한 경계 45')
    ax5.set_title('외력 f = VIX 지수', color='white', fontsize=12)
    ax5.tick_params(colors='white')
    ax5.legend(fontsize=8, facecolor=dark_bg, edgecolor='gray', labelcolor='white')
    ax5.grid(True, color=grid_color, alpha=0.5)

    # --- Panel 6: Force Decomposition ---
    ax6 = fig.add_subplot(gs[3, 0])
    ax6.set_facecolor(dark_bg)
    if components:
        forces = ['이류\n(u·∇)u', '압력\n∇p', '확산\nν∇²u', '외력\nf']
        values = [components['advection'], components['pressure'],
                  components['diffusion'], components['external']]
        colors_bar = ['#ff6b6b' if v < 0 else '#00ff88' for v in values]
        bars = ax6.bar(forces, values, color=colors_bar, alpha=0.8, edgecolor='white', linewidth=0.5)
        ax6.axhline(y=0, color='white', linewidth=0.5)
        for bar, val in zip(bars, values):
            ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                     f'{val:+.3f}', ha='center', va='bottom', color='white', fontsize=10)
    ax6.set_title('Navier-Stokes 힘 분해', color='white', fontsize=12)
    ax6.tick_params(colors='white')
    ax6.grid(True, color=grid_color, alpha=0.3, axis='y')

    # --- Panel 7: ETF Allocation Pie ---
    ax7 = fig.add_subplot(gs[3, 1])
    ax7.set_facecolor(dark_bg)
    alloc_labels = ['주식 ETF', '채권 ETF', '금', '현금']
    alloc_vals = [allocation['equity'], allocation['bond'],
                  allocation['gold'], allocation['cash']]
    alloc_colors = ['#00d4ff', '#7b68ee', '#ffd700', '#888888']
    wedges, texts, autotexts = ax7.pie(
        alloc_vals, labels=alloc_labels, colors=alloc_colors,
        autopct='%1.0f%%', startangle=90, textprops={'color': 'white', 'fontsize': 11}
    )
    for at in autotexts:
        at.set_fontweight('bold')
    ax7.set_title('ETF 배분 권고', color='white', fontsize=12)

    # --- Panel 8: Summary Box ---
    ax8 = fig.add_subplot(gs[4, :])
    ax8.set_facecolor('#0d1117')
    ax8.set_xlim(0, 10)
    ax8.set_ylim(0, 4)
    ax8.axis('off')

    # Current values
    u_now = float(u.dropna().iloc[-1]) if len(u.dropna()) > 0 else 0
    rho_now = float(density.dropna().iloc[-1]) * 100 if len(density.dropna()) > 0 else 30
    pe_now = float(pe_proxy.dropna().iloc[-1]) if len(pe_proxy.dropna()) > 0 else 12
    nu_now = float(viscosity.dropna().iloc[-1]) if len(viscosity.dropna()) > 0 else 15

    kospi_now = float(kospi_close.iloc[-1]) if len(kospi_close) > 0 else 0

    summary_text = (
        f"KOSPI: {kospi_now:,.0f}  |  VIX: {vix_current:.1f}  |  "
        f"레짐: {emoji} {regime}\n\n"
        f"u(유속) = {u_now:+.2f}%  |  ρ(밀도) = {rho_now:.1f}%  |  "
        f"p(압력) = {pe_now:.1f}x  |  ν(점성) = {nu_now:.1f}%\n\n"
        f"P/E 신호: {allocation['pe_signal']}\n"
    )

    if components and outlook:
        flow_dir = "유입 ↑" if components['u_predicted'] > 0 else "유출 ↓"
        summary_text += (
            f"예측: 현재 u={components['u_current']:+.2f}% → "
            f"다음 u={components['u_predicted']:+.2f}% ({flow_dir})\n"
            f"5일 전망: [{', '.join([f'{o:+.1f}' for o in outlook])}]"
        )

    ax8.text(0.5, 2.0, summary_text, transform=ax8.transAxes,
             fontsize=13, color='white', ha='center', va='center',
             fontfamily='NanumSquare', linespacing=1.8,
             bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                       edgecolor='#30363d', linewidth=2))

    # Timestamp
    fig.text(0.98, 0.005, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M KST")}',
             ha='right', fontsize=9, color='#555555')
    fig.text(0.02, 0.005, 'Navier-Stokes Capital Flow Model v1.0 | chimera-ai',
             ha='left', fontsize=9, color='#555555')

    output_path = '/home/ubuntu/.cokacdir/workspace/pfiuywu4/capital_flow_dashboard.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] Dashboard saved: {output_path}")
    return output_path


# ============================================================
# 6. TEXT REPORT
# ============================================================

def generate_report(vix_current, regime, emoji, allocation, components, outlook,
                    u, density, pe_proxy, viscosity, kospi_close):
    """Generate text report for Telegram"""

    u_now = float(u.dropna().iloc[-1]) if len(u.dropna()) > 0 else 0
    rho_now = float(density.dropna().iloc[-1]) * 100 if len(density.dropna()) > 0 else 30
    pe_now = float(pe_proxy.dropna().iloc[-1]) if len(pe_proxy.dropna()) > 0 else 12
    nu_now = float(viscosity.dropna().iloc[-1]) if len(viscosity.dropna()) > 0 else 15
    kospi_now = float(kospi_close.iloc[-1]) if len(kospi_close) > 0 else 0

    report = f"""
{'='*40}
  Navier-Stokes 자본흐름 예측
  {datetime.now().strftime('%Y-%m-%d %H:%M KST')}
{'='*40}

{emoji} 현재 레짐: {regime}
  KOSPI: {kospi_now:,.0f} | VIX: {vix_current:.1f}

--- 유체역학 변수 ---
  u (유속)  = {u_now:+.2f}% (5일 변화율)
  ρ (밀도)  = {rho_now:.1f}% (반도체 비중)
  p (압력)  = {pe_now:.1f}x (P/E 프록시)
  ν (점성)  = {nu_now:.1f}% (20일 변동성)
"""

    if components:
        report += f"""
--- Navier-Stokes 힘 분해 ---
  이류 (u·∇)u  = {components['advection']:+.4f}
  압력 ∇p      = {components['pressure']:+.4f}
  확산 ν∇²u    = {components['diffusion']:+.4f}
  외력 f(VIX)  = {components['external']:+.4f}
  ─────────────────
  총 Δu       = {components['total_du']:+.4f}

--- 흐름 예측 ---
  현재: u = {components['u_current']:+.2f}%
  예측: u = {components['u_predicted']:+.2f}%
  방향: {'자본 유입 ↑' if components['u_predicted'] > 0 else '자본 유출 ↓'}
"""

    if outlook:
        report += f"  5일 전망: {' → '.join([f'{o:+.1f}' for o in outlook])}\n"

    report += f"""
--- ETF 배분 권고 (Table 5) ---
  주식 ETF: {allocation['equity']}%
  채권 ETF: {allocation['bond']}%
  금:       {allocation['gold']}%
  현금:     {allocation['cash']}%

  P/E 조정: {allocation['pe_signal']}

--- 위험 신호 ---
"""

    # Risk signals
    if rho_now > 35:
        report += "  ⚠️ 반도체 밀도 > 35%: 집중 리스크 경고\n"
    if vix_current > 30:
        report += "  ⚠️ VIX > 30: 난류 구간 진입\n"
    if pe_now > 22:
        report += "  ⚠️ P/E > 22x: 버블 구간 경고\n"
    if pe_now < 10:
        report += "  ✅ P/E < 10x: 극심한 저평가 (매수 기회)\n"
    if abs(u_now) < 1:
        report += "  ℹ️ 유속 안정: 층류 흐름 유지\n"
    if abs(u_now) > 5:
        report += "  ⚠️ 유속 급변: 급격한 자본 이동 감지\n"
    if nu_now > 25:
        report += "  ⚠️ 고점성: 유동성 경색 주의\n"

    report += f"""
{'='*40}
  Based on "Capital as a Viscous Fluid"
  Nakcho Choi (2026), chimera-ai
{'='*40}
"""

    # Save report
    report_path = '/home/ubuntu/.cokacdir/workspace/pfiuywu4/capital_flow_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)

    return report, report_path


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 50)
    print("  Navier-Stokes 자본흐름 예측 시스템 v1.0")
    print("  Based on: Choi (2026)")
    print("=" * 50)

    # 1. Fetch data
    print("\n[Phase 1] 시장 데이터 수집 (yfinance, 무료)")
    data = fetch_market_data()

    # 2. Compute hydrodynamic variables
    print("\n[Phase 2] 유체역학 변수 계산")

    print("  Computing u (flow velocity)...")
    u, du_dt = compute_flow_velocity(data['kospi'])

    print("  Computing ρ (capital density)...")
    density = compute_capital_density(data['kospi'], data['samsung'], data['skhynix'])

    print("  Computing p (pressure / P/E)...")
    pe_proxy, grad_p = compute_pressure(data['kospi'])

    print("  Computing ν (viscosity)...")
    viscosity = compute_viscosity(data['kospi'])

    # 3. Get current VIX
    vix_close = data['vix']['Close'].squeeze()
    vix_current = float(vix_close.dropna().iloc[-1])
    print(f"\n  Current VIX: {vix_current:.2f}")

    # 4. Classify regime
    regime, emoji = classify_regime(vix_current)
    print(f"  Regime: {emoji} {regime}")

    # 5. P/E proxy current
    pe_now = float(pe_proxy.dropna().iloc[-1]) if len(pe_proxy.dropna()) > 0 else 12
    print(f"  P/E Proxy: {pe_now:.1f}x")

    # 6. ETF allocation
    allocation = get_etf_allocation(vix_current, pe_now)
    print(f"  Allocation: Equity {allocation['equity']}% / Bond {allocation['bond']}% / "
          f"Gold {allocation['gold']}% / Cash {allocation['cash']}%")

    # 7. Flow prediction
    print("\n[Phase 3] Navier-Stokes 흐름 예측")
    components, outlook = predict_flow(u, du_dt, density, pe_proxy, grad_p, viscosity, vix_close)

    if components:
        flow_dir = "유입 ↑" if components['u_predicted'] > 0 else "유출 ↓"
        print(f"  Current u: {components['u_current']:+.2f}%")
        print(f"  Predicted u: {components['u_predicted']:+.2f}% ({flow_dir})")

    # 8. Create dashboard
    print("\n[Phase 4] 대시보드 생성")
    dashboard_path = create_dashboard(
        data, u, density, pe_proxy, pe_proxy, viscosity,
        vix_current, regime, emoji, allocation, components, outlook
    )

    # 9. Generate report
    print("\n[Phase 5] 리포트 생성")
    kospi_close = data['kospi']['Close'].squeeze()
    report, report_path = generate_report(
        vix_current, regime, emoji, allocation, components, outlook,
        u, density, pe_proxy, viscosity, kospi_close
    )

    print(report)
    print(f"\n[DONE] Dashboard: {dashboard_path}")
    print(f"[DONE] Report: {report_path}")

    return dashboard_path, report_path, report


if __name__ == '__main__':
    main()
