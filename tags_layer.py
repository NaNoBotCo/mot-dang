#!/usr/bin/env python3
"""🏷 Tags — the cross-shelf layer (WO-15).

A shelf answers *what kind of place is this* — one branch of the tree. A facet
answers *is THAT branch worth walking to* — the per-shelf ticks an owner can
set. A tag answers *what is this place ALSO*, across every shelf: vegan,
bitcoin, wifi, wheelchair, open 24 h, inside the moat, 7-Eleven, royal temple.
Each tag is a page a reader lands on for "vegan chiang mai" — the queries the
tree cannot answer and the ones this directory can win, because the list is
exhaustive over data only it holds.

Three rules, none of them new here:

1. **A tag is derived, never typed.** `data/tags.json` gives each tag ONE rule
   over a field the record already carries (an attrs value, a facet key, the
   honours list, the moat polygon). No tag without a rule; no rule without a
   source field. The vocabulary was mined from the catalogue before a line of
   this was written — a tag exists only where the data already answers for it.
2. **Provenance travels.** Every assignment remembers how it was earned
   (`tagVia`), the pill's tooltip says so, and `data/places.json` carries both.
3. **Empty is hidden by design.** A tag page renders only from `min_tag`
   records in a province; a tag×shelf page only from `tag_shelf_min`. Counts on
   every page are of records a reader can see.

Brand tags are generated at build from `attrs.brand` via build._brand_index —
the corpus's own say-so about which spellings are one chain — so a chain the
crawl meets next month gets its page without anyone editing a list.

Entry points, in the order build.py calls them:
    assign(g, data)        after load(): computes every record's tags → g["TAGS"]
    pills(g, r)            the row of tag links on a place page
    search_words(g, r)     the tag words folded into the search index's `k`
    emit(g, data)          the pages + data exports, before the sitemap
"""
import collections
import json
import unicodedata
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TAGS_PATH = ROOT / "data" / "tags.json"
CURATED_PATH = ROOT / "data" / "curated" / "tags_curated.json"

# How a tag was earned, in the reader's two languages. Keyed by the head of the
# `tagVia` string; facet sources reuse build's own FACET_SRC_NOTE wording.
VIA_NOTE = {
    "attr": ("จากข้อมูลที่บันทึกไว้ของที่นี่เอง (OpenStreetMap หรือทะเบียน)",
             "from this place's own recorded fields (OpenStreetMap or a register)"),
    "moat": ("คำนวณจากหมุดกับแนวคูเมือง", "computed from the pin and the moat outline"),
    "honours": ("จากรายการเกียรติที่เก็บด้วยมือ มีแหล่งอ้างอิงทุกรายการ",
                "from the hand-kept honours list — every entry has a source"),
    "brand": ("จากป้ายแบรนด์ที่บันทึกไว้", "from the brand tag on the record"),
    "curated": ("คัดด้วยมือโดยทีมมดแดง", "curated by the Mot Dang team"),
    "facet:field": ("มีคนไปดูมาเอง", "checked by a person"),
    "facet:osm-near": ("จากแผนที่ OpenStreetMap ที่ปักไว้ใกล้ร้าน",
                       "an OpenStreetMap point beside the shop"),
    "facet:osm-tag": ("จากป้ายข้อมูลใน OpenStreetMap", "tagged in OpenStreetMap"),
}


def _doc():
    return json.loads(TAGS_PATH.read_text())


def _curated():
    if CURATED_PATH.exists():
        return json.loads(CURATED_PATH.read_text())
    return {}


def _tokens(v):
    """An attrs string value as casefolded tokens: OSM joins many values with
    ';' (cuisine=thai;japanese) and this must match either half."""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip().casefold() for x in v]
    return [t.strip().casefold() for t in str(v).split(";") if t.strip()]


def _in_poly(lat, lng, ring):
    """Ray casting over the moat quadrilateral — ring is [(lat, lng), ...]."""
    inside = False
    n = len(ring)
    for i in range(n):
        y1, x1 = ring[i]
        y2, x2 = ring[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            x_at = (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-12) + x1
            if lng < x_at:
                inside = not inside
    return inside


def _match(rule, r, a, fac, g):
    """Does this record earn this tag? Returns the `tagVia` string or None."""
    kind = rule.get("kind")
    if kind == "attr":
        key = rule["key"]
        toks = _tokens(a.get(key))
        hit = False
        if toks:
            vals = {v.casefold() for v in rule.get("values", [])}
            if vals and any(t in vals for t in toks):
                hit = True
            if not hit and rule.get("contains_any"):
                raw = " ".join(toks)
                nots = {v.casefold() for v in rule.get("not_values", [])}
                if raw not in nots and any(s in raw for s in rule["contains_any"]):
                    hit = True
        if hit:
            return f"attr:{key}"
        of = rule.get("or_facet")
        if of and of in fac:
            return f"facet:{fac[of]}:{of}"
        return None
    if kind == "attr-dict":
        d = a.get(rule["key"])
        if not isinstance(d, dict):
            return None
        if "sub" in rule:
            v = str(d.get(rule["sub"], "")).casefold()
            return f"attr:{rule['key']}:{rule['sub']}" if v in {x.casefold() for x in rule["values"]} else None
        for sub, vals in (rule.get("any") or {}).items():
            if str(d.get(sub, "")).casefold() in {x.casefold() for x in vals}:
                for usub, uvals in (rule.get("unless") or {}).items():
                    if str(d.get(usub, "")).casefold() in {x.casefold() for x in uvals}:
                        return None
                return f"attr:{rule['key']}:{sub}"
        return None
    if kind == "attr-list":
        toks = _tokens(a.get(rule["key"]))
        vals = {v.casefold() for v in rule["values"]}
        if any(t in vals for t in toks):
            return f"attr:{rule['key']}"
        of = rule.get("or_facet")
        if of and of in fac:
            return f"facet:{fac[of]}:{of}"
        return None
    if kind == "attr-true":
        return f"attr:{rule['key']}" if a.get(rule["key"]) is True else None
    if kind == "facet":
        k = rule["key"]
        return f"facet:{fac[k]}:{k}" if k in fac else None
    if kind == "moat":
        if a.get("inOldCity") is True:
            return "attr:inOldCity"
        ring = g.get("MOAT_POLY")
        if (ring and r.get("province") == "cm" and r.get("lat") is not None
                and (r.get("geoPrecision") or "exact") == "exact"
                and _in_poly(r["lat"], r["lng"], ring)):
            return "moat"
        return None
    if kind == "royal":
        return "honours:royal" if g["royal_of"](r) else None
    if kind == "food-award":
        pref = rule.get("prefix", "")
        for f in g["FOOD_BY_ID"].get(r["id"], []):
            if str(f.get("award", "")).startswith(pref):
                return "honours:food"
        return None
    return None


def _slug_of(text, g):
    """ASCII slug (git on macOS renormalises Unicode filenames — place_slug's
    rule). Accents are spelling, not identity: Café Amazon → cafe-amazon."""
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return g["_SLUG_UNSAFE"].sub("-", s.strip().lower()).strip("-")[:48].rstrip("-")


def _brand_tags(g, data, doc):
    """One tag per chain, from the corpus's own brand tags. Returns
    (defs_in_order, by_id_slug) — by_id maps record id → brand slug."""
    brand_index, fold_key, norm = g["_brand_index"], g["fold_key"], g["_norm_brand"]
    name_of, has_thai = g["name_of"], g["has_thai"]
    every = [r for p in g["PROVINCES"] for r in data[p["key"]]]
    alias = brand_index(every)
    groups = collections.defaultdict(list)
    for r in every:
        a = r.get("attrs") or {}
        has_brand = any((a.get(k) or "").strip() for k in ("brand", "brandTh", "brandEn"))
        if has_brand:
            key = fold_key(r, alias)
        else:
            nm = (r.get("name") or "").strip() or name_of(r)
            key = alias.get(norm(nm))
            if not key:
                continue
        groups[key].append(r)
    defs, by_id = [], {}
    taken = set()
    for key, rs in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(rs) < doc.get("brand_min", 5):
            continue
        thai, latin = key
        slug = _slug_of(latin, g) if latin else ""
        if not slug:
            qids = collections.Counter((r.get("attrs") or {}).get("brandWikidata")
                                       for r in rs if (r.get("attrs") or {}).get("brandWikidata"))
            slug = qids.most_common(1)[0][0].lower() if qids else "brand-%08x" % zlib.crc32(thai.encode("utf-8"))
        base, n = slug, 2
        while slug in taken:               # two chains slugging alike: number the second
            slug = f"{base}-{n}"; n += 1
        taken.add(slug)
        defs.append({"slug": slug, "family": "brand", "th": thai, "en": latin,
                     "glyph": "🏪", "rule": {"kind": "brand"}, "generated": True,
                     "branches": len(rs)})
        for r in rs:
            by_id[r["id"]] = slug
    return defs, by_id


def assign(g, data):
    """Every record's tags, once, before any page is drawn. Sets and returns
    g["TAGS"] = {defs, order, by_id, via, counts, families, min_tag, ...}."""
    doc = _doc()
    CLAIMS = g.get("CLAIMS") or {}
    defs = {t["slug"]: t for t in doc["tags"]}
    order = [t["slug"] for t in doc["tags"]]
    by_id = collections.defaultdict(list)
    via = collections.defaultdict(dict)
    counts = {p["key"]: collections.Counter() for p in g["PROVINCES"]}
    shelf_counts = {p["key"]: collections.defaultdict(collections.Counter) for p in g["PROVINCES"]}

    def take(r, slug, how):
        if slug in via[r["id"]]:
            return
        by_id[r["id"]].append(slug)
        via[r["id"]][slug] = how
        counts[r["province"]][slug] += 1
        for c in r.get("cat") or []:
            shelf_counts[r["province"]][slug][c] += 1

    # Curated outranks derived: a person's list is applied first, so the
    # provenance a record keeps for a curated tag is the person's.
    cur = _curated()
    for slug, spec in (cur.get("tags") or {}).items():
        if slug not in defs:
            defs[slug] = {"slug": slug, "family": spec.get("family", "place"),
                          "th": spec.get("th", slug), "en": spec.get("en", slug),
                          "glyph": spec.get("glyph", "🏷"), "rule": {"kind": "curated"},
                          "curated": True, "note_th": spec.get("note_th"), "note_en": spec.get("note_en")}
            order.append(slug)
    cur_ids = {}
    for slug, spec in (cur.get("tags") or {}).items():
        for pid in spec.get("ids") or []:
            cur_ids.setdefault(pid, []).append(slug)

    for p in g["PROVINCES"]:
        for r in data[p["key"]]:
            a = r.get("attrs") or {}
            fac = dict(a.get("facets") or {})
            for k in (CLAIMS.get(r["id"]) or {}).get("facets") or []:
                fac[k] = "field"
            for slug in cur_ids.get(r["id"], []):
                take(r, slug, f"curated:{slug}")
            for t in doc["tags"]:
                how = _match(t["rule"], r, a, fac, g)
                if how:
                    take(r, t["slug"], how)

    bdefs, b_by_id = _brand_tags(g, data, doc)
    for d in bdefs:
        if d["slug"] in defs:           # a hand-defined slug wins over a generated one
            d["slug"] = "brand-" + d["slug"]
        defs[d["slug"]] = d
        order.append(d["slug"])
    for p in g["PROVINCES"]:
        for r in data[p["key"]]:
            slug = b_by_id.get(r["id"])
            if slug:
                if ("brand-" + slug) in defs and slug not in defs:
                    slug = "brand-" + slug
                take(r, slug, "brand")

    g["TAGS"] = {"doc": doc, "defs": defs, "order": order, "by_id": dict(by_id),
                 "via": dict(via), "counts": counts, "shelf_counts": shelf_counts,
                 "min_tag": int(doc.get("min_tag", 3)),
                 "tag_shelf_min": int(doc.get("tag_shelf_min", 8))}
    return g["TAGS"]


def _via_note(how):
    head = how.split(":")[0]
    if head == "facet":
        src = how.split(":")[1] if ":" in how else ""
        return VIA_NOTE.get(f"facet:{src}", VIA_NOTE["attr"])
    return VIA_NOTE.get(head, VIA_NOTE["attr"])


def pills(g, r):
    """The row of tag links on a place page. Only tags whose province page
    exists are linked; the rest are still in places.json."""
    T = g.get("TAGS")
    if not T:
        return ""
    slugs = T["by_id"].get(r["id"]) or []
    if not slugs:
        return ""
    bi, att, esc = g["bi"], g["att"], g["esc"]
    prov = r["province"]
    out = []
    for slug in sorted(slugs, key=lambda s: T["order"].index(s) if s in T["order"] else 9999):
        d = T["defs"].get(slug)
        if not d or T["counts"][prov][slug] < T["min_tag"]:
            continue
        how = T["via"][r["id"]].get(slug, "attr")
        tip = " / ".join(_via_note(how))
        out.append(f'<a class="tag" href="../tag/{slug}.html" title="{att(tip)}">'
                   f'{esc(d["glyph"])} {bi(d["th"], d["en"])}</a>')
    if not out:
        return ""
    return (f'<p class="tagrow"><span class="taglabel">🏷 {bi("ป้ายกำกับ", "Tags")}</span> '
            + " ".join(out) + "</p>")


def search_words(g, r):
    """Both names of every tag this place earned — matched by search, never
    shown, so "vegan" finds the cafés that only say so in a diet tag."""
    T = g.get("TAGS")
    if not T:
        return ""
    words = []
    for slug in T["by_id"].get(r["id"]) or []:
        d = T["defs"].get(slug)
        if d:
            words += [d["th"], d["en"]]
    return " ".join(dict.fromkeys(w for w in words if w))


def _rule_words(d):
    """What the tag means, in plain words for the page lede."""
    k = d["rule"].get("kind")
    if k == "brand":
        return ("ทุกสาขาที่บันทึกไว้ว่าเป็นเครือนี้ — จากป้ายแบรนด์ในข้อมูลของแต่ละที่",
                "Every branch the catalogue records as this chain — read from the brand tag on each record.")
    if k == "moat":
        return ("ที่ที่หมุดอยู่ภายในแนวคูเมืองเชียงใหม่ (สี่แจ่ง) — คำนวณจากพิกัด ไม่ได้พิมพ์ใส่เอง",
                "Places whose pin lies inside the Chiang Mai moat quadrilateral — computed from the coordinates, never typed.")
    if k == "royal":
        return ("วัดที่อยู่ในรายการพระอารามหลวงที่มดแดงเก็บด้วยมือ ทุกรายการมีแหล่งอ้างอิง",
                "Temples on the royal-temple list this site keeps by hand — every entry with a fetched source.")
    if k == "food-award":
        return ("ร้านที่มีเครื่องหมายในรายการเกียรติด้านอาหาร ทุกรายการมีแหล่งอ้างอิงและปีที่ได้",
                "Places carrying a food mark on the honours list — each with its source and the year it was awarded.")
    if k == "facet":
        return ("จากป้ายข้อมูลของแต่ละที่ หรือจากเจ้าของที่ติ๊กยืนยันเอง",
                "From each place's own recorded tags, or from an owner who ticked it themselves.")
    if k == "curated":
        return (d.get("note_th") or "รายการที่คัดด้วยมือโดยทีมมดแดง",
                d.get("note_en") or "A list kept by hand by the Mot Dang team.")
    return ("จากข้อมูลที่บันทึกไว้ของแต่ละที่เอง (OpenStreetMap หรือทะเบียน) — มีเท่าที่รู้ ไม่ได้แปลว่าที่อื่นไม่มี",
            "From each place's own recorded fields (OpenStreetMap or a register) — what we know of, not what the others lack.")


def emit(g, data):
    T = g.get("TAGS") or assign(g, data)
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    DOCS, BASE = g["DOCS"], g["BASE"]
    entry_li, shelf_map, toolbar = g["entry_li"], g["shelf_map"], g["toolbar"]
    share_block, ad_box = g["share_block"], g["ad_box"]
    breadcrumb_ld, item_list_ld = g["breadcrumb_ld"], g["item_list_ld"]
    listing_page, geojson = g["listing_page"], g["geojson"]
    CATS, CAT_ORDER, PROVINCES = g["CATS"], g["CAT_ORDER"], g["PROVINCES"]
    name_of, is_featured = g["name_of"], g["is_featured"]
    BUILD_DATE = g["BUILD_DATE"]
    defs, order = T["defs"], T["order"]
    fams = {f["key"]: f for f in T["doc"]["families"]}
    fam_order = [f["key"] for f in T["doc"]["families"]]

    # Which records carry which tag, per province, in one pass.
    members = {p["key"]: collections.defaultdict(list) for p in PROVINCES}
    for p in PROVINCES:
        for r in data[p["key"]]:
            for slug in T["by_id"].get(r["id"]) or []:
                members[p["key"]][slug].append(r)

    n_pages = n_cross = 0
    export = []
    (DOCS / "data" / "tags").mkdir(parents=True, exist_ok=True)

    def ordered(recs):
        # Shelf order first (the page groups by shelf), featured, then name —
        # and the SAME order goes to shelf_map, whose dots point at row indexes.
        def k(r):
            cats = r.get("cat") or []
            ci = min((CAT_ORDER.index(c) for c in cats if c in CAT_ORDER), default=999)
            return (ci, not is_featured(r), name_of(r))
        return sorted(recs, key=k)

    for p in PROVINCES:
        key = p["key"]
        tdir = DOCS / key / "tag"
        tdir.mkdir(parents=True, exist_ok=True)
        for slug in order:
            recs = members[key].get(slug) or []
            d = defs[slug]
            if len(recs) < T["min_tag"]:
                continue
            recs = ordered(recs)
            # Plain-text forms for <title>, desc, crumbs-ld and share text: a
            # chain with one sign has one name, so either half may be empty and
            # the other stands in. Display goes through bi(), which copes.
            t_th, t_en = (d["th"] or d["en"]), (d["en"] or d["th"])
            fam = fams.get(d["family"], {"th": d["family"], "en": d["family"], "glyph": "🏷"})
            path = f"{key}/tag/{slug}.html"
            # Rows grouped by shelf — each record ONCE, under its first shelf,
            # so the page is a partition a reader can add up — with a heading
            # per shelf that names it and links to it. The tag×shelf page is a
            # different question ("every wifi place that is ALSO on the food
            # shelf"), so its membership is ANY shelf the record stands on:
            # a pharmacy shelved under essentials and medical belongs on
            # wifi--medical even though it is filed once, under essentials,
            # on this page. Its link appears on whichever heading it has.
            rows, cross = [], []
            by_cat = collections.OrderedDict()
            for r in recs:
                c = next((c for c in (r.get("cat") or []) if c in CATS), (r.get("cat") or ["?"])[0])
                by_cat.setdefault(c, []).append(r)
            x_members = {}
            for r in recs:
                for c in (r.get("cat") or []):
                    if c in CATS:
                        x_members.setdefault(c, []).append(r)
            for c, rs in x_members.items():
                if len(rs) >= T["tag_shelf_min"]:
                    cross.append((c, rs, f"{key}/tag/{slug}--{c}.html"))
            has_cross = {c for c, _, _ in cross}
            for c, rs in by_cat.items():
                cdef = CATS.get(c, {"th": c, "en": c})
                head = (f'<a href="../{c}/index.html">{bi(cdef["th"], cdef["en"])}</a>'
                        if c in CATS else esc(c))
                xlink = ""
                if c in has_cross:
                    xn = len(x_members[c])
                    xlink = (f' · <a class="xshelf" href="{slug}--{c}.html">'
                             + bi("ดูเฉพาะหมวดนี้", "just this shelf")
                             + (f" ({xn:,})" if xn != len(rs) else "") + "</a>")
                rows.append(f'<li class="shelf areahead">{head} '
                            f'<span class="count">{len(rs):,}</span>{xlink}</li>')
                rows += [entry_li(r, f"../p/{g['place_slug'](r)}.html") for r in rs]
            # A tag×shelf page whose shelf is nobody's first shelf here (every
            # open-late pharmacy is filed under essentials first) still needs a
            # door from this page, or it is reachable from the sitemap alone.
            orphan = [c for c in has_cross if c not in by_cat]
            if orphan:
                links = " · ".join(
                    f'<a class="xshelf" href="{slug}--{c}.html">{bi(CATS[c]["th"], CATS[c]["en"])} '
                    f'<span class="count">{len(x_members[c]):,}</span></a>' for c in orphan)
                rows.append(f'<li class="shelf areahead">'
                            + bi("ยืนอยู่บนหมวดอื่นด้วย", "Also standing on other shelves")
                            + f": {links}</li>")
            rule_th, rule_en = _rule_words(d)
            also = ""
            if d.get("also"):
                links = " · ".join(
                    f'<a href="{att(x["url"])}" rel="noopener nofollow">{esc(x["name"])}</a>'
                    for x in d["also"])
                also = (f'<p class="tinynote tagalso">'
                        + bi("ที่อื่นที่เก็บเรื่องนี้ไว้ด้วย", "Also catalogued by")
                        + f": {links}</p>")
            gj = geojson(recs)
            gj_name = f"{key}-tag-{slug}.geojson"
            (DOCS / "data" / gj_name).write_text(json.dumps(gj, ensure_ascii=False))
            dl = (f'<p class="prov"><a href="../../data/{gj_name}">⬇ GeoJSON</a> '
                  f'({len(gj["features"]):,} {bi("จุด", "points")}) · '
                  f'<a href="../../data/tags/{key}-{slug}.json">JSON</a></p>')
            title_th = f'{t_th} {p["th"]}'
            crumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
                      f'<a href="../../tags.html">{bi("ป้ายกำกับ", "Tags")}</a> › '
                      f'<a href="../index.html">{bi(p["th"], p["en"])}</a> › {bi(d["th"], d["en"])}')
            bc = breadcrumb_ld([("หน้าแรก", BASE), ("ป้ายกำกับ", BASE + "tags.html"),
                                (p["th"], BASE + key + "/index.html"), (t_th, BASE + path)])
            body = (f'<h1>{esc(d["glyph"])} {bi(d["th"], d["en"])} '
                    f'<span class="count">({len(recs):,})</span></h1>'
                    f'<p class="tinynote tagfam">🏷 {bi(fam["th"], fam["en"])} · '
                    + bi("ป้ายกำกับข้ามหมวด", "a cross-shelf tag") + "</p>"
                    f'<p class="taglede">{bi(rule_th, rule_en)}</p>{also}'
                    f'{ad_box(path, 2)}'
                    f'{shelf_map(recs, "tag-" + slug, p, label_th=t_th, label_en=t_en)}'
                    f'{toolbar(recs)}'
                    f'<ul class="dir" data-sortable>{"".join(rows)}</ul>{dl}'
                    f'{share_block(BASE + path, title_th)}')
            (tdir / f"{slug}.html").write_text(page(
                f'{title_th} · {t_en}, {p["en"]}', body, depth=2, crumbs=crumbs,
                path=path,
                desc=f'{t_th} {p["th"]} — {len(recs)} แห่ง · {t_en}, {p["en"]} · มดแดง',
                extra_head=bc + item_list_ld(recs, key)))
            n_pages += 1
            (DOCS / "data" / "tags" / f"{key}-{slug}.json").write_text(json.dumps({
                "tag": slug, "province": key, "th": d["th"], "en": d["en"],
                "family": d["family"], "count": len(recs), "generated": BUILD_DATE,
                "page": BASE + path,
                "places": [{"id": r["id"], "name": name_of(r),
                            "url": BASE + f"{key}/p/{g['place_slug'](r)}.html",
                            "via": T["via"][r["id"]].get(slug)} for r in recs]},
                ensure_ascii=False))
            # tag × shelf, only where the crowd is real.
            for c, rs, xpath in cross:
                cdef = CATS[c]
                xt_th = f'{t_th} · {cdef["th"]}'
                xt_en = f'{t_en} · {cdef["en"]}'
                xcrumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
                           f'<a href="../../tags.html">{bi("ป้ายกำกับ", "Tags")}</a> › '
                           f'<a href="{slug}.html">{bi(d["th"], d["en"])}</a> › '
                           f'<a href="../{c}/index.html">{bi(cdef["th"], cdef["en"])}</a>')
                xbc = breadcrumb_ld([("หน้าแรก", BASE), ("ป้ายกำกับ", BASE + "tags.html"),
                                     (t_th, BASE + path), (cdef["th"], BASE + xpath)])
                # No map here on purpose: listing_page folds brand rows into
                # <details> shelves, which reorders the DOM rows the map's dot
                # indexes point at. The parent tag page carries the map over
                # the full list, in an order it controls.
                lede = (f'<p class="taglede">{bi(rule_th, rule_en)}</p>'
                        f'<p class="tinynote"><a href="{slug}.html">← '
                        + bi(f"ทุกหมวดของ {t_th}", f"all shelves for {t_en}")
                        + f' ({len(recs):,})</a></p>')
                (tdir / f"{slug}--{c}.html").write_text(listing_page(
                    xt_th, xt_en, ordered(rs), depth=2, prov=key, crumbs=xcrumbs, path=xpath,
                    extra_top=lede, extra_head=xbc + item_list_ld(rs, key),
                    seo_title=f'{xt_th} {p["th"]}',
                    seo_title_en=f'{xt_en}, {p["en"]}'))
                n_cross += 1

    # ---- /tags.html: the index, Yahoo-style — Tag (count) by family ---------
    sections = []
    for fk in fam_order:
        f = fams[fk]
        items = []
        for slug in order:
            d = defs[slug]
            if d["family"] != fk:
                continue
            links = []
            for p in PROVINCES:
                n = T["counts"][p["key"]][slug]
                if n >= T["min_tag"]:
                    links.append(f'<a href="{p["key"]}/tag/{slug}.html">{bi(p["th"], p["en"])} '
                                 f'<span class="count">({n:,})</span></a>')
            if not links:
                continue
            items.append(f'<li>{esc(d["glyph"])} <b>{bi(d["th"], d["en"])}</b> — '
                         + " · ".join(links) + "</li>")
        if items:
            sections.append(f'<h2 id="{fk}">{esc(f["glyph"])} {bi(f["th"], f["en"])} '
                            f'<span class="count">({len(items)})</span></h2>'
                            f'<ul class="dir tagidx">{"".join(items)}</ul>')
    total_pages = n_pages
    lede_th = ("หมวดบอกว่าที่นี่เป็นร้านแบบไหน ป้ายกำกับบอกว่าที่นี่ *ยังเป็น* อะไรอีก — ข้ามทุกหมวด: "
               "มีอาหารวีแกน รับบิตคอยน์ มีไวไฟ รถเข็นเข้าได้ เปิด 24 ชั่วโมง อยู่ในคูเมือง เป็นสาขาเซเว่น "
               "ทุกป้ายคำนวณจากข้อมูลที่แต่ละที่บันทึกไว้เองตามกฎข้อเดียวต่อป้าย ไม่มีใครพิมพ์ใส่ "
               "และทุกหน้านับเฉพาะที่ที่มีจริงในสารบัญ")
    lede_en = ("A shelf says what kind of place this is; a tag says what it ALSO is, across every shelf — "
               "vegan options, takes bitcoin, has Wi-Fi, wheelchair access, open 24 hours, inside the moat, "
               "a 7-Eleven branch. Every tag is worked out from each place's own recorded fields by one "
               "stated rule; nothing is typed on, and every page counts only places the directory holds.")
    how_th = ("ป้ายที่มีน้อยกว่า %d แห่งในจังหวัดยังไม่ได้เปิดหน้า — ไม่ใช่ว่าไม่มี แค่ยังไม่พอจะเป็นหน้า "
              "ชี้เมาส์ที่ป้ายบนหน้าร้านใด ๆ จะบอกว่าป้ายนั้นมาจากไหน" % T["min_tag"])
    how_en = ("A tag with fewer than %d places in a province has no page yet — not absent, just not yet "
              "a page. Point at any tag on a place page to see where it came from." % T["min_tag"])
    body = (f'<h1>🏷 {bi("ป้ายกำกับ", "Tags")} <span class="count">({total_pages:,})</span></h1>'
            f'<p class="myhint">{bi(lede_th, lede_en)}</p>'
            + "".join(sections)
            + f'<p class="tinynote">{bi(how_th, how_en)} · '
            f'<a href="data/tags.json">data/tags.json</a></p>'
            + share_block(BASE + "tags.html", "ป้ายกำกับ · มดแดง"))
    (DOCS / "tags.html").write_text(page(
        "ป้ายกำกับ", body, depth=0, path="tags.html",
        desc="ป้ายกำกับข้ามหมวดของมดแดง — วีแกน บิตคอยน์ ไวไฟ รถเข็น เปิด 24 ชม. ในคูเมือง แบรนด์ · Tags across every shelf",
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("ป้ายกำกับ", "Tags")}'))

    # ---- data/tags.json: the definitions with live counts and page urls ----
    for slug in order:
        d = defs[slug]
        row = {"slug": slug, "family": d["family"], "th": d["th"], "en": d["en"],
               "glyph": d["glyph"], "rule": d["rule"],
               "counts": {p["key"]: T["counts"][p["key"]][slug] for p in PROVINCES},
               "pages": {p["key"]: BASE + f'{p["key"]}/tag/{slug}.html'
                         for p in PROVINCES if T["counts"][p["key"]][slug] >= T["min_tag"]}}
        if d.get("also"):
            row["also"] = d["also"]
        if d.get("generated"):
            row["generated"] = True
        export.append(row)
    (DOCS / "data" / "tags.json").write_text(json.dumps({
        "generated": BUILD_DATE, "min_tag": T["min_tag"], "tag_shelf_min": T["tag_shelf_min"],
        "note": "A tag is derived by exactly one rule from a field the record carries; "
                "`tags` and `tagVia` on each record in places.json say which and how. "
                "Counts are per province; a tag under min_tag has no page.",
        "families": T["doc"]["families"], "tags": export}, ensure_ascii=False, indent=1))
    tagged = sum(1 for v in T["by_id"].values() if v)
    return (f"{n_pages} tag pages + {n_cross} tag×shelf pages, {len(order)} tags defined "
            f"({sum(1 for s in order if defs[s].get('generated'))} brands), {tagged:,} records tagged")


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. Run: python3 build.py")
