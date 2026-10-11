#!/usr/bin/env python3
"""Where people and bots look on the maps, weekly.

Nan, 2026-09-29: "CAN MOtdang learn from how humans and bots interact with
maps?" — "everything". The rows come from the site Worker (publish/worker.js):
map events from /api/map (mapsense_layer.py) and the map searches on
/api/v1/search, both in traffic_eye, read with the fleet token.

    python3 map_learn.py            # last 7 days
    python3 map_learn.py --days 28

Writes
  ~/Desktop/1 — NEXT UP/MAP — where people and bots look.txt   the report (go/map-learn)
  _incoming/map-misses-<date>.json                              map searches that found nothing
Launchd com.nanobotco.map-learn, Mondays 07:30.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from traffic import sql  # noqa: E402

HOST = "motdang.net"
OUT = Path.home() / "Desktop" / "1 — NEXT UP" / "MAP — where people and bots look.txt"
MISSES = ROOT / "_incoming"
EV = "SUM(_sample_interval * double5) AS n"
WHO = "if(blob2 = 'human', 'people', 'machines')"


def rows(where: str, cols: str, group: str, order="n DESC", limit=15):
    return sql(f"SELECT {cols}, {EV} FROM traffic_eye WHERE blob1 = '{HOST}' AND {where} "
               f"GROUP BY {group} ORDER BY {order} LIMIT {limit}")


def num(r) -> int:
    return int(float(r.get("n") or 0))


def maplink(cell: str, z: int = 15) -> str:
    lat, lng = cell.split(",")
    return f"https://motdang.net/map.html#{z}/{lat}/{lng}"


def placename(key: str) -> str:
    prov, slug = key.split(":", 1)
    try:
        d = json.loads((ROOT / "docs" / prov / "p" / f"{slug}.json").read_text())
        return " · ".join(x for x in (d.get("nameTh"), d.get("nameEn")) if x) or d.get("name") or slug
    except Exception:
        return slug


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    since = f"timestamp > NOW() - INTERVAL '{a.days}' DAY"
    ev = f"{since} AND blob4 = '/api/map' AND blob11 NOT LIKE 'ab:%'"   # the front page A/B: ab_home.py
    se = f"{since} AND blob4 = '/api/v1/search' AND blob9 = 'search'"
    today = dt.date.today().isoformat()
    L = [f"MAP — where people and bots look · {today} · last {a.days} days", ""]

    tally = rows(ev, f"blob9 e, {WHO} w", "e, w", "e", 40)
    t = {}
    for r in tally:
        t.setdefault(r["e"], {})[r["w"]] = num(r)
    L.append("WHAT HAPPENED ON THE MAPS        people   machines")
    for e in ("view", "open", "near", "pin", "share", "unsave", "code", "coord"):
        p, m = t.get(e, {}).get("people", 0), t.get(e, {}).get("machines", 0)
        L.append(f"  {e:<30}{p:>7}  {m:>9}")
    sp = rows(se, f"{WHO} w", "w", "w", 5)
    for r in sp:
        L.append(f"  {'map + API searches, ' + r['w']:<30}{num(r):>7}")
    L.append("")

    views = {}
    for who in ("people", "machines"):
        v = rows(f"{ev} AND blob9 = 'view' AND blob10 != '' AND {WHO} = '{who}'", "blob10 c", "c")
        s = rows(f"{se} AND blob10 != '' AND {WHO} = '{who}'", "blob10 c", "c")
        both = {}
        for r in v + s:
            both[r["c"]] = both.get(r["c"], 0) + num(r)
        views[who] = both
        L.append(f"WHERE {who.upper()} LOOK (views they stopped on + areas they searched), ~1 km cells")
        if not both:
            L.append("  none yet")
        for c, n in sorted(both.items(), key=lambda kv: -kv[1])[:12]:
            L.append(f"  {n:>5}  {maplink(c)}")
        L.append("")

    only_p = [c for c in sorted(views["people"], key=lambda c: -views["people"][c])[:20] if c not in views["machines"]]
    only_m = [c for c in sorted(views["machines"], key=lambda c: -views["machines"][c])[:20] if c not in views["people"]]
    L.append("WHERE THEY DIFFER")
    L.append("  people look, machines do not:")
    L += [f"    {maplink(c)}" for c in only_p[:8]] or ["    none yet"]
    L.append("  machines look, people do not:")
    L += [f"    {maplink(c)}" for c in only_m[:8]] or ["    none yet"]
    L.append("")

    L.append("PLACES OPENED ON A MAP, by people")
    op = rows(f"{ev} AND blob9 IN ('open','near') AND blob11 LIKE '__:%' AND blob11 NOT LIKE 'ev:%' AND blob2 = 'human'", "blob11 k", "k")
    if not op:
        L.append("  none yet")
    for r in op:
        prov, slug = r["k"].split(":", 1)
        L.append(f"  {num(r):>5}  {placename(r['k'])}  https://motdang.net/{prov}/p/{slug}.html")
    L.append("")

    L.append("MAP SEARCHES THAT FOUND NOTHING")
    miss = rows(f"{se} AND blob11 != ''", f"blob11 q, {WHO} w", "q, w", limit=40)
    if not miss:
        L.append("  none yet")
    for r in miss:
        L.append(f"  {num(r):>5}  {r['w']:<9} {r['q']}")
    L.append("")

    L.append("PASTED INTO THE MAP BOX, by people")
    pasted = rows(f"{ev} AND blob9 IN ('coord','code') AND blob2 = 'human'", "blob9 e, blob11 d", "e, d", limit=20)
    if not pasted:
        L.append("  none yet")
    for r in pasted:
        L.append(f"  {num(r):>5}  {r['e']}: {r['d']}")

    OUT.write_text("\n".join(L) + "\n")
    MISSES.mkdir(exist_ok=True)
    (MISSES / f"map-misses-{today}.json").write_text(json.dumps(
        [{"q": r["q"], "who": r["w"], "n": num(r)} for r in miss], ensure_ascii=False, indent=1))
    print(OUT)


if __name__ == "__main__":
    main()
