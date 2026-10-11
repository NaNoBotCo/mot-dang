#!/usr/bin/env python3
"""แม่น้ำปิง — the gauges, from the Royal Irrigation Department's own hourly register.

WO-57 item 5. WHAT THIS REPLACES. The proposal for a flood layer was to read
each pin's ground height out of the SRTM tiles already cached here and put it
beside the river. That was refused on its own numbers: the terrain cache is
z12, about 38 m a cell, with five to ten metres of vertical error, and a page
built on it would have told somebody whether their house floods using a model
that cannot tell one soi from the next. What it would really have been is a
guess wearing a contour line.

WHAT IS TRUE INSTEAD. The Upper Northern Region Irrigation Hydrology Centre
publishes hourly stage and discharge for every gauge on the Ping and its
tributaries — and, on every single row, THE STATION'S OWN ALERT LEVEL. P.1 at
Nawarat Bridge reports level_limit 3.70 m. That number is not ours, not a
newspaper's and not inferred: it arrives in the same record as the reading.
So the page can say "1.37 of 3.70 metres, and the limit is the RID's" and
never has to model anything.

THE LEAD TIME IS MEASURED, NOT LOOKED UP. Everybody in Chiang Mai repeats
that water takes six to eight hours from Mae Tae to Nawarat. This computes it
instead: the two hourly series are cross-correlated over the last LAG_DAYS
and the lag with the highest correlation is reported, with the correlation
beside it so a weak answer looks weak. In a dry month the series barely move
and the number means little — which is exactly why it is printed with its own
r and its own window rather than as a fact about the river.

NO FORECAST. This says what the gauges read, what each station's own limit
is, which way the last six hours went, and how long the water has historically
taken between two stations. It does not predict a crest and it does not tell
anybody to leave. That is ปภ.'s job and the page says so.

    python3 importers/make_ping.py            # keeps a fresh reading
    python3 importers/make_ping.py --refetch  # force
"""
import datetime
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ping.json"
META = ROOT / "data" / "ping.meta.json"
STALE_MIN = 45
LAG_DAYS = 30
DAYS = 7                      # hourly series kept for the page

API = "https://hydro1.ddns.net/main/information_6/water_today_search_json.php"
UA = "Mozilla/5.0 (mot-dang reader; +https://motdang.net)"
SOURCE = {
    "name": "ศูนย์อุทกวิทยาชลประทานภาคเหนือตอนบน กรมชลประทาน",
    "en": "Upper Northern Region Irrigation Hydrology Centre, "
          "Royal Irrigation Department",
    "url": "https://www.hydro-1.net/",
    "api": API,
    "note_th": "ระดับเตือนภัยของแต่ละสถานีมาจากข้อมูลของสถานีเอง ไม่ใช่ตัวเลขที่มดแดงตั้ง",  # stylecheck: allow — the official term for a station's alert level
    "note_en": "Each station's alert level comes with its own readings — it is "
               "not a number Mot Dang chose.",
}

# Down the Ping, in the order the water passes. `chain` marks the mainstem, so
# the page can draw the river as a line and the tributaries as what joins it.
STATIONS = [
    ("P.20",  True,  "บ้านเชียงดาว", "Ban Chiang Dao"),
    ("P.75",  True,  "บ้านช่อแล", "Ban Cho Lae"),
    ("P.67",  True,  "บ้านแม่แต", "Ban Mae Tae"),
    ("P.1",   True,  "สะพานนวรัฐ", "Nawarat Bridge"),
    ("P.103", True,  "บ้านป่าข่อยใต้", "Ban Pa Khoi Tai"),
    ("P.4A",  False, "บ้านแม่แตง", "Ban Mae Taeng"),
    ("P.21",  False, "บ้านเหมืองผ่า", "Ban Muang Pha"),
    ("P.71A", False, "บ้านกลาง", "Ban Klang"),
    ("P.82",  False, "บ้านสบวิน", "Ban Sop Win"),
    ("P.81",  False, "บ้านโป่ง", "Ban Pong"),
]
CITY = "P.1"
UPSTREAM = "P.67"             # the pair whose lag the page reports

TH_MONTH = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
            "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม",
            "พฤศจิกายน", "ธันวาคม"]


def get(station, start, end):
    q = urllib.parse.urlencode({"station01": station,
                                "datestart": start.isoformat(),
                                "dateend": end.isoformat()})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8-sig"))


def stamp(row):
    """The register writes Thai dates — 'วันที่ 1 กันยายน 2569', '01.00 น.'.

    Parsed into an ISO hour so two stations can be lined up against each
    other. A row whose date will not parse is dropped rather than guessed."""
    m = re.search(r"(\d+)\s+(\S+)\s+(\d{4})", row.get("date") or "")
    h = re.match(r"(\d+)", (row.get("time") or "").strip())
    if not m or not h:
        return None
    day, month_th, be = int(m.group(1)), m.group(2), int(m.group(3))
    if month_th not in TH_MONTH:
        return None
    try:
        d = datetime.date(be - 543, TH_MONTH.index(month_th), day)
    except ValueError:
        return None
    return f"{d.isoformat()}T{int(h.group(1)) % 24:02d}:00"


def num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def series(rows):
    out = {}
    for r in rows:
        t, lv = stamp(r), num(r.get("level"))
        if t and lv is not None:
            out[t] = {"level": lv, "dischg": num(r.get("dischg"))}
    return out


def lag_hours(a, b, max_lag=24):
    """Hours by which series `b` follows series `a`, and how well it fits.

    Plain Pearson correlation of the overlapping hours at each candidate lag;
    the best lag wins and its r is returned with it. Both are printed on the
    page, because in a dry month the levels barely move and the best r is
    near nothing — a lag with a weak r is a number, not a lead time."""
    ta = sorted(a)
    best = (None, 0.0, 0)
    for lag in range(0, max_lag + 1):
        xs, ys = [], []
        for t in ta:
            dt = datetime.datetime.fromisoformat(t) + datetime.timedelta(hours=lag)
            k = dt.strftime("%Y-%m-%dT%H:00")
            if k in b:
                xs.append(a[t]["level"])
                ys.append(b[k]["level"])
        n = len(xs)
        if n < 48:
            continue
        mx, my = sum(xs) / n, sum(ys) / n
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        if sxx <= 0 or syy <= 0:
            continue
        r = sxy / (sxx * syy) ** 0.5
        if r > best[1]:
            best = (lag, r, n)
    return {"hours": best[0], "r": round(best[1], 3), "hours_compared": best[2],
            "window_days": LAG_DAYS}


def main():
    if OUT.exists() and "--refetch" not in sys.argv:
        age = (time.time() - OUT.stat().st_mtime) / 60
        if age < STALE_MIN:
            print(f"ping.json is {age:.0f} min old — keeping it "
                  f"(--refetch to force)")
            return 0

    today = datetime.date.today()
    start = today - datetime.timedelta(days=LAG_DAYS)
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    prev_st = {s["id"]: s for s in prev.get("stations", [])}

    out, failed, full = [], [], {}
    for sid, chain, th, en in STATIONS:
        try:
            rows = get(sid, start, today)
        except Exception as e:                      # noqa: BLE001
            failed.append(f"{sid}: {e}")
            if sid in prev_st:
                out.append(prev_st[sid])
            continue
        ser = series(rows)
        full[sid] = ser
        if not ser:
            failed.append(f"{sid}: no readings parsed")
            if sid in prev_st:
                out.append(prev_st[sid])
            continue
        last = max(ser)
        meta = rows[-1]
        keep = sorted(ser)[-DAYS * 24:]
        # Which way, and by how much — the arithmetic, never an adjective.
        six = (datetime.datetime.fromisoformat(last)
               - datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:00")
        then = ser.get(six, {}).get("level")
        out.append({
            "id": sid,
            "chain": chain,
            "th": th, "en": en,
            "river_th": (meta.get("water_name") or "").strip(),
            "amphoe": (meta.get("address2") or "").strip(),
            "province": (meta.get("address3") or "").strip(),
            "limit": num(meta.get("level_limit")),
            "dischg_limit": num(meta.get("dischg_limit")),
            "level": ser[last]["level"],
            "dischg": ser[last]["dischg"],
            "observed": last,
            "change6h": (None if then is None
                         else round(ser[last]["level"] - then, 2)),
            "hours": [[t, ser[t]["level"]] for t in keep],
        })
        time.sleep(0.8)

    if not out:
        print("nothing fetched and nothing on disk — data/ping.json untouched")
        return 1

    lag = (lag_hours(full[UPSTREAM], full[CITY])
           if UPSTREAM in full and CITY in full else None)

    doc = {
        "generated": datetime.datetime.now().astimezone().replace(
            microsecond=0).isoformat(),
        "source": SOURCE,
        "city_station": CITY,
        "lag": ({"from": UPSTREAM, "to": CITY, **lag} if lag else None),
        "rule": "Each station's alert level is the register's own level_limit. "
                "Nothing here is a forecast.",
        "stations": out,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pm = json.loads(META.read_text()) if META.exists() else {}
    META.write_text(json.dumps({
        "file": "ping.json", "checked_at": now, "fetched_at": now,
        "last_success_at": now if not failed else pm.get("last_success_at"),
        "consecutive_failures": 0 if not failed
        else int(pm.get("consecutive_failures") or 0) + 1,
        "row_count": len(out),
        "content_hash": "sha256:" + hashlib.sha256(
            json.dumps(out, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "sources_ok": [API] if not failed else [],
        "sources_failed": failed, "source_published_at": None,
        "last_error": failed[0] if failed else None,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    city = next((s for s in out if s["id"] == CITY), None)
    if city:
        print(f"P.1 {city['th']}: {city['level']:.2f} m of "
              f"{city['limit']:.2f} m stated limit "
              f"({100 * city['level'] / city['limit']:.0f}%), "
              f"{city['change6h']:+.2f} m in 6 h, at {city['observed']}")
    if lag and lag["hours"] is not None:
        print(f"{UPSTREAM} → {CITY}: best lag {lag['hours']} h "
              f"(r={lag['r']}, {lag['hours_compared']} hours compared over "
              f"{LAG_DAYS} days)")
    print(f"{len(out)} stations -> data/ping.json"
          + (f"  ({len(failed)} failed: {failed[0]})" if failed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
