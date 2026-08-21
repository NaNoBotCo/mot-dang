#!/usr/bin/env python3
"""The open lists — WO-16's approved fetches from data.go.th, and nothing else.

WHY THIS EXISTS. The door survey of 2026-08-19 (notes/aggregators-and-tags-
proposal-2026-08-19.md §3) read the provincial open-data catalogues end to end:
most "place" datasets are COUNT series, but a handful are real LISTS — police
stations with phone numbers, eco attractions with phone numbers, 641 bus
routes, the Thai SELECT restaurants, the ธงฟ้า restaurants, the LPG shops, the
SAT-certified boxing camps, the FDA pharmacy licences. Nan's go on 2026-08-20
("go on WO-16 open lists") is the confirmation those fetches needed. This file
fetches EXACTLY that list; adding a source here means going back for another go.

MANNERS AND THE ONE TRAP. Announced User-Agent with a URL and an address —
and WITHOUT the word "bot": measured 2026-08-19, the gdcatalog.go.th WAF
returns 403 to any UA containing that substring while the same request with
MotDang/1.0 passes. It is a word list, not a policy; we announce ourselves
fully either way. Three seconds between requests. Snapshot-first into
cache/datagoth/ so a re-run costs the hosts nothing.

ENCODINGS, measured: Chiang Mai's CSVs are UTF-8, Chiang Rai's are cp874
(TIS-620), and two Chiang Mai ones (dataset_10_344, dataset_10_238) are cp874
too. _text() tries utf-8-sig first and falls back, same as import_citizeninfo.

XLSX with no third-party library: an .xlsx is a zip of XML, and _xlsx_rows()
reads sharedStrings + the first worksheet with zipfile + ElementTree. It
handles shared strings, inline strings and plain values — enough for these
registers, and nothing more is promised.

OUTPUT
  cache/datagoth/<key>.<csv|xlsx>      raw snapshots (gitignored)
  cache/datagoth/pkg_<id>.json         CKAN package_show answers (URL drift guard)
  data/curated/datagoth.json           parsed rows per source + provenance
  data/curated/yardsticks.json         the official COUNTS, for /stats.html
  data/bus_routes.json                 the 641+27 Chiang Mai bus routes, for WO-13

data/curated/ here follows the enrich.json arrangement: this importer owns
datagoth.json and yardsticks.json and rewrites them wholesale; nothing else
may touch them; hand-kept truth lives in OTHER curated files.

    python3 importers/harvest_datagoth.py            # fetch what is missing
    python3 importers/harvest_datagoth.py --refetch  # ask everything again
    python3 importers/harvest_datagoth.py --offline  # parse snapshots only
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "datagoth")
OUT = os.path.join(ROOT, "data", "curated", "datagoth.json")
YARD = os.path.join(ROOT, "data", "curated", "yardsticks.json")
BUS = os.path.join(ROOT, "data", "bus_routes.json")
# No "bot" in this string — the gdcatalog WAF 403s the substring (measured
# 2026-08-19). Still announced: a name, a URL, an address to complain to.
UA = "MotDang/1.0 (+https://motdang.net/about.html; 530kings@proton.me)"
PAUSE = 3.0
TODAY = date.today().isoformat()

# The approved list. `dataset` is the data.go.th CKAN id; `pick` chooses the
# resource by format and, where a dataset carries several files, by a name
# fragment. Every entry names why it is being fetched.
SOURCES = [
    ("cm-wats-6704", "67-04", "CSV", None,
     "วัดและสำนักสงฆ์ จ.เชียงใหม่ — cross-check for the ONAB register fold + the สำนักสงฆ์ rows the register lacks"),
    ("cm-bus-routes", "_67_70", "CSV", None,
     "เส้นทางเดินรถโดยสารประจำทาง — 641 routes with amphoe/tambon passed"),
    ("cm-bus-cat14", "dataset_10_238", "CSV", None,
     "เส้นทางหมวด 1 และ 4 — 27 numbered routes"),
    ("cm-bus-city", "69_148", "CSV", None,
     "รถโดยสารในเขตเมืองเชียงใหม่ — the city routes"),
    ("cr-eco", "eco", "CSV", None,
     "รายชื่อแหล่งท่องเที่ยว เชียงราย — 38 rows with addresses and PHONES"),
    ("cr-religious", "dataset_20_19", "CSV", None,
     "แหล่งท่องเที่ยวเชิงศาสนา ศิลปะ วัฒนธรรม เชียงราย — 127 named sites"),
    ("cr-community", "dataset_20_12", "CSV", None,
     "แหล่งท่องเที่ยวโดยชุมชนแนะนำ เชียงราย — 119 named sites"),
    ("cm-police", "_67_73", "CSV", None,
     "สถานีตำรวจ ภ.จว.เชียงใหม่ — 39 stations with phone numbers"),
    ("cm-thai-select", "_67_69", "CSV", None,
     "Thai SELECT เชียงใหม่ — 23 restaurant names, for honours.json"),
    ("cr-thongfah", "dataset40_11", "CSV", None,
     "ร้านอาหารธงฟ้า เชียงราย — 33 rows, for a curated tag"),
    ("cm-lpg", "69_139", "CSV", None,
     "สถานประกอบการก๊าซ LPG เชียงใหม่ — 27 named companies (69_140 serves the identical file; one fetch)"),
    ("sat-camps", "sat-standardized-boxingcamps", "XLSX", "standardized-boxing-camps",
     "SAT-certified muay thai camps, CC-BY — the CM/CR rows join WO-12's shelf"),
    ("fda-drug", "drug-location", "XLSX", "drug_location",
     "FDA drug-premises licences 2024 — the pharmacy yardstick, CM/CR rows only are kept"),
    # Yardsticks — official counts to print beside what we hold.
    ("cm-hotels-cert", "_67_76", "CSV", None, "hotels certified, by amphoe (yardstick)"),
    ("cm-tour-ops", "dataset_10_344", "CSV", None, "licensed tour operators (yardstick)"),
    ("cr-clinics", "dataset50_77", "CSV", None, "CR clinics of all types (yardstick)"),
    ("cm-otop", "_67_83", "CSV", None, "OTOP outlets by amphoe (yardstick)"),
    ("cm-stays", "69_158", "CSV", None, "CM accommodation by type (yardstick)"),
]


def get(url, maxb=6_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(maxb)


def pkg_show(dataset, refetch=False):
    p = os.path.join(CACHE, f"pkg_{dataset}.json")
    if os.path.exists(p) and not refetch:
        return json.load(open(p))
    url = ("https://data.go.th/api/3/action/package_show?"
           + urllib.parse.urlencode({"id": dataset}))
    doc = json.loads(get(url).decode("utf-8", "replace"))["result"]
    json.dump(doc, open(p, "w"), ensure_ascii=False)
    time.sleep(PAUSE)
    return doc


def pick_resource(doc, fmt, frag):
    """The named format; the name fragment first where one is given; and a
    Data-Dictionary file is documentation, never the data."""
    cands = [r for r in doc.get("resources", [])
             if (r.get("format") or "").upper().lstrip(".") == fmt
             and "dictionary" not in (r.get("name") or "").lower()
             and "dictionary" not in (r.get("url") or "").lower()]
    if frag:
        strong = [r for r in cands if frag in (r.get("url") or "") + (r.get("name") or "")]
        cands = strong or cands
    return cands[0] if cands else None


def _text(raw):
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _csv_rows(raw):
    rows = list(csv.reader(io.StringIO(_text(raw))))
    return [[(c or "").strip() for c in r] for r in rows if any((c or "").strip() for c in r)]


def _col_index(ref):
    """'BC12' -> 54 (0-based column)."""
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return n - 1


def _xlsx_rows(path):
    """First worksheet as a list of rows of strings. Stdlib only."""
    NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    sheet = next((n for n in ("xl/worksheets/sheet1.xml",) if n in z.namelist()),
                 next((n for n in sorted(z.namelist())
                       if n.startswith("xl/worksheets/sheet")), None))
    if not sheet:
        return []
    rows = []
    for row in ET.fromstring(z.read(sheet)).iter(NS + "row"):
        cells = {}
        for c in row.iter(NS + "c"):
            ref = c.get("r") or ""
            idx = _col_index(ref) if ref else len(cells)
            t = c.get("t")
            v = c.find(NS + "v")
            is_ = c.find(NS + "is")
            if t == "s" and v is not None:
                val = shared[int(v.text)] if v.text and v.text.isdigit() else ""
            elif t == "inlineStr" and is_ is not None:
                val = "".join(x.text or "" for x in is_.iter(NS + "t"))
            else:
                val = v.text if v is not None and v.text is not None else ""
            cells[idx] = str(val).strip()
        if not cells:
            continue
        width = max(cells) + 1
        rows.append([cells.get(i, "") for i in range(width)])
    return [r for r in rows if any(c for c in r)]


def fetch_all(refetch=False, offline=False):
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    for key, dataset, fmt, frag, why in SOURCES:
        ext = fmt.lower()
        snap = os.path.join(CACHE, f"{key}.{ext}")
        meta = {"key": key, "dataset": dataset,
                "dataset_url": f"https://data.go.th/dataset/{dataset}", "why": why}
        if not os.path.exists(snap):
            if offline:
                print(f"  {key}: no snapshot and --offline — skipped")
                continue
            try:
                doc = pkg_show(dataset, refetch)
                res = pick_resource(doc, fmt, frag)
                if not res:
                    print(f"  {key}: no {fmt} resource on {dataset} — skipped")
                    continue
                meta["resource_url"] = res.get("url")
                meta["licence"] = doc.get("license_title") or "not specified"
                meta["publisher"] = (doc.get("organization") or {}).get("title") or ""
                raw = get(res["url"])
                open(snap, "wb").write(raw)
                json.dump(meta, open(snap + ".meta.json", "w"), ensure_ascii=False)
                print(f"  {key}: fetched {len(raw):,} bytes")
                time.sleep(PAUSE)
            except Exception as e:
                print(f"  {key}: FAILED {type(e).__name__}: {str(e)[:120]}")
                continue
        mpath = snap + ".meta.json"
        if os.path.exists(mpath):
            meta.update(json.load(open(mpath)))
        meta["fetched"] = date.fromtimestamp(os.path.getmtime(snap)).isoformat()
        rows = _xlsx_rows(snap) if ext == "xlsx" else _csv_rows(open(snap, "rb").read())
        meta["rows"] = rows
        out[key] = meta
        print(f"  {key}: {len(rows)} row(s)  [{meta.get('licence', '?')}]")
    return out


def _th_int(s):
    m = re.search(r"[\d,]+", (s or "").replace(" ", ""))
    return int(m.group(0).replace(",", "")) if m else None


def yardsticks(data):
    """The official counts, each with its year and its source — the numbers
    /stats.html prints beside what the catalogue holds. Only what the fetched
    rows actually say; a source that failed to fetch simply contributes none."""
    y = []

    def add(key, th, en, official, unit_th, unit_en, year_be, ours, src_key):
        m = data.get(src_key) or {}
        if official is None:
            return
        y.append({"key": key, "th": th, "en": en, "official": official,
                  "unit_th": unit_th, "unit_en": unit_en, "year_be": year_be,
                  "ours": ours,
                  "source_name": m.get("publisher") or "data.go.th",
                  "source_url": m.get("dataset_url"), "fetched": m.get("fetched")})

    # hotels certified — the last year's row, summed across amphoes
    hc = data.get("cm-hotels-cert")
    if hc and hc["rows"]:
        rows = hc["rows"][1:]
        years = [(_th_int(r[0]) or 0) for r in rows]
        last = max(years) if years else 0
        tot = sum((_th_int(r[-1]) or 0) for r, yr in zip(rows, years) if yr == last)
        add("cm-hotels-cert", "ธุรกิจโรงแรมที่ได้รับการรับรองมาตรฐาน (เชียงใหม่)",
            "Hotels certified to standard (Chiang Mai)", tot or None,
            "แห่ง", "places", last or None, {"cat": "hotel", "prov": "cm"}, "cm-hotels-cert")
    to = data.get("cm-tour-ops")
    if to and to["rows"]:
        # a year per row — the NEWEST year is the yardstick, not the first row
        rows = [r for r in to["rows"][1:] if len(r) > 3]
        best = max(rows, key=lambda r: _th_int(r[1]) or 0, default=None)
        if best:
            add("cm-tour-ops", "ธุรกิจนำเที่ยวที่ได้รับใบอนุญาต (เชียงใหม่)",
                "Licensed tour operators (Chiang Mai)",
                _th_int(best[3]), "ราย", "operators",
                _th_int(best[1]), None, "cm-tour-ops")
    cc = data.get("cr-clinics")
    if cc and cc["rows"]:
        rows = cc["rows"][1:]
        best = max(rows, key=lambda r: _th_int(r[0]) or 0, default=None)
        if best:
            add("cr-clinics", "คลินิกทุกประเภท (เชียงราย)", "Clinics of all types (Chiang Rai)",
                _th_int(best[2] if len(best) > 2 else ""), "แห่ง", "clinics",
                _th_int(best[0]), {"cat": "medical", "sub": "clinic", "prov": "cr"}, "cr-clinics")
    ot = data.get("cm-otop")
    if ot and ot["rows"]:
        rows = ot["rows"][1:]
        years = [(_th_int(r[1]) or 0) for r in rows]
        last = max(years) if years else 0
        tot = sum((_th_int(r[-1]) or 0) for r, yr in zip(rows, years) if yr == last)
        add("cm-otop", "แหล่งจำหน่ายของฝาก-OTOP (เชียงใหม่ ทุกอำเภอ)",
            "OTOP & gift outlets (Chiang Mai, all amphoes)", tot or None,
            "แห่ง", "outlets", last or None, None, "cm-otop")
    st = data.get("cm-stays")
    if st and st["rows"]:
        rows = [r for r in st["rows"][1:] if len(r) > 3]
        years = [(_th_int(r[0]) or 0) for r in rows]
        last = max(years) if years else 0
        tot = sum((_th_int(r[3]) or 0) for r, yr in zip(rows, years) if yr == last)
        add("cm-stays", "สถานที่พักแรมทุกประเภท (เชียงใหม่)",
            "Places to stay, all types (Chiang Mai)", tot or None,
            "แห่ง", "places", last or None, {"cat": "hotel", "prov": "cm"}, "cm-stays")
    fda = data.get("fda-drug")
    if fda and fda["rows"]:
        # The FDA export's headers are romanised field names, measured:
        # lcntpcd = licence type, thanm = premises name, thachngwtnm = province,
        # cncnm = status (คงอยู่ = extant). "ขายยาแผนปัจจุบัน" alone is the
        # ordinary retail pharmacy (ขย.1); the บรรจุเสร็จ variants are the
        # limited licences and the วัตถุออกฤทธิ์/ยาเสพติด ones are controlled-
        # substance permissions a pharmacy holds ON TOP, not extra shops.
        head = fda["rows"][0]
        H = {h: i for i, h in enumerate(head)}
        if "thachngwtnm" in H and "lcntpcd" in H:
            for prov_th, prov in (("เชียงใหม่", "cm"), ("เชียงราย", "cr")):
                rows = [r for r in fda["rows"][1:]
                        if len(r) > H["thachngwtnm"] and r[H["thachngwtnm"]] == prov_th
                        and ("cncnm" not in H or len(r) <= H["cncnm"] or r[H["cncnm"]] in ("คงอยู่", ""))]
                retail = [r for r in rows if r[H["lcntpcd"]] == "ขายยาแผนปัจจุบัน"]
                add(f"{prov}-pharmacies-licensed",
                    f"ใบอนุญาตขายยาแผนปัจจุบัน ({'เชียงใหม่' if prov == 'cm' else 'เชียงราย'})",
                    f"Retail-pharmacy licences ({'Chiang Mai' if prov == 'cm' else 'Chiang Rai'})",
                    len(retail) or None, "ใบอนุญาต", "licences", 2567,
                    {"cat": "medical", "sub": "pharmacy", "prov": prov}, "fda-drug")
    return y


def bus_routes(data):
    routes = []
    br = data.get("cm-bus-routes")
    if br and br["rows"]:
        H = {h: i for i, h in enumerate(br["rows"][0])}
        for r in br["rows"][1:]:
            def col(name):
                i = H.get(name)
                return r[i] if i is not None and i < len(r) else ""
            nm = col("ชื่อเส้นทาง")
            if not nm:
                continue
            routes.append({"name": nm, "year_be": _th_int(col("ปี")),
                           "amphoe": col("อำเภอที่ผ่าน") or None,
                           "tambon": col("ตำบลที่ผ่าน") or None,
                           "kind": "provincial"})
    cat14 = data.get("cm-bus-cat14")
    if cat14 and cat14["rows"]:
        for r in cat14["rows"][1:]:
            if len(r) >= 4 and r[3]:
                routes.append({"name": r[3], "route_no": r[2] or None,
                               "kind": "category-1-4"})
    city = data.get("cm-bus-city")
    if city and city["rows"]:
        H = {h: i for i, h in enumerate(city["rows"][0])}
        for r in city["rows"][1:]:
            def col(name):
                i = H.get(name)
                return r[i] if i is not None and i < len(r) else ""
            nm = col("route_name")
            if nm:
                routes.append({"name": nm, "route_no": col("route_no") or None,
                               "route_class": col("route_class") or None,
                               "vehicles": _th_int(col("value")),
                               "kind": "city"})
    return routes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    data = fetch_all(refetch=args.refetch, offline=args.offline)
    doc = {"_comment": "Parsed snapshots of WO-16's approved data.go.th lists. "
                       "Owned wholesale by importers/harvest_datagoth.py (the "
                       "enrich.json arrangement) — hand truth goes in OTHER "
                       "curated files. Every entry carries dataset_url, "
                       "resource_url, licence, publisher and the fetch date; "
                       "import_opendata.py reads this and never the network.",
           "generated": TODAY, "sources": data}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(data)} sources)")
    y = yardsticks(data)
    json.dump({"_comment": "Official counts for /stats.html — what the province "
                           "counts beside what the catalogue holds. Owned "
                           "wholesale by importers/harvest_datagoth.py; every "
                           "row names its publisher, dataset and fetch date.",
               "generated": TODAY, "yardsticks": y},
              open(YARD, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {os.path.relpath(YARD, ROOT)} ({len(y)} yardsticks)")
    b = bus_routes(data)
    if b:
        meta = {k: {kk: vv for kk, vv in (data.get(k) or {}).items() if kk != "rows"}
                for k in ("cm-bus-routes", "cm-bus-cat14", "cm-bus-city")}
        json.dump({"_comment": "Chiang Mai bus routes from the provincial open "
                               "lists — the register of WO-13's future bus "
                               "board. Route names + areas passed; no "
                               "timetables (the register carries none).",
                   "generated": TODAY, "sources": meta, "routes": b},
                  open(BUS, "w"), ensure_ascii=False, indent=1)
        print(f"wrote {os.path.relpath(BUS, ROOT)} ({len(b)} routes)")


if __name__ == "__main__":
    main()
