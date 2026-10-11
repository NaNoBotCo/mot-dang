#!/usr/bin/env python3
"""Bake the Government Lottery draw — the public record — into data/lottery.json.

Same shape as make_air.py: fetched once here, written to data/, read by
build.py. The published tile makes no external request and REGISTERS AS AN
ALMANAC ENTRY: the record of what the Government Lottery Office announced,
never a prediction, a tip, or a lucky number. The ตรวจ is the reader's own.

    python3 importers/make_lottery.py               # one polite fetch
    python3 importers/make_lottery.py --from-cache  # rebuild offline from cache/

WHY THIS SOURCE (surveyed 2026-08-12, both candidates tested empirically):

1. data.go.th CKAN (opend.data.go.th, api-key from ~/.config/nanobotco/
   keys.json — the key itself never enters this repo): package_search over
   สลากกินแบ่ง / ผลสลาก / รางวัลสลาก / lottery / กองสลาก finds NO lottery-results
   dataset at all. The ~10 hits are keyword noise — household-income survey
   tables and one PDF circular about controlling lottery advertising. Nothing
   machine-readable, nothing from the GLO.
2. glo.or.th, the Government Lottery Office itself:
   - POST /api/checking/getLotteryResult answers 200 but with response:null
     for every body shape tried — it is the site's own per-ticket checker,
     not a results feed.
   - POST /api/lottery/getLatestLottery with an empty JSON body returns the
     complete official record of the latest draw: date, every prize tier with
     amounts, and the office's own PDF of the announcement sheet. CHOSEN —
     first-party (the office that conducts the draw), keyless, current the
     evening of the draw.

NEXT DRAW DATE IS DELIBERATELY ABSENT. Draws are nominally the 1st and 16th,
but the official calendar shifts around New Year and royal ceremony days, and
no GLO endpoint we could find publishes the schedule. A date the source has
not confirmed is a date this file does not carry (presence-only, as
everywhere in this repo).

Manners: ONE fetch per run, 45 s timeout, snapshot-first. The raw response is
archived under cache/lottery/ (gitignored with the rest of cache/). A fetch
that fails, or a sheet that fails validation, keeps what is on disk. A
re-fetch that finds the SAME draw leaves data/lottery.json byte-identical, so
the morning walk's nothing-new check stays meaningful — this record changes
twice a month, and the file should only churn when the draw does.

Validated before anything is written: the sheet's own status flag (1 is the
value a finished, published draw carries — observed, not documented), the
draw date parses, every number is digits of the width its tier promises, and
the four headline groups (รางวัลที่ 1, เลขหน้า 3 ตัว, เลขท้าย 3 ตัว, เลขท้าย 2 ตัว)
are present and non-empty. The source also publishes its separate N3 digit
lottery under an `n3` key; deliberately not baked — different product,
different tile if ever wanted.

PAST DRAWS -> data/lottery_history.json (surveyed 2026-10-03, from the
office's own front-end bundle, /_nuxt/*.js, LotteryCheckStore):
   - POST /api/lottery/getPeriodsByYear {"year": "2026", "type": "CHECKED"}
     lists the year's draw dates (each date twice, one per sheet number).
   - POST /api/lottery/getLotteryAward {"date": "16", "month": "09",
     "year": "2026"} returns ONE past draw in the same envelope as
     getLatestLottery, so build_record() reads it unchanged. Keyless, no
     CAPTCHA (the per-ticket checker is the one that carries reCAPTCHA).
   The history keeps the newest HISTORY_N draws, the latest one included,
   newest first; each entry is the `draw` object of data/lottery.json. A run
   fetches only the draws it does not hold yet: a sheet already in
   cache/lottery/ is read from there, and every request waits PAUSE seconds
   after the one before. The first run costs up to two period lists and
   HISTORY_N sheets; a run after a new draw costs one period list (the
   latest sheet is already in hand); a run with no new draw costs nothing
   beyond the latest-draw fetch. Unchanged draws -> byte-identical file.
"""
import json
import sys
import time
import urllib.request
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import ingest      # shared write discipline (WO-41 Phase 2)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lottery.json"
CACHE = ROOT / "cache" / "lottery"
URL = "https://www.glo.or.th/api/lottery/getLatestLottery"
URL_AWARD = "https://www.glo.or.th/api/lottery/getLotteryAward"
URL_PERIODS = "https://www.glo.or.th/api/lottery/getPeriodsByYear"
HIST = ROOT / "data" / "lottery_history.json"
HISTORY_N = 24
PAUSE = 3.0   # seconds between requests to the office
UA = ("mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; "
      "lottery-draw public-record snapshot, twice monthly)")

# GLO key -> (our id, Thai label, English label, digit width). Order here is
# display order: the four headline groups first, then the rest of the sheet.
PRIZES = [
    ("first",  "first",      "รางวัลที่ 1",                 "First prize",                  6),
    ("last3f", "front3",     "เลขหน้า 3 ตัว",               "Front three digits",           3),
    ("last3b", "back3",      "เลขท้าย 3 ตัว",               "Last three digits",            3),
    ("last2",  "last2",      "เลขท้าย 2 ตัว",               "Last two digits",              2),
    ("near1",  "near_first", "รางวัลข้างเคียงรางวัลที่ 1",   "Either side of the first prize", 6),
    ("second", "second",     "รางวัลที่ 2",                 "Second prize",                 6),
    ("third",  "third",      "รางวัลที่ 3",                 "Third prize",                  6),
    ("fourth", "fourth",     "รางวัลที่ 4",                 "Fourth prize",                 6),
    ("fifth",  "fifth",      "รางวัลที่ 5",                 "Fifth prize",                  6),
]
HEADLINE = {"first", "front3", "back3", "last2"}

_TH_WD = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี",
          "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
_EN_WD = ["Monday", "Tuesday", "Wednesday", "Thursday",
          "Friday", "Saturday", "Sunday"]
_TH_MO = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
          "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
_EN_MO = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def fetch(url=URL, body=None):
    """One polite POST. For the latest draw the empty JSON body is the whole
    request; the history calls pass their own small body."""
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


_last_request = [0.0]


def polite_fetch(url, body):
    """fetch(), PAUSE seconds after the previous office request of this run."""
    wait = _last_request[0] + PAUSE - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    try:
        return fetch(url, body)
    finally:
        _last_request[0] = time.monotonic()


def period_dates(year):
    """The office's draw dates for one CE year, newest first, de-duplicated."""
    payload = polite_fetch(URL_PERIODS, {"year": str(year), "type": "CHECKED"})
    rows = ((payload or {}).get("response") or {}).get("result") or []
    out = set()
    for r in rows:
        try:
            out.add(date.fromisoformat(str(r.get("date"))[:10]))
        except ValueError:
            continue
    return sorted(out, reverse=True)


def cached_sheet(day):
    f = CACHE / ("glo-%s.json" % day.isoformat())
    if f.exists():
        try:
            return json.loads(f.read_text())
        except ValueError:
            return None
    return None


def update_history(latest, fetched_at, offline):
    """data/lottery_history.json: the newest HISTORY_N draws, latest included.

    Draws already held stay as they are; a missing one comes from cache/ or,
    online, from one getLotteryAward request. A sheet that fails build_record()
    is left out and named, and the rest of the history still writes."""
    held = {}
    if HIST.exists():
        try:
            old = json.loads(HIST.read_text())
        except ValueError:
            old = {}
        for d in old.get("draws") or []:
            if d.get("date"):
                held[d["date"]] = d
    else:
        old = {}
    already = latest["date"] in held and len(held) >= HISTORY_N
    held[latest["date"]] = latest
    newest = date.fromisoformat(latest["date"])

    if already:
        wanted = []   # nothing new since the last run: no request at all
    elif offline:
        wanted = sorted((date.fromisoformat(f.stem[4:]) for f in CACHE.glob("glo-*.json")),
                        reverse=True) if CACHE.exists() else []
    else:
        wanted = []
        year = newest.year
        while len([d for d in wanted if d <= newest]) < HISTORY_N \
                and year >= newest.year - 2:
            try:
                wanted += [d for d in period_dates(year) if d <= newest]
            except Exception as e:
                print("🐜 period list %d failed (%s) — history from what is held" % (year, e))
                break
            year -= 1
    wanted = [d for d in wanted if d <= newest][:HISTORY_N]

    skipped = []
    for day in wanted:
        key = day.isoformat()
        if key in held:
            continue
        payload = cached_sheet(day)
        if payload is None and not offline:
            try:
                payload = polite_fetch(URL_AWARD, {"date": "%02d" % day.day,
                                                   "month": "%02d" % day.month,
                                                   "year": str(day.year)})
            except Exception as e:
                skipped.append("%s (%s)" % (key, e))
                continue
            CACHE.mkdir(parents=True, exist_ok=True)
            (CACHE / ("glo-%s.json" % key)).write_text(
                json.dumps(payload, ensure_ascii=False, indent=1))
        if payload is None:
            continue
        rec = build_record(payload, fetched_at)
        if isinstance(rec, str):
            skipped.append("%s (%s)" % (key, rec))
            continue
        if rec["draw"]["date"] != key:
            skipped.append("%s (sheet says %s)" % (key, rec["draw"]["date"]))
            continue
        held[key] = rec["draw"]

    draws = [held[k] for k in sorted(held, reverse=True)][:HISTORY_N]
    if old.get("draws") == draws:
        doc = old
    else:
        doc = {
            "generated": fetched_at[:10],
            "fetched_at": fetched_at,
            "source": ("สำนักงานสลากกินแบ่งรัฐบาล — Government Lottery Office, glo.or.th "
                       "(POST /api/lottery/getLotteryAward, one request a draw)"),
            "draws": draws,
        }
    ingest.write(HIST, doc, count=len(draws), min_rows=1,
                 source_published_at=draws[0]["date"], label="lottery_history.json")
    for s_ in skipped:
        print("🐜 history: left out %s" % s_)
    print("🐜 history: %d draws, %s to %s -> %s"
          % (len(draws), draws[-1]["date"], draws[0]["date"], HIST))


def newest_cache():
    files = sorted(CACHE.glob("glo-*.json")) if CACHE.exists() else []
    return files[-1] if files else None


def parse_amount(price):
    """GLO sends amounts as strings like '6000000.00'. None in, None out."""
    try:
        f = float(price)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else f


def build_record(payload, fetched_at):
    """The GLO envelope -> our record, or a str explaining the refusal."""
    resp = payload.get("response") if isinstance(payload, dict) else None
    if not isinstance(resp, dict):
        return "no response object in the payload"
    if resp.get("status") not in (None, 1):
        return "sheet status is %r, not a finished draw — keeping the snapshot" % (
            resp.get("status"),)
    try:
        d = date.fromisoformat(str(resp.get("date"))[:10])
    except ValueError:
        return "draw date %r does not parse" % (resp.get("date"),)

    tiers = resp.get("data") or {}
    prizes = []
    for glo_key, pid, th, en, width in PRIZES:
        tier = tiers.get(glo_key) or {}
        entries = tier.get("number") or []
        # The source's own drawn sequence, kept as-is. The official PDF prints
        # tiers re-sorted for scanning; consumers who want that can sort.
        entries = sorted(entries, key=lambda e: e.get("round", 0))
        nums = [str(e.get("value", "")).strip() for e in entries]
        nums = [n for n in nums if n]
        if not nums:
            if pid in HEADLINE:
                return "headline group %s is empty — keeping the snapshot" % pid
            continue  # presence-only: a tier the source did not carry is omitted
        for n in nums:
            if not (n.isdigit() and len(n) == width):
                return "%s carries %r, not %d digits — keeping the snapshot" % (
                    pid, n, width)
        rec = {"id": pid, "th": th, "en": en, "numbers": nums}
        amount = parse_amount(tier.get("price"))
        if amount is not None:
            rec["amount_baht"] = amount
        prizes.append(rec)

    date_th = "%sที่ %d %s %d" % (_TH_WD[d.weekday()], d.day, _TH_MO[d.month], d.year + 543)
    date_en = "%s %d %s %d" % (_EN_WD[d.weekday()], d.day, _EN_MO[d.month], d.year)
    draw = {
        "date": d.isoformat(),
        "date_th": date_th,
        "date_en": date_en,
        "be_year": d.year + 543,
        "prizes": prizes,
    }
    if resp.get("pdf_url"):
        # The office's own announcement sheet for this draw — provenance,
        # not furniture; the tile never renders it.
        draw["record_pdf"] = resp["pdf_url"]
    return {
        "generated": fetched_at[:10],
        "fetched_at": fetched_at,
        "source": ("สำนักงานสลากกินแบ่งรัฐบาล — Government Lottery Office, glo.or.th "
                   "(POST /api/lottery/getLatestLottery)"),
        "register": ("บันทึกผลตามประกาศทางการ ไม่ใช่คำทำนาย — the record of the announced "
                     "draw, never a prediction or a tip"),
        "draw": draw,
    }


def main():
    from_cache = "--from-cache" in sys.argv
    now = datetime.now(timezone(timedelta(hours=7)))
    fetched_at = now.isoformat(timespec="seconds")

    if from_cache:
        src = newest_cache()
        if not src:
            sys.exit("no cached sheet under cache/lottery/ — run once online first")
        payload = json.loads(src.read_text())
        print("🐜 rebuilding from %s (no network)" % src.name)
    else:
        try:
            payload = fetch()
        except Exception as e:
            msg = "lottery fetch failed (%s)" % e
            if OUT.exists():
                sys.exit("%s — keeping the snapshot on disk" % msg)
            sys.exit(msg)

    rec = build_record(payload, fetched_at)
    if isinstance(rec, str):
        if OUT.exists():
            sys.exit("🐜 %s" % rec)
        sys.exit(rec)

    if not from_cache:
        CACHE.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(payload, ensure_ascii=False, indent=1)
        (CACHE / ("glo-%s.json" % rec["draw"]["date"])).write_text(raw)

    # Unchanged draw -> untouched file, so git diff means something. Only the
    # draw itself is compared: fetched_at moves every run and must not count.
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text())
        except ValueError:
            old = {}
        if old.get("draw") == rec["draw"]:
            # Same draw: the file is left exactly as it was (the change gate
            # depends on that), but the run is still recorded — a sidecar that
            # cannot tell "checked, nothing new" from "nobody looked" is the
            # blindness WO-41 exists to end. ingest.write sees the identical
            # content hash and updates only the meta.
            ingest.write(OUT, rec, count=1, min_rows=1,
                         source_published_at=rec["draw"]["date"],
                         label="lottery.json")
            print("🐜 งวด %s unchanged — data/lottery.json kept as it was"
                  % rec["draw"]["date"])
            update_history(rec["draw"], fetched_at, from_cache)
            return

    # WO-41 Phase 2. The sheet is already validated above; this records the
    # run in the sidecar and keeps the atomic write. count=1 — a draw is one
    # record, and its own guard is the prize-tier validation, not a row count.
    ingest.write(OUT, rec, count=1, min_rows=1,
                 source_published_at=rec["draw"]["date"], label="lottery.json")
    first = next((p for p in rec["draw"]["prizes"] if p["id"] == "first"), {})
    print("🐜 งวด %s — รางวัลที่ 1: %s -> %s"
          % (rec["draw"]["date"], " ".join(first.get("numbers", [])), OUT))
    update_history(rec["draw"], fetched_at, from_cache)


if __name__ == "__main__":
    main()
