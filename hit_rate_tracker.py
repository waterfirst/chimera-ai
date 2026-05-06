#!/usr/bin/env python3
"""
Chimera Hit Rate Tracker — 모멘텀 판정 적중률 자동 추적
친구 시스템의 '주간 적중률 55% 미만 시 자동 경고'를 참고하여 구축.

매주 모멘텀 기반 매수/매도/홀드 판정을 기록하고,
N주 후 실제 수익률과 비교하여 적중률을 계산한다.
"""

import json
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.dirname(__file__)
HISTORY_FILE = os.path.join(DATA_DIR, 'hit_rate_history.json')
ALERT_THRESHOLD = 55  # 적중률 이 미만이면 경고


# ============================================================
# 1. 판정 기록
# ============================================================

def load_history():
    """기존 판정 이력 로드"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'predictions': [], 'weekly_reports': []}


def save_history(data):
    """판정 이력 저장"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_prediction(etf_name, action, momentum_rank, momentum_score,
                      current_price=None, reason=""):
    """모멘텀 판정 기록

    Args:
        etf_name: ETF 이름
        action: 'BUY' / 'SELL' / 'HOLD' / 'REDUCE'
        momentum_rank: 모멘텀 순위
        momentum_score: 모멘텀 점수
        current_price: 현재가 (나중에 수익률 계산용)
        reason: 판정 근거
    """
    history = load_history()

    prediction = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'etf_name': etf_name,
        'action': action,
        'momentum_rank': momentum_rank,
        'momentum_score': momentum_score,
        'price_at_prediction': current_price,
        'reason': reason,
        'verified': False,
        'actual_return_1w': None,
        'actual_return_2w': None,
        'hit': None
    }

    history['predictions'].append(prediction)
    save_history(history)
    print(f"[적중률] 기록: {etf_name} → {action} (순위 {momentum_rank})")
    return prediction


# ============================================================
# 2. 판정 검증 (N주 후 실제 수익률 확인)
# ============================================================

def verify_predictions(lookback_days=14):
    """미검증 판정을 yfinance로 검증"""
    import yfinance as yf

    history = load_history()
    today = datetime.now()
    verified_count = 0

    # ETF 이름 → yfinance 티커 매핑
    ticker_map = {
        'TIGER 반도체TOP10': '396500.KS',
        'KODEX 200': '069500.KS',
        'RISE 네트워크인프라': '464290.KS',
        'TIGER 코리아원자력': '462290.KS',
        'SOL 조선TOP3플러스': '466920.KS',
        'KODEX 미국S&P500': '379800.KS',
        'KODEX 200타겟위클리커버드콜': '441680.KS',
        'TIGER 크리아이전략기기TOP3플러스': '472150.KS',
        'PLUS 고배당주': '161510.KS',
    }

    for pred in history['predictions']:
        if pred['verified']:
            continue

        pred_date = datetime.strptime(pred['date'], '%Y-%m-%d')
        days_elapsed = (today - pred_date).days

        if days_elapsed < 7:
            continue  # 최소 1주 대기

        etf = pred['etf_name']
        ticker = ticker_map.get(etf)
        if not ticker:
            continue

        try:
            data = yf.download(ticker, start=pred_date - timedelta(days=1),
                             end=min(today, pred_date + timedelta(days=lookback_days + 3)),
                             progress=False)
            if data.empty or len(data) < 2:
                continue

            close = data['Close'].squeeze()
            base_price = pred['price_at_prediction'] or float(close.iloc[0])

            # 1주 수익률
            if len(close) >= 6:
                price_1w = float(close.iloc[min(5, len(close)-1)])
                pred['actual_return_1w'] = round((price_1w / base_price - 1) * 100, 2)

            # 2주 수익률
            if len(close) >= 11:
                price_2w = float(close.iloc[min(10, len(close)-1)])
                pred['actual_return_2w'] = round((price_2w / base_price - 1) * 100, 2)

            # 적중 판정
            ret = pred['actual_return_2w'] or pred['actual_return_1w']
            if ret is not None:
                action = pred['action']
                if action == 'BUY' and ret > 0:
                    pred['hit'] = True
                elif action == 'SELL' and ret < 0:
                    pred['hit'] = True  # 매도 판정 후 실제 하락 = 적중
                elif action == 'REDUCE' and ret < 2:
                    pred['hit'] = True  # 비중 축소 후 상승 미미 = 적중
                elif action == 'HOLD' and abs(ret) < 5:
                    pred['hit'] = True  # 홀드 후 안정적 = 적중
                else:
                    pred['hit'] = False

                pred['verified'] = True
                verified_count += 1

        except Exception as e:
            print(f"[WARN] 검증 실패 ({etf}): {e}")

    save_history(history)
    print(f"[적중률] {verified_count}개 판정 검증 완료")
    return verified_count


# ============================================================
# 3. 적중률 리포트
# ============================================================

def compute_hit_rate(weeks=4):
    """최근 N주간 적중률 계산"""
    history = load_history()

    cutoff = datetime.now() - timedelta(weeks=weeks)
    verified = [p for p in history['predictions']
                if p['verified'] and datetime.strptime(p['date'], '%Y-%m-%d') >= cutoff]

    if not verified:
        return {
            'total': 0, 'hits': 0, 'rate': 0,
            'alert': False, 'message': '검증된 판정 없음'
        }

    hits = sum(1 for p in verified if p['hit'])
    total = len(verified)
    rate = round(hits / total * 100, 1) if total > 0 else 0

    # 액션별 적중률
    by_action = {}
    for action in ['BUY', 'SELL', 'HOLD', 'REDUCE']:
        action_preds = [p for p in verified if p['action'] == action]
        if action_preds:
            a_hits = sum(1 for p in action_preds if p['hit'])
            by_action[action] = {
                'total': len(action_preds),
                'hits': a_hits,
                'rate': round(a_hits / len(action_preds) * 100, 1)
            }

    # 경고 체크
    alert = rate < ALERT_THRESHOLD and total >= 5

    result = {
        'period': f'최근 {weeks}주',
        'total': total,
        'hits': hits,
        'rate': rate,
        'by_action': by_action,
        'alert': alert,
        'message': f'⚠️ 적중률 {rate}% — {ALERT_THRESHOLD}% 미만! 모델 재검토 필요' if alert
                   else f'✅ 적중률 {rate}% ({hits}/{total})'
    }

    # 주간 리포트 기록
    history['weekly_reports'].append({
        'date': datetime.now().strftime('%Y-%m-%d'),
        'rate': rate,
        'total': total,
        'hits': hits,
        'alert': alert
    })
    # 최근 52주만 유지
    history['weekly_reports'] = history['weekly_reports'][-52:]
    save_history(history)

    return result


def format_telegram_report():
    """적중률 리포트를 텔레그램 메시지로 포맷"""
    report = compute_hit_rate(weeks=4)
    lines = []

    if report['alert']:
        lines.append(f"🚨 모멘텀 판정 적중률 경고!")
    else:
        lines.append(f"📈 모멘텀 판정 적중률 리포트")

    lines.append(f"{report['period']}: {report['rate']}% ({report['hits']}/{report['total']})")
    lines.append("─" * 25)

    for action, data in report.get('by_action', {}).items():
        emoji = '🟢' if data['rate'] >= 60 else '🟡' if data['rate'] >= 45 else '🔴'
        lines.append(f"{emoji} {action}: {data['rate']}% ({data['hits']}/{data['total']})")

    lines.append("")
    lines.append(report['message'])

    return "\n".join(lines)


# ============================================================
# 4. 키메라 모멘텀 데이터에서 자동 판정 기록
# ============================================================

def auto_record_from_momentum(momentum_file='etf_momentum_results.json'):
    """ETF 모멘텀 결과에서 자동으로 판정 기록"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, momentum_file)

    if not os.path.exists(filepath):
        print(f"[적중률] 모멘텀 파일 없음: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 포트폴리오 종목 매핑
    portfolio = {
        'RISE 네트워크인프라': {},
        'TIGER 반도체TOP10': {},
        'TIGER 코리아원자력': {},
        'SOL 조선TOP3플러스': {},
        'KODEX 200타겟위클리커버드콜': {},
    }

    for item in data.get('etfs', data) if isinstance(data, dict) else data:
        name = item.get('name', '')
        for pname in portfolio:
            if pname in name or name in pname:
                rank = item.get('rank', 999)
                score = item.get('score', 0)
                rank_change = item.get('rank_change', 0)

                # 자동 판정 룰
                if rank <= 20 and rank_change >= 0:
                    action = 'BUY'
                    reason = f'상위 {rank}위, 순위 유지/상승'
                elif rank <= 50:
                    action = 'HOLD'
                    reason = f'{rank}위, 중상위권'
                elif rank <= 80 and rank_change < -10:
                    action = 'REDUCE'
                    reason = f'{rank}위, 순위 하락 {rank_change}'
                elif rank > 80:
                    action = 'SELL'
                    reason = f'하위 {rank}위, 모멘텀 소진'
                else:
                    action = 'HOLD'
                    reason = f'{rank}위'

                record_prediction(pname, action, rank, score, reason=reason)
                break

    print("[적중률] 모멘텀 기반 자동 판정 기록 완료")


if __name__ == '__main__':
    # 1. 미검증 판정 검증
    verify_predictions()

    # 2. 적중률 리포트
    print("\n" + format_telegram_report())
