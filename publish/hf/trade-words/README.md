---
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

1,782 Thai trade terms taken from the tags on business listings in
Chiang Mai and Chiang Rai — the words the city uses for what a shop does —
each with an RTGS reading and an English gloss. Plus 403
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
| trade terms | 1,782 |
| with an English gloss | 1,782 (100%) |
| with an RTGS reading | 1,782 (100%) |
| administrative names | 403 |

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
| `curated` | 1,540 |
| `thesaurus` | 164 |
| `record` | 78 |

Nothing is machine translated. A gloss is the dictionary equivalence for the
word on the sign — ซ่อม is to repair, ปะยาง is to patch a tyre, หยอดเหรียญ is
coin-operated. Where a term is English written in Thai script the reading is
RTGS throughout, so ซ่อมมอเตอร์ไซค์ reads *Som Motoesai* rather than half a
reading and half a translation.

## The twenty most common

| Thai | reading | gloss | places |
|---|---|---|---|
| ตู้น้ำดื่มหยอดเหรียญ | Tunam Duem Yotrian | coin-op drinking-water dispenser | 238 |
| ซักผ้าหยอดเหรียญ | Sakpha Yotrian | coin-op laundry | 200 |
| ซ่อมมอเตอร์ไซค์ | Som Motoesai | motorcycle repair | 191 |
| ปะยางมอเตอร์ไซค์ | Pa Yang Motoesai | motorcycle tyre patching | 170 |
| ตู้น้ำหยอดเหรียญ | Tunam Yotrian | coin-op water dispenser | 162 |
| ถ่ายน้ำมันเครื่องมอเตอร์ไซค์ | Thai Namman Khrueang Motoesai | motorcycle oil change | 144 |
| ตู้น้ำดื่ม | Tunam Duem | drinking-water dispenser | 122 |
| ทำฟัน | Thamfan | dental work | 91 |
| จัดฟัน | Chatfan | braces, orthodontics | 88 |
| เครื่องซักผ้าหยอดเหรียญ | Khrueangsakpha Yotrian | coin-op washing machine | 83 |
| ซักอบรีด | Sakabrit | dry clean | 79 |
| ไวนิล | Wainin | vinyl banner | 71 |
| ร้านสะดวกซัก | Ran Saduaksak | self-service laundrette | 56 |
| ถ่ายเอกสาร | Thaieksan | copy shop | 54 |
| ป้าย | Pai | label | 53 |
| อุดฟัน | Utfan | dental filling | 48 |
| ซ่อมทีวี | Som Thiwi | TV repair | 47 |
| อาหารสัตว์ | Ahansat | animal feed | 46 |
| ป่าช้า | Pa Cha | cremation ground | 42 |
| สุสาน | Susan | cremation ground | 42 |

## Licence

Readings and glosses CC BY 4.0. See `LICENSE` for the word list's origin.
