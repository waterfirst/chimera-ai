# Chimera AI 진화 기록

> 기억, 실행, 검색, 인터넷, 키메라 아키텍처 등 업그레이드 과정을 기록한다.

---

## v0.1 — 기본 구성 (2026-03-27)
- **두뇌**: Claude Code (EC2 t3.micro, ap-northeast-2)
- **인터페이스**: Telegram 봇 (cokacdir)
- **기억**: 없음 (세션 단위 휘발)
- **실행**: bash, python3
- **검색**: 없음
- **음성**: 없음

## v0.2 — 음성 추가 (2026-03-28 오전)
- **음성**: GPT TTS (gpt-4o-mini-tts, nova) 도입
- 감정 인스트럭션 엔지니어링 (씬별 톤 변화)
- 한계 발견: 한국어 발음 부자연스러움 → edge-tts(SunHi) 병행 검토

## v0.3 — 키메라 아키텍처 확립 (2026-03-28 오전)
- **손발**: Gemini 2.5 Flash API 연동
- 3두 체제 확립: Claude(두뇌) + GPT(목소리) + Gemini(손발)
- 첫 합동작전: 1인 라디오쇼 (Gemini 검색 → Claude 대본 → GPT 음성)
- GitHub 레포 생성: waterfirst/chimera-ai

## v0.4 — 기억 시스템 도입 (2026-03-28 오후)
- **기억**: Walnut 구조 채택
  - `MEMORY.md` — 커널 인덱스
  - `now.md` — 현재 상태 (매 세션 갱신)
  - `tasks.md` — 작업 큐 (우선순위별)
  - `insights.md` — 검증된 지식
  - `profile.md` — 사용자 정체성
  - `hippocampus.md` — 대화 기록 (append-only)
- 설계 원칙: 기억 < 맥락. API 비용 0원, 전부 로컬 마크다운.

## v0.5 — 자동화 (2026-03-28 오후)
- **스케줄링**: cokacdir --cron 으로 반복 작업 설정
- 속보 모니터링: 2시간마다 뉴스 체크 → 있으면 텔레그램 전송
- **파일 전송**: cokacdir --sendfile 로 결과물 자동 전달

## v0.6 — 영상 생성 (2026-03-28 오후)
- DALL-E 3 이미지 + PIL 프레임 가공 + ffmpeg 조립
- Ken Burns 효과, 크로스페이드, 한글 자막(NanumSquareRound)
- numpy 앰비언트 패드 BGM 생성
- 한계 발견: DALL-E 씬 간 인물 불일치, Sora 수준 불가

---

## 현재 아키텍처 요약 (v0.6)

```
┌─────────────────────────────────────────┐
│              사용자 (Telegram)            │
│                    ↕                     │
│           cokacdir (중계/스케줄)          │
│                    ↕                     │
│  ┌─────────── Claude (두뇌) ──────────┐  │
│  │  사고 · 분석 · 대화 · 코딩 · 판단   │  │
│  │                                    │  │
│  │  [기억: Walnut 마크다운 커널]       │  │
│  │   now / tasks / insights / log     │  │
│  └────────┬──────────┬────────────────┘  │
│           │          │                   │
│     ┌─────▼──┐  ┌────▼─────┐             │
│     │GPT TTS │  │ Gemini   │             │
│     │(목소리) │  │(손발)    │             │
│     │nova    │  │검색/웹   │             │
│     └────────┘  └──────────┘             │
│                                          │
│  [도구] bash · python · DALL-E · ffmpeg  │
│  [MCP]  AgentQL (월300회 무료)           │
└─────────────────────────────────────────┘
```

## v0.7 — Navier-Stokes 자본흐름 예측 (2026-03-28 심야)
- **금융 모델**: 사용자 논문 "Capital as a Viscous Fluid" 기반 구현
- Navier-Stokes 방정식 → 금융 변수 매핑 (Table 1)
  - u(유속)=5일 수익률, ρ(밀도)=반도체 비중, p(압력)=P/E, ν(점성)=변동성, f(외력)=VIX
- VIX 레짐 분류: 층류(<20) → 천이(20-30) → 난류(30-45) → 극한(>45)
- ETF 배분 엔진: VIX 레짐 + P/E 압력-구배 리밸런싱
- 5일 흐름 전망 (단순화 N-S 수치 적분)
- 대시보드: 8패널 (KOSPI/u, ρ, p, ν, VIX, 힘분해, ETF파이, 요약)
- 데이터: yfinance 무료 API (KOSPI, VIX, 삼성전자, SK하이닉스, TNX, Gold)
- `capital_flow.py` — 단일 파일, 독립 실행

## v0.8 — Agent Reach: 인터넷 눈 장착 (2026-03-29)
- **검색**: Agent Reach v1.3.0 설치 — AI 에이전트 인터넷 접근 툴킷 (무료)
- **7/16 채널 활성화**:
  - ✅ Exa 시맨틱 검색 (전체 웹, 무료, API 키 불필요)
  - ✅ Jina Reader (임의 웹페이지 → 마크다운 변환)
  - ✅ YouTube 자막 추출 (yt-dlp)
  - ✅ RSS/Atom 피드 읽기
  - ✅ Bilibili 영상/자막/검색
  - ✅ V2EX 커뮤니티
  - ✅ WeChat 공식계정 글 (검색 + 읽기)
- **추가 도구 설치됨**: mcporter (MCP 서버 관리), bird CLI (Twitter용, 미인증)
- **환경**: `~/.agent-reach-venv/` (Python venv)
- **의미**: 기존에는 AgentQL(월 300회)과 WebFetch에 의존했으나, 이제 무제한 무료로 웹 전체 검색/읽기 가능
- **첫 실전 테스트**: "glass substrate semiconductor packaging 2026" → MIT Tech Review 최신 기사(2026-03-13) 즉시 검색 성공

## v0.8.1 — 팟캐스트 파이프라인 (2026-03-29)
- **팟캐스트 생성기**: Gemini(대본) → GPT TTS(2인 음성) → ffmpeg(결합)
- 2인 호스트: nova(여성) + onyx(남성), 자연스러운 한국어 대화체
- 첫 에피소드: 글래스 패키징 기술 세미나 (3.0MB, 16턴)
- GitHub 저장소: waterfirst/sunday-ai-coffee-club
- Podbbang 채널 연동: "일요 AI 커피 클럽" (32+ 에피소드)

## v0.8.2 — Google Cloud 인증 (2026-03-29)
- OAuth 2.0 PKCE 커스텀 플로우 구현 (headless EC2 대응)
- gcloud CLI 설치 (v562.0.0)
- Google Cloud 프로젝트 접근 토큰 확보 (cloud-platform 스코프)
- Discovery Engine API 활성화 (gemini-455003 프로젝트)
- NotebookLM Enterprise API는 소비자 계정 미지원 확인

## v0.9 — Gemini TTS: 목소리 혁명 (2026-03-29 심야)
- **음성 엔진 교체**: GPT TTS → Gemini TTS (`gemini-2.5-flash-preview-tts`)
- **완전 무료**: OpenAI API 비용 0원 (Gemini 무료 tier)
- 여성 호스트: Kore (한국어 네이티브 품질)
- 남성 호스트: Charon (깊은 톤)
- 자동 폴백: Gemini 실패 시 → OpenAI TTS 자동 전환
- PCM→MP3 실시간 변환 파이프라인 (ffmpeg)
- 짧은 대사 패딩 처리 (15자 미만 자동 보정)
- `--engine gemini|openai` CLI 옵션 추가
- **3두 완전 무료 체제 확립**: Claude(두뇌) + Gemini TTS(목소리) + Gemini Flash(손발)
- GPT는 범용 폴백으로 격하 (비용 절감)

---

## 현재 아키텍처 요약 (v0.9)

```
┌──────────────────────────────────────────────┐
│              사용자 (Telegram)                 │
│                    ↕                          │
│           cokacdir (중계/스케줄)               │
│                    ↕                          │
│  ┌─────────── Claude (두뇌) ──────────────┐   │
│  │  사고 · 분석 · 대화 · 코딩 · 판단      │   │
│  │                                        │   │
│  │  [기억: Walnut 마크다운 커널]           │   │
│  │   now / tasks / insights / log         │   │
│  └──┬──────────┬──────────┬───────────────┘   │
│     │          │          │                   │
│  ┌──▼──────┐ ┌▼───────┐ ┌▼────────────────┐  │
│  │Gemini   │ │Gemini  │ │ Agent Reach     │  │
│  │TTS 🆕  │ │Flash   │ │ (인터넷 눈)     │  │
│  │Kore     │ │검색    │ │ Exa/Jina/YT    │  │
│  │Charon   │ │대본    │ │ RSS/WeChat     │  │
│  └─────────┘ └────────┘ └────────────────┘  │
│                                               │
│  [폴백] GPT TTS(nova/onyx) + GPT 범용       │
│  [도구] bash·python·DALL-E·ffmpeg·gcloud     │
│  [MCP]  AgentQL(300/월) + mcporter(무제한)   │
│  [인증] Google OAuth PKCE 토큰 보유          │
└──────────────────────────────────────────────┘
```

---

## 다음 업그레이드 후보
- [ ] Agent Reach 추가 채널 활성화 (Twitter 인증, Reddit 프록시, 샤오홍슈 Docker)
- [ ] Gemini Live API 실시간 음성 대화 (WebSocket A2A)
- [ ] 영상 인물 일관성 (IP-Adapter / 참조 이미지 기법)
- [ ] NotebookLM 브라우저 자동화 (PC 환경에서 시도)
- [ ] 아들 에이전트 배포 (독립 워크스페이스)
- [ ] capsule 패턴 도입 (프로젝트별 독립 작업 단위)
- [x] ~~Gemini 웹 검색 자동화 강화~~ → Agent Reach로 대체 (v0.8)
- [x] ~~한국어 TTS 네이티브화~~ → Gemini TTS Kore/Charon (v0.9)
