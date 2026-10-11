#!/usr/bin/env python3
"""🏷 The tag layer keeps its promises — run after build.py.

    python3 tests/test_tags.py            # against docs/
    MD_DOCS=/path/to/scratch python3 tests/test_tags.py

What it guards, each against a way this goes wrong quietly:

1. **Every tag has a rule, both names, a known family.** data/tags.json is the
   contract; a tag without a rule is a tag somebody typed, which the layer
   forbids by construction.
2. **A rule that matches nothing is a bug, not a quiet zero.** Every defined
   tag must reach a page in at least one province unless it is listed in
   KNOWN_EMPTY with a reason — the cafe-subcategory-sat-at-zero-for-weeks
   failure, caught at the gate instead of in a gemba.
3. **Counts are true.** For every province × tag, the page exists exactly when
   the count reaches min_tag; the h1 count, the rows on the page and
   data/tags.json agree; no tag×shelf page exists below tag_shelf_min and each
   one that exists forwards to search for that tag on that shelf.
4. **Provenance travels.** In places.json every record with `tags` carries a
   `tagVia` for each, with a head the layer knows.
5. **The pills are on the place pages**, linking only to pages that exist,
   and absent where a place earned nothing.
6. **Nothing leaks, everything indexes.** No /Users/ path on a tag page; every
   tag page is in the sitemap; /tags.html links only to pages that exist.
"""
import json
import os
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = pathlib.Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
SRC = json.loads((ROOT / "data" / "tags.json").read_text())
sys.path.insert(0, str(ROOT))

import tags_layer  # noqa: E402
import tags_mine   # noqa: E402

KNOWN_KINDS = {"attr", "attr-dict", "attr-list", "attr-true", "facet", "moat",
               "royal", "food-award", "brand", "curated",
               # WO-76: one rule per value the corpus's own fields carry
               "mined", "field", "hours"}
# `mined:` names the field it was read off; `name:` names the word it read out
# of the place's own name (2026-09-08).
VIA_HEADS = {"attr", "facet", "moat", "honours", "brand", "curated",
             "mined", "field", "hours", "name"}
# Defined on purpose, empty today, with the reason. A tag here is still
# worth defining: the day the crawl brings a fourth NGV pump the page appears
# with no edit. Anything else that is empty everywhere is a rule to look at.
KNOWN_EMPTY = {
    "ngv": "one CNG pump in all of CM, none in CR (fuel=cng on 1 record)",
}
ROW = re.compile(r'<li[^>]* data-n="')
PAGE_N = re.compile(r"-p\d+$")
HUB_CAP = 1400  # build.HUB_MAX_ROWS


def rows_all_pages(first):
    """Rows on a list page and on its -p2, -p3 … pages (paged since 2026-10-03)."""
    n, i = len(ROW.findall(first.read_text())), 2
    while (first.parent / f"{first.stem}-p{i}.html").exists():
        n += len(ROW.findall((first.parent / f"{first.stem}-p{i}.html").read_text()))
        i += 1
    return n
H1_COUNT = re.compile(r'<h1>.*?<span class="count">\(([\d,]+)\)</span></h1>', re.S)


def fail(msgs, m):
    msgs.append(m)


def engine(msgs):
    """0. the minting, no docs/ needed — two defects seen live 2026-09-10."""
    # ONE ROAD, ONE WAY. A record STREET_OF has matched to a street mints the
    # on-* tag from the street record — its slug, both names — so the tag and
    # the street chip are the same words. The address string is read only
    # where no match exists. The road here carries ํ+า for ำ, as 228 records do.
    spec = next(m for m in SRC["mined"] if m["key"] == "street")
    st = {"value": "rachadamnoen-road-82685d", "slug": "rachadamnoen-road-82685d",
          "th": "ถนนราชดำเนิน", "en": "Rachadamnoen Road", "source": "streets.json"}
    recs = [{"id": f"m{i}", "attrs": {"road": "ราชดําเนิน"}} for i in range(9)]
    recs += [{"id": f"u{i}", "attrs": {"road": "ราชดําเนิน"}} for i in range(9)]
    matched = {r["id"]: st for r in recs if r["id"].startswith("m")}
    defs, by_id = tags_mine.mine(recs, spec, {}, matched=matched)[:2]
    slugs = {d["slug"]: d for d in defs}
    on_st = "on-" + st["slug"]
    addr = "on-" + tags_mine._ascii_slug(tags_mine._romanize("ราชดำเนิน"))
    if sorted(slugs) != sorted([on_st, addr]):
        fail(msgs, f"street family minted {sorted(slugs)}, wanted [{on_st}, {addr}]")
    d = slugs.get(on_st) or {}
    if (d.get("th"), d.get("en")) != (st["th"], st["en"]):
        fail(msgs, f"{on_st}: names {d.get('th')!r} / {d.get('en')!r} are not the street's")
    if (d.get("rule") or {}).get("source") != "streets.json":
        fail(msgs, f"{on_st}: rule source {(d.get('rule') or {}).get('source')!r}, not streets.json")
    if "on-ratdanoen" in slugs:
        fail(msgs, "ํ+า still read as 'Ratdanoen'")
    for r in recs:
        want = on_st if r["id"] in matched else addr
        if by_id.get(r["id"]) != [want]:
            fail(msgs, f"{r['id']}: carries {by_id.get(r['id'])}, wanted [{want}]")
    plain = tags_mine.mine(recs, spec, {})[0]
    if [x["slug"] for x in plain] != [addr]:
        fail(msgs, f"with no match the address string should mint [{addr}], got {[x['slug'] for x in plain]}")
    # 345 streets are named in Latin only and 608 carry no nameEn: a match
    # still fills both halves, as the street chip does.
    for name, want in (("One Street", ("One Street", "One Street")),
                       ("ถนนสิงหราช", ("ถนนสิงหราช", tags_mine._romanize("ถนนสิงหราช")))):
        m2 = {"value": "x-1", "slug": "x-1", "th": name, "en": "", "source": "streets.json"}
        d2 = tags_mine.mine(recs, spec, {}, matched={r["id"]: m2 for r in recs})[0]
        got = (d2[0].get("th"), d2[0].get("en")) if d2 else None
        if got != want:
            fail(msgs, f"street {name!r} with no nameEn: names {got}, wanted {want}")
    print(f"engine: street tag   {on_st} from the match, {addr} off the address")

    # THE CAUTIOUS READING WINS. attrs.wheelchair "yes;limited" (merged
    # sources) or limited + the OSM facet was earning both wheelchair tags.
    def rec(i, **attrs):
        return {"id": f"w{i}", "province": "cm", "cat": ["food"], "name": f"ร้าน {i}", "attrs": attrs}
    data = {"cm": [rec(1, wheelchair="yes;limited"),
                   rec(2, wheelchair="limited", facets={"wheelchair": "osm-tag"}),
                   rec(3, wheelchair="yes"),
                   rec(4, wheelchair="limited")]}
    g = {"PROVINCES": [{"key": "cm"}], "CLAIMS": {}, "MOAT_POLY": None,
         "royal_of": lambda r: False, "FOOD_BY_ID": {},
         "_brand_index": lambda every: {}, "fold_key": lambda r, alias: None,
         "_norm_brand": lambda s: s, "name_of": lambda r: r.get("name") or "",
         "has_thai": lambda s: False, "SUB_LABELS": {}, "STREET_OF": {}}
    T = tags_layer.assign(g, data)
    want = {"w1": "wheelchair-limited", "w2": "wheelchair-limited",
            "w3": "wheelchair", "w4": "wheelchair-limited"}
    for pid, slug in want.items():
        got = [s for s in (T["by_id"].get(pid) or []) if s.startswith("wheelchair")]
        if got != [slug]:
            fail(msgs, f"{pid} ({data['cm'][int(pid[1]) - 1]['attrs']}): wheelchair tags {got}, wanted [{slug}]")
    print("engine: wheelchair   partial stands over full when sources disagree")


def main():
    msgs = []
    engine(msgs)
    # 1. the contract ----------------------------------------------------
    fams = {f["key"] for f in SRC["families"]}
    slugs = [t["slug"] for t in SRC["tags"]]
    if len(slugs) != len(set(slugs)):
        fail(msgs, "duplicate slugs in data/tags.json")
    for t in SRC["tags"]:
        for k in ("slug", "family", "th", "en", "glyph", "rule"):
            if not t.get(k):
                fail(msgs, f"tag {t.get('slug')!r} lacks {k}")
        if t.get("family") not in fams:
            fail(msgs, f"tag {t['slug']}: unknown family {t.get('family')!r}")
        if (t.get("rule") or {}).get("kind") not in KNOWN_KINDS:
            fail(msgs, f"tag {t['slug']}: unknown rule kind {t.get('rule')!r}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", t["slug"]):
            fail(msgs, f"tag {t['slug']}: slug must be ascii a-z0-9-")
        if "--" in t["slug"]:
            fail(msgs, f"tag {t['slug']}: '--' is the tag×shelf separator")
    print(f"defined tags       {len(slugs)} in {len(fams)} families")

    if not DOCS.exists():
        print("\n".join("  ! " + m for m in msgs))
        print("docs/ is not built — run build.py first")
        return 1
    built = (DOCS / "data" / "tags.json")
    if not built.exists():
        fail(msgs, "docs/data/tags.json missing — tags_layer.emit() did not run")
        print("\n".join(msgs)); print("FAIL"); return 1
    B = json.loads(built.read_text())
    min_tag, x_min = int(B["min_tag"]), int(B["tag_shelf_min"])
    provs = [p for p in ("cm", "cr") if (DOCS / p).is_dir()]
    bdefs = {t["slug"]: t for t in B["tags"]}
    if len(bdefs) < len(slugs):
        fail(msgs, f"built tags.json lists {len(bdefs)} tags, fewer than the {len(slugs)} defined")

    # 2. nothing silently empty ------------------------------------------
    for slug in slugs:
        t = bdefs.get(slug)
        if t and not any(t["counts"].get(p, 0) >= min_tag for p in provs) and slug not in KNOWN_EMPTY:
            fail(msgs, f"tag {slug}: no page in any province (counts {t['counts']}) — rule matches "
                       f"nothing, or add it to KNOWN_EMPTY with a reason")
    for slug in KNOWN_EMPTY:
        t = bdefs.get(slug)
        if t and any(t["counts"].get(p, 0) >= min_tag for p in provs):
            fail(msgs, f"tag {slug} is in KNOWN_EMPTY but now has a page — drop it from the list")

    # 3. counts are true --------------------------------------------------
    places = json.loads((DOCS / "data" / "places.json").read_text())
    by_prov_tag = {}
    by_prov_tag_cat = {}
    for r in places:
        for s in r.get("tags") or []:
            by_prov_tag.setdefault((r["province"], s), []).append(r)
            for c in r.get("cat") or []:
                by_prov_tag_cat.setdefault((r["province"], s, c), []).append(r)
    n_pages = n_cross = 0
    # sitemap.xml is an index since 2026-09-20 and names sitemap-N.xml; the
    # page URLs are in the shards, so the membership test reads those.
    sitemap = "".join(f.read_text() for f in sorted(DOCS.glob("sitemap-*.xml"))) \
        or ((DOCS / "sitemap.xml").read_text() if (DOCS / "sitemap.xml").exists() else "")
    for slug, t in bdefs.items():
        for p in provs:
            n = t["counts"].get(p, 0)
            pg = DOCS / p / "tag" / f"{slug}.html"
            if n >= min_tag:
                if not pg.exists():
                    fail(msgs, f"{p}/tag/{slug}.html missing though count {n} ≥ {min_tag}")
                    continue
                n_pages += 1
                html = pg.read_text()
                rows = rows_all_pages(pg)
                m = H1_COUNT.search(html)
                h1n = int(m.group(1).replace(",", "")) if m else -1
                real = len(by_prov_tag.get((p, slug), []))
                # A `state` tag past the shelf cap is a hub of shelf doors, no rows.
                if rows == 0 and t.get("family") == "state" and real > HUB_CAP:
                    rows = real
                if not (rows == h1n == n == real):
                    fail(msgs, f"{p}/tag/{slug}: rows {rows}, h1 {h1n}, tags.json {n}, places.json {real}")
                if "/Users/" in html:
                    fail(msgs, f"{p}/tag/{slug}: /Users/ path leak")
                if f"{p}/tag/{slug}.html" not in sitemap:
                    fail(msgs, f"{p}/tag/{slug}: not in sitemap.xml")
                # The crumb carries the family anchor (tags.html#cuisine) since
                # the family pages landed; the bare string it once looked for
                # failed every one of 2,685 pages, live and built alike (2026-09-10).
                if 'href="../../tags.html' not in html:
                    fail(msgs, f"{p}/tag/{slug}: no crumb back to /tags.html")
                if t["pages"].get(p) != f"https://motdang.net/{p}/tag/{slug}.html":
                    fail(msgs, f"{p}/tag/{slug}: tags.json page url wrong: {t['pages'].get(p)}")
            else:
                if pg.exists():
                    fail(msgs, f"{p}/tag/{slug}.html exists though count {n} < {min_tag}")
                if t["pages"].get(p):
                    fail(msgs, f"{p}/tag/{slug}: below threshold but tags.json lists a page url")
        # tag × shelf pages
        for p in provs:
            tdir = DOCS / p / "tag"
            if not tdir.is_dir():
                continue
            for xf in tdir.glob(f"{slug}--*.html"):
                if PAGE_N.search(xf.stem):
                    continue
                cat = xf.stem.split("--", 1)[1]
                real = by_prov_tag_cat.get((p, slug, cat), [])
                if len(real) < x_min:
                    fail(msgs, f"{p}/tag/{xf.name}: exists with only {len(real)} records (< {x_min})")
                # a forward to search since 2026-10-11 (tags_layer.emit)
                if f"search.html?tag={slug}&amp;cat={cat}" not in xf.read_text(encoding="utf-8"):
                    fail(msgs, f"{p}/tag/{xf.name}: not a forward to search?tag={slug}&cat={cat}")
                n_cross += 1
            # and none missing where the crowd is real
            for (pp, s, c), rs in by_prov_tag_cat.items():
                if pp == p and s == slug and len(rs) >= x_min and t["counts"].get(p, 0) >= min_tag \
                        and not (t.get("family") == "state" and len(rs) > HUB_CAP) \
                        and not (tdir / f"{slug}--{c}.html").exists():
                    fail(msgs, f"{p}/tag/{slug}--{c}.html missing though {len(rs)} ≥ {x_min}")
    print(f"tag pages          {n_pages}")
    print(f"tag×shelf pages    {n_cross}")

    # 4. provenance travels ----------------------------------------------
    tagged = [r for r in places if r.get("tags")]
    bad_via = 0
    for r in tagged:
        via = r.get("tagVia") or {}
        for s in r["tags"]:
            if s not in bdefs:
                fail(msgs, f"{r['id']}: tag {s} not in tags.json"); break
            if s not in via or via[s].split(":")[0] not in VIA_HEADS:
                bad_via += 1
    if bad_via:
        fail(msgs, f"{bad_via} tag assignments without a known tagVia")
    print(f"tagged records     {len(tagged):,} of {len(places):,}")

    # 5. the pills --------------------------------------------------------
    rnd = random.Random(20260819)
    sample = rnd.sample(tagged, min(40, len(tagged)))
    for r in sample:
        # the place page path: province/p/<slug>.html — slug is what build wrote;
        # find it through the per-tag JSON, which carries the url.
        s = r["tags"][0]
        tj = DOCS / "data" / "tags" / f"{r['province']}-{s}.json"
        if not tj.exists():
            continue            # below threshold: no page, no json — fine
        hit = next((x for x in json.loads(tj.read_text())["places"] if x["id"] == r["id"]), None)
        if not hit:
            fail(msgs, f"{r['id']}: not in data/tags/{r['province']}-{s}.json"); continue
        rel = hit["url"].split("motdang.net/", 1)[1]
        pg = DOCS / rel
        if not pg.exists():
            fail(msgs, f"{rel}: place page missing"); continue
        html = pg.read_text()
        if 'class="tagrow"' not in html:
            fail(msgs, f"{rel}: tagged but no tagrow on the page"); continue
        for href in re.findall(r'<a class="tag" href="([^"]+)"', html):
            target = (pg.parent / href).resolve()
            if not target.exists():
                fail(msgs, f"{rel}: pill links to missing {href}")
    untagged = [r for r in places if not r.get("tags")]
    for r in rnd.sample(untagged, min(10, len(untagged))):
        # any page of this record: build names it <latin>-<digits>.html or
        # <digits>.html. The glob alone is not enough — "*{digits}.html"
        # suffix-matches ANOTHER record whose longer stem happens to end in
        # these digits (found the hard way: an untagged record's digits
        # matched a tagged school's page). Re-strip and compare exactly.
        digits = re.sub(r"\D", "", r["id"])
        cands = [p for p in (DOCS / r["province"] / "p").glob(f"*{digits}.html")
                 if re.sub(r"\D", "", p.stem) == digits] if digits else []
        for pg in cands[:1]:
            if 'class="tagrow"' in pg.read_text():
                fail(msgs, f"{pg.relative_to(DOCS)}: untagged record shows a tagrow")

    # 6. the index --------------------------------------------------------
    idx = DOCS / "tags.html"
    if not idx.exists():
        fail(msgs, "tags.html missing")
    else:
        html = idx.read_text()
        for href in re.findall(r'href="((?:cm|cr)/tag/[^"]+)"', html):
            if not (DOCS / href).exists():
                fail(msgs, f"tags.html links to missing {href}")
        if "/Users/" in html:
            fail(msgs, "tags.html: /Users/ path leak")

    # 7. the search index carries the tags (WO-69) ---------------------------
    # A tag on a place page and a tag in a result card must be the same tag:
    # the index row's `t` ints resolve through search_tables.json to exactly
    # the slugs the record earned, and the 🔍 beside each pill opens the
    # search filtered to that tag.
    idx_p = DOCS / "data" / "index.json"
    tab_p = DOCS / "data" / "search_tables.json"
    if not idx_p.exists() or not tab_p.exists():
        fail(msgs, "data/index.json or data/search_tables.json missing (WO-69)")
    else:
        tab = json.loads(tab_p.read_text())
        by_id = {e["id"]: e for e in json.loads(idx_p.read_text())}
        slug_of = [row[0] for row in tab.get("tags", [])]
        n_t = sum(1 for e in by_id.values() if e.get("t"))
        print(f"index rows with t  {n_t:,}")
        for r in rnd.sample(tagged, min(60, len(tagged))):
            e = by_id.get(r["id"])
            if not e:
                continue        # held, or otherwise out of the ranked index
            got = sorted(slug_of[i] for i in (e.get("t") or []) if i < len(slug_of))
            want = sorted(r["tags"])
            if got != want:
                fail(msgs, f"{r['id']}: index t={got} but the record earned {want}")
        for r in sample[:10]:
            s = r["tags"][0]
            tj = DOCS / "data" / "tags" / f"{r['province']}-{s}.json"
            if not tj.exists():
                continue
            hit = next((x for x in json.loads(tj.read_text())["places"] if x["id"] == r["id"]), None)
            if not hit:
                continue
            pg = DOCS / hit["url"].split("motdang.net/", 1)[1]
            if pg.exists() and 'class="tagseek"' not in pg.read_text():
                fail(msgs, f"{pg.relative_to(DOCS)}: tag pills carry no 🔍 search link")

    for m in msgs[:40]:
        print("  !", m)
    if len(msgs) > 40:
        print(f"  ... and {len(msgs) - 40} more")
    print("PASS" if not msgs else f"FAIL ({len(msgs)})")
    return 0 if not msgs else 1


if __name__ == "__main__":
    sys.exit(main())
