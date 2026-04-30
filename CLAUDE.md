# Chimera-AI 프로젝트 규칙

## Project Overview
- **키메라 AI 경제분석 매거진** — 다중 AI 모델(Claude, GPT, Gemini) 기반 주간 증시·경제 분석 보고서
- GitHub Pages: https://waterfirst.github.io/chimera-ai/
- 저자: Nakcho Choi | Alpha Hunter x Chimera-AI

## Important Rules

### 1. 개인 연금 콘텐츠 금지
- **개인 연금(pension) 관련 콘텐츠는 이 프로젝트에 포함하지 않는다.**
- 연금 포트폴리오 제안, 퇴직연금/개인연금 잔고 등 개인 재정 정보를 넣지 않는다.
- pension_strategy_guide.py 등 연금 관련 파일은 생성·커밋하지 않는다.

### 2. Alpha Hunter는 별도 저장소
- Alpha Hunter 보고서는 이 매거진에 포함하지 않는다.
- Alpha Hunter 저장소: https://github.com/waterfirst/alpha-hunter
- 이 매거진의 "관련 프로젝트" 섹션에 링크만 유지한다.

## 주간 리포트 발행 프로세스

### 발행 주기
- **매주 일요일 저녁 20:00 (KST)** — 한 주간(월~금) 증시 데이터를 종합하여 발행

### 기술 스택
- **R + ggplot2** — 차트 생성 (Plotly 사용 금지, 파일 용량 문제)
- **Quarto (.qmd)** — 보고서 렌더링
- `lightbox: true` — 차트 클릭 시 줌인 가능
- `self-contained: true` — 단일 HTML 파일로 배포
- `dev: ragg_png` — CJK 폰트 렌더링
- 폰트: `"Noto Sans CJK KR"` (시스템 폰트 직접 사용, showtext 사용 금지)

### 파일 명명 규칙
```
reports/chimera-weekly-YYYY-MM-DD.qmd   # Quarto 소스
reports/chimera-weekly-YYYY-MM-DD.html  # 렌더링된 보고서
```
- 날짜는 해당 주의 마지막 거래일 기준

### Quarto YAML 헤더 템플릿
```yaml
---
title: "Chimera-AI 주간 증시 분석 리포트"
subtitle: "N월 N주차 (MM.DD~MM.DD) — 핵심 요약"
author: "Chimera-AI Multi-Agent System"
date: "YYYY-MM-DD"
format:
  html:
    theme: darkly
    toc: true
    toc-depth: 3
    toc-location: left
    number-sections: true
    code-fold: true
    code-tools: true
    self-contained: true
    lightbox: true
    smooth-scroll: true
    page-layout: article
    fig-align: center
    fig-width: 10
    fig-height: 6
knitr:
  opts_chunk:
    dev: ragg_png
    dpi: 150
execute:
  echo: false
  warning: false
  message: false
---
```

### ggplot2 차트 규칙
1. **3자리 hex 색상 금지** — `"#aaa"` 사용 금지, 반드시 `"#aaaaaa"` 6자리로 작성 (Quarto+ragg 호환 문제)
2. **showtext 사용 금지** — Quarto knitr 환경에서 충돌. 시스템 폰트 직접 사용
3. **다크 테마 커스텀 함수** — `theme_chimera()` 사용
4. **lightbox 활성화** — 각 차트 청크에 `#| lightbox: true` 추가

```r
kfont <- "Noto Sans CJK KR"

theme_chimera <- function(base_size = 13) {
  theme_minimal(base_size = base_size) +
    theme(
      plot.background = element_rect(fill = "#1a1a2e", color = NA),
      panel.background = element_rect(fill = "#1a1a2e", color = NA),
      panel.grid.major = element_line(color = "#2a2a4a", linewidth = 0.3),
      panel.grid.minor = element_blank(),
      text = element_text(family = kfont, color = "#e4e4ec"),
      axis.text = element_text(color = "#aaaaaa"),
      axis.title = element_text(color = "#cccccc", size = rel(0.9)),
      plot.title = element_text(color = "#f59e0b", face = "bold", size = rel(1.2)),
      plot.subtitle = element_text(color = "#888888", size = rel(0.85)),
      plot.caption = element_text(color = "#666666", size = rel(0.7)),
      legend.background = element_rect(fill = "#1a1a2e", color = NA),
      legend.text = element_text(color = "#cccccc"),
      legend.title = element_text(color = "#f59e0b"),
      strip.text = element_text(color = "#f59e0b", face = "bold")
    )
}
```

### 보고서 필수 섹션
1. **핵심 요약** (Executive Summary) — KPI 카드 + 주요 지표 테이블
2. **글로벌 증시 동향** — 미국(다우/S&P/나스닥), 유럽, 아시아
3. **한국 증시 분석** — KOSPI, KOSDAQ, 대형주/중소형주 양극화
4. **섹터 분석** — 업종별 히트맵 + 바차트
5. **TACO 모델 분석** — Trump-Adjusted Capital Oscillator 6대 팩터
6. **리스크 요인** — 과열 지표 대시보드
7. **투자 전략** — 시나리오별(강세/횡보/약세) 탭 패널
8. **다음 주 전망** — 경제 캘린더 + 실적 발표 일정

### 필수 차트 (최소 6개)
1. 미국 지수 일간/월간 수익률 (patchwork 조합)
2. KOSPI 일별 추이 + 거래대금 (patchwork 상하 조합)
3. 시가총액별 수익률 비교 (양극화)
4. 업종별 히트맵 + 바차트 (patchwork 조합)
5. TACO 리스크 팩터 롤리팝 차트
6. 과열 경고 지표 바차트
7. 포트폴리오 배분 도넛 차트

### 데이터 수집 방법
1. **웹 검색** — 주간 증시 뉴스, FOMC, 지정학 이슈
2. **yfinance** (가능한 경우) — 주가, 환율, 유가, VIX 정량 데이터
3. **주요 소스** — Bloomberg, CNBC, 한국경제, Investing.com, KRX

### 발행 절차
```bash
# 1. chimera-ai 레포 클론
cd /tmp && git clone https://github.com/waterfirst/chimera-ai.git

# 2. 데이터 수집 (웹 검색 + yfinance)

# 3. .qmd 파일 작성
#    reports/chimera-weekly-YYYY-MM-DD.qmd

# 4. Quarto 렌더링
cd /tmp/chimera-ai/reports
quarto render chimera-weekly-YYYY-MM-DD.qmd

# 5. index.html 목차 업데이트
#    - 새 보고서를 최상단에 추가 (NEW 태그)
#    - 이전 보고서에서 NEW 태그 제거

# 6. Git 커밋 & 푸시
cd /tmp/chimera-ai
git add reports/chimera-weekly-YYYY-MM-DD.qmd reports/chimera-weekly-YYYY-MM-DD.html index.html
git commit -m "feat: N월 N주차 주간 보고서 발행"
git push origin main

# 7. 텔레그램으로 보고서 파일 전송
cokacdir --sendfile reports/chimera-weekly-YYYY-MM-DD.html --chat CHAT_ID --key KEY

# 8. GitHub Pages URL 안내
# https://waterfirst.github.io/chimera-ai/reports/chimera-weekly-YYYY-MM-DD.html
```

### index.html 목차 카드 템플릿
```html
<div class="card"><a href="reports/chimera-weekly-YYYY-MM-DD.html">
<div class="row"><span class="tag t-new">NEW</span><span class="tag t-wk">WN</span><span class="date">YYYY.MM.DD</span></div>
<h3>주간 증시 분석 — N월 N주차 (MM.DD~MM.DD)</h3>
<div class="sub">핵심 키워드 · 핵심 키워드 · 핵심 키워드</div>
<div class="scope">미국 · 한국 · 글로벌 매크로</div>
</a></div>
```

## Repository Structure
```
chimera-ai/
├── index.html              # 매거진 메인 페이지 (목차)
├── hero.png                # 스플래시 이미지
├── CLAUDE.md               # 프로젝트 규칙 (이 파일)
├── reports/
│   ├── chimera-weekly-YYYY-MM-DD.qmd   # Quarto 소스
│   ├── chimera-weekly-YYYY-MM-DD.html  # 렌더링된 보고서
│   ├── chimera-weekly-report-0427.html # 기존 보고서
│   ├── chimera-weekly-report-0424.html
│   ├── weekly_report.html
│   └── NS_KOSPI_Paper_Final.pdf
├── agents/                 # 에이전트 설정
├── config/                 # 설정 파일
├── memory/                 # 메모리 저장소
└── voice/                  # 보이스 설정
```

## Related Projects
- Alpha Hunter: https://github.com/waterfirst/alpha-hunter
- Insight Lab: https://github.com/waterfirst/insight-lab
- OLED Viewing Angle: https://github.com/waterfirst/oled-viewing-angle
