#!/usr/bin/env python3
"""The trade-tag and admin-name lexicon: Thai → reading → gloss → shelf.

Nan, 2026-09-06: "one of the MOST helpful things this site does, and doesn't do
nearly enough, is romanization/transliteration of Thai terms associated with
listings." And, the same day: no blurbs — a place's own words stay as FIELDS.

The fields in question are `attrs.tradeTags` — 1,724 distinct Thai trade
words on 2,564 records, read off a Thai directory — and the tambon/amphoe a
record sits in (3,823 records). Until today the tags reached a page only as a
joined sentence, and the admin names only in Thai. This builds one table for
both, so that every surface (the place page, the search index, the AI's
vocabulary) reads from the same file:

    data/trade_lexicon.json
      tags:  {thai: {reading, gloss, glossVia, shelves, n, suspect?}}
      areas: {thai: {reading, kind}}          kind = tambon | amphoe

A READING IS A READING. It is produced by translit.py (RTGS) and labelled
`.roman` wherever it prints; it never becomes a name. Where the letter rules
fail — a syllable read to nothing, a loanword spelt in Thai — the entry is
marked `suspect` and the page prints the Thai alone rather than a wrong
reading. The suspects are listed at the end of the run so the curated
rtgs_lexicon.json can pick them up one by one.

A GLOSS IS ONLY EVER SOURCED. Three sources, in order: a paired
`tradeTagsEn` on a record (a session read it off the shop's own page), the
search thesaurus (cross-language equivalence, mined from the site's own
labels), and a shelf whose Thai label IS the tag. Nothing is machine
translated. A tag with no gloss stays a Thai word with a reading — which is
what the sign says.

    python3 importers/build_trade_lexicon.py
    python3 importers/build_trade_lexicon.py --suspects   # print them all
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import translit  # noqa: E402

OUT = os.path.join(ROOT, "data", "trade_lexicon.json")
OVERRIDES = os.path.join(ROOT, "data", "curated", "trade_lexicon_overrides.json")
THAI = re.compile(r"[฀-๿]+")


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def segdict():
    words = set()
    lp = os.path.join(ROOT, "data", "curated", "rtgs_lexicon.json")
    if os.path.exists(lp):
        lex = load(lp)
        for k in ("loanword", "irregular", "place", "brand"):
            words |= set((lex.get(k) or {}).keys())
    p = os.path.join(ROOT, "data", "search_segdict.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                words.add(line)
    return words


def pieces(text, words):
    """Longest-match split of a Thai run on the corpus dictionary; a run the
    dictionary cannot place comes back whole, so nothing is ever dropped."""
    out, i, n = [], 0, len(text)
    while i < n:
        best = None
        for j in range(min(n, i + 24), i, -1):
            if text[i:j] in words:
                best = j
                break
        if best is None:
            # swallow to the next dictionary word start, or the end
            j = i + 1
            while j < n and not any(text[j:k] in words for k in range(j + 1, min(n, j + 24) + 1)):
                j += 1
            out.append(text[i:j])
            i = j
        else:
            out.append(text[i:best])
            i = best
    return out


_LEXWORDS = None


def lex_split(run, words):
    """Split a Thai run around the curated lexicon's own words FIRST — a
    loanword inside a compound (ซ่อม|มอเตอร์ไซค์) must come out whole even
    when the corpus dictionary also knows the whole compound — then split what
    remains on the dictionary."""
    global _LEXWORDS
    if _LEXWORDS is None:
        lp = os.path.join(ROOT, "data", "curated", "rtgs_lexicon.json")
        lex = load(lp) if os.path.exists(lp) else {}
        keys = set()
        for k in ("loanword", "irregular"):
            keys |= {w for w in (lex.get(k) or {}) if len(w) >= 3}
        _LEXWORDS = (re.compile("(" + "|".join(re.escape(w) for w in sorted(keys, key=len, reverse=True)) + ")")
                     if keys else None)
    out = []
    parts = _LEXWORDS.split(run) if _LEXWORDS else [run]
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 1:          # a lexicon word, kept whole
            out.append(part)
        else:
            out.extend(pieces(part, words))
    return out


def read(text, words):
    """(reading, suspect).

    The Thai is split on the corpus dictionary PLUS the curated lexicon's own
    words (loanwords, irregulars), and each piece is read on its own, so a
    loanword inside a compound — ซ่อม|มอเตอร์ไซค์ — gets its English rather
    than a syllable-by-syllable noise. Suspect when any Thai piece reads to
    nothing: that is a hole in the rules, and the Thai alone is truer than a
    reading with a word missing."""
    out, suspect = [], False
    pos = 0
    for m in THAI.finditer(text):
        if m.start() > pos:
            lat = text[pos:m.start()].strip()
            if lat:
                out.append(lat)
        for piece in lex_split(m.group(), words):
            rom = translit.reading(piece).strip()
            if not rom:
                suspect = True
                continue
            out.append(rom)
        pos = m.end()
    if pos < len(text) and text[pos:].strip():
        out.append(text[pos:].strip())
    return " ".join(out), suspect


def main():
    want_suspects = "--suspects" in sys.argv
    words = segdict()
    recs = []
    for pv in ("cm", "cr"):
        recs += load(os.path.join(ROOT, "data", "canonical", f"{pv}.json"))

    # --- tags ------------------------------------------------------------
    count = collections.Counter()
    paired = {}
    for r in recs:
        a = r.get("attrs") or {}
        tt = [t.strip() for t in (a.get("tradeTags") or []) if isinstance(t, str) and t.strip()]
        te = a.get("tradeTagsEn") or []
        for i, t in enumerate(tt):
            count[t] += 1
            if i < len(te) and isinstance(te[i], str) and te[i].strip():
                paired.setdefault(t, te[i].strip())

    thes = load(os.path.join(ROOT, "data", "search_thesaurus.json")).get("groups") or []
    th_en = {}
    for grp in thes:
        ens = [w for w in grp if w.isascii() and not w.startswith("-")]
        for w in grp:
            if THAI.search(w) and ens:
                th_en.setdefault(w, ens[0])

    shelves = load(os.path.join(ROOT, "data", "search_shelves.json")).get("shelves") or {}
    cats = load(os.path.join(ROOT, "data", "categories.json"))
    label_en = {}
    for ck, c in cats.items():
        if not isinstance(c, dict):
            continue
        if c.get("th") and c.get("en"):
            label_en.setdefault(c["th"], c["en"])
        for ch in (c.get("children") or []):
            if isinstance(ch, dict) and ch.get("th") and ch.get("en"):
                label_en.setdefault(ch["th"], ch["en"])

    over = load(OVERRIDES) if os.path.exists(OVERRIDES) else {}
    over_tags = over.get("tags") or {}
    over_areas = over.get("areas") or {}

    tags = {}
    suspects = []
    via = collections.Counter()
    for t, n in count.most_common():
        rom, sus = read(t, words)
        gloss, gv = "", ""
        if t in paired:
            gloss, gv = paired[t], "record"
        elif t in label_en:
            gloss, gv = label_en[t], "shelf-label"
        elif t in th_en:
            gloss, gv = th_en[t], "thesaurus"
        entry = {"reading": rom, "gloss": gloss, "glossVia": gv,
                 "shelves": shelves.get(t) or [], "n": n}
        if sus:
            entry["suspect"] = True
            suspects.append((t, rom, n))
        if t in over_tags:
            entry.update({k: v for k, v in over_tags[t].items() if k in ("reading", "gloss")})
            entry["glossVia"] = "curated" if over_tags[t].get("gloss") else entry["glossVia"]
            entry.pop("suspect", None)
        if gv:
            via[gv] += 1
        tags[t] = entry

    # --- areas -----------------------------------------------------------
    # The curated admin file FIRST, because its spellings are the ones on the
    # road signs, and then every admin name the catalogue itself carries.
    #
    # WO-76: this used to read the curated file alone, and the curated file
    # holds 43 อำเภอ and 16 ตำบล. Measured 2026-09-08: the catalogue prints 294
    # distinct ตำบล on 3,031 records and this table could read 8% of them. The
    # rest reached the page in Thai with nothing beside them — on the one row
    # of a place page that tells a reader which district they are looking at.
    areas = {}
    admin = load(os.path.join(ROOT, "data", "curated", "admin_areas.json")).get("areas") or {}
    area_sus = []

    def area(name, kind):
        name = (name or "").strip()
        if not name or not THAI.search(name) or name in areas:
            return
        rom, sus = read(name, words)
        e = {"reading": rom, "kind": kind}
        if sus:
            e["suspect"] = True
            area_sus.append((name, rom))
        if name in over_areas:
            e["reading"] = over_areas[name]
            e.pop("suspect", None)
        areas[name] = e

    for pv in admin.values():
        for kind in ("amphoe", "tambon"):
            for name in (pv.get(kind) or {}):
                area(name, kind)
    # The catalogue's own admin names, under the field that named them. A
    # value carrying its own ต./อ. prefix is stored WITHOUT it, because the
    # prefix is a word the page prints in English and the name is not.
    FIELD_KIND = {"tambon": "tambon", "subdistrict": "tambon",
                  "amphoe": "amphoe", "district": "amphoe",
                  "city": "city", "pinFrom": "pinFrom", "addrProvince": "province"}
    strip_pre = re.compile(r"^(?:ต\.|อ\.|จ\.|ตำบล|อำเภอ|จังหวัด)\s*")
    for r in recs:
        a = r.get("attrs") or {}
        for field, kind in FIELD_KIND.items():
            v = a.get(field)
            for one in (v if isinstance(v, list) else [v]):
                if not isinstance(one, str):
                    continue
                for part in one.split("/"):
                    area(strip_pre.sub("", part).strip(), kind)

    doc = {
        "_note": ("Generated by importers/build_trade_lexicon.py from canonical records, "
                  "the search thesaurus, categories.json and admin_areas.json. Readings are "
                  "RTGS (translit.py) and print as readings, never as names. A gloss is "
                  "present only where a source gave it (glossVia). Hand fixes go in "
                  "data/curated/trade_lexicon_overrides.json, never here."),
        "_built": __import__("datetime").date.today().isoformat(),
        "counts": {"tags": len(tags), "tagsWithGloss": sum(1 for e in tags.values() if e["gloss"]),
                   "tagsSuspect": len(suspects), "areas": len(areas),
                   "areasSuspect": len(area_sus), "glossVia": dict(via)},
        "tags": tags, "areas": areas,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    c = doc["counts"]
    print(f"tags {c['tags']:,} · glossed {c['tagsWithGloss']:,} ({c['glossVia']}) · "
          f"suspect readings {c['tagsSuspect']:,}")
    print(f"areas {c['areas']:,} · suspect readings {c['areasSuspect']:,}")
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    shown = suspects if want_suspects else suspects[:15]
    for t, rom, n in shown:
        print(f"  suspect tag  {t!r:32} → {rom!r:24} ×{n}")
    for name, rom in (area_sus if want_suspects else area_sus[:10]):
        print(f"  suspect area {name!r:32} → {rom!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
