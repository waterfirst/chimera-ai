#!/usr/bin/env python3
"""
Chimera Sentiment Scorer — 뉴스 감성 분석 점수화
친구 시스템의 FinBERT 감성분석(20점)을 참고하여 구축.
Gemini API로 한국어 뉴스 감성을 분석하고 0~100점 점수화.
"""

import json
import os
import re
from datetime import datetime, timedelta

# ============================================================
# 1. 뉴스 수집 (Google News RSS + 네이버)
# ============================================================

def fetch_news_headlines(query, max_results=10):
    """Google News RSS로 헤드라인 수집 (무료, API키 불필요)"""
    import urllib.request
    import xml.etree.ElementTree as ET

    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read())
        items = root.findall('.//item')[:max_results]
        headlines = []
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            headlines.append({'title': title, 'date': pub_date})
        return headlines
    except Exception as e:
        print(f"[WARN] 뉴스 수집 실패 ({query}): {e}")
        return []


# ============================================================
# 2. LLM 감성 분석 (Gemini API — 무료 티어)
# ============================================================

def analyze_sentiment_llm(headlines, topic="시장"):
    """Gemini API로 뉴스 헤드라인 감성 분석"""
    from google import genai

    api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyBUqu7RNyDpWyrh91wce61vrkoD0J4_4Gc')
    client = genai.Client(api_key=api_key)

    if not headlines:
        return {'score': 50, 'label': '중립', 'summary': '뉴스 데이터 없음', 'bullish': 0, 'bearish': 0}

    news_text = "\n".join([f"- {h['title']}" for h in headlines[:15]])

    prompt = f"""아래 {topic} 관련 뉴스 헤드라인을 분석하여 JSON으로 답하라.

뉴스:
{news_text}

다음 형식으로만 답하라 (다른 텍스트 없이 JSON만):
{{
  "score": 0~100 정수 (0=극도 비관, 50=중립, 100=극도 낙관),
  "label": "매우 비관/비관/약간 비관/중립/약간 낙관/낙관/매우 낙관" 중 하나,
  "bullish_count": 호재 뉴스 수,
  "bearish_count": 악재 뉴스 수,
  "top_bullish": "가장 강한 호재 한 줄 요약",
  "top_bearish": "가장 강한 악재 한 줄 요약",
  "summary": "전체 감성 요약 2줄"
}}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {'score': 50, 'label': '중립', 'summary': 'LLM 응답 파싱 실패'}
    except Exception as e:
        print(f"[WARN] LLM 감성 분석 실패: {e}")
        return {'score': 50, 'label': '중립', 'summary': f'API 오류: {e}'}


# ============================================================
# 3. 멀티 토픽 감성 대시보드
# ============================================================

TOPICS = {
    'KOSPI': '코스피 주식시장',
    '반도체': '반도체 삼성전자 SK하이닉스',
    '2차전지': '2차전지 배터리 LG에너지',
    '원자력': '원자력 SMR 한국수력원자력',
    'AI': 'AI 인공지능 엔비디아',
    '유가': '유가 WTI 원유 OPEC',
    '환율': '환율 원달러 외환',
    '미국증시': '미국 S&P500 나스닥 월스트리트',
}


def run_full_sentiment(topics=None):
    """전체 토픽 감성 분석 실행"""
    if topics is None:
        topics = TOPICS

    results = {}
    for key, query in topics.items():
        print(f"[감성] {key} 분석 중...")
        headlines = fetch_news_headlines(query, max_results=10)
        sentiment = analyze_sentiment_llm(headlines, topic=key)
        sentiment['headline_count'] = len(headlines)
        results[key] = sentiment

    # 종합 점수 계산 (가중 평균)
    weights = {'KOSPI': 2.0, '반도체': 1.5, 'AI': 1.5, '미국증시': 1.5,
               '2차전지': 1.0, '원자력': 1.0, '유가': 1.0, '환율': 1.0}

    total_weight = 0
    weighted_sum = 0
    for key, data in results.items():
        w = weights.get(key, 1.0)
        score = data.get('score', 50)
        weighted_sum += score * w
        total_weight += w

    overall_score = round(weighted_sum / total_weight) if total_weight > 0 else 50
    overall_label = score_to_label(overall_score)

    output = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'overall_score': overall_score,
        'overall_label': overall_label,
        'topics': results
    }

    # 파일 저장
    out_path = os.path.join(os.path.dirname(__file__), 'sentiment_latest.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[감성] 저장 완료: {out_path}")
    print(f"[감성] 종합 점수: {overall_score}/100 ({overall_label})")

    return output


def score_to_label(score):
    if score >= 80: return '매우 낙관'
    elif score >= 65: return '낙관'
    elif score >= 55: return '약간 낙관'
    elif score >= 45: return '중립'
    elif score >= 35: return '약간 비관'
    elif score >= 20: return '비관'
    else: return '매우 비관'


# ============================================================
# 4. 텔레그램 리포트 포맷
# ============================================================

def format_telegram_report(data):
    """감성 분석 결과를 텔레그램 메시지로 포맷"""
    lines = []
    lines.append(f"📊 감성 분석 대시보드 ({data['timestamp'][:10]})")
    lines.append(f"종합: {data['overall_score']}/100 ({data['overall_label']})")
    lines.append("─" * 25)

    for key, val in data['topics'].items():
        score = val.get('score', 50)
        label = val.get('label', '중립')
        emoji = '🟢' if score >= 60 else '🟡' if score >= 40 else '🔴'
        lines.append(f"{emoji} {key}: {score}점 ({label})")

    return "\n".join(lines)


if __name__ == '__main__':
    result = run_full_sentiment()
    print("\n" + format_telegram_report(result))
