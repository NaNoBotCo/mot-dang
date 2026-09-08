"""Thai administrative and registry vocabulary, glossed by composing its parts.

WHAT THIS IS
------------
`translit.py` answers "how does this sound". This answers "what does this
word mean" for the closed vocabularies the registers write in: a temple's
nikaya, the levels a school teaches, the education area it answers to, what a
condominium's title deed says the unit is for, what an OSM parking record is
called before its own name is added.

Measured 2026-09-08, across the 88,161-record catalogue: 33,369 attribute
values print in Thai script with no Latin anywhere beside them, over 59
fields — while the FIELD LABELS beside them have been bilingual all along.
A reader without Thai sees a label they can read and a value they cannot, and
the language toggle cannot help them because there is nothing to toggle to.

WHY IT COMPOSES RATHER THAN LISTING
-----------------------------------
`registerUses` has 39 distinct values on 559 records and every one of them is
the same dozen words joined with slashes. `levels` has 35 values and they are
six stage words and a number. A flat table of 39 strings is 39 chances to
have missed one; a table of twelve words that compose covers the fortieth
value the day the register adds it, and says so honestly when it cannot.

WHAT IT WILL NOT DO
-------------------
  * It does not gloss NAMES. A name is what a place calls itself; the site
    keeps that sourced and does not machine-translate it. Anything this file
    returns is a dictionary word or an administrative term.
  * It returns "" rather than a partial gloss. A value glossed as
    "residential unit / ??? / balcony area" is worse than the Thai alone,
    because the Thai alone is at least true.
  * It never writes to `data/canonical/` or to `nameEn`. Gloss and reading
    are computed and are labelled as computed wherever they print.

    python3 tests/test_terms.py
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
CURATED = os.path.join(ROOT, "data", "curated", "thai_terms.json")
THAI = re.compile(r"[฀-๿]")

_DOC = None


def _doc():
    global _DOC
    if _DOC is None:
        try:
            with open(CURATED, encoding="utf-8") as fh:
                _DOC = json.load(fh)
        except (OSError, ValueError):
            _DOC = {"parts": {}, "separators": {}}
    return _DOC


def parts(field):
    """The word table for one field, without the _underscore keys."""
    t = (_doc().get("parts") or {}).get(field) or {}
    return {k: v for k, v in t.items() if not k.startswith("_") and isinstance(v, str)}


def has_thai(s):
    return bool(THAI.search(s or ""))


# ---------------------------------------------------------------------------
# The splitter. A value is cut on the punctuation the register itself used —
# never inside a word — and each piece is looked up whole, longest first.
# ---------------------------------------------------------------------------
_SPLIT = re.compile(r"([–—\-/,()]|\s+)")


def _lookup(piece, table):
    """The longest entry in `table` that IS this piece, or that this piece
    opens with — a register's own spelling wanders, and ห้องชุดพักอาศัย
    followed by a parenthetical is still a residential unit."""
    p = piece.strip()
    if not p:
        return None
    if p in table:
        return table[p]
    for k in sorted(table, key=len, reverse=True):
        if p.startswith(k) and len(k) >= 3:
            rest = p[len(k):].strip(" ()")
            if not rest:
                return table[k]
            sub = _lookup(rest, table)
            if not sub:
                return None
            # The register says it twice: ห้องชุดเพื่อประกอบการค้า
            # (ห้องชุดพาณิชยกรรม) is a commercial unit, in parentheses, a
            # commercial unit. Say it once.
            if sub.strip().lower() in table[k].strip().lower():
                return table[k]
            return f"{table[k]}, {sub}"
    return None


_NUM = re.compile(r"^([฀-๿.]+?)\s*(\d+)$")


def _numbered(piece, field):
    """อ.2 · ป.6 · ม.3 · ปวช.3 — a stage word and the year inside it."""
    table = ((_doc().get("parts") or {}).get(field) or {}).get("_numbered") or {}
    m = _NUM.match(piece.strip())
    if not m:
        return None
    stem, n = m.group(1), int(m.group(2))
    row = table.get(stem)
    if not row:
        return None
    label, offset = row[0], row[1]
    return f"{label}{n + offset}"


def agency(value):
    """The English an agency publishes for its own name, or "".

    Whole-string only. An organisation's name is not composed of glossable
    parts, and 13 names cover every credit line in the catalogue: the source a
    row is credited to is how a reader decides what the row is worth, and it
    was legible to half the readership.
    """
    if not isinstance(value, str):
        return ""
    t = _doc().get("agency") or {}
    return t.get(value.strip(), "") if not value.strip().startswith("_") else ""


def gloss(value, field, read_tail=None):
    """An English gloss for one field value, or "" when the words are not all
    known. Composition preserves the register's own separators, so the gloss
    has the shape of the Thai it stands beside.

    Matching is GREEDY OVER TOKENS, not per token: `แหล่งท่องเที่ยวเชิงศาสนา
    ศิลปะ วัฒนธรรม` is one entry in the table and three whitespace-separated
    pieces in the value, and a per-piece loop can never see it.

    `read_tail` is a romaniser, passed only by callers whose field is a head
    word followed by a NAME — `ลานจอดรถ มหาวิทยาลัยเชียงใหม่` is a parking
    yard at a university, and the university is read, never translated. Every
    other caller leaves it None and gets "" rather than a half-gloss.
    """
    if not isinstance(value, str) or not value.strip():
        return ""
    v = value.strip()
    table = parts(field)
    numbered = ((_doc().get("parts") or {}).get(field) or {}).get("_numbered") or {}
    if not table and not numbered:
        return ""
    seps = _doc().get("separators") or {}
    toks = [t for t in _SPLIT.split(v) if t]
    out, saw_word, i = [], False, 0

    def put(s):
        # The Thai carried no space between a head word and what follows it;
        # the English needs one, or "ลานจอดรถ มหาวิทยาลัยเชียงใหม่" comes out
        # as "parking yardChiang Mai University".
        if s and out and out[-1] and not out[-1][-1].isspace() and not s[0].isspace():
            out.append(" ")
        out.append(s)

    while i < len(toks):
        tok = toks[i]
        if _SPLIT.fullmatch(tok):
            out.append(seps.get(tok.strip(), " " if tok.isspace() else tok.strip()))
            i += 1
            continue
        hit, j = None, i + 1
        for k in range(len(toks), i, -1):
            cand = "".join(toks[i:k]).strip()
            if not cand:
                continue
            hit = _numbered(cand, field) or _lookup(cand, table)
            if hit is not None:
                j = k
                break
        if hit is None:
            # A Thai word nobody has glossed. Latin and digits carry
            # themselves; Thai does not, and a hole makes the whole gloss a
            # lie about how much we understood.
            if has_thai(tok):
                if not (saw_word and read_tail):
                    return ""
                rest = "".join(toks[i:]).strip()
                rd = read_tail(rest) or ""
                if not rd:
                    return ""
                put(rd)
                break
            put(tok)
            i += 1
            continue
        if hit:
            saw_word = True
        put(hit)
        i = j
    if not saw_word:
        return ""
    text = "".join(out)
    text = re.sub(r"\s+", " ", text).strip(" ·–-,")
    text = re.sub(r"\s+([,)])", r"\1", text)
    return text


# ---------------------------------------------------------------------------
# Two fields the parts table cannot reach on its own, because half of each
# value is a PLACE NAME and a place name is read, never translated.
# ---------------------------------------------------------------------------
_EDU = re.compile(r"^(สพป\.|สพม\.)\s*(.+?)(?:\s*เขต\s*(\d+))?$")


def edu_area(value, read):
    """สพป.เชียงราย เขต 2 → "Chiang Rai Primary Education Service Area 2".

    `read` is the caller's romaniser (the site passes the one that checks the
    area lexicon first, so the province is spelt the way the road signs spell
    it and not the way the letter rules would).
    """
    if not isinstance(value, str) or not value.strip():
        return ""
    v = value.strip()
    t = parts("eduArea")
    m = _EDU.match(v)
    if not m:
        return t.get(v, "")
    kind, where, area = m.group(1), m.group(2).strip(), m.group(3)
    label = t.get(kind)
    if not label:
        return ""
    name = read(where) or ""
    if not name:
        return ""
    return f"{name} {label}" + (f" {area}" if area else "")


_PREFIXED = re.compile(r"^(ต\.|อ\.|จ\.|ถ\.|ซ\.|ตำบล|อำเภอ|จังหวัด|ถนน|ซอย|หมู่ที่|หมู่)\s*(.+)$")


def prefixed(value, read):
    """ต.วัดเกต → ("Tambon", "Wat Ket"). The prefix is a word and is
    translated; what follows it is a name and is only ever read."""
    if not isinstance(value, str):
        return None
    m = _PREFIXED.match(value.strip())
    if not m:
        return None
    label = parts("prefix").get(m.group(1))
    if not label:
        return None
    name = read(m.group(2).strip()) or ""
    return (label, name) if name else None


# ---------------------------------------------------------------------------
# A Thai address, decomposed. 36,442 records carry an address with no Latin
# character anywhere in it; almost all of them name their ตำบล, อำเภอ and
# จังหวัด, and those three are the part a reader actually needs to place
# themselves. What is left — a house number, a soi, a landmark — is read.
# ---------------------------------------------------------------------------
_ADDR_PREFIX = r"(?:ตำบล|ต\.|อำเภอ|อ\.|จังหวัด|จ\.|ถนน|ถ\.|ซอย|ซ\.|แขวง|หมู่ที่|หมู่)"
_ADDR_SPLIT = re.compile(f"({_ADDR_PREFIX})")
_POSTCODE = re.compile(r"\s*\d{5}\s*$")


def address(value, read):
    """The named units of a Thai address, in order, as (label, reading) pairs.

    Only the units the address itself labels. An address that names none of
    them comes back empty rather than romanised whole — a run-on reading of a
    landmark and a house number helps nobody and looks like a translation.
    """
    if not isinstance(value, str) or not value.strip():
        return []
    out, seen = [], set()
    pre = parts("prefix")
    # Cut the string ON the prefix words, so one unit can never swallow the
    # next: "ตำบลหนองบัว อำเภอไชยปราการ จังหวัดเชียงใหม่" is three units, and
    # a regex that reads "everything up to a comma" makes it one.
    chunks = _ADDR_SPLIT.split(value)
    for k in range(1, len(chunks), 2):
        label = pre.get(chunks[k])
        name = (chunks[k + 1] if k + 1 < len(chunks) else "")
        # A comma ends a unit. "ต.วัดเกต, เมือง" is a tambon and then an
        # unlabelled something; reading the something as part of the tambon
        # invents a district called Wat Ket Mueang.
        name = name.split(",")[0].strip()
        name = _POSTCODE.sub("", name).strip(" ,")
        if not label or not name or not has_thai(name):
            continue
        rd = read(name) or ""
        if not rd or (label, rd) in seen:
            continue
        seen.add((label, rd))
        out.append((label, rd))
    return out
