#!/usr/bin/env python3
"""/full-moon (fullmoon_layer.py), its data, and the net it stamps.

What this holds:
  · every full moon is a published date, a lunar month apart, and the big ones sit
    on the same days as data/festival_calendar.json (hand-checked against Thai
    calendars) — the two files cannot drift apart silently
  · every line about a wat names a source with a date or a year
  · every wat with a record id resolves to a page
  · the pages render, link only to full moons that exist, and draw no emoji
  · stamping twice leaves one copy of the net, not two

    python3 tests/test_full_moon.py
"""
import datetime
import json
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import fullmoon_layer as F  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAIL.append(name)


d, fest, paths = F.load()
moons = d["moons"]
dates = [m["date"] for m in moons]

# ---- the dates
check("25 full moons, 2026–2027", len(moons) == 25, str(len(moons)))
check("in order", dates == sorted(dates))
gaps = [(datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days
        for a, b in zip(dates, dates[1:])]
check("a lunar month apart", all(29 <= g <= 31 for g in gaps), str(gaps))
check("every observance is defined", all(k in d["observances"] for m in moons for k in m["obs"]))

cal = json.loads((ROOT / "data" / "festival_calendar.json").read_text())["rows"]
OBS_OF = {"makha-bucha": "makha", "visakha-bucha": "visakha", "asalha-bucha": "asanha",
          "ok-phansa": "ok_phansa", "yi-peng-loi-krathong": "yi_peng"}
by_date = {m["date"]: m for m in moons}
for r in cal:
    k = OBS_OF.get(r["festival_id"])
    if k and r["date_start"][:4] in ("2026", "2027"):
        m = by_date.get(r["date_start"])
        check(f'{r["festival_id"]} {r["date_start"]} is a full moon carrying {k}',
              bool(m) and k in m["obs"], "not in the table" if not m else str(m["obs"]))
check("26 Sep 2026 is Twelve Peng", "salak" in by_date["2026-09-26"]["obs"])

# ---- the wats
for w in d["wats"]:
    for h in w["holds"]:
        ok = (h["obs"] in d["observances"] and h["conf"] in F.CONF
              and re.match(r"https?://", h["src"]["url"]) and h["src"]["label"]
              and (h["when"] == "monthly" or h["conf"] == "disputed" or re.match(r"\d{4}-\d\d-\d\d$", h["when"])))
        check(f'{w["en"]}: {h["obs"]} is sourced and dated', bool(ok))
    if w["id"]:
        check(f'{w["en"]} resolves to a page', w["id"] in paths)
check("ids are unique", len({w["id"] for w in d["wats"] if w["id"]}) == len([w for w in d["wats"] if w["id"]]))

# ---- the pages
today = datetime.date(2026, 9, 27)
pages = [F.page_index(d, fest, paths, ROOT / "docs", today), F.page_wats(d, fest, paths, ROOT / "docs", today),
         F.page_how(d)] + [F.page_moon(i, d, fest, paths, ROOT / "docs", today) for i in range(len(moons))]
check("every page renders", all(len(p) > 20_000 for p in pages))
links = {x for p in pages for x in re.findall(r'https://motdang\.net/full-moon/(\d{4}-\d\d-\d\d)/', p)}
check("every dated link is a full moon", links <= set(dates), str(sorted(links - set(dates))))
emoji = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
check("no emoji on any page", not any(emoji.search(re.sub(r"<(style|script)\b.*?</\1>", "", p, flags=re.S))
                                      for p in pages))
for p in pages[:1]:
    for name in sorted(set(re.findall(r'<use href="#([a-z0-9-]+)"', p))):
        check(f"{name} is in the page's sprite", f'id="{name}"' in p[:p.find("</defs>")])
check("the index tells tonight from the table", 'id="fm-data"' in pages[0])
check("no third-party fetch", "fetch(" not in "".join(pages))

# ---- the stamp is idempotent
src = ROOT / "docs"
if (src / "festivals" / "ok-phansa.html").exists():
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for rel in ["festivals/ok-phansa.html", "cm/wat/index.html"]:
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src / rel, t / rel)
        F.stamp(t, d, fest, paths)
        F.stamp(t, d, fest, paths)
        for rel in ["festivals/ok-phansa.html", "cm/wat/index.html"]:
            n = (t / rel).read_text().count(F.MARK[0])
            check(f"{rel} carries the net once", n == 1, str(n))

print()
print(f"{len(FAIL)} failed" if FAIL else "all green")
sys.exit(1 if FAIL else 0)
