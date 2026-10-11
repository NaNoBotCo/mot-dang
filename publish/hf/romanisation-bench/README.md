---
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
| all | 153,948 | 79.62% | 77.51% | +2.11% |
| in place names | 21,425 | 84.22% | 83.45% | +0.77% |
| ร์ + consonant | 2,917 | 46.59% | 50.70% | -4.11% |

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
| ทิพยเนตร | thipphayanet | thipyanet |
| นอร์ทเทิร์น | nothoen | North thoen |
| นกหงส์หยก | nokhongyok | nok ngayok |
| บ้านเทวี | banthewi | ban theo |
| มธุรส | mathurot | mathunsa |
| บ้านมิตรไมตรี | banmitmaitri | ban mitramaitri |
| นพเก้า | nopphakao | nopkao |
| นิวาสสถาน | niwatsathan | ni wa sot than |
| หวง | huang | wong |
| สคูล | sakhun | School |
| ปฏิบัติธรรม | patibattham | patibati Tham |
| แสตนเลส | saetonlet | saetnalet |

Some of these are the disagreement above rather than an error: สคูล → *School*
is the lexicon choosing the English word over its Thai spelling-out. Others are
real — นิวาสสถาน read as four syllables, มธุรส given an n it does not have.

## Licence

CC BY-SA 3.0, inherited from the reference readings. See `LICENSE`.
