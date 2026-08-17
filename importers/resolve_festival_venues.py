#!/usr/bin/env python3
"""Give the festival canon's venues a place id. Zero network.

WHY
`data/festivals.json` names 52 venues in prose — "วัดเจดีย์หลวง · Wat Chedi
Luang", "ข่วงประตูท่าแพ · Tha Phae Gate square". Nothing joins prose to the
catalogue, so `festivals_layer.venue_places()` re-runs the strict matcher on
every build and guesses again from scratch each time. The result: a festival
band reaches **13 of 12,319** place pages.

An id resolves once, by a person looking at the answer, and stays resolved. The
free text stays exactly where it is — it is the display name and the fallback
when a venue is a river bank or a stretch of road that is not a catalogue
record and never will be.

HOW
The same strict matcher the events layer uses (`build.match_venue`): a curated
alias, an exact name, or a full distinctive-token subset landing on exactly one
record. Loose matching is not available and should not be added — it is what
put "Fact Cafe" on "Bua Bhat Factory".

Three buckets, and only the first is written:
  matched       -> venues[].place_id in data/festivals.json
  ambiguous     -> review file; the matcher found candidates and could not choose
  no candidate  -> review file; usually correct, because a moat bank is not a shop

    python3 importers/resolve_festival_venues.py           # report only
    python3 importers/resolve_festival_venues.py --write   # write the ids

Re-runnable: --write only ever fills an empty place_id, so a hand-corrected id
survives the next run. Remove an id by hand to have it reconsidered.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402  (the matcher and the index live there)


def load_places() -> dict:
    return {p["key"]: json.loads((ROOT / "data" / "canonical" / f"{p['key']}.json").read_text())
            for p in build.PROVINCES}


# A venue string names its province for a reader's benefit — "ประตูท่าแพ
# เชียงใหม่", "Singha Park, Chiang Rai". The catalogue record does not carry
# the province in its name, so the suffix has to come off before comparing or
# an exact match is never reached. Left on, "ประตูท่าแพ เชียงใหม่" missed the
# gate entirely and the token fallback landed on Punspace Tha Phae Gate, a
# coworking office of a similar name.
PROV_SUFFIX = re.compile(
    r"[\s,]*(เชียงใหม่|เชียงราย|chiang\s*mai|chiang\s*rai)\s*$", re.IGNORECASE)


def forms(raw: str):
    """The spellings of a venue string worth trying, longest first."""
    out = []
    for base in (raw, re.split(r"[—(/·]|,", raw)[0].strip()):
        for cand in (base, PROV_SUFFIX.sub("", base).strip()):
            if cand and cand not in out:
                out.append(cand)
    return out


def stated_province(raw: str):
    """The province the venue string itself names, if it names one."""
    m = PROV_SUFFIX.search(raw or "")
    if not m:
        return None
    return "cm" if m.group(1).lower().replace(" ", "") in ("เชียงใหม่", "chiangmai") else "cr"


def candidates(raw: str, indexes: dict):
    """{province: (record, how, form)} — every province whose catalogue answers.

    Matching one province at a time is what catches a name standing in both.
    วัดพระสิงห์ is a famous temple in Chiang Mai and also a temple in Chiang
    Rai; a single index returns whichever was inserted first, which put
    Songkran's Phra Buddha Sihing procession in the wrong province.
    """
    hits = {}
    for prov, idx in indexes.items():
        for cand in forms(raw):
            r, how = build.match_venue(cand, idx)
            if r:
                hits[prov] = (r, how, cand)
                break
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="write place_id into data/festivals.json")
    args = ap.parse_args()

    path = ROOT / "data" / "festivals.json"
    doc = json.loads(path.read_text())
    fests = doc.get("festivals") or []

    data = load_places()
    # One index per province, so a name standing in both is visible as such
    # instead of being settled by whichever record was loaded first.
    indexes = {p["key"]: build._venue_index(
        {q["key"]: (data[q["key"]] if q["key"] == p["key"] else [])
         for q in build.PROVINCES}) for p in build.PROVINCES}

    matched, kept, unresolved, decided = 0, 0, [], []
    for f in fests:
        fest_prov = f.get("province")
        for v in f.get("venues") or []:
            if v.get("place_id"):
                kept += 1
                continue
            label = v.get("th") or v.get("en") or "?"
            # Both spellings are asked, and both answers are kept. A venue's
            # Thai and Latin names must land on the same place; when they do
            # not, one of the two catalogue records is missing a name and the
            # matcher has quietly crossed a province. That is how Songkran's
            # Phra Buddha Sihing procession reached Chiang Rai's วัดพระสิงห์
            # while our Chiang Mai record for Wat Phra Singh — which carries no
            # Thai name at all — sat right there unmatched.
            hits, used_raw = {}, ""
            for raw in (v.get("th"), v.get("en")):
                if not raw:
                    continue
                found = candidates(raw, indexes)
                if found and not hits:
                    used_raw = raw
                for prov, val in found.items():
                    hits.setdefault(prov, val)

            if not hits:
                unresolved.append(
                    f"{f['id']}  {f['name_th']} · {f['name_en']}\n"
                    f"    venue: {label}\n"
                    f"    no catalogue record answers to this name. Often right —\n"
                    f"    a river bank, a stretch of road, a whole quarter — but if\n"
                    f"    it is a place we hold, add an alias to\n"
                    f"    data/curated/venue_aliases.json rather than loosening the matcher.\n")
                continue

            # Which province is this venue in? The string may say so; a
            # single-province festival says so; otherwise only one answering
            # province is an answer at all.
            want = stated_province(used_raw) or (
                fest_prov if fest_prov in ("cm", "cr") else None)
            if want and want in hits:
                pv = want
            elif len(hits) == 1:
                pv = next(iter(hits))
            else:
                lines = "".join(
                    f"      {p}: {r['id']}  {build.name_text(r)}\n"
                    for p, (r, _h, _c) in sorted(hits.items()))
                unresolved.append(
                    f"{f['id']}  {f['name_th']} · {f['name_en']}\n"
                    f"    venue: {label}\n"
                    f"    this name stands in both provinces and the festival "
                    f"({fest_prov}) does not say which:\n" + lines
                    + f"    Name the province in the venue string, or set place_id by hand.\n")
                continue

            hit, how, used = hits[pv]
            decided.append({"f": f, "v": v, "label": label, "prov": pv,
                            "rec": hit, "how": how, "used": used,
                            "stated": bool(stated_province(used_raw)),
                            "alt": {p: h[0] for p, h in hits.items() if p != pv}})

    # A festival's venues corroborate each other. Where a festival gathers in
    # one province and a single venue resolves to the other without saying so,
    # the odd one out is a mis-match, not a discovery: Songkran's Phra Buddha
    # Sihing procession landed on Chiang Rai's วัดพระสิงห์ because our Chiang
    # Mai record for Wat Phra Singh carries no Thai name for the Thai string to
    # reach. Nothing is corrected here — it goes to a person.
    counts = {}
    for d in decided:
        counts.setdefault(d["f"]["id"], {}).setdefault(d["prov"], 0)
        counts[d["f"]["id"]][d["prov"]] += 1
    for d in decided:
        tally = counts[d["f"]["id"]]
        others = sum(n for p, n in tally.items() if p != d["prov"])
        if d["stated"] or tally[d["prov"]] > 1 or others < 2:
            f, v = d["f"], d["v"]
            if args.write:
                v["place_id"] = d["rec"]["id"]
                v["place_matched"] = d["how"]
            matched += 1
            print(f"  {f['id']:<22} {d['label'][:36]:<36} → {d['rec']['id']}"
                  f"  ({d['how']}, via {d['used'][:26]!r}, {d['prov']})")
            continue
        unresolved.append(
            f"{d['f']['id']}  {d['f']['name_th']} · {d['f']['name_en']}\n"
            f"    venue: {d['label']}\n"
            f"    resolved to {d['prov']} ({d['rec']['id']} "
            f"{build.name_text(d['rec'])}) while {others} other venue(s) of this\n"
            f"    festival are in the other province, and the string does not say "
            f"which.\n"
            f"    Usually our record in the gathering province carries no Thai "
            f"name for the\n    Thai string to reach. Settle it with an entry in "
            f"data/curated/venue_aliases.json.\n")

    if args.write:
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")

    cache = ROOT / "cache"
    cache.mkdir(exist_ok=True)
    rpath = cache / "festival_venues_review.txt"
    rpath.write_text(
        f"{len(unresolved)} festival venue(s) with no catalogue record.\n"
        f"Nothing here is guessed into data/festivals.json. A venue that IS a\n"
        f"place we hold belongs in data/curated/venue_aliases.json; a venue that\n"
        f"is a riverbank or a road stays prose, which is the right answer.\n\n"
        + "\n".join(unresolved), encoding="utf-8")

    total = sum(len(f.get("venues") or []) for f in fests)
    print(f"\nfestival venues: {matched} newly resolved, {kept} already held, "
          f"{len(unresolved)} unresolved of {total}")
    print(f"  review → {rpath.relative_to(ROOT)}")
    if not args.write:
        print("  (report only — pass --write to record the ids)")


if __name__ == "__main__":
    main()
