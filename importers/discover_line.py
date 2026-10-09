#!/usr/bin/env python3
"""discover_line.py — find the businesses whose whole web presence is a LINE
Official Account, by searching for the handle rather than for the shop.

    python3 importers/discover_line.py --dry-run          print the query list
    python3 importers/discover_line.py --queue 60         next 60 unrun queries, as JSON, for a bot
    python3 importers/discover_line.py --deposit _incoming/line-search/2026-09-21.json
    python3 importers/discover_line.py --report           rebuild the JSON from cache, no network
    python3 importers/discover_line.py --limit 40         a short polite direct run
    python3 importers/discover_line.py --self-test        no network

WHY (measured 2026-09-21). A LINE Official Account has a public profile page,
and that page carries the name, a phone, an address, a lat/lng and the
account's own website field. A Chiang Mai shop with no site still has all of
that — it is simply not written down anywhere a crawler of the open web goes.
88,275 canonical records; 15,571 carry a website. 742 already carry a LINE
link, 714 of those on rows with no website at all.

HOW. Three query shapes, three different doors, over the vocabulary
discover_facebook.py already built out of data/categories.json and the trade
words this city's businesses use for themselves:

    site:page.line.me <word> <city>        LINE's own pages, as indexed
    "lin.ee" <word> <city>                 the add-friend link, pasted anywhere
    "LINE ID" <word> <city>                the id typed out, no link at all
    "ไลน์ไอดี" <word> <city>

A result is worth keeping only if a LINE handle can be read out of its url,
title or snippet. That handle then goes to probe_line_oa.py, which is the only
thing here that ever talks to LINE.

WHO RUNS THE SEARCHES. The same arrangement discover_facebook.py settled on:
html.duckduckgo.com challenges a self-identified bot, this script keeps its own
name in its UA and stops when challenged, and the volume goes through the Opus
bots' sanctioned web search — `--queue N` prints the next N unrun queries,
`--deposit` folds the answers in as if they had been fetched here.

    deposit shape, one JSON file, a list of:
      {"q": "site:page.line.me ร้านกาแฟ เชียงใหม่", "fetched": "2026-09-21",
       "results": [{"url": "...", "title": "...", "snippet": "..."}],
       "via": "<bot> webSearch"}

WHAT IT WRITES.
  cache/line_discovery/queries/<sha1>.json  one file per query, dated, so a
                                            re-run costs only what changed.
  cache/line_oa_seeds.json                  every handle found, with the
                                            queries that found it. This is what
                                            probe_line_oa.py --seed-search
                                            reads.
  data/curated/line_search.json             the report: handle, where it was
                                            found, what shelf the query came
                                            from, and whether the catalogue
                                            already carries it.

WHAT IT WILL NOT DO. It writes no records and it fetches nothing from LINE. A
handle that matches nothing in the catalogue is a LEAD; "no match" says no
record carries this handle, which is all a lookup can say.
"""
import argparse
import datetime as dt
import hashlib
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))

from discover_facebook import (  # noqa: E402
    PROVINCES, amphoe, fetch as ddg_fetch, Challenge, vocab2, vocabulary,
    _identity, load_catalogue,
)
from probe_line_oa import handles_in  # noqa: E402

QCACHE = ROOT / "cache" / "line_discovery" / "queries"
SEEDS = ROOT / "cache" / "line_oa_seeds.json"
OUT = ROOT / "data" / "curated" / "line_search.json"
TODAY = dt.date.today().isoformat()

SHAPES = [
    ("page", 'site:page.line.me {word} {city}'),
    ("link", '"lin.ee" {word} {city}'),
    ("typed_en", '"LINE ID" {word} {city}'),
    ("typed_th", '"ไลน์ไอดี" {word} {city}'),
]


def queries(provinces, only=None, tier="all", shapes=None):
    """Every query, in the order they should be run.

    tier 1  shelf label x province        the site's own tree, both languages
    tier 2  self-description x province   what businesses call themselves
    tier 3  shelf label x AMPHOE          the province rather than the city;
            page-shape only, which is the shape that returns LINE's own pages
    """
    want = {"all": {1, 2, 3}, "1": {1}, "2": {2}, "3": {3}, "12": {1, 2}}[str(tier)]
    use = [s for s in SHAPES if not shapes or s[0] in shapes]
    for prov in provinces:
        P = PROVINCES[prov]
        base = []
        if 1 in want:
            base += [(c, ch, l, w, 1) for c, ch, l, w in vocabulary(only)]
        if 2 in want:
            base += [(c, ch, l, w, 2) for c, ch, l, w in vocab2(only)]
        for cat, child, lang, word, tr in base:
            for shape, tpl in use:
                # A Thai-language door wants a Thai word; an English one, English.
                if shape == "typed_th" and lang != "th":
                    continue
                if shape == "typed_en" and lang != "en":
                    continue
                yield {"prov": prov, "cat": cat, "child": child, "lang": lang,
                       "word": word, "tier": tr, "area": None, "shape": shape,
                       "q": tpl.format(word=word, city=P[lang])}
        if 3 in want:
            seen = set()
            for cat, child, lang, word in list(vocabulary(only)) + list(vocab2(only)):
                if (word, lang) in seen:
                    continue
                seen.add((word, lang))
                for amp in amphoe(prov):
                    yield {"prov": prov, "cat": cat, "child": child, "lang": lang,
                           "word": word, "tier": 3, "area": amp, "shape": "page",
                           "q": f"site:page.line.me {word} {amp}"}


def qpath(q):
    return QCACHE / (hashlib.sha1(q.encode("utf-8")).hexdigest()[:16] + ".json")


def unrun(qs, fresh_days):
    today = dt.date.today()
    out = []
    for spec in qs:
        p = qpath(spec["q"])
        if p.exists():
            try:
                prev = json.loads(p.read_text(encoding="utf-8"))
                if (today - dt.date.fromisoformat(prev["fetched"])).days < fresh_days:
                    continue
            except Exception:                                # noqa: BLE001
                pass
        out.append(spec)
    return out


def deposit(path, provinces, only=None):
    """Fold result sets a bot ran into the cache. Returns (accepted, unknown)."""
    QCACHE.mkdir(parents=True, exist_ok=True)
    spec_by_q = {s["q"]: s for s in queries(provinces, only, "all")}

    def canon(q):
        return re.sub(r"\s+", " ", (q or "").strip())

    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = entries.get("searches") or entries.get("results") or [entries]
    accepted = unknown = 0
    for e in entries:
        q = canon(e.get("q") or e.get("query") or "")
        spec = spec_by_q.get(q)
        if not spec:
            unknown += 1
            print(f"  ? not a vocabulary query, kept under its own text: {q}", file=sys.stderr)
            spec = {"prov": e.get("prov") or ("cr" if "เชียงราย" in q or "Chiang Rai" in q else "cm"),
                    "cat": e.get("cat") or "unshelved", "child": e.get("child"),
                    "lang": "th" if re.search(r"[ก-๙]", q) else "en",
                    "tier": e.get("tier") or 0, "area": e.get("area"),
                    "shape": e.get("shape") or "deposit",
                    "word": e.get("word") or q, "q": q}
        results = [{"url": r["url"], "title": r.get("title") or "", "snippet": r.get("snippet") or ""}
                   for r in (e.get("results") or []) if r.get("url")]
        rec = dict(spec, fetched=e.get("fetched") or TODAY, results=results, error=None,
                   via=e.get("via") or f"deposit:{Path(path).name}")
        qpath(spec["q"]).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        accepted += 1
    return accepted, unknown


def run_queries(qs, pause, fresh_days, limit):
    QCACHE.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    ran = cached = 0
    for spec in qs:
        p = qpath(spec["q"])
        if p.exists():
            try:
                prev = json.loads(p.read_text(encoding="utf-8"))
                if (today - dt.date.fromisoformat(prev["fetched"])).days < fresh_days:
                    cached += 1
                    continue
            except Exception:                                # noqa: BLE001
                pass
        if limit is not None and ran >= limit:
            break
        try:
            results = ddg_fetch(spec["q"])
        except Challenge:
            print(f"\n  challenge page after {ran} queries — stopping; progress is saved.",
                  file=sys.stderr)
            break
        except Exception as e:                               # noqa: BLE001
            results = None
            print(f"  ! {spec['q']}: {e}", file=sys.stderr)
        rec = dict(spec, fetched=today.isoformat(), via="direct",
                   results=results if results is not None else [],
                   error=None if results is not None else "fetch failed")
        p.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        ran += 1
        found = sum(len(handles_in(r["url"] + " " + r["title"] + " " + r["snippet"]))
                    for r in rec["results"])
        print(f"  {ran:4d}  {len(rec['results']):2d} results  {found:2d} handles  {spec['q']}")
        time.sleep(pause + random.uniform(0, pause / 2))
    return ran, cached


# ---- harvest ---------------------------------------------------------------

BARE_RE = re.compile(r"(?:LINE\s*ID|ไลน์ไอดี|ไลน์|LINE)\s*[:：]?\s*@([a-z0-9][a-z0-9._-]{3,19})", re.I)


def handles_of(res):
    """Handles in one result — from the url, and from the text around an @."""
    text = f"{res['url']} {res['title']} {res['snippet']}"
    out = list(handles_in(text))
    for m in BARE_RE.finditer(text):
        h = m.group(1).lower()
        if h == h.strip("._-"):
            out.append(("oa", "@" + h))
    seen, uniq = set(), []
    for kind, val in out:
        if (kind, val) not in seen:
            seen.add((kind, val))
            uniq.append((kind, val))
    return uniq


def build_report(provinces):
    by_key, by_name = load_catalogue()
    catalogue_handles = {}
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if not f.exists():
            continue
        for rec in json.loads(f.read_text(encoding="utf-8")):
            blob = json.dumps(rec, ensure_ascii=False)
            if "lin.ee" in blob or "line.me" in blob:
                for kind, val in handles_in(blob):
                    catalogue_handles.setdefault((kind, val), rec["id"])

    rows, n_q, n_res = {}, 0, 0
    for p in sorted(QCACHE.glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            continue
        if rec["prov"] not in provinces:
            continue
        n_q += 1
        shelf = rec["cat"] + ("/" + rec["child"] if rec["child"] else "")
        for res in rec["results"]:
            n_res += 1
            for kind, val in handles_of(res):
                row = rows.get((kind, val))
                if row is None:
                    name = re.split(r"\s*\|\s*", res["title"])[0].strip()
                    row = {"kind": kind, "handle": val, "name_hint": name,
                           "found_on": res["url"], "snippet": res["snippet"],
                           "prov": rec["prov"], "shelves": [], "queries": [],
                           "shapes": [], "fetched": rec["fetched"],
                           "inCatalogue": catalogue_handles.get((kind, val)),
                           "status": "lead"}
                    rows[(kind, val)] = row
                for field, v in (("shelves", shelf), ("queries", rec["q"]), ("shapes", rec["shape"])):
                    if v not in row[field]:
                        row[field].append(v)

    fresh = [r for r in rows.values() if not r["inCatalogue"]]
    # Merged, not overwritten: decode_line_qr.py writes into the same file.
    from decode_line_qr import merge_seeds
    merge_seeds([{"kind": r["kind"], "handle": r["handle"], "prov": r["prov"],
                  "name_hint": r["name_hint"], "found_on": r["found_on"],
                  "queries": r["queries"], "how": "web search"}
                 for r in rows.values()])

    doc = {
        "_comment": "LINE handles found by searching the open web for the handle "
                    "rather than for the shop. LEADS, not records. 'inCatalogue' "
                    "null means no record carries this handle — which is what a "
                    "lookup can say, and not that the business is missing.",
        "generated": TODAY,
        "counts": {
            "queries": n_q, "results": n_res,
            "handles": len(rows),
            "officialAccounts": sum(1 for r in rows.values() if r["kind"] != "personal"),
            "personal": sum(1 for r in rows.values() if r["kind"] == "personal"),
            "alreadyInCatalogue": len(rows) - len(fresh),
            "new": len(fresh),
            "byShape": {s: sum(1 for r in rows.values() if s in r["shapes"]) for s, _ in SHAPES},
        },
        "handles": sorted(rows.values(), key=lambda r: (r["prov"], r["handle"])),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def self_test():
    qs = list(queries(["cm"], tier="1", shapes={"page"}))
    assert qs and all(q["q"].startswith("site:page.line.me ") for q in qs)
    assert all("เชียงใหม่" in q["q"] or "Chiang Mai" in q["q"] for q in qs)
    th = [q for q in queries(["cm"], tier="1", shapes={"typed_th"})]
    assert all(q["lang"] == "th" for q in th)
    got = handles_of({"url": "https://page.line.me/gyk4392g", "title": "ราชพฤกษ์แล็บ | LINE Official Account",
                      "snippet": "ไลน์ไอดี: @ratchaphrueklab โทร 085..."})
    assert ("oa", "@gyk4392g") in got, got
    assert ("oa", "@ratchaphrueklab") in got, got
    none = handles_of({"url": "https://example.com", "title": "x", "snippet": "y"})
    assert none == [], none
    assert qpath("a") != qpath("b")
    print("self-test ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--province", choices=["cm", "cr"], action="append")
    ap.add_argument("--only", help="one category key from data/categories.json")
    ap.add_argument("--tier", default="all", choices=["all", "1", "2", "3", "12"])
    ap.add_argument("--shape", action="append", choices=[s for s, _ in SHAPES])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--pause", type=float, default=3.0)
    ap.add_argument("--fresh-days", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--queue", type=int)
    ap.add_argument("--deposit")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    provinces = a.province or ["cm", "cr"]
    shapes = set(a.shape) if a.shape else None
    qs = list(queries(provinces, a.only, a.tier, shapes))

    if a.dry_run:
        for spec in qs:
            print(spec["q"])
        print(f"\n{len(qs)} queries", file=sys.stderr)
        return
    if a.queue:
        print(json.dumps([{"q": s["q"], "prov": s["prov"], "cat": s["cat"],
                           "child": s["child"], "lang": s["lang"], "tier": s["tier"],
                           "area": s["area"], "shape": s["shape"], "word": s["word"]}
                          for s in unrun(qs, a.fresh_days)[:a.queue]],
                         ensure_ascii=False, indent=1))
        return
    if a.deposit:
        ok, unknown = deposit(a.deposit, provinces, a.only)
        print(f"{ok} deposited, {unknown} outside the vocabulary", file=sys.stderr)
    elif not a.report:
        ran, cached = run_queries(qs, a.pause, a.fresh_days, a.limit)
        print(f"{ran} run, {cached} already fresh", file=sys.stderr)
    doc = build_report(provinces)
    print(json.dumps(doc["counts"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
