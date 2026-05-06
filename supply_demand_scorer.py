#!/usr/bin/env python3
"""
Chimera Supply-Demand Scorer — 외국인/기관 수급 점수화
친구 시스템의 수급 25점 모델을 참고하여 구축.
pykrx로 외국인/기관 순매수 데이터를 수집하고 0~100점 점수화.
"""

import json
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 1. 수급 데이터 수집 (pykrx — 무료)
# ============================================================

def fetch_investor_data(ticker, days=20):
    """pykrx로 외국인/기관 순매수 데이터 수집"""
    from pykrx import stock

    end = datetime.now()
    start = end - timedelta(days=days + 10)  # 여유분

    start_str = start.strftime('%Y%m%d')
    end_str = end.strftime('%Y%m%d')

    try:
        df = stock.get_market_trading_volume_by_date(start_str, end_str, ticker)
        if df.empty:
            return None
        # 최근 N일만
        df = df.tail(days)
        return df
    except Exception as e:
        print(f"[WARN] pykrx 수급 데이터 실패 ({ticker}): {e}")
        return None


def fetch_market_investor_data(market="KOSPI", days=20):
    """시장 전체 외국인/기관 순매수"""
    from pykrx import stock

    end = datetime.now()
    start = end - timedelta(days=days + 10)

    start_str = start.strftime('%Y%m%d')
    end_str = end.strftime('%Y%m%d')

    try:
        df = stock.get_market_trading_volume_by_date(start_str, end_str, market)
        if df.empty:
            return None
        return df.tail(days)
    except Exception as e:
        print(f"[WARN] 시장 수급 데이터 실패 ({market}): {e}")
        return None


# ============================================================
# 2. 수급 점수 계산 (0~100)
# ============================================================

def compute_supply_demand_score(df):
    """외국인/기관 수급 데이터를 100점 만점으로 점수화

    점수 구성:
    - 외국인 흐름 (40점): 최근 5일 순매수 추세 + 누적
    - 기관 흐름 (30점): 최근 5일 순매수 추세 + 누적
    - 수급 모멘텀 (30점): 최근 5일 vs 이전 15일 비교
    """
    if df is None or df.empty:
        return {'score': 50, 'foreign_score': 25, 'inst_score': 25, 'momentum_score': 25,
                'detail': '데이터 없음'}

    # 컬럼명 확인 (pykrx 버전에 따라 다를 수 있음)
    cols = df.columns.tolist()

    # 외국인, 기관 컬럼 찾기
    foreign_col = None
    inst_col = None
    for c in cols:
        if '외국인' in c:
            foreign_col = c
        if '기관' in c:
            inst_col = c

    if foreign_col is None or inst_col is None:
        # 컬럼명이 다르면 인덱스로
        if len(cols) >= 5:
            foreign_col = cols[3]  # 보통 외국인
            inst_col = cols[1]     # 보통 기관
        else:
            return {'score': 50, 'detail': f'컬럼 매핑 실패: {cols}'}

    foreign = df[foreign_col].values
    inst = df[inst_col].values

    # --- 외국인 점수 (40점) ---
    f_recent_5 = foreign[-5:].sum() if len(foreign) >= 5 else foreign.sum()
    f_total = foreign.sum()
    f_trend = sum(1 for i in range(1, min(5, len(foreign))) if foreign[-i] > 0)

    # 정규화: 순매수 양에 따라 0~40
    f_score = 20  # 기본 중립
    if f_recent_5 > 0:
        f_score = min(40, 20 + min(20, f_trend * 4 + 4))
    elif f_recent_5 < 0:
        f_score = max(0, 20 - min(20, (5 - f_trend) * 4 + 4))

    # --- 기관 점수 (30점) ---
    i_recent_5 = inst[-5:].sum() if len(inst) >= 5 else inst.sum()
    i_trend = sum(1 for i in range(1, min(5, len(inst))) if inst[-i] > 0)

    i_score = 15
    if i_recent_5 > 0:
        i_score = min(30, 15 + min(15, i_trend * 3 + 3))
    elif i_recent_5 < 0:
        i_score = max(0, 15 - min(15, (5 - i_trend) * 3 + 3))

    # --- 모멘텀 점수 (30점) ---
    if len(foreign) >= 10:
        recent = (foreign[-5:].sum() + inst[-5:].sum())
        earlier = (foreign[-10:-5].sum() + inst[-10:-5].sum())
        if earlier != 0:
            momentum_ratio = recent / abs(earlier) if earlier != 0 else 1
        else:
            momentum_ratio = 1.0 if recent >= 0 else -1.0

        m_score = 15
        if momentum_ratio > 1.5:
            m_score = 28
        elif momentum_ratio > 1.0:
            m_score = 22
        elif momentum_ratio > 0.5:
            m_score = 18
        elif momentum_ratio > 0:
            m_score = 12
        else:
            m_score = 5
    else:
        m_score = 15

    total = f_score + i_score + m_score

    return {
        'score': total,
        'foreign_score': f_score,
        'inst_score': i_score,
        'momentum_score': m_score,
        'foreign_5d_net': int(f_recent_5),
        'inst_5d_net': int(i_recent_5),
        'foreign_trend': f'{f_trend}/5 매수일',
        'inst_trend': f'{i_trend}/5 매수일',
        'label': score_to_label(total)
    }


def score_to_label(score):
    if score >= 80: return '강력 매수세'
    elif score >= 65: return '매수 우위'
    elif score >= 55: return '약매수'
    elif score >= 45: return '중립'
    elif score >= 35: return '약매도'
    elif score >= 20: return '매도 우위'
    else: return '강력 매도세'


# ============================================================
# 3. ETF 수급 분석 (키메라 모멘텀과 연동)
# ============================================================

# 주요 ETF 티커 매핑
ETF_TICKERS = {
    'TIGER 반도체TOP10': '396500',
    'KODEX 200': '069500',
    'RISE 네트워크인프라': '464290',
    'TIGER 코리아원자력': '462290',
    'SOL 조선TOP3플러스': '466920',
    'ACE 구글밸류체인액티브': '487230',
    'KODEX 미국S&P500': '379800',
}


def run_etf_supply_demand(etf_map=None):
    """주요 ETF 수급 점수 일괄 분석"""
    if etf_map is None:
        etf_map = ETF_TICKERS

    results = {}

    # 시장 전체
    print("[수급] KOSPI 전체 분석...")
    mkt_data = fetch_market_investor_data("KOSPI", days=20)
    mkt_score = compute_supply_demand_score(mkt_data)
    results['KOSPI_전체'] = mkt_score

    # 개별 ETF
    for name, ticker in etf_map.items():
        print(f"[수급] {name} ({ticker}) 분석...")
        data = fetch_investor_data(ticker, days=20)
        score = compute_supply_demand_score(data)
        score['ticker'] = ticker
        results[name] = score

    # 파일 저장
    output = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'results': results
    }

    out_path = os.path.join(os.path.dirname(__file__), 'supply_demand_latest.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[수급] 저장 완료: {out_path}")

    return output


def format_telegram_report(data):
    """수급 분석 결과를 텔레그램 메시지로 포맷"""
    lines = []
    lines.append(f"💰 수급 분석 대시보드 ({data['timestamp'][:10]})")
    lines.append("─" * 25)

    for name, val in data['results'].items():
        score = val.get('score', 50)
        label = val.get('label', '중립')
        emoji = '🟢' if score >= 60 else '🟡' if score >= 40 else '🔴'
        f_net = val.get('foreign_5d_net', 'N/A')
        lines.append(f"{emoji} {name}: {score}/100 ({label})")
        if isinstance(f_net, int):
            f_str = f"+{f_net:,}" if f_net > 0 else f"{f_net:,}"
            lines.append(f"   외국인5일: {f_str}주")

    return "\n".join(lines)


if __name__ == '__main__':
    result = run_etf_supply_demand()
    print("\n" + format_telegram_report(result))
