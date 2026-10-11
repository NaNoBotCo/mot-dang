"""Take the template out of the index before it is loaded.

Why this exists (Nan 2026-09-25, "tha phae gate" answered with 40,601 pages,
parking lots first): every Chiang Mai page prints a bearing to Tha Phae Gate,
every unnamed car park was NAMED by that bearing, and every page repeats its
own title four or five times. bm25 read all of it as meaning. The fix is not a
rule about Tha Phae Gate; it is a rule about templates:

  * a piece of text whose numbers CHANGE from page to page while its words
    stay is a template — in a title from TITLE_DF pages ("Parking · 41 km
    east of Tha Phae Gate"), in a body from BODY_DF; a number that never
    changes is part of a name ("7-Eleven");
  * a piece of three words or more that recurs on CHROME_DF pages is chrome
    ("Skip to content", "Add to my plan");
  * the part of a title after its last " — " that recurs on TPL_DF pages is
    the shelf and brand ("ที่จอดรถ เชียงใหม่ · มดแดง Mot Dang"); it leaves the
    title and stays searchable in the body;
  * a title piece that measures a distance ("41 km east of …", "ห่าง … 3.8
    กม.") locates the page; it does not name it, and it leaves the title;
  * the page's own title, said again in its body (description, h1, the
    English-name row), comes out of the body — the title column carries it;
  * a piece already said once on the page is not said again.

Counted from the corpus at load time, so a new template on any site is caught
without a line of code naming it. Single words and pairs are never chrome —
a category label ("Parking", "อาหารไทย") is meaning even on 5,000 pages.

Spelling: a thesaurus group whose Latin members differ only by spaces and
aspirated h (tha phae · thapae · thaphae) is one name spelled three ways. The
body of a page titled "Thapae Gate" also says "Tha Phae Gate" and "Thaphae
Gate", so every spelling finds it; the title keeps the page's own spelling,
so an exact title still outranks it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

TPL_DF = 25        # a title suffix this common is the shelf and brand
TITLE_DF = 8
BODY_DF = 200
CHROME_DF = 500

RE_PIECE = re.compile(r"\s+[·—|•–]\s+")
RE_DIGITS = re.compile(r"\d+")
RE_WS = re.compile(r"\s+")
RE_LATIN = re.compile(r"^[a-z][a-z ]*[a-z]$")
RE_DIST = re.compile(r"\d(?:[\d.,]*\d)?\s*(?:km|m|กม\.?|ม\.|เมตร|กิโลเมตร)(?![a-z])", re.I)


def norm(s: str) -> str:
    return RE_WS.sub(" ", RE_DIGITS.sub("#", s.lower())).strip()


def pieces(s: str) -> list[str]:
    return [p for p in RE_PIECE.split(s) if p.strip()]


def _title_parts(title_s: str) -> tuple[list[str], str]:
    """(name parts, suffix) — the suffix is what follows the last " — "."""
    parts = title_s.split(" — ")
    return parts, parts[-1] if len(parts) > 1 else ""


class Deboil:
    def __init__(self, thesaurus: Path | None = None):
        self.df: dict[int, int] = {}
        self.raw: dict[int, int] = {}      # key → the first raw form seen; 0 once it varies
        self.variants: dict[str, list[str]] = {}
        if thesaurus and thesaurus.exists():
            self._spellings(json.loads(thesaurus.read_text(encoding="utf-8")).get("groups") or [])

    def _spellings(self, groups):
        for g in groups:
            lat = sorted({m.lower().strip() for m in g if RE_LATIN.match(m.lower().strip())})
            if len(lat) < 2:
                continue
            if len({m.replace(" ", "").replace("h", "") for m in lat}) != 1:
                continue
            for m in lat:
                self.variants[m] = lat
        # longest first, so "tha phae" is tried before any shorter member
        self._vre = [(re.compile(rf"(?<![a-z]){re.escape(m)}(?![a-z])"), m)
                     for m in sorted(self.variants, key=len, reverse=True)]

    # ---------------------------------------------------------------- counting
    def _keys(self, r: dict) -> dict[int, int]:
        ks = {}
        parts, suffix = _title_parts(r["title_s"])
        if suffix:
            ks[hash("S" + norm(suffix))] = 1
        for part in parts:
            for p in pieces(part):
                if RE_DIGITS.search(p):
                    ks[hash("T" + norm(p))] = hash(p)
        for p in pieces(r["body_s"]):
            if RE_DIGITS.search(p) or p.count(" ") >= 2:
                ks[hash("B" + norm(p))] = hash(p)
        return ks

    def count(self, r: dict):
        df, raw = self.df, self.raw
        for k, h in self._keys(r).items():
            df[k] = df.get(k, 0) + 1
            if raw.get(k, h) != h:
                raw[k] = 0
            else:
                raw.setdefault(k, h)

    def prune(self):
        """Drop the counts that can never cross a threshold; the rest is kept."""
        lo = min(TPL_DF, TITLE_DF, CHROME_DF)
        self.df = {k: n for k, n in self.df.items() if n >= lo}
        self.varies = {k for k in self.df if self.raw.get(k) == 0}
        self.raw = {}

    # ---------------------------------------------------------------- applying
    def _n(self, tag: str, p: str) -> int:
        return self.df.get(hash(tag + norm(p)), 0)

    def _tpl(self, tag: str, p: str, floor: int) -> bool:
        k = hash(tag + norm(p))
        return bool(RE_DIGITS.search(p)) and k in self.varies and self.df.get(k, 0) >= floor

    def title(self, title_s: str) -> tuple[str, str, list[str]]:
        """(the title as it should match, the suffix moved out of it, the
        title's pieces in the other spellings)."""
        parts, suffix = _title_parts(title_s)
        moved = ""
        if suffix and self._n("S", suffix) >= TPL_DF:
            parts, moved = parts[:-1], suffix
        kept, seen = [], set()
        for part in parts:
            for p in pieces(part):
                k = norm(p)
                if k in seen:
                    continue
                if self._tpl("T", p, TITLE_DF) or RE_DIST.search(p):
                    continue
                seen.add(k)
                kept.append(p)
        if not kept:                       # all template: the title stays whole  stylecheck: allow (code)
            return title_s, "", []
        alias = []
        for p in kept if self.variants else []:
            low = p.lower()
            for rx, m in self._vre:
                if rx.search(low):
                    alias += [rx.sub(v, low) for v in self.variants[m] if v != m]
                    break
        return " · ".join(kept), moved, alias

    def body(self, body_s: str, title_s: str, moved: str, said: str = "",
             alias: list[str] | None = None) -> str:
        """The title's own words once more, then what the page says besides —
        a locator piece of the title not even once."""
        name = pieces(title_s)
        for p in sorted(pieces(said.split(" — ")[0]) if said else [], key=len, reverse=True):
            if len(p) >= 6:
                body_s = body_s.replace(p, " · ")
        seen = {norm(p) for p in name}
        kept = ([moved] if moved else []) + name + (alias or [])
        for p in pieces(body_s):
            k = norm(p)
            if k in seen:
                continue
            seen.add(k)
            if self._tpl("B", p, BODY_DF):
                continue
            if p.count(" ") >= 2 and self._n("B", p) >= CHROME_DF:
                continue
            kept.append(p)
        return " · ".join(kept)

    def apply(self, r: dict) -> tuple[str, str]:
        t, moved, alias = self.title(r["title_s"])
        return t, self.body(r["body_s"], t, moved, r["title_s"], alias)


# ------------------------------------------------------------------ the page's chrome
# The counting above catches a template by its numbers or its length. Chrome
# that is short and the same on every page slips through it: measured
# 2026-10-03, รังมด matched 75,871 pages (the anthill link on every place page,
# "บอทว่าอย่างไรเกี่ยวกับที่นี่ — รังมด"), grab 68,474 (the ride button),
# "garden restaurant" 14,745 (the sponsor box). So the crawler takes these
# blocks out of the HTML by their class before it reads a word, and whatever
# they say never reaches the index.
CHROME_CLASSES = {
    "skiplink", "sr",                          # skip to content
    "nownear",                                 # the weather / now-near strip under the top bar
    "share", "sharebar",                       # share buttons
    "footsos", "sos",                          # the emergency numbers strip
    "adbox", "adsell", "adlabel",              # sponsor boxes and "advertise here"
    "planbtn",                                 # add to my plan
    "grabride",                                # ride here · Grab
    "looline", "loomore",                      # nearest toilet: another place's name
    "cpics", "wander-near",                    # around here: other places' names
    "waypics", "wander-rand",                  # the way here in pictures, take me somewhere
    "gapdrawer",                               # what is missing, claim, report an error
    "anthill",                                 # what the bots say about this place
    "sitenet",                                 # the Mot Dang net on every minisite
    "fleetband",                               # our other sites
    "toolbar",                                 # sort-by controls
}
_RE_TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>")
_RE_CLASS = re.compile(r"""\bclass\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)
# A link to the map with the brand as its text ("แผนที่ · Map: มดแดง · Mot Dang").
_RE_MAPLINK = re.compile(r'(?is)<a\b[^>]*href="[^"]*map\.html#[^"]*"[^>]*>.*?</a\s*>')
_VOID = {"br", "img", "input", "meta", "link", "hr", "wbr", "source", "area", "col", "embed", "track", "param"}


def strip_chrome(html: str, classes=CHROME_CLASSES) -> str:
    """The HTML with every element whose class names a piece of chrome cut
    out, children and all. Nesting is counted per tag name, so a <div> of
    chrome holding other <div>s is cut at its own close. An element whose
    close never comes loses only its opening tag."""
    out, pos, at = [], 0, 0
    while True:
        m = _RE_TAG.search(html, at)
        if not m:
            break
        at = m.end()
        close, name, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if close or name in _VOID or attrs.rstrip().endswith("/"):
            continue
        c = _RE_CLASS.search(attrs)
        if not c or not (classes & set((c.group(1) or c.group(2) or c.group(3) or "").split())):
            continue
        depth, end = 1, None
        for n in _RE_TAG.finditer(html, at):
            if n.group(2).lower() != name or (not n.group(1) and n.group(3).rstrip().endswith("/")):
                continue
            depth += -1 if n.group(1) else 1
            if depth == 0:
                end = n.end()
                break
        out.append(html[pos:m.start()])
        pos = at = end if end is not None else m.end()   # never closed: only the tag goes
    out.append(html[pos:])
    return _RE_MAPLINK.sub(" ", "".join(out))


_BRAND_SEP = re.compile(r"\s+[·—|•–]\s+")


def brand_suffix(title: str, brands) -> tuple[str, str]:
    """(the title without the site's own name at its end, the name taken off).
    "Wawee Coffee — กาแฟ-คาเฟ่ เชียงใหม่ · มดแดง Mot Dang" → ("Wawee Coffee —
    กาแฟ-คาเฟ่ เชียงใหม่", "มดแดง Mot Dang"). A title that is nothing but the
    name stays whole."""
    words = sorted({b.lower() for b in brands if b}, key=len, reverse=True)
    if not words:
        return title, ""
    cut = ""
    while True:
        seps = list(_BRAND_SEP.finditer(title))
        if not seps:
            break
        last = seps[-1]
        piece = title[last.end():].lower()
        for w in words:
            piece = piece.replace(w, " ")
        if re.search(r"\w", piece):
            break
        cut = (title[last.end():] + (" · " + cut if cut else "")).strip()
        title = title[:last.start()]
    return title, cut
