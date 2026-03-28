#!/usr/bin/env python3
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
    status += f"\nKOSPI {kospi_now:,.0f} | VIX {vix_now:.1f} | P/E {pe:.1f}x"

    if alerts:
        status += "\n\n" + "\n".join(alerts)
        return True, status, urgency
    else:
        return False, status, "quiet"

if __name__ == "__main__":
    has_alert, msg, urgency = check_signals()
    if has_alert or urgency != "quiet":
        print(msg)
    else:
        print(f"[N-S] {datetime.now().strftime('%H:%M')} — 변동 없음, 대기 중")
