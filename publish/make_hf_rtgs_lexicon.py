#!/usr/bin/env python3
"""The RTGS exception lexicon — the words the letter rules cannot reach.

data/curated/rtgs_lexicon.json is what a rule-based Thai romaniser needs and
does not have: the table of forms whose reading cannot be derived from the
spelling. Sanskrit loans whose written vowel is not said where it is written
(เกษตร is kṣetra, ka-set), English written in Thai script, settled English
spellings of local place names, and Latin spellings a building's own sign uses.

Every entry was found by measuring — against a human English name held on the
same record, against pythainlp/thai-romanization-dataset, or against a road
sign — and each section of the source file says which. That is the part worth
publishing: rule engines are common, the exception table is the work.

    python3 publish/make_hf_rtgs_lexicon.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "publish" / "hf" / "rtgs-lexicon"
REPO_ID = "NaNoBotCo/thai-rtgs-romanisation-lexicon"

LEX = json.loads((ROOT / "data" / "curated" / "rtgs_lexicon.json").read_text())

CLASSES = {
    "irregular": "A dictionary word whose reading the letter rules cannot "
                 "derive — chiefly Pali and Sanskrit forms whose written "
                 "vowel is not said where it is written.",
    "loanword": "ทับศัพท์ — English written in Thai script. The reading IS "
                "the English word the spelling transcribes.",
    "place": "A place name in the spelling already on the road signs. RTGS "
             "cannot know where usage has fixed the word breaks: Mae Fah "
             "Luang, not Mae Fa Luang.",
    "brand": "A name's own Latin spelling, read off a record in the catalogue "
             "that carries it. A claim about spelling only.",
}


def rows():
    for cls in CLASSES:
        for thai, roman in LEX[cls].items():
            yield {"thai": thai, "roman": roman, "class": cls}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data").mkdir(exist_ok=True)
    recs = list(rows())
    with (OUT / "data" / "lexicon.jsonl").open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    counts = {c: sum(1 for r in recs if r["class"] == c) for c in CLASSES}
    (OUT / "README.md").write_text(card(recs, counts))
    (OUT / "LICENSE").write_text(LICENCE)
    print(f"wrote {OUT}")
    print(f"  lexicon.jsonl  {len(recs):,}  {counts}")
    print(f"  push: python3 publish/hf_push.py {OUT} {REPO_ID}")


LICENCE = """The RTGS exception lexicon
https://motdang.net

Creative Commons Attribution 4.0 International (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/

The readings follow the Royal Society of Thailand's 1999 principles of
romanization and, for the Pali and Sanskrit forms, the Royal Institute
Dictionary. The table — which words are here, and what each is read as — was
assembled at motdang.net. Attribution to motdang.net is all we ask.
"""


def card(recs, counts):
    tbl = "\n".join(f"| `{c}` | {counts[c]:,} | {d} |"
                    for c, d in CLASSES.items())
    ex = {
        "irregular": [("เกษตร", "Kaset"), ("เพชร", "Phet"), ("ถาวร", "Thawon")],
        "loanword": [("มอเตอร์ไซค์", "Motorcycle"), ("คอมพิวเตอร์", "Computer")],
        "place": [("เชียงใหม่", "Chiang Mai"), ("แม่ฟ้าหลวง", "Mae Fah Luang")],
        "brand": [("ปันนา", "Punna"), ("ชมดอย", "Chomdoi")],
    }
    exl = "\n".join(f"| {t} | {r} | `{c}` |"
                    for c, pairs in ex.items() for t, r in pairs)
    return f"""---
license: cc-by-4.0
language:
- th
- en
tags:
- thai
- romanization
- rtgs
- transliteration
- lexicon
size_categories:
- n<1K
configs:
- config_name: default
  data_files: data/lexicon.jsonl
---

# Thai RTGS romanisation — the exception lexicon

{len(recs):,} Thai forms whose romanisation cannot be derived from the
spelling, each with the reading a rule-based romaniser should use instead.

This is the companion to a rule engine, not a replacement for one. The rules
handle the regular cases; this names the irregulars. Measured: it takes the
romaniser behind [motdang.net](https://motdang.net) from 77.51% to 79.62%
agreement on 153,948 Thai words, and from 83.45% to 84.22% on the 21,425 of
them that appear in a place name — see
[the benchmark](https://huggingface.co/datasets/NaNoBotCo/thai-place-name-romanisation-benchmark)
and [the live romaniser](https://huggingface.co/spaces/NaNoBotCo/thai-rtgs-romaniser).

## Classes

| class | entries | what it is |
|---|---|---|
{tbl}

## Examples

| Thai | reading | class |
|---|---|---|
{exl}

## Why เกษตร is here

เกษตร is Sanskrit *kṣetra*. It is said *ka-set*; the letters say *ke-set*, and
a syllable walker reading it left to right produces *ketta*. No rule derives
this from the spelling, so it goes in a table. 739 records in the Mot Dang
catalogue carried one of these forms; เพชรเกษม, a national highway, read
"phetraketma" until it did not.

## What is deliberately absent

Translations. กาแฟ → Coffee and เภสัช → Pharmacy are translations, and the
readings *Kafae* and *Phesat* are correct — a translation does not belong in a
romanisation table. Only pairs sharing a consonant shape were kept.

## Fields

`thai`, `roman`, `class`.
"""


if __name__ == "__main__":
    main()
