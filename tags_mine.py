#!/usr/bin/env python3
"""🏷 Mined tags — the vocabulary the catalogue already speaks (WO-76).

`tags_layer` holds 76 tags written by hand, one rule each. That was right when
the corpus was 16,270 records and 140 attrs keys. It is now 88,161 records and
288 keys, and the hand list reaches 6.4% of them: 82,555 records carry no tag
at all. The gap is not that the rules are wrong. It is that the vocabulary is
hand-sized and the corpus is not.

So this module does for every categorical field what `_brand_tags` already does
for `attrs.brand`: it reads the field's OWN values off the records and mints one
tag per value that clears a floor. Nothing is typed on, nothing is invented, and
the rule stays one rule per tag — "attrs.overtureCategory contains
`noodles_restaurant`" is as stated a rule as "attrs.cuisine contains `japanese`".
The vocabulary grows when the crawl meets a new word, which is the point.

WHY THIS MATTERS MORE AFTER THE OVERTURE FOLD
    21,027 records (23.9%) stand on a shelf with NO sub-shelf — 13,668 of them
    on `food`. For those, the fine-grained word they carry is
    attrs.overtureCategory and nothing reads it. They are findable by name and
    by nothing else. Minting the field makes 62,376 records reachable by what
    they are.

LABELS
    A mined tag needs two names. In order: data/curated/tag_labels.json (a
    person's own wording), then data/curated/index_labels.json (the site's own
    shelf labels), then the value itself — a Thai value keeps the Thai and gets
    an RTGS *reading* beside it (labelled as a reading, never as a name; see
    translit.py), an English value is de-snaked. A label nobody has written is
    a gap the file records, not a reason to drop the tag.

Entry point:
    mine(records, spec, labels, existing_slugs) -> (defs, by_id, gaps)
"""
import collections
import re
import unicodedata

_UNSAFE = re.compile(r"[^a-z0-9]+")
_THAI = re.compile(r"[฀-๿]")


def _ascii_slug(text, limit=48):
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return _UNSAFE.sub("-", s.strip().lower()).strip("-")[:limit].rstrip("-")


def _romanize(text):
    """RTGS reading of a Thai string, or "" if translit is unavailable."""
    try:
        import translit
        # ํ+า typed for ำ: 228 records carry it in attrs.road, and the reader
        # then hears ราชดําเนิน as "Ratdanoen". derive.normalise folds it at
        # import; the value already on a record is read the same way here.
        return translit.title((text or "").replace("ํา", "ำ")) or ""
    except Exception:
        return ""


def _values(rec, source):
    """The field's values on one record, as a list of stripped strings.
    `source` is "attrs.<key>" or a top-level record key."""
    if source.startswith("attrs."):
        holder = rec.get("attrs") or {}
        key = source.split(".", 1)[1]
    else:
        holder, key = rec, source
    v = holder.get(key)
    if v is None or v == "" or v == [] or v == {}:
        return []
    if isinstance(v, list):
        out = []
        for x in v:
            out += [t.strip() for t in str(x).split(";") if t.strip()]
        return out
    return [t.strip() for t in str(v).split(";") if t.strip()]


def _label(value, spec, labels):
    """(th, en, glyph, labelled) for one mined value."""
    row = (labels.get(spec["key"]) or {}).get(value) or labels.get("_any", {}).get(value)
    if row:
        return (row.get("th") or "", row.get("en") or "",
                row.get("glyph") or spec.get("glyph", "🏷"), True)
    glyph = spec.get("glyph", "🏷")
    if _THAI.search(value):
        # A tag is not a place, and a tag's English half is not `nameEn`: no
        # shop is being given a name it did not choose. An English-mode reader
        # meeting a chip with nothing on it cannot read, type or remember the
        # tag; an RTGS reading gives them all three. So the reading fills the
        # English half here and is kept on the def under `roman` as well, so a
        # page that wants to mark it as a pronunciation can. The value goes in
        # `gaps` regardless — a hand-written label is better than a reading.
        return (value, _romanize(value), glyph, False)
    en = value.replace("_", " ").replace("-", " ").strip()
    en = en[:1].upper() + en[1:]
    return ("", en, glyph, False)


def mine(records, spec, labels, existing_slugs=frozenset(), skip_seen=None,
         label_seen=None, family_of=None, matched=None):
    """One mined family. Returns (defs, by_id, gaps).

    defs  — tag definitions in count order, each with `mined": True`
    by_id — {record id: [slug, …]} (a record may carry several values)
    gaps  — [(value, count)] for values that cleared the floor with no
            hand-written label; the file that would fix them is
            data/curated/tag_labels.json.

    `skip_seen` is the set of values an earlier family on the same field has
    already spoken for, so one value is one tag across the whole vocabulary.

    `matched` is {record id: {"value", "slug", "th", "en", "source"}} — a
    record already matched to a named thing outside the field. The street
    family: a place STREET_OF has put on ถนนราชดำเนิน was also minting
    "on-ratdanoen" off its own address string, so one page said the road three
    ways. A matched record takes the match and its names, not the field; the
    field is read only where no match exists.
    """
    source = spec["source"]
    matched = matched or {}
    known = {}                           # match value -> its match dict
    floor = int(spec.get("min", 8))
    skip = {str(x).strip().casefold() for x in (spec.get("skip_values") or [])}
    skip |= {str(x).strip().casefold() for x in (skip_seen or ())}
    # A family that owns only part of a field. `thai_restaurant` and
    # `japanese_restaurant` are cuisines, not kinds — they were being minted as
    # 380 separate "kind" tags beside a hand-written cuisine list that already
    # had the word. only_suffix takes them; strip_suffix names them by what
    # they are ("Thai", not "Thai restaurant"); map_existing then hands the
    # records to the cuisine tag that already exists instead of minting a
    # second one, which is the difference between one axis and two halves.
    only = [str(x) for x in (spec.get("only_suffix") or [])]
    strip = spec.get("strip_suffix")
    groups = collections.defaultdict(list)
    for r in records:
        m = matched.get(r["id"])
        if m:
            known[m["value"]] = m
            groups[m["value"]].append(r["id"])
            continue
        for v in _values(r, source):
            if v.casefold() in skip:
                continue
            if only and not any(v.endswith(sfx) for sfx in only):
                continue
            groups[v].append(r["id"])
    defs, by_id, gaps = [], collections.defaultdict(list), []
    taken, consumed = set(), set()
    mapped = collections.defaultdict(list)   # slug -> the values that joined it
    for value, ids in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(ids) < floor:
            continue
        naked = value
        if strip:
            for sfx in only or []:
                if naked.endswith(sfx):
                    naked = naked[:-len(sfx)]
                    break
        m = known.get(value)
        if m:
            # The match's own names and slug, so the tag reads exactly as the
            # street chip does: a missing half takes the other, and a Thai
            # name with no English gets its reading (345 streets are named in
            # Latin only, 608 carry no nameEn).
            th = m.get("th") or m.get("en") or ""
            en = m.get("en") or (_romanize(th) if _THAI.search(th) else th)
            glyph, labelled = spec.get("glyph", "🏷"), True
            roman = en if (not m.get("en") and _THAI.search(th)) else ""
            base = m["slug"]
        else:
            th, en, glyph, labelled = _label(naked, spec, labels)
            roman = _romanize(naked) if _THAI.search(naked) else ""
            base = _ascii_slug(en) or _ascii_slug(roman) or _ascii_slug(naked)
        if not base:
            continue
        base = (spec.get("prefix", "") + base)[:52].rstrip("-")
        # Two values that say the same thing in both languages are one tag:
        # ปะยางมอเตอร์ไซค์ and ปะยางรถมอเตอร์ไซค์ were arriving as
        # motorbike-puncture-repair and motorbike-puncture-repair-2.
        # A match is one named thing already; it never folds into another.
        twin = None if m else (label_seen or {}).get(
            (spec["family"], th.strip(), en.strip().casefold()))
        if twin:
            consumed.add(value)
            mapped[twin].append(value)
            for pid in ids:
                by_id[pid].append(twin)
            continue
        slug, n = base, 2
        # A hand-written tag owns its slug: the mined one steps aside under the
        # family key rather than shadowing a rule someone wrote on purpose —
        # unless the spec says these ARE the same thing, in which case the
        # records join the tag that already exists and no def is minted.
        if slug in existing_slugs:
            # ONLY INTO THE SAME FAMILY. The corpus holds junk brand values —
            # six records whose attrs.brand is the word "Restaurant" — and the
            # first cut of this mapped 7,516 restaurants onto that brand tag,
            # which says every one of them belongs to a chain called
            # Restaurant. A value may join a tag that means the same KIND of
            # thing; it may never join one that means a different kind.
            if spec.get("map_existing") and (
                    (family_of or {}).get(slug) == spec["family"]):
                consumed.add(value)
                mapped[slug].append(value)
                for pid in ids:
                    by_id[pid].append(slug)
                continue
            if spec.get("skip_existing"):
                continue
            slug = f"{spec['key']}-{base}"
        while slug in taken:
            slug = f"{base}-{n}"
            n += 1
        taken.add(slug)
        if not labelled:
            gaps.append((value, len(ids)))
        # อ.สันทราย, ต.สันทราย and ถ.สันทราย are three different places with one
        # name; undecorated they arrive as three identical chips and a reader
        # has to guess which is which. The decoration goes on AFTER the slug is
        # settled, so the address stays /tags/in-san-sai/ rather than growing
        # the word "district" into it.
        if spec.get("th_prefix"):
            # A postcode has no Thai in it to prefix, and a chip reading only
            # "50300" says nothing in either language.
            th = th or naked
            if not th.startswith(spec["th_prefix"]):
                th = spec["th_prefix"] + th
        if en and spec.get("en_suffix") and not en.endswith(spec["en_suffix"]):
            en = en + spec["en_suffix"]
        defs.append({
            "slug": slug, "family": spec["family"], "th": th, "en": en,
            "glyph": glyph, "mined": True, "generated": True,
            "value": value, "labelled": labelled, "members": len(ids),
            "rule": {"kind": "mined", "source": (m or {}).get("source") or source,
                     "value": value},
        })
        if roman:
            defs[-1]["roman"] = roman
        if label_seen is not None:
            label_seen[(spec["family"], th.strip(), en.strip().casefold())] = slug
        consumed.add(value)
        for pid in ids:
            by_id[pid].append(slug)
    return defs, dict(by_id), gaps, consumed, dict(mapped)


def mine_all(records, doc, labels, taken=(), matched=None):
    """Every family in doc["mined"], in order. Later families see the slugs the
    earlier ones took, so a slug is claimed once across the whole vocabulary.
    `taken` is what the hand list and the brand index already own — mining runs
    last and steps aside, never over. `matched` is {spec key: {record id:
    match}} — see mine()."""
    existing = {t["slug"] for t in doc.get("tags", [])} | set(taken)
    all_defs, all_by_id, all_gaps = [], collections.defaultdict(list), {}
    # One value is one tag. A family that takes part of a field (the cuisines
    # out of overtureCategory) tells the families after it on the same field
    # what it has spoken for, so the same word cannot come back as a second tag
    # under another name.
    spoken = collections.defaultdict(set)
    sources = {}
    merges = {}
    # (family, th, en) -> slug, so one wording is one tag across every family
    # that mints. Seeded with the hand list, which owns its wordings.
    label_seen = {}
    family_of = {}
    for t in doc.get("tags", []):
        label_seen[(t.get("family", ""), (t.get("th") or "").strip(),
                    (t.get("en") or "").strip().casefold())] = t["slug"]
        family_of[t["slug"]] = t.get("family", "")
    # What the caller already holds — the brand index, mostly. A mapping tells
    # us the family too; a bare set tells us only the name, and a slug whose
    # family is unknown is never mapped onto.
    if isinstance(taken, dict):
        for slug, d in taken.items():
            family_of[slug] = (d or {}).get("family", "") if isinstance(d, dict) else ""
    for spec in doc.get("mined", []):
        defs, by_id, gaps, consumed, mapped = mine(
            records, spec, labels, existing, skip_seen=spoken[spec["source"]],
            label_seen=label_seen, family_of=family_of,
            matched=(matched or {}).get(spec["key"]))
        spoken[spec["source"]] |= consumed
        # A record handed to a tag that already existed still came off a field,
        # and both the provenance and the tag's own definition have to say so:
        # `earned_by` is every other (field, value) pair that earns this tag, which
        # is what keeps "every member really carries the value" checkable once
        # a tag can be earned more than one way.
        for slug, values in mapped.items():
            sources[slug] = spec["source"]
            merges.setdefault(slug, [])
            for v in values:
                merges[slug].append({"source": spec["source"], "value": v})
        for d in defs:
            existing.add(d["slug"])
            sources[d["slug"]] = d["rule"]["source"]
            family_of[d["slug"]] = d["family"]
        all_defs += defs
        for pid, slugs in by_id.items():
            all_by_id[pid] += slugs
        if gaps:
            all_gaps[spec["key"]] = gaps
    # ---- the curated merge -------------------------------------------
    # Four fields can say one thing in four wordings: sub `cafe` arrived as
    # กาแฟ-คาเฟ่, overtureCategory `cafe` as คาเฟ่, `coffee_shop` as ร้านกาแฟ
    # and cuisine `coffee` as Coffee — four chips, one question. The label
    # dedupe above only catches wordings that are identical; deciding that
    # "Coffee shop" and "Café" are the same tag is a person's judgment, so it
    # is written down in data/tags.json under `merge` and applied here, after
    # every family has minted, so the order of the specs cannot matter.
    fold = {}
    for target, sources_ in (doc.get("merge", {}).get("into") or {}).items():
        for src in sources_:
            fold[src] = target
    if fold:
        minted = {d["slug"]: d for d in all_defs}
        for slug, target in list(fold.items()):
            if slug not in minted:            # already gone, or a hand tag
                continue
            if target not in minted and target not in {t["slug"] for t in doc.get("tags", [])}:
                continue
            d = minted[slug]
            pair = {"source": d["rule"]["source"], "value": d["rule"]["value"]}
            merges.setdefault(target, []).append(pair)
            for extra in (d.get("earned_by") or []):
                merges[target].append(extra)
        gone = {s2 for s2 in fold if s2 in minted}
        all_defs = [d for d in all_defs if d["slug"] not in gone]
        for pid, slugs in list(all_by_id.items()):
            out, seen = [], set()
            for s2 in slugs:
                s2 = fold.get(s2, s2)
                if s2 not in seen:
                    seen.add(s2)
                    out.append(s2)
            all_by_id[pid] = out
        for s2 in gone:
            sources.pop(s2, None)

    for d in all_defs:
        if d["slug"] in merges:
            d["earned_by"] = (d.get("earned_by") or []) + merges.pop(d["slug"])
    # what is left belongs to hand-written or brand tags, which the caller owns
    return all_defs, dict(all_by_id), all_gaps, sources, merges


# --------------------------------------------------------------- by name
# THE NAME IS A FIELD TOO. Nan, 2026-09-08: *"tag every record you can — make
# tags prolific. Some tags can/should be inferred."*
#
# Every tag here was minted from a field some records carry and most do not:
# 22,966 records hold no categorical field at all, and a further 41,287 hold
# exactly one. What they DO hold is a name, and in this catalogue a name is
# usually a description — ซักผ้าหยอดเหรียญ ป้าแดง is a coin laundry, ก๋วยเตี๋ยว
# เรือ ป้านิด is a noodle shop, Baan Suan Guesthouse is a guesthouse. The shop
# wrote that itself. Reading it is inference, not invention, and the tag says
# which word it read.
#
# Two guards keep it from becoming invention:
#
#   * THE SHELF MUST ALREADY SAY IT. A tag may only be earned by name on a
#     shelf where the FIELD-earned members of that same tag already stand. So
#     "Thai" can be read off a food place's name and never off นวดแผนไทย, and
#     "eye clinic" is never read off a name on the optician's shelf unless the
#     field-earned eye clinics are there too. The vocabulary calibrates itself
#     off what the fields already proved.
#   * A WORD HAS TO BE A WORD. Thai matches are substrings of at least three
#     characters, because Thai is written without spaces; Latin matches are
#     whole words of at least four letters, so "bar" never lights up "Barber"
#     and "spa" never lights up "Spanish". Anything shorter earns nothing.
def _words_for(d, aliases):
    """The words a name would have to contain to be saying this tag."""
    out = set()
    for w in [d.get("value"), d.get("th"), d.get("en"), d.get("roman")]:
        w = (w or "").strip()
        if not w:
            continue
        if _THAI.search(w):
            if len(w) >= 3:
                out.add(w)
        else:
            w = w.replace("_", " ").strip()
            if len(w) >= 4:
                out.add(w.casefold())
    for w in (aliases.get(d["slug"]) or []):
        w = str(w).strip()
        if w:
            out.add(w if _THAI.search(w) else w.casefold())
    return out


def earn_by_name(records, defs, by_id, spec, shelf_of):
    """{record id: [(slug, word), …]} — tags a record's own name says.

    `defs` is every tag already defined, `by_id` what the fields already
    earned, `shelf_of(record)` the shelf keys it stands on.
    """
    fams = set(spec.get("families") or [])
    stop = {str(x).strip().casefold() for x in (spec.get("stop_words") or [])}
    aliases = spec.get("aliases") or {}
    floor = int(spec.get("min_members", 3))
    cap = int(spec.get("max_per_record", 4))

    members = collections.Counter()
    shelves = collections.defaultdict(collections.Counter)
    for r in records:
        for slug in by_id.get(r["id"]) or []:
            members[slug] += 1
            for c in shelf_of(r):
                shelves[slug][c] += 1

    vocab = []                      # (word, slug, is_thai) longest word first
    for slug, d in defs.items():
        if d.get("family") not in fams or members[slug] < floor:
            continue
        for w in _words_for(d, aliases):
            if w in stop:
                continue
            vocab.append((w, slug, bool(_THAI.search(w))))
    vocab.sort(key=lambda x: -len(x[0]))
    latin = [(re.compile(r"\b" + re.escape(w) + r"\b"), slug, w) for w, slug, th in vocab if not th]
    thai = [(w, slug) for w, slug, th in vocab if th]

    out = collections.defaultdict(list)
    for r in records:
        have = set(by_id.get(r["id"]) or [])
        mine_shelves = set(shelf_of(r))
        if not mine_shelves:
            continue
        name_th = " ".join(str(r.get(k) or "") for k in ("name", "nameTh"))
        name_lat = (str(r.get("nameEn") or "") + " " + str(r.get("name") or "")).casefold()
        got = 0
        for w, slug in thai:
            if got >= cap:
                break
            if slug in have or w not in name_th:
                continue
            if not (mine_shelves & set(shelves[slug])):
                continue
            have.add(slug)
            out[r["id"]].append((slug, w))
            got += 1
        for rx, slug, w in latin:
            if got >= cap:
                break
            # the substring test first: the word must be in the name for its regex to match,
            # and it is ~30x cheaper (74 s of tags.assign on motdang-build, 2026-10-11)
            if slug in have or w not in name_lat or not rx.search(name_lat):
                continue
            if not (mine_shelves & set(shelves[slug])):
                continue
            have.add(slug)
            out[r["id"]].append((slug, rx.pattern))
            got += 1
    return dict(out)


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent
    doc = json.loads((root / "data" / "tags.json").read_text())
    lp = root / "data" / "curated" / "tag_labels.json"
    labels = json.loads(lp.read_text()) if lp.exists() else {}
    recs = []
    for p in ("cm", "cr"):
        f = root / "data" / "canonical" / f"{p}.json"
        if f.exists():
            recs += json.loads(f.read_text())
    defs, by_id, gaps, _src, _also = mine_all(recs, doc, labels)
    tagged = len(by_id)
    print(f"{len(recs):,} records · {len(defs):,} mined tags · "
          f"{tagged:,} records carry at least one ({tagged / max(len(recs), 1):.1%})")
    fam = collections.Counter(d["family"] for d in defs)
    for k, v in fam.most_common():
        print(f"  {v:5d}  {k}")
    unlabelled = sum(len(v) for v in gaps.values())
    print(f"{unlabelled:,} mined tags have no hand-written label yet "
          f"(data/curated/tag_labels.json)")
    if "-v" in sys.argv:
        for key, rows in gaps.items():
            print(f"\n-- {key}")
            for v, c in rows[:40]:
                print(f"  {c:6d}  {v}")
