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
import re
import unicodedata
import zlib
from pathlib import Path

import tags_mine

ROOT = Path(__file__).resolve().parent
TAGS_PATH = ROOT / "data" / "tags.json"
CURATED_PATH = ROOT / "data" / "curated" / "tags_curated.json"
LABELS_PATH = ROOT / "data" / "curated" / "tag_labels.json"

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
    "mined": ("จากค่าที่บันทึกไว้ในข้อมูลของที่นี่เอง", "from a value recorded on this place's own entry"),
    # the street a record is matched to (build.STREET_OF), stated in its
    # address or the nearest road line to its pin — not a field it carries
    "mined:streets.json": ("จากถนนที่จับคู่ไว้กับที่นี่", "from the road this place is matched to"),
    "field": ("จากช่องข้อมูลที่สารบัญนี้มีหรือยังไม่มี", "from which fields this catalogue holds for it"),
    "hours": ("อ่านจากเวลาเปิด-ปิดที่บันทึกไว้", "read from the recorded opening hours"),
    "name": ("อ่านจากชื่อที่ร้านตั้งเอง", "read from the name the place gave itself"),
    "facet:field": ("มีคนไปดูมาเอง", "checked by a person"),
    "facet:osm-near": ("จากแผนที่ OpenStreetMap ที่ปักไว้ใกล้ร้าน",
                       "an OpenStreetMap point beside the shop"),
    "facet:osm-tag": ("จากป้ายข้อมูลใน OpenStreetMap", "tagged in OpenStreetMap"),
    # Nan's word (data/curated/aircon_stated.json). The page names no source
    # for it: her rule for the toilet facts, 2026-09-23.
    "facet:said": ("", ""),
}


def _doc():
    return json.loads(TAGS_PATH.read_text())


def _labels():
    if LABELS_PATH.exists():
        return json.loads(LABELS_PATH.read_text())
    return {}


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
    if kind == "field":
        # Presence/absence of fields the RECORD carries. This family describes
        # the entry, not the shop: `stub` says the catalogue holds little about
        # a place, never that the place is little.
        def present(name):
            if name == "pin":
                return r.get("lat") is not None and (r.get("geoPrecision") or "exact") == "exact"
            if name.startswith("attrs."):
                return bool(a.get(name.split(".", 1)[1]))
            return bool(r.get(name))
        ms = rule.get("min_sources")
        if ms is not None:
            # OUR OWN DERIVATIONS DO NOT CORROBORATE ANYTHING. The tag this
            # serves says "more than one source agrees", and a `derived` row —
            # an address we parsed, a pin we geocoded — agrees with the source
            # it was computed from by construction. Counting it would have put
            # that claim on 31,365 records the day derive.py started writing
            # its source row (2026-09-08), and it is already wrong on the 180
            # that carry derived:geocode_local.
            outside = [x for x in (r.get("sources") or [])
                       if (x.get("type") or "") != "derived"]
            return "field:sources" if len(outside) >= int(ms) else None
        need = rule.get("need") or []
        lack = rule.get("lack") or []
        of = rule.get("of")
        if need and not all(present(x) for x in need):
            return None
        if lack and any(present(x) for x in lack):
            return None
        if of is not None:
            cap = rule.get("max_present")
            n = sum(1 for x in of if present(x))
            if cap is not None and n > int(cap):
                return None
            lo = rule.get("min_present")
            if lo is not None and n < int(lo):
                return None
        if not (need or lack or of):
            return None
        return "field:" + (",".join(need or lack or ["count"]))[:40]
    if kind == "hours":
        hit = _hours_match(rule, r.get("hours"))
        if hit:
            return hit
        of = rule.get("or_facet")
        if of and of in fac:
            return f"facet:{fac[of]}:{of}"
        return None
    if kind == "mined":
        # Assigned in bulk by tags_mine.mine_all(), not one record at a time.
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


_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def _hours_spans(text):
    """(days, open_min, close_min) triples out of an OSM opening_hours string.

    Deliberately small: it reads the shapes the corpus actually holds —
    "Mo-Su 08:00-20:00", "24/7", ";"-joined rules, ","-joined day lists and
    time ranges. Anything it cannot read earns no tag, which is the fitting
    outcome: an unparsed string is not a closed shop.
    """
    if not text or not isinstance(text, str):
        return []
    out = []
    # ";" is the OSM separator; a newline is what a person typed instead.
    for rule in re.split(r"[;\n\r]+", text):
        rule = rule.strip()
        if not rule:
            continue
        if rule.lower().startswith("24/7"):
            out.append((set(_DAYS), 0, 24 * 60))
            continue
        m = re.match(r"^([A-Za-z,\- ]*?)\s*([\d:\-, ]*)$", rule) or re.match(
            r"^([A-Za-z,\-]*)\s*(.*)$", rule, re.S)
        daypart, timepart = ((m.group(1) or "").strip(), (m.group(2) or "").strip()) if m else ("", rule)
        days = set()
        for chunk in [c for c in daypart.split(",") if c.strip()]:
            chunk = chunk.strip()
            if "-" in chunk:
                a, b = [x.strip()[:2].title() for x in chunk.split("-", 1)]
                if a in _DAYS and b in _DAYS:
                    i, j = _DAYS.index(a), _DAYS.index(b)
                    days |= set(_DAYS[i:j + 1] if i <= j else _DAYS[i:] + _DAYS[:j + 1])
            elif chunk[:2].title() in _DAYS:
                days.add(chunk[:2].title())
        if not days:
            days = set(_DAYS)          # a bare time range means every day
        if "off" in timepart.lower() or "closed" in timepart.lower():
            continue
        for a, b in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", timepart):
            ah, am = [int(x) for x in a.split(":")]
            bh, bm = [int(x) for x in b.split(":")]
            o, c = ah * 60 + am, bh * 60 + bm
            if c <= o:
                c += 24 * 60           # past midnight
            out.append((days, o, c))
    return out


def _hours_match(rule, text):
    spans = _hours_spans(text)
    if not spans:
        return None
    sh = rule.get("spans_hours")
    if sh and not any((c - o) >= int(sh) * 60 for _, o, c in spans):
        return None
    wd = rule.get("weekday")
    if wd and not any(wd in d for d, _, _ in spans):
        return None
    ca = rule.get("closes_after")
    if ca:
        h, m = [int(x) for x in ca.split(":")]
        if not any(c >= h * 60 + m for _, _, c in spans):
            return None
    ob = rule.get("opens_before")
    if ob:
        h, m = [int(x) for x in ob.split(":")]
        if not any(o <= h * 60 + m for _, o, _ in spans):
            return None
    return "hours"


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
    # A WORD THAT NAMES A KIND OF PLACE IS NOT A CHAIN. The corpus holds
    # records whose attrs.brand is "Restaurant", "Pharmacy", "Viewpoint" or
    # "ตู้น้ำดื่มหยอดเหรียญ" — a category typed into a brand box. Left alone
    # they mint a chain tag that says six unrelated shops are branches of one
    # another, and they hold the good slug against the tag that means the kind.
    skip = {str(x).strip().casefold() for x in (doc.get("brand_skip") or [])}
    skip |= {t["slug"] for t in doc.get("tags", [])}
    for key, rs in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(rs) < doc.get("brand_min", 5):
            continue
        thai, latin = key
        if (str(latin).strip().casefold() in skip or str(thai).strip().casefold() in skip
                or _slug_of(latin, g) in skip):
            continue
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


# THE CAUTIOUS READING WINS. Merged sources disagree: one says wheelchair=yes,
# another limited (attrs.wheelchair "yes;limited"), or the OSM facet says
# wheelchair while the attr says limited — and the record wore both "Wheelchair
# accessible" and "Wheelchair — partly" on one row. A record gets one. The
# partial tag stands over the full one, because a reader who arrives in a chair
# and meets a step is worse off than one who finds a ramp nobody promised.
# Key: the tag that stands; value: the tags it puts down.
CAUTIOUS = {"wheelchair-limited": ("wheelchair",)}


def _cautious(hits):
    """[(slug, how)] with the tags a more cautious sibling puts down removed."""
    won = {slug for slug, _ in hits}
    down = set()
    for slug, losers in CAUTIOUS.items():
        if slug in won:
            down.update(losers)
    return [(slug, how) for slug, how in hits if slug not in down]


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
            hits = []
            for t in doc["tags"]:
                how = _match(t["rule"], r, a, fac, g)
                if how:
                    hits.append((t["slug"], how))
            for slug, how in _cautious(hits):
                take(r, slug, how)

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

    # 🏷 CO-OCCURRENCE (WO-76). Discovery is the other half of tagging: a tag
    # page that only lists its own members is a dead end, and a reader who has
    # arrived at "coin laundry" has told us more than one thing about what they
    # want. `pairs` holds, per province and per tag, the tags its members most
    # often ALSO carry — each of which is a door: search.html?tag=a&tag=b is
    # already a real AND filter (build.py's F.tag loop), so every chip is a
    # narrower list that exists, with its count on it before it is clicked.
    # 🏷 MINED (WO-76): one tag per value the corpus's own categorical fields
    # already carry — see tags_mine.py for why the hand list could not keep up.
    every = [r for p2 in g["PROVINCES"] for r in data[p2["key"]]]
    # `defs` rather than its keys: the miner needs the FAMILY of what is
    # already taken, so a mined value can only join a tag that means the same
    # kind of thing (see the note in tags_mine.mine).
    # THE SITE'S OWN WORDS FIRST. tags_mine's docstring has always said a mined
    # label comes from the hand-written file, then the shelf labels, then the
    # value — but nothing ever handed it the shelf labels, so 180 sub-shelf
    # tags arrived as "Hotel full" and "Bakery dessert" with no Thai at all.
    # SUB_LABELS is what the shelf pages themselves are titled with.
    lab = dict(_labels())
    subs = {k: {"th": v.get("th"), "en": v.get("en")}
            for k, v in (g.get("SUB_LABELS") or {}).items() if v.get("th") or v.get("en")}
    if subs:
        merged = dict(lab.get("sub") or {})
        for k, v in subs.items():
            merged.setdefault(k, v)
        lab["sub"] = merged
    # THE ROAD IS THE MATCHED ROAD. A place build.STREET_OF has put on
    # ถนนราชดำเนิน was minting "on-ratdanoen" off its own address string as
    # well, so one page said the road three ways — tag, street chip, road row.
    # Matched records mint the street tag from the street record (its slug and
    # both names), so tag and chip are the same words; the address string is
    # read only where no match exists.
    street_of = {}
    for pid, hit in (g.get("STREET_OF") or {}).items():
        st = hit[0] if isinstance(hit, tuple) else hit
        if st and st.get("slug"):
            street_of[pid] = {"value": st["slug"], "slug": st["slug"],
                              "th": st.get("name") or "", "en": st.get("nameEn") or "",
                              "source": "streets.json"}
    mdefs, m_by_id, m_gaps, m_src, m_also = tags_mine.mine_all(
        every, doc, lab, taken=defs, matched={"street": street_of})
    for d in mdefs:
        defs[d["slug"]] = d
        order.append(d["slug"])
    # A hand-written tag that mining handed records to says so on its own def,
    # so "every member carries the value" stays a question with an answer.
    for slug, also in m_also.items():
        if slug in defs:
            defs[slug]["earned_by"] = (defs[slug].get("earned_by") or []) + also
    for p2 in g["PROVINCES"]:
        for r in data[p2["key"]]:
            for slug in m_by_id.get(r["id"]) or []:
                # The source is looked up rather than read off the def: a
                # value mapped onto a hand-written tag (japanese_restaurant →
                # japanese) still came off attrs.overtureCategory, and the def
                # it landed on carries the hand rule.
                take(r, slug, "mined:" + (m_src.get(slug) or "field"))

    # 🏷 BY NAME (2026-09-08, Nan: "tag every record you can — make tags
    # prolific. Some tags can/should be inferred"). Every tag above was minted
    # from a field; a name is a field too, and in this catalogue it is usually
    # the shop's own description of itself. A tag may only be read off a name
    # on a shelf where the field-earned members of that same tag already stand
    # — see tags_mine.earn_by_name for the two guards and why they are those.
    nspec = doc.get("name_tags") or {}
    if nspec:
        named = tags_mine.earn_by_name(every, defs, dict(by_id), nspec,
                                       lambda r: r.get("cat") or [])
        for p2 in g["PROVINCES"]:
            for r in data[p2["key"]]:
                for slug, word in named.get(r["id"]) or []:
                    take(r, slug, "name:" + word)

    # A mined tag whose floor was cleared across the two provinces together but
    # not inside either one would be defined and never drawn — the shape
    # tests/test_tags.py calls a quiet zero. Drop it here rather than carry it.
    prov_keys = [p2["key"] for p2 in g["PROVINCES"]]
    thin = [d["slug"] for d in mdefs
            if max(counts[k][d["slug"]] for k in prov_keys) < int(doc.get("min_tag", 3))]
    for slug in thin:
        del defs[slug]
        order.remove(slug)
        for k in prov_keys:
            counts[k].pop(slug, None)
            shelf_counts[k].pop(slug, None)
    if thin:
        thin_set = set(thin)
        for pid in list(by_id):
            keep = [x for x in by_id[pid] if x not in thin_set]
            if keep:
                by_id[pid] = keep
            else:
                del by_id[pid]
            for x in thin_set:
                via[pid].pop(x, None)

    #
    # RANKED BY LIFT, NOT BY COUNT. Ranked by count, every rail on the site
    # read "also: has a phone number (44,007)" — true, useless, and the same
    # three chips on all 1,840 pages. Lift asks the other question: of the
    # places carrying THIS tag, how much more often than the province at large
    # do they also carry that one. Coin laundries come back paired with coin
    # washing machines and 24-hour opening, not with Facebook.
    #
    # Families flagged `rails: false` are left out entirely: `state` describes
    # the entry, and "this record also has a website" is not a door.
    no_rail = {f["key"] for f in doc["families"] if f.get("rails") is False}
    pairs = {}
    for p2 in g["PROVINCES"]:
        key = p2["key"]
        co = collections.defaultdict(collections.Counter)
        pool = [s2 for s2 in defs if defs[s2]["family"] not in no_rail]
        railable = set(pool)
        tot = 0
        for r in data[key]:
            slugs = [s2 for s2 in (by_id.get(r["id"]) or []) if s2 in railable]
            if len(slugs) < 2 or len(slugs) > 40:
                continue                      # a 40-tag record pairs nothing usefully
            tot += 1
            for i, a1 in enumerate(slugs):
                for b1 in slugs[i + 1:]:
                    co[a1][b1] += 1
                    co[b1][a1] += 1
        cnt = counts[key]
        n_all = max(len(data[key]), 1)
        out = {}
        for a1, row in co.items():
            ca = max(cnt[a1], 1)
            scored = []
            for b1, n2 in row.items():
                if n2 < 3:
                    continue        # two places sharing a tag is a coincidence
                cb = max(cnt[b1], 1)
                lift = (n2 / ca) / (cb / n_all)
                scored.append((lift, n2, b1))
            scored.sort(reverse=True)
            out[a1] = [(b1, n2) for _, n2, b1 in scored[:24]]
        pairs[key] = out

    g["TAGS"] = {"doc": doc, "defs": defs, "mined_gaps": m_gaps, "pairs": pairs, "order": order, "by_id": dict(by_id),
                 "via": dict(via), "counts": counts, "shelf_counts": shelf_counts,
                 "min_tag": int(doc.get("min_tag", 3)),
                 "tag_shelf_min": int(doc.get("tag_shelf_min", 8))}
    return g["TAGS"]


def _via_note(how):
    head = how.split(":")[0]
    if head == "facet":
        src = how.split(":")[1] if ":" in how else ""
        return VIA_NOTE.get(f"facet:{src}", VIA_NOTE["attr"])
    return VIA_NOTE.get(how) or VIA_NOTE.get(head, VIA_NOTE["attr"])


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
    hows = []
    # RAREST FIRST (WO-76). With a mined vocabulary a café carries `coffee shop`
    # (3,679) and `coin laundry` (200) at once, and only one of those is why a
    # reader would land here. The rare word is the question — the same lesson
    # the guitar bug taught ranking — so the pills are ordered by how few places
    # in this province share them, and the common ones fall to the end.
    ranked = sorted(slugs, key=lambda s2: (T["counts"][prov][s2],
                                           T["order"].index(s2) if s2 in T["order"] else 9999))
    for slug in ranked:
        d = T["defs"].get(slug)
        if not d or T["counts"][prov][slug] < T["min_tag"]:
            continue
        if d.get("family") == "state":
            continue      # about the entry, not the place — see index_tags()
        if re.match(r"open-(mon|tues|wednes|thurs|fri|satur|sun)day$", slug):
            continue      # the hours line already says which days
        how = T["via"][r["id"]].get(slug, "attr")
        if how not in hows:
            hows.append(how)
        tip = " / ".join(x for x in _via_note(how) if x)
        # The pill opens the tag's own page (its href is walked as a file by
        # tests/test_tags.py); the 🔍 beside it opens the search filtered to
        # the tag — the door Michael asked for on 2026-09-07: "discovery should
        # EXPLICITLY allow searching/finding by tags".
        out.append(f'<a class="tag" href="../tag/{slug}.html" title="{att(tip)}">'
                   f'{esc(d["glyph"])} {bi(d["th"], d["en"])}</a>'
                   f'<a class="tagseek" href="../../search.html?tag={slug}" '
                   f'aria-label="{att(d["en"])}">🔍</a>')
    if not out:
        return ""
    # WO-52 put the provenance sentences in a tap-sheet on the label; WO-69
    # (2026-09-07, Michael: "if you need to explain something using words,
    # you're fucking up") takes the sheet off. Each pill still carries its
    # own provenance in title= for a pointer, and the tag page says the rest.
    label = f'<span class="taglabel">🏷</span>'
    cap = 14
    if len(out) <= cap:
        return (f'<div class="tagrow">{label} ' + " ".join(out) + "</div>")
    rest = len(out) - cap
    return (f'<div class="tagrow">{label} ' + " ".join(out[:cap])
            + f'<details class="tagrest"><summary>+{rest:,} '
            + g["bi"]("ป้าย", "more") + "</summary>" + " ".join(out[cap:])
            + "</details></div>")


def index_tags(g, r):
    """The tag slugs a record carries, in display order — for the search
    index's `t` field (WO-69). Every assigned tag, not only those with a
    province page: a filter can narrow to two places, a page cannot."""
    T = g.get("TAGS")
    if not T:
        return []
    slugs = T["by_id"].get(r["id"]) or []
    order = T["order"]
    # THE STATE FAMILY IS RECORDS MANAGEMENT, NOT A CHIP (Nan, 2026-09-10:
    # "Tags that should be background for records management appearing in
    # foreground to users"). "Phone number held" stood on 61,181 result rows
    # beside the phone number itself; "A thin entry" announced a lack the row
    # showed by being short. They stay on the record, in tags.html and in the
    # API's `tags`; they do not ride into `t`, which is what every row chip,
    # the second line and the refine drawers read.
    defs = T.get("defs") or {}
    slugs = [s for s in slugs if (defs.get(s) or {}).get("family") != "state"]
    return sorted(slugs, key=lambda s: order.index(s) if s in order else 9999)


# TAGS WHOSE LABEL IS NOT A WORD ANYBODY SEARCHES FOR.
#
# Beer (Pallida), 2026-09-09, two screenshots: "search is completely broken
# since the rebuild". He was looking at the page BEFORE the answer — the shelf
# chips draw in 0.4 s, and data/index.json took 10.6 s to arrive and parse on a
# Mac on wired broadband. On his phone that window did not end.
#
# Measured against the live index that morning: 87,833 rows, 49.3 MB raw, and
# `k` — the searchable blob every row carries — was 20.72 MB of it, 45.8%.
# 10.93 MB of that 20.72, more than half, was these two families of label:
#
#   FIELD, 9 tags, 10.93 MB.  They describe THE ENTRY, not the shop, which
#   _rule_words already says in as many words: "It describes the entry, not
#   the shop."  `held` stood on 87,799 rows of 87,833 — 100%.
#   "มีเพจเฟซบุ๊ก Facebook page held" on 68,981 (78.5%), 2.55 MB for the Thai
#   token alone; "มีเบอร์โทร Phone number held" on 61,181 (69.7%), 1.90 MB.
#   Nobody has ever typed "A thin entry" to find a shop, and the facets these
#   come from are already filterable as ints in `t`.
#
#   AMPHOE AND TAMBON, 0.49 MB.  data/tags.json decorates those two mined
#   specs with th_prefix "อ." / "ต." and en_suffix " (district)" /
#   " (subdistrict)", so `k` carried "อ.เมืองเชียงใหม่ Mueang Chiang Mai
#   (district)" — and build.py writes the same tambon, the same amphoe and the
#   same lexicon readings into `k` raw, a few lines further down. Checked
#   across the index: the bare word is also present on 99.8% of ต. rows and
#   every real อ. row. This is the decorated second copy, and "(district)" is
#   not a search term.
#
#   Their two siblings in the `area` family STAY. `street` is the road off the
#   record's own address and reaches records STREET_OF does not; `postcode` is
#   a thing a reader genuinely types. Muting the family would have taken both,
#   which is why the cut is on the two sources and not on the family.
#
# The cost of that prose was never mainly bytes on the wire — brotli squashes
# a string that repeats 68,981 times. It was PARSE TIME and MEMORY on a phone,
# and it was RANKING: a facet label competes with a name, which is why "Event"
# answered with lawyers carrying the chip "🎪 รับจัดงาน · Event planning"
# ahead of the two places actually on the Event Venues shelf.
#
# Everything else stays. A reader really does search "vegan", "บิตคอยน์",
# "open 24 hours", a brand, the moat — those are the shop, not the record.
SEARCH_MUTE_KINDS = {"field"}
SEARCH_MUTE_SOURCES = {"attrs.amphoe", "attrs.tambon"}


def search_words(g, r):
    """Both names of every tag this place earned — matched by search, never
    shown, so "vegan" finds the cafés that only say so in a diet tag.

    Minus the tags that describe the entry rather than the place, and the
    amphoe and tambon tags whose words build.py writes into `k` undecorated
    anyway. See SEARCH_MUTE_KINDS above for what that was costing and why.
    """
    T = g.get("TAGS")
    if not T:
        return ""
    words = []
    for slug in T["by_id"].get(r["id"]) or []:
        d = T["defs"].get(slug)
        if not d:
            continue
        rule = d.get("rule") or {}
        if rule.get("kind") in SEARCH_MUTE_KINDS:
            continue
        if rule.get("source") in SEARCH_MUTE_SOURCES:
            continue
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
                "Places whose pin lies inside the Chiang Mai moat quadrilateral — computed from the coordinates, not typed in by hand.")
    if k == "royal":
        return ("วัดที่อยู่ในรายการพระอารามหลวงที่มดแดงเก็บด้วยมือ ทุกรายการมีแหล่งอ้างอิง",
                "Temples on the royal-temple list this site keeps by hand — every entry with a fetched source.")
    if k == "food-award":
        return ("ร้านที่มีเครื่องหมายในรายการเกียรติด้านอาหาร ทุกรายการมีแหล่งอ้างอิงและปีที่ได้",
                "Places carrying a food mark on the honours list — each with its source and the year it was awarded.")
    if k == "mined" and d["rule"].get("source") == "streets.json":
        return ("ทุกที่ที่จับคู่กับถนนสายนี้ — จากที่อยู่ที่ร้านบอกเอง หรือแนวถนนที่ใกล้หมุดที่สุด",
                "Every place matched to this road — from the address it gives, or the road line nearest its pin.")
    if k == "mined":
        src = d["rule"].get("source", "").replace("attrs.", "")
        return (f"ทุกที่ที่ข้อมูลของตัวเองบันทึกค่า “{d['rule'].get('value','')}” ไว้ในช่อง {src} — "
                "อ่านจากข้อมูล ไม่ได้พิมพ์ใส่",
                f"Every place whose own record carries “{d['rule'].get('value','')}” in its {src} field — "
                "read off the data, not typed on.")
    if k == "field":
        return (d.get("note_th") or "นับจากช่องข้อมูลที่สารบัญนี้มีหรือยังไม่มีสำหรับที่นี่ "
                "เป็นเรื่องของบันทึก ไม่ใช่เรื่องของร้าน",
                d.get("note_en") or "Counted from which fields this catalogue holds for the place. "
                "It describes the entry, not the shop.")
    if k == "hours":
        return ("อ่านจากเวลาเปิด-ปิดที่บันทึกไว้ ที่ที่ยังไม่มีเวลาเปิดไม่ได้แปลว่าปิด",
                "Read from the opening hours on the record. A place with no hours held is not a place that is shut.")
    if k == "facet":
        return ("จากป้ายข้อมูลของแต่ละที่ หรือจากเจ้าของที่ติ๊กยืนยันเอง",
                "From each place's own recorded tags, or from an owner who ticked it themselves.")
    if k == "curated":
        return (d.get("note_th") or "รายการที่คัดด้วยมือโดยทีมมดแดง",
                d.get("note_en") or "A list kept by hand by the Mot Dang team.")
    return ("จากข้อมูลที่บันทึกไว้ของแต่ละที่เอง (OpenStreetMap หรือทะเบียน) — มีเท่าที่รู้ ไม่ได้แปลว่าที่อื่นไม่มี",
            "From each place's own recorded fields (OpenStreetMap or a register) — what we know of, not what the others lack.")


def _chip(g, href, glyph, th, en, n):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    return (f'<a class="tagchip" href="{att(href)}">{esc(glyph)} {bi(th, en)}'
            f'<span class="count">{n:,}</span></a>')


def also_rail(g, prov, slug, depth=2, limit=14, floor=3):
    """The tags this tag's places most often ALSO carry, each a door to the
    pair. `search.html?tag=a&tag=b` is an AND filter that already works, so the
    chip's count is the size of the list behind it, not an estimate."""
    T = g.get("TAGS")
    if not T or slug not in T["defs"]:
        return ""
    rows = (T.get("pairs", {}).get(prov) or {}).get(slug) or []
    up = "../" * depth
    out = []
    for other, n in rows:
        if n < floor or len(out) >= limit:
            continue
        d = T["defs"].get(other)
        if not d or other == slug:
            continue
        out.append(_chip(g, f"{up}search.html?tag={slug}&tag={other}",
                         d.get("glyph", "🏷"), d["th"], d["en"], n))
    if not out:
        return ""
    bi = g["bi"]
    return ('<div class="alsorail"><span class="raillabel">'
            + bi("มักเป็นอย่างอื่นด้วย", "These are also") + "</span>"
            + " ".join(out) + "</div>")


def family_rail(g, prov, slug, depth=2, limit=16):
    """Siblings in the same family, commonest first — the sideways step a
    reader wants when this tag was nearly the right word."""
    T = g.get("TAGS")
    if not T or slug not in T["defs"]:
        return ""
    fam = T["defs"][slug]["family"]
    sibs = [(T["counts"][prov][s2], s2) for s2 in T["order"]
            if s2 != slug and T["defs"][s2]["family"] == fam
            and T["counts"][prov][s2] >= T["min_tag"]]
    sibs.sort(reverse=True)
    if not sibs:
        return ""
    bi = g["bi"]
    out = [_chip(g, f"{s2}.html", T["defs"][s2].get("glyph", "🏷"),
                 T["defs"][s2]["th"], T["defs"][s2]["en"], n)
           for n, s2 in sibs[:limit]]
    fams = {f["key"]: f for f in T["doc"]["families"]}
    f = fams.get(fam, {"th": fam, "en": fam})
    more = ""
    if len(sibs) > limit:
        more = (f' <a class="tagmore" href="{"../" * depth}tags.html#{fam}">'
                + bi(f"ทั้งหมด {len(sibs) + 1:,}", f"all {len(sibs) + 1:,}") + "</a>")
    return ('<div class="alsorail famrail"><span class="raillabel">'
            + bi(f["th"], f["en"]) + "</span>" + " ".join(out) + more + "</div>")


def shelf_chips(g, prov, cat, depth=1, limit=18, floor=None):
    """🏷 The doors a shelf page can open (WO-76). The tags most carried by the
    records ON this shelf, each linking to the tag×shelf page where one exists
    and to the AND search where it does not. Called from build.py's shelf
    pages: a reader standing on `food` with 26,984 rows in front of them can
    step to `noodle shop` (662) or `open late` in one click, without typing."""
    T = g.get("TAGS")
    if not T:
        return ""
    floor = T["tag_shelf_min"] if floor is None else floor
    counts = T["shelf_counts"][prov]
    # `state` is about the entry, not the place — see the families note in
    # data/tags.json. Ranked by count it would take every slot on every shelf
    # ("also: has a phone number, 14,714") and say nothing about the food.
    no_rail = {f["key"] for f in T["doc"]["families"] if f.get("rails") is False}
    rows = sorted(((counts[s][cat], s) for s in T["order"]
                   if counts[s][cat] >= floor and T["defs"][s]["family"] not in no_rail),
                  reverse=True)
    if not rows:
        return ""
    bi = g["bi"]
    up = "../" * depth
    out = []
    for n, slug in rows[:limit]:
        d = T["defs"][slug]
        href = (f"{up}../search.html?tag={slug}&amp;cat={cat}" if n >= T["tag_shelf_min"]
                else f"{up}../search.html?tag={slug}")
        out.append(_chip(g, href, d.get("glyph", "🏷"), d["th"], d["en"], n))
    more = ""
    if len(rows) > limit:
        more = (f' <a class="tagmore" href="{up}../tags.html">'
                + bi(f"ป้ายทั้งหมด {len(rows):,}", f"all {len(rows):,} tags here") + "</a>")
    return ('<div class="alsorail shelfrail"><span class="raillabel">'
            + bi("แคบลงด้วยป้าย", "Narrow this shelf") + "</span>"
            + " ".join(out) + more + "</div>")


def emit(g, data):
    T = g.get("TAGS") or assign(g, data)
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    DOCS, BASE = g["DOCS"], g["BASE"]
    entry_li, shelf_map, toolbar = g["entry_li"], g["shelf_map"], g["toolbar"]
    share_block, ad_box = g["share_block"], g["ad_box"]
    breadcrumb_ld, item_list_ld = g["breadcrumb_ld"], g["item_list_ld"]
    listing_page = g["listing_page"]
    CATS, CAT_ORDER, PROVINCES = g["CATS"], g["CAT_ORDER"], g["PROVINCES"]
    name_of, is_featured, ground_truth = g["name_of"], g["is_featured"], g["ground_truth"]
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
    n_hub = 0
    export = []
    (DOCS / "data" / "tags").mkdir(parents=True, exist_ok=True)

    def ordered(recs):
        # Shelf order first (the page groups by shelf), featured, then name —
        # and the SAME order goes to shelf_map, whose dots point at row indexes.
        def k(r):
            cats = r.get("cat") or []
            ci = min((CAT_ORDER.index(c) for c in cats if c in CAT_ORDER), default=999)
            return (ci, not is_featured(r), -ground_truth(r), name_of(r))
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
            # OVER THE SHELF CAP THE PAGE IS A HUB, NOT A ROLL (2026-09-10).
            # has-facebook.html was 68 MB and 48,988 rows — no phone opens
            # that, and drawing those rows was most of an 80-minute build
            # phase. HUB_MAX_ROWS is the shelves' own number (build.py, Nan's
            # go): past it a shelf front becomes doors with counts, so a tag
            # page does the same — one line per shelf, the count, the door to
            # the tag×shelf page where one is built. Nothing is lost: every
            # row is on its shelf, in data/tags/<prov>-<slug>.json, and behind
            # search.html?tag=<slug>, which is where the hub sends a reader.
            # Since 2026-10-03 (Nan: "break up all the shelf pages") a big tag
            # pages its rows like every shelf does; only the `state` tags — a
            # record holding a phone number, a website, a Facebook page — keep
            # the hub form past the cap, because their rows are the record's
            # bookkeeping and not a list a reader came for.
            cap = int(g.get("HUB_MAX_ROWS") or 0)
            no_rail_fams = {f["key"] for f in T["doc"]["families"] if f.get("rails") is False}
            big = bool(cap) and len(recs) > cap and d["family"] in no_rail_fams
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
            rows, cross, dom_order = [], [], []
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
            # A tag×shelf roll over the cap is built, paged — the shelf fronts
            # link it as a shelf of its own — except for the `state` tags.
            cross = [(c, rs, xp) for c, rs, xp in cross
                     if not (cap and len(rs) > cap and d["family"] in no_rail_fams)]
            has_cross = {c for c, _, _ in cross}
            heads = {}
            for c, rs in by_cat.items():
                cdef = CATS.get(c, {"th": c, "en": c})
                head = (f'<a href="../{c}/index.html">{bi(cdef["th"], cdef["en"])}</a>'
                        if c in CATS else esc(c))
                xlink = ""
                if c in has_cross:
                    xn = len(x_members[c])
                    xlink = (f' · <a class="xshelf" href="../../search.html?tag={slug}&amp;cat={c}">'
                             + bi("ดูเฉพาะหมวดนี้", "just this shelf")
                             + (f" ({xn:,})" if xn != len(rs) else "") + "</a>")
                heads[c] = (f'<li class="shelf areahead">{head} '
                            f'<span class="count">{len(rs):,}</span>{xlink}</li>')
            # Paged at SHELF_PAGE_ROWS; a page repeats the shelf heading of the
            # rows it carries. The map's dots carry a ROW INDEX and md.js
            # resolves it against this page's li[data-n] in document order — so
            # each page's map is drawn from the order its rows land in, which
            # is by shelf here and not the order `recs` arrived in. Same rule
            # fold_rows keeps for the shelves.
            flat = [(c, r) for c, rs in by_cat.items() for r in rs]
            pages_rows = []
            for chunk in ([[]] if big else g["chunked"](flat)):
                prow, pdom, last = [], [], None
                if big:
                    prow = list(heads.values())
                for c, r in chunk:
                    if c != last:
                        prow.append(heads[c])
                        last = c
                    prow.append(entry_li(r, f"../p/{g['place_slug'](r)}.html"))
                    pdom.append(r)
                pages_rows.append((prow, pdom))
            rows, dom_order = pages_rows[0]
            pager_of = lambda n: g["shelf_pager"](n, len(pages_rows), f"{slug}.html")
            # A tag×shelf page whose shelf is nobody's first shelf here (every
            # open-late pharmacy is filed under essentials first) still needs a
            # door from this page, or it is reachable from the sitemap alone.
            orphan = [c for c in has_cross if c not in by_cat]
            if orphan:
                links = " · ".join(
                    f'<a class="xshelf" href="../../search.html?tag={slug}&amp;cat={c}">{bi(CATS[c]["th"], CATS[c]["en"])} '
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
            # One download per tag: the JSON. A GeoJSON beside each (3,007 files,
            # 215 MB) went 2026-10-11 (Nan: cut what weighs and adds little).
            dl = (f'<p class="prov"><a href="../../data/tags/{key}-{slug}.json">⬇ JSON</a> '
                  f'({len(recs):,} {bi("แห่ง", "places")})</p>')
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
                    + also_rail(g, key, slug) + family_rail(g, key, slug)
                    + f'{ad_box(path, 2)}'
                    + ("" if big else
                       f'{shelf_map(dom_order or recs, "tag-" + slug, p, label_th=t_th, label_en=t_en)}'
                       f'{toolbar(dom_order)}')
                    + pager_of(1)
                    + f'<ul class="dir" data-sortable>{"".join(rows)}</ul>'
                    + pager_of(1)
                    + (f'<p class="tinynote"><a href="../../search.html?tag={slug}">'
                       + bi(f"ดูทั้ง {len(recs):,} แห่งในช่องค้นหา",
                            f"all {len(recs):,} places, in search") + "</a></p>"
                       if big else "")
                    + f'{dl}'
                    f'{share_block(BASE + path, title_th)}')
            (tdir / f"{slug}.html").write_text(page(
                f'{title_th} · {t_en}, {p["en"]}', body, depth=2, crumbs=crumbs,
                path=path,
                desc=f'{t_th} {p["th"]} — {len(recs)} แห่ง · {t_en}, {p["en"]} · มดแดง',
                extra_head=bc + item_list_ld(recs, key)))
            for pn, (prow, pdom) in enumerate(pages_rows[1:], 2):
                pname = g["page_name"](f"{slug}.html", pn)
                lo = (pn - 1) * g["SHELF_PAGE_ROWS"] + 1
                rng = f"{lo:,}–{lo + len(pdom) - 1:,}"
                pbody = (f'<h1>{esc(d["glyph"])} {bi(d["th"], d["en"])} '
                         f'<span class="count">({rng} {bi("จาก", "of")} {len(recs):,})</span></h1>'
                         f'<p class="prov"><a href="{slug}.html">← '
                         + bi("กลับหน้าแรกของป้ายนี้", "Back to the front of this tag")
                         + "</a></p>"
                         f'{shelf_map(pdom, "tag-" + slug, p, label_th=t_th, label_en=t_en)}'
                         f'{toolbar(pdom)}{pager_of(pn)}'
                         f'<ul class="dir" data-sortable>{"".join(prow)}</ul>{pager_of(pn)}')
                (tdir / pname).write_text(page(
                    f'{title_th} · {t_en}, {p["en"]} — {pn}', pbody, depth=2, crumbs=crumbs,
                    path=f"{key}/tag/{pname}",
                    desc=f'{t_th} {p["th"]} — {rng} จาก {len(recs)} แห่ง · {t_en}, {p["en"]} · มดแดง'))
            n_pages += 1
            n_hub += big
            (DOCS / "data" / "tags" / f"{key}-{slug}.json").write_text(json.dumps({
                "tag": slug, "province": key, "th": d["th"], "en": d["en"],
                "family": d["family"], "count": len(recs), "generated": BUILD_DATE,
                "page": BASE + path,
                "places": [{"id": r["id"], "name": name_of(r),
                            "url": BASE + f"{key}/p/{g['place_slug'](r)}.html",
                            "via": T["via"][r["id"]].get(slug)} for r in recs]},
                ensure_ascii=False))
            # tag × shelf: since 2026-10-11 (Nan: cut what weighs and adds little) a
            # search for the tag on that shelf, not a page of its own. The pages were
            # 8,358 of 14,409 tag pages and about 1 GB; each old address, and its
            # -pN pages, keeps a small forward so a shared link still lands.
            for c, rs, xpath in cross:
                target = BASE + f"search.html?tag={slug}&cat={c}"
                stub = ('<!doctype html><html lang="th"><head><meta charset="utf-8">'
                        '<meta name="robots" content="noindex">'
                        f'<link rel="canonical" href="{att(target)}">'
                        f'<meta http-equiv="refresh" content="0; url={att(target)}">'
                        '<title>ย้ายแล้ว · moved</title></head><body>'
                        f'<p>หน้านี้ย้ายไปที่ <a href="{att(target)}">{esc(target)}</a> · '
                        'This page has moved.</p></body></html>\n')
                first = xpath.rsplit("/", 1)[1]
                for i in range(1, max(1, -(-len(rs) // g["SHELF_PAGE_ROWS"])) + 1):
                    (tdir / g["page_name"](first, i)).write_text(stub)
                n_cross += 1

    # ---- /tags.html + /tags/<family>.html ---------------------------------
    # The vocabulary was 76 tags and fitted on one page. It is now ~1,270 and
    # does not: a flat list would be a quarter of a megabyte of chips nobody
    # scrolls. So the index carries each family's commonest tags and a door to
    # the whole of it, and the family page carries the rest with a box that
    # narrows as you type. Yahoo-style throughout — Term (count), never a term
    # without its number.
    def tag_row(slug, up=""):
        d = defs[slug]
        links = []
        for p2 in PROVINCES:
            n = T["counts"][p2["key"]][slug]
            if n >= T["min_tag"]:
                links.append(f'<a href="{up}{p2["key"]}/tag/{slug}.html">{bi(p2["th"], p2["en"])} '
                             f'<span class="count">({n:,})</span></a>')
        if not links:
            return None, 0
        total = sum(T["counts"][p2["key"]][slug] for p2 in PROVINCES)
        return (f'<li data-tag="{att((d["th"] or "") + " " + (d["en"] or "") + " " + slug)}">'
                f'{esc(d["glyph"])} <b>{bi(d["th"], d["en"])}</b> — '
                + " · ".join(links) + "</li>"), total

    by_fam = collections.defaultdict(list)
    for slug in order:
        row, total = tag_row(slug)
        if row:
            by_fam[defs[slug]["family"]].append((total, slug, row))
    for rows in by_fam.values():
        rows.sort(key=lambda x: -x[0])

    FILTER_JS = ("<script>(function(){var b=document.getElementById('tagfilter');"
                 "if(!b)return;var li=[].slice.call(document.querySelectorAll('.tagidx li'));"
                 "var c=document.getElementById('tagfiltern');"
                 "b.addEventListener('input',function(){var q=b.value.trim().toLowerCase();var n=0;"
                 "li.forEach(function(e){var hit=!q||(e.getAttribute('data-tag')||'').toLowerCase().indexOf(q)>=0;"
                 "e.hidden=!hit;if(hit)n++;});"
                 "document.querySelectorAll('.tagidx').forEach(function(u){"
                 "u.hidden=!u.querySelector('li:not([hidden])');"
                 "var h=u.previousElementSibling;if(h&&h.tagName==='H2')h.hidden=u.hidden;});"
                 "if(c)c.textContent=q?n.toLocaleString():'';});})();</script>")

    def filter_box(n):
        return ('<p class="tagfilterbox"><label for="tagfilter">'
                + bi("พิมพ์เพื่อกรอง", "Type to narrow") + " </label>"
                f'<input id="tagfilter" type="search" autocomplete="off" '
                f'placeholder="{att(bi("เช่น ซักผ้า, noodle, in-", "e.g. laundry, noodle, in-"))}">'
                f' <span id="tagfiltern" class="count"></span> '
                f'<span class="tinynote">{bi(f"{n:,} ป้าย", f"{n:,} tags")}</span></p>')

    # ---- one page per family ------------------------------------------------
    (DOCS / "tags").mkdir(parents=True, exist_ok=True)
    fam_pages = 0
    for fk in fam_order:
        rows = by_fam.get(fk) or []
        if not rows:
            continue
        f = fams[fk]
        f_th, f_en = f["th"], f["en"]
        fpath = f"tags/{fk}.html"
        crumbs = (f'<a href="../index.html">{bi("หน้าแรก", "Home")}</a> › '
                  f'<a href="../tags.html">{bi("ป้ายกำกับ", "Tags")}</a> › {bi(f_th, f_en)}')
        items = "".join(r.replace('href="', 'href="../') for _, _, r in rows)
        body = (f'<h1>{esc(f["glyph"])} {bi(f_th, f_en)} '
                f'<span class="count">({len(rows):,})</span></h1>'
                + filter_box(len(rows))
                + f'<ul class="dir tagidx">{items}</ul>'
                + f'<p class="tinynote"><a href="../tags.html">← {bi("ป้ายกำกับทั้งหมด", "All tags")}</a>'
                f' · <a href="../data/tags.json">data/tags.json</a></p>'
                + FILTER_JS
                + share_block(BASE + fpath, f"{f_th} · ป้ายกำกับ"))
        (DOCS / "tags" / f"{fk}.html").write_text(page(
            f'{f_th} · {f_en}', body, depth=1, path=fpath, crumbs=crumbs,
            desc=f'{f_th} — {len(rows):,} ป้ายกำกับ · {f_en}, {len(rows):,} tags · มดแดง'))
        fam_pages += 1

    # ---- the index ----------------------------------------------------------
    TOP = 30
    sections, jump = [], []
    for fk in fam_order:
        rows = by_fam.get(fk) or []
        if not rows:
            continue
        f = fams[fk]
        jump.append(f'<a href="tags/{fk}.html">{esc(f["glyph"])} {bi(f["th"], f["en"])} '
                    f'<span class="count">({len(rows):,})</span></a>')
        head = (f'<h2 id="{fk}">{esc(f["glyph"])} '
                f'<a href="tags/{fk}.html">{bi(f["th"], f["en"])}</a> '
                f'<span class="count">({len(rows):,})</span></h2>')
        items = "".join(r for _, _, r in rows[:TOP])
        more = ""
        if len(rows) > TOP:
            more = (f'<p class="tinynote"><a class="tagmore" href="tags/{fk}.html">'
                    + bi(f"ดูทั้งหมด {len(rows):,} ป้ายใน{f['th']}",
                         f"all {len(rows):,} in {f['en']}") + " →</a></p>")
        sections.append(head + f'<ul class="dir tagidx">{items}</ul>' + more)
    total_tags = sum(len(v) for v in by_fam.values())
    lede_th = ("หมวดบอกว่าที่นี่เป็นร้านแบบไหน ป้ายกำกับบอกว่าที่นี่ *ยังเป็น* อะไรอีก — ข้ามทุกหมวด: "
               "ร้านก๋วยเตี๋ยว ซักผ้าหยอดเหรียญ มีอาหารวีแกน รับบิตคอยน์ รถเข็นเข้าได้ เปิด 24 ชั่วโมง "
               "อยู่ในคูเมือง เป็นสาขาเซเว่น ทุกป้ายคำนวณจากข้อมูลที่แต่ละที่บันทึกไว้เองตามกฎข้อเดียว "
               "ต่อป้าย ไม่มีใครพิมพ์ใส่ และทุกหน้านับเฉพาะที่ที่มีจริงในสารบัญ")
    lede_en = ("A shelf says what kind of place this is; a tag says what it ALSO is, across every shelf — "
               "a noodle shop, a coin laundry, vegan options, takes bitcoin, wheelchair access, open 24 "
               "hours, inside the moat, a 7-Eleven branch. Every tag is worked out from each place's own "
               "recorded fields by one stated rule; nothing is typed on, and every page counts only "
               "places the directory holds.")
    how_th = ("ป้ายที่มีน้อยกว่า %d แห่งในจังหวัดยังไม่ได้เปิดหน้า — ไม่ใช่ว่าไม่มี แค่ยังไม่พอจะเป็นหน้า "
              "ชี้เมาส์ที่ป้ายบนหน้าร้านใด ๆ จะบอกว่าป้ายนั้นมาจากไหน" % T["min_tag"])
    how_en = ("A tag with fewer than %d places in a province has no page yet — not absent, just not yet "
              "a page. Point at any tag on a place page to see where it came from." % T["min_tag"])
    body = (f'<h1>🏷 {bi("ป้ายกำกับ", "Tags")} <span class="count">({total_tags:,})</span></h1>'
            f'<p class="myhint">{bi(lede_th, lede_en)}</p>'
            + f'<p class="tagjump">{" · ".join(jump)}</p>'
            + filter_box(total_tags)
            + "".join(sections)
            + f'<p class="tinynote">{bi(how_th, how_en)} · '
            f'<a href="data/tags.json">data/tags.json</a></p>'
            + FILTER_JS
            + share_block(BASE + "tags.html", "ป้ายกำกับ · มดแดง"))
    (DOCS / "tags.html").write_text(page(
        "ป้ายกำกับ", body, depth=0, path="tags.html",
        desc="ป้ายกำกับข้ามหมวดของมดแดง — ก๋วยเตี๋ยว ซักผ้าหยอดเหรียญ วีแกน บิตคอยน์ ไวไฟ รถเข็น เปิด 24 ชม. ในคูเมือง แบรนด์ · Tags across every shelf",
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
    mined_n = sum(1 for s2 in order if defs[s2].get("mined"))
    brands_n = sum(1 for s2 in order if defs[s2].get("generated") and not defs[s2].get("mined"))
    return (f"{n_pages} tag pages ({n_hub} hubs over the shelf cap) + {n_cross} tag×shelf + {fam_pages} family pages, "
            f"{len(order)} tags defined ({mined_n} mined, {brands_n} brands), "
            f"{tagged:,} records tagged ({tagged / max(sum(len(data[p2['key']]) for p2 in PROVINCES), 1):.1%})")


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. Run: python3 build.py")
