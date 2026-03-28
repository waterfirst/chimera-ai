# Memory Kernel (Walnut 구조)

## 커널 파일
- **now.md** — 현재 상태, 활성 캡슐, 다음 행동
- **tasks.md** — 작업 큐 (우선순위별)
- **insights.md** — 검증된 기술/사용자/아키텍처 지식
- **profile.md** — 사용자 정체성 (key.md 역할)
- **hippocampus.md** — 대화 기록 (log.md, append-only)

## 설계 원칙
> AI 에이전트의 가장 큰 문제는 기억력이 아니라 **맥락**이다.
> 맥락은 AI 안의 기능이 아니라, AI 아래에 깔리는 레이어다.
> — Walnut 프로젝트에서 영감

## 핵심 규칙
- 세션 끝 → now.md 갱신
- 검증된 사실 → insights.md
- 작업 변동 → tasks.md
- 사적 대화 → hippocampus.md (append-only)
- API 비용 0원 — 전부 로컬 마크다운
