"""Gemini 2.5 Flash - 키메라의 손발
검색, 유튜브 추천, 웹 탐색 등 외부 세계와의 인터페이스
"""
import os
import json
import requests

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"

def ask_gemini(prompt: str) -> str:
    """Gemini에게 질문하고 텍스트 응답을 받는다."""
    response = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}]
        }
    )
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def search_youtube(query: str, count: int = 5) -> str:
    """Gemini를 경유한 유튜브 검색/추천"""
    prompt = f"""유튜브에서 "{query}" 관련 영상 {count}개를 추천해줘.
각각 영상 제목, 아티스트/채널, 유튜브 URL을 알려줘. 실제 존재하는 영상만."""
    return ask_gemini(prompt)


def get_weather(location: str = "수원") -> str:
    """Gemini를 통한 날씨 정보"""
    from datetime import date
    today = date.today().isoformat()
    prompt = f"오늘 {today} {location} 날씨를 알려줘. 기온, 하늘 상태, 미세먼지 정보 포함."
    return ask_gemini(prompt)


if __name__ == "__main__":
    # 테스트
    print("=== 날씨 ===")
    print(get_weather())
    print("\n=== 유튜브 검색 ===")
    print(search_youtube("토요일 아침 카페 음악"))
