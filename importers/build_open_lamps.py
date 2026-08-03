#!/usr/bin/env python3
"""เมืองหลับนิดหน่อย — bake opening hours into lamp schedules.

Reads data/canonical/{cm,cr}.json, parses every `hours` string it can stand
behind into minute-of-week intervals, and writes data/open_lamps.json for
nitnoy_layer.py (the map page) to draw from.

Presence is the only claim, extended to time: a place whose hours we do not
hold is simply ABSENT from this file — the page renders it as nothing, never
as closed. A string the parser cannot read is counted and sampled in
`parse.excluded`, not guessed at.

Also baked here, because they fall straight out of the same bitmaps:
  - meals: open-fraction curves by food subcategory + which meal windows a
    subcategory serves (breakfast/lunch/dinner/late) — an inference from
    opening hours, and labelled that way wherever it renders.
  - markets: the market records whose hours we hold, classified by when
    their open window sits (morning kad / daytime / evening / night).

Deterministic: same canonical data in, byte-same JSON out (the `generated`
stamp is the newest updatedAt among the records used, not the wall clock).

    python3 importers/build_open_lamps.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "open_lamps.json"

WEEK = 7 * 1440
DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
DAY_IDX = {d: i for i, d in enumerate(DAYS)}

# Full/abbreviated English day names → OSM two-letter, longest first so
# "Sunday" never half-matches as "Sun".
_DAY_WORDS = [
    ("monday", "Mo"), ("tuesday", "Tu"), ("wednesday", "We"),
    ("thursday", "Th"), ("friday", "Fr"), ("saturday", "Sa"), ("sunday", "Su"),
    ("mon", "Mo"), ("tue", "Tu"), ("wed", "We"), ("thu", "Th"),
    ("fri", "Fr"), ("sat", "Sa"), ("sun", "Su"),
]

_MONTHS = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", re.I)
_DAYSPEC = re.compile(
    r"(?:Mo|Tu|We|Th|Fr|Sa|Su|PH)(?:\s*[-,]\s*(?:Mo|Tu|We|Th|Fr|Sa|Su|PH))*")
_SPAN = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")
_OFF = re.compile(r"\b(off|closed)\b", re.I)


def _normalize(s):
    s = s.replace(" ", " ").replace(" ", " ")
    s = re.sub(r'"[^"]*"', " ", s)          # drop free-text comments
    s = s.replace("\n", ";").replace("||", ";")
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = re.sub(r"\s*น\.?(?=\s|$|[;,-])", " ", s)   # Thai clock marker
    s = re.sub(r"\bdaily\b|\beveryday\b|\bevery day\b", "Mo-Su", s, flags=re.I)
    s = s.replace("～", "-").replace("〜", "-")
    s = re.sub(r"\bmidnight\b", "24:00", s, flags=re.I)
    s = re.sub(r"\bnoon\b", "12:00", s, flags=re.I)
    s = re.sub(r"(?<![\d:.])(\d{1,2})\s*(am|pm)\b", r"\1:00 \2", s,
               flags=re.I)
    for word, two in _DAY_WORDS:
        s = re.sub(r"\b" + word + r"\b", two, s, flags=re.I)
    # dotted clock (Thai habit): 9.00 → 9:00 — only between digit pairs, so
    # "24/7" and prose stay untouched
    s = re.sub(r"(\d{1,2})\.(\d{2})\b", r"\1:\2", s)

    def _ampm(m):
        h, mn, half = int(m.group(1)), m.group(2), m.group(3).upper()
        if half == "PM" and h != 12:
            h += 12
        if half == "AM" and h == 12:
            h = 0
        return "%02d:%s" % (h, mn)
    s = re.sub(r"(\d{1,2}):(\d{2})\s*(AM|PM)\b", _ampm, s, flags=re.I)
    return s


def _parse_days(spec):
    """Day spec → set of day indices; PH tokens are dropped (holiday rules
    are about dates, not weekdays — nothing here can honour them)."""
    days = set()
    for part in re.split(r"\s*,\s*", spec.strip()):
        part = part.strip()
        if not part or part == "PH":
            continue
        m = re.match(r"^(\w\w)\s*-\s*(\w\w)$", part)
        if m:
            a, b = DAY_IDX.get(m.group(1)), DAY_IDX.get(m.group(2))
            if a is None or b is None:
                return None
            i = a
            days.add(i)
            while i != b:
                i = (i + 1) % 7
                days.add(i)
        elif part in DAY_IDX:
            days.add(DAY_IDX[part])
        else:
            return None
    return days


def parse_hours(raw):
    """OSM opening_hours subset → sorted merged [start,end) minute-of-week
    intervals, or None when the string says something we cannot represent.
    Handled: 24/7 · day ranges/lists · multiple rules (';') · several spans
    per rule · overnight wrap · off/closed · dotted-Thai and 12h clocks.
    Refused (whole string): month/seasonal rules, week numbers, sunrise/
    sunset, anything the grammar does not recognise."""
    s = _normalize(raw)
    if _MONTHS.search(s) or re.search(r"\bweek\b|sunrise|sunset", s, re.I):
        return None
    if re.fullmatch(r"\s*24\s*/\s*7\s*", s):
        return [[0, WEEK]]

    intervals = []
    saw_rule = False
    for rule in s.split(";"):
        rule = rule.strip()
        if not rule:
            continue
        if re.fullmatch(r"\s*24\s*/\s*7\s*", rule):
            intervals.append([0, WEEK])
            saw_rule = True
            continue
        # a rule may pack several day-group segments with no separator
        # ("Mo-Fr 17:30-23:30 Sa-Su 09:00-23:45") — split keeping day specs
        parts = [p for p in _DAYSPEC.split(rule)]
        specs = _DAYSPEC.findall(rule)
        # parts = [before, after-spec-0, after-spec-1, ...]
        segments = []
        if parts and parts[0].strip():
            segments.append((None, parts[0]))
        for spec, tail in zip(specs, parts[1:]):
            segments.append((spec, tail))
        ok_rule = False
        for spec, tail in segments:
            days = _parse_days(spec) if spec is not None else set(range(7))
            if days is None:
                return None
            spans = _SPAN.findall(tail)
            leftover = _SPAN.sub("", tail)
            leftover = _OFF.sub("", leftover)
            if re.search(r"[0-9]", leftover):
                return None          # digits the grammar didn't consume
            if _OFF.search(tail):
                ok_rule = True       # "Su off": nothing to add, still valid
                if spans:
                    return None      # "off 10:00-12:00" — not representable
                continue
            if not spans:
                continue
            for h1, m1, h2, m2 in spans:
                a = int(h1) * 60 + int(m1)
                b = int(h2) * 60 + int(m2)
                if a >= 1440 or b > 1440 or (b == a):
                    return None
                for d in days:
                    base = d * 1440
                    if b > a:
                        intervals.append([base + a, base + b])
                    else:                      # overnight wrap
                        intervals.append([base + a, base + 1440])
                        if b > 0:              # "-00:00" ends AT midnight
                            nxt = ((d + 1) % 7) * 1440
                            intervals.append([nxt, nxt + b])
            ok_rule = True
        if ok_rule:
            saw_rule = True
    if not saw_rule or not intervals:
        return None
    intervals.sort()
    merged = [intervals[0][:]]
    for a, b in intervals[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    total = sum(b - a for a, b in merged)
    if total <= 0 or total > WEEK:
        return None
    return merged


# ---- lamp groups: what colour a place burns ------------------------------

def _group(r):
    cat = r["cat"][0] if r["cat"] else ""
    subs = r.get("sub") or []
    if cat == "market":
        return "market"
    if cat == "food":
        if "bar-pub" in subs:
            return "night"
        if "cafe" in subs:
            return "cafe"
        return "food"
    if cat in ("massage", "beauty"):
        return "care"
    if cat in ("essentials", "shopping"):
        return "shop"
    return "other"


# ---- meal windows (half-hour slots; an inference from opening hours) -----

SLOTS = 48
WINDOWS = {
    "breakfast": list(range(13, 20)),                 # 06:30–10:00
    "lunch": list(range(22, 28)),                     # 11:00–14:00
    "dinner": list(range(34, 42)),                    # 17:00–21:00
    "late": list(range(42, 48)) + [0, 1],             # 21:00–01:00
}
BAND_CUT = 0.7        # share of a curve's own peak that claims a window


def day_curve(sched):
    """Open-fraction per half-hour slot averaged over the seven days."""
    out = []
    for slot in range(SLOTS):
        n = 0
        for d in range(7):
            t = d * 1440 + slot * 30 + 15       # slot midpoint
            if any(a <= t < b for a, b in sched):
                n += 1
        out.append(n / 7.0)
    return out


def classify(curve):
    peak = max(curve)
    if peak <= 0:
        return [], {}
    scores = {w: round((sum(curve[i] for i in idx) / len(idx)) / peak, 2)
              for w, idx in WINDOWS.items()}
    bands = [w for w in ("breakfast", "lunch", "dinner", "late")
             if scores[w] >= BAND_CUT]
    if len(bands) == 4:
        bands = ["allday"]
    return bands, scores


def main():
    recs = []
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / (prov + ".json")
        if p.exists():
            recs.extend(json.loads(p.read_text()))
    with_hours = [r for r in recs if r.get("hours")
                  and r.get("lat") is not None]

    sched_ids = {}
    schedules = []
    places = []
    excluded = []
    latest = ""
    for r in sorted(with_hours, key=lambda r: r["id"]):
        sched = parse_hours(r["hours"])
        if sched is None:
            excluded.append(r["hours"])
            continue
        key = json.dumps(sched)
        if key not in sched_ids:
            sched_ids[key] = len(schedules)
            schedules.append(sched)
        latest = max(latest, r.get("updatedAt") or "")
        places.append({
            "id": r["id"],
            "n": r.get("nameTh") or r["name"],
            "la": round(r["lat"], 5),
            "ln": round(r["lng"], 5),
            "p": r["province"],
            "g": _group(r),
            "k": sched_ids[key],
        })

    # ---- meals: curves by food subcategory and by cuisine tag -------------
    by_sub = {}
    by_cui = {}
    for r in sorted(with_hours, key=lambda r: r["id"]):
        if "food" not in r["cat"]:
            continue
        sched = parse_hours(r["hours"])
        if sched is None:
            continue
        for sub in (r.get("sub") or ["(no sub)"])[:1]:
            by_sub.setdefault(sub, []).append(sched)
        cui = str(r["attrs"].get("cuisine") or "")
        for t in cui.split(";")[:1]:
            t = t.strip().lower()
            if t:
                by_cui.setdefault(t, []).append(sched)

    def _curves(groups, key_name, floor):
        out = []
        for key in sorted(groups):
            group = groups[key]
            if len(group) < floor:
                continue
            agg = [0.0] * SLOTS
            for sched in group:
                c = day_curve(sched)
                for i in range(SLOTS):
                    agg[i] += c[i]
            curve = [round(v / len(group), 3) for v in agg]
            bands, scores = classify(curve)
            out.append({key_name: key, "n": len(group), "curve": curve,
                        "bands": bands, "scores": scores})
        return out

    meals = _curves(by_sub, "sub", 15)
    cuisines = _curves(by_cui, "cuisine", 20)

    # ---- markets: rhythm classification -----------------------------------
    markets = []
    n_markets = 0
    for r in sorted(recs, key=lambda r: r["id"]):
        if "market" not in r["cat"]:
            continue
        n_markets += 1
        if not r.get("hours"):
            continue
        sched = parse_hours(r["hours"])
        if sched is None:
            continue
        opens = [t for a, b in sched for t in range(a, b, 30)]
        center = (sum(t % 1440 for t in opens) / len(opens)) / 60.0
        kind = ("morning" if center < 11 else
                "day" if center < 16 else
                "evening" if center < 21 else "night")
        markets.append({"id": r["id"],
                        "n": r.get("nameTh") or r["name"],
                        "k": len(schedules), "kind": kind,
                        "hours": r["hours"]})
        markets[-1]["k"] = sched_ids.get(json.dumps(sched))
        if markets[-1]["k"] is None:      # market outside lamp set (no coords)
            sched_ids[json.dumps(sched)] = len(schedules)
            schedules.append(sched)
            markets[-1]["k"] = sched_ids[json.dumps(sched)]

    out = {
        "generated": latest,
        "week_min": WEEK,
        "schedules": schedules,
        "places": places,
        "parse": {
            "records": len(recs),
            "with_hours": len(with_hours),
            "parsed": len(places),
            "excluded": len(excluded),
            "excluded_sample": sorted(set(excluded))[:8],
        },
        "meals": {
            "note": "inference from opening hours; a curve describes a "
                    "subcategory's habit, never a promise about one shop",
            "windows": {w: [min(i) * 30, (max(i) + 1) * 30]
                        for w, i in
                        {k: v for k, v in WINDOWS.items()
                         if k != "late"}.items()},
            "late_window": [1260, 1500],
            "band_cut": BAND_CUT,
            "subs": meals,
            "cuisines": cuisines,
        },
        "markets": {"total": n_markets, "with_hours": len(markets),
                    "list": markets},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False,
                              separators=(",", ":")) + "\n")
    print("open_lamps: %d places lit of %d with hours (%d strings unread), "
          "%d schedules, %d food subs curved, markets %d/%d"
          % (len(places), len(with_hours), len(excluded), len(schedules),
             len(meals), len(markets), n_markets))


if __name__ == "__main__":
    main()
