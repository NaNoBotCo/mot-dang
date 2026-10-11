#!/usr/bin/env python3
"""Turn a CMHY read into catalogue records — the shared half. WO-56+.

What every trade's register builder needs and none should rewrite:
  dedupe   the same door is not written twice. A directory row within
           RADIUS metres of a canonical record on the SAME category is that
           record; the builder gets the id back and enriches or skips.
           Distance, not name — a shop's Thai directory name and its OSM
           English name rarely share a character (the WO-54 rule).
  record   one shape for a cm-curated-* row: directory-published GPS, the
           directory's dateModified as sourceUpdated, hours read off the
           cached page, `_hoursSource` naming the directory, `needs-pin`
           when the directory publishes no GPS (the WO-54b CR-tailor shape).
  upsert   append to additions-chiang-mai.json without touching a record
           that already exists (a second pass may fill hours and desc only).

Nothing here decides a trade: that is the builder's job, from the shop's
own tags and name, with the refusals written down.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_paper_sites as reader  # noqa: E402
import build_paper_register as paper  # noqa: E402 — hours_of / page_extras

ROOT = Path(__file__).resolve().parent.parent
RADIUS = 80.0


def dist_m(a, b, c, d):
    return paper.dist_m(a, b, c, d)


def canonical(prov="cm"):
    p = ROOT / "data" / "canonical" / f"{prov}.json"
    return json.loads(p.read_text()) if p.exists() else []


def near(lat, lng, recs, cats=None, radius=RADIUS):
    """The nearest canonical record within radius on one of `cats` (any
    category when cats is None). Returns (record, metres) or (None, None)."""
    best, bd = None, None
    for r in recs:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        if cats and not (set(r.get("cat") or []) & set(cats)):
            continue
        d = dist_m(lat, lng, r["lat"], r["lng"])
        if d < radius and (bd is None or d < bd):
            best, bd = r, d
    return best, bd


def page_extras(job, pid):
    reader.CACHE = ROOT / "cache" / "cmhy" / job
    return paper.page_extras(pid)


def slug(name):
    return paper.slug(name)


_LINKHEALTH = None
_BROKEN = {"dns", "gone", "parked", "http-error", "timeout"}


def link_verdict(url):
    """What data/linkhealth.json already knows about a URL, or None.

    A directory row's `website` is often a domain that died years ago —
    bikkychiangmai.com is PARKED and link-health has said so since July —
    and writing it into a record puts a bare <a href> to a parked domain on
    a place page, which the publish gate refuses and is right to. So the
    field is not written at all when the checker already knows it is bad;
    the address is kept in attrs with the verdict, which is the dead-ref
    rule the register pages use, applied one layer earlier.
    """
    global _LINKHEALTH
    if _LINKHEALTH is None:
        p = ROOT / "data" / "linkhealth.json"
        _LINKHEALTH = (json.loads(p.read_text(encoding="utf-8")).get("links", {})
                       if p.exists() else {})
    u = (url or "").strip()
    for cand in (u, u + "/", u.rstrip("/")):
        v = _LINKHEALTH.get(cand)
        if v:
            return v
    return None


def record(row, rid, cat, sub, kind, today, job, prov="cm", attrs=None,
           blurb_th="", blurb_en="", name_en="", facility=None):
    hours, desc = page_extras(job, row["id"])
    street = row.get("street") or ""
    needs_pin = not row.get("lat")
    a = {"kind": kind, "pinVia": "directory-published-gps",
         "tradeTags": [t for t in row.get("tags", []) if t]}
    if desc:
        a["desc"] = desc[:300]
    if hours:
        a["_hoursSource"] = "cmhy.city directory row, not the shop's own page"
    if facility:
        a["facilityType"] = facility
    if needs_pin:
        a["pinVia"] = "directory publishes no GPS — address only"
    site = (row.get("site") or "").strip()
    v = link_verdict(site)
    if site and v and v.get("status") in _BROKEN:
        a["deadSite"] = site
        a["deadSiteWhy"] = f"{v.get('status')} (link-health, checked {v.get('checkedAt')})"
        if (v.get("wayback") or {}).get("url"):
            a["deadSiteArchive"] = v["wayback"]["url"]
        site = ""
    a.update(attrs or {})
    return {
        "id": rid, "province": prov, "cat": [cat], "sub": [sub] if sub else [],
        "name": row["name"], "nameEn": name_en,
        "address": ", ".join(x for x in (street, row.get("amphoe", ""), row.get("postcode", "")) if x),
        "phone": row.get("phone", ""), "website": site, "hours": hours,
        "attrs": a, "featured": False, "landmark": False,
        # Nan, 2026-09-06: no blurbs. The tags are the record (attrs.tradeTags);
        # the joined sentence and any hand-written prose are refused here so a
        # re-import cannot regrow them. tests/test_no_blurbs.py.
        "blurb_th": "",
        "blurb_en": "",
        "sources": [{"type": "directory", "ref": row["url"], "fetched": today,
                     "sourceUpdated": (row.get("modified") or "")[:10]}],
        "confidence": "curated", "updatedAt": today,
        "lat": None if needs_pin else float(row["lat"]),
        "lng": None if needs_pin else float(row["lng"]),
        "geoPrecision": "needs-pin" if needs_pin else "approx",
    }


def upsert(records, prov="cm"):
    p = ROOT / "data" / "curated" / f"additions-chiang-{'mai' if prov == 'cm' else 'rai'}.json"
    add = json.loads(p.read_text())
    have = {r["id"]: r for r in add}
    n_new, n_touched = 0, 0
    for rec in records:
        old = have.get(rec["id"])
        if old is None:
            add.append(rec)
            have[rec["id"]] = rec
            n_new += 1
            continue
        # Second pass: hours and the shop's own paragraph only.
        if rec.get("hours") and not old.get("hours"):
            old["hours"] = rec["hours"]
            n_touched += 1
        if rec["attrs"].get("desc") and not old["attrs"].get("desc"):
            old["attrs"]["desc"] = rec["attrs"]["desc"]
        # A CORRECTED RULE HAS TO BE ABLE TO REACH THE ROWS IT ALREADY WROTE.
        # Until 2026-09-05 this loop touched hours and desc and nothing else,
        # so a trade whose sub was left blank the first time stayed blank
        # forever however the rule was fixed afterwards. That is what kept 64
        # pet shops off a shelf: the rule said ("pets", None, ...) because
        # `pets` had no shop child, the child went up, and the rule change
        # reached nothing. This fills a sub the old row does not have; it
        # never removes one and never overrules one, which is the same bar
        # shelves.json holds itself to.
        if rec.get("sub") and not (old.get("sub") or []):
            old["sub"] = sorted(set(rec["sub"]))
            n_touched += 1
    p.write_text(json.dumps(add, ensure_ascii=False, indent=1) + "\n")
    return n_new, n_touched


def blob(row):
    return (" ".join(row.get("tags", [])) + " " + row.get("name", "") + " " + (row.get("desc") or "")).lower()


def own(row):
    """What the shop calls itself: name + tags, not the paragraph."""
    return (" ".join(row.get("tags", [])) + " " + row.get("name", "")).lower()


def has(text, words):
    return any(w.lower() in text for w in words)


def fresh(row):
    return (row.get("modified") or "")[:4] in ("2025", "2026")
