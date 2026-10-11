#!/usr/bin/env python3
"""Who shares what on motdang.net, and who comes back, weekly.

Nan, 2026-10-03: "Sharing should be encouraged and include lots of ways for me
to measure." The rows come from the site Worker (publish/sharesense.js): the
Send sheet's events from POST /api/share (share_layer.py), and a "land" row for
every request that came in on a shared link (?s=<code>.<channel>), all in
traffic_eye, read with the fleet token.

    python3 share_learn.py            # last 7 days
    python3 share_learn.py --days 28

Writes ~/Desktop/1 — NEXT UP/SHARE — who shares what, and who comes back.txt (go/share-learn).
Launchd com.nanobotco.share-learn, Mondays 07:40.
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
OUT = Path.home() / "Desktop" / "1 — NEXT UP" / "SHARE — who shares what, and who comes back.txt"
EV = "SUM(_sample_interval * double5) AS n"
WHO = "if(blob2 = 'human', 'people', 'machines')"
CH = {"n": "phone share sheet", "l": "LINE", "w": "WhatsApp", "m": "email", "c": "copied link",
      "f": "Facebook", "g": "Messenger", "t": "Telegram", "x": "X", "p": "picture", "q": "QR", "r": "result row"}


def rows(where: str, cols: str, group: str, order="n DESC", limit=20):
    return sql(f"SELECT {cols}, {EV} FROM traffic_eye WHERE blob1 = '{HOST}' AND blob4 = '/api/share' "
               f"AND {where} GROUP BY {group} ORDER BY {order} LIMIT {limit}")


def num(r) -> int:
    return int(float(r.get("n") or 0))


def name(key: str) -> str:
    """cm:slug → the place's name; ev:slug → the event's title."""
    kind, _, slug = key.partition(":")
    try:
        if kind == "ev":
            evs = json.loads((ROOT / "docs" / "front" / "events.json").read_text()).get("events", [])
            hit = next((e for e in evs if e.get("k") == slug), None)
            return (hit or {}).get("t") or slug
        d = json.loads((ROOT / "docs" / kind / "p" / f"{slug}.json").read_text())
        return " · ".join(x for x in (d.get("nameTh"), d.get("nameEn")) if x) or d.get("name") or slug
    except Exception:
        return slug


def link(key: str) -> str:
    kind, _, slug = key.partition(":")
    return f"https://motdang.net/#ev={slug}" if kind == "ev" else f"https://motdang.net/{kind}/p/{slug}.html"


def table(L, title, data, order, label=lambda k: k, width=30):
    L.append(f"{title:<{width + 2}}people   machines")
    keys = [k for k in order if k in data] + sorted(k for k in data if k not in order)
    if not keys:
        L.append("  none yet")
    for k in keys:
        L.append(f"  {label(k):<{width}}{data[k].get('people', 0):>6}  {data[k].get('machines', 0):>9}")
    L.append("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    since = f"timestamp > NOW() - INTERVAL '{a.days}' DAY"
    today = dt.date.today().isoformat()
    L = [f"SHARE — who shares what, and who comes back · {today} · last {a.days} days", ""]

    def split(event, col):
        out = {}
        for r in rows(f"{since} AND blob9 = '{event}'", f"{col} k, {WHO} w", "k, w", limit=60):
            out.setdefault(r["k"] or "(none)", {})[r["w"]] = num(r)
        return out

    tally = {}
    for r in rows(since, f"blob9 e, {WHO} w", "e, w", "e", 60):
        tally.setdefault(r["e"], {})[r["w"]] = num(r)
    table(L, "THE SEND SHEET", tally, ["sheet", "option", "channel", "native-done", "native-cancel", "native-fail",
                                       "picture", "picture-saved", "calendar", "nudge", "nudge-tap", "nudge-shut",
                                       "welcome", "arrive", "land"])
    table(L, "OPENED FROM", split("sheet", "blob11"), ["button", "nudge", "card"])
    table(L, "WHAT THEY CHOSE", split("option", "blob11"), ["page", "picture", "event", "part", "row", "now", "live"])
    table(L, "HOW IT LEFT", split("channel", "blob11"), ["native", "line", "whatsapp", "facebook", "messenger",
                                                         "telegram", "mail", "copy"])
    table(L, "PICTURES MADE", split("picture", "blob11"), ["place", "event", "map", "doodle", "page"])
    table(L, "PICTURES SAVED", split("picture-saved", "blob11"), ["place", "event", "map", "doodle", "page"])
    table(L, "ADDED TO A CALENDAR", split("calendar", "blob11"), ["ics", "google"])
    shown, tapped = split("nudge", "blob11"), split("nudge-tap", "blob11")
    L.append("PROMPTS, by people              shown   tapped")
    if not shown:
        L.append("  none yet")
    for k in ("saved", "directions", "event", "doodle"):
        if k in shown:
            L.append(f"  {k:<30}{shown[k].get('people', 0):>6}  {tapped.get(k, {}).get('people', 0):>7}")
    L.append("")

    # who came back: arrivals where the page's script ran (people), and every request on a shared link
    arr = split("arrive", "blob11")
    land = {}
    for r in rows(f"{since} AND blob9 = 'land'", f"blob11 k, {WHO} w", "k, w", limit=60):
        land.setdefault(CH.get(r["k"], r["k"] or "(none)"), {})[r["w"]] = num(r)
    table(L, "CAME BACK, page open (arrive)", arr, ["line", "whatsapp", "native", "facebook", "messenger", "copy", "mail"])
    table(L, "LINKS OPENED (land), any opener", land, list(CH.values()))
    L.append("LINK PREVIEWS FETCHED BY APPS (machines on shared links)")
    prev = rows(f"{since} AND blob9 = 'land' AND blob2 != 'human'", "blob3 a", "a", limit=12)
    if not prev:
        L.append("  none yet")
    for r in prev:
        L.append(f"  {num(r):>5}  {r['a']}")
    L.append("")

    # per code: shared how, came back how often
    out = {}
    for r in rows(f"{since} AND blob9 = 'channel' AND blob10 != '' AND blob2 = 'human'",
                  "blob10 s, blob11 c, blob13 p, blob14 k", "s, c, p, k", limit=2000):
        o = out.setdefault(r["s"], {"ch": set(), "p": "", "k": ""})
        o["ch"].add(r["c"])
        o["p"] = o["p"] or r["p"]
        o["k"] = o["k"] or r["k"]
    back = {}
    for r in rows(f"{since} AND blob9 = 'arrive' AND blob10 != '' AND blob2 = 'human'", "blob10 s", "s", limit=2000):
        back[r["s"]] = num(r)
    shared = len(out)
    hit = [s for s in out if back.get(s)]
    L.append("SHARES THAT BROUGHT SOMEONE")
    L.append(f"  {shared} shares sent by people; {len(hit)} brought at least one person back; "
             f"{sum(back.get(s, 0) for s in out)} people came back on them"
             + (f" ({sum(back.get(s, 0) for s in out) / shared:.2f} a share)." if shared else "."))
    second = [s for s in out if out[s]["p"]]
    L.append(f"  {len(second)} of those shares came from someone who had arrived on a shared link "
             f"(a share of a share); {sum(back.get(s, 0) for s in second)} people came back on them.")
    if back and not out:
        L.append(f"  {sum(back.values())} people came back on links shared before this window.")
    top = sorted(hit, key=lambda s: -back[s])[:12]
    for s in top:
        o = out[s]
        what = f"{name(o['k'])}  {link(o['k'])}" if o["k"] else "a page"
        L.append(f"  {back[s]:>4} back · {s} · {', '.join(sorted(o['ch']))} · {what}")
    L.append("")

    L.append("WHAT PEOPLE SEND")
    things = rows(f"{since} AND blob9 IN ('channel','option') AND blob14 != '' AND blob2 = 'human'", "blob14 k", "k", limit=15)
    if not things:
        L.append("  none yet")
    for r in things:
        L.append(f"  {num(r):>5}  {name(r['k'])}  {link(r['k'])}")
    L.append("")

    L.append("PAGES WHERE THE SHEET OPENS, by people")
    pages = rows(f"{since} AND blob9 = 'sheet' AND blob2 = 'human'", "blob12 p", "p", limit=15)
    if not pages:
        L.append("  none yet")
    for r in pages:
        L.append(f"  {num(r):>5}  https://motdang.net{r['p']}")

    OUT.write_text("\n".join(L) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
