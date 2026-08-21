#!/usr/bin/env python3
"""Open a new reader question — the stub in data/asked.json and the note.

    python3 asked_new.py <key> --q-th "…" --q-en "…" [--via facebook|line|site|walk]
    python3 asked_new.py <key> --q-th "…" --q-en "…" --from-suggestion 3f2a9c1e
    python3 asked_new.py <key> --q-th "…" --q-en "…" --gap

This is step 2 of the daily loop (see CLAUDE.md, "A reader question is a
data record"). It does two things and refuses to do a third:

  1. Appends a DRAFT entry to data/asked.json — `draft: true` keeps it out of
     asked_layer.load(), so nothing renders, nothing draws, no reply can be
     made, and tests/test_asked.py (a hard gate in the walk) skips it. When
     the find/lead/notes are filled, deleting "draft" by hand is the release.
  2. Writes notes/asked-<key>-<date>.md — question, what was searched, the
     sources with dates, the leads (name + why + the one act that clears it),
     the decision, prices, and the four-outputs checklist. Refuses to
     overwrite a note that exists.

It does NOT stub a shelf child in data/categories.json or a facet in
data/facets.json. Both need the trade's own word and the door-survey
sentence (ask_th/ask_en), and a placeholder name is exactly the error that
made the ขัดขี้ไคล question unanswerable for a year — a shelf called
"Korean scrub" would have hidden five shops that call it something else.
Those two edits stay deliberate; this prints where they go.

`--from-suggestion ID` records `via: "suggest:<id>"` — the queue id only,
never the address the reader left. That address lives in _incoming/ and
nowhere else.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASKED = ROOT / "data" / "asked.json"
NOTES = ROOT / "notes"

NOTE = """# {key} — {q_th}

*{q_en}*

- asked_on: {date}
- via: {via}
- status: DRAFT (`draft: true` in data/asked.json — delete it when the four outputs exist)

## The question, in the trade's own word

Which Thai word does Chiang Mai actually sell this under? Search that, not the
reader's English. (ขัดขี้ไคล was the lesson: "Korean scrub" returned one paid
ad; the Thai word returned a trade with price boards.)

- word tried:
- `python3 importers/reconcile_names.py _incoming/asked-{key}-names.txt` →

## Sources (url · fetched YYYY-MM-DD · what it supports)

-

## Leads — name · what is missing · why it is not in the catalogue yet · the one act that clears it

- [ ]

## Decision

- found N / gap:
- shelf (child key, in the trade's word) or none:
- facet (key + ask_th/ask_en) or none — remember the three places + KNOWN_EMPTY:
- what was NOT recorded, and why:

## Prices

All `_pricesVerified: false` until somebody reads a board on the street.

## The four outputs

- [ ] records with dated sources in data/curated/additions-*.json → `importers/import_all.py`
- [ ] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [ ] `python3 make_shelf_cards.py --only asked-{key}` → `build.py` → `tests/test_asked.py`
- [ ] `python3 make_post.py {key}` pasted back{done_line}
"""

REMINDER = """
next:
  1. names → _incoming/asked-{key}-names.txt, then
     python3 importers/reconcile_names.py _incoming/asked-{key}-names.txt
  2. records → data/curated/additions-chiang-mai.json (cm-curated-<slug>, sources[{{type,ref,fetched}}],
     _pricesVerified:false on any price) → python3 importers/import_all.py
     shelf?  data/categories.json child {{key,th,en,match:{{sub}}}} — the trade's own word
     facet?  data/facets.json + worker/worker.js FACET_KEYS + build.py, with ask_th/ask_en;
             empty shelf → tests/test_facets.py KNOWN_EMPTY with its reason
  3. python3 asked_check.py {key}
  4. fill find / lead / notes in data/asked.json, delete "draft"; finish {note}
  5. python3 make_shelf_cards.py --only asked-{key} && python3 build.py && python3 tests/test_asked.py
  6. python3 make_post.py {key}{done}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--q-th", required=True)
    ap.add_argument("--q-en", required=True)
    ap.add_argument("--via", default="facebook",
                    choices=["facebook", "line", "site", "walk", "email", "other"])
    ap.add_argument("--from-suggestion", metavar="ID",
                    help="the sug: id from sync_suggestions.py --kind question")
    ap.add_argument("--gap", action="store_true",
                    help="open as a candid gap (no find selector, no card)")
    args = ap.parse_args()

    key = args.key
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", key):
        sys.exit(f"key must be a url-safe slug, got {key!r}")
    doc = json.loads(ASKED.read_text())
    if any(e["key"] == key for e in doc["asked"]):
        sys.exit(f"{key} is already in data/asked.json")

    today = datetime.date.today().isoformat()
    via = f"suggest:{args.from_suggestion}" if args.from_suggestion else args.via
    entry = {"key": key, "q": {"th": args.q_th, "en": args.q_en},
             "asked_on": today, "via": via, "draft": True}
    if args.gap:
        entry.update({"gap": True,
                      "panel": {"th": "ยังไม่มีในสารบัญ", "en": "not in the catalogue yet"}})
    else:
        entry.update({"find": {"prov": "cm"}, "show": "phone"})
    entry.update({"lead": [{"th": "", "en": ""}], "notes": []})
    doc["asked"].append(entry)
    ASKED.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

    NOTES.mkdir(exist_ok=True)
    note = NOTES / f"asked-{key}-{today}.md"
    if note.exists():
        sys.exit(f"{note} already exists — not overwriting")
    done = (f"; python3 importers/sync_suggestions.py --done {args.from_suggestion}"
            if args.from_suggestion else "")
    note.write_text(NOTE.format(key=key, q_th=args.q_th, q_en=args.q_en, date=today,
                                via=via, done_line=done and f"\n- [ ] {done[2:]}"))
    print(f"draft entry {key} → data/asked.json   (via {via})")
    print(f"note → {note.relative_to(ROOT)}")
    print(REMINDER.format(key=key, note=note.relative_to(ROOT), done=done))


if __name__ == "__main__":
    main()
