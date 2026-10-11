#!/usr/bin/env python3
"""Romaniser readings measured against an outside corpus. Zero network.

WHERE THIS CAME FROM
--------------------
`pythainlp/thai-romanization-dataset` on Hugging Face (CC-BY-SA-3.0, 498,966
Thai->roman word pairs). Nan authorised share-alike sources on 2026-09-08, and
this was the first time translit.py's output had ever been checked against
anything but itself.

    2026-09-08, before                   after
    all pure-Thai words   79.90%   ->    80.65%   (+1,100 words of 147,229)
    place-name-shaped     86.50%   ->    87.90%   (of 31,292)

WHAT WAS ACTUALLY WRONG, AND WHAT WAS NOT
-----------------------------------------
My first reading of the misses was that a cluster rule was broken. It was not.
นคร, บพิตร, จันทร์, ศาสตร์ and อมร were all already right, so the ร and ล
cluster rules work. Two different things were wrong:

1. A REAL RULE BUG, now fixed in `_wo_is_vowel`: กว/ขว/คว followed by ย is not
   a cluster, because `-วย` is the rime /uai/. ก๋วยเตี๋ยว read `kwo tiao`.
   1,528 records carry ก๋วย. This is the same confusion that put แก้ว in the
   lexicon as Kaeo, one letter of lookahead apart.

2. SANSKRIT LOANS whose written vowel is not said where it is written —
   เกษตร (kṣetra) is ka-set, not ke-set. No rule can derive these from the
   letters; the curated lexicon is what this repo already has for them, and
   that is where they went. 739 records carried one.

A THIRD FIX WAS TRIED AND THROWN AWAY, which is why the corpus matters: making
loan clusters (ดร, บร, บล, ฟร, ฟล) form only at a word start, to stop จอดรถ
reading `chodrot`. It did not fix จอดรถ — it only moved the error to
`chodarot` — and it MEASURED WORSE, -187 words across the corpus. Reverted.
จอดรถ went to the lexicon instead. A plausible rule that measures worse is
worth more written down than a plausible rule that was never measured.

    python3 tests/test_translit_clusters.py
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import translit  # noqa: E402


def letters(s):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKC", s or "").lower())


# Fixed 2026-09-08. Each was wrong before, each is reproducible in isolation,
# so a later change that breaks one is caught without the corpus on disk.
FIXED = [
    ("ก๋วย", "kuai"),          # was kwo   — rule fix, _wo_is_vowel
    ("ก๋วยเตี๋ยว", "kuaitiao"),
    ("เกษตร", "kaset"),        # was ketta — lexicon, Sanskrit
    ("เกษม", "kasem"),         # was ketma
    ("เพชร", "phet"),          # was phetra
    ("เพชรบุรี", "phetchaburi"),
    ("เพชรเกษม", "phetkasem"),  # was phetraketma — a national highway
    ("ถาวร", "thawon"),        # was thaora
    ("จอดรถ", "chotrot"),      # was chodrot — lexicon, not a rule
    ("ที่จอดรถ", "thichotrot"),
]

# Real names out of data/canonical, so the fix is judged on our own data.
IN_THE_WILD = [
    ("วัวลายการเกษตร", "kaset"),
    ("มูลนิธิเพชรเกษม เชียงใหม่", "phetkasem"),
    ("เพชรมอเตอร์", "phet"),
]

# Words the ว/ย rule must NOT have touched: กว is a true cluster in all of
# these. The fix is one lookahead wide and this is what pins it that narrow.
UNTOUCHED = [
    ("กวาง", "kwang"), ("ควาย", "khwai"), ("ขวา", "khwa"), ("ความ", "khwam"),
    ("กล้วย", "kluai"), ("ห้วย", "huai"), ("แก้ว", "kaeo"),
    ("นคร", "nakhon"), ("บพิตร", "baphit"), ("จันทร์", "chan"),
    ("ศาสตร์", "sat"), ("อมร", "amon"), ("ได้รับ", "dairap"),
]

# KNOWN, MEASURED, DELIBERATELY NOT FIXED. Kept here so nobody rediscovers
# them as new, and so the reason survives the person who found it.
#
# พลวง  reads "phon wong". _rom_word("พลวง") is CORRECT on its own — the
#       failure is _segment splitting พล|วง before the reader ever sees the
#       word, because พลวง is not in data/search_segdict.txt. A lexicon entry
#       cannot reach it: segmentation happens first. It appears in 0 records
#       in data/canonical, so the segdict entry has not been made for it
#       alone; the general fix is dictionary coverage, not a rule.
#
# แหน   the corpus says "haen", we say "nae", and NEITHER is simply right.
#       แหน is two words: /nae/ with a silent leading ห (จอกแหน, duckweed)
#       and /haen/ where ห is the initial and น the final (หวงแหน). 44
#       records carry it and which one they mean is not decidable from the
#       letters. Changing it would trade one wrong answer for another.
KNOWN_UNFIXED = {
    "พลวง": "segmenter splits it; 0 records; needs segdict coverage, not a rule",
    "แหน": "genuinely two words (/nae/ duckweed, /haen/ in หวงแหน); undecidable",
}


def main():
    fails = []

    for th, want in FIXED:
        got = letters(translit.romanize(th))
        if got != letters(want):
            fails.append(f"REGRESSED  {th}: want '{want}', got '{got}'")

    for th, must_contain in IN_THE_WILD:
        got = letters(translit.romanize(th))
        if letters(must_contain) not in got:
            fails.append(f"IN THE WILD {th}: read '{got}', expected '{must_contain}' in it")

    for th, want in UNTOUCHED:
        got = letters(translit.romanize(th))
        if got != letters(want):
            fails.append(f"COLLATERAL {th}: want '{want}', got '{got}' — "
                         f"the ว/ย fix was meant to leave this alone")

    # The lexicon is data; a reading that vanishes from it is a silent
    # regression, so its absence is a failure here rather than a surprise
    # in the next build.
    lex = json.loads((ROOT / "data" / "curated" / "rtgs_lexicon.json")
                     .read_text(encoding="utf-8"))
    for w in ("เกษตร", "เพชร", "ถาวร", "เกษม", "จอดรถ"):
        if w not in lex.get("irregular", {}):
            fails.append(f"LEXICON   {w} is gone from rtgs_lexicon.json['irregular']")

    if fails:
        print(f"translit reading defects: {len(fails)}")
        for f in fails:
            print("  " + f)
        return 1

    print(f"translit readings: {len(FIXED) + len(IN_THE_WILD) + len(UNTOUCHED)} "
          f"checks pass")
    for w, why in KNOWN_UNFIXED.items():
        print(f"  known, not fixed: {w} — {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
