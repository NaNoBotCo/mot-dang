#!/usr/bin/env python3
"""การอ่านชื่อ — which names this catalogue romanises WRONGLY, across every shelf.

Zero network. WO-56's sweep, generalised from the housing shelf to the whole
catalogue, because the fault it found is not a housing fault:

    every state register writes Thai only     ONAB 2,084 · OBEC 1,302 ·
                                              MOPH 490 · OPEC 168 (100%) ·
                                              FDA 907 · condominiums 367 (98%)
    58% of OSM records carry Latin only       8,676 of 14,851
    records holding both scripts               24%

So the reading is the only thing that can introduce a place's two halves to
each other, and a wrong reading is a place nobody can find in the language
they type. `translit.reading` is right about Thai; it is wrong about ENGLISH
WRITTEN IN THAI, where the letters say one thing and the sign says another —
ยูนีค read letter by letter is Yu Nik and the building is called Unique.

WHAT THIS PRINTS. Every Thai word in a name that the RTGS lexicon does not
know, ranked by how many records carry it, with two pieces of evidence beside
it so a person can rule quickly:

  reads     what the letter rules give today
  corpus    a Latin name held in THIS catalogue whose consonants match, which
            is the strongest evidence available offline — the same word
            written in the other alphabet by whoever mapped it

Nothing is written. A ruling goes in data/curated/rtgs_lexicon.json:
`loanword` when the Thai spells an English word, `brand` when a name's own
Latin spelling was read off a record here (that entry names the record).

    python3 importers/audit_readings.py                  # every shelf
    python3 importers/audit_readings.py --cat wat --top 60
"""
import argparse
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import translit as T      # noqa: E402
import namejoin as N      # noqa: E402

THAI = re.compile(r"[ก-๙]+")
# A karan (ทัณฑฆาต) or a doubled vowel sign is the orthography of a borrowed
# word far more often than of a Thai one. Not a rule, a hint printed beside
# the count so a reader can spot the loanwords in a long list.
FOREIGN_HINT = re.compile(r"[์็]|ิ์|ี้|ั้|่ส$")


def load(cat=None):
    out = []
    for pv in ("cm", "cr"):
        p = os.path.join(ROOT, "data", "canonical", f"{pv}.json")
        if not os.path.exists(p):
            continue
        for r in json.load(open(p, encoding="utf-8")):
            if cat and cat not in (r.get("cat") or []):
                continue
            r["_pv"] = pv
            out.append(r)
    return out


def latin_index(records):
    """{consonant skeleton: [Latin names]} over every Latin name held."""
    idx = collections.defaultdict(set)
    for r in records:
        for nm in (r.get("name"), r.get("nameEn"), r.get("nameTh")):
            if not nm or not re.search(r"[A-Za-z]{3}", nm):
                continue
            for w in re.findall(r"[A-Za-z]{4,}", nm):
                s = N.skeleton(w.lower())
                if len(s) >= 2:
                    idx[s].add(w)
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", default=None, help="one shelf, default every shelf")
    ap.add_argument("--top", type=int, default=80)
    ap.add_argument("--min", type=int, default=2, help="records a word must appear in")
    a = ap.parse_args()

    recs = load(a.cat)
    everything = load(None)
    known = set(T._lexicon())
    lidx = latin_index(everything)

    counts = collections.Counter()
    where = collections.defaultdict(list)
    for r in recs:
        nm = (r.get("name") or "").strip()
        if not THAI.search(nm):
            continue
        for run in THAI.findall(nm):
            for w in T._segment(run):
                if len(w) < 3 or w in known:
                    continue
                counts[w] += 1
                if len(where[w]) < 3:
                    where[w].append(nm[:38])

    label = a.cat or "every shelf"
    print(f"{label}: {len(recs):,} records · {len(counts):,} Thai words the "
          f"lexicon does not know\n")
    print(f"{'word':16} {'n':>4}  {'reads as':22} {'corpus Latin':24} example")
    print("-" * 108)
    shown = 0
    for w, n in counts.most_common():
        if n < a.min or shown >= a.top:
            continue
        reading = T.reading(w)
        sk = N.skeleton(reading.lower().replace(" ", ""))
        hits = sorted(lidx.get(sk, ()))[:2]
        hint = "·" if FOREIGN_HINT.search(w) else " "
        print(f"{w:16} {n:4}{hint} {reading[:22]:22} {', '.join(hits)[:24]:24} "
              f"{where[w][0][:30]}")
        shown += 1
    print(f"\n· = spelled like a borrowed word (karan or a doubled vowel sign)")
    print("A ruling goes in data/curated/rtgs_lexicon.json — `loanword` for "
          "English in Thai script,\n`brand` for a Latin spelling read off a "
          "record here (name the record in the entry).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
