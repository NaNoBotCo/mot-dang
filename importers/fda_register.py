#!/usr/bin/env python3
"""fda_register.py — each compound in data/curated/compounds.json, looked up on Thailand's drug register.

The Thai FDA's public product search (pertento.fda.moph.go.th, FRM_SEARCH_DRUG.aspx) takes an
active-ingredient name and answers with every modern-medicine registration carrying it: the
registration number, the Thai and English trade names, the licence holder, the legal class
(ยาสามัญประจำบ้าน · ยาอันตราย · ยาควบคุมพิเศษ …), the dosage form and whether the registration
stands. One substance a request pair, two seconds apart, cached a week under cache/fda_register/.
Only the first result page is read: the count, the classes and the brand names it shows are
what an answer needs.

Writes data/curated/fda_register.json. Run: python3 importers/fda_register.py [--refetch] [id …]
"""
import html
import http.cookiejar
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEX = ROOT / "data" / "curated" / "compounds.json"
OUT = ROOT / "data" / "curated" / "fda_register.json"
CACHE = ROOT / "cache" / "fda_register"
URL = "https://pertento.fda.moph.go.th/FDA_SEARCH_DRUG/SEARCH_DRUG/FRM_SEARCH_DRUG.aspx"
WEEK = 7 * 86400

# the register's own name for a substance, where the reader's name differs
QUERY = {
    "hcg": "chorionic", "emtricitabine/tenofovir": "tenofovir", "nad+": "nicotinamide adenine",
    "insulin glargine": "glargine", "botulinum toxin": "botulinum", "conjugated estrogens": "conjugated",
    "thymosin alpha-1": "thymalfasin", "melanotan ii": "melanotan", "igf-1 lr3": "mecasermin",
    "coenzyme q10": "ubidecarenone", "low-dose naltrexone": "naltrexone", "pt-141": "bremelanotide",
    "ss-31": "elamipretide", "mk-677": "ibutamoren", "ostarine": "enobosarm", "cardarine": "501516",
    "rapamycin": "sirolimus", "tb-500": "thymosin beta", "rad-140": "testolone", "lgd-4033": "ligandrol",
    "methandrostenolone": "metandienone", "turinabol": "chlorodehydromethyl", "clomiphene": "clomifene",
    "kratom": None,
}

# substances whose name sits inside another's (estradiol in ethinylestradiol, progesterone in
# medroxyprogesterone): the count stands, the first page's brand names do not describe them
COLLIDES = {"estradiol", "progesterone", "testosterone", "insulin glargine", "nad+", "nicotinamide riboside",
            "levonorgestrel", "estriol", "naltrexone", "low-dose naltrexone", "tenofovir", "emtricitabine/tenofovir"}

CLASS_TH = {"ยาสามัญประจำบ้าน": "household", "ยาอันตราย": "dangerous", "ยาควบคุมพิเศษ": "special",  # stylecheck: allow — the register's class names
            "ยาบรรจุเสร็จที่ไม่ใช่ยาอันตรายหรือยาควบคุมพิเศษ": "packaged"}

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
OP.addheaders = [("User-Agent", "Mozilla/5.0 (motdang.net drug-register lookup; one request every 2 s)")]


def _hidden(h):
    return {m.group(1): html.unescape(m.group(2))
            for m in re.finditer(r'name="(__[A-Z]+)" id="[^"]*" value="([^"]*)"', h)}


def fetch(sub):
    h = OP.open(URL, timeout=40).read().decode("utf-8", "replace")
    f = _hidden(h)
    f.update({"ctl00$ContentPlaceHolder1$txt_substance": sub,
              "ctl00$ContentPlaceHolder1$btn_sea_drug": "ค้นหา",
              "ctl00$ContentPlaceHolder1$txt_Product_THAI": "", "ctl00$ContentPlaceHolder1$txt_Product_ENG": "",
              "ctl00$ContentPlaceHolder1$Txt_fdpdtno": ""})
    return OP.open(URL, data=urllib.parse.urlencode(f).encode(), timeout=90).read().decode("utf-8", "replace")


def _cells(row):
    return [re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", c))).replace("\xa0", " ").strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]


def parse(page):
    m = re.search(r"จำนวนค้นหาทั้งหมด\s*([\d,]+)", re.sub("<[^>]+>", " ", page))
    total = int(m.group(1).replace(",", "")) if m else 0
    rows = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        c = _cells(row)
        # data rows carry 23 cells: the hidden columns, then ลำดับ … สถานะ
        if len(c) >= 22 and c[14].isdigit():
            rows.append({"reg": c[15], "th": c[16], "en": c[17], "holder": c[18], "class_th": c[19],
                         "form": c[20], "status": c[21]})
    return total, rows


def summary(cid, q, total, rows):
    active = [r for r in rows if r["status"].startswith("คงอยู่")]
    classes = {}
    for r in active or rows:
        classes[r["class_th"]] = classes.get(r["class_th"], 0) + 1
    seen_en, seen_th = [], []
    for r in active or rows:
        en = re.sub(r"\s+[\d.,]+\s*(MG|MCG|G|ML|IU|%|มิลลิกรัม|ไมโครกรัม).*$", "", r["en"], flags=re.I).strip()
        th = re.sub(r"\s+[\d.,]+\s*(มิลลิกรัม|ไมโครกรัม|กรัม|มก\.?|mg).*$", "", r["th"], flags=re.I).strip()
        if en and en not in seen_en:
            seen_en.append(en)
        if th and th not in seen_th:
            seen_th.append(th)
    return {"query": q, "total": total, "page_active": len(active), "page_rows": len(rows),
            "classes": classes, "class": [CLASS_TH.get(k, k) for k in classes],
            "brands_en": [] if cid in COLLIDES else seen_en[:6],
            "brands_th": [] if cid in COLLIDES else seen_th[:6],
            "forms": sorted({r["form"] for r in rows if r["form"]})[:5]}


def main(argv):
    refetch = "--refetch" in argv
    only = [a for a in argv if not a.startswith("--")]
    lex = json.loads(LEX.read_text(encoding="utf-8"))["compounds"]
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"rows": {}}
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = dict(old.get("rows", {}))
    for c in lex:
        cid = c["id"]
        if only and cid not in only:
            continue
        q = QUERY.get(cid, cid)
        if q is None:
            rows[cid] = {"query": None, "total": None, "note": "not a modern medicine; not looked up"}
            continue
        cf = CACHE / (re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-") + ".html")
        if cf.exists() and not refetch and time.time() - cf.stat().st_mtime < WEEK:
            page = cf.read_text(encoding="utf-8")
        else:
            try:
                page = fetch(q)
            except Exception as e:  # one failed lookup leaves the old row in place
                print(f"  {cid}: fetch failed ({e.__class__.__name__}); kept the previous row")
                time.sleep(4)
                continue
            cf.write_text(page, encoding="utf-8")
            time.sleep(2)
        total, prow = parse(page)
        rows[cid] = summary(cid, q, total, prow)
        print(f"  {cid:24} {total:4}  {', '.join(rows[cid]['class'])}  {', '.join(rows[cid]['brands_en'][:3])}")
    out = {"_readme": "Thai FDA drug register, one lookup a compound (importers/fda_register.py).",
           "source": URL, "fetched": time.strftime("%Y-%m-%d"), "rows": rows}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"fda_register: {len(rows)} rows -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
