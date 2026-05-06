#!/usr/bin/env python3
"""
Chimera Enhanced Daily Report — 감성 + 수급 + 적중률 통합 리포트
기존 포트폴리오 트래커에 3대 업그레이드 모듈을 결합한 일일 종합 리포트.
"""

import json
import os
import sys
from datetime import datetime

# 같은 디렉토리의 모듈 import
sys.path.insert(0, os.path.dirname(__file__))
from sentiment_scorer import run_full_sentiment, format_telegram_report as fmt_sentiment
from supply_demand_scorer import run_etf_supply_demand, format_telegram_report as fmt_supply
from hit_rate_tracker import verify_predictions, compute_hit_rate, format_telegram_report as fmt_hitrate


def run_enhanced_daily():
    """통합 일일 리포트 실행"""
    print("=" * 50)
    print(f"Chimera Enhanced Daily Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    results = {}

    # ── Step 1: 감성분석 ──
    print("\n[1/4] 감성분석 실행...")
    try:
        sentiment = run_full_sentiment()
        results['sentiment'] = sentiment
        print(f"  → 종합: {sentiment['overall_score']}/100 ({sentiment['overall_label']})")
    except Exception as e:
        print(f"  → 실패: {e}")
        results['sentiment'] = None

    # ── Step 2: 수급분석 ──
    print("\n[2/4] 수급분석 실행...")
    try:
        supply = run_etf_supply_demand()
        results['supply_demand'] = supply
        print(f"  → 완료: {len(supply.get('results', {}))}개 종목")
    except Exception as e:
        print(f"  → 실패: {e}")
        results['supply_demand'] = None

    # ── Step 3: 적중률 검증 ──
    print("\n[3/4] 적중률 검증...")
    try:
        verified = verify_predictions()
        hitrate = compute_hit_rate(weeks=4)
        results['hit_rate'] = hitrate
        print(f"  → {hitrate['message']}")
    except Exception as e:
        print(f"  → 실패: {e}")
        results['hit_rate'] = None

    # ── Step 4: 통합 리포트 생성 ──
    print("\n[4/4] 통합 리포트 생성...")
    report = format_combined_report(results)

    # 저장
    out_path = os.path.join(os.path.dirname(__file__), 'daily_enhanced_latest.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    report_path = os.path.join(os.path.dirname(__file__), 'daily_enhanced_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n저장: {out_path}")
    print(f"리포트: {report_path}")
    return report


def format_combined_report(results):
    """통합 텔레그램 리포트 포맷"""
    lines = []
    today = datetime.now().strftime('%Y-%m-%d')

    lines.append(f"🔮 Chimera 종합 일일 리포트 ({today})")
    lines.append("═" * 30)

    # ── 감성분석 ──
    sent = results.get('sentiment')
    if sent:
        score = sent['overall_score']
        label = sent['overall_label']
        emoji = '🟢' if score >= 60 else '🟡' if score >= 40 else '🔴'
        lines.append(f"\n📊 뉴스 감성: {emoji} {score}/100 ({label})")

        # 토픽별 한 줄
        topics = sent.get('topics', {})
        top_bull = max(topics.items(), key=lambda x: x[1].get('score', 0)) if topics else None
        top_bear = min(topics.items(), key=lambda x: x[1].get('score', 0)) if topics else None
        if top_bull:
            lines.append(f"  최강: {top_bull[0]} {top_bull[1].get('score', 0)}점")
        if top_bear:
            lines.append(f"  최약: {top_bear[0]} {top_bear[1].get('score', 0)}점")

        # 호재/악재 요약
        for key, val in topics.items():
            bull = val.get('top_bullish', '')
            bear = val.get('top_bearish', '')
            if bull and key in ['KOSPI', '반도체', '미국증시']:
                lines.append(f"  📈 {key}: {bull}")
            if bear and key in ['KOSPI', '유가', '환율']:
                lines.append(f"  📉 {key}: {bear}")
    else:
        lines.append("\n📊 뉴스 감성: 데이터 없음")

    # ── 수급분석 ──
    supply = results.get('supply_demand')
    if supply and supply.get('results'):
        lines.append(f"\n💰 수급 분석:")
        for name, val in supply['results'].items():
            score = val.get('score', 50)
            label = val.get('label', '중립')
            emoji = '🟢' if score >= 60 else '🟡' if score >= 40 else '🔴'
            f_net = val.get('foreign_5d_net', '')
            f_str = ''
            if isinstance(f_net, int) and f_net != 0:
                f_str = f" (외인5일:{'+' if f_net > 0 else ''}{f_net:,})"
            lines.append(f"  {emoji} {name}: {score}점{f_str}")
    else:
        lines.append(f"\n💰 수급: 장중/장후 실행 시 데이터 수집")

    # ── 적중률 ──
    hr = results.get('hit_rate')
    if hr:
        if hr['total'] > 0:
            emoji = '🚨' if hr.get('alert') else '✅'
            lines.append(f"\n🎯 적중률: {emoji} {hr['rate']}% ({hr['hits']}/{hr['total']})")
            for action, data in hr.get('by_action', {}).items():
                lines.append(f"  {action}: {data['rate']}% ({data['hits']}/{data['total']})")
            if hr.get('alert'):
                lines.append(f"  ⚠️ {hr['message']}")
        else:
            lines.append(f"\n🎯 적중률: 판정 누적 중 (다음 주부터 검증)")
    else:
        lines.append(f"\n🎯 적중률: 초기화 중")

    # ── 종합 판단 ──
    lines.append(f"\n{'═' * 30}")
    sent_score = sent['overall_score'] if sent else 50
    if sent_score >= 65:
        lines.append("📌 종합: 감성 낙관 — 모멘텀 상위 ETF 유지/확대")
    elif sent_score >= 45:
        lines.append("📌 종합: 감성 중립 — 현 포지션 유지, 관망")
    else:
        lines.append("📌 종합: 감성 비관 — 방어적 포지션, 현금 비중 확대 검토")

    return "\n".join(lines)


if __name__ == '__main__':
    report = run_enhanced_daily()
    print("\n" + report)
