# DEEPNOID DART Financial Dashboard

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-2563eb?style=for-the-badge)](https://hsc-class02.github.io/JS_DEEPNOID/)

딥노이드(코스닥 315640)의 DART 정기보고서를 수집·정규화·분석하고 GitHub Pages에서 시각화하는 자동화 프로젝트입니다.

## 1. 수집 범위
- 사업보고서 (Annual)
- 반기보고서 (Half-year)
- 1분기·3분기보고서 (Quarterly)
- 수집 시작연도: **2010년**
- 자동 업데이트: **매월 1일**
- 데이터 원천: 금융감독원 OpenDART
- 원문 공시: `data/raw/`
- 분석 데이터: `data/processed/financials.csv`
- Dashboard: `docs/index.html`

> OpenDART의 구조화된 주요계정 API는 2015년 이후 재무정보를 제공합니다. 따라서 2010~2014년은 DART에서 이용 가능한 정기보고서 원문을 우선 보존하고, 구조화 재무계정은 API 제공 범위부터 자동 추출합니다. 딥노이드의 실제 공시 시작시점에 따라 특정 연도/보고서가 존재하지 않을 수 있습니다.

## 2. API Key 설정
OpenDART 인증키를 발급한 뒤 **GitHub Repository Secret**에 저장합니다.

1. GitHub Repository → **Settings**
2. **Secrets and variables → Actions**
3. **New repository secret**
4. Name: `DART_API_KEY`
5. Secret: OpenDART에서 발급받은 인증키
6. **Actions → Monthly DART update → Run workflow**로 수동 실행해 테스트

API Key를 `company.json`이나 Python 코드에 직접 넣지 마세요.

### 로컬 실행
Windows PowerShell:
```powershell
$env:DART_API_KEY="YOUR_KEY"
python scripts/update_data.py
python scripts/build_dashboard.py
```

macOS/Linux:
```bash
export DART_API_KEY="YOUR_KEY"
python scripts/update_data.py
python scripts/build_dashboard.py
```

## 3. 자동 업데이트
`.github/workflows/monthly_dart_update.yml`이 매월 1일 00:00 UTC에 실행됩니다. 한국시간으로는 **매월 1일 오전 9시**입니다.

워크플로는 다음 순서로 동작합니다.

**OpenDART → 공시 목록 → 원문 ZIP 보존 → 구조화 재무정보 → 재무비율 → Dashboard → GitHub commit → GitHub Pages 배포**

## 4. 주요 분석 지표
### 재무상태
총자산, 유동자산, 현금및현금성자산, 매출채권, 재고자산, 유형자산, 총부채, 유동부채, 이자부차입금, 자본총계

### 손익
매출액, 매출총이익, 판매비와관리비, 영업이익, 세전이익, 당기순이익, 지배주주순이익, EPS, EBITDA proxy

### 현금흐름
CFO, CFI, CFF, CAPEX, FCF, 순차입금

### 재무비율
매출증가율, 매출총이익률, 영업이익률, 순이익률, EBITDA 마진, ROA, ROE, ROIC, 유동비율, 당좌비율, 부채비율, 총자산회전율, DSO, DIO, DPO, CCC, CFO/순이익, 순차입금/EBITDA

> 일부 지표는 DART 계정명과 기업별 회계표시 방식에 따라 결측될 수 있습니다. 특히 EBITDA/CAPEX/DPO 등은 공시 계정 구조가 일관되지 않아 현재 버전에서는 확인 가능한 계정만 계산하며, 원문 주석 검토가 필요합니다.

## 5. 국내 Peer Firms
| Peer | Code | 비교영역 |
|---|---:|---|
| 루닛 (Lunit) | 328130 | 의료영상 AI / 암 진단 |
| 뷰노 (VUNO) | 338220 | 의료영상·생체신호 AI |
| 제이엘케이 (JLK) | 322510 | 뇌졸중·의료영상 AI |
| 코어라인소프트 (Coreline Soft) | 384470 | 흉부 CT·의료영상 AI |
| 뉴로핏 (Neurophet) | 380550 | 뇌영상·치매 AI |

Peer는 사업영역 비교를 위한 분석 비교군이며 우열 순위나 투자등급을 의미하지 않습니다.

## 6. GitHub Pages
Repository → **Settings → Pages → Build and deployment → Source: GitHub Actions**

배포 주소:
https://hsc-class02.github.io/JS_DEEPNOID/

## 7. 프로젝트 구조
```
JS_DEEPNOID/
├─ .github/workflows/
│  ├─ monthly_dart_update.yml
│  └─ pages.yml
├─ config/company.json
├─ scripts/
│  ├─ update_data.py
│  └─ build_dashboard.py
├─ data/
│  ├─ raw/
│  └─ processed/
└─ docs/index.html
```

## Sources
- OpenDART: https://opendart.fss.or.kr/
- OpenDART Guide: https://opendart.fss.or.kr/guide/main.do
- DART: https://dart.fss.or.kr/
- KRX: https://kind.krx.co.kr/
