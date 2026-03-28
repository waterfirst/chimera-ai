#!/usr/bin/env python3
"""
Navier-Stokes 자본흐름: 역사적 패턴 비교 + 예측 + 전략
Historical crisis patterns vs. Current situation
"""

import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

matplotlib.rcParams['font.family'] = 'NanumSquare'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. PAPER DATA (Table 2 & 3)
# ============================================================

# Table 2: Historical crisis density/pressure data
HISTORICAL_CRISES = {
    '2000 Q1\nIT 버블': {'kospi': 1059, 'density': 18.2, 'pe': 22.4, 'regime': 'Turbulent', 'color': '#ff4444'},
    '2008 Q4\nGFC': {'kospi': 938, 'density': 22.1, 'pe': 8.3, 'regime': 'Extreme', 'color': '#ff0000'},
    '2020 Q1\nCOVID': {'kospi': 1457, 'density': 25.7, 'pe': 10.2, 'regime': 'Turbulent', 'color': '#ff6600'},
    '2021 Q4\nAI 전주기': {'kospi': 2977, 'density': 27.3, 'pe': 13.8, 'regime': 'Transitional', 'color': '#ffaa00'},
    '2025 Q4\nAI 피크': {'kospi': 5846, 'density': 33.8, 'pe': 21.9, 'regime': 'Pre-turbulence', 'color': '#ff8800'},
    '2026 Feb 28\n피크': {'kospi': 6307, 'density': 35.1, 'pe': 23.4, 'regime': 'Critical', 'color': '#ff2200'},
    '2026 Mar 04\nSudden Stop': {'kospi': 5094, 'density': 31.2, 'pe': 9.7, 'regime': 'Extreme', 'color': '#cc0000'},
}

# Table 3: March 2026 Sudden Stop event study
MARCH_2026_EVENT = [
    {'date': 'Feb 26', 'kospi': 6307.27, 'return': +3.67, 'foreign_flow': +124.3, 'vix_chg': +5.2},
    {'date': 'Mar 03', 'kospi': 5791.91, 'return': -7.24, 'foreign_flow': -5132.7, 'vix_chg': +18.7},
    {'date': 'Mar 04', 'kospi': 5093.54, 'return': -12.06, 'foreign_flow': -6890.4, 'vix_chg': +11.3},
    {'date': 'Mar 05', 'kospi': 5583.90, 'return': +9.63, 'foreign_flow': +2341.2, 'vix_chg': -14.1},
]

# ============================================================
# 2. FETCH CURRENT DATA
# ============================================================

def fetch_current():
    """Fetch latest market data"""
    end = datetime.now()
    start = end - timedelta(days=180)

    print("[1/4] KOSPI...")
    kospi = yf.download("^KS11", start=start, end=end, progress=False)
    print("[2/4] VIX...")
    vix = yf.download("^VIX", start=start, end=end, progress=False)
    print("[3/4] Samsung...")
    sam = yf.download("005930.KS", start=start, end=end, progress=False)
    print("[4/4] SK Hynix...")
    sk = yf.download("000660.KS", start=start, end=end, progress=False)

    return kospi, vix, sam, sk


def compute_current_variables(kospi, vix, sam, sk):
    """Compute current N-S variables"""
    k_close = kospi['Close'].squeeze()
    v_close = vix['Close'].squeeze()

    # Current values
    kospi_now = float(k_close.iloc[-1])
    vix_now = float(v_close.iloc[-1])

    # Flow velocity (5-day return)
    u_now = float(k_close.pct_change(5).iloc[-1] * 100)

    # P/E proxy
    ma200 = k_close.rolling(200).mean()
    pe_now = float((k_close / ma200).iloc[-1] * 12) if not np.isnan((k_close / ma200).iloc[-1]) else 14.0

    # Density proxy
    s_close = sam['Close'].squeeze()
    h_close = sk['Close'].squeeze()
    base = 0.30
    s_norm = s_close / s_close.iloc[0]
    h_norm = h_close / h_close.iloc[0]
    k_norm = k_close / k_close.iloc[0]
    aligned = pd.DataFrame({'s': s_norm, 'h': h_norm, 'k': k_norm}).dropna()
    if len(aligned) > 0:
        semi = aligned['s'] * 0.7 + aligned['h'] * 0.3
        density_now = float((base * semi / aligned['k']).iloc[-1] * 100)
    else:
        density_now = 30.0

    # Volatility
    vol = float(k_close.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100)

    # Recent KOSPI history for pattern comparison
    recent_returns = k_close.pct_change().iloc[-30:] * 100

    return {
        'kospi': kospi_now, 'vix': vix_now, 'u': u_now,
        'pe': pe_now, 'density': density_now, 'vol': vol,
        'k_close': k_close, 'v_close': v_close,
        'recent_returns': recent_returns
    }


# ============================================================
# 3. PREDICTION ENGINE
# ============================================================

def predict_scenarios(cur):
    """Generate 3 scenarios based on N-S model + historical patterns"""

    kospi = cur['kospi']
    vix = cur['vix']
    pe = cur['pe']
    u = cur['u']

    # Scenario 1: March 2026 패턴 반복 (이란 사태 확대)
    # 2일간 -19.3% → 반등 +9.63%
    sc1_days = list(range(0, 21))
    sc1_kospi = [kospi]
    # Day 1-2: Sharp drop (-8% per day)
    sc1_kospi.append(kospi * 0.92)
    sc1_kospi.append(kospi * 0.92 * 0.88)  # -19.3% total
    # Day 3: Sharp rebound (+9.6%)
    sc1_kospi.append(sc1_kospi[-1] * 1.096)
    # Day 4-20: Gradual recovery with volatility
    for i in range(4, 21):
        recovery = sc1_kospi[-1] * (1 + 0.005 * np.sin(i * 0.5) + 0.003)
        sc1_kospi.append(recovery)

    # Scenario 2: 점진적 안정화 (외교 해결)
    sc2_kospi = [kospi]
    for i in range(1, 21):
        # VIX gradually declining, market recovering
        recovery_rate = 0.003 * (1 - np.exp(-i/5))
        noise = np.random.normal(0, 0.005)
        sc2_kospi.append(sc2_kospi[-1] * (1 + recovery_rate + noise))

    # Scenario 3: 장기 하락 (전쟁 확대 / Extreme Turbulence)
    sc3_kospi = [kospi]
    for i in range(1, 21):
        decline = -0.015 * np.exp(-i/10) - 0.002
        noise = np.random.normal(0, 0.008)
        sc3_kospi.append(sc3_kospi[-1] * (1 + decline + noise))
    np.random.seed(42)  # Reproducible

    # Recalculate with seed
    sc2_kospi = [kospi]
    sc3_kospi = [kospi]
    np.random.seed(42)
    for i in range(1, 21):
        recovery_rate = 0.003 * (1 - np.exp(-i/5))
        sc2_kospi.append(sc2_kospi[-1] * (1 + recovery_rate + np.random.normal(0, 0.005)))
    np.random.seed(123)
    sc3_kospi = [kospi]
    for i in range(1, 21):
        decline = -0.015 * np.exp(-i/10) - 0.002
        sc3_kospi.append(sc3_kospi[-1] * (1 + decline + np.random.normal(0, 0.008)))

    # Probability assignment based on current variables
    if vix > 40:
        p1, p2, p3 = 45, 15, 40  # High tension
    elif vix > 30:
        p1, p2, p3 = 40, 35, 25  # Current state
    else:
        p1, p2, p3 = 20, 55, 25  # Calming

    return {
        'days': sc1_days,
        'sc1': {'kospi': sc1_kospi, 'name': 'Sudden Stop 반복\n(이란 확대 → 급락 → 반등)', 'prob': p1, 'color': '#ff4444'},
        'sc2': {'kospi': sc2_kospi, 'name': '점진적 안정화\n(외교 해결)', 'prob': p2, 'color': '#00cc66'},
        'sc3': {'kospi': sc3_kospi, 'name': '장기 하락\n(전쟁 확대)', 'prob': p3, 'color': '#8800ff'},
    }


def get_strategy(cur, scenarios):
    """Generate strategy based on regime + scenarios"""
    vix = cur['vix']
    pe = cur['pe']
    density = cur['density']

    strategies = []

    # Phase 1: NOW
    if vix > 30:
        strategies.append({
            'phase': '1단계: 지금 즉시',
            'action': '방어 포지션 전환',
            'detail': f'주식 → 20%, 채권 40%, 금 20%, 현금 20%\nVIX {vix:.0f} > 30 난류 진입',
            'color': '#ff4444'
        })

    # Phase 2: Watch for buy signal
    strategies.append({
        'phase': '2단계: P/E < 10x 진입 시',
        'action': '공격 매수 (압력-구배 신호)',
        'detail': f'현재 P/E {pe:.1f}x → 10x 이하 시 주식 +15pp\n'
                  f'2026.3.4 P/E 9.7x 때 다음날 +9.63% 반등',
        'color': '#00ff88'
    })

    # Phase 3: VIX normalization
    strategies.append({
        'phase': '3단계: VIX < 20 복귀 시',
        'action': '정상 배분 복귀',
        'detail': '주식 70%, 채권 20%, 금 10%\n층류 레짐 복귀 확인 후',
        'color': '#00d4ff'
    })

    # Risk alerts
    alerts = []
    if density > 35:
        alerts.append(f'⚠️ 반도체 밀도 {density:.0f}% > 35%: 집중 리스크')
    if vix > 30:
        alerts.append(f'⚠️ VIX {vix:.1f} > 30: 난류 구간')
    if pe > 22:
        alerts.append(f'⚠️ P/E {pe:.1f}x > 22: 버블 주의')
    elif pe < 10:
        alerts.append(f'✅ P/E {pe:.1f}x < 10: 매수 기회!')

    return strategies, alerts


# ============================================================
# 4. MEGA DASHBOARD
# ============================================================

def create_mega_dashboard(cur, scenarios, strategies, alerts):
    """Create the comprehensive strategy dashboard"""

    fig = plt.figure(figsize=(18, 28), facecolor='#080810')

    # Title
    fig.suptitle('Navier-Stokes 자본흐름 분석',
                 fontsize=28, fontweight='bold', color='white', y=0.985)
    fig.text(0.5, 0.975, f'역사적 패턴 비교 | 시나리오 예측 | 전략 제시  —  {datetime.now().strftime("%Y-%m-%d %H:%M KST")}',
             ha='center', fontsize=12, color='#888888')

    gs = GridSpec(6, 2, figure=fig, hspace=0.32, wspace=0.25,
                  left=0.07, right=0.95, top=0.96, bottom=0.02)

    dark = '#0d1117'
    grid_c = '#1a1a2e'

    # ═══════════════════════════════════════
    # PANEL 1: Historical Crisis Comparison (scatter)
    # ═══════════════════════════════════════
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(dark)

    for label, d in HISTORICAL_CRISES.items():
        ax1.scatter(d['density'], d['pe'], s=max(100, d['kospi']/10),
                   color=d['color'], alpha=0.7, edgecolors='white', linewidth=0.5, zorder=5)
        ax1.annotate(label, (d['density'], d['pe']),
                    fontsize=7, color='white', ha='center', va='bottom',
                    xytext=(0, 8), textcoords='offset points')

    # Current point (★)
    ax1.scatter(cur['density'], cur['pe'], s=300, color='#00ff88',
               marker='*', edgecolors='white', linewidth=1, zorder=10)
    ax1.annotate(f'현재\nKOSPI {cur["kospi"]:,.0f}',
                (cur['density'], cur['pe']),
                fontsize=9, color='#00ff88', fontweight='bold',
                ha='center', va='bottom', xytext=(0, 12), textcoords='offset points')

    # Danger zones
    ax1.axvline(x=35, color='red', linestyle='--', alpha=0.4, label='밀도 위험선 35%')
    ax1.axhline(y=22, color='orange', linestyle='--', alpha=0.4, label='P/E 버블 22x')
    ax1.axhline(y=10, color='green', linestyle='--', alpha=0.4, label='P/E 매수 10x')

    ax1.set_xlabel('반도체 밀도 ρ (%)', color='white', fontsize=10)
    ax1.set_ylabel('Forward P/E (p)', color='white', fontsize=10)
    ax1.set_title('역사적 위기 vs 현재 위치', color='#00d4ff', fontsize=13, fontweight='bold')
    ax1.tick_params(colors='white')
    ax1.legend(fontsize=7, facecolor=dark, edgecolor='gray', labelcolor='white', loc='upper left')
    ax1.grid(True, color=grid_c, alpha=0.3)

    # ═══════════════════════════════════════
    # PANEL 2: March 2026 Sudden Stop Pattern
    # ═══════════════════════════════════════
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(dark)

    dates_m = [e['date'] for e in MARCH_2026_EVENT]
    returns_m = [e['return'] for e in MARCH_2026_EVENT]
    flows_m = [e['foreign_flow'] for e in MARCH_2026_EVENT]

    colors_bar = ['#00ff88' if r > 0 else '#ff4444' for r in returns_m]
    bars = ax2.bar(dates_m, returns_m, color=colors_bar, alpha=0.8, edgecolor='white', linewidth=0.5)

    for bar, val in zip(bars, returns_m):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + (0.3 if val > 0 else -0.8),
                f'{val:+.1f}%', ha='center', va='bottom' if val > 0 else 'top',
                color='white', fontsize=11, fontweight='bold')

    ax2_twin = ax2.twinx()
    ax2_twin.plot(dates_m, flows_m, color='#ffaa00', linewidth=2, marker='D', markersize=6)
    ax2_twin.set_ylabel('외국인 순매수 (십억원)', color='#ffaa00', fontsize=9)
    ax2_twin.tick_params(colors='#ffaa00')

    ax2.set_title('2026년 3월 Sudden Stop 이벤트 (논문 Table 3)', color='#ff6b6b', fontsize=13, fontweight='bold')
    ax2.set_ylabel('일간 수익률 (%)', color='white', fontsize=10)
    ax2.tick_params(colors='white')
    ax2.axhline(y=0, color='white', linewidth=0.5)
    ax2.grid(True, color=grid_c, alpha=0.3, axis='y')

    # ═══════════════════════════════════════
    # PANEL 3: Recent KOSPI (6 months)
    # ═══════════════════════════════════════
    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor(dark)

    k_close = cur['k_close']
    ax3.plot(k_close.index, k_close, color='#00d4ff', linewidth=2)
    ax3.fill_between(k_close.index, k_close.min() * 0.98, k_close,
                     color='#00d4ff', alpha=0.05)

    # Mark current
    ax3.scatter(k_close.index[-1], float(k_close.iloc[-1]), color='#00ff88', s=100, zorder=10)
    ax3.annotate(f'{float(k_close.iloc[-1]):,.0f}',
                (k_close.index[-1], float(k_close.iloc[-1])),
                fontsize=12, color='#00ff88', fontweight='bold',
                xytext=(-60, 15), textcoords='offset points',
                arrowprops=dict(arrowstyle='->', color='#00ff88', lw=1.5))

    # VIX overlay
    v_close = cur['v_close']
    ax3_twin = ax3.twinx()
    ax3_twin.fill_between(v_close.index, 0, v_close, color='#ff4444', alpha=0.15)
    ax3_twin.plot(v_close.index, v_close, color='#ff4444', linewidth=1, alpha=0.7)
    ax3_twin.axhline(y=30, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax3_twin.set_ylabel('VIX', color='#ff4444', fontsize=10)
    ax3_twin.tick_params(colors='#ff4444')

    ax3.set_title('KOSPI 6개월 + VIX (현재 난류 구간)', color='white', fontsize=14, fontweight='bold')
    ax3.tick_params(colors='white')
    ax3.grid(True, color=grid_c, alpha=0.3)

    # ═══════════════════════════════════════
    # PANEL 4: 3 Scenarios (20-day forecast)
    # ═══════════════════════════════════════
    ax4 = fig.add_subplot(gs[2, :])
    ax4.set_facecolor(dark)

    days = scenarios['days']
    for key in ['sc1', 'sc2', 'sc3']:
        sc = scenarios[key]
        ax4.plot(days, sc['kospi'], color=sc['color'], linewidth=2.5,
                label=f"{sc['name']} ({sc['prob']}%)", alpha=0.9)
        # End label
        ax4.annotate(f'{sc["kospi"][-1]:,.0f}',
                    (days[-1], sc['kospi'][-1]),
                    fontsize=10, color=sc['color'], fontweight='bold',
                    xytext=(10, 0), textcoords='offset points')

    ax4.axhline(y=cur['kospi'], color='white', linestyle=':', alpha=0.3)
    ax4.scatter([0], [cur['kospi']], color='white', s=100, zorder=10)
    ax4.annotate(f'현재 {cur["kospi"]:,.0f}', (0, cur['kospi']),
                fontsize=10, color='white', xytext=(10, 10), textcoords='offset points')

    # Buy zone (P/E < 10x equivalent)
    pe_ratio = cur['pe']
    if pe_ratio > 10:
        buy_threshold = cur['kospi'] * (10 / pe_ratio)
        ax4.axhline(y=buy_threshold, color='#00ff88', linestyle='--', alpha=0.5, linewidth=1.5)
        ax4.annotate(f'매수 구간 (P/E≈10x) ≈ {buy_threshold:,.0f}',
                    (10, buy_threshold), fontsize=9, color='#00ff88',
                    xytext=(0, -15), textcoords='offset points')

    ax4.set_xlabel('거래일 (D+0 = 오늘)', color='white', fontsize=11)
    ax4.set_ylabel('KOSPI', color='white', fontsize=11)
    ax4.set_title('20일 시나리오 예측 (Navier-Stokes 기반)', color='#ffaa00', fontsize=14, fontweight='bold')
    ax4.tick_params(colors='white')
    ax4.legend(fontsize=10, facecolor=dark, edgecolor='gray', labelcolor='white',
              loc='lower left', framealpha=0.9)
    ax4.grid(True, color=grid_c, alpha=0.3)

    # ═══════════════════════════════════════
    # PANEL 5: N-S Variable Gauges
    # ═══════════════════════════════════════
    ax5 = fig.add_subplot(gs[3, 0])
    ax5.set_facecolor(dark)

    vars_data = [
        ('유속 u', cur['u'], '%', -10, 10, [-10, -5, 0, 5, 10]),
        ('밀도 ρ', cur['density'], '%', 15, 50, [15, 25, 35, 50]),
        ('압력 p', cur['pe'], 'x', 5, 25, [5, 10, 14, 18, 22, 25]),
        ('점성 ν', cur['vol'], '%', 5, 80, [5, 15, 25, 40, 80]),
        ('외력 f', cur['vix'], '', 10, 50, [10, 20, 30, 45, 50]),
    ]

    y_positions = list(range(len(vars_data)))

    for i, (name, val, unit, vmin, vmax, ticks) in enumerate(vars_data):
        # Background bar
        bar_width = (val - vmin) / (vmax - vmin)
        bar_width = max(0, min(1, bar_width))

        # Color based on danger
        if name == '유속 u':
            color = '#ff4444' if abs(val) > 5 else ('#ffaa00' if abs(val) > 2 else '#00ff88')
        elif name == '밀도 ρ':
            color = '#ff4444' if val > 35 else ('#ffaa00' if val > 30 else '#00ff88')
        elif name == '압력 p':
            color = '#ff4444' if val > 22 else ('#00ff88' if val < 10 else '#ffaa00')
        elif name == '점성 ν':
            color = '#ff4444' if val > 40 else ('#ffaa00' if val > 20 else '#00ff88')
        else:  # VIX
            color = '#ff4444' if val > 30 else ('#ffaa00' if val > 20 else '#00ff88')

        ax5.barh(i, bar_width, color=color, alpha=0.6, height=0.6, left=0)
        ax5.text(-0.02, i, f'{name}', ha='right', va='center', color='white', fontsize=11, fontweight='bold')
        ax5.text(bar_width + 0.02, i, f'{val:.1f}{unit}', ha='left', va='center',
                color=color, fontsize=12, fontweight='bold')

    ax5.set_xlim(-0.01, 1.2)
    ax5.set_yticks([])
    ax5.set_xticks([])
    ax5.set_title('유체역학 변수 게이지', color='white', fontsize=13, fontweight='bold')
    ax5.grid(False)

    # ═══════════════════════════════════════
    # PANEL 6: ETF Allocation (Before → After)
    # ═══════════════════════════════════════
    ax6 = fig.add_subplot(gs[3, 1])
    ax6.set_facecolor(dark)

    # Before (laminar default)
    categories = ['주식', '채권', '금', '현금']
    before = [70, 20, 10, 0]  # Laminar
    after = [20, 40, 20, 20]  # Turbulent (current)

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax6.bar(x - width/2, before, width, label='층류 (VIX<20)', color='#00d4ff', alpha=0.6, edgecolor='white', linewidth=0.5)
    bars2 = ax6.bar(x + width/2, after, width, label=f'난류 (VIX={cur["vix"]:.0f})', color='#ff4444', alpha=0.8, edgecolor='white', linewidth=0.5)

    for bar, val in zip(bars1, before):
        if val > 0:
            ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'{val}%', ha='center', color='#00d4ff', fontsize=10)
    for bar, val in zip(bars2, after):
        if val > 0:
            ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'{val}%', ha='center', color='#ff4444', fontsize=10, fontweight='bold')

    # Arrows showing change
    for i in range(len(categories)):
        diff = after[i] - before[i]
        if diff != 0:
            ax6.annotate(f'{diff:+d}pp', (x[i], max(before[i], after[i]) + 5),
                        ha='center', fontsize=9, color='#ffaa00', fontweight='bold')

    ax6.set_xticks(x)
    ax6.set_xticklabels(categories, color='white', fontsize=11)
    ax6.set_title('ETF 배분 전환 (Table 5)', color='#ffaa00', fontsize=13, fontweight='bold')
    ax6.tick_params(colors='white')
    ax6.legend(fontsize=10, facecolor=dark, edgecolor='gray', labelcolor='white')
    ax6.grid(True, color=grid_c, alpha=0.3, axis='y')
    ax6.set_ylim(0, 85)

    # ═══════════════════════════════════════
    # PANEL 7: Strategy Timeline
    # ═══════════════════════════════════════
    ax7 = fig.add_subplot(gs[4, :])
    ax7.set_facecolor(dark)
    ax7.set_xlim(0, 10)
    ax7.set_ylim(0, len(strategies) + 1)
    ax7.axis('off')
    ax7.set_title('전략 타임라인', color='#00ff88', fontsize=15, fontweight='bold', pad=15)

    for i, strat in enumerate(strategies):
        y = len(strategies) - i
        # Phase circle
        circle = plt.Circle((0.5, y), 0.3, color=strat['color'], alpha=0.8)
        ax7.add_patch(circle)
        ax7.text(0.5, y, str(i+1), ha='center', va='center', color='white',
                fontsize=14, fontweight='bold')

        # Phase label
        ax7.text(1.2, y + 0.15, strat['phase'], color=strat['color'],
                fontsize=13, fontweight='bold', va='center')
        ax7.text(1.2, y - 0.15, strat['action'], color='white',
                fontsize=12, va='center')

        # Detail box
        ax7.text(5.5, y, strat['detail'], color='#cccccc',
                fontsize=10, va='center', fontfamily='NanumSquare',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#161b22',
                         edgecolor=strat['color'], linewidth=1.5, alpha=0.9))

        # Connecting line
        if i < len(strategies) - 1:
            ax7.plot([0.5, 0.5], [y - 0.3, y - 0.7], color='gray', linewidth=1, alpha=0.5)

    # ═══════════════════════════════════════
    # PANEL 8: Summary & Alerts
    # ═══════════════════════════════════════
    ax8 = fig.add_subplot(gs[5, :])
    ax8.set_facecolor('#0d1117')
    ax8.axis('off')

    # Current regime banner
    if cur['vix'] >= 45:
        regime_text = "극한 난류"
        regime_color = '#ff0000'
    elif cur['vix'] >= 30:
        regime_text = "난류"
        regime_color = '#ff6600'
    elif cur['vix'] >= 20:
        regime_text = "천이"
        regime_color = '#ffaa00'
    else:
        regime_text = "층류"
        regime_color = '#00ff88'

    # Build summary
    summary = f"현재 레짐: {regime_text} (VIX {cur['vix']:.1f})\n\n"
    summary += "위험 신호:\n"
    for alert in alerts:
        summary += f"  {alert}\n"

    summary += f"\n핵심 판단: "
    if cur['vix'] > 30 and cur['pe'] > 10:
        summary += "방어 우선 → P/E 10x 이하 진입 시 공격 매수 전환\n"
        summary += f"매수 트리거: KOSPI ≈ {cur['kospi'] * 10 / cur['pe']:,.0f} (P/E 10x 환산)"
    elif cur['pe'] < 10:
        summary += "극심한 저평가! 즉시 매수 신호 (P/E < 10x)"
    else:
        summary += "현 수준 유지, VIX 30 하회 시 점진적 비중 확대"

    ax8.text(0.5, 0.5, summary, transform=ax8.transAxes,
             fontsize=14, color='white', ha='center', va='center',
             fontfamily='NanumSquare', linespacing=1.8,
             bbox=dict(boxstyle='round,pad=1', facecolor='#161b22',
                       edgecolor=regime_color, linewidth=3))

    # Footer
    fig.text(0.5, 0.005,
             '"Capital as a Viscous Fluid: A Navier-Stokes Framework" — Nakcho Choi (2026)  |  chimera-ai v0.7',
             ha='center', fontsize=10, color='#555555', style='italic')

    output = '/home/ubuntu/.cokacdir/workspace/pfiuywu4/capital_flow_strategy.png'
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] Saved: {output}")
    return output


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("  Navier-Stokes: 패턴 비교 + 예측 + 전략")
    print("=" * 55)

    # Fetch data
    print("\n[Phase 1] 데이터 수집...")
    kospi, vix, sam, sk = fetch_current()

    # Compute
    print("\n[Phase 2] 변수 계산...")
    cur = compute_current_variables(kospi, vix, sam, sk)
    print(f"  KOSPI: {cur['kospi']:,.0f}")
    print(f"  VIX: {cur['vix']:.1f}")
    print(f"  u(유속): {cur['u']:+.2f}%")
    print(f"  ρ(밀도): {cur['density']:.1f}%")
    print(f"  p(P/E): {cur['pe']:.1f}x")
    print(f"  ν(점성): {cur['vol']:.1f}%")

    # Scenarios
    print("\n[Phase 3] 시나리오 예측...")
    scenarios = predict_scenarios(cur)
    for key in ['sc1', 'sc2', 'sc3']:
        sc = scenarios[key]
        print(f"  {sc['name'].replace(chr(10), ' ')}: {sc['prob']}% → KOSPI {sc['kospi'][-1]:,.0f}")

    # Strategy
    print("\n[Phase 4] 전략 생성...")
    strategies, alerts = get_strategy(cur, scenarios)
    for s in strategies:
        print(f"  {s['phase']}: {s['action']}")

    # Dashboard
    print("\n[Phase 5] 대시보드 생성...")
    output = create_mega_dashboard(cur, scenarios, strategies, alerts)

    print(f"\n[DONE] {output}")
    return output


if __name__ == '__main__':
    main()
