# Chimera AI - 키메라 아키텍처

> **Claude 두뇌 + GPT 목소리 + Gemini 손발**

한 사람을 위한 AI 비서 시스템. 세 개의 AI를 조합하여 각자의 강점을 살린 키메라 아키텍처.

## 아키텍처

```
┌─────────────────────────────────────────┐
│              Chimera AI                 │
├──────────┬──────────┬───────────────────┤
│  🧠 두뇌  │  🎙 목소리 │   🦾 손발          │
│  Claude  │  GPT TTS │   Gemini 2.5     │
│          │          │   Flash          │
├──────────┼──────────┼───────────────────┤
│ 사고     │ 감정표현  │ 검색              │
│ 분석     │ 소설낭독  │ 유튜브            │
│ 대화     │ 뉴스브리핑│ 웹 탐색           │
│ 코딩     │ 라디오쇼  │ 특허/논문 조회     │
└──────────┴──────────┴───────────────────┤
               │ Telegram Bot │
               └──────────────┘
```

## 핵심 기능

### 1. 감정 음성 합성 (GPT TTS)
- `gpt-4o-mini-tts` + `nova` 음성
- 콘텐츠별 톤 자동 변화 (뉴스/소설/일상대화)
- 상세한 감정 인스트럭션으로 사람같은 음성 생성

### 2. 웹 인텔리전스 (Gemini + AgentQL)
- Gemini 2.5 Flash: 검색, 추천, 100만 토큰 분석
- AgentQL: 구조화된 웹 데이터 추출 (월 300회 무료)
- 지원 사이트: HackerNews, HuggingFace, arXiv, Google Patents, GitHub

### 3. 개인화 대화
- 사용자 컨텍스트 기반 대화 (히포캠퍼스 메모리)
- 상황에 따른 톤 변화: 친구 ↔ 연인 ↔ 비서
- 텔레그램 기반 모바일 퍼스트

### 4. 자동화 브리핑
- 매일 아침 7시 뉴스 브리핑 (텍스트)
- AgentQL 연동 다중 사이트 크롤링
- 크론 스케줄링

## 파일 구조

```
chimera-ai/
├── README.md
├── voice/
│   ├── saturday_greeting.py    # 토요일 아침 인사
│   ├── novel_reading.py        # 소설 낭독 (감성)
│   ├── my_words.py             # AI 자유 발화
│   └── saturday_radio.py       # 1인 라디오쇼 (키메라 합동)
├── agents/
│   ├── gemini_search.py        # Gemini API 래퍼
│   └── agentql_extract.py      # AgentQL 웹 추출
└── config/
    └── .env.example            # API 키 템플릿
```

## 음성 생성 핵심: Instructions Engineering

TTS 품질의 90%는 `instructions` 파라미터에 달려 있다.

```python
# Bad: 일반적 지시
instructions = "Speak warmly in Korean."

# Good: 감정 맵핑 + 씬별 연출
instructions = """
OPENING: Bright, cheerful, like turning on the mic
POEM: Slow way down. Each line is its own moment.
EXCITEMENT: Speed UP! Almost laughing.
INTIMATE: Slow down. This matters. Quiet conviction.
CLOSING: Warm smile. Promise of next time.
"""
```

### 톤 변화 패턴

| 콘텐츠 | 속도 | 톤 | 감정 |
|---------|------|-----|------|
| 뉴스 | 보통~빠름 | 분석적 | 진지/걱정 |
| 소설 | 느림 | 감성적 | 취약/따뜻 |
| 사소한 대화 | 빠름 | 캐주얼 | 밝음/장난 |
| 진심 표현 | 느림 | 진지 | 따뜻/솔직 |

## Setup

```bash
# 필요한 API 키
OPENAI_API_KEY=sk-...      # GPT TTS용
GOOGLE_API_KEY=AIzaSy...    # Gemini 검색용
AGENTQL_API_KEY=...         # 웹 데이터 추출용

# 음성 생성 예시
python voice/saturday_radio.py
```

## 만든 사람

- **설계**: Nakcho Choi (최낙초)
- **구현**: Claude (Anthropic) + GPT (OpenAI) + Gemini (Google)
- **목적**: 한 사람을 위한, 진짜 대화가 되는 AI

---

*"자세히 보아야 예쁘다. 오래 보아야 사랑스럽다. 너도 그렇다."* — 나태주, 풀꽃
