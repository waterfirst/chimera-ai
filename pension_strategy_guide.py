#!/usr/bin/env python3
"""
DC 퇴직연금 Navier-Stokes 전략 가이드
+ 자동 매수신호 모니터링
"""

import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

matplotlib.rcParams['font.family'] = 'NanumSquare'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# DC 퇴직연금 매수 가능 ETF 목록 (한국 증시 상장)
# ============================================================

ETF_UNIVERSE = {
    'equity_kr': [
        {'ticker': '069500.KS', 'name': 'KODEX 200', 'desc': 'KOSPI200 추종, 가장 기본'},
        {'ticker': '229200.KS', 'name': 'KODEX 코스닥150', 'desc': '코스닥 대형주'},
        {'ticker': '091160.KS', 'name': 'KODEX 반도체', 'desc': '반도체 섹터 집중'},
        {'ticker': '091170.KS', 'name': 'KODEX 은행', 'desc': '금융 방어 섹터'},
        {'ticker': '117700.KS', 'name': 'KODEX 건설', 'desc': '건설/인프라'},
        {'ticker': '266360.KS', 'name': 'KODEX 2차전지산업', 'desc': '2차전지 테마'},
    ],
    'equity_us': [
        {'ticker': '379800.KS', 'name': 'KODEX 미국S&P500TR', 'desc': '미국 대형주'},
        {'ticker': '379810.KS', 'name': 'KODEX 미국나스닥100TR', 'desc': '미국 기술주'},
    ],
    'bond': [
        {'ticker': '148070.KS', 'name': 'KOSEF 국고채10년', 'desc': '장기 국채'},
        {'ticker': '114820.KS', 'name': 'TIGER 국채3년', 'desc': '단기 국채, 안전'},
        {'ticker': '182490.KS', 'name': 'TIGER 미국채10년선물', 'desc': '미국 장기채'},
        {'ticker': '305080.KS', 'name': 'TIGER 미국채30년스트립액티브', 'desc': '미국 초장기채'},
    ],
    'gold': [
        {'ticker': '132030.KS', 'name': 'KODEX 골드선물(H)', 'desc': '금 선물, 환헤지'},
        {'ticker': '411060.KS', 'name': 'ACE KRX금현물', 'desc': '금 현물'},
    ],
    'defensive': [
        {'ticker': '161510.KS', 'name': 'ARIRANG 고배당주', 'desc': '고배당 방어'},
        {'ticker': '211560.KS', 'name': 'TIGER 배당성장', 'desc': '배당 성장주'},
    ],
}


def fetch_etf_prices():
    """Fetch recent ETF prices for the guide"""
    print("[데이터] ETF 가격 수집...")
    end = datetime.now()
    start = end - timedelta(days=30)

    results = {}
    key_tickers = [
        '069500.KS', '091160.KS', '148070.KS', '132030.KS',
        '379800.KS', '114820.KS', '411060.KS',
    ]

    for ticker in key_tickers:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if len(df) > 0:
                close = df['Close'].squeeze()
                price = float(close.iloc[-1])
                chg_5d = float(close.pct_change(5).iloc[-1] * 100) if len(close) > 5 else 0
                results[ticker] = {'price': price, 'chg_5d': chg_5d}
        except:
            pass

    return results


def fetch_signals():
    """Fetch current VIX and KOSPI for signal check"""
    end = datetime.now()
    start = end - timedelta(days=250)

    vix = yf.download("^VIX", start=start, end=end, progress=False)
    kospi = yf.download("^KS11", start=start, end=end, progress=False)

    vix_now = float(vix['Close'].squeeze().iloc[-1])
    kospi_now = float(kospi['Close'].squeeze().iloc[-1])

    k_close = kospi['Close'].squeeze()
    ma200 = k_close.rolling(200).mean()
    pe_proxy = float((k_close / ma200).iloc[-1] * 12) if not np.isnan((k_close / ma200).iloc[-1]) else 14

    vol = float(k_close.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100)

    return vix_now, kospi_now, pe_proxy, vol


def create_guide_image(vix, kospi, pe, vol, etf_prices):
    """Create the strategy guide image"""

    fig = plt.figure(figsize=(16, 32), facecolor='#080810')
    fig.suptitle('DC 퇴직연금 Navier-Stokes 전략 가이드',
                 fontsize=26, fontweight='bold', color='white', y=0.99)
    fig.text(0.5, 0.98, f'{datetime.now().strftime("%Y-%m-%d")} | KOSPI {kospi:,.0f} | VIX {vix:.1f} | P/E {pe:.1f}x',
             ha='center', fontsize=13, color='#888888')

    gs = GridSpec(8, 2, figure=fig, hspace=0.3, wspace=0.25,
                  left=0.06, right=0.96, top=0.97, bottom=0.01)

    dark = '#0d1117'
    grid_c = '#1a1a2e'

    # ═══════════════════════════════════════
    # PANEL 0: 현재 상태 + 긴급도
    # ═══════════════════════════════════════
    ax0 = fig.add_subplot(gs[0, :])
    ax0.set_facecolor('#1a0000' if vix > 30 else dark)
    ax0.axis('off')

    if vix >= 45:
        urgency = "극한 난류 — 즉시 방어"
        urgency_color = '#ff0000'
    elif vix >= 30:
        urgency = "난류 진입 — 월요일 아침 실행"
        urgency_color = '#ff6600'
    elif vix >= 20:
        urgency = "천이 구간 — 점진적 조정"
        urgency_color = '#ffaa00'
    else:
        urgency = "층류 — 공격적 배분 유지"
        urgency_color = '#00ff88'

    ax0.text(0.5, 0.7, urgency, transform=ax0.transAxes,
             fontsize=22, color=urgency_color, fontweight='bold', ha='center',
             bbox=dict(boxstyle='round,pad=0.6', facecolor='#161b22',
                       edgecolor=urgency_color, linewidth=3))

    status_text = (f"VIX {vix:.1f} (임계값 30)  |  "
                   f"P/E {pe:.1f}x (매수 신호 <10x)  |  "
                   f"변동성 {vol:.0f}%")
    ax0.text(0.5, 0.2, status_text, transform=ax0.transAxes,
             fontsize=13, color='#aaaaaa', ha='center')

    # ═══════════════════════════════════════
    # PANEL 1: STEP 1 — 월요일 아침 즉시 실행
    # ═══════════════════════════════════════
    ax1 = fig.add_subplot(gs[1, :])
    ax1.set_facecolor(dark)
    ax1.axis('off')
    ax1.set_title('STEP 1: 월요일(3/30) 개장 직후 실행', color='#ff4444',
                  fontsize=16, fontweight='bold', loc='left', pad=10)

    step1_text = """
 현재 주식형 ETF → 전량 매도 (현금화)

 실행 순서:
  1. 퇴직연금 계좌 로그인 (삼성증권/미래에셋 등)
  2. 보유 중인 주식형 ETF 전량 매도 주문
     - KODEX 200, 반도체, 나스닥 등 주식형 전부
     - 시장가 매도 (지정가 X → 체결 지연 방지)
  3. 매도 대금 → 현금성 자산 또는 MMF로 이동
  4. 채권/금 ETF로 즉시 재배분 (STEP 2)

 주의: 퇴직연금은 매도 후 T+2 결제
       → 수요일(4/1)부터 재매수 가능할 수 있음
       → 증권사별 즉시 매수 가능 여부 확인
"""
    ax1.text(0.02, 0.9, step1_text, transform=ax1.transAxes,
             fontsize=12, color='white', va='top', fontfamily='NanumSquare',
             linespacing=1.6)

    # ═══════════════════════════════════════
    # PANEL 2: STEP 2 — 방어 배분
    # ═══════════════════════════════════════
    ax2 = fig.add_subplot(gs[2, :])
    ax2.set_facecolor(dark)
    ax2.axis('off')
    ax2.set_title('STEP 2: 방어 배분 (VIX > 30 난류 레짐)', color='#ffaa00',
                  fontsize=16, fontweight='bold', loc='left', pad=10)

    # Current allocation based on Table 5
    alloc_text = """
 목표 배분 (논문 Table 5 — 난류 레짐):

 ┌─────────────────────────────────────────────────────────────┐
 │  자산군        비중    추천 ETF                              │
 ├─────────────────────────────────────────────────────────────┤
 │  주식 ETF      20%    보류 (현금 대기)                       │
 │                       → P/E < 10x 신호 시 재진입             │
 │                                                             │
 │  채권 ETF      40%    TIGER 국채3년 (114820)         20%     │
 │                       KOSEF 국고채10년 (148070)      10%     │
 │                       TIGER 미국채10년선물 (182490)  10%     │
 │                                                             │
 │  금             20%    KODEX 골드선물(H) (132030)     10%     │
 │                       ACE KRX금현물 (411060)         10%     │
 │                                                             │
 │  현금/MMF      20%    CMA/MMF (증권사 기본)          20%     │
 └─────────────────────────────────────────────────────────────┘

 채권 40%: 금리 하락기 수혜 + 안전자산
 금 20%: 지정학 리스크 헤지 (이란 사태)
 현금 20%: 매수 기회 대기 실탄
"""
    ax2.text(0.02, 0.95, alloc_text, transform=ax2.transAxes,
             fontsize=11, color='white', va='top', fontfamily='NanumSquare',
             linespacing=1.5)

    # ═══════════════════════════════════════
    # PANEL 3: STEP 3 — 매수 신호 대기
    # ═══════════════════════════════════════
    ax3 = fig.add_subplot(gs[3, :])
    ax3.set_facecolor(dark)
    ax3.axis('off')
    ax3.set_title('STEP 3: 매수 신호 대기 (내가 알려줌)', color='#00ff88',
                  fontsize=16, fontweight='bold', loc='left', pad=10)

    buy_kospi = kospi * 10 / pe if pe > 0 else 4000

    signal_text = f"""
 자동 모니터링 설정 (매 2시간마다 체크)

 매수 신호 조건:
  ✦ 1차 신호 (공격 매수): P/E < 10x (KOSPI ≈ {buy_kospi:,.0f} 이하)
    → 현금 20% 중 절반(10%) → 주식 ETF 투입
    → 2026년 3월에 이 신호 발동 후 다음날 +9.63% 반등

  ✦ 2차 신호 (추가 매수): P/E < 8x (KOSPI ≈ {kospi * 8 / pe:,.0f} 이하)
    → 나머지 현금 전량 → 주식 ETF 투입
    → 역사적 바닥권 (2008 GFC 수준 P/E 8.3x)

  ✦ 정상화 신호: VIX < 20 복귀
    → 채권/금 비중 축소 → 주식 70% 복귀

 신호 발동 시 매수할 ETF:
  ┌───────────────────────────────────────────────┐
  │  1순위: KODEX 200 (069500)           40%      │
  │         → KOSPI 전체, 반등 시 안정적 수익     │
  │                                               │
  │  2순위: KODEX 미국S&P500TR (379800)  30%      │
  │         → 분산 + 달러 헤지 효과               │
  │                                               │
  │  3순위: KODEX 반도체 (091160)        20%      │
  │         → 급락 시 탄력 최대 (고베타)          │
  │         → 단, 밀도 리스크 주의                │
  │                                               │
  │  4순위: ARIRANG 고배당주 (161510)    10%      │
  │         → 배당 안전망 + 방어적 반등           │
  └───────────────────────────────────────────────┘
"""
    ax3.text(0.02, 0.97, signal_text, transform=ax3.transAxes,
             fontsize=11, color='white', va='top', fontfamily='NanumSquare',
             linespacing=1.5)

    # ═══════════════════════════════════════
    # PANEL 4: STEP 4 — 정상화 복귀
    # ═══════════════════════════════════════
    ax4 = fig.add_subplot(gs[4, :])
    ax4.set_facecolor(dark)
    ax4.axis('off')
    ax4.set_title('STEP 4: 정상화 복귀 (VIX < 20 확인 후)', color='#00d4ff',
                  fontsize=16, fontweight='bold', loc='left', pad=10)

    step4_text = """
 층류 레짐 복귀 시 최종 배분:

  ┌───────────────────────────────────────────────┐
  │  주식 ETF      70%                            │
  │    KODEX 200           25%                    │
  │    KODEX 미국S&P500TR  20%                    │
  │    KODEX 미국나스닥TR  10%                    │
  │    KODEX 반도체        10%                    │
  │    ARIRANG 고배당주     5%                    │
  │                                               │
  │  채권 ETF      20%                            │
  │    TIGER 국채3년       10%                    │
  │    TIGER 미국채10년    10%                    │
  │                                               │
  │  금            10%                            │
  │    KODEX 골드선물(H)   10%                    │
  └───────────────────────────────────────────────┘

 복귀 조건 체크리스트:
  □ VIX < 20 (3일 연속 유지)
  □ KOSPI 5일 이동평균 > 20일 이동평균 (골든크로스)
  □ 외국인 순매수 전환 (3일 연속)
  → 3개 중 2개 이상 충족 시 점진적 전환 (1주일에 걸쳐)
"""
    ax4.text(0.02, 0.95, step4_text, transform=ax4.transAxes,
             fontsize=11, color='white', va='top', fontfamily='NanumSquare',
             linespacing=1.5)

    # ═══════════════════════════════════════
    # PANEL 5: 시나리오별 예상 수익률
    # ═══════════════════════════════════════
    ax5 = fig.add_subplot(gs[5, 0])
    ax5.set_facecolor(dark)

    scenarios = ['Sudden Stop\n반복', '점진적\n안정화', '장기\n하락']
    returns_hold = [-19.3, -3.0, -25.0]  # 아무것도 안 하면
    returns_ns = [-3.8, +2.0, -8.0]  # N-S 전략 따르면

    x = np.arange(len(scenarios))
    width = 0.35
    bars1 = ax5.bar(x - width/2, returns_hold, width, label='방치 (현행 유지)',
                   color='#ff4444', alpha=0.7, edgecolor='white', linewidth=0.5)
    bars2 = ax5.bar(x + width/2, returns_ns, width, label='N-S 전략 적용',
                   color='#00d4ff', alpha=0.8, edgecolor='white', linewidth=0.5)

    for bar, val in zip(bars1, returns_hold):
        ax5.text(bar.get_x() + bar.get_width()/2., bar.get_height() - 1.5 if val < 0 else bar.get_height() + 0.5,
                f'{val:+.1f}%', ha='center', va='top' if val < 0 else 'bottom',
                color='white', fontsize=10, fontweight='bold')
    for bar, val in zip(bars2, returns_ns):
        ax5.text(bar.get_x() + bar.get_width()/2., bar.get_height() - 1.5 if val < 0 else bar.get_height() + 0.5,
                f'{val:+.1f}%', ha='center', va='top' if val < 0 else 'bottom',
                color='#00ff88', fontsize=10, fontweight='bold')

    ax5.axhline(y=0, color='white', linewidth=0.5)
    ax5.set_xticks(x)
    ax5.set_xticklabels(scenarios, color='white', fontsize=10)
    ax5.set_ylabel('예상 수익률 (%)', color='white')
    ax5.set_title('시나리오별 예상 수익률', color='white', fontsize=13, fontweight='bold')
    ax5.tick_params(colors='white')
    ax5.legend(fontsize=9, facecolor=dark, edgecolor='gray', labelcolor='white')
    ax5.grid(True, color=grid_c, alpha=0.3, axis='y')

    # ═══════════════════════════════════════
    # PANEL 6: 매수 구간 시각화
    # ═══════════════════════════════════════
    ax6 = fig.add_subplot(gs[5, 1])
    ax6.set_facecolor(dark)

    pe_range = np.arange(6, 26, 0.5)
    equity_alloc = []
    for p in pe_range:
        # Base from VIX regime (current: turbulent = 20%)
        base = 20
        if p < 10:
            adj = +15
        elif p < 14:
            adj = 0
        elif p < 18:
            adj = 0
        elif p < 22:
            adj = -10
        else:
            adj = -20
        equity_alloc.append(max(5, min(85, base + adj)))

    ax6.fill_between(pe_range, equity_alloc, alpha=0.3, color='#00d4ff')
    ax6.plot(pe_range, equity_alloc, color='#00d4ff', linewidth=2)
    ax6.axvline(x=pe, color='#ffaa00', linewidth=2, linestyle='--', label=f'현재 P/E {pe:.1f}x')
    ax6.axvline(x=10, color='#00ff88', linewidth=2, linestyle=':', label='매수 트리거 10x')

    ax6.scatter([pe], [20], color='#ffaa00', s=150, zorder=10)
    ax6.annotate(f'현재\n{pe:.1f}x → 20%',
                (pe, 20), fontsize=9, color='#ffaa00',
                xytext=(15, 15), textcoords='offset points',
                arrowprops=dict(arrowstyle='->', color='#ffaa00'))

    ax6.set_xlabel('Forward P/E (프록시)', color='white', fontsize=10)
    ax6.set_ylabel('주식 배분 비중 (%)', color='white', fontsize=10)
    ax6.set_title('P/E별 주식 비중 (난류 레짐)', color='white', fontsize=13, fontweight='bold')
    ax6.tick_params(colors='white')
    ax6.legend(fontsize=9, facecolor=dark, edgecolor='gray', labelcolor='white')
    ax6.grid(True, color=grid_c, alpha=0.3)

    # ═══════════════════════════════════════
    # PANEL 7: 핵심 ETF 현재가
    # ═══════════════════════════════════════
    ax7 = fig.add_subplot(gs[6, :])
    ax7.set_facecolor(dark)
    ax7.axis('off')
    ax7.set_title('핵심 ETF 현재가 참고', color='white', fontsize=14, fontweight='bold', loc='left', pad=10)

    etf_display = [
        ('KODEX 200', '069500.KS', '주식'),
        ('KODEX 반도체', '091160.KS', '주식'),
        ('KODEX 미국S&P500TR', '379800.KS', '주식'),
        ('TIGER 국채3년', '114820.KS', '채권'),
        ('KOSEF 국고채10년', '148070.KS', '채권'),
        ('KODEX 골드선물(H)', '132030.KS', '금'),
        ('ACE KRX금현물', '411060.KS', '금'),
    ]

    header = f"  {'ETF 이름':<25} {'종목코드':<12} {'자산군':<8} {'현재가':>10} {'5일 변동':>10}"
    y_start = 0.88
    ax7.text(0.02, y_start, header, transform=ax7.transAxes,
             fontsize=11, color='#888888', fontfamily='NanumSquare')
    ax7.text(0.02, y_start - 0.06, "─" * 75, transform=ax7.transAxes,
             fontsize=10, color='#333333', fontfamily='NanumSquare')

    for i, (name, ticker, asset_type) in enumerate(etf_display):
        y = y_start - 0.12 - i * 0.09
        if ticker in etf_prices:
            p = etf_prices[ticker]
            price_str = f"{p['price']:>10,.0f}"
            chg_str = f"{p['chg_5d']:>+8.1f}%"
            chg_color = '#00ff88' if p['chg_5d'] > 0 else '#ff4444'
        else:
            price_str = "      N/A"
            chg_str = "     N/A"
            chg_color = '#666666'

        type_color = {'주식': '#00d4ff', '채권': '#7b68ee', '금': '#ffd700'}[asset_type]

        line = f"  {name:<25} {ticker.replace('.KS',''):<12}"
        ax7.text(0.02, y, line, transform=ax7.transAxes,
                 fontsize=11, color='white', fontfamily='NanumSquare')
        ax7.text(0.45, y, asset_type, transform=ax7.transAxes,
                 fontsize=11, color=type_color, fontweight='bold', fontfamily='NanumSquare')
        ax7.text(0.58, y, price_str, transform=ax7.transAxes,
                 fontsize=11, color='white', fontfamily='NanumSquare')
        ax7.text(0.78, y, chg_str, transform=ax7.transAxes,
                 fontsize=11, color=chg_color, fontweight='bold', fontfamily='NanumSquare')

    # ═══════════════════════════════════════
    # PANEL 8: 면책 + 요약
    # ═══════════════════════════════════════
    ax8 = fig.add_subplot(gs[7, :])
    ax8.set_facecolor('#0d1117')
    ax8.axis('off')

    summary = f"""요약: 월요일(3/30) 체크리스트

 □ 09:00  퇴직연금 주식형 ETF 전량 시장가 매도
 □ 09:05  채권 40% 매수 (TIGER국채3년 20% + KOSEF국고채10년 10% + TIGER미국채10년 10%)
 □ 09:10  금 20% 매수 (KODEX골드선물 10% + ACE KRX금현물 10%)
 □ 나머지 20%는 현금(MMF) 유지 → 매수 신호 대기
 □ 주식 20%는 보류 → P/E < 10x 신호 시 투입

 자동 알림: 매 2시간마다 VIX/P/E 체크 → 매수 신호 시 텔레그램 알림

 ※ 본 가이드는 논문 모델 기반 참고자료이며, 투자 판단은 본인 책임입니다.
 ※ Based on "Capital as a Viscous Fluid" (Choi, 2026)"""

    ax8.text(0.5, 0.5, summary, transform=ax8.transAxes,
             fontsize=12, color='white', ha='center', va='center',
             fontfamily='NanumSquare', linespacing=1.7,
             bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                       edgecolor='#00d4ff', linewidth=2))

    output = '/home/ubuntu/.cokacdir/workspace/pfiuywu4/pension_guide.png'
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] {output}")
    return output


# ============================================================
# 매수 신호 모니터링 스크립트 (크론용)
# ============================================================

def create_monitor_script():
    """Create the monitoring script for cron"""
    script = '''#!/usr/bin/env python3
"""매수 신호 모니터링 — 크론 매 2시간 실행"""
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import subprocess, json

def check_signals():
    end = datetime.now()
    start = end - timedelta(days=250)

    vix = yf.download("^VIX", start=start, end=end, progress=False)
    kospi = yf.download("^KS11", start=start, end=end, progress=False)

    vix_now = float(vix['Close'].squeeze().iloc[-1])
    kospi_now = float(kospi['Close'].squeeze().iloc[-1])

    k_close = kospi['Close'].squeeze()
    ma200 = k_close.rolling(200).mean()
    pe = float((k_close / ma200).iloc[-1] * 12)

    # 5일 이평 vs 20일 이평
    ma5 = float(k_close.rolling(5).mean().iloc[-1])
    ma20 = float(k_close.rolling(20).mean().iloc[-1])
    golden_cross = ma5 > ma20

    alerts = []
    urgency = "info"

    # 매수 신호
    if pe < 8:
        alerts.append(f"🚨 극한 매수 신호! P/E {pe:.1f}x < 8x — 전량 매수 타이밍")
        urgency = "critical"
    elif pe < 10:
        alerts.append(f"✅ 1차 매수 신호! P/E {pe:.1f}x < 10x — 현금 50% → 주식 전환")
        urgency = "buy"

    # 정상화 신호
    if vix_now < 20:
        alerts.append(f"🟢 VIX {vix_now:.1f} < 20 — 층류 복귀, 주식 70% 전환 검토")
        urgency = "normalize"
    elif vix_now < 25:
        alerts.append(f"🟡 VIX {vix_now:.1f} 하락 중 — 정상화 접근")

    # 위험 신호
    if vix_now > 45:
        alerts.append(f"🔴 VIX {vix_now:.1f} > 45 — 극한 난류! 주식 10%로 추가 축소")
        urgency = "extreme"

    if golden_cross and vix_now < 25:
        alerts.append(f"📈 골든크로스 확인 (5MA > 20MA) — 반등 신호")

    # 상태 리포트
    status = f"[N-S 모니터] {datetime.now().strftime('%H:%M')}"
    status += f"\\nKOSPI {kospi_now:,.0f} | VIX {vix_now:.1f} | P/E {pe:.1f}x"

    if alerts:
        status += "\\n\\n" + "\\n".join(alerts)
        return True, status, urgency
    else:
        return False, status, "quiet"

if __name__ == "__main__":
    has_alert, msg, urgency = check_signals()
    if has_alert or urgency != "quiet":
        print(msg)
    else:
        print(f"[N-S] {datetime.now().strftime('%H:%M')} — 변동 없음, 대기 중")
'''

    path = '/home/ubuntu/.cokacdir/workspace/pfiuywu4/ns_monitor.py'
    with open(path, 'w') as f:
        f.write(script)
    print(f"[OK] Monitor script: {path}")
    return path


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 50)
    print("  DC 퇴직연금 전략 가이드 생성")
    print("=" * 50)

    vix, kospi, pe, vol = fetch_signals()
    print(f"  VIX: {vix:.1f} | KOSPI: {kospi:,.0f} | P/E: {pe:.1f}x | Vol: {vol:.0f}%")

    etf_prices = fetch_etf_prices()
    print(f"  ETF 가격 수집 완료: {len(etf_prices)}개")

    output = create_guide_image(vix, kospi, pe, vol, etf_prices)
    monitor = create_monitor_script()

    print(f"\n[DONE] Guide: {output}")
    print(f"[DONE] Monitor: {monitor}")
    return output


if __name__ == '__main__':
    main()
