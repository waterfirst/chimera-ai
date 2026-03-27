"""AgentQL - 자연어 웹 데이터 추출
월 300회 무료, 구조화된 JSON 반환
"""
import os
import json
import requests

AGENTQL_API_KEY = os.getenv("AGENTQL_API_KEY")
AGENTQL_URL = "https://api.agentql.com/v1/query-data"

def extract_web_data(url: str, prompt: str) -> dict:
    """웹페이지에서 자연어로 데이터 추출"""
    response = requests.post(
        AGENTQL_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AGENTQL_API_KEY}"
        },
        json={
            "url": url,
            "prompt": prompt
        }
    )
    return response.json()


# 검증된 사이트 목록
VERIFIED_SITES = {
    "hackernews": ("https://news.ycombinator.com", "top 10 stories with title, url, points, comments count"),
    "huggingface": ("https://huggingface.co/models?sort=trending", "top 10 trending models with name, task, downloads"),
    "arxiv_oled": ("https://arxiv.org/search/?query=OLED&searchtype=all&order=-announced_date_first", "latest 5 papers with title, authors, abstract, date"),
    "google_patents": ("https://patents.google.com/?q=samsung+display+OLED&oq=samsung+display+OLED", "top 10 patents with title, assignee, inventors, publication date, patent number"),
    "github_trending": ("https://github.com/trending", "top 10 trending repositories with name, description, stars, language"),
}

# 차단된 사이트 (사용 금지)
BLOCKED_SITES = ["Google News", "Yahoo Finance"]


if __name__ == "__main__":
    # HackerNews 테스트
    url, prompt = VERIFIED_SITES["hackernews"]
    result = extract_web_data(url, prompt)
    print(json.dumps(result, indent=2, ensure_ascii=False))
