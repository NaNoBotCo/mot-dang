---
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

694 Thai forms whose romanisation cannot be derived from the
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
| `irregular` | 102 | A dictionary word whose reading the letter rules cannot derive — chiefly Pali and Sanskrit forms whose written vowel is not said where it is written. |
| `loanword` | 492 | ทับศัพท์ — English written in Thai script. The reading IS the English word the spelling transcribes. |
| `place` | 77 | A place name in the spelling already on the road signs. RTGS cannot know where usage has fixed the word breaks: Mae Fah Luang, not Mae Fa Luang. |
| `brand` | 23 | A name's own Latin spelling, read off a record in the catalogue that carries it. A claim about spelling only. |

## Examples

| Thai | reading | class |
|---|---|---|
| เกษตร | Kaset | `irregular` |
| เพชร | Phet | `irregular` |
| ถาวร | Thawon | `irregular` |
| มอเตอร์ไซค์ | Motorcycle | `loanword` |
| คอมพิวเตอร์ | Computer | `loanword` |
| เชียงใหม่ | Chiang Mai | `place` |
| แม่ฟ้าหลวง | Mae Fah Luang | `place` |
| ปันนา | Punna | `brand` |
| ชมดอย | Chomdoi | `brand` |

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
