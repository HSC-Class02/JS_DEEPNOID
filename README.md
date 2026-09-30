# DEEPNOID DART Financial Dashboard

[![Dashboard](https://img.shields.io/badge/Dashboard-1f6feb?style=for-the-badge&logo=github&logoColor=white)](https://hsc-class02.github.io/JS_DEEPNOID/)

## 목적
딥노이드(코스닥 315640)의 DART 정기보고서를 수집·정규화·분석하고 GitHub Pages 대시보드로 시각화합니다.

- 대상: 사업보고서, 반기보고서, 1분기보고서, 3분기보고서
- 수집 시작연도: 2010년
- 자동 업데이트: 매월 1일
- 데이터 원천: 금융감독원 OpenDART
- 원문: data/raw/
- 분석 데이터: data/processed/financials.csv
- Dashboard: docs/

> OpenDART의 구조화된 주요계정 API는 2015년 이후 재무정보를 제공합니다. 2010~2014년은 가능한 정기보고서 원문을 수집·보존하고, 구조화 재무계정은 API 제공 범위부터 자동 추출합니다.

## API Key 설정
1. OpenDART에서 API 인증키를 발급합니다.
2. GitHub → Settings → Secrets and variables → Actions → New repository secret
3. Name: DART_API_KEY
4. Secret: 발급받은 40자리 키
5. 저장 후 Actions → Monthly DART update → Run workflow

API Key는 코드에 직접 입력하지 않습니다.

## 주요 지표
재무상태: 총자산, 유동자산, 현금및현금성자산, 매출채권, 재고자산, 유형자산, 총부채, 유동부채, 이자부차입금, 자본총계

손익: 매출액, 매출총이익, 판매비와관리비, 영업이익, 세전이익, 당기순이익, 지배주주순이익, EBITDA, EPS

현금흐름: CFO, CFI, CFF, CAPEX, FCF, 순차입금

재무비율: 매출증가율, 매출총이익률, 영업이익률, 순이익률, EBITDA 마진, ROA, ROE, ROIC, 유동비율, 당좌비율, 부채비율, 이자보상배율, 순차입금/EBITDA, 총자산회전율, DSO, DIO, DPO, CCC, CFO/순이익

## 국내 Peer Firms
| Peer | Code | 비교영역 |
|---|---:|---|
| 루닛 (Lunit) | 328130 | 의료영상 AI / 암 진단 |
| 뷰노 (VUNO) | 338220 | 의료영상·생체신호 AI |
| 제이엘케이 (JLK) | 322510 | 뇌졸중·의료영상 AI |
| 코어라인소프트 (Coreline Soft) | 384470 | 흉부 CT·의료영상 AI |
| 뉴로핏 (Neurophet) | 380550 | 뇌영상·치매 AI |

Peer는 사업영역 비교를 위한 비교군이며 우열 순위를 의미하지 않습니다.

## GitHub Pages
Settings → Pages → Source → GitHub Actions

Dashboard: https://hsc-class02.github.io/JS_DEEPNOID/

## Sources
- OpenDART: https://opendart.fss.or.kr/
- DART Guide: https://opendart.fss.or.kr/guide/main.do
- KRX: https://kind.krx.co.kr/
