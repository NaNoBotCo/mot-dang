#!/usr/bin/env python3
"""Read the massage shelf's own names for the modality they declare. Zero network.

Same contract as audit_shelves.py: this script never edits canonical data. It
reports, and --emit prints shelves.json-ready entries for a human to paste after
looking at them. Every entry it proposes carries `source: "osm name: <name>"`,
which is a source type shelves.json already accepts — the claim is not ours, it
is the shop's, read off the sign it chose for itself.

Why bother when the yield is a fifth. Measured 2026-08-17: 57 of 294 records
name a modality, 237 say nothing. It is free, it seeds the sixteen new children
on the massage shelf so they are not all wireframe on day one, and the shops
that DO name their modality are exactly the ones a reader can already choose
between. The other four fifths wait for somebody at the door, and a shelf that
says nothing is the correct output for a shop nobody has visited.

(An earlier loose pass over the same names scored 36% by counting "spa" as a
modality. It is not one — see the note below — and the real figure is 19%.)

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Infer the sensitive shelf from anything but the venue's own word. ap-ob-nuat
    is proposed only when อาบอบนวด (or a romanisation of it) is IN THE NAME,
    which is the venue advertising itself. Nothing about hours, street, staff or
    tone of signage is evidence of anything here and none of it is read.
  * Treat "spa" as a modality on its own. Half the shopfronts in Chiang Mai say
    spa; it tells you the tier, not what the hands do, so it proposes spa-body
    only alongside a scrub/steam/sauna word.

Usage:
  python3 importers/audit_massage.py           # report
  python3 importers/audit_massage.py --emit    # shelves.json-ready JSON
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"

# Thai needs no word boundary (no spaces between words); Latin does, or "spa"
# matches "Spafford" and "oil" matches "Boiler". \b on every Latin alternative.
RULES = [
    ("thai-traditional", r"นวดแผนไทย|แผนโบราณ|นวดไทย|\bthai\s+(?:traditional\s+)?massage\b"
                         r"|\btraditional\s+thai\b|\bnuad\s+(?:thai|boran)\b|\bboran\b"),
    ("foot",             r"นวดเท้า|ฝ่าเท้า|\bfoot\s+(?:massage|reflex\w*|spa)\b"
                         r"|\breflexolog\w*\b"),
    ("oil",              r"นวดน้ำมัน|อโรมา|\boil\s+massage\b|\baroma(?:therapy)?\b"),
    ("prakhop",          r"ประคบ|สมุนไพร|\bherbal\s+(?:compress|massage|ball)\b"),
    ("chap-sen",         r"จับเส้น|\bchap\s*sen\b"),
    ("tok-sen",          r"ตอกเส้น|\btok\s*-?\s*sen\b"),
    ("yam-khang",        r"ย่ำขาง|\byam\s*-?\s*khang\b"),
    ("ratchasamnak",     r"ราชสำนัก|\bratchasamnak\b|\broyal\s+(?:thai\s+)?(?:court|style)\b"),
    ("office-syndrome",  r"ออฟฟิศซินโดรม|\boffice\s+syndrome\b"),
    ("face",            r"นวดหน้า|กัวซาหน้า|\bfacial\b|\bface\s+(?:massage|gua\s*sha)\b"),
    ("cupping",          r"ครอบแก้ว|\bcupping\b"),
    ("postpartum",       r"ทับหม้อเกลือ|อยู่ไฟ|หลังคลอด|\bpost[\s-]?(?:partum|natal)\b"),
    ("prenatal",         r"นวดคนท้อง|\bpre[\s-]?natal\b|\bpregnan\w*\b"),
    ("blind-massage",    r"คนตาบอด|ผู้พิการทางสายตา|\bblind\b"),
    # The venue's own word for itself, and the only route to this shelf.
    ("ap-ob-nuat",       r"อาบอบนวด|\bap\s*-?\s*ob\s*-?\s*nuad?t?\b|\bsoapy\b"),
]

# spa-body needs a second word: "spa" alone is a tier, not a treatment.
SPA_BODY = r"ขัดผิว|สครับ|อบไอน้ำ|อบสมุนไพร|ซาวน่า|\bscrub\b|\bsauna\b|\bsteam\b|\bbody\s+wrap\b"


def load():
    recs = []
    for f in ("cm.json", "cr.json"):
        recs += json.loads((CANON / f).read_text())
    return [r for r in recs if "massage" in (r.get("cat") or [])]


def name_of(r):
    return " ".join(str(x) for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)


def read_name(r):
    """Modality keys the record's own name declares. Empty is a fine answer."""
    n = name_of(r).lower()
    hits = [k for k, pat in RULES if re.search(pat, n, re.I)]
    if re.search(SPA_BODY, n, re.I):
        hits.append("spa-body")
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    args = ap.parse_args()

    recs = load()
    already = set(json.loads(SHELVES.read_text())["shelves"])
    found = [(r, read_name(r)) for r in recs]
    hit = [(r, h) for r, h in found if h and r["id"] not in already]

    if args.emit:
        out = {}
        for r, h in hit:
            out[r["id"]] = {
                "note": f"{r.get('name')} — modality read off the shop's own name",
                "add_sub": sorted(h),
                "source": f"osm name: {name_of(r)}",
                # The record's own date, not today's: this attests when that
                # name was last seen, which is the thing being cited.
                "fetched": r.get("updatedAt", ""),
            }
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return

    tally = Counter(k for _, h in found for k in h)
    silent = [r for r, h in found if not h]
    print(f"massage records: {len(recs)}")
    print(f"  name declares a modality: {len(found) - len(silent)}"
          f" total, {len(hit)} of them new to shelves.json")
    print(f"  name declares nothing:    {len(silent)}  "
          f"({100 * len(silent) // max(1, len(recs))}% — these wait for the door survey)")
    print()
    for k, _ in RULES:
        print(f"  {k:18} {tally.get(k, 0)}")
    print(f"  {'spa-body':18} {tally.get('spa-body', 0)}")
    print()
    print("Sample of what it read (check these before --emit):")
    for r, h in hit[:14]:
        print(f"  {'+'.join(sorted(h)):28} {name_of(r)[:56]}")
    if any("ap-ob-nuat" in h for _, h in hit):
        print()
        print("NOTE: ap-ob-nuat proposed. Confirm the venue's own name really "
              "carries the word before pasting — that shelf takes nothing else "
              "as evidence.")


if __name__ == "__main__":
    main()
