#!/usr/bin/env python3
"""The carving-village register stands on what it can show, or this fails. WO-51.

    python3 tests/test_tawai.py
    MD_DOCS=/path/to/scratch python3 tests/test_tawai.py

Run after build.py. The rules it enforces are this order's, and each one is
here because getting it wrong would put a specific falsehood on the page:

  1. EVERY dated claim resolves to a source. Each row that carries `src`
     names a key in `sources`, and every source has a `ref` and a `fetched`
     date. A history page whose dates float free is a rumour with a byline.
  2. Every reader-facing field is a PAIR. A Thai sentence with no gloss (or
     the reverse) renders as half a page to half the readers.
  3. Carry-flags are the souvenir page's four and no others, and the two
     regulated woods AGREE with data/curated/wildlife.json's wood row. Two
     pages disagreeing about whether rosewood needs papers is worse than
     either page alone, and this is the only mechanism stopping it.
  4. The shelves.json fix is still there and is still ADDITIVE — the Ban
     Tawai record keeps its market shelf and its URL. The whole argument of
     the page is that nothing was taken away from the crawl's own reading.
  5. The fair keeps at least two editions with different months. The page's
     one practical warning is that the fair drifts; an editions list that
     quietly collapsed to one month would make the warning unreadable.
  6. After a build: tawai.html + tawai.css exist, every h2 anchor the page
     promises is present, the three drawn figures carry aria-labels, the
     souvenir door resolves, and no unfilled Python None or bare %d leaked.
  7. The drawn geometry stays inside its viewBox — the chain of hands is
     six boxes on a 760-wide canvas with no room to spare, and a seventh
     trade added to the register would silently push one off the edge.
"""
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = pathlib.Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))

fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)


reg = json.loads((ROOT / "data" / "curated" / "carve.json").read_text())
src = reg["sources"]

# ── 1 · every dated claim names a source that exists and was fetched ──────
for key, s in src.items():
    check(bool(s.get("ref")), f"source {key} has no ref")
    check(bool(s.get("fetched")), f"source {key} has no fetched date")
    check(bool(s.get("note")), f"source {key} has no note")

rows = []
for e in reg["timeline"]:
    rows.append(("timeline " + str(e["ce"]), e, ("th", "en"), e["src"]))
for h in reg["honours"]:
    rows.append(("honour " + h["en"], h, ("th", "en", "by_th", "by_en"), h["src"]))
for h in reg["hands"]:
    rows.append(("hand " + h["key"], h, ("th", "en", "note_th", "note_en"), h["src"]))
for w in reg["woods"]:
    rows.append(("wood " + w["en"], w, ("th", "en", "use_th", "use_en", "latin"), w["src"]))
for z in reg["zones"]:
    rows.append(("zone " + z["key"], z, ("th", "en", "what_th", "what_en"), z["src"]))
for s_ in reg["road"]:
    rows.append(("road " + s_["key"], s_,
                 ("th", "en", "craft_th", "craft_en", "where_th", "where_en",
                  "note_th", "note_en"), s_["src"]))
for m in reg["masters"]:
    rows.append(("master " + m["name_en"], m,
                 ("name_th", "name_en", "honour_th", "honour_en", "by_th", "by_en",
                  "for_th", "for_en"), m["src"]))
for ed in reg["fair"]["editions"]:
    rows.append(("fair edition %d" % ed["n"], ed, ("th", "en"), ed["src"]))

for label, row, fields, key in rows:
    check(key in src, f"{label}: src {key!r} is not in sources")
    for f in fields:
        check(bool(str(row.get(f) or "").strip()), f"{label}: field {f} is empty")

# ── 2 · the free-standing pairs ───────────────────────────────────────────
for label, obj, pairs in (
        ("village", reg["village"], [("name_story_th", "name_story_en"),
                                     ("old_ground_th", "old_ground_en"),
                                     ("pin_note_th", "pin_note_en"),
                                     ("peoples_th", "peoples_en")]),
        ("royal_note", reg["royal_note"], [("th", "en")]),
        ("carry_note", reg["carry_note"], [("th", "en")]),
        ("getting_there", reg["getting_there"], [("th", "en")]),
        ("fair", reg["fair"], [("th", "en"), ("where_th", "where_en"),
                               ("by_th", "by_en"), ("drift_th", "drift_en")])):
    for a, b in pairs:
        check(bool(str(obj.get(a) or "").strip()) and bool(str(obj.get(b) or "").strip()),
              f"{label}: {a}/{b} is not a filled pair")
for a in reg["asks"]:
    for f in ("th", "en", "why_th", "why_en"):
        check(bool(str(a.get(f) or "").strip()), f"ask {a.get('en')}: {f} is empty")

# The Buddha-image section. It is the one thing here the souvenir page cannot
# carry — its handicraft row says the law leaves handicraft wide open, which is
# true of a carved elephant and not true of a carved Buddha — so it has to keep
# its source, its caveat, and its own dated sheet.
ex = reg["export"]
check(ex["src"] in src, "the export section's source is not in sources")
for f in ("title_th", "title_en", "lead_th", "lead_en", "ask_th", "ask_en",
          "caveat_th", "caveat_en"):
    check(bool(str(ex.get(f) or "").strip()), f"export section: {f} is empty")
check(len(ex["rows"]) >= 4, "the export section has lost rows")
for r in ex["rows"]:
    check(bool(r.get("th")) and bool(r.get("en")), "an export row is not a filled pair")
check("2560" in ex["caveat_th"] or "2017" in ex["caveat_en"],
      "the export caveat no longer dates the sheet it quotes — a fee table with no "
      "edition on it reads as current forever")
# Published organisational contacts only — no personal mobiles, and the source
# has to say who published it.
for c in reg["contacts"]["rows"]:
    check(c["src"] in src, f"contact {c.get('en')}: src is not in sources")
    for f in ("th", "en", "tel"):
        check(bool(str(c.get(f) or "").strip()), f"contact {c.get('en')}: {f} is empty")
    check(re.match(r"^0[\d-]{8,12}$", c["tel"]) is not None,
          f"contact {c['en']}: {c['tel']!r} is not a Thai number in the printed form")

check(len(reg["unverified"]) >= 3,
      "the unverified list has shrunk — every figure on this page came from "
      "somebody else and at least the travel, hours and shop-count caveats belong there")
for u in reg["unverified"]:
    check(" · " in u, f"unverified line is not bilingual: {u[:40]}")
# A source that refused us is printed as a refusal, not silently dropped.
check(len(reg.get("attempted", [])) >= 1,
      "the attempted list is empty — three hosts refused this order and saying so is "
      "the difference between 'we could not read it' and 'it does not say that'")
for a in reg.get("attempted", []):
    for f in ("ref", "tried", "what", "th", "en"):
        check(bool(str(a.get(f) or "").strip()), f"attempted {a.get('ref','?')[:40]}: {f} is empty")

# ── 3 · carry-flags agree with the souvenir register ──────────────────────
FLAGS = {"ok", "ask", "papers", "no"}
for w in reg["woods"]:
    check(w["carry"] in FLAGS, f"wood {w['en']}: carry flag {w['carry']!r} is not one "
                               f"of the souvenir page's four")
wild = json.loads((ROOT / "data" / "curated" / "wildlife.json").read_text())
wood_row = [i for i in wild["items"] if i["key"] == "wood"]
check(len(wood_row) == 1, "wildlife.json no longer holds a wood row to agree with")
if wood_row:
    want = wood_row[0]["carry"]
    for w in reg["woods"]:
        if re.search(r"Dalbergia|Aquilaria", w["latin"]):
            check(w["carry"] == want,
                  f"wood {w['en']}: carry={w['carry']} but souvenir.html says {want} — "
                  f"two pages disagreeing about paperwork is worse than one")
check(reg["carry_note"]["href"] == "souvenir.html",
      "carry_note no longer points at the page that holds the flags")

# ── 4 · the shelves.json fix, still additive ──────────────────────────────
TAWAI_ID = "cm-osm-node-2055923138"
shelves = json.loads((ROOT / "data" / "curated" / "shelves.json").read_text())["shelves"]
entry = shelves.get(TAWAI_ID)
check(entry is not None, "shelves.json no longer gives the Ban Tawai record a craft shelf")
if entry:
    check("crafts" in (entry.get("add_sub") or []), "Ban Tawai shelf entry lost its crafts sub")
    check(bool(entry.get("source")), "Ban Tawai shelf entry has no source")
    check("remove_cat" not in entry and "remove_sub" not in entry,
          "the Ban Tawai entry has started removing shelves — shelves.json ADDS")

canonical = {}
for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
    for r in json.loads(f.read_text()):
        canonical[r["id"]] = r
rec = canonical.get(TAWAI_ID)
check(rec is not None, "the Ban Tawai record has gone from canonical data")
if rec:
    check("market" in (rec.get("cat") or []),
          "the Ban Tawai record lost its market shelf — the fix was supposed to ADD one")
    v = reg["village"]
    check(abs(rec["lat"] - v["lat"]) < 0.02 and abs(rec["lng"] - v["lng"]) < 0.02,
          "the register's village pin has drifted from the record it describes")

# ── 5 · the fair still drifts, and the register still shows it ────────────
eds = reg["fair"]["editions"]
check(len(eds) >= 2, "the fair needs at least two editions to show the drift")
months = {re.search(r"(January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)", e["en"]).group(1)
          for e in eds if re.search(r"[A-Z][a-z]+", e["en"])}
check(len(months) >= 2,
      "every listed fair edition falls in the same month — the page's one practical "
      "warning is that it does not")

# ── 6 and 7 · the built page ──────────────────────────────────────────────
if (DOCS / "index.html").exists() or (DOCS / "tawai.html").exists():
    check((DOCS / "tawai.html").exists(), "built docs/ has no tawai.html")
    check((DOCS / "tawai.css").exists(), "built docs/ has no tawai.css")
    if (DOCS / "tawai.html").exists():
        html = (DOCS / "tawai.html").read_text()
        for anchor in ("ground", "teak", "start", "hands", "wood", "phra",
                       "ask", "walk", "fair", "road", "register"):
            check(f'id="{anchor}"' in html, f"tawai.html lost its #{anchor} section")
        check(html.count("<svg") >= 3, "tawai.html is missing one of the three figures")
        n_lab = len(re.findall(r'<svg[^>]*aria-label="', html))
        check(n_lab >= 3,
              f"only {n_lab} of the drawn figures carry an aria-label — a picture a "
              f"screen reader cannot hear is not on the page for that reader")
        check('href="souvenir.html"' in html, "tawai.html lost the souvenir door")
        # the paper version has to BE there, not just be linked
        if 'href="reader/carve-words.pdf"' in html:
            check((DOCS / "reader" / "carve-words.pdf").exists(),
                  "tawai.html links reader/carve-words.pdf and the build did not copy it "
                  "— a linked sheet that 404s is worse than no sheet")
        check(">None<" not in html and "None</" not in html.replace("None</a", ""),
              "tawai.html leaks a Python None")
        check("%d" not in html and "%s" not in html,
              "tawai.html leaks an unfilled format placeholder")
        for e in reg["timeline"]:
            check(str(e["ce"]) in html, f"tawai.html does not render timeline row {e['ce']}")
        for w in reg["woods"]:
            check(w["latin"].split(" ")[0] in html,
                  f"tawai.html does not render the wood {w['en']}")

# geometry: the chain has to fit the canvas it is drawn on
BW, GAP, CANVAS = 112, 16, 760
n_hands = len(reg["hands"])
check(n_hands * BW + (n_hands - 1) * GAP <= CANVAS,
      f"the chain of hands is now {n_hands} trades and no longer fits the 760-wide "
      f"canvas — widen the viewBox in carve_layer._chain_svg before adding another")

if fails:
    print(f"test_tawai: {len(fails)} failure(s)")
    for m in fails:
        print("  FAIL", m)
    sys.exit(1)
print(f"test_tawai: OK — {len(reg['timeline'])} dated rows, {len(reg['woods'])} woods, "
      f"{len(reg['honours'])} register honours, {len(src)} sources"
      + (", page checked" if (DOCS / "tawai.html").exists() else ", no build to check"))
