import io,json,os,re,time,zipfile
from pathlib import Path
import pandas as pd,requests

ROOT=Path(__file__).resolve().parents[1]
CFG_PATH=ROOT/"config/company.json"
CFG=json.loads(CFG_PATH.read_text(encoding="utf-8"))
KEY=os.environ.get("DART_API_KEY","").strip()
BASE="https://opendart.fss.or.kr/api"
RAW=ROOT/"data/raw"; OUT=ROOT/"data/processed"
RAW.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
if not KEY: raise SystemExit("DART_API_KEY is required.")
S=requests.Session()

def api(endpoint,**params):
    params["crtfc_key"]=KEY
    r=S.get(f"{BASE}/{endpoint}.json",params=params,timeout=90); r.raise_for_status()
    x=r.json()
    return x if str(x.get("status"))=="000" else None

def corp_code():
    if CFG.get("corp_code"): return CFG["corp_code"]
    r=S.get(f"{BASE}/corpCode.xml",params={"crtfc_key":KEY},timeout=120); r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z: xml=z.read("CORPCODE.xml").decode("utf-8","replace")
    m=re.search(r"<list>.*?<corp_code>(\d+)</corp_code>.*?<corp_name>딥노이드</corp_name>.*?</list>",xml,re.S)
    if not m: raise RuntimeError("DEEPNOID corp_code not found")
    CFG["corp_code"]=m.group(1); CFG_PATH.write_text(json.dumps(CFG,ensure_ascii=False,indent=2),encoding="utf-8"); return m.group(1)

CORP=corp_code()
def num(v):
    try: return float(str(v).replace(",","").replace(" ","")) if v not in (None,"","-") else None
    except: return None

ALIASES={
"total_assets":["자산총계"],"current_assets":["유동자산"],"cash":["현금및현금성자산","현금및현금성자산(현금성자산포함)"],
"receivables":["매출채권","매출채권및기타채권"],"inventory":["재고자산"],"ppe":["유형자산"],
"total_liabilities":["부채총계"],"current_liabilities":["유동부채"],"total_equity":["자본총계"],
"revenue":["매출액","수익(매출액)","영업수익"],"gross_profit":["매출총이익"],"sga":["판매비와관리비"],
"operating_income":["영업이익","영업이익(손실)"],"pretax_income":["법인세비용차감전순이익","법인세비용차감전순이익(손실)"],
"net_income":["당기순이익","당기순이익(손실)"],"eps":["기본주당이익","기본주당순이익"]
}
def pick(rows,names):
    for n in names:
        a=[x for x in rows if str(x.get("account_nm","")).strip()==n]
        if not a: a=[x for x in rows if n in str(x.get("account_nm",""))]
        if a: return num(a[0].get("thstrm_amount"))
    return None

def raw_doc(rcept,year,name):
    d=RAW/str(year); d.mkdir(parents=True,exist_ok=True)
    f=d/f"{rcept}_{re.sub(r'[^0-9A-Za-z가-힣._-]+','_',name)}.zip"
    if f.exists(): return
    r=S.get(f"{BASE}/document.xml",params={"crtfc_key":KEY,"rcept_no":rcept},timeout=120)
    if r.ok and r.content[:2]==b"PK": f.write_bytes(r.content)

def filings():
    a=[]
    for y in range(int(CFG["start_year"]),pd.Timestamp.now().year+1):
        x=api("list",corp_code=CORP,bgn_de=f"{y}0101",end_de=f"{y}1231",last_reprt_at="Y",page_no=1,page_count=100)
        if not x: continue
        for q in x.get("list",[]):
            n=q.get("report_nm","")
            if "반기보고서" in n: c="Half-year"
            elif "1분기보고서" in n or "3분기보고서" in n: c="Quarterly"
            elif "사업보고서" in n: c="Annual"
            else: continue
            r=q.get("rcept_no"); raw_doc(r,y,n)
            a.append({"year":y,"category":c,"report_nm":n,"rcept_no":r,"rcept_dt":q.get("rcept_dt"),"report_url":f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r}"})
    return pd.DataFrame(a).drop_duplicates()

def financials():
    a=[]
    for y in range(2015,pd.Timestamp.now().year+1):
        for c,code in [("Annual","11011"),("Half-year","11012"),("Quarterly","11013"),("Quarterly","11014")]:
            x=api("fnlttSinglAcnt",corp_code=CORP,bsns_year=str(y),reprt_code=code,fs_div="CFS"); div="CFS"
            if not x or not x.get("list"):
                x=api("fnlttSinglAcnt",corp_code=CORP,bsns_year=str(y),reprt_code=code,fs_div="OFS"); div="OFS"
            if not x or not x.get("list"): continue
            z={"year":y,"category":c,"report_code":code,"fs_div":div}
            for k,v in ALIASES.items(): z[k]=pick(x["list"],v)
            a.append(z)
    return pd.DataFrame(a)

def ratios(d):
    def q(a,b): return a/b if pd.notna(a) and pd.notna(b) and b!=0 else None
    d["gross_margin"]=[q(a,b) for a,b in zip(d.gross_profit,d.revenue)]
    d["operating_margin"]=[q(a,b) for a,b in zip(d.operating_income,d.revenue)]
    d["net_margin"]=[q(a,b) for a,b in zip(d.net_income,d.revenue)]
    d["current_ratio"]=[q(a,b) for a,b in zip(d.current_assets,d.current_liabilities)]
    d["debt_ratio"]=[q(a,b) for a,b in zip(d.total_liabilities,d.total_equity)]
    d["asset_turnover"]=[q(a,b) for a,b in zip(d.revenue,d.total_assets)]
    an=d[d.category=="Annual"].sort_values("year"); g=dict(zip(an.year,an.revenue.pct_change())); d["revenue_growth"]=d.year.map(g)
    return d

f=filings(); f.to_csv(OUT/"filings.csv",index=False,encoding="utf-8-sig")
d=financials()
if d.empty: raise RuntimeError("No structured financial data returned")
ratios(d).to_csv(OUT/"financials.csv",index=False,encoding="utf-8-sig")
print(f"filings={len(f)} financial_rows={len(d)}")
