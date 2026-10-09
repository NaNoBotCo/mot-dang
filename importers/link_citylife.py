#!/usr/bin/env python3
"""Match Mot Dang's venues to the pages Chiang Mai Citylife wrote about them.

Citylife has published a Chiang Mai magazine since 2002 and keeps 504 venue
pages, each with an editor's paragraph, a category and a pin. This directory
knows where those places are now, in Thai, with a phone number; it holds no
paragraph about any of them. A reader who wants both has had to know that both
sites exist.

    python3 importers/link_citylife.py [--harvest PATH]

Writes data/citylife_links.json, read by build.py. Nothing is fetched at build
time: the sibling index is read once here and baked, the same shape as
link_wichaa.py reading the vault. If the index is not on this machine the file
is left alone and the links simply do not render.

THE INDEX. Citylife publishes no API — /wp-json/ redirects to a YouTube video
— so the sibling index is built from their own public pages by
../citylife-api/harvest.py, one request a second. Their venue pages carry
data-marker-lat / data-marker-lon in the markup, which is where the positions
below come from.

MATCHING. A name alone is not identity and neither is a pin: Citylife's pins
are from 2015 and this city rebuilds itself. So a link is written where the
two agree on BOTH, and how much of each is traded against the other:

  * a name that is all but identical (>= NAME_SURE) may stand up to FAR_M
    apart — two venues called Le Coq d'Or 364 m apart is not what happened,
    a pin dropped on the wrong side of the block is;
  * a looser name (>= NAME_OK) has to be within NEAR_M.

Anything else is counted and left unlinked. A wrong link here sends a reader
to another restaurant's write-up, which is worse than no link at all — the
same reasoning link_wichaa.py uses on three temples sharing one name.
"""
import argparse
import json
import math
import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "citylife_links.json"
DEFAULT_HARVEST = ROOT.parent / "citylife-api" / "out" / "places.json"

NEAR_M = 150.0     # how far a merely similar name may sit
FAR_M = 400.0      # how far an all-but-identical name may sit
NAME_OK = 0.82
NAME_SURE = 0.95
NEAR_MISS = 0.60   # below this there is no counterpart here, only a neighbour

# Only the words that say nothing about which venue this is. Café, hotel and
# spa stay in: dropping them made "Small Café" and "The Small Chiang Mai" the
# same string, and they are two businesses.
NOISE = re.compile(r"\b(the|chiang ?mai|co|ltd|company|thailand)\b")


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9ก-๙ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def core(s):
    return re.sub(r"\s+", " ", NOISE.sub(" ", norm(s))).strip() or norm(s)


def sim(a, b):
    """0..1. Containment counts only for a name of two words or more landing on
    word boundaries — a plain substring test matched "U" inside "Lost Lounge",
    and "Market" inside "Ploen Rudee Night Market" 400 m away."""
    a, b = core(a), core(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    score = SequenceMatcher(None, a, b).ratio()
    if len(short.split()) >= 2 and re.search(r"(?:^| )" + re.escape(short) + r"(?:$| )", long):
        score = max(score, 0.93)
    ta, tb = set(a.split()), set(b.split())
    shared = ta & tb
    if len(shared) >= 2:
        score = max(score, 0.95 * len(shared) / len(ta | tb))
    return score


def haversine(a, b, c, d):
    r = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def verdict(metres, score):
    if score >= NAME_SURE and metres <= FAR_M:
        return "name-sure"
    if score >= NAME_OK and metres <= NEAR_M:
        return "near+name"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default=str(DEFAULT_HARVEST))
    args = ap.parse_args()
    harvest = Path(args.harvest)
    if not harvest.exists():
        print(f"🐜 no Citylife index at {harvest} — leaving {OUT.name} as it is")
        return

    venues = [v for v in json.loads(harvest.read_text()) if v.get("lat") and v.get("name")]
    index = json.loads((harvest.parent / "index.json").read_text()) if \
        (harvest.parent / "index.json").exists() else {}
    read_on = (index.get("generated") or "")[:10] or date.today().isoformat()

    records = []
    for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
        d = json.loads(f.read_text())
        records += d if isinstance(d, list) else (d.get("places") or d.get("records") or [])

    # 0.01° is about 1.1 km — wide enough for FAR_M with a cell to spare.
    grid = {}
    for r in records:
        if r.get("lat") is not None and r.get("lng") is not None:
            grid.setdefault((round(r["lat"], 2), round(r["lng"], 2)), []).append(r)

    links, held, unmatched = {}, [], 0
    for v in venues:
        cands = []
        for dy in (-0.01, 0, 0.01):
            for dx in (-0.01, 0, 0.01):
                cands += grid.get((round(v["lat"] + dy, 2), round(v["lng"] + dx, 2)), [])
        best = None
        for r in cands:
            m = haversine(v["lat"], v["lng"], r["lat"], r["lng"])
            if m > FAR_M:
                continue
            s = max(sim(v["name"], r.get(k)) for k in ("nameEn", "name", "nameTh"))
            if best is None or (s, -m) > (best[1], -best[0]):
                best = (m, s, r)
        if best is None:
            unmatched += 1
            continue
        m, s, r = best
        rule = verdict(m, s)
        if not rule:
            # A near miss is worth recording; a venue whose only neighbour
            # happens to be a noodle stall with another name is not a near
            # miss, it is a venue this directory does not hold.
            if s >= NEAR_MISS:
                held.append({"citylife": v["name"], "motdang": r.get("nameEn") or r.get("name"),
                             "metres": round(m), "nameScore": round(s, 3), "url": v["url"]})
            else:
                unmatched += 1
            continue
        year = (v.get("published") or "")[:4]
        keep = {"url": v["url"], "name": v["name"], "rule": rule,
                "metres": round(m), "nameScore": round(s, 3), "checked": read_on}
        if year:
            keep["year"] = year
        # One Citylife page per record, and one record per Citylife page: where
        # two venues land on the same row, the closer one keeps it.
        prev = links.get(r["id"])
        if prev and prev["metres"] <= keep["metres"]:
            continue
        links[r["id"]] = keep

    OUT.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "source": "https://www.chiangmaicitylife.com/",
        "index_read": str(harvest),
        "index_generated": read_on,
        "rule": (f"name >= {NAME_SURE} within {FAR_M:.0f} m, or name >= {NAME_OK} "
                 f"within {NEAR_M:.0f} m; anything looser is counted and left unlinked"),
        "citylife_venues": len(venues), "matched": len(links),
        "held_as_too_loose": len(held), "not_held_here": unmatched,
        "held": sorted(held, key=lambda h: -h["nameScore"]),
        "links": links}, ensure_ascii=False, indent=1))
    print(f"🐜 {len(links)} places matched to Chiang Mai Citylife "
          f"({len(venues)} venue pages read) -> {OUT}")
    print(f"   {len(held)} near misses held rather than published, "
          f"{unmatched} venues this directory does not hold")


if __name__ == "__main__":
    main()
