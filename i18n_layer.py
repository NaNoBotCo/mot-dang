#!/usr/bin/env python3
"""Burmese (my) and Shan (shn) for the interface (WO-112, 2026-10-11).

Thai stays the base and English the gloss. A reader who taps မြန်မာ or တႆး gets a third span inside each
`.bi` pair, filled in the browser by assets/i18n.js from a dictionary file for that language. The pages
are not rebuilt for a change of wording.

    data/i18n/base.json   {"S0001": {"th": "…", "en": "…"}}   the strings, by a stable id
    data/i18n/my.json     {"S0001": "…"}                       Burmese, Unicode Myanmar script
    data/i18n/shn.json    {"S0001": "…"}                       Shan, Unicode Shan letters

base.json holds the Thai and English of the short strings the layers write with bi(): shelf and sub-shelf
names, buttons and labels, filter ticks, tag names, the questions put to owners. Sentences of more than
eight English words are not in it. The Burmese and Shan are machine drafts that no native reader has read
(Nan, 2026-10-11: ship self-written translations). Place records stay Thai and English.

emit(docs) writes docs/i18n/<lang>.json and docs/i18n.js. A served file is

    {"lang": "my", "e": {"<English>": "<translation>"},      looked up by the English text of a pair
     "t": {"<Thai>\\u001f<English>": "<translation>"},       the English texts that two Thai texts share
     "p": [["<English with {name} slots>", "<translation>"]]} strings with a slot the site fills in

tests/test_i18n.py holds the contract: every dictionary id is in base.json and the slots match.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "data" / "i18n"
LANGS = ("my", "shn")
SLOT = re.compile(r"\{[^{}]*\}")
SEP = "\u001f"


def load_base():
    return json.loads((DIR / "base.json").read_text(encoding="utf-8"))


def load_lang(lang):
    return json.loads((DIR / f"{lang}.json").read_text(encoding="utf-8"))


def slots(s):
    """The slots of a string, in order."""
    return SLOT.findall(s)


def suffix_slots(s):
    """Slots written straight after a letter, "offer{x2}": the site fills them with a plural
    ending. Burmese and Shan have none, so a translation may leave them out."""
    return [m.group(0) for m in SLOT.finditer(s) if m.start() and s[m.start() - 1].isalpha()]


def served(lang, base=None, tr=None):
    """The dictionary the browser fetches for one language."""
    base = base if base is not None else load_base()
    tr = tr if tr is not None else load_lang(lang)
    by_en = {}
    for sid, row in base.items():
        if sid.startswith("_") or sid not in tr:
            continue
        by_en.setdefault(row["en"].strip(), []).append((row["th"].strip(), tr[sid].strip()))
    e, t, p = {}, {}, []
    for en, rows in by_en.items():
        if SLOT.search(en):
            # "{x1} · {name}" holds nothing to translate, and as a pattern it would match every pair
            if re.search(r"[^\W\d_]", SLOT.sub("", en)):
                p.append([en, rows[0][1]])
        elif len({r[1] for r in rows}) == 1:
            e[en] = rows[0][1]
        else:
            for th, val in rows:
                t[th + SEP + en] = val
    return {"lang": lang, "e": e, "t": t, "p": p}


def emit(docs):
    """docs/i18n/my.json, docs/i18n/shn.json and docs/i18n.js. Returns the number of strings served."""
    out = Path(docs) / "i18n"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for lang in LANGS:
        d = served(lang)
        (out / f"{lang}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")),
                                          encoding="utf-8")
        n += len(d["e"]) + len(d["t"]) + len(d["p"])
    shutil.copyfile(ROOT / "assets" / "i18n.js", Path(docs) / "i18n.js")
    return n


if __name__ == "__main__":
    import sys
    for lang in LANGS:
        d = served(lang)
        print(lang, len(d["e"]), "by English,", len(d["t"]), "by Thai and English,", len(d["p"]), "with slots")
    sys.exit(0)
