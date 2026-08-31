#!/usr/bin/env python3
"""Harvest this year's festival dates from official announcements.

The festivals canon (data/festivals.json) carries a date RULE and never a date.
This is the other half: the routine pass that turns "usually late May" into
"26 May – 2 June 2569, announced by the province on this page".

What it does NOT do is publish a date on its own authority. Every row carries
the source URL and a status:

    announced — a canon festival matched AND a date parsed out of an official
                source (a provincial PR office, a municipality, the organiser).
                These are safe to show, attributed, on the festival page.
    candidate — something festival-shaped turned up but either the festival or
                the date is uncertain. Held for a human to look at. Nothing on
                the site reads these.

Sources were probed on 2026-07-29 and only the ones that actually answered a
plain fetch are in here. Two of the spec's first-choice sources do not:
tourismthailand.org and chiangmaipao.go.th both refuse (recorded as `blocked`
in data/sources.json), and chiangmai.go.th serves a self-signed certificate. The
provincial PR offices and Chiang Mai municipality answer fine and are where the
festival announcements actually live, so that is what this reads.

Snapshot-first and gentle, same manners as harvest_events.py and
crawl_overpass.py: every fetch lands in cache/festivals/ with the date taken, a
rerun only touches what is stale, and build.py never makes a network call.

    python3 importers/harvest_festivals.py            # fetch what is stale
    python3 importers/harvest_festivals.py --refetch  # ignore the cache
    python3 importers/harvest_festivals.py --dry      # parse cache only, no network
"""

import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime

import ingest      # shared write discipline (WO-41 Phase 2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "festivals")
CANON = os.path.join(ROOT, "data", "festivals.json")
OUT = os.path.join(ROOT, "data", "festival_dates.json")
UA = ("MotDangEvents/1.0 (+https://motdang.net/festivals.html; "
      "festival dates for a local directory)")
TIMEOUT = 25
STALE_DAYS = 7        # announcements are weekly news, not hourly
PAUSE = 3.0           # gentle: government sites, one at a time

# Probed 2026-07-29; `official` decides whether a parsed date may be published.
SOURCES = [
    {"id": "prd-chiangmai", "official": True,
     "name_th": "สำนักงานประชาสัมพันธ์จังหวัดเชียงใหม่",
     "name_en": "Chiang Mai Provincial Public Relations Office",
     "url": "https://chiangmai.prd.go.th/",
     "link_pattern": r"/th/content/category/detail/id/\d+/iid/\d+"},
    {"id": "prd-chiangrai", "official": True,
     "name_th": "สำนักงานประชาสัมพันธ์จังหวัดเชียงราย",
     "name_en": "Chiang Rai Provincial Public Relations Office",
     "url": "https://chiangrai.prd.go.th/",
     "link_pattern": r"/th/content/category/detail/id/\d+/iid/\d+"},
    {"id": "cmcity-activities", "official": True,
     "name_th": "เทศบาลนครเชียงใหม่ — ข่าวกิจกรรม",
     "name_en": "Chiang Mai Municipality — activity news",
     "url": "https://www.cmcity.go.th/list/group/321/%E0%B8%82%E0%B9%88%E0%B8%B2"
            "%E0%B8%A7%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1/",
     "link_pattern": r"/News/\d+-"},
    {"id": "cea-cmdw", "official": True,
     "name_th": "เทศกาลงานออกแบบเชียงใหม่ (CEA)",
     "name_en": "Chiang Mai Design Week (CEA)",
     "url": "https://www.chiangmaidesignweek.com/",
     "link_pattern": r"/(?:cmdw\d+|event|program)"},
    {"id": "singhapark", "official": True,
     "name_th": "สิงห์ปาร์ค เชียงราย",
     "name_en": "Singha Park Chiang Rai",
     "url": "https://singhapark.com/",
     "link_pattern": r"/(?:event|activity|news)"},
    {"id": "maefahluang", "official": True,
     "name_th": "มูลนิธิแม่ฟ้าหลวง (ดอยตุง)",
     "name_en": "Mae Fah Luang Foundation (Doi Tung)",
     "url": "https://www.maefahluang.org/",
     "link_pattern": r"/(?:event|news|activity|กิจกรรม)"},
    {"id": "chiangraifocus", "official": False,
     "name_th": "เชียงรายโฟกัส",
     "name_en": "Chiang Rai Focus",
     "url": "https://www.chiangraifocus.com/",
     "link_pattern": r"/(?:news|event)/"},
]

# ------------------------------------------------------------------ Thai dates
MONTHS_FULL = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
MONTHS_ABBR = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
               "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
MONTH_NUM = {}
for _i, (_f, _a) in enumerate(zip(MONTHS_FULL, MONTHS_ABBR), start=1):
    MONTH_NUM[_f] = _i
    MONTH_NUM[_a] = _i
    MONTH_NUM[_a.replace(".", "")] = _i
_MON = "|".join(sorted((re.escape(k) for k in MONTH_NUM), key=len, reverse=True))
DASH = r"[-–—ถึง\s]{1,6}"

# "1–3 กุมภาพันธ์ 2569" — a span inside one month
RE_SPAN_1M = re.compile(r"(\d{1,2})\s*[-–—]\s*(\d{1,2})\s*(" + _MON + r")\s*(?:พ\.?ศ\.?\s*)?(\d{4})?")
# "26 มกราคม – 4 กุมภาพันธ์ 2569" — a span across two months
RE_SPAN_2M = re.compile(r"(\d{1,2})\s*(" + _MON + r")\s*(?:พ\.?ศ\.?\s*)?(\d{4})?" + DASH +
                        r"(\d{1,2})\s*(" + _MON + r")\s*(?:พ\.?ศ\.?\s*)?(\d{4})?")
# "วันที่ 12 สิงหาคม 2569" — a single day
RE_ONE = re.compile(r"(?:วันที่\s*)?(\d{1,2})\s*(" + _MON + r")\s*(?:พ\.?ศ\.?\s*)?(\d{4})?")


def _ce(year_txt, month, today):
    """Buddhist era to Gregorian; absent year means the next occurrence."""
    if year_txt:
        y = int(year_txt)
        return y - 543 if y > 2400 else y
    y = today.year
    return y + 1 if month < today.month - 1 else y


def _mk(y, m, d):
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def parse_thai_dates(text, today=None):
    """First date or span found in a Thai string -> (start, end) ISO, or None.

    Deliberately conservative. Government prose is full of numbers — budget
    years, document ids, phone numbers — and a wrong date on a festival page is
    worse than no date, so anything that does not match one of three explicit
    shapes is left alone.
    """
    today = today or date.today()
    text = unicodedata.normalize("NFC", text)
    m = RE_SPAN_2M.search(text)
    if m:
        d1, mo1, y1, d2, mo2, y2 = m.groups()
        m1, m2 = MONTH_NUM[mo1], MONTH_NUM[mo2]
        yy2 = _ce(y2 or y1, m2, today)
        yy1 = _ce(y1 or y2, m1, today)
        if m1 > m2 and not (y1 and y2):
            yy1 = yy2 - 1                        # a span that crosses new year
        a, b = _mk(yy1, m1, int(d1)), _mk(yy2, m2, int(d2))
        if a and b and a <= b:
            return a, b
    m = RE_SPAN_1M.search(text)
    if m:
        d1, d2, mo, y = m.groups()
        mm = MONTH_NUM[mo]
        yy = _ce(y, mm, today)
        a, b = _mk(yy, mm, int(d1)), _mk(yy, mm, int(d2))
        if a and b and a <= b:
            return a, b
    m = RE_ONE.search(text)
    if m:
        d1, mo, y = m.groups()
        mm = MONTH_NUM[mo]
        a = _mk(_ce(y, mm, today), mm, int(d1))
        if a:
            return a, a
    return None


# --------------------------------------------------------------- canon match
FESTIVAL_WORDS = ("เทศกาล", "ประเพณี", "ปอย", "งานประจำปี", "สืบชะตา",
                  "ลอยกระทง", "ยี่เป็ง", "สงกรานต์", "ตักบาตร", "แห่", "กฐิน",
                  "มหกรรม", "งานฤดูหนาว", "บวงสรวง")

# Government news is overwhelmingly retrospective — "the governor attended",
# "citizens joined" — and a report of a ceremony that already happened is not an
# announcement of next year's. Only a forward-looking headline may set a date.
ANNOUNCING = ("ขอเชิญ", "เชิญชวน", "เตรียมจัด", "เตรียมความพร้อม", "กำหนดจัด",
              "พร้อมจัด", "จัดขึ้นระหว่าง", "จะจัดขึ้น", "เปิดลงทะเบียน",
              "ชวนเที่ยว", "ชวนร่วม", "แถลงข่าว")
MAX_SPAN_DAYS = 45      # longer than any festival in the canon


def _plausible(fid, canon_by_id, start, end, today):
    """Would this date be a believable instance of this festival?

    Three cheap gates, each of which the first live run would have needed:
    the date must be in the future (an announcement is about what is coming),
    the span must be festival-length, and it must land in a month the canon
    already says this festival falls in. A Khao Phansa "date" in late July that
    turns out to be a King's-Birthday merit ceremony fails the third.
    """
    if not (start and end):
        return False, "no-date"
    if start < today.isoformat():
        return False, "past"
    a = date.fromisoformat(start)
    b = date.fromisoformat(end)
    if (b - a).days > MAX_SPAN_DAYS:
        return False, "span-too-long"
    f = canon_by_id.get(fid)
    if not f:
        return False, "no-canon"
    months = set(f.get("months") or [f["month"]])
    # allow one month either side: lunar festivals drift across a boundary
    near = {((m + d - 1) % 12) + 1 for m in months for d in (-1, 0, 1)}
    if a.month not in near:
        return False, "wrong-month"
    return True, "ok"


def _norm(s):
    s = unicodedata.normalize("NFC", s or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def match_canon(title, canon):
    """Which canon festival is this headline about? Strict: a full Thai name, or
    a distinctive stem of it. Returns (festival_id, how) or (None, None)."""
    t = _norm(title)
    for f in canon:
        name = f["name_th"].split("(")[0].strip()
        if len(name) >= 6 and name in t:
            return f["id"], "name"
    # A few festivals are near-universally written in a shortened form.
    stems = {"อินทขีล": "inthakhin", "ยี่เป็ง": "yi-peng-loi-krathong",
             "ลอยกระทง": "yi-peng-loi-krathong", "สงกรานต์": "songkran-pi-mai-muang",
             "ปอยส่างลอง": "poy-sang-long", "ป๋าเวณีปี๋ใหม่เมือง": "songkran-pi-mai-muang",
             "ร่มบ่อสร้าง": "bo-sang-umbrella", "ไม้ดอกไม้ประดับ": "cm-flower-festival",
             "พ่อขุนเม็งราย": "cr-red-cross-fair", "สืบชะตาเมือง": "suep-chata-mueang",
             "ตานก๋วยสลาก": "tan-kuay-salak", "สลากภัต": "tan-kuay-salak",
             "งานออกแบบเชียงใหม่": "cm-design-week", "บอลลูน": "singha-balloon-fiesta"}
    ids = {f["id"] for f in canon}
    for stem, fid in stems.items():
        if stem in t and fid in ids:
            return fid, "stem"
    return None, None


# ------------------------------------------------------------------ fetching
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "th,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=TIMEOUT,
                                context=ssl.create_default_context()) as r:
        return r.read(800_000).decode("utf-8", "replace")


def cached(sid, url, refetch=False, dry=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, sid + ".json")
    if not refetch and os.path.exists(path):
        try:
            snap = json.load(open(path))
            taken = datetime.strptime(snap["fetched"], "%Y-%m-%d").date()
            if dry or (date.today() - taken).days < STALE_DAYS:
                return snap["body"], True
        except (ValueError, KeyError, json.JSONDecodeError):
            pass
    if dry:
        return None, True
    body = fetch(url)
    json.dump({"url": url, "fetched": date.today().isoformat(), "body": body},
              open(path, "w"))
    time.sleep(PAUSE)
    return body, False


ANCHOR = re.compile(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', re.S | re.I)


def headlines(body, src):
    """(url, title) pairs that look like announcements, not site chrome."""
    pat = re.compile(src["link_pattern"])
    base = re.match(r"https?://[^/]+", src["url"]).group(0)
    out, seen = [], set()
    for href, inner in ANCHOR.findall(body):
        if not pat.search(href):
            continue
        title = _norm(inner)
        if len(title) < 15 or len(re.findall(r"[ก-๙]", title)) < 8:
            continue
        full = href if href.startswith("http") else base + href
        if (full, title) in seen:
            continue
        seen.add((full, title))
        out.append((full, title))
    return out


# ----------------------------------------------------------------------- main
def main():
    refetch = "--refetch" in sys.argv
    dry = "--dry" in sys.argv
    canon = json.load(open(CANON))["festivals"]
    canon_by_id = {f["id"]: f for f in canon}
    today = date.today()
    rows, failures, fetched = [], [], 0

    for src in SOURCES:
        try:
            body, was_cached = cached(src["id"], src["url"], refetch, dry)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as ex:
            failures.append((src["id"], str(ex)[:90]))
            print(f"  FAIL   {src['id']}: {str(ex)[:80]}")
            continue
        if body is None:
            print(f"  skip   {src['id']}: no snapshot (--dry)")
            continue
        fetched += 0 if was_cached else 1
        hits = headlines(body, src)
        kept = 0
        for url, title in hits:
            fid, how = match_canon(title, canon)
            dates = parse_thai_dates(title, today)
            festivalish = fid or any(w in title for w in FESTIVAL_WORDS)
            if not festivalish:
                continue
            ok, why = _plausible(fid, canon_by_id,
                                 dates[0] if dates else None,
                                 dates[1] if dates else None, today)
            announcing = any(w in title for w in ANNOUNCING)
            status = ("announced" if (ok and announcing and src["official"])
                      else "candidate")
            rows.append({
                "festival_id": fid, "matched_by": how,
                "held_because": None if status == "announced" else (
                    why if not ok else "not-an-announcement"),
                "title_th": title[:220], "source_id": src["id"],
                "source_name_th": src["name_th"], "source_name_en": src["name_en"],
                "source_url": url, "official": src["official"],
                "date_start": dates[0] if dates else None,
                "date_end": dates[1] if dates else None,
                "status": status, "first_seen": today.isoformat(),
            })
            kept += 1
        print(f"  {'cache' if was_cached else 'fetch'}  {src['id']}: "
              f"{len(hits)} headline(s), {kept} festival-shaped")

    # Same festival announced on two sources: keep the official one, then the
    # one that actually carries a date.
    best = {}
    for r in rows:
        key = (r["festival_id"] or r["title_th"][:60], r["date_start"])
        rank = (r["status"] == "announced", r["official"], bool(r["date_start"]))
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r)
    rows = [r for _, r in best.values()]
    rows.sort(key=lambda r: (r["date_start"] or "9999", r["title_th"]))

    announced = [r for r in rows if r["status"] == "announced"]
    doc = {
        "generated": today.isoformat(),
        "_comment": (
            "Dated instances of the recurring festivals in data/festivals.json, "
            "harvested from official announcements. status=announced means a canon "
            "festival matched AND a date parsed out of an official source, and only "
            "those are shown on the site, always with the source link. "
            "status=candidate is held for human review and is never published. "
            "Nothing here is inferred from the lunar calendar — a rule is not a date."),
        "sources": [{"id": s["id"], "name_en": s["name_en"], "url": s["url"],
                     "official": s["official"]} for s in SOURCES],
        "count": len(rows), "announced": len(announced), "rows": rows,
    }
    # WO-41 Phase 2. min_rows=1 on ROWS, not on announced: a week when no
    # official source has announced anything is a true and ordinary state of
    # the world (the file's own charter — a rule is not a date), while zero
    # rows at all means the parse or the fetch broke.
    ingest.write(OUT, doc, count=len(rows), min_rows=1,
                 label="festival_dates.json")
    print(f"   {len(announced)} announced, {fetched} live fetch(es)")
    for r in announced[:12]:
        print(f"   {r['date_start']}..{r['date_end']}  {r['festival_id']}  "
              f"{r['title_th'][:60]}")
    if failures:
        print(f"⚠  {len(failures)} source(s) failed: {[f[0] for f in failures]}")


if __name__ == "__main__":
    main()
