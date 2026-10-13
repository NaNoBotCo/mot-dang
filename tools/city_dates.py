#!/usr/bin/env python3
"""Dated days for the Pathum Thani and Phnom Penh calendars, into data/curated/event_extras.json "add".

Nan, 2026-10-13: Pathum Thani "a doodle map and calendar … fill in dates you're reasonably sure of",
then "Do the same thing for Phnom Penh". A row goes in only when a source names its day for this year:
Phnom Penh's public holidays from the sub-decree list Psar Phnom Penh carries (../phnom-penh/data/soon.json),
and the researched file in _incoming/ (pth / pp rows, each with the page that states its date). Rows this
tool wrote before (uid city-dates-…) are replaced, so a rerun after a new file is safe.

    python3 tools/city_dates.py _incoming/pt-pp-dates-2026-10-13.json --take loy-krathong-2026
    python3 tools/city_dates.py                     the Phnom Penh holidays alone

--take names the rows of the file to use (a national day such as Ok Phansa is already a festival on every
Thai calendar, and Phnom Penh's holidays are the sub-decree list already read); without it, all of them.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRAS = ROOT / "data" / "curated" / "event_extras.json"
PP_SOON = ROOT.parent / "phnom-penh" / "data" / "soon.json"
TAG = "city-dates-"


def row(city, rid, th, en, start, end, all_day, about, venue, src_url, src_name, tz):
    s = start if len(start) > 10 else start + " 00:00:00"
    if len(s) == 16:
        s += ":00"
    e = end and (end if len(end) > 10 else end + " 23:59:00")
    return {"uid": TAG + city + "-" + rid + "-" + start[:10], "start": s, "all_day": bool(all_day), "tz": tz, "end": e,
            "title": f"{th} · {en}" if th and en and th != en else (en or th), "description": " · ".join(x for x in (about, src_name) if x),
            "url": src_url, "source": "city-dates", "venue_name": venue or "", "venue_from": "title", "recurring": False,
            "weekday": None, "cost": None, "from_rule": False, "city": city}


def main():
    x = json.loads(EXTRAS.read_text())
    keep = [r for r in x.get("add", []) if not str(r.get("uid", "")).startswith(TAG)]
    new = []
    soon = json.loads(PP_SOON.read_text())
    for i in soon["items"]:
        rid = "".join(c if c.isalnum() else "-" for c in i["en"].lower()).strip("-")[:40]
        new.append(row("pp", rid, i.get("th"), i["en"], i["start"], i.get("end"), True, i.get("line_en", ""), "",
                       i.get("src", ""), "Sub-Decree 167 (2026 public holidays)", "Asia/Phnom_Penh"))
    args, take = sys.argv[1:], None
    if "--take" in args:
        i = args.index("--take"); take = set(args[i + 1].split(",")); args = args[:i] + args[i + 2:]
    for f in args:
        d = json.loads(Path(f).read_text())
        for city in ("pth", "pp"):
            for i in d.get(city, []):
                if not i.get("source_url") or not i.get("start") or (take and i["id"] not in take):
                    continue
                new.append(row(city, i["id"], i.get("title_th"), i.get("title_en"), i["start"], i.get("end"), i.get("all_day", True),
                               i.get("about_en", ""), i.get("venue_th") if city == "pth" else i.get("venue_en"),
                               i["source_url"], i.get("source_name", ""), "Asia/Phnom_Penh" if city == "pp" else "Asia/Bangkok"))
    seen, out = set(), []
    for r in new:
        if r["uid"] not in seen:
            seen.add(r["uid"]); out.append(r)
    x["add"] = keep + out
    EXTRAS.write_text(json.dumps(x, ensure_ascii=False, indent=1) + "\n")
    print(len(out), "rows:", {c: sum(1 for r in out if r["city"] == c) for c in ("pth", "pp")})


if __name__ == "__main__":
    main()
