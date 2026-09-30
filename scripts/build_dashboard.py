from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/processed/financials.csv"
OUT=ROOT/"docs/index.html"
if not DATA.exists(): raise SystemExit("financials.csv not found")
df=pd.read_csv(DATA).sort_values(["year","category","report_code"])
annual=df[df.category=="Annual"].sort_values("year")
half=df[df.category=="Half-year"].sort_values("year")
quarter=df[df.category=="Quarterly"].sort_values(["year","report_code"])
latest=df.iloc[-1]

def fmt(v,p=False):
    if pd.isna(v): return "—"
    return f"{v*100:,.1f}%" if p else f"{v:,.0f}"

def table(d,cols):
    h="".join(f"<th>{b}</th>" for a,b in cols); rows=[]
    for _,r in d.iterrows():
        cells=[]
        for a,b in cols: cells.append(fmt(r.get(a),a in {"gross_margin","operating_margin","net_margin","revenue_growth"}))
        rows.append("<tr>"+"".join(f"<td>{x}</td>" for x in cells)+"</tr>")
    return "<table><thead><tr>"+h+"</tr></thead><tbody>"+"".join(rows)+"</tbody></table>"

annual_cols=[("year","연도"),("revenue","매출액"),("operating_income","영업이익"),("net_income","당기순이익"),("cash","현금"),("total_assets","총자산"),("total_liabilities","총부채"),("total_equity","자본총계"),("operating_margin","영업이익률"),("debt_ratio","부채비율")]
period_cols=[("year","연도"),("report_code","보고서"),("revenue","매출액"),("operating_income","영업이익"),("net_income","당기순이익"),("cash","현금"),("current_ratio","유동비율"),("debt_ratio","부채비율")]
labels=annual.year.astype(int).tolist()
revenue=[None if pd.isna(x) else float(x) for x in annual.revenue]
op=[None if pd.isna(x) else float(x) for x in annual.operating_income]
net=[None if pd.isna(x) else float(x) for x in annual.net_income]
margin=[None if pd.isna(x) else float(x)*100 for x in annual.operating_margin]
growth=[None if pd.isna(x) else float(x)*100 for x in annual.revenue_growth]
peers=[("루닛","328130","의료영상 AI / 암 진단"),("뷰노","338220","의료영상·생체신호 AI"),("제이엘케이","322510","뇌졸중·의료영상 AI"),("코어라인소프트","384470","흉부 CT·의료영상 AI"),("뉴로핏","380550","뇌영상·치매 AI")]
peer_html="".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a,b,c in peers)
html=f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DEEPNOID DART Financial Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>:root{{--bg:#f5f7fb;--card:#fff;--text:#172033;--muted:#6b7280;--line:#e5e7eb}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,Arial,sans-serif}}.wrap{{max-width:1320px;margin:auto;padding:32px 22px 60px}}h1{{font-size:30px;margin:8px 0}}h2{{font-size:20px}}.muted{{color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card,.section{{background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 4px 18px rgba(15,23,42,.04)}}.card{{padding:18px}}.label{{font-size:13px;color:var(--muted)}}.value{{font-size:24px;font-weight:700;margin-top:8px}}.section{{padding:20px;margin-top:18px}}.charts{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.chart{{height:360px}}.table{{overflow:auto;max-height:520px;border:1px solid var(--line);border-radius:12px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:10px 9px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f8fafc;color:#475569}}.badge{{display:inline-block;padding:5px 9px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:12px;font-weight:600}}@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}.charts{{grid-template-columns:1fr}}}}@media(max-width:520px){{.grid{{grid-template-columns:1fr}}}}</style></head>
<body><main class="wrap"><span class="badge">OpenDART · KOSDAQ 315640</span><h1>DEEPNOID Financial Dashboard</h1><p class="muted">2010년 이후 정기보고서 · Annual / Half-year / Quarterly · 매월 1일 자동 업데이트</p>
<section class="grid"><div class="card"><div class="label">Latest Revenue</div><div class="value">{fmt(latest.get("revenue"))}</div></div><div class="card"><div class="label">Operating Income</div><div class="value">{fmt(latest.get("operating_income"))}</div></div><div class="card"><div class="label">Net Income</div><div class="value">{fmt(latest.get("net_income"))}</div></div><div class="card"><div class="label">Total Equity</div><div class="value">{fmt(latest.get("total_equity"))}</div></div></section>
<section class="section"><h2>Financial Trend</h2><div class="charts"><div class="chart"><canvas id="profit"></canvas></div><div class="chart"><canvas id="ratio"></canvas></div></div></section>
<section class="section"><h2>Annual</h2><div class="table">{table(annual,annual_cols)}</div></section>
<section class="section"><h2>Half-year</h2><div class="table">{table(half,period_cols)}</div></section>
<section class="section"><h2>Quarterly</h2><div class="table">{table(quarter,period_cols)}</div></section>
<section class="section"><h2>Domestic Peer Firms</h2><p class="muted">사업영역 비교용 국내 의료AI 상장 Peer set입니다. 순위나 투자등급을 의미하지 않습니다.</p><div class="table"><table><thead><tr><th>기업</th><th>종목코드</th><th>주요 비교영역</th></tr></thead><tbody>{peer_html}</tbody></table></div></section>
<p class="muted">Source: Financial Supervisory Service OpenDART. 상세 회계기준과 주석은 원문 공시를 확인하세요.</p></main>
<script>
const labels={json.dumps(labels,ensure_ascii=False)},revenue={json.dumps(revenue)},op={json.dumps(op)},net={json.dumps(net)},margin={json.dumps(margin)},growth={json.dumps(growth)};
new Chart(document.getElementById("profit"),{{type:"line",data:{{labels,datasets:[{{label:"Revenue",data:revenue,tension:.25}},{{label:"Operating income",data:op,tension:.25}},{{label:"Net income",data:net,tension:.25}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:"bottom"}}}}}}}});
new Chart(document.getElementById("ratio"),{{type:"bar",data:{{labels,datasets:[{{label:"Operating margin %",data:margin}},{{label:"Revenue growth %",data:growth}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:"bottom"}}}}}}}});
</script></body></html>"""
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(html,encoding="utf-8")
print("Dashboard generated:",OUT)
