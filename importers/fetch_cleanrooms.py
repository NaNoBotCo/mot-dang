#!/usr/bin/env python3
"""ห้องปลอดฝุ่น — the clean-air rooms, from the Department of Health's own register.

WO-57 item 4. WHAT THIS SETTLES. Smoke season is the hazard this city meets
every February, and the site could say what the PM2.5 number meant but not
where to go and breathe. The instinct was to guess — malls have air handling,
libraries are indoors — and a guess is exactly what this site does not print.
It turns out no guess is needed: กรมอนามัย keeps a national register of
assessed clean-air rooms at podfoon.anamai.moph.go.th, with a public API,
and it holds 2,433 PUBLICLY ACCESSIBLE rooms across our two provinces, every
one of them with a phone number and all but five with a pin.

WHAT IT CORRECTS. A March 2026 newspaper piece said Chiang Mai had 45 public
clean-air rooms and that only 13 of 25 districts had any. The register says
1,382 public rooms in Chiang Mai across all 26 of its districts. The paper was
counting one programme's rooms; the register counts every assessed one. This
is the reason the rule here is read the register, never the article about it.

WHAT RIDES AND WHAT IS DROPPED:
  · PublicAccess only. Over a thousand rows in each province are households
    that registered their own room, and a stranger's living room is not
    somewhere to send anybody.
  · A row with no pin is dropped, and the count of those is kept and printed.
  · A row with a BULK-ENTRY PHONE loses it. See SHARE_SITES.
  · A row with a BAD pin is kept, flagged, and left out of the nearest-thing
    search. The register is entered by thousands of hands and it shows: one
    row carries latitude 473027, another 10.0/9.0, sixty sit outside both
    provinces entirely, and forty-five rows naming amphoe as far off as
    Mae Sai and Omkoi are pinned within five kilometres of Tha Phae Gate —
    which is exactly what the first draft of /foon.html offered as the
    nearest clean-air room, 226 m away and 90 km wrong. Two checks catch
    them: a bounding box, and a nearest-middle test against every other row
    claiming the same amphoe. See FAR_KM for how it was tuned and why it
    errs loose.
  · The GRADE rides on every row and is never smoothed: `evaluator` means an
    officer assessed it and there is an expiry date; `self` means the place
    assessed itself. 221 of 2,433 are evaluator-assessed. A page that shows
    them alike is a page that has invented a standard.
  · The assessment DATE rides too. Some rows were last assessed in 2024, and
    "assessed" without "when" is not a fact anybody can use.

SNAPSHOT FIRST, like every other fetcher here: if the register cannot be
reached, whatever is on disk stays. A season with an old list beats a season
with none.

    python3 importers/fetch_cleanrooms.py            # keeps a fresh snapshot
    python3 importers/fetch_cleanrooms.py --refetch  # force
"""
import datetime
import hashlib
import json
import math
import re
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cleanrooms.json"
META = ROOT / "data" / "cleanrooms.meta.json"
SNAP = ROOT / "cache" / "cleanrooms"
STALE_DAYS = 20
# The two provinces, generously. Anything outside is not a Chiang Mai or
# Chiang Rai room however the register files it.
BBOX = (17.0, 20.5, 97.3, 100.4)          # lat_min, lat_max, lng_min, lng_max
# A pin is called misplaced when it is FAR_KM from the middle of the rows that
# share its own amphoe AND at least RATIO times as far from that middle as
# from the nearest OTHER amphoe's middle. A plain radius does not work: the
# amphoe here range from 40 km² to 2,000 km², so any radius wide enough for
# อมก๋อย waves through a Doi Saket room pinned at Tha Phae Gate, 15 km from
# where it belongs and 3 km from the middle of Mueang.
#
# TUNED AGAINST A TRUTH SET, not by feel. 45 rows sit within 5 km of Tha Phae
# while naming an amphoe that is not Mueang Chiang Mai; every one of those is
# wrong by inspection. At 10 km and 2.0 the check flags 144 of 2,428 rows and
# catches 42 of those 45. Tighter ratios flag fewer and catch far fewer.
#
# THE ERRORS ARE NOT SYMMETRIC and that is the whole argument for erring
# loose. A genuine room wrongly flagged keeps its register row, its phone and
# its count and only loses its seat in the nearest-thing list. A wrong pin
# left unflagged offers somebody with asthma a room twenty kilometres away as
# though it were down the soi. So: flag generously, delete nothing, and say
# on the page how many were set aside and why.
# A phone entered at more than SHARE_SITES places that are SHARE_KM or more
# apart is a bulk-entry default, not that place's number. One number,
# 053211048, is on 428 rows at 246 separate sites — CMU Fitness, a dance
# studio, two hospitals and a district office among them. Only four numbers
# in the whole register behave this way, and Suan Prung's real switchboard
# (41 rows, one site) is correctly left alone, so the test separates a
# switchboard from a default rather than punishing large institutions.
# The number is kept on the row as `tDefault` and taken out of `t`: a wrong
# number offered as a place's own is worse than no number, and this is not
# the absent-evidence case — it is a positively wrong one.
SHARE_SITES = 3
SHARE_KM = 2.0
FAR_KM = 10.0
FAR_RATIO = 2.0
SETTLE_KM = 60.0   # first pass only, so one wild pin cannot drag its own median

API = "https://podfoon.anamai.moph.go.th/api/cleanroom"
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle register read)"
# PROVINCE_ID from /api/cleanroom/province — not the two-digit province code.
PROVINCES = [("cm", 38, "เชียงใหม่"), ("cr", 45, "เชียงราย")]
SOURCE = {
    "name": "ห้องปลอดฝุ่น — ระบบฐานข้อมูลห้องปลอดฝุ่น กรมอนามัย",
    "url": "https://podfoon.anamai.moph.go.th/",
    "api": API,
    "credit": "กรมอนามัย กระทรวงสาธารณสุข (ออกแบบระบบโดย CCDC มหาวิทยาลัยเชียงใหม่)",
    "note_th": "ทะเบียนราชการ ไม่ใช่รายการที่มดแดงประเมินเอง",
    "note_en": "A state register, not an assessment Mot Dang made.",
}
# A second door, kept because it is the one a Chiang Mai reader is likelier to
# have heard of, and because two doors to the same fact is how this site says
# it did not invent the fact.
ALSO = {"name": "พักปอด — CMU UNISERV + CCDC",
        "url": "https://pakpod.cmuccdc.org/"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def km(a, b, c, e):
    R, t = 6371.0, math.pi / 180
    x, y = (c - a) * t, (e - b) * t
    h = (math.sin(x / 2) ** 2
         + math.cos(a * t) * math.cos(c * t) * math.sin(y / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def flag_shared_phones(rooms):
    """Take away the numbers that are somebody else's.

    Counts SITES, not rows: a hospital that registers forty rooms behind one
    switchboard is one site and keeps its number. A number that turns up at
    four or more places kilometres apart was typed in by whoever filed the
    batch."""
    by = {}
    for r in rooms:
        n = re.sub(r"\D", "", r.get("t") or "")
        if len(n) >= 6:
            by.setdefault(n, []).append(r)
    hit = 0
    for n, rs in by.items():
        sites = []
        for r in rs:
            if not any(km(c[0], c[1], r["la"], r["ln"]) <= SHARE_KM
                       for c in sites):
                sites.append((r["la"], r["ln"]))
        if len(sites) > SHARE_SITES:
            for r in rs:
                r["tDefault"] = r["t"]
                r["t"] = ""
                hit += 1
    return hit


def flag_pins(rooms):
    """Mark the pins that cannot be where the row says they are.

    Never deletes: a flagged row keeps its place in the register, its phone
    and its assessment, and only loses its seat in the nearest-thing search —
    a wrong pin there is a person sent twenty kilometres, which is the one
    failure this page cannot afford. Returns the counts so the page can say
    how many and why instead of quietly holding a smaller number.
    """
    counts = {"outside": 0, "far": 0, "unchecked": 0}
    inside = []
    for r in rooms:
        if not (BBOX[0] <= r["la"] <= BBOX[1] and BBOX[2] <= r["ln"] <= BBOX[3]):
            r["doubt"] = "outside"
            counts["outside"] += 1
        else:
            inside.append(r)

    # Twelve of the seventy rows that name no amphoe put one in their own
    # title — สำนักงานสาธารณสุขอำเภอดอยหล่อ, โรงพยาบาลพร้าว, ที่ว่าการอำเภอ
    # สันกำแพง. Names of three characters or fewer are not used: พาน and ฝาง
    # are amphoe here and also ordinary Thai words, and Thai writes no spaces
    # to tell one use from the other. A name-derived amphoe is only ever used
    # to CHECK a pin, never to place one.
    known = sorted({r["d"] for r in inside if r["d"] and len(r["d"]) > 3},
                   key=len, reverse=True)
    for r in inside:
        if not r["d"]:
            hit = next((a for a in known if a in r["n"]), None)
            if hit:
                r["dFromName"] = hit

    def claimed(r):
        return r["d"] or r.get("dFromName") or ""

    def middles(rs):
        by = {}
        for r in rs:
            # Only a row that states its own amphoe defines a middle. A
            # name-derived one is a guess, and a guess must not move the
            # yardstick it is about to be measured against.
            if r["d"]:
                by.setdefault((r["p"], r["d"]), []).append(r)
        return {k: (statistics.median(x["la"] for x in v),
                    statistics.median(x["ln"] for x in v))
                for k, v in by.items()}

    # Two passes. The first middle is computed from everything, which a
    # handful of wild pins can drag; the rows more than SETTLE_KM from it are
    # certainly wrong wherever the middle really is, so dropping them and
    # recomputing gives a middle worth measuring against.
    mid = middles(inside)
    settled = [r for r in inside
               if not r["d"] or (r["p"], r["d"]) not in mid
               or km(*mid[(r["p"], r["d"])], r["la"], r["ln"]) <= SETTLE_KM]
    mid = middles(settled)

    for r in inside:
        if not claimed(r):
            # No amphoe on the row and none in its name means there was
            # nothing to compare it against. That is not a bad pin and it is
            # not a good one, so it says so rather than passing silently.
            r["doubt"] = "unchecked"
            counts["unchecked"] += 1
            continue
        own = mid.get((r["p"], claimed(r)))
        if own is None:
            r["doubt"] = "unchecked"
            counts["unchecked"] += 1
            continue
        d_own = km(own[0], own[1], r["la"], r["ln"])
        d_best = min(km(c[0], c[1], r["la"], r["ln"]) for c in mid.values())
        if d_own > FAR_KM and d_own > FAR_RATIO * max(d_best, 0.3):
            r["doubt"] = "far"
            counts["far"] += 1
    return counts


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f else None


def main():
    fresh = OUT.exists() and "--refetch" not in sys.argv
    if fresh:
        age = (time.time() - OUT.stat().st_mtime) / 86400
        if age < STALE_DAYS:
            print(f"cleanrooms.json is {age:.0f} days old — keeping it "
                  f"(--refetch to force)")
            return 0

    SNAP.mkdir(parents=True, exist_ok=True)
    raw, failed = {}, []
    for key, pid, th in PROVINCES:
        try:
            rows = get(f"{API}/province/{pid}")
            (SNAP / f"{key}.json").write_text(
                json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            raw[key] = rows
            print(f"  {th}: {len(rows):,} rows")
        except Exception as e:                       # noqa: BLE001
            failed.append(f"{th}: {e}")
            snap = SNAP / f"{key}.json"
            if snap.exists():
                raw[key] = json.loads(snap.read_text(encoding="utf-8"))
                print(f"  {th}: unreachable — keeping the snapshot on disk")
            else:
                print(f"  {th}: unreachable and no snapshot — skipped")
        time.sleep(1.0)

    if not raw:
        print("nothing fetched and nothing on disk — data/cleanrooms.json "
              "left exactly as it was")
        return 1

    types, rooms, dropped, private = [], [], 0, 0
    for key, _pid, _th in PROVINCES:
        for r in raw.get(key, []):
            if not r.get("PublicAccess"):
                private += 1
                continue
            la, ln = num(r.get("Latitude")), num(r.get("Longitude"))
            if la is None or ln is None:
                dropped += 1
                continue
            t = (r.get("Type") or "").strip() or "—"
            if t not in types:
                types.append(t)
            grade = "evaluator" if (r.get("AssessedByEvaluatorResult") or "").strip() \
                else "self"
            cap = r.get("Capacity")
            try:
                cap = int(cap)
            except (TypeError, ValueError):
                cap = 0
            rooms.append({
                "p": key,
                "n": (r.get("LocationName") or "").strip(),
                "la": round(la, 5),
                "ln": round(ln, 5),
                "t": (r.get("Phone") or "").strip(),
                "d": (r.get("District") or "").strip(),
                "s": (r.get("Subdistrict") or "").strip(),
                "k": types.index(t),
                "g": grade,
                # The register's own verdict, kept in its own words. Anything
                # that is not ผ่าน is NOT translated into a fail here — the
                # register may simply not have finished with it.
                "e": (r.get("EvaluationResult") or "").strip(),
                "w": (r.get("SelfAssessment") or "")[:10],
                "x": (r.get("AssessedByEvaluatorExpire") or "") or "",
                "c": cap,
            })

    shared = flag_shared_phones(rooms)
    doubts = flag_pins(rooms)
    rooms.sort(key=lambda r: (r["p"], r["d"], r["n"]))
    doc = {
        "generated": datetime.date.today().isoformat(),
        "source": SOURCE,
        "also": ALSO,
        "rule": "PublicAccess only; a row with no pin is dropped and counted; "
                "a row whose pin cannot be where the row says is KEPT, marked "
                "`doubt`, and left out of the nearest-thing search. The grade "
                "and the assessment date ride on every row.",
        "pin_check": {
            "bbox": list(BBOX),
            "far_km": FAR_KM,
            "far_ratio": FAR_RATIO,
            "how": "outside = not inside either province; far = more than "
                   "far_km from the middle of the rows sharing its amphoe AND "
                   "at least far_ratio times as far from that middle as from "
                   "the nearest other amphoe's; unchecked = the row names no "
                   "amphoe to compare against. Flagged rows keep their place "
                   "in this file and are left out of the nearest-thing list.",
        },
        "doubts": doubts,
        "shared_phones_removed": shared,
        "phone_check": {
            "share_sites": SHARE_SITES, "share_km": SHARE_KM,
            "how": "a number entered at more than share_sites places that are "
                   "share_km or more apart is a bulk-entry default; it moves "
                   "from `t` to `tDefault` and is not offered as that place's "
                   "own number",
        },
        "types": types,
        "dropped_no_pin": dropped,
        "private_not_listed": private,
        "rooms": rooms,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev = json.loads(META.read_text()) if META.exists() else {}
    META.write_text(json.dumps({
        "file": "cleanrooms.json",
        "checked_at": now,
        "fetched_at": now,
        "last_success_at": now if not failed else prev.get("last_success_at"),
        "consecutive_failures": 0 if not failed
        else int(prev.get("consecutive_failures") or 0) + 1,
        "row_count": len(rooms),
        "content_hash": "sha256:" + hashlib.sha256(
            json.dumps(rooms, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "sources_ok": [SOURCE["api"]] if not failed else [],
        "sources_failed": failed,
        "source_published_at": None,
        "last_error": failed[0] if failed else None,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = len(rooms) - sum(doubts.values())
    print(f"{shared:,} rows lost a bulk-entry phone that belonged to nobody")
    print(f"{len(rooms):,} public rooms with a pin, {ok:,} of them placeable "
          f"({doubts['outside']} outside the provinces, {doubts['far']} in the "
          f"wrong amphoe, {doubts['unchecked']} with no amphoe to check) · "
          f"{dropped} with no pin dropped · {private:,} private rows not "
          f"listed · {len(types)} types -> data/cleanrooms.json")
    return 1 if failed and not rooms else 0


if __name__ == "__main__":
    sys.exit(main())
