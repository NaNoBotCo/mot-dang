"""อ่านเป็นไทย — a Latin name read in Thai script. The other half of translit.py.

translit.py reads a Thai-only name in Latin letters for a reader without Thai.
This reads a Latin-only name in Thai letters for a reader without English, so
the city map can name a place in either language: 58% of the open map's
records carry a Latin name only, and a Thai map left them blank.

What it builds is a READING, under the same licence as translit.py: it sits
beside the name, is never written into `name` or `nameEn`, and never drives a
slug.

Where a word's Thai comes from, best first:

  1. data/curated/thai_spelling.json — the sign spellings (Coffee → คอฟฟี่),
     Thai words as Latin signs spell them (Baan → บ้าน, Huay → ห้วย), phrases,
     and generic heads Thai writes first (Wang Kaew School → โรงเรียนวังแก้ว).
  2. rtgs_lexicon.json `loanword` / `brand` / `place`, reversed.
  3. thapsap's confirmed pairs (exports/thapsap.json), reversed.
  4. data/thai_spelling_learned.json — words this catalogue already spelt
     both ways, learned by `python3 thaiscript.py --learn` from records that
     carry a Thai name and a sourced Latin one.
  5. letters spelt out, for initials: CMU → ซีเอ็มยู.
  6. letter rules, the last resort. `read()` says how many words reached it.
"""

import functools
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "data", "curated", "thai_spelling.json")
LEARNED = os.path.join(HERE, "data", "thai_spelling_learned.json")
THAPSAP = os.path.join(os.path.dirname(HERE), "thapsap", "exports", "thapsap.json")

THAI = re.compile(r"[฀-๿]")
LETTER = {
    "a": "เอ", "b": "บี", "c": "ซี", "d": "ดี", "e": "อี", "f": "เอฟ", "g": "จี", "h": "เอช",
    "i": "ไอ", "j": "เจ", "k": "เค", "l": "แอล", "m": "เอ็ม", "n": "เอ็น", "o": "โอ", "p": "พี",
    "q": "คิว", "r": "อาร์", "s": "เอส", "t": "ที", "u": "ยู", "v": "วี", "w": "ดับเบิลยู",
    "x": "เอ็กซ์", "y": "วาย", "z": "แซด",
}


def _fold(s):
    """lower case, accents off: Café → cafe."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).replace("’", "'")


def _j(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@functools.lru_cache(maxsize=None)
def _tables():
    """(words, phrases, heads, drop): every source folded into one lookup."""
    t = _j(TABLE)
    words = {}
    # weakest first, so each later source overwrites the one before
    learned = _j(LEARNED).get("words", {})
    for k, v in learned.items():
        words[k] = v["th"] if isinstance(v, dict) else v
    seen = {}
    for e in (_j(THAPSAP).get("entries") or []):
        if str(e.get("kind", "")).startswith("thapsap:en") and e.get("en") and e.get("th"):
            k = _fold(e["en"])
            rank = (e.get("how") == "hand", e.get("seen", 0))   # a person's reading before one sighting
            if k not in seen or rank > seen[k]:
                seen[k] = rank
                words[k] = e["th"]
    lex = _j(os.path.join(HERE, "data", "curated", "rtgs_lexicon.json"))
    for part in ("place", "loanword", "brand"):
        for th, en in (lex.get(part) or {}).items():
            k = _fold(en)
            if k not in seen:
                words.setdefault(k, th)
    for part in ("alias", "word"):
        for k, v in (t.get(part) or {}).items():
            words[_fold(k)] = v
    phrases = {k: v for k, v in words.items() if " " in k}
    heads = {_fold(k): v for k, v in (t.get("head") or {}).items()}
    return words, phrases, heads, frozenset(_fold(x) for x in t.get("drop") or [])


# ---------------------------------------------------------------------------
# Letter rules: the last resort, for a word no table holds. English spelling
# is not a rule system, so this aims at what a Thai sign-writer would most
# likely put, syllable by syllable, and nothing better.
# ---------------------------------------------------------------------------
_ONSET = [("sch", "สก"), ("tch", "ช"), ("sh", "ช"), ("ch", "ช"), ("th", "ท"), ("ph", "ฟ"), ("wh", "ว"),
          ("kh", "ค"), ("qu", "คว"), ("ck", "ค"), ("gh", "ก"),
          ("b", "บ"), ("c", "ค"), ("d", "ด"), ("f", "ฟ"), ("g", "ก"), ("h", "ฮ"), ("j", "จ"), ("k", "ค"),
          ("l", "ล"), ("m", "ม"), ("n", "น"), ("p", "พ"), ("q", "ค"), ("r", "ร"), ("s", "ส"), ("t", "ท"),
          ("v", "ว"), ("w", "ว"), ("x", "ซ"), ("y", "ย"), ("z", "ซ")]
_CODA = {"b": "บ", "c": "ค", "ck": "ค", "d": "ด", "f": "ฟ", "g": "ก", "k": "ค", "l": "ล", "m": "ม",
         "n": "น", "ng": "ง", "p": "ป", "s": "ส", "t": "ท", "x": "กซ์", "z": "ซ", "sh": "ช", "ch": "ช",
         "th": "ธ", "v": "ฟ", "j": "จ", "q": "ค"}
_CLUSTER = {"bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr", "tr", "sk", "sl", "sm", "sn",
            "sp", "st", "sw", "tw", "th", "sh", "ch", "ph", "sc"}
# vowel → (open template, closed template); O = onset, F = coda
_VOWEL = [("ee", "Oี", "OีF"), ("ea", "Oี", "OีF"), ("ie", "Oี", "OีF"), ("oo", "Oู", "OูF"),
          ("ou", "เOา", "เOาF"), ("ow", "โO", "เOาF"), ("oa", "โO", "โOF"), ("ai", "ไO", "เOF"),
          ("ay", "เO", "เOF"), ("ey", "เO", "เOF"), ("ei", "เO", "เOF"), ("au", "ออ", "OอF"),
          ("aw", "Oอ", "OอF"), ("oi", "Oอย", "OอยF"), ("oy", "Oอย", "OอยF"), ("ue", "Oู", "OูF"),
          ("ui", "Oุย", "OุยF"),
          ("a", "Oา", "OัF"), ("e", "เO", "เO็F"), ("i", "Oิ", "OิF"), ("o", "โO", "OอF"),
          ("u", "Oู", "OัF"), ("y", "Oี", "OิF")]
_R_VOWEL = {"a": "Oาร์", "e": "เOอร์", "i": "เOอร์", "o": "Oอร์", "u": "เOอร์"}


def _rules(w):
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return ""
    w = re.sub(r"c(?=[eiy])", "s", w)     # soft c: city, centre
    w = re.sub(r"(.)\1+", r"\1", w)
    w = re.sub(r"^(?:wr|kn)", lambda m: m.group(0)[1], w)
    magic = len(w) > 3 and w.endswith("e") and w[-2] not in "aeiouy" and w[-3] in "aeiou" and w[-4] not in "aeiou"
    if magic:
        w = w[:-1]                        # a silent e: the vowel before it is long
    out, i, n = [], 0, len(w)
    while i < n:
        onset = ""
        while i < n and w[i] not in "aeiou" and not (w[i] == "y" and onset):
            for g, th in _ONSET:
                if w.startswith(g, i):
                    onset += th
                    i += len(g)
                    break
            else:
                i += 1
        if i >= n:                        # trailing consonants with no vowel
            if onset and out:
                out[-1] += onset[-1] + "์"
            elif onset:
                out.append(onset + "์")
            break
        O = onset or "อ"
        if O == "ส":
            O = "ซ"                        # a lone s before a vowel: ซิตี้, ซัน
        for g, op, cl in _VOWEL:
            if w.startswith(g, i):
                i += len(g)
                break
        if magic and len(g) == 1 and not re.search(r"[aeiouy]", w[i:]):
            op = cl = {"a": "เOF", "e": "OีF", "i": "ไOF", "o": "โOF", "u": "ยูF"}[g]
        if i < n and w[i] == "r" and (i + 1 == n or w[i + 1] not in "aeiouy"):
            out.append(_R_VOWEL.get(g[0], "Oอร์").replace("O", O))
            i += 1
            continue
        coda = ""
        j = i
        while j < n and w[j] not in "aeiouy":
            j += 1
        run = w[i:j]
        if j < n and run:                 # V C V: the last consonant opens the next syllable
            if run in ("sh", "ch", "th", "ph", "wh", "gh"):
                run = ""
            elif run == "ck":
                run = "c"
            elif run.startswith("ng"):
                run = "ng"
            elif len(run) >= 3 and run[-2:] in _CLUSTER:
                run = run[:-2]
            else:
                run = run[:-1]
        if run:
            first = run[:2] if run[:2] in _CODA else run[:1]
            coda = _CODA.get(first, "")
            rest = run[len(first):]
            if rest:
                coda += "".join(_CODA.get(c, "")[:1] for c in rest) + "์"
            elif j == n and coda in ("ท", "ด", "ส", "ซ", "ฟ", "ช", "ธ", "จ") and (magic or len(g) == 2):
                coda += "์"                # after a long vowel the sign marks it: ไรด์, เอาท์
        i += len(run)
        out.append((cl if coda else op).replace("O", O).replace("F", coda))
    return "".join(out)


# ---------------------------------------------------------------------------
_TOKEN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+|&|\S", re.UNICODE)


def read(name):
    """(thai reading, words that reached the letter rules). '' if none is needed or none can be made."""
    name = re.sub(r"[\u200b-\u200d\ufeff]", "", unicodedata.normalize("NFKC", name or ""))
    if not name.strip() or THAI.search(name):
        return "", 0
    words, phrases, heads, drop = _tables()
    native = _native()
    s = re.sub(r"\s*[\(\[].*?[\)\]]", "", name).strip() or name
    s = re.sub(r"\b7\s*-?\s*(?=eleven\b)", "seven ", s, flags=re.I)   # 7-Eleven: เซเว่น อีเลฟเว่น
    toks = _TOKEN.findall(s)
    folded = [_fold(t) for t in toks]
    # a name with a Thai word in it (Baan, Wat, Huay…) is a Thai name in Latin letters:
    # its short words are Thai too, even where English has the same spelling (Ban Hong)
    thaiish = any(f in native for f in folded)
    out, lead, guessed, i = [], [], 0, 0
    while i < len(toks):
        f = folded[i]
        hit = None
        for L in (4, 3, 2):               # phrases, longest first
            if i + L <= len(toks) and all(re.match(r"\w", x) for x in folded[i:i + L]):
                key = " ".join(folded[i:i + L])
                if key in heads:
                    hit = ("head", heads[key], L)
                    break
                if key in phrases:
                    hit = ("word", phrases[key], L)
                    break
        if hit:
            kind, th, L = hit
            if kind == "head" and (i + L == len(toks) or i == 0):
                lead.append(th)
            else:
                out.append((th, " ".join(folded[i:i + L]) in native))
            i += L
            continue
        i += 1
        t = toks[i - 1]
        if t.isdigit():
            out.append((t, False))
            continue
        if t == "&":
            out.append(("แอนด์", False))
            continue
        if not re.match(r"\w", t, re.UNICODE):
            if t in "-–·/,.:;!?'\"@#*+":
                continue
            out.append((t, False))
            continue
        f = re.sub(r"['’]s$", "", f)
        if f in drop:
            continue
        if f in heads and (i == len(toks) or i == 1):
            lead.append(heads[f])
            continue
        th = words.get(f) or (words.get(f[:-1]) if f.endswith("s") and len(f) > 3 else None)
        if th:
            out.append((th, f in native))
        elif len(f) == 1 or (t.isupper() and len(t) <= 3) or not re.search(r"[aeiouy]", f):
            out.append(("".join(LETTER.get(c, "") for c in f), False))
        elif (thaiish or f not in _english()) and _split(f):
            out.append((_split(f), True))
        else:
            out.append((_rules(f), False))
            guessed += 1
    # Thai words run together as Thai writes them (บ้านสวน); a loanword keeps its space
    th, prev = "".join(lead), bool(lead)
    for x, nat in out:
        if x:
            th += ("" if (nat and prev) or not th else " ") + x
            prev = nat
    return th.strip(), guessed


@functools.lru_cache(maxsize=None)
def _rev():
    """sound key → the Thai word this catalogue writes most often with that sound.

    Built from the Thai names in the catalogue, cut by translit's segmenter and
    read back by RTGS, so Witthayalai finds วิทยาลัย and Hong finds the ห้อง or
    ฮ่อง the catalogue uses most. Cached on disk beside the learned words.
    """
    loan = _loan()
    return {k: v for k, v in (_j(LEARNED).get("rev") or {}).items() if v not in loan}


@functools.lru_cache(maxsize=None)
def _loan():
    """Thai spellings of English words: never the answer for a Thai name's sound."""
    words, _, _, _ = _tables()
    native = _native()
    return frozenset(v for k, v in words.items() if k not in native)


def _build_rev():
    sys.path.insert(0, HERE)
    import translit
    seen = defaultdict(Counter)
    ix = _j(os.path.join(HERE, "docs", "api", "v1", "index.json"))
    known = translit._load_dict()
    for r in ix.get("places") or []:
        for chunk in (r.get("name") or "").split():
            if not THAI.search(chunk):
                continue
            for w in translit._segment(chunk):
                w = re.sub(r"[^\u0e00-\u0e7f]", "", w)
                if len(w) >= 2 and w in known:
                    seen[_key(translit.romanize(w, sep=""))][w] += 1
    out = {}
    for k, c in seen.items():
        (w, n), total = c.most_common(1)[0], sum(c.values())
        if len(k) >= 2 and n >= 3 and n * 2 >= total:
            out[k] = w
    return out


@functools.lru_cache(maxsize=None)
def _split(f):
    """A run-together Thai name in Latin (Maeonwittayalai) cut into words the catalogue knows."""
    words, _, _, _ = _tables()
    native = _native()
    rev = _rev()

    def piece(x, whole):
        if x in native and x in words:
            return words[x]
        k = _key(x)
        return rev.get(k) if len(k) >= 2 else None

    n = len(f)
    best = [None] * (n + 1)
    best[0] = (0, [])
    for i in range(n):
        if best[i] is None:
            continue
        for j in range(i + 2, min(n, i + 14) + 1):
            p, cost = piece(f[i:j], i == 0 and j == n), 1
            if not p and j - i <= 3 and re.search(r"[aeiou]", f[i:j]):
                p, cost = _rules(f[i:j]), 2.5     # one short piece the catalogue lacks (the On of Mae On)
            if p and (best[j] is None or best[i][0] + cost < best[j][0]):
                best[j] = (best[i][0] + cost, best[i][1] + [p])
    if best[n] is None or best[n][0] > max(2, n / 3.5):
        return ""
    return "".join(best[n][1])


@functools.lru_cache(maxsize=None)
def _native():
    """Latin spellings of THAI words (alias, learned): these join up with no space."""
    t = _j(TABLE)
    return frozenset([_fold(k) for k in t.get("alias") or {}] + list(_j(LEARNED).get("words", {})))


@functools.lru_cache(maxsize=None)
def reading(name):
    """The Thai reading of a Latin-only name, or ''."""
    return read(name)[0]


# ---------------------------------------------------------------------------
# Learning: the words this catalogue already spelt both ways.
# ---------------------------------------------------------------------------
def _key(s):
    """A coarse sound key, so Baan, Ban and บ้าน's reading Ban meet."""
    s = re.sub(r"[^a-z]", "", _fold(s))
    for a, b in (("tch", "C"), ("ch", "C"), ("sh", "C"), ("j", "C"), ("ph", "p"), ("th", "t"), ("kh", "k"),
                 ("ck", "k"), ("qu", "kw"), ("q", "k"), ("x", "ks"), ("c", "k"), ("z", "s"), ("v", "w"),
                 ("ee", "i"), ("ea", "i"), ("ie", "i"), ("oo", "u"), ("ou", "u"), ("ue", "u"), ("aa", "a"),
                 ("ae", "e"), ("oe", "e"), ("ay", "ai"), ("ey", "ei"), ("au", "o"), ("aw", "o"),
                 ("ow", "o"), ("y", "i")):
        s = s.replace(a, b)
    s = re.sub(r"(?<=[^aeiou])h|h$", "", s)   # Hong keeps its h; Phra, Khao, Kh lose theirs
    return re.sub(r"(.)\1+", r"\1", s)


def _sim(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def learn(pairs):
    """{english word: {th, n}} from (thai name, latin name) pairs.

    Each Latin word is matched to the run of one to three Thai words whose
    RTGS reading sounds most like it; a match counts only when the sound keys
    agree closely, so translated words (School ↔ โรงเรียน) teach nothing.
    """
    sys.path.insert(0, HERE)
    import translit
    tally = defaultdict(Counter)
    english = _english()
    for th, en in pairs:
        th = re.sub(r"\s*[\(\[].*?[\)\]]", "", th)
        en = re.sub(r"\s*[\(\[].*?[\)\]]", "", en)
        segs = []
        for chunk in th.split():
            if THAI.search(chunk):
                segs.append([re.sub(r"[^\u0e00-\u0e7f]", "", w) for w in translit._segment(chunk) if THAI.search(w)])
        spans = []
        for seg in segs:
            for a in range(len(seg)):
                for b in range(a + 1, min(a + 3, len(seg)) + 1):
                    w = "".join(seg[a:b])
                    spans.append((w, _key(translit.romanize(w, sep=""))))
        for tok in re.findall(r"[^\W\d_]+", en, re.UNICODE):
            f = _fold(tok)
            if len(f) < 3 or f in english:
                continue
            k = _key(f)
            # a run whose sound is much longer or shorter than the word is another word glued on
            fit = [s for s in spans if s[1] and 0.8 <= len(k) / len(s[1]) <= 1.25]
            best = max(fit, key=lambda s: (_sim(k, s[1]), -len(s[0])), default=None)
            if best and _sim(k, best[1]) >= 0.8:
                tally[f][best[0]] += 1
    out = {}
    for f, c in tally.items():
        (th, n), total = c.most_common(1)[0], sum(c.values())
        if n * 2 > total:
            out[f] = {"th": th, "n": n}
    return out


@functools.lru_cache(maxsize=None)
def _english():
    try:
        with open("/usr/share/dict/words", encoding="utf-8") as fh:
            return frozenset(w.strip() for w in fh if w.strip().islower() and len(w.strip()) > 2)
    except OSError:
        return frozenset()


def _corpus_pairs():
    ix = _j(os.path.join(HERE, "docs", "api", "v1", "index.json"))
    for r in ix.get("places") or []:
        th, en = r.get("name") or "", r.get("nameEn") or ""
        if en and THAI.search(th) and not THAI.search(en):
            yield th, en


if __name__ == "__main__":
    if "--learn" in sys.argv:
        got = learn(list(_corpus_pairs()))
        rev = _build_rev()
        with open(LEARNED, "w", encoding="utf-8") as fh:
            json.dump({"_note": "Latin words this catalogue already spelt in Thai, learned by thaiscript.py --learn "
                                "from records carrying a Thai name and a sourced Latin one (n = records agreeing); "
                                "rev = sound key → the Thai word the catalogue's own names use most for that sound.",
                       "words": dict(sorted(got.items())), "rev": dict(sorted(rev.items()))},
                      fh, ensure_ascii=False, indent=0)
        print(len(got), "words,", len(rev), "sounds →", LEARNED)
    else:
        for a in sys.argv[1:] or [l.rstrip("\n") for l in sys.stdin]:
            th, g = read(a)
            print(f"{a}\t{th}" + (f"\t({g} by rule)" if g else ""))
