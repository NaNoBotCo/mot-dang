#!/usr/bin/env python3
"""ชื่อเดียวกันคนละสคริปต์ — one name written in two scripts, and how they meet.

WO-56. A place in this catalogue arrives from one of two kinds of source and
they do not speak the same language:

    every state register is Thai-only     ONAB temples 2,084 (100%) ·
                                          OBEC schools 1,302 (100%) ·
                                          MOPH 490 (100%) · OPEC 168 (100%) ·
                                          FDA 907 (98%) · condominiums 367 (98%)
    the open map is mostly Latin-only     8,676 of 14,851 OSM records (58%)

Only 24% of the catalogue holds both scripts of its own name. So a building,
a clinic or a school can stand in the directory twice — once as a pin with an
English sign and once as a Thai row from the register — and neither half can
see the other. That is how a resident came to say his condominium was not on
the site while it sat there ten times: ปันนา in the register, Punna on the
sign, and nothing in between.

WHAT THIS MODULE IS. The vocabulary for that meeting, in one place because
`import_condo_register`, `build` and any future register importer must all
mean the same thing by "the same name":

    token(name)          the name's first identifying word, romanised —
                         generic words (residence, condo, school, wat) removed
    skeleton(word)       its consonants, for a coarse candidate sweep
    vowel_variants(a,b)  whether two romanised words differ by ONE VOWEL,
                         which is what a Thai spelling read back looks like
                         beside the sign's own Latin (ปันนา → Panna vs Punna)
    families(records)    records grouped by EXACT token, then joined by the
                         unions a person has confirmed in
                         data/curated/name_families.json

WHY THE EXACT TOKEN IS THE PUBLISHED RULE AND THE REST IS A CANDIDATE LIST.
Measured over all 671 housing records on 2026-09-04, every rule loose enough
to gather the ten Punnas also merges two Thai words that differ by a vowel —
because that is what they are:

    consonant skeleton `pn`      gathers all ten · and เพนนี Penny Place too
    one edit apart, chained      gathers all ten · chains ahan→akhan→akhin→anan
    one vowel apart, unchained   gathers all ten · still merges chai with chao
    exact romanised token        never wrong · splits Punna 7 + 3

So the machine proposes and a person settles, the same rule that governs
data/curated/merges.json. A union in name_families.json is a statement that
two SPELLINGS are one name. It is never a statement that two buildings are one
building (that is merges.json) and never a statement about who owns them —
nothing on this disk says who developed Punna, and a name family does not
claim it.
"""
import json
import os
import re
import unicodedata

import translit

ROOT = os.path.dirname(os.path.abspath(__file__))
FAMILIES = os.path.join(ROOT, "data", "curated", "name_families.json")

# Words that name the KIND of place rather than the place. A family keyed on
# one of these would gather every apartment block in the province under
# "apartment", which distinguishes nothing — the WO-52 rule about a sentence
# true on 20,000 pages, applied to a grouping.
GENERIC = {
    # housing
    "residence", "residences", "resident", "condo", "condominium",
    "condominiums", "apartment", "apartments", "mansion", "court", "place",
    "tower", "towers", "building", "bldg", "phase", "suite", "suites",
    "dormitory", "dorm", "hostel", "village", "moobaan", "muban",
    # the words any name may wear
    "the", "and", "at", "aet", "park", "plaza", "view", "city", "home",
    "homes", "house", "baan", "ban",
    # the kind-words of the other shelves, so a family key is never the trade:
    # `wat phra sing` must file under `sing`, not gather 2,084 temples under
    # `phra`, and a clinic must not gather every clinic.
    "wat", "phra", "rongrian", "school", "hospital", "rongphayaban",
    "clinic", "khlinik", "market", "talat", "borisat", "hang", "ran",
    # this province, these districts — a toponym is not a brand
    "chiang", "chiangmai", "mai", "chiangrai", "rai", "lanna", "thai",
    "thailand", "nimman", "nimmana", "nimmanhaemin", "suthep", "huaykaew",
    "santitham", "hangdong", "sansai", "maerim", "doi",
}

_VOWELS = set("aeiou")


def romanise(name):
    """The name in Latin: its own spelling where it has one, the RTGS reading
    where it is Thai. Never stored on a record — a reading is not a name.

    Accents are folded first. `Hinokï Condo` and ฮิโนกิ (reading: Hinoki) are
    one word, and without this they parted at the ï and arrived in the review
    file as a spelling union for a person to rule on — a question invented by
    the regex rather than found in the data."""
    nm = (name or "").strip()
    if re.search(r"[A-Za-z]{3}", nm):
        # Latin only. NFKD must NEVER touch the Thai path: it decomposes สระ อำ
        # (U+0E33) into nikhahit + สระ อา, and dropping "combining" marks then
        # eats the nikhahit — เดอะยูนีค came back as `yanik` instead of Unique,
        # silently, on the one path where the reading is all there is.
        d = unicodedata.normalize("NFKD", nm)
        return "".join(c for c in d if not unicodedata.combining(c))
    return translit.reading(nm) if nm else ""


def token(name):
    """The first identifying word of a name, romanised and lowercased, or ''.

    Four letters minimum: shorter romanised words are mostly particles and
    articles, and a three-letter family gathers strangers."""
    for t in re.findall(r"[a-z]+", romanise(name).lower()):
        if t not in GENERIC and len(t) >= 4:
            return t
    return ""


def skeleton(word):
    """The consonants of a romanised word, for the coarse sweep only. Digraphs
    fold first (ph→f, th→t) because the RTGS reading and an owner's own
    spelling disagree about them constantly."""
    w = re.sub(r"ph", "f", word or "")
    w = re.sub(r"th", "t", w)
    w = re.sub(r"ck", "k", w)
    w = w.replace("c", "k").replace("q", "k").replace("x", "ks")
    w = re.sub(r"[aeiouyhw]", "", w)
    return re.sub(r"(.)\1+", r"\1", w)


def vowel_variant(a, b):
    """True when two romanised words differ in exactly one position and both
    characters there are vowels — ปันนา read as `panna` beside the sign's own
    `punna`. This is a CANDIDATE test, never a published join: `chai` and
    `chao` pass it and are different words."""
    if not a or not b or len(a) != len(b) or a == b:
        return False
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    return len(diff) == 1 and a[diff[0]] in _VOWELS and b[diff[0]] in _VOWELS


def load_generic(path=None):
    """{token: reason} — words refused as family keys because they name a KIND
    or a PLACE, not a building. A refusal carries its ground, so the next
    person can disagree with a reason rather than a silence: the file is the
    KNOWN_EMPTY discipline applied to grouping."""
    p = path or FAMILIES
    if not os.path.exists(p):
        return {}
    doc = json.loads(open(p, encoding="utf-8").read())
    return {k.lower(): v for k, v in (doc.get("generic") or {}).items()}


def load_unions(path=None):
    """{spelling: canonical spelling} from the curated file — confirmed only.

    A union listed without `confirmed: true` is a candidate somebody has not
    read yet and joins nothing, so a half-finished review can never publish a
    grouping nobody agreed to."""
    p = path or FAMILIES
    if not os.path.exists(p):
        return {}
    doc = json.loads(open(p, encoding="utf-8").read())
    out = {}
    for u in doc.get("unions") or []:
        if not u.get("confirmed"):
            continue
        spellings = [s.lower() for s in (u.get("spellings") or []) if s]
        if len(spellings) < 2:
            continue
        canon = (u.get("canonical") or spellings[0]).lower()
        for s in spellings:
            out[s] = canon
    return out


def family_key(name, unions=None, generic=None):
    """The family a name belongs to: its exact token, mapped through any
    confirmed union. '' when the name has no identifying word, and '' when that
    word is on the refusal list — a family keyed on หญิง or on a district
    gathers strangers, and an empty key is how a grouping declines to exist."""
    t = token(name)
    if not t:
        return ""
    if t in (load_generic() if generic is None else generic):
        return ""
    return (unions or {}).get(t, t)


def families(records, unions=None, name_of=lambda r: r.get("name") or ""):
    """{family key: [records]} — every record whose name has a token, grouped.
    Single-member families are kept; the caller decides what a group of one is
    worth (on a page, nothing)."""
    u = unions if unions is not None else load_unions()
    g = load_generic()
    out = {}
    for r in records:
        k = family_key(name_of(r), u, g)
        if k:
            out.setdefault(k, []).append(r)
    return out


def union_candidates(records, unions=None, name_of=lambda r: r.get("name") or ""):
    """[(a, b, [example names])] — spelling pairs a person has not yet ruled
    on, ordered by how many records they would join. Both the vowel test and
    the skeleton test are offered, labelled, because the skeleton reaches
    pairs the vowel test cannot (Punna/Panna passes both; a doubled consonant
    or a dropped `h` passes only the skeleton) and lies more often."""
    u = unions if unions is not None else load_unions()
    seen = {}
    for r in records:
        t = token(name_of(r))
        if t:
            seen.setdefault(t, []).append(name_of(r))
    toks = sorted(seen)
    out = []
    for i, a in enumerate(toks):
        for b in toks[i + 1:]:
            if u.get(a, a) == u.get(b, b):
                continue                    # already one family
            how = ("one vowel" if vowel_variant(a, b)
                   else ("same consonants" if (skeleton(a) == skeleton(b)
                                               and len(skeleton(a)) >= 2
                                               and a[0] == b[0]) else ""))
            if not how:
                continue
            out.append((a, b, how, len(seen[a]) + len(seen[b]),
                        seen[a][:2] + seen[b][:2]))
    out.sort(key=lambda x: -x[3])
    return out
