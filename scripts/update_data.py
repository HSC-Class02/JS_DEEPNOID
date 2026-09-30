import io, json, os, re, time, zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "config" / "company.json"
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))

KEY = os.environ.get("DART_API_KEY", "").strip()
BASE = "https://opendart.fss.or.kr/api"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

if not KEY:
    raise SystemExit("DART_API_KEY is required. Add it as a GitHub Actions secret.")

S = requests.Session()
S.headers.update({"User-Agent": "JS_DEEPNOID-DART-dashboard/1.0"})


def get_json(endpoint, **params):
    params["crtfc_key"] = KEY
    last_error = None
    for attempt in range(4):
        try:
            r = S.get(f"{BASE}/{endpoint}.json", params=params, timeout=90)
            r.raise_for_status()
            data = r.json()
            status = str(data.get("status", ""))
            if status == "000":
                return data
            # 013/020 etc. can mean no data or rate/parameter issues; keep the run alive.
            if status in {"013", "020"}:
                return None
            raise RuntimeError(f"{endpoint}: {status} {data.get('message', '')}")
        except Exception as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"{endpoint} failed after retries: {last_error}")


def resolve_corp_code():
    if CFG.get("corp_code"):
        return CFG["corp_code"]

    r = S.get(f"{BASE}/corpCode.xml", params={"crtfc_key": KEY}, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        xml = z.read("CORPCODE.xml").decode("utf-8", "replace")

    pattern = re.compile(
        r"<list>.*?<corp_code>(\d+)</corp_code>.*?"
        r"<corp_name>딥노이드</corp_name>.*?</list>",
        re.S,
    )
    m = pattern.search(xml)
    if not m:
        raise RuntimeError("DEEPNOID corp_code not found in OpenDART corpCode.xml")

    CFG["corp_code"] = m.group(1)
    CFG_PATH.write_text(
        json.dumps(CFG, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return CFG["corp_code"]


CORP = resolve_corp_code()


def num(value):
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace(" ", ""))
    except (TypeError, ValueError):
        return None


def pick(rows, aliases):
    # Prefer an exact account-name match, then a contains match.
    for alias in aliases:
        exact = [x for x in rows if str(x.get("account_nm", "")).strip() == alias]
        if exact:
            return num(exact[0].get("thstrm_amount"))
    for alias in aliases:
        contains = [x for x in rows if alias in str(x.get("account_nm", ""))]
        if contains:
            return num(contains[0].get("thstrm_amount"))
    return None


ALIASES = {
    "total_assets": ["자산총계"],
    "current_assets": ["유동자산"],
    "cash": ["현금및현금성자산", "현금및현금성자산(현금성자산포함)", "현금및현금성자산(현금성자산포함)"],
    "receivables": ["매출채권", "매출채권및기타채권", "매출채권및기타유동채권"],
    "inventory": ["재고자산"],
    "ppe": ["유형자산"],
    "total_liabilities": ["부채총계"],
    "current_liabilities": ["유동부채"],
    "interest_bearing_debt": [
        "단기차입금", "유동성장기부채", "장기차입금", "사채",
        "전환사채", "전환우선주부채", "리스부채", "장기리스부채",
    ],
    "total_equity": ["자본총계"],
    "revenue": ["매출액", "수익(매출액)", "영업수익"],
    "gross_profit": ["매출총이익"],
    "sga": ["판매비와관리비"],
    "operating_income": ["영업이익", "영업이익(손실)"],
    "pretax_income": ["법인세비용차감전순이익", "법인세비용차감전순이익(손실)"],
    "net_income": ["당기순이익", "당기순이익(손실)"],
    "controlling_net_income": ["지배기업의 소유주에게 귀속되는 당기순이익", "지배기업 소유주지분 순이익"],
    "eps": ["기본주당이익", "기본주당순이익"],
    "cfo": ["영업활동현금흐름"],
    "depreciation": ["감가상각비"],
    "amortization": ["무형자산상각비", "상각비"],
    "cfi": ["투자활동현금흐름"],
    "cff": ["재무활동현금흐름"],
    "capex": ["유형자산의 취득", "유형자산 취득"],
}


def download_raw_document(receipt_no, year, report_name):
    if not receipt_no:
        return
    folder = RAW / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", report_name).strip("_")
    target = folder / f"{receipt_no}_{safe}.zip"
    if target.exists():
        return
    r = S.get(
        f"{BASE}/document.xml",
        params={"crtfc_key": KEY, "rcept_no": receipt_no},
        timeout=120,
    )
    if r.ok and r.content[:2] == b"PK":
        target.write_bytes(r.content)


def collect_filings():
    records = []
    current_year = pd.Timestamp.now().year

    for year in range(int(CFG["start_year"]), current_year + 1):
        page_no = 1
        while True:
            data = get_json(
                "list",
                corp_code=CORP,
                bgn_de=f"{year}0101",
                end_de=f"{year}1231",
                last_reprt_at="Y",
                page_no=page_no,
                page_count=100,
            )
            if not data:
                break

            items = data.get("list", [])
            for item in items:
                report_name = item.get("report_nm", "")
                if "사업보고서" in report_name:
                    category = "Annual"
                    report_code = "11011"
                elif "반기보고서" in report_name:
                    category = "Half-year"
                    report_code = "11012"
                elif "1분기보고서" in report_name:
                    category = "Quarterly"
                    report_code = "11013"
                elif "3분기보고서" in report_name:
                    category = "Quarterly"
                    report_code = "11014"
                else:
                    continue

                receipt = item.get("rcept_no")
                download_raw_document(receipt, year, report_name)
                records.append({
                    "year": year,
                    "category": category,
                    "report_code": report_code,
                    "report_nm": report_name,
                    "rcept_no": receipt,
                    "rcept_dt": item.get("rcept_dt"),
                    "report_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}",
                })

            total_page = int(data.get("total_page", page_no))
            if page_no >= total_page:
                break
            page_no += 1

    result = pd.DataFrame(records).drop_duplicates(subset=["rcept_no"])
    if not result.empty:
        result = result.sort_values(["year", "category", "report_code"])
    return result


def get_accounts(year, report_code):
    for fs_div in ("CFS", "OFS"):
        data = get_json(
            "fnlttSinglAcnt",
            corp_code=CORP,
            bsns_year=str(year),
            reprt_code=report_code,
            fs_div=fs_div,
        )
        if data and data.get("list"):
            return data["list"], fs_div
    return [], None


def collect_financials():
    rows = []
    for year in range(2015, pd.Timestamp.now().year + 1):
        for category, report_code in [
            ("Annual", "11011"),
            ("Half-year", "11012"),
            ("Quarterly", "11013"),
            ("Quarterly", "11014"),
        ]:
            accounts, fs_div = get_accounts(year, report_code)
            if not accounts:
                continue

            row = {
                "year": year,
                "category": category,
                "report_code": report_code,
                "period": {"11011": "FY", "11012": "H1", "11013": "Q1", "11014": "Q3"}[report_code],
                "fs_div": fs_div,
            }
            for key, aliases in ALIASES.items():
                row[key] = pick(accounts, aliases)
            rows.append(row)

    return pd.DataFrame(rows)


def derive_metrics(df):
    df = df.copy()

    def div(a, b):
        return a / b if pd.notna(a) and pd.notna(b) and b != 0 else None

    def add(name, a, b):
        df[name] = [div(x, y) for x, y in zip(df[a], df[b])]

    add("gross_margin", "gross_profit", "revenue")
    add("operating_margin", "operating_income", "revenue")
    add("net_margin", "net_income", "revenue")
    add("ebitda_margin", "operating_income", "revenue")
    add("current_ratio", "current_assets", "current_liabilities")
    df["quick_assets"] = df["cash"].fillna(0) + df["receivables"].fillna(0)
    add("quick_ratio", "quick_assets", "current_liabilities")
    add("debt_ratio", "total_liabilities", "total_assets")
    add("asset_turnover", "revenue", "total_assets")
    add("cfo_to_net_income", "cfo", "net_income")

    df["net_debt"] = df["interest_bearing_debt"] - df["cash"]
    df["ebitda"] = df["operating_income"] + df["depreciation"].fillna(0) + df["amortization"].fillna(0)
    df.loc[df[["depreciation", "amortization"]].isna().all(axis=1), "ebitda"] = pd.NA

    annual = df[df.category == "Annual"].sort_values("year").copy()
    annual["revenue_growth"] = annual["revenue"].pct_change()
    annual["roa"] = annual.apply(lambda r: div(r["net_income"], r["total_assets"]), axis=1)
    annual["roe"] = annual.apply(lambda r: div(r["net_income"], r["total_equity"]), axis=1)
    annual["roic"] = annual.apply(
        lambda r: div(r["operating_income"], r["total_assets"] - r["current_liabilities"]),
        axis=1,
    )
    annual["net_debt_ebitda"] = annual.apply(lambda r: div(r["net_debt"], r["ebitda"]), axis=1)

    # Working-capital days use year-end balances and annual revenue/cost proxies.
    annual["dso"] = annual.apply(lambda r: div(r["receivables"], r["revenue"]) * 365 if div(r["receivables"], r["revenue"]) is not None else None, axis=1)
    annual["dio"] = annual.apply(lambda r: div(r["inventory"], r["revenue"]) * 365 if div(r["inventory"], r["revenue"]) is not None else None, axis=1)
    annual["dpo"] = None
    annual["ccc"] = annual["dso"] + annual["dio"] - annual["dpo"] if "dpo" in annual else None

    annual_map = annual.set_index("year")
    for col in ["revenue_growth", "roa", "roe", "roic", "net_debt_ebitda", "dso", "dio", "dpo", "ccc"]:
        df[col] = df["year"].map(annual_map[col].to_dict())

    # FCF = CFO + CFI; when CAPEX is available, this is also CFO - CAPEX on a cash basis.
    df["fcf"] = df["cfo"] + df["cfi"]
    return df


filings_df = collect_filings()
filings_df.to_csv(OUT / "filings.csv", index=False, encoding="utf-8-sig")

financials_df = collect_financials()
if financials_df.empty:
    raise RuntimeError("No structured financial data returned by OpenDART.")

financials_df = derive_metrics(financials_df)
financials_df.to_csv(OUT / "financials.csv", index=False, encoding="utf-8-sig")

print(f"corp_code={CORP}")
print(f"filings={len(filings_df)} financial_rows={len(financials_df)}")
