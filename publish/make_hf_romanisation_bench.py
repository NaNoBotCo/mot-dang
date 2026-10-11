#!/usr/bin/env python3
"""A benchmark for Thai romanisation on the words place names are made of.

WHY THIS EXISTS. General Thai romanisation sets are made of dictionary words.
The words a directory has to read are proper nouns and signage compounds —
เพชรเกษม, ก๋วยเตี๋ยว, ฌาปนกิจสถาน — and a romaniser can score well on the
first set while getting a road sign wrong. This names that gap by scoring the
same engine on both, with the slice stated rather than implied.

WHAT IS COMPARED. Every distinct pure-Thai word in
pythainlp/thai-romanization-dataset (CC-BY-SA-3.0), against translit.py, the
rule-based RTGS engine behind motdang.net, twice: with its curated exception
lexicon and with the rules alone. The comparison is exact after stripping to
[a-z], because RTGS spacing and capitalisation are not what is being tested.

    python3 publish/make_hf_romanisation_bench.py
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import translit  # noqa: E402

OUT = ROOT / "publish" / "hf" / "romanisation-bench"
REPO_ID = "NaNoBotCo/thai-place-name-romanisation-benchmark"

REF_REPO = "pythainlp/thai-romanization-dataset"
REF_FILE = "data/train-00000-of-00001.parquet"

THAI_ONLY = re.compile(r"^[ก-๎]+$")
THAI_RUN = re.compile(r"[ก-๎]+")
RAI_KARAN = re.compile(r"ร์.")


def norm(s):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s or "").lower())


def reference():
    """Distinct pure-Thai word → its reading, first spelling wins."""
    import duckdb
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(REF_REPO, REF_FILE, repo_type="dataset")
    out = {}
    for thai, roman in duckdb.sql(
            f"select * from read_parquet('{path}')").fetchall():
        thai = (thai or "").strip()
        roman = (roman or "").strip()
        if thai and roman and THAI_ONLY.match(thai):
            out.setdefault(thai, roman)
    return out


def name_substrings():
    """Every Thai substring of length 2..15 that occurs in a place NAME.

    A word "occurs in a place name" if it appears inside one, not if a
    segmenter chose to cut there — the segmenter is part of what is being
    measured and cannot also be the judge.
    """
    subs = set()
    for prov in ("cm", "cr"):
        recs = json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text())
        for r in recs:
            for key in ("name", "nameTh"):
                v = r.get(key)
                if not v:
                    continue
                for chunk in THAI_RUN.findall(v):
                    n = len(chunk)
                    for i in range(n):
                        for j in range(i + 2, min(i + 16, n) + 1):
                            subs.add(chunk[i:j])
    return subs


def main():
    ref = reference()
    subs = name_substrings()

    rows = []
    for thai, roman in ref.items():
        rows.append({
            "thai": thai,
            "reference": roman,
            "motdang": translit.romanize(thai),
            "in_place_names": thai in subs,
            "has_rai_karan": bool(RAI_KARAN.search(thai)),
        })

    # The ablation: the same engine with its exception table emptied. Run
    # second, and the cache is cleared first, or the lexicon-fed memo tables
    # answer for it.
    translit._LEX = {}
    translit._ELEMENTS = None
    translit._DICT = None
    for r in rows:
        r["motdang_rules_only"] = translit.romanize(r["thai"])

    for r in rows:
        ref_n = norm(r["reference"])
        r["agree"] = norm(r["motdang"]) == ref_n
        r["agree_rules_only"] = norm(r["motdang_rules_only"]) == ref_n

    (OUT / "data").mkdir(parents=True, exist_ok=True)
    with (OUT / "data" / "words.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    slices = {
        "all": rows,
        "in place names": [r for r in rows if r["in_place_names"]],
        "ร์ + consonant": [r for r in rows if r["has_rai_karan"]],
    }
    stats = {k: (len(v),
                 sum(r["agree"] for r in v),
                 sum(r["agree_rules_only"] for r in v))
             for k, v in slices.items()}

    (OUT / "README.md").write_text(card(stats, rows))
    (OUT / "LICENSE").write_text(LICENCE)

    print(f"wrote {OUT}")
    for k, (n, a, b) in stats.items():
        print(f"  {k:<16} {n:>7,}   lexicon {a / n:6.2%}   rules only {b / n:6.2%}")
    print(f"  push: python3 publish/hf_push.py {OUT} {REPO_ID}")


LICENCE = """Thai place-name romanisation benchmark

The Thai words and the `reference` readings are taken from
pythainlp/thai-romanization-dataset and carry its licence:

    Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0)
    https://creativecommons.org/licenses/by-sa/3.0/

This dataset is therefore CC BY-SA 3.0 as a whole. The `motdang` and
`motdang_rules_only` columns, the slice definitions and the scoring are from
motdang.net and are contributed under the same terms.
"""


def card(stats, rows):
    def line(k):
        n, a, b = stats[k]
        return (f"| {k} | {n:,} | {a / n:.2%} | {b / n:.2%} | "
                f"{'+' if a >= b else ''}{(a - b) / n:.2%} |")
    misses = [r for r in rows if r["in_place_names"] and not r["agree"]][:12]
    mtbl = "\n".join(f"| {r['thai']} | {r['reference']} | {r['motdang']} |"
                     for r in misses)
    return f"""---
license: cc-by-sa-3.0
language:
- th
tags:
- thai
- romanization
- rtgs
- transliteration
- benchmark
- evaluation
size_categories:
- 100K<n<1M
configs:
- config_name: default
  data_files: data/words.jsonl
---

# Thai romanisation, scored on the words place names are made of

A romaniser can do well on dictionary words and still misread a road sign.
This dataset scores one engine on both, so the difference is a number rather
than an impression.

Every distinct pure-Thai word in
[pythainlp/thai-romanization-dataset](https://huggingface.co/datasets/pythainlp/thai-romanization-dataset)
is romanised by [`translit.py`](https://huggingface.co/spaces/NaNoBotCo/thai-rtgs-romaniser),
the rule-based RTGS engine behind [motdang.net](https://motdang.net), twice:
with its [curated exception lexicon](https://huggingface.co/datasets/NaNoBotCo/thai-rtgs-romanisation-lexicon)
and with the rules alone.

## Results

| slice | words | with lexicon | rules only | the lexicon is worth |
|---|---|---|---|---|
{line("all")}
{line("in place names")}
{line("ร์ + consonant")}

The last row is where the two disagree about the job. ร์ + consonant is
English written in Thai script, and the exception lexicon deliberately reads
สคูล as *School* and นอร์ทเทิร์น as *Northern* — the word on the sign — while
the reference gives the phonetic *sakhun*, *nothoen*. Scored as exact match
those are misses. On a shop front they are what the reader needs. Read that
row as a statement about the metric, not about the engine, and read the
overall figure as understating a romaniser aimed at signage.

## Slices, defined

- **in place names** — the word occurs as a substring (2 to 15 characters) of
  a Thai place name in the Mot Dang catalogue of 88,161 places. Substring, not
  segmenter output: the segmenter is part of what is measured and cannot also
  be the judge.
- **ร์ + consonant** — the word contains ร์ followed by a consonant, the shape
  English loanwords take in Thai script.

## Scoring

Exact match after `NFKD`, lowercase, and stripping to `[a-z]`. RTGS spacing
and capitalisation are conventions, not the thing being tested. One reference
reading per word: where the source lists several, the first is kept.

## Fields

| field | |
|---|---|
| `thai` | the word |
| `reference` | the reading from pythainlp/thai-romanization-dataset |
| `motdang` | translit.py, with the curated exception lexicon |
| `motdang_rules_only` | translit.py, exception lexicon emptied |
| `agree`, `agree_rules_only` | exact match after normalisation |
| `in_place_names`, `has_rai_karan` | slice membership |

## Where it still misses, in place names

| Thai | reference | motdang |
|---|---|---|
{mtbl}

Some of these are the disagreement above rather than an error: สคูล → *School*
is the lexicon choosing the English word over its Thai spelling-out. Others are
real — นิวาสสถาน read as four syllables, มธุรส given an n it does not have.

## Licence

CC BY-SA 3.0, inherited from the reference readings. See `LICENSE`.
"""


if __name__ == "__main__":
    main()
