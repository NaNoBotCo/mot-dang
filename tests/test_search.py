#!/usr/bin/env python3
"""The search page's own logic, exercised against the real index.

This exists because of a bug nobody would have found by reading the code. The
matcher tested the whole query as one unbroken substring, so `rajavej hospital`
scored zero against "Rajavej Chiang Mai Hospital" — the page was built, indexed
and linked, and simply could not be found by anyone typing its name. 5,190 of
the catalogue's names run three words or longer, so the same hole swallowed
`maharaj hospital`, `nimman coffee` and `dental clinic chiang mai`.

The logic is JavaScript living inside build.py, so the test lifts that exact
block out and runs it under node against docs/data/index.json. No reimplementing
in Python — a paraphrase would pass while the shipped code failed. The block
runs from the table set-up down to the first DOM write, which since WO-24 also
covers the two decisions the page renders from:

  * which rich door (data/curated/search_panels.json) a query opens, and
  * the namesake split — ช้าง answers twice in this city, the camps and the
    gates/roads/shops that merely CARRY the elephant in their name, and the
    page files them under separate headers.

    python3 tests/test_search.py          (after a build; MD_DOCS for scratch)
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build.py")
DOCS = os.environ.get("MD_DOCS", os.path.join(ROOT, "docs"))
INDEX = os.path.join(DOCS, "data", "index.json")

# The extracted block: pure decisions, no fetch above it, no DOM below it.
# START sits just after the table fetches resolve; END is the first DOM write.
START = "const SEG=segText.split"
END = "document.getElementById('rescount')"

ENP = "cm-curated-elephant-nature-park"
MAESA = "cm-curated-maesa-elephant-camp"

# Each case: query, then only the expectations that matter for it.
#   id_in    — this record id must be among the returned ids
#   tier     — the reported worst tier must be exactly this
#   none     — True: the query must return nothing
#   panel    — the rich door that must open ('' asserts NO panel opens)
#   on_id    — this id must land in the on-shelf rows
#   names_nonempty / on_nonempty — that partition must hold something
#   namesake_lookup — resolve a known namesake from the index by name and
#                     require it in the names partition
CASES = [
    ("rajavej hospital", {"id_in": "cm-osm-way-97675282", "tier": "exact"},
     "the bug this file exists for: words with two others wedged between them"),
    ("Rajavej Hospital", {"id_in": "cm-osm-way-97675282"}, "case must not matter"),
    ("hospital rajavej", {"id_in": "cm-osm-way-97675282"}, "word order must not matter"),
    ("โรงพยาบาลราชเวช", {"id_in": "cm-osm-way-97675282"},
     "Thai carries no spaces — one term, matched as it always was"),
    ("rajavey hospitl", {"id_in": "cm-osm-way-97675282", "tier": "loose"},
     "two typos still land, and the tier says it loosened"),
    ("maharaj hospital", {}, "the same word-gap shape, different place"),
    ("wat phra singh", {}, "a name that WAS contiguous must not regress"),
    ("", {"none": True}, "empty query finds nothing rather than everything"),
    ("   ", {"none": True}, "whitespace is not a search"),
    # Not zero: the phonetic key folds a consonant run, so zzzzqqq lands one
    # edit from SK House's key. Three near-noise rows is livable; the
    # catalogue is not. A tighter key for consonant runs is a search-core
    # precision item, not this page's.
    ("zzzzqqq", {"max_n": 5}, "a real miss stays tiny — fuzziness must not match all"),
    ("kow soi", {}, "romanisation drift — signage in this city uses all of them"),
    ("ข้าวซอย", {}, "the same dish in Thai finds the same places"),
    ("coffee", {"panel": ""},
     "the shelf is matched — and no rich door exists for coffee, so none opens"),
    ("นวด", {"panel": "massage"}, "a Thai shelf word reaches the massage places"),
    ("temple", {"panel": "wat"}, "an English word for a Thai shelf"),
    # WO-24: the rich doors, and the namesake split.
    ("elephant", {"panel": "chang", "on_id": ENP, "names_nonempty": True,
                  "namesake_lookup": True},
     "the chang door opens; camps on the shelf, ช้างเผือก the hospital never among them"),
    ("ช้าง", {"panel": "chang", "on_id": ENP, "names_nonempty": True},
     "the same door in Thai"),
    ("จ๊าง", {"panel": "chang"},
     "the Northern form arrives through the thesaurus, no extra listing needed"),
    ("ปางช้างแม่สา", {"id_in": MAESA, "on_id": MAESA},
     "a camp by its own Thai name lands on the shelf side"),
    ("womens health", {"panel": "womens-health"},
     "the query the screenshot was full of — the curated page answers first"),
    ("มวยไทย", {"panel": "muaythai"}, "the fight-night door"),
    # เรียนทำอาหาร/ทำอาหาร still open the door by query substring, but the
    # segmenter takes ทำอาหาร apart (ทำ + อา + ร) so the ROWS are noise —
    # a search-core vocabulary item (the term belongs in the thesaurus, and a
    # thesaurus term is never segmented), noted in ROLLOUT's gap list. The
    # English form both opens the door and finds the schools.
    ("cooking class", {"panel": "cooking"}, "class-shaped query opens the class door"),
    ("มังสวิรัติ", {"panel": ""},
     "a vegetarian wants dinner, not a cooking class — the mined shelf table "
     "sends this word to the cooking shelf and the door must NOT follow it"),
    ("ห้องน้ำ", {"panel": "toilets"}, "the nearest-toilet door"),
    ("yi peng", {"panel": "festivals"}, "a festival name opens the festival door"),
    ("วัด", {"panel": "wat", "on_nonempty": True},
     "the bare word is in no mined table — the door itself lifts the shelf"),
    # WO-25 groundwork — the ongoing-care gemba (2026-08-21).
    ("menopause", {"panel": "womens-health"},
     "zero corpus rows for this word — the curated page is the true answer"),
    ("วัยทอง", {"panel": "womens-health"},
     "the sign word for the same clinic, through the same door"),
    ("hormone", {"panel": "womens-health"},
     "hormone care doors to the women's-health page and its glossary"),
    ("international clinic", {"panel": "care"},
     "the mined table maps 'clinic' to the chang shelf (lifted from the "
     "elephant-hospital child's name); shelf_stops keeps this out of the "
     "elephant door, and since the care page exists it answers instead"),
    ("elephant clinic", {"panel": "chang"},
     "the stop is per word: elephant itself still opens the chang door"),
    # WO-25 door 1 — the care register (data/curated/care.json) is read, so
    # the queries that returned NOTHING on the gemba walk have a true answer.
    # These assert the DOOR, not rows: the corpus holds no cardiology record
    # and inventing one is the failure the register exists to avoid.
    ("cardiologist", {"panel": "care"},
     "zero rows in the corpus; the read register names two stated heart clinics"),
    ("โรคหัวใจ", {"panel": "care"},
     "the Thai word, which used to return fried-meatball stalls"),
    ("อายุรกรรม", {"panel": "care"},
     "the department word for a lifelong condition — 2,522 rows of noise before"),
    ("FMP", {"panel": "care"},
     "the VA claim programme — used to loosen to a hotel named Champa"),
    ("คลินิกพิเศษ", {"panel": "care"},
     "the after-hours clinic, the phrase rarely printed in English"),
    ("ใบรับรองแพทย์", {"panel": "care"},
     "the certificate a visa desk asks for; 2,107 partial rows before"),
    ("มวยไทย", {"panel": "muaythai"},
     "a nearby door must not be swallowed by care's long query list"),
    # WO-26 — trans health (2026-08-21). The curated register
    # (data/curated/transhealth.json) feeds the index via TRANSHEALTH_ROWS in
    # build.py, so these land on real places; the door is the panel. Route and
    # reference grades carry no topic words by design — an unconfirmed
    # hospital must not answer "transgender" as if it had said yes.
    ("transgender", {"panel": "trans-health", "id_in": "cm-curated-mplus-chiangmai"},
     "zero corpus rows carry this word — the register rows and the door answer"),
    ("ข้ามเพศ", {"panel": "trans-health"},
     "the Thai term, and every compound carrying it, by query substring"),
    ("กะเทย", {"panel": "trans-health"},
     "the community's own word reaches the same door"),
    ("transport", {"panel": ""},
     "trans- the prefix is not trans the topic — a bus-and-songthaew reader "
     "must not be doored to a health page"),
    ("ฮอร์โมน", {"id_in": "cm-curated-mplus-chiangmai"},
     "hormone in Thai lands on the places that state hormone care"),
    # WO-27 — realestate (2026-08-21). The panel triggers by variants and
    # query substring only, NEVER by the mined shelves table: that table
    # sends หมู่บ้าน and "buildings" to the realestate shelf, and a person
    # typing a village's name is not hunting a housing estate — the same
    # overfire the มังสวิรัติ guard holds for cooking.
    ("condo", {"panel": "realestate"},
     "the residential door, and the ring reaches อพาร์ตเมนต์/หอพัก rows too"),
    ("แมนชั่น", {"panel": "realestate"},
     "a Mansion in Thailand is a monthly building — the Thai word opens the door"),
    ("หอพัก", {"panel": "realestate"},
     "the dorm word opens the residential door"),
    ("หมู่บ้านป่าไผ่", {"panel": ""},
     "a village name is not a housing-estate query — the mined หมู่บ้าน mapping "
     "must not door it (the realestate panel carries no shelves trigger)"),
]


def extract_js():
    src = open(BUILD, encoding="utf-8").read()
    i = src.index(START)
    j = src.index(END, i)
    return src[i:src.rindex("\n", i, j)]


def find_namesake(idx):
    """A place that carries ช้างเผือก in its NAME and is not on the chang
    shelf — โรงพยาบาลช้างเผือก, the human hospital, is the canonical one
    (its name-fence was a WO-19 gotcha). Resolved from the index rather than
    pinned to an id, so a re-crawl that renumbers it cannot rot this test."""
    for e in idx:
        name = (e.get("n") or "") + " " + (e.get("e") or "")
        cats = (e.get("c") or []) + (e.get("su") or [])
        if "ช้างเผือก" in name and "chang" not in cats and "โรงพยาบาล" in name:
            return e["id"]
    for e in idx:  # any namesake will do if the hospital ever leaves the index
        name = e.get("n") or ""
        cats = (e.get("c") or []) + (e.get("su") or [])
        if "ช้างเผือก" in name and "chang" not in cats:
            return e["id"]
    return None


def main():
    if not os.path.exists(INDEX):
        print(f"✗ {INDEX} missing — run build.py first")
        return 1
    js = extract_js()
    idx = json.load(open(INDEX, encoding="utf-8"))
    namesake = find_namesake(idx)
    # The block widens spellings through the REAL tables — a stub would let a
    # broken group or a broken panel trigger ship green.
    thes_path = os.path.join(ROOT, "data", "search_thesaurus.json")
    thes = json.load(open(thes_path, encoding="utf-8"))["groups"] \
        if os.path.exists(thes_path) else []
    seg_path = os.path.join(ROOT, "data", "search_segdict.txt")
    seg = open(seg_path, encoding="utf-8").read() if os.path.exists(seg_path) else ""
    shelves_path = os.path.join(ROOT, "data", "search_shelves.json")
    shelves = json.load(open(shelves_path, encoding="utf-8")) \
        if os.path.exists(shelves_path) else {"shelves": {}}
    panels_path = os.path.join(ROOT, "data", "curated", "search_panels.json")
    panels = json.load(open(panels_path, encoding="utf-8")) \
        if os.path.exists(panels_path) else {"panels": []}
    cfg = json.load(open(os.path.join(ROOT, "data", "categories.json"), encoding="utf-8"))
    catwords = {c["key"]: f'{c["th"]} · {c["en"]}' for c in cfg["categories"]}
    subwords = {}
    for c in cfg["categories"]:
        for ch in c.get("children") or []:
            k = (ch.get("match") or {}).get("sub") or ch.get("key")
            if k:
                subwords.setdefault(k, f'{ch.get("th","")} {ch.get("en","")}'.strip())
    harness = (
        "import fs from 'fs';\n"
        "import {createRequire} from 'module';\n"
        "const require=createRequire(import.meta.url);\n"
        f"const SEARCHCORE=require({json.dumps(os.path.join(ROOT, 'assets', 'searchcore.js'))});\n"
        f"const MD_CATWORDS={json.dumps(catwords, ensure_ascii=False)};\n"
        f"const MD_SUBWORDS={json.dumps(subwords, ensure_ascii=False)};\n"
        f"const thesDoc={{groups:{json.dumps(thes, ensure_ascii=False)}}};\n"
        f"const segText={json.dumps(seg, ensure_ascii=False)};\n"
        f"const shelfDoc={json.dumps(shelves, ensure_ascii=False)};\n"
        f"const panelDoc={json.dumps(panels, ensure_ascii=False)};\n"
        f"const idx=JSON.parse(fs.readFileSync({json.dumps(INDEX)},'utf8'));\n"
        "function search(q){\n" + js + "\n"
        "return {n:found.length,tier:found.length?found[0].tier:null,\n"
        "ids:hits.map(e=>e.id),panel:panel?panel.id:null,\n"
        "on:onHits.map(e=>e.id),names:nameHits.map(e=>e.id)};}\n"
        "const out=JSON.parse(process.argv[2]).map(q=>search(q));\n"
        "console.log(JSON.stringify(out));\n")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        proc = subprocess.run(["node", path, json.dumps([c[0] for c in CASES])],
                              capture_output=True, text=True, timeout=240)
    finally:
        os.unlink(path)
    if proc.returncode:
        print("✗ search block failed to run under node:\n" + proc.stderr[-800:])
        return 1
    got = json.loads(proc.stdout)

    bad = 0
    for (q, want, note), r in zip(CASES, got):
        faults = []
        if want.get("none"):
            if r["n"] != 0:
                faults.append(f"expected nothing, found {r['n']}")
        elif want.get("max_n") is not None:
            if r["n"] > want["max_n"]:
                faults.append(f"found {r['n']}, cap {want['max_n']}")
        elif not want.get("panel") and r["n"] < 1 and "panel" not in want:
            faults.append("found nothing")
        if "id_in" in want and want["id_in"] not in r["ids"]:
            faults.append(f"{want['id_in']} not in results")
        if "tier" in want and r["tier"] != want["tier"]:
            faults.append(f"tier {r['tier']!r}, wanted {want['tier']!r}")
        if "panel" in want:
            expected = want["panel"] or None
            if r["panel"] != expected:
                faults.append(f"panel {r['panel']!r}, wanted {expected!r}")
        if "on_id" in want and want["on_id"] not in r["on"]:
            faults.append(f"{want['on_id']} not in on-shelf rows")
        if want.get("on_nonempty") and not r["on"]:
            faults.append("on-shelf rows empty")
        if want.get("names_nonempty") and not r["names"]:
            faults.append("namesake rows empty")
        # The invariant is that a namesake NEVER sits among the on-shelf rows —
        # that interleaving is the harm this order removed. Being past the
        # 200-row cap is fine; being filed as a camp is not.
        if want.get("namesake_lookup"):
            if namesake is None:
                faults.append("no ช้างเผือก namesake found in the index at all")
            elif namesake in r["on"]:
                faults.append(f"namesake {namesake} filed among the on-shelf rows")
        # A loosened tier that returns the whole catalogue is not a search.
        # A strict match on a shelf word is a different thing: "coffee" really
        # does reach 1,976 cafes, and capping that would forbid shelf matching.
        if r["tier"] in ("loose", "partial") and r["n"] > 200:
            faults.append(f"loosened to {r['n']} — a loosened tier must not return the catalogue")
        ok = not faults
        extra = "" if ok else " — " + "; ".join(faults)
        print(f"  {'✓' if ok else '✗'} {q!r:22} n={r['n']:<5} tier={r['tier'] or '-':9} "
              f"panel={r['panel'] or '-':13} {note}{extra}")
        bad += not ok
    # Every internal door on every panel must be a page the build wrote — a
    # panel pointing at a missing page is a wrong answer wearing gold.
    for p in panels.get("panels", []):
        for d in p.get("doors", []):
            href = d.get("href", "")
            if href.startswith("http"):
                continue
            target = os.path.join(DOCS, href.rstrip("/"),
                                  "index.html") if href.endswith("/") \
                else os.path.join(DOCS, href)
            if not os.path.exists(target):
                print(f"  ✗ panel {p['id']}: door {href!r} is not in the built site")
                bad += 1
    print(f"\n{'✓ search page OK' if not bad else f'✗ {bad} search case(s) failed'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
