from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "financials.csv"
OUT = ROOT / "docs" / "index.html"

if not DATA.exists():
    raise SystemExit("financials.csv not found")

df = pd.read_csv(DATA).sort_values(["year", "category", "report_code"])
annual = df[df.category == "Annual"].sort_values("year")
half = df[df.category == "Half-year"].sort_values("year")
quarter = df[df.category == "Quarterly"].sort_values(["year", "report_code"])
latest = df.iloc[-1]


def fmt(v, pct=False, decimals=0):
    """
    Format numeric dashboard values safely.

    OpenDART-derived CSV fields can occasionally be read as strings when a
    column contains mixed values. Convert numeric-looking strings before
    applying Python's numeric format specifiers, and preserve genuine text.
    """
    if pd.isna(v):
        return "—"

    if isinstance(v, str):
        raw = v.strip()
        if raw in {"", "—", "-"}:
            return "—"
        numeric = pd.to_numeric(raw, errors="coerce")
        if pd.isna(numeric):
            return raw
        v = float(numeric)
    else:
        numeric = pd.to_numeric(v, errors="coerce")
        if pd.isna(numeric):
            return str(v)
        v = float(numeric)

    if pct:
        return f"{v * 100:,.1f}%"
    return f"{v:,.{decimals}f}"


def table(data, columns):
    head = "".join(f"<th>{label}</th>" for _, label in columns)
    body = []
    for _, row in data.iterrows():
        cells = []
        for key, _ in columns:
            pct = key in {
                "revenue_growth", "gross_margin", "operating_margin", "net_margin",
                "ebitda_margin", "roa", "roe", "roic", "debt_ratio",
                "current_ratio", "quick_ratio"
            }
            value = row.get(key)
            if key in {"current_ratio", "quick_ratio", "asset_turnover"}:
                text_value = fmt(value, False, 2)
            elif key in {"dso", "dio", "dpo", "ccc"}:
                text_value = fmt(value, False, 1)
            else:
                text_value = fmt(value, pct)
            cells.append(f"<td>{text_value}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        "<table><thead><tr>" + head + "</tr></thead><tbody>"
        + "".join(body) + "</tbody></table>"
    )


annual_cols = [
    ("year", "연도"), ("revenue", "매출액"), ("operating_income", "영업이익"),
    ("net_income", "순이익"), ("cfo", "CFO"), ("fcf", "FCF"), ("cash", "현금"),
    ("total_assets", "총자산"), ("total_liabilities", "총부채"),
    ("total_equity", "자본"), ("operating_margin", "영업이익률"),
    ("net_margin", "순이익률"), ("debt_ratio", "부채비율"), ("roe", "ROE"),
]
period_cols = [
    ("year", "연도"), ("period", "기간"), ("revenue", "매출액"),
    ("operating_income", "영업이익"), ("net_income", "순이익"),
    ("cfo", "CFO"), ("fcf", "FCF"), ("cash", "현금"),
    ("current_ratio", "유동비율"), ("debt_ratio", "부채비율"),
]

labels = annual.year.astype(int).tolist()
series = {}
for key in ["revenue", "operating_income", "net_income", "cash", "total_liabilities", "total_equity"]:
    series[key] = [None if pd.isna(x) else float(x) for x in annual[key]]

margin = [None if pd.isna(x) else float(x) * 100 for x in annual.operating_margin]
net_margin = [None if pd.isna(x) else float(x) * 100 for x in annual.net_margin]
growth = [None if pd.isna(x) else float(x) * 100 for x in annual.revenue_growth]

peers = [
    ("루닛 (Lunit)", "328130", "의료영상 AI / 암 진단"),
    ("뷰노 (VUNO)", "338220", "의료영상·생체신호 AI"),
    ("제이엘케이 (JLK)", "322510", "뇌졸중·의료영상 AI"),
    ("코어라인소프트 (Coreline Soft)", "384470", "흉부 CT·의료영상 AI"),
    ("뉴로핏 (Neurophet)", "380550", "뇌영상·치매 AI"),
]
peer_html = "".join(
    f"<tr><td>{name}</td><td>{code}</td><td>{area}</td></tr>"
    for name, code, area in peers
)

cards = [
    ("Latest Revenue", fmt(latest.get("revenue"))),
    ("Operating Income", fmt(latest.get("operating_income"))),
    ("Net Income", fmt(latest.get("net_income"))),
    ("Cash & Equivalents", fmt(latest.get("cash"))),
    ("Operating Margin", fmt(latest.get("operating_margin"), True)),
    ("Current Ratio", fmt(latest.get("current_ratio"), False, 2)),
    ("Debt Ratio", fmt(latest.get("debt_ratio"), True)),
    ("ROE", fmt(latest.get("roe"), True)),
]
card_html = "".join(
    f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>'
    for label, value in cards
)

html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DEEPNOID DART Financial Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{{--bg:#f4f7fb;--card:#fff;--text:#172033;--muted:#64748b;--line:#e2e8f0;--accent:#2563eb}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,Arial,sans-serif}}
.wrap{{max-width:1380px;margin:auto;padding:30px 22px 60px}}
.hero{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}}
h1{{font-size:32px;margin:8px 0}} h2{{font-size:20px;margin:0 0 16px}}
.muted{{color:var(--muted);line-height:1.55}}
.badge{{display:inline-block;padding:6px 10px;border-radius:999px;background:#dbeafe;color:#1d4ed8;font-size:12px;font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.card,.section{{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:0 4px 18px rgba(15,23,42,.04)}}
.card{{padding:17px}} .label{{font-size:12px;color:var(--muted)}} .value{{font-size:23px;font-weight:750;margin-top:8px}}
.section{{padding:20px;margin-top:18px}} .charts{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.chart{{height:350px;position:relative}} .table{{overflow:auto;max-height:560px;border:1px solid var(--line);border-radius:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:10px 9px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}} th{{position:sticky;top:0;background:#f8fafc;color:#475569;z-index:1}}
.note{{font-size:12px;color:var(--muted);margin-top:10px}}
@media(max-width:950px){{.grid{{grid-template-columns:repeat(2,1fr)}}.charts{{grid-template-columns:1fr}}.hero{{display:block}}}}
@media(max-width:520px){{.grid{{grid-template-columns:1fr}}h1{{font-size:26px}}}}
</style>
</head>
<body>
<main class="wrap">
<div class="hero">
<div><span class="badge">OpenDART · KOSDAQ 315640</span><h1>DEEPNOID Financial Dashboard</h1>
<p class="muted">2010년 이후 정기보고서 수집 · 구조화 재무정보는 OpenDART 제공 범위인 2015년 이후부터 표시 · 매월 1일 자동 업데이트</p></div>
</div>
<section class="grid">{card_html}</section>
<section class="section"><h2>Financial Trend</h2><div class="charts">
<div class="chart"><canvas id="profit"></canvas></div>
<div class="chart"><canvas id="balance"></canvas></div>
</div></section>
<section class="section"><h2>Profitability & Growth</h2><div class="chart"><canvas id="ratio"></canvas></div></section>
<section class="section"><h2>Annual</h2><div class="table">{table(annual, annual_cols)}</div></section>
<section class="section"><h2>Half-year</h2><div class="table">{table(half, period_cols)}</div><div class="note">반기보고서는 보고기간 누적 기준 금액이 포함될 수 있습니다. 원문 공시의 기간 정보를 함께 확인하세요.</div></section>
<section class="section"><h2>Quarterly</h2><div class="table">{table(quarter, period_cols)}</div><div class="note">Q1/Q3는 DART 보고서 기준입니다. 계정별 누적/당기 금액의 의미가 다를 수 있으므로 원문 공시를 함께 확인하세요.</div></section>
<section class="section"><h2>Domestic Peer Firms</h2><p class="muted">사업영역 비교를 위한 국내 의료AI 상장기업 비교군입니다. 우열·투자등급을 의미하지 않습니다.</p>
<div class="table"><table><thead><tr><th>기업</th><th>종목코드</th><th>주요 비교영역</th></tr></thead><tbody>{peer_html}</tbody></table></div></section>
<p class="note">Source: Financial Supervisory Service OpenDART. 단위 및 회계기준은 원문 공시를 확인하세요.</p>
</main>
<script>
const labels={json.dumps(labels, ensure_ascii=False)};
const revenue={json.dumps(series["revenue"])}, op={json.dumps(series["operating_income"])}, net={json.dumps(series["net_income"])};
const cash={json.dumps(series["cash"])}, liabilities={json.dumps(series["total_liabilities"])}, equity={json.dumps(series["total_equity"])};
const margin={json.dumps(margin)}, netMargin={json.dumps(net_margin)}, growth={json.dumps(growth)};
new Chart(document.getElementById("profit"),{{type:"line",data:{{labels,datasets:[
{{label:"Revenue",data:revenue,tension:.25}},{{label:"Operating income",data:op,tension:.25}},{{label:"Net income",data:net,tension:.25}}
]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:"bottom"}}}}}}}});
new Chart(document.getElementById("balance"),{{type:"line",data:{{labels,datasets:[
{{label:"Cash",data:cash,tension:.25}},{{label:"Liabilities",data:liabilities,tension:.25}},{{label:"Equity",data:equity,tension:.25}}
]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:"bottom"}}}}}}}});
new Chart(document.getElementById("ratio"),{{type:"bar",data:{{labels,datasets:[
{{label:"Operating margin %",data:margin}},{{label:"Net margin %",data:netMargin}},{{label:"Revenue growth %",data:growth}}
]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:"bottom"}}}}}}}});
</script>
</body></html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print("Dashboard generated:", OUT)
