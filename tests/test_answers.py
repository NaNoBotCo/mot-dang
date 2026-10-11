#!/usr/bin/env python3
"""คำตอบ — the contracts that keep the answer pages worth landing on.

The three surfaces of answers_layer.py each make one promise a test has to
keep:

1. festival-dates: a date never appears without a source. Every row in
   data/festival_calendar.json names a festival that exists in the canon and
   a source that exists in the file; dates are real ISO dates in the row's
   own year. And the marquee date actually reaches the built pages and the
   ICS feed — a data file nobody renders is not an answer.
2. open-now: the hour table is the whole week (24 rows x 7 columns), and a
   capped section says out loud that it is capped — no silent truncation.
3. lists: the count in the heading equals the rows on the page equals the
   records in the canonical data. The number is a promise; drift is a lie
   with a headline.

Run after build.py:

    python3 tests/test_answers.py
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT))
import answers_layer  # noqa: E402

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  %s" % name)
    else:
        failures.append(name)
        print("  FAIL %s %s" % (name, detail))


# ---- 1. the calendar file: no date without a source -----------------------
doc = json.loads((ROOT / "data" / "festival_calendar.json").read_text())
canon = {f["id"] for f in
         json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]}
sources = doc.get("sources", {})
check("calendar has rows", len(doc.get("rows", [])) > 0)
for r in doc.get("rows", []):
    rid = "%s/%s" % (r.get("festival_id"), r.get("year"))
    check("row %s names a canon festival" % rid, r["festival_id"] in canon)
    check("row %s names a known source" % rid, r.get("source") in sources)
    try:
        a = datetime.date.fromisoformat(r["date_start"])
        b = datetime.date.fromisoformat(r["date_end"])
        check("row %s dates are ordered, in-year" % rid,
              a <= b and a.year == r["year"])
    except (KeyError, ValueError) as e:
        check("row %s dates parse" % rid, False, str(e))
for sid, s in sources.items():
    check("source %s carries name+url" % sid,
          bool(s.get("name_en")) and str(s.get("url", "")).startswith("https://"))

# ---- the built pages ------------------------------------------------------
if not (DOCS / "festival-dates.html").exists():
    print("  (docs/ not built — run python3 build.py first; "
          "skipping the built-page checks)")
    sys.exit(1 if failures else 0)

fd = (DOCS / "festival-dates.html").read_text()
fests = json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]
for f in fests:
    check("festival-dates lists %s" % f["id"], f["name_th"] in fd)
check("festival-dates carries the FAQ JSON-LD", '"FAQPage"' in fd)
check("festival-dates never renders a Python None", ">None<" not in fd)

# the marquee row travels: calendar file -> dates page, festival page, ICS
yp = next(r for r in doc["rows"]
          if r["festival_id"] == "yi-peng-loi-krathong" and r["year"] == 2026)
check("Yi Peng 2026 date is on festival-dates.html",
      "24 พฤศจิกายน 2569" in fd)
fp = (DOCS / "festivals" / "yi-peng-loi-krathong.html").read_text()
check("Yi Peng 2026 date is on the festival page",
      "24 พฤศจิกายน 2569" in fp and "ปฏิทินจันทรคติ" in fp)
ics = (DOCS / "festivals.ics").read_text()
check("Yi Peng 2026 reached festivals.ics",
      "UID:lunar-yi-peng-loi-krathong-%s@motdang.net" % yp["date_start"] in ics)
check("ICS lunar entries name their calendar source",
      "Published Thai lunar-calendar date" in ics)

# ---- 2. open-now: whole week, no silent caps ------------------------------
on = (DOCS / "open-now.html").read_text()
check("open-now hour table has 24 rows",
      len(re.findall(r'<tr data-h="\d+">', on)) == 24)
check("open-now hour rows have 7 day cells",
      all(len(re.findall(r'<td data-d="\d"', row)) == 7
          for row in re.findall(r'<tr data-h="\d+">.*?</tr>', on)))
check("open-now states the silence rule", "ความเงียบไม่ใช่คำว่าไม่" in on)
for m in re.finditer(
        r'<span class="count">\(([\d,]+)\)</span></h2>.*?<ul class="dir">(.*?)</ul>(.*?)(?=<h2|$)',
        on, re.S):
    n = int(m.group(1).replace(",", ""))
    lis = len(re.findall(r"<li ", m.group(2)))
    if n > lis:
        check("open-now capped section (%d of %d) says so" % (lis, n),
              "แสดง" in m.group(3), "cap note missing")
    else:
        check("open-now section count matches rows (%d)" % n, n == lis)

# ---- 3. lists: the heading number is the rows on the page -----------------
data = {p: json.loads((ROOT / "data" / "canonical" / ("%s.json" % p)).read_text())
        for p in ("cm", "cr")}
for L in answers_layer.LISTS:
    page = (DOCS / "lists" / ("%s.html" % L["slug"])).read_text()
    m = re.search(r'<span class="count">\(([\d,]+)\)</span>', page)
    heading = int(m.group(1).replace(",", "")) if m else -1
    lis = len(re.findall(r"<li ", page.split('<ul class="dir"', 1)[1]))
    recs = sum(1 for r in data[L["prov"]] if L["cat"] in (r.get("cat") or []))
    check("list %s: heading %d == rows %d == data %d"
          % (L["slug"], heading, lis, recs), heading == lis == recs)
    check("list %s carries ItemList JSON-LD" % L["slug"], '"ItemList"' in page)
check("lists hub exists", (DOCS / "lists" / "index.html").exists())

# ---- 4. compare-cm-cr: every number is counted, nothing is claimed ---------
# WO-102 Option A. The page may not be in docs/ until the next build, so the
# contract is checked by rendering it here from the canonical data, then also
# against the built file when it exists.
import html as _html  # noqa: E402
_cats = json.loads((ROOT / "data" / "categories.json").read_text())
_cats = _cats["categories"] if isinstance(_cats, dict) else _cats
_catkeys = {c["key"] for c in _cats}
_cap = {}


def _stub_page(title, body, depth=0, **kw):
    _cap["title"], _cap["body"] = title, body
    return body


_g = {"bi": lambda th, en: "%s / %s" % (th, en), "esc": _html.escape,
      "page": _stub_page, "share_block": lambda *a, **k: "",
      "BASE": "https://motdang.net/",
      "_CATPAIR": {c["key"]: [c["th"], c["en"]] for c in _cats}}
rendered = answers_layer.compare_page(_g, data)
check("compare page renders", bool(rendered))
if rendered:
    b = _cap["body"]
    ncm, ncr = len(data["cm"]), len(data["cr"])
    check("compare: CM total (%d) is the counted number on the page" % ncm,
          ("%d" % ncm if ncm < 1000 else "{:,}".format(ncm)) in b)
    check("compare: CR total (%d) is on the page" % ncr,
          "{:,}".format(ncr) in b)
    # the strongest lean is re-derived and must be named
    ccm = answers_layer._cat_counts(data["cm"])
    ccr = answers_layer._cat_counts(data["cr"])
    top_cr = answers_layer._leans(ccr, ncr, ccm, ncm, answers_layer.COMPARE_MIN_CR)
    check("compare: names Chiang Rai's top lean (%s)"
          % (top_cr[0][0] if top_cr else "?"),
          bool(top_cr) and ("cat=%s" % top_cr[0][0]) in b)
    check("compare: states what it does NOT count (price/safety)",
          "does <b>not</b> answer" in b)
    check("compare: never renders a Python None", ">None<" not in b)
    for c in set(re.findall(r'search\.html\?cat=([a-zA-Z\-]+)', b)):
        check("compare: cat link %s is a real category" % c, c in _catkeys)
built = DOCS / "compare-cm-cr.html"
if built.exists():
    cb = built.read_text()
    check("compare built file carries the CR count",
          "{:,}".format(len(data["cr"])) in cb)
    check("compare built file is indexable", "index,follow" in cb or "noindex" not in cb)
else:
    print("  (compare-cm-cr.html not built yet — the walk will build it)")

# ---- 5. orientation: no claim without provenance --------------------------
# WO-102 Option A phase two. The directory holds no prices and measures no
# safety, so every line in the data file must name a source or be Nan's own
# framing (`by`). A claim from nowhere is the one thing this page cannot ship.
odoc = json.loads((ROOT / "data" / "curated" / "orientation.json").read_text())
otopics = odoc.get("topics", [])
check("orientation has topics", len(otopics) > 0)
for t in otopics:
    tid = t.get("id", "?")
    check("orientation %s has a bilingual question" % tid,
          bool(t.get("q_th")) and bool(t.get("q_en")))
    if t.get("items"):
        # a per-item verdict topic: each item is Nan's call (`by`) plus an
        # outside view that names its source. A verdict from nowhere cannot ship.
        check("orientation %s has items" % tid, len(t["items"]) > 0)
        for it in t["items"]:
            nm = it.get("en") or it.get("name_en") or "?"
            check("worth-visiting '%s' has a verdict" % nm,
                  bool(it.get("verdict")) and bool(it.get("verdict_en")))
            check("worth-visiting '%s' verdict is attributed" % nm, bool(it.get("by")))
            check("worth-visiting '%s' outside view names a source" % nm,
                  bool((it.get("source") or {}).get("url")))
            for k in ("source", "source2"):
                s = it.get(k)
                if s:
                    check("worth-visiting '%s' source is https" % nm,
                          str(s.get("url", "")).startswith("https://"))
        continue
    check("orientation %s stance is attributed" % tid, bool(t.get("by")))
    alllines = list(t.get("evidence", [])) + list(t.get("exceptions", []))
    check("orientation %s has at least one evidence line" % tid,
          len(t.get("evidence", [])) > 0)
    for it in alllines:
        has_src = bool((it.get("source") or {}).get("url")) or bool(it.get("by"))
        check("orientation %s: '%s' names its provenance"
              % (tid, (it.get("en") or "")[:40]), has_src)
        for k in ("source", "source2"):
            s = it.get(k)
            if s:
                check("orientation %s source URL is https" % tid,
                      str(s.get("url", "")).startswith("https://"))
rendered_o = answers_layer.orientation_page(_g)
check("orientation page renders", bool(rendered_o))
if rendered_o:
    ob = _cap["body"]
    check("orientation names the Pai lion source",
          "chiangmaicitylife.com" in ob or "thethaiger.com" in ob)
    check("orientation carries the cheap stance", "Cheap" in ob)
    check("orientation carries the safety stance", "surveillance" in ob)
    check("orientation carries the worth-visiting verdicts", "Worth it" in ob)
    check("orientation renders the tiger/lion skip verdict", "ไม่แนะนำ" in ob)
    check("orientation keeps Nan's Pai / Mae Hong Son note", "Mae Hong Son" in ob)
    check("orientation keeps Nan's zoo caveat", "black leopard" in ob)
    check("orientation never renders a Python None", ">None<" not in ob)
obuilt = DOCS / "cost-of-living-and-safety.html"
if not obuilt.exists():
    print("  (cost-of-living-and-safety.html not built yet — the walk will build it)")

print()
if failures:
    print("FAILED: %d — %s" % (len(failures), ", ".join(failures[:8])))
    sys.exit(1)
print("all good — the answers keep their promises")
