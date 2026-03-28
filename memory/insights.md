# insights.md — 검증된 지식

## 기술
- GPT TTS(nova) 한국어 발음 부자연스러움 → 한국어는 edge-tts(SunHi) 또는 한국어 특화 TTS가 나음
- DALL-E 3 씬 간 인물 일관성 유지 불가 → 영상용 한계
- Gemini 2.5 Flash 무료 tier 넉넉, 검색/요약에 강함
- AgentQL 월 300회 무료, Google News/Yahoo Finance 차단
- PIL + ffmpeg: 슬라이드쇼 수준, Ken Burns + 크로스페이드 + 자막 가능
- NanumSquareRound: 한글 자막 최적 폰트

## 아키텍처
- 키메라: Claude(두뇌) + GPT(목소리) + Gemini(손발)
- 맥락 > 기억: now.md(상태) + tasks.md(큐) + insights.md(지식)
- 무료 API 우선, 토큰 절약
