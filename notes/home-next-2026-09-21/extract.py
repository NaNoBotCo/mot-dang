#!/usr/bin/env python3
"""Read-only pass over mot-dang's data. Writes one payload JSON to the scratchpad.
The tower is hot; this opens nothing for writing inside the repo."""
import json, pathlib, collections, urllib.parse as up

ROOT = pathlib.Path.home() / "Developer/claude code projects/mot-dang"
DATA = ROOT / "data"
OUT = pathlib.Path(__file__).resolve().parent


def j(p):
    return json.loads((DATA / p).read_text())


cats = {c["key"]: c for c in j("categories.json")["categories"]}
order = list(cats)

lh = j("linkhealth.json")
LINKS, PLACES = lh["links"], lh["places"]
# place id -> best status among its links
best = {}
for url, rows in PLACES.items():
    st = (LINKS.get(url) or {}).get("status")
    for r in rows:
        pid = r["id"]
        if st == "ok":
            best[pid] = "ok"
        elif st == "social" and best.get(pid) != "ok":
            best[pid] = "social"
        else:
            best.setdefault(pid, st or "?")

wl = j("wichaa_links.json")["links"]

shelf = collections.defaultdict(lambda: collections.Counter())
tot = {}
domains = collections.Counter()
for city in ("cm", "cr"):
    recs = j(f"canonical/{city}.json")
    tot[city] = len(recs)
    for r in recs:
        c = (r.get("cat") or [None])[0]
        if c not in cats:
            continue
        s = shelf[c]
        s[city] += 1
        if r.get("lat"):
            s["pin"] += 1
        if r.get("phone"):
            s["tel"] += 1
        if r.get("hours"):
            s["hrs"] += 1
        w = r.get("website")
        if w:
            s["web"] += 1
            st = best.get(r["id"])
            if st == "ok":
                s["live"] += 1
                domains[up.urlsplit(w).netloc.lower().removeprefix("www.")] += 1
            elif st == "social":
                s["social"] += 1
        if r["id"] in wl:
            s["wichaa"] += 1

out = {
    "totals": tot,
    "shelves": [
        {"key": k, "th": cats[k]["th"], "en": cats[k]["en"], **dict(shelf[k])}
        for k in order
    ],
    "linkhealth": {
        "generated": lh["generated"],
        "urls": len(LINKS),
        "ok": sum(1 for v in LINKS.values() if v.get("status") == "ok"),
        "social": sum(1 for v in LINKS.values() if v.get("status") == "social"),
        "domains": len({up.urlsplit(u).netloc.lower().removeprefix("www.") for u in LINKS}),
    },
    "top_domains": domains.most_common(40),
    "wichaa": len(wl),
}
(OUT / "payload.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("shelves", len(out["shelves"]), "totals", tot)
print("linkhealth", out["linkhealth"])
print("top", out["top_domains"][:12])
