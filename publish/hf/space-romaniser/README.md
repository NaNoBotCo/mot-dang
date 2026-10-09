---
title: Thai RTGS Romaniser
emoji: 🐜
colorFrom: red
colorTo: yellow
sdk: static
app_file: index.html
pinned: false
license: cc-by-4.0
short_description: Thai to RTGS romanisation by rule, from motdang.net
---

# ไทย → RTGS

Rule-based Royal Thai General System romanisation: a syllable walker over Thai
orthography, plus a curated table of forms the letters cannot reach. No model,
no server — `translit.py` runs in your browser under Pyodide, unmodified from
the repo it ships in.

- benchmark — [thai-place-name-romanisation-benchmark](https://huggingface.co/datasets/NaNoBotCo/thai-place-name-romanisation-benchmark)
- exception lexicon — [thai-rtgs-romanisation-lexicon](https://huggingface.co/datasets/NaNoBotCo/thai-rtgs-romanisation-lexicon)
- trade vocabulary — [thai-trade-words-chiang-mai](https://huggingface.co/datasets/NaNoBotCo/thai-trade-words-chiang-mai)
- the places — [mot-dang-chiang-mai-chiang-rai](https://huggingface.co/datasets/NaNoBotCo/mot-dang-chiang-mai-chiang-rai)

`translit.py` and `data/` are CC BY 4.0, from [motdang.net](https://motdang.net).
`dict.txt` bundles words from
[pythainlp/thai-romanization-dataset](https://huggingface.co/datasets/pythainlp/thai-romanization-dataset)
and carries CC BY-SA 3.0.
