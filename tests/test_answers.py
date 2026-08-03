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

print()
if failures:
    print("FAILED: %d — %s" % (len(failures), ", ".join(failures[:8])))
    sys.exit(1)
print("all good — the answers keep their promises")
