#!/usr/bin/env python3
"""เทศกาล — the contracts that keep the festival canon and its pages aligned.

The canon (data/festivals.json) and festivals_layer.py each make promises a
test has to keep:

1. Every canon entry becomes a built page, and no orphan page survives an
   entry that was renamed or removed — the two directions of the same drift.
2. Bilingual fields travel in pairs. A cost_th without a cost_en (or a venue
   note_th without note_en) renders as a Thai-only shard on the EN toggle;
   the canon never ships half a sentence.
3. The optional sections actually reach the page: an entry that carries
   cost_th shows the เข้าฟรีไหม section, a venue that carries note_th shows
   its note. A data field nobody renders is not an answer.
4. Every entry states its confidence, and only from the known vocabulary —
   the provenance footer switches wording on it.

Run after build.py (or a standalone festivals_layer.py pass):

    python3 tests/test_festivals.py
    MD_DOCS=/path/to/scratch python3 tests/test_festivals.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  %s" % name)
    else:
        failures.append(name)
        print("  FAIL %s %s" % (name, detail))


canon = json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]
built = {p.stem for p in (DOCS / "festivals").glob("*.html")}

# ---- 1. canon <-> pages, both directions ----------------------------------
ids = {f["id"] for f in canon}
check("every canon entry has a page", ids <= built, str(ids - built))
check("no orphan festival pages", built <= ids, str(built - ids))
# 33 + the two muay thai days (วันมวยไทย 6 Feb, วันนายขนมต้ม 17 Mar), added
# 2026-08-19 with WO-12. Bump this deliberately, never to make it pass.
check("canon holds 38 festivals", len(canon) == 38, str(len(canon)))  # 35 → 36 กินเจ (WO-14), → 37 วันช้างไทย (WO-15), both 2026-08-19, → 38 ปู่แสะย่าแสะ (WO-39 shrines, 2026-08-27), on purpose

# ---- 2. bilingual fields travel in pairs ----------------------------------
PAIRED = ["name", "window", "blurb", "rule", "auspicious", "merit", "verify",
          "cost"]
for f in canon:
    for stem in PAIRED:
        th, en = f.get(stem + "_th"), f.get(stem + "_en")
        check(f"{f['id']}.{stem} th/en pair", bool(th) == bool(en)) \
            if (th or en) else None
    for v in f.get("venues") or []:
        if v.get("note_th") or v.get("note_en"):
            check(f"{f['id']} venue note th/en pair",
                  bool(v.get("note_th")) == bool(v.get("note_en")), v["th"])

# ---- 3. optional sections reach the page ----------------------------------
for f in canon:
    page = (DOCS / "festivals" / f"{f['id']}.html")
    if not page.exists():
        continue
    html = page.read_text()
    if f.get("cost_th"):
        check(f"{f['id']} cost section renders",
              "เข้าฟรีไหม" in html and f["cost_en"][:40] in html)
    for v in f.get("venues") or []:
        if v.get("note_en"):
            check(f"{f['id']} venue note renders", v["note_en"][:40] in html,
                  v["en"])

# ---- 4. confidence from the known vocabulary ------------------------------
KNOWN = {"general-knowledge", "needs-verification"}
for f in canon:
    check(f"{f['id']} confidence stated",
          f.get("confidence") in KNOWN, str(f.get("confidence")))

print()
if failures:
    print("%d contract(s) broken" % len(failures))
    sys.exit(1)
print("all good — the festival canon keeps its promises")
