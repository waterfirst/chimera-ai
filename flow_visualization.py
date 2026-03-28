#!/usr/bin/env python3
"""
Navier-Stokes 자본흐름 — 층류/난류 유체 형상화
과거 위기 패턴 vs 현재 상태를 유체역학적으로 시각화
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as pathfx
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

matplotlib.rcParams['font.family'] = 'NanumSquare'
matplotlib.rcParams['axes.unicode_minus'] = False


def draw_flow_field(ax, regime='laminar', title='', vix=15, pe=12, kospi=2500,
                    density=25, date_label='', detail=''):
    """Draw fluid flow visualization
    regime: 'laminar', 'transitional', 'turbulent', 'extreme'
    """
    ax.set_facecolor('#080810')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    np.random.seed(hash(regime) % 2**31)

    # Flow parameters by regime
    params = {
        'laminar': {'n_lines': 18, 'amplitude': 0.02, 'freq': 1, 'speed': 1.0,
                    'color_start': '#0044ff', 'color_end': '#00ccff', 'particle_chaos': 0.05},
        'transitional': {'n_lines': 20, 'amplitude': 0.15, 'freq': 3, 'speed': 0.8,
                         'color_start': '#0088ff', 'color_end': '#ffaa00', 'particle_chaos': 0.2},
        'turbulent': {'n_lines': 25, 'amplitude': 0.5, 'freq': 6, 'speed': 0.5,
                      'color_start': '#ff6600', 'color_end': '#ff0000', 'particle_chaos': 0.6},
        'extreme': {'n_lines': 30, 'amplitude': 1.0, 'freq': 10, 'speed': 0.3,
                    'color_start': '#ff0000', 'color_end': '#ff00ff', 'particle_chaos': 1.0},
    }

    p = params[regime]

    # --- Draw channel walls ---
    wall_color = '#333355'
    ax.plot([0, 10], [0.3, 0.3], color=wall_color, linewidth=3)
    ax.plot([0, 10], [5.7, 5.7], color=wall_color, linewidth=3)

    # Wall labels
    ax.text(0.15, 0.05, '시장 바닥 (지지선)', color='#555577', fontsize=7)
    ax.text(0.15, 5.8, '시장 천장 (저항선)', color='#555577', fontsize=7)

    # --- Draw streamlines ---
    x = np.linspace(0, 10, 300)
    y_base = np.linspace(0.8, 5.2, p['n_lines'])

    cmap = LinearSegmentedColormap.from_list('flow', [p['color_start'], p['color_end']])

    for i, yb in enumerate(y_base):
        # Center velocity profile (parabolic - faster in center)
        center_dist = abs(yb - 3.0) / 2.5
        velocity = 1.0 - center_dist ** 2  # Parabolic profile

        # Streamline with perturbation
        if regime == 'laminar':
            y = yb + p['amplitude'] * np.sin(p['freq'] * x * 0.5 + i * 0.3)
        elif regime == 'transitional':
            y = yb + p['amplitude'] * np.sin(p['freq'] * x * 0.3 + i * 0.5) * (1 + 0.3 * np.sin(x * 2))
        elif regime == 'turbulent':
            noise = np.cumsum(np.random.randn(len(x)) * 0.03)
            y = yb + p['amplitude'] * np.sin(p['freq'] * x * 0.2 + i * 0.7) + noise * 0.3
        else:  # extreme
            noise = np.cumsum(np.random.randn(len(x)) * 0.06)
            vortex = 0.5 * np.sin(x * 1.5 + i) * np.cos(x * 0.7 - i * 0.3)
            y = yb + p['amplitude'] * np.sin(p['freq'] * x * 0.15 + i) + noise * 0.4 + vortex

        # Clip to channel
        y = np.clip(y, 0.5, 5.5)

        # Color by velocity
        color_val = velocity * 0.8 + 0.1
        line_color = cmap(color_val)
        alpha = 0.3 + 0.5 * velocity

        ax.plot(x, y, color=line_color, linewidth=0.8 + velocity * 1.2, alpha=alpha)

    # --- Draw particles (capital particles) ---
    n_particles = int(30 + p['particle_chaos'] * 50)
    px = np.random.uniform(0.5, 9.5, n_particles)
    py = np.random.uniform(1, 5, n_particles)

    # Particle velocity arrows
    for j in range(n_particles):
        center_d = abs(py[j] - 3.0) / 2.5
        vel = (1.0 - center_d ** 2) * p['speed']

        dx = vel * 0.3
        dy = p['particle_chaos'] * np.random.randn() * 0.15

        particle_color = cmap(vel)
        size = 8 + vel * 15

        ax.scatter(px[j], py[j], s=size, color=particle_color, alpha=0.6, zorder=5)

        if vel > 0.2:
            ax.annotate('', xy=(px[j] + dx, py[j] + dy), xytext=(px[j], py[j]),
                       arrowprops=dict(arrowstyle='->', color=particle_color,
                                      lw=0.5 + vel, alpha=0.4))

    # --- Vortices for turbulent regimes ---
    if regime in ('turbulent', 'extreme'):
        n_vortex = 3 if regime == 'turbulent' else 6
        for v in range(n_vortex):
            vx = np.random.uniform(2, 8)
            vy = np.random.uniform(1.5, 4.5)
            vr = np.random.uniform(0.3, 0.7) * (1.5 if regime == 'extreme' else 1.0)

            theta = np.linspace(0, 4 * np.pi, 80)
            r = np.linspace(0.05, vr, 80)
            spiral_x = vx + r * np.cos(theta)
            spiral_y = vy + r * np.sin(theta)

            vortex_color = '#ff4444' if regime == 'extreme' else '#ff8800'
            ax.plot(spiral_x, spiral_y, color=vortex_color, linewidth=1.2, alpha=0.5)

            # Vortex center marker
            ax.scatter(vx, vy, s=30, color=vortex_color, marker='x', linewidth=1.5, alpha=0.7, zorder=6)

    # --- Regime label & info ---
    regime_names = {
        'laminar': ('층류 (Laminar)', '#00ccff'),
        'transitional': ('천이 (Transitional)', '#ffaa00'),
        'turbulent': ('난류 (Turbulent)', '#ff6600'),
        'extreme': ('극한 난류 (Extreme)', '#ff0000'),
    }
    rname, rcolor = regime_names[regime]

    # Title banner
    ax.text(5, 5.4, title, ha='center', va='center', fontsize=13,
            fontweight='bold', color='white',
            path_effects=[pathfx.withStroke(linewidth=3, foreground='black')])

    ax.text(5, 5.0, rname, ha='center', va='center', fontsize=11,
            fontweight='bold', color=rcolor,
            path_effects=[pathfx.withStroke(linewidth=2, foreground='black')])

    # Info box
    info = f"KOSPI {kospi:,}  |  VIX {vix}  |  P/E {pe}x  |  밀도 {density}%"
    ax.text(5, 0.65, info, ha='center', va='center', fontsize=8,
            color='#aaaaaa',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0a0a15', edgecolor=rcolor, alpha=0.8))

    if date_label:
        ax.text(0.3, 5.35, date_label, fontsize=9, color='#888888',
                path_effects=[pathfx.withStroke(linewidth=2, foreground='black')])

    if detail:
        ax.text(5, 0.15, detail, ha='center', fontsize=7, color='#666688')

    # Re number indicator
    re_val = {'laminar': 'Re < 2000', 'transitional': '2000 < Re < 4000',
              'turbulent': 'Re > 4000', 'extreme': 'Re >> 4000'}
    ax.text(9.7, 5.35, re_val[regime], ha='right', fontsize=7, color=rcolor, alpha=0.7)


def create_flow_dashboard():
    """Create the complete flow visualization dashboard"""

    fig = plt.figure(figsize=(18, 36), facecolor='#050510')

    fig.suptitle('자본을 점성 유체로 본다면',
                 fontsize=30, fontweight='bold', color='white', y=0.99)
    fig.text(0.5, 0.982,
             'Navier-Stokes 자본흐름 모델  —  ∂u/∂t + (u·∇)u = -(1/ρ)∇p + ν∇²u + f',
             ha='center', fontsize=13, color='#555577', style='italic')

    gs = GridSpec(7, 2, figure=fig, hspace=0.15, wspace=0.08,
                  left=0.03, right=0.97, top=0.97, bottom=0.02)

    # ═══════════════════════════════════════
    # ROW 1: 유체역학 개념 설명
    # ═══════════════════════════════════════

    # Laminar example
    ax_lam = fig.add_subplot(gs[0, 0])
    draw_flow_field(ax_lam, 'laminar',
                    title='층류: 자본이 질서있게 흐른다',
                    vix=15, pe=14, kospi=2800, density=22,
                    date_label='이상적 상태',
                    detail='VIX < 20 | 낮은 변동성 | 예측 가능한 흐름 | 주식 70%')

    # Turbulent example
    ax_turb = fig.add_subplot(gs[0, 1])
    draw_flow_field(ax_turb, 'extreme',
                    title='난류: 자본이 혼돈에 빠진다',
                    vix=50, pe=8, kospi=1000, density=35,
                    date_label='위기 상태',
                    detail='VIX > 30 | 와류 발생 | 예측 불가 | 주식 10~20%')

    # ═══════════════════════════════════════
    # ROW 2-5: 역사적 위기 패턴들
    # ═══════════════════════════════════════

    historical = [
        # (row, col, regime, title, params)
        (1, 0, 'extreme', '2000 Q1 — IT 버블 붕괴',
         {'vix': 34, 'pe': 22.4, 'kospi': 1059, 'density': 18.2,
          'date': '2000.03', 'detail': '기술주 과열 → 밀도 낮았지만 P/E 22x 버블 → 급락'}),

        (1, 1, 'extreme', '2008 Q4 — 글로벌 금융위기',
         {'vix': 80, 'pe': 8.3, 'kospi': 938, 'density': 22.1,
          'date': '2008.10', 'detail': 'VIX 80! 역사상 최대 난류 | P/E 8.3x → 극한 매수 신호'}),

        (2, 0, 'turbulent', '2020 Q1 — COVID 팬데믹',
         {'vix': 65, 'pe': 10.2, 'kospi': 1457, 'density': 25.7,
          'date': '2020.03', 'detail': 'V자 반등 → P/E 10x에서 산 사람이 2년간 +100%'}),

        (2, 1, 'transitional', '2021 Q4 — AI 사이클 시작',
         {'vix': 23, 'pe': 13.8, 'kospi': 2977, 'density': 27.3,
          'date': '2021.12', 'detail': '천이 구간 | 반도체 밀도 상승 시작 | AI 붐 전조'}),

        (3, 0, 'transitional', '2025 Q4 — AI 피크',
         {'vix': 18, 'pe': 21.9, 'kospi': 5846, 'density': 33.8,
          'date': '2025.12', 'detail': 'P/E 22x 접근 → 버블 경고 | 밀도 34% 위험 임계 접근'}),

        (3, 1, 'extreme', '2026 Mar — Sudden Stop (이란 사태)',
         {'vix': 45, 'pe': 9.7, 'kospi': 5094, 'density': 31.2,
          'date': '2026.03.04', 'detail': '2일간 -19.3% | 12조 유출 | 다음날 P/E 9.7x → +9.63% 반등'}),
    ]

    for row, col, regime, title, params in historical:
        ax = fig.add_subplot(gs[row, col])
        draw_flow_field(ax, regime, title=title,
                       vix=params['vix'], pe=params['pe'],
                       kospi=params['kospi'], density=params['density'],
                       date_label=params['date'], detail=params['detail'])

    # ═══════════════════════════════════════
    # ROW 6: 현재 상태 (강조)
    # ═══════════════════════════════════════
    ax_now = fig.add_subplot(gs[4, :])
    draw_flow_field(ax_now, 'turbulent',
                    title='현재 (2026.03.28) — 이란 사태 재격화',
                    vix=31, pe=14, kospi=5439, density=44,
                    date_label='NOW',
                    detail='VIX 31 난류 진입 | 반도체 밀도 44% 과밀 | P/E 14x 중립 | 변동성 77% | 유속 -5.9%')

    # Add "NOW" emphasis
    ax_now.text(0.5, 3.0, 'LIVE', fontsize=50, color='#ff0000', alpha=0.08,
               ha='center', va='center', fontweight='bold', rotation=15)

    # ═══════════════════════════════════════
    # ROW 7: 흐름 해석 + 전략 요약
    # ═══════════════════════════════════════
    ax_summary = fig.add_subplot(gs[5, :])
    ax_summary.set_facecolor('#0a0a15')
    ax_summary.axis('off')

    # Navier-Stokes equation display
    eq_text = "∂u/∂t  +  (u·∇)u  =  -(1/ρ)∇p  +  ν∇²u  +  f"
    ax_summary.text(0.5, 0.88, eq_text, transform=ax_summary.transAxes,
                   ha='center', fontsize=18, color='#00ccff', fontweight='bold',
                   fontfamily='serif')

    # Force arrows diagram
    labels = [
        ("가속도\n∂u/∂t", 0.08, '#ffffff'),
        ("이류(관성)\n(u·∇)u", 0.23, '#ff8800'),
        ("압력 구배\n-(1/ρ)∇p", 0.42, '#7b68ee'),
        ("확산(점성)\nν∇²u", 0.62, '#00cc66'),
        ("외력(VIX)\nf", 0.80, '#ff4444'),
    ]

    for text, x_pos, color in labels:
        ax_summary.text(x_pos, 0.62, text, transform=ax_summary.transAxes,
                       ha='center', fontsize=11, color=color, fontweight='bold')

    # Current decomposition values
    decomp = """현재 힘 분해:
  이류 (u·∇)u  = -0.040  ← 하락 관성 (자기강화 매도)
  압력 ∇p      = +2.671  ← 강한 반등 압력 (저평가 매력)
  확산 ν∇²u    = -0.052  ← 높은 점성이 흐름 억제
  외력 f(VIX)  = -0.361  ← 이란 리스크 지속

  순 힘 = +2.219 → 반등 방향이지만 아직 VIX 억제 중"""

    ax_summary.text(0.5, 0.22, decomp, transform=ax_summary.transAxes,
                   ha='center', va='center', fontsize=12, color='#cccccc',
                   fontfamily='NanumSquare', linespacing=1.6,
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='#0d1117',
                            edgecolor='#333355', linewidth=1.5))

    # ═══════════════════════════════════════
    # ROW 8: 전략 요약
    # ═══════════════════════════════════════
    ax_strat = fig.add_subplot(gs[6, :])
    ax_strat.set_facecolor('#0a0a15')
    ax_strat.axis('off')

    ax_strat.text(0.5, 0.92, '패턴 비교 결론', transform=ax_strat.transAxes,
                 ha='center', fontsize=18, color='#ffaa00', fontweight='bold')

    comparison = """
  2008 GFC (VIX 80, P/E 8.3x)  →  극한 난류  →  바닥 확인 후 2년간 +150%
  2020 COVID (VIX 65, P/E 10.2x) → 난류  →  V자 반등, 1년간 +100%
  2026.03 이란 (VIX 45, P/E 9.7x) → 극한 난류  →  다음날 +9.63% 반등

  지금 (VIX 31, P/E 14x, 밀도 44%) → 난류 초입  →  아직 바닥 아님

  공통 패턴:
    ① 난류 진입 → 주식 축소 (방어)
    ② P/E 10x 이하 → 압력-구배 매수 신호
    ③ VIX 정상화 → 주식 비중 복귀

  현재 위치: ① 단계 (방어)
  다음 행동: P/E가 10x 아래로 떨어질 때까지 대기"""

    ax_strat.text(0.5, 0.45, comparison, transform=ax_strat.transAxes,
                 ha='center', va='center', fontsize=12, color='white',
                 fontfamily='NanumSquare', linespacing=1.7,
                 bbox=dict(boxstyle='round,pad=0.8', facecolor='#0d1117',
                          edgecolor='#ffaa00', linewidth=2))

    # Footer
    fig.text(0.5, 0.005,
             '"Capital as a Viscous Fluid" — Nakcho Choi (2026) | chimera-ai v0.7 | Navier-Stokes Capital Flow Model',
             ha='center', fontsize=10, color='#333344', style='italic')

    output = '/home/ubuntu/.cokacdir/workspace/pfiuywu4/flow_visual.png'
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] {output}")
    return output


if __name__ == '__main__':
    print("Navier-Stokes 유체 흐름 시각화 생성 중...")
    output = create_flow_dashboard()
    print(f"[DONE] {output}")
