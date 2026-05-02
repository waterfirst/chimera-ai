# Chimera-AI 경제분석 매거진

<context>
다중 AI 모델(Claude, GPT, Gemini) 기반 주간 증시·경제 분석 보고서 매거진.
GitHub Pages: https://waterfirst.github.io/chimera-ai/
저자: Nakcho Choi | Alpha Hunter x Chimera-AI
매주 일요일 20:00 KST에 한 주간(월~금) 증시 데이터를 종합하여 발행한다.
</context>

<instructions>

## 콘텐츠 범위

이 저장소는 주간 증시·경제 분석 보고서만 포함한다.

개인 재정(연금, 퇴직금, 재무설계 등) 콘텐츠는 이 프로젝트의 범위 밖이다.
pension 관련 파일이 발견되면 삭제하고 커밋에서 제외한다.
투자 전략 섹션에서도 연금 포트폴리오 제안은 작성하지 않는다.

Alpha Hunter 보고서는 별도 저장소(https://github.com/waterfirst/alpha-hunter)에서 관리한다.
이 매거진의 "관련 프로젝트" 섹션에 링크만 유지한다.

</instructions>

<technical_stack>

## 기술 스택

R + ggplot2로 차트를 생성한다. Plotly는 파일 용량이 비대해지므로 사용하지 않는다.
시계열/그룹 비교 시각화는 tidyplots 패키지를 우선 사용한다 (ggplot2 래퍼, 코드 간결, 출판 품질). tidyplots가 적합하지 않은 복잡한 커스텀 차트는 ggplot2 직접 사용.
Quarto (.qmd)로 보고서를 렌더링하며, 아래 설정을 따른다:

- `lightbox: true` — 차트를 클릭하면 줌인할 수 있어서 독자의 데이터 탐색 경험이 향상된다
- `self-contained: true` — 단일 HTML로 배포하여 GitHub Pages에서 바로 열린다
- `dev: ragg_png` — ragg 디바이스가 CJK 폰트를 정상 렌더링한다
- 폰트: `"Noto Sans CJK KR"` 시스템 폰트를 직접 사용한다. showtext는 Quarto knitr 환경에서 grid.Call 충돌을 일으키므로 사용하지 않는다.
- 색상: 6자리 hex만 사용한다 (`"#aaaaaa"`). 3자리 hex(`"#aaa"`)는 Quarto+ragg 조합에서 "invalid RGB specification" 에러를 발생시킨다.

</technical_stack>

<quarto_template>

## Quarto YAML 헤더 템플릿

```yaml
---
title: "Chimera-AI 주간 증시 분석 리포트"
subtitle: "N월 N주차 (MM.DD~MM.DD) — 핵심 요약"
author: "Chimera-AI Multi-Agent System"
date: "YYYY-MM-DD"
format:
  html:
    theme:
      dark: darkly
      light: flatly
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

</quarto_template>

<chart_theme>

## ggplot2 다크 테마

각 차트 청크에 `#| lightbox: true`를 추가하여 줌인을 활성화한다.

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

</chart_theme>

<report_structure>

## 보고서 구조

파일명: `reports/chimera-weekly-YYYY-MM-DD.qmd` (날짜는 해당 주 마지막 거래일 기준)

### 필수 섹션 (순서대로)
1. 핵심 요약 — KPI 카드 + 주요 지표 테이블
2. 글로벌 증시 동향 — 미국(다우/S&P/나스닥), 유럽, 아시아
3. 한국 증시 분석 — KOSPI, KOSDAQ, 대형주/중소형주 양극화
4. 섹터 분석 — 업종별 히트맵 + 바차트
5. TACO 모델 분석 — Trump-Adjusted Capital Oscillator 6대 팩터
6. 리스크 요인 — 과열 지표 대시보드
7. 투자 전략 — 시나리오별(강세/횡보/약세) 탭 패널
8. 다음 주 전망 — 경제 캘린더 + 실적 발표 일정

### 필수 차트 (최소 6개, 모두 `#| lightbox: true`)
1. 미국 지수 일간/월간 수익률 (patchwork 조합)
2. KOSPI 일별 추이 + 거래대금
3. 시가총액별 수익률 비교 (양극화)
4. 업종별 히트맵 + 바차트
5. TACO 리스크 팩터 롤리팝 차트
6. 과열 경고 지표 바차트
7. 포트폴리오 배분 도넛 차트

### 데이터 수집
- 웹 검색: 주간 증시 뉴스, FOMC, 지정학 이슈
- yfinance: 주가, 환율, 유가, VIX 정량 데이터
- 주요 소스: Bloomberg, CNBC, 한국경제, Investing.com, KRX

</report_structure>

<publishing_workflow>

## 발행 절차

```bash
# 1. 레포 클론
cd /tmp && git clone https://github.com/waterfirst/chimera-ai.git

# 2. 데이터 수집 (웹 검색 + yfinance)

# 3. .qmd 작성 (위 YAML 헤더 + theme_chimera() 사용)

# 4. 렌더링
cd /tmp/chimera-ai/reports && quarto render chimera-weekly-YYYY-MM-DD.qmd

# 5. index.html 목차 업데이트: 새 보고서를 최상단에 NEW 태그로 추가, 이전 보고서 NEW 태그 제거

# 6. 커밋 & 푸시
git add reports/chimera-weekly-YYYY-MM-DD.qmd reports/chimera-weekly-YYYY-MM-DD.html index.html
git commit -m "feat: N월 N주차 주간 보고서 발행"
git push origin main

# 7. 텔레그램 전송
cokacdir --sendfile reports/chimera-weekly-YYYY-MM-DD.html --chat CHAT_ID --key KEY
```

### index.html 카드 템플릿
```html
<div class="card"><a href="reports/chimera-weekly-YYYY-MM-DD.html">
<div class="row"><span class="tag t-new">NEW</span><span class="tag t-wk">WN</span><span class="date">YYYY.MM.DD</span></div>
<h3>주간 증시 분석 — N월 N주차 (MM.DD~MM.DD)</h3>
<div class="sub">핵심 키워드 · 핵심 키워드 · 핵심 키워드</div>
<div class="scope">미국 · 한국 · 글로벌 매크로</div>
</a></div>
```

</publishing_workflow>

<investigate_before_answering>
코드를 수정하기 전에 반드시 해당 파일을 읽어라.
열지 않은 파일의 내용을 추측하지 말고, 실제 코드를 확인한 뒤 답변한다.
기존 보고서의 스타일, 구조, 데이터 형식을 확인한 뒤 새 보고서를 작성한다.
</investigate_before_answering>

<avoid_overengineering>
요청된 변경만 수행한다.
변경하지 않은 코드에 주석이나 타입 어노테이션을 추가하지 않는다.
한 번만 사용하는 로직에 헬퍼 함수나 추상화를 만들지 않는다.
보고서 차트는 위 필수 차트 목록에 집중하고, 불필요한 추가 시각화를 넣지 않는다.
</avoid_overengineering>

<frontend_aesthetics>
index.html을 수정할 때, 기존 매거진의 다크 테마(#0a0a14 배경, #f59e0b 액센트)와 카드 레이아웃 패턴을 유지한다.
새 카드를 추가할 때 기존 카드의 태그 스타일(t-new, t-wk, t-sp)과 클래스 구조를 따른다.
</frontend_aesthetics>

<session_protocol>

## 세션 종료 프로토콜

세션을 어떻게 종료하느냐가 컨텍스트 관리와 코드 품질에 직결된다.
모든 세션 종료 시 아래 5단계를 순서대로 수행한다.

### 1. Cleanup (정리)
- 임시 파일(.knit.md, _files/), 디버그 코드를 삭제한다
- `git status`로 의도하지 않은 변경 사항이 없는지 확인한다
- /tmp에 클론한 레포의 중간 산출물을 정리한다

### 2. Verify (확인)
- `quarto render`가 에러 없이 완료되었는지 확인한다
- 생성된 HTML의 차트가 정상 렌더링되고, lightbox 줌인이 작동하는지 점검한다
- index.html 목차의 링크가 올바른 파일을 가리키는지 확인한다
- `git diff`로 최종 변경 내역을 리뷰한다

### 3. Reflect (배움)
- 이번 세션에서 발견한 기술적 제약이나 해결 패턴을 기록한다
  (예: "3자리 hex가 Quarto+ragg에서 에러", "showtext+patchwork 충돌")
- 시장 데이터 수집 과정에서 막힌 소스가 있으면 대체 경로를 메모한다
- 다음 주 보고서에서 개선할 점을 파악한다

### 4. Persist (기억)
- 새로 발견한 규칙이나 제약을 이 CLAUDE.md에 반영한다
- 보고서 발행 이력을 git log로 추적할 수 있도록 커밋 메시지를 명확히 작성한다
- 시장 분석에서 반복 사용할 데이터 소스나 패턴을 memory/에 기록한다

### 5. Ship (인계)
- `git push origin main`으로 변경 사항을 원격에 반영한다
- GitHub Pages 배포 완료 후 URL을 사용자에게 전달한다
- 다음 세션이 이어받을 수 있도록 컨텍스트를 남긴다:
  이번 주 보고서 상태, 남은 작업, 다음 주 주요 이벤트

</session_protocol>

## Repository Structure

```
chimera-ai/
├── index.html              # 매거진 메인 페이지 (목차)
├── hero.png                # 스플래시 이미지
├── CLAUDE.md               # 프로젝트 규칙 (이 파일)
├── reports/                # 주간 보고서 (.qmd + .html)
├── agents/                 # 에이전트 설정
├── config/                 # 설정 파일
├── memory/                 # 메모리 저장소
└── voice/                  # 보이스 설정
```

## Related Projects
- Alpha Hunter: https://github.com/waterfirst/alpha-hunter
- Insight Lab: https://github.com/waterfirst/insight-lab
- OLED Viewing Angle: https://github.com/waterfirst/oled-viewing-angle
