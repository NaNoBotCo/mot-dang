#!/usr/bin/env python3
"""คำบนป้าย — the words on the signs, as a Hugging Face dataset.

data/trade_lexicon.json holds the vocabulary Chiang Mai and Chiang Rai name
their own trades in: 1,782 Thai terms read off shop listings, each with an
RTGS reading and an English gloss, plus 403 administrative place names. It
reaches a reader today as /trades.html and as a field on a place page. This
puts the same table where a machine can take it.

WHY THIS AND NOT THE PLACES. The places dataset is a directory of businesses.
This is a lexicon: a word, how it is said, what it means, and how often the
corpus met it. Nothing here names a business.

    python3 publish/make_hf_trade_words.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "publish" / "hf" / "trade-words"
REPO_ID = "NaNoBotCo/thai-trade-words-chiang-mai"

LEX = json.loads((ROOT / "data" / "trade_lexicon.json").read_text())


def trade_rows():
    for thai, e in LEX["tags"].items():
        yield {
            "thai": thai,
            "reading": e.get("reading"),
            "gloss": e.get("gloss"),
            "gloss_source": e.get("glossVia"),
            "n_places": e.get("n") or 0,
            "shelves": list(e.get("shelves") or []),
        }


def area_rows():
    for thai, e in LEX["areas"].items():
        yield {"thai": thai, "reading": e.get("reading"), "kind": e.get("kind")}


def write(name, rows):
    path = OUT / "data" / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def main():
    trades = write("trade_words", trade_rows())
    areas = write("areas", area_rows())

    glossed = sum(1 for r in trades if r["gloss"])
    read = sum(1 for r in trades if r["reading"])
    by_src = {}
    for r in trades:
        by_src[r["gloss_source"]] = by_src.get(r["gloss_source"], 0) + 1
    top = sorted(trades, key=lambda r: -r["n_places"])[:20]

    (OUT / "README.md").write_text(card(trades, areas, glossed, read, by_src, top))
    (OUT / "LICENSE").write_text(LICENCE)

    print(f"wrote {OUT}")
    print(f"  trade_words.jsonl  {len(trades):,}  "
          f"({glossed:,} glossed, {read:,} read)")
    print(f"  areas.jsonl        {len(areas):,}")
    print(f"  push: python3 publish/hf_push.py {OUT} {REPO_ID}")


LICENCE = """คำบนป้าย — Thai trade words of Chiang Mai and Chiang Rai
https://motdang.net/trades.html

THE READINGS AND THE GLOSSES — the RTGS reading of each term and its English
equivalent, written and corrected by hand at motdang.net:

    Creative Commons Attribution 4.0 International (CC BY 4.0)
    https://creativecommons.org/licenses/by/4.0/

THE WORD LIST is the set of distinct Thai trade terms that appear as tags on
records in the Mot Dang catalogue, which were read from a Thai business
directory. Individual words are not anyone's property; the counts are counts
over our own corpus. No business is named in this dataset.

Attribution to motdang.net is all we ask.
"""


def card(trades, areas, glossed, read, by_src, top):
    rows = "\n".join(
        f"| {r['thai']} | {r['reading']} | {r['gloss']} | {r['n_places']:,} |"
        for r in top)
    src = "\n".join(f"| `{k}` | {v:,} |" for k, v in
                    sorted(by_src.items(), key=lambda kv: -kv[1]))
    return f"""---
license: cc-by-4.0
language:
- th
- en
tags:
- thai
- lexicon
- romanization
- rtgs
- chiang-mai
size_categories:
- 1K<n<10K
configs:
- config_name: trade_words
  default: true
  data_files: data/trade_words.jsonl
- config_name: areas
  data_files: data/areas.jsonl
---

# คำบนป้าย — Thai trade words of Chiang Mai and Chiang Rai

{len(trades):,} Thai trade terms taken from the tags on business listings in
Chiang Mai and Chiang Rai — the words the city uses for what a shop does —
each with an RTGS reading and an English gloss. Plus {len(areas):,}
administrative place names (tambon, amphoe, city, province) with their
readings.

    ซ่อมมอเตอร์ไซค์   Som Motoesai      motorcycle repair              191 places
    ตู้น้ำดื่มหยอดเหรียญ  Tunam Duem Yotrian coin-op drinking-water dispenser 238
    ฌาปนกิจสถาน       Chapanakit Sathan  crematorium

Built for [motdang.net](https://motdang.net), a directory of 88,161 places in the
two provinces. Terms of this kind are absent from general Thai-English
dictionaries: they are compound signage vocabulary, not headwords.

## Coverage

| | |
|---|---|
| trade terms | {len(trades):,} |
| with an English gloss | {glossed:,} ({glossed / len(trades):.0%}) |
| with an RTGS reading | {read:,} ({read / len(trades):.0%}) |
| administrative names | {len(areas):,} |

## Fields — `trade_words`

| field | |
|---|---|
| `thai` | the term as it is written on the listing |
| `reading` | RTGS romanisation, from [`translit.py`](https://huggingface.co/spaces/NaNoBotCo/thai-rtgs-romaniser) |
| `gloss` | English equivalent of the word, not a description of the shop |
| `gloss_source` | `curated` (written by hand), `thesaurus`, or `record` (a listing carried its own English) |
| `n_places` | records in the Mot Dang catalogue carrying this tag |
| `shelves` | site categories whose Thai label is this term |

`areas` carries `thai`, `reading`, `kind`.

## How the glosses were made

| source | terms |
|---|---|
{src}

Nothing is machine translated. A gloss is the dictionary equivalence for the
word on the sign — ซ่อม is to repair, ปะยาง is to patch a tyre, หยอดเหรียญ is
coin-operated. Where a term is English written in Thai script the reading is
RTGS throughout, so ซ่อมมอเตอร์ไซค์ reads *Som Motoesai* rather than half a
reading and half a translation.

## The twenty most common

| Thai | reading | gloss | places |
|---|---|---|---|
{rows}

## Licence

Readings and glosses CC BY 4.0. See `LICENSE` for the word list's origin.
"""


if __name__ == "__main__":
    main()
