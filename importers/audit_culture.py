#!/usr/bin/env python3
"""Read the culture shelves' own names for what they declare. Zero network.

Same contract as audit_massage.py and audit_shelves.py, and it is the whole
point of the script: this never edits canonical data. It reports, and --emit
prints shelves.json-ready entries for a human to look at before pasting. Every
proposed entry carries `source: "osm name: <name>"` or `source: "osm tag:
museum=<v>"` — the claim is not ours, it is the place's own, read off the sign
it chose or the tag a mapper put on it.

Five reports, because the six domains Nan asked for are in five different
states (notes/culture-shelf-proposal-2026-08-18.md has the measurement):

  LIBRARY  20 records, all lens points inherited from mueang-map. amenity=library
           has never been crawled. 17 of the 20 are CMU faculty libraries.
  MUSEUM   72 records under two undifferentiated subs. OSM's own museum=* subtag
           is on the raw elements and is DROPPED at import — this script reads it
           back out of cache/overpass/ (local files, still zero network).
  CRAFT    85 records on shopping/crafts, gathered by a craft=*/gift dragnet.
  BOOKS    0 records. shop=books is in no query group. This report therefore
           scans the WHOLE corpus, not a shelf — the only bookshops that can
           exist today are ones crawled under some other tag, the way Hub 53
           sat under guesthouse until the 2026-08-07 coworking sweep found it.
  STRAYS   records on the craft shelf whose own name says they are something
           else (a latex showroom, a barber, a guesthouse). Proposed for a look,
           never moved — shelves.json is additive and does not argue with the
           crawl.

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Infer access. Nothing here proposes "open to the public" or "members only"
    for any library, ever. That is a question for somebody at the desk, and a
    wrong answer either sends a person to a locked door or stops them going.
  * Infer price, or that a place charges at all.
  * Rank, score, or mark anything culturally important. The register (OTOP, GI,
    ครูศิลป์ของแผ่นดิน) carries that, sourced and dated, or nothing does.
  * Sort craft places into real and touristic. "Is anyone making anything here
    today" is visible from the pavement and is a door question; deserving is
    not a question this directory asks.

Usage:
  python3 importers/audit_culture.py             # all five reports
  python3 importers/audit_culture.py --only craft
  python3 importers/audit_culture.py --emit      # shelves.json-ready JSON
"""
import argparse
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"
OVERPASS = ROOT / "cache" / "overpass"

# Thai needs no word boundary (no spaces between words); Latin does, or "art"
# matches "Cartier" and "gem" matches "Gemma". \b on every Latin alternative.
#
# Thai patterns carry their own traps and each fence below is there because a
# real record tripped it:
#   ร่ม   alone matches รพ.สต. ร่มเกล้า and เรือนร่มไม้ — require ร่มบ่อสร้าง/ทำร่ม.
#   วัวลาย alone matches every health station on Wualai Road — it is a ROAD as
#         well as the silver quarter, so it is not evidence of silver by itself.
#   ไหม   is the Thai question particle. Only ผ้าไหม counts as silk.
#   ตุง   is a common syllable; only ตุงล้านนา is taken.
#   เตา   matches เตาถ่าน หมูกะทะ (a BBQ buffet). Only named kiln words count.

LIBRARY_RULES = [
    ("library-national",   r"หอสมุดแห่งชาติ|\bnational\s+library\b"),
    ("library-public",     r"ห้องสมุดประชาชน|\bpublic\s+library\b"),
    ("library-university", r"ห้องสมุดคณะ|ห้องสมุดวิทยาลัย|สำนักหอสมุด|ห้องสมุดมหาวิทยาลัย"
                           r"|หอสมุดกลาง"
                           r"|\b(?:faculty|university|college|campus)\s+library\b"
                           r"|\blibrary\s+of\s+(?:the\s+)?faculty\b"
                           # "Faculty of Veterinary Medicine Library" — the head
                           # noun trails the faculty name, so the two-word form
                           # above never fires. Any name that says both faculty
                           # and library is a faculty library.
                           r"|\bfaculty\s+of\b(?=.*\blibrary\b)"),
    ("library-temple",     r"ห้องสมุดวัด|หอไตร|หอธรรม|\btemple\s+library\b"),
    ("library-childrens",  r"ห้องสมุดเด็ก|ห้องสมุดเยาวชน|\bchildren'?s?\s+library\b"),
    ("library-foreign",    r"\bAUA\b|\bbritish\s+council\b|\balliance\s+fran\w*\b"
                           r"|\bgoethe\b|\bjapan\s+foundation\b|สถาบันภาษา"),
]

MUSEUM_RULES = [
    ("museum-national",     r"พิพิธภัณฑสถานแห่งชาติ|\bnational\s+museum\b"),
    # (?<!ห) or every "พิพิธภัณฑ์แห่งชาติ จังหวัดเชียงใหม่" reads as a temple
    # museum: จังหวัด, the word for province, ends in the letters ว ั ด. Thai has
    # no spaces to fence on, so the trap is a bare substring. Note the fence is
    # ห and not จัง — จังหวัด is จ ั ง ห ว ั ด, so the character immediately
    # before วัด is ห. ไข้หวัด (flu) is caught by the same fence. No temple name
    # has ห directly before วัด.
    ("museum-temple",       r"พิพิธภัณฑ์\s*(?<!ห)วัด|(?<!ห)วัด.{0,12}พิพิธภัณฑ์|หอธรรม"
                            r"|\btemple\s+museum\b"),
    ("museum-ethnographic", r"ชาติพันธุ์|ชาวเขา|ไทลื้อ|ไตลื้อ|ล้านนาศึกษา"
                            r"|\bhmong\b|\bkaren\b|\blahu\b|\bakha\b|\blisu\b"
                            r"|\btribal\b|\bhill\s*tribe\b|\bethnograph\w*\b"),
    ("museum-house",        r"คุ้ม(?:เจ้า)?|บ้านโบราณ|เรือนโบราณ|\bhouse\s+museum\b"
                            r"|\bheritage\s+house\b|\bmansion\b"),
    ("museum-local",        r"ศูนย์การเรียนรู้|พิพิธภัณฑ์ท้องถิ่น|พิพิธภัณฑ์ชุมชน"
                            r"|\blocal\s+museum\b|\blearning\s+cent(?:er|re)\b"
                            r"|\bcommunity\s+museum\b"),
    ("art-studio",          r"สตูดิโอ|\bstudio\b|\bart\s+space\b|\bresidency\b"
                            r"|\batelier\b|\bworkshop\b"),
]

# OSM's own museum=* subtag, read back from the cached Overpass responses.
# 13 elements carry it and every one is dropped at import today.
#
# museum=art maps to museum-art and NOT to either gallery shelf. An art museum
# is not an artist-run space and is not a dealer; an earlier draft of this map
# sent museum=art to gallery-artistrun and promptly proposed it for Art in
# Paradise (a paid trick-art attraction) and for พิพิธภัณฑสถานแห่งชาติ เชียงแสน
# (a national museum). OSM cannot tell us who sells the work on a wall, so
# nothing here proposes gallery-commercial or gallery-artistrun. That pair is a
# door question and starts on the KNOWN_EMPTY list.
MUSEUM_TAG = {
    "history":    "museum-local",
    "local":      "museum-local",
    "art":        "museum-art",
    "railway":    "museum-subject",
    "nature":     "museum-subject",
    "technology": "museum-subject",
    "transport":  "museum-subject",
    "ethnology":  "museum-ethnographic",
}

CRAFT_RULES = [
    ("silver",        r"เครื่องเงิน|ช่างเงิน|\bsilversmith\b|\bsilverware\b"
                      r"|\bsilver\s+(?:shop|factory|craft|handicraft)\b"),
    ("lacquer",       r"เครื่องเขิน|\blacquer\w*\b"),
    ("celadon",       r"ศิลาดล|เซลาดอน|เครื่องปั้นดินเผา|เตาเม็งราย|เตาสังคโลก"
                      r"|\bceladon\b|\bpottery\b|\bceramics?\b|\bkiln\b|\bstoneware\b"),
    ("woodcarving",   r"แกะสลักไม้|ไม้แกะสลัก|บ้านถวาย|\bwood\s*-?\s*carv\w*\b"
                      r"|\bwoodwork\w*\b|\btawai\b"),
    ("textile",       r"ผ้าทอ|ทอผ้า|ผ้าฝ้าย|ผ้าชาติพันธุ์|ผ้าปัก|\bhand\s*woven\b"
                      r"|\bweav\w*\b|\btextiles?\b|\bcotton\s+(?:mill|craft|shop)\b"),
    ("silk",          r"ผ้าไหม|\bsilk\b"),
    ("sa-paper",      r"กระดาษสา|\bsa\s+paper\b|\bmulberry\s+paper\b"
                      r"|\bhandmade\s+paper\b|\bpaper\s+making\b"),
    ("umbrella",      r"ร่มบ่อสร้าง|ทำร่ม|หัตถกรรมร่ม|\bumbrella\b"),
    ("tung",          r"ตุงล้านนา|โคมล้านนา|โคมยี่เป็ง"),
    ("bamboo-rattan", r"จักสาน|เครื่องจักสาน|\brattan\b|\bwicker\b|\bbamboo\s+craft\b"),
    ("craft-village", r"หมู่บ้านหัตถกรรม|ศูนย์หัตถกรรม|บ้านถวาย|บ่อสร้าง"
                      r"|\bhandicraft\s+(?:village|cent(?:er|re))\b|\botop\b|โอทอป"),
]

BOOK_RULES = [
    ("bookshop-used",    r"หนังสือมือสอง|\bused\s+book\w*\b|\bsecond\s*-?\s*hand\s+book\w*\b"
                         r"|\bbackstreet\s+book\w*\b|\bgecko\s+book\w*\b"),
    ("bookshop-foreign", r"หนังสือภาษาอังกฤษ|\benglish\s+book\w*\b|\bforeign\s+book\w*\b"
                         r"|\basia\s+books\b|\bkinokuniya\b"),
    ("bookshop-dhamma",  r"หนังสือธรรมะ|ธรรมบรรณาคาร|\bdhamma\s+book\w*\b"
                         r"|\bbuddhist\s+book\w*\b"),
    # The chain names are the trap here, not the Thai. SE-ED must keep its
    # hyphen: an optional-separator form (\bse\s*-?\s*ed\b) matches the ordinary
    # English word "Seed", and duly filed Liberated Seed Roasters as a bookshop.
    ("bookshop-new",     r"ร้านหนังสือ|\bbook\s*(?:shop|store)\b|\bbookshop\b|\bbookstore\b"
                         r"|นายอินทร์|ซีเอ็ด|\bse-ed\w*\b|\bb2s\b|\bnaiin\b"),
    ("stationery",       r"เครื่องเขียน|หนังสือเรียน|\bstationer\w*\b|\bnewsagent\b"),
]

# Names on the craft shelf that say, in their own words, that they are something
# else. Proposed for a human look; nothing is moved by this script.
STRAY_RULES = [
    ("latex/mattress",  r"\blatex\b|ยางพารา|ที่นอนยาง|\bmattress\b|\bpillow\b"),
    ("tattoo/barber",   r"\btattoo\b|\bbarber\b|สักลาย|ร้านตัดผม"),
    ("lodging",         r"\bguest\s*house\b|\bhostel\b|\bhotel\b|เกสต์เฮ้าส์|ที่พัก"),
    ("market",          r"\bmarket\b|ตลาด|\bbazaar\b|\bplaza\b"),
    ("cosmetics",       r"\bcosmetic\w*\b|เครื่องสำอาง|\bspa\b|\bbeauty\b"),
    ("food",            r"\bcafe\b|\bcoffee\b|\brestaurant\b|ร้านอาหาร|ร้านกาแฟ"),
]


def load():
    recs = []
    for f in ("cm.json", "cr.json"):
        recs += json.loads((CANON / f).read_text())
    return recs


def name_of(r):
    return " ".join(str(x) for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)


def lens_of(r):
    return (r.get("attrs") or {}).get("lens") or []


def read_name(rules, r):
    """Keys the record's own name declares. Empty is a fine answer."""
    n = name_of(r).lower()
    return [k for k, pat in rules if re.search(pat, n, re.I)]


def museum_tags():
    """museum=<v> from the CACHED Overpass responses. Local files, no network.

    These tags reach cache/overpass/ and are then dropped by import_overpass.py,
    which maps tourism=museum -> ('museums-galleries', 'museum') and keeps no
    subtag. Reading them back here recovers a fact OSM already published and
    this directory already downloaded.
    """
    out = {}
    for path in glob.glob(str(OVERPASS / "*" / "*.json")):
        prov = Path(path).parent.name
        try:
            data = json.loads(Path(path).read_text())
        except (ValueError, OSError):
            continue
        for el in data.get("elements", []):
            t = el.get("tags") or {}
            if t.get("museum"):
                out[f"{prov}-osm-{el.get('type')}-{el.get('id')}"] = t["museum"]
    return out


def band(title, note=""):
    print()
    print(title)
    print("-" * len(title))
    if note:
        print(note)


def report_library(recs):
    lib = [r for r in recs if "library" in lens_of(r)]
    band(f"LIBRARY — {len(lib)} records",
         "amenity=library is in no query group. Every record here arrived from the\n"
         "mueang-map lens import; none was crawled as a library.")
    print(f"  province:  cm {sum(1 for r in lib if r['province'] == 'cm')}"
          f"   cr {sum(1 for r in lib if r['province'] == 'cr')}")
    for f in ("hours", "phone", "website"):
        print(f"  has {f:8} {sum(1 for r in lib if r.get(f)):3}/{len(lib)}")
    print()
    tally = Counter()
    silent = []
    for r in lib:
        hits = read_name(LIBRARY_RULES, r)
        tally.update(hits)
        if not hits:
            silent.append(r)
        else:
            print(f"  {'+'.join(hits):20} {name_of(r)[:56]}")
    print()
    for k, _ in LIBRARY_RULES:
        print(f"  {k:20} {tally.get(k, 0)}")
    print(f"  {'(name says nothing)':20} {len(silent)}")
    for r in silent:
        print(f"      ? {name_of(r)[:60]}")
    return lib


def report_museum(recs, tags):
    mg = [r for r in recs if "museums-galleries" in (r.get("cat") or [])]
    band(f"MUSEUM & GALLERY — {len(mg)} records",
         "Two subs today: museum, gallery. OSM's own museum=* subtag is recovered\n"
         "from cache/overpass/ below — it is downloaded already and dropped at import.")
    print(f"  province:  cm {sum(1 for r in mg if r['province'] == 'cm')}"
          f"   cr {sum(1 for r in mg if r['province'] == 'cr')}")
    for f in ("hours", "phone", "website"):
        print(f"  has {f:8} {sum(1 for r in mg if r.get(f)):3}/{len(mg)}")
    print()
    tally = Counter()
    silent = 0
    for r in mg:
        hits = read_name(MUSEUM_RULES, r)
        tag = tags.get(r["id"])
        if tag and MUSEUM_TAG.get(tag) and MUSEUM_TAG[tag] not in hits:
            hits = hits + [MUSEUM_TAG[tag] + f" (tag museum={tag})"]
        tally.update(h.split(" (")[0] for h in hits)
        if hits:
            print(f"  {'+'.join(hits)[:40]:42} {name_of(r)[:48]}")
        else:
            silent += 1
    print()
    for k, _ in MUSEUM_RULES:
        print(f"  {k:20} {tally.get(k, 0)}")
    for k in ("museum-subject", "museum-art"):
        print(f"  {k:20} {tally.get(k, 0)}   (from OSM museum=* only)")
    print(f"  {'(says nothing)':20} {silent}")
    print()
    print("  NOT readable from any name or tag: whether a gallery SELLS the work on")
    print("  its walls. gallery-commercial vs gallery-artistrun is a door question,")
    print("  and both shelves should expect to start on the KNOWN_EMPTY list.")
    return mg


def report_craft(recs):
    cr_ = [r for r in recs if "crafts" in (r.get("sub") or [])]
    band(f"CRAFT — {len(cr_)} records on shopping/crafts",
         "Gathered by craft=* + shop=gift + shop=second_hand. The craft itself is\n"
         "not recorded anywhere; these are the ones whose own name names it.")
    tally = Counter()
    hitrows = []
    for r in cr_:
        hits = read_name(CRAFT_RULES, r)
        tally.update(hits)
        if hits:
            hitrows.append((r, hits))
    for r, hits in hitrows:
        print(f"  {'+'.join(hits)[:30]:32} {name_of(r)[:46]}")
    print()
    for k, _ in CRAFT_RULES:
        n = tally.get(k, 0)
        flag = "   <- ZERO on a craft this city is known for" if n == 0 else ""
        print(f"  {k:16} {n}{flag}")
    print(f"\n  named a craft: {len(hitrows)}/{len(cr_)}   silent: {len(cr_) - len(hitrows)}")
    return cr_


def report_books(recs):
    band("BOOKS — 0 records exist; scanning the WHOLE corpus",
         "shop=books and shop=stationery are in no query group, so the only bookshops\n"
         "that can be in this data are ones crawled under some other tag. Same shape as\n"
         "the coworking sweep that found Hub 53 filed as a guesthouse.")
    found = []
    for r in recs:
        hits = read_name(BOOK_RULES, r)
        if hits:
            found.append((r, hits))
    for r, hits in found:
        print(f"  {'+'.join(hits)[:26]:28} {name_of(r)[:40]:42} "
              f"now: {'/'.join(r.get('cat') or [])}/{'/'.join(r.get('sub') or [])}")
    print(f"\n  {len(found)} candidate(s) already in the corpus under another tag.")
    print("  Everything else waits on the crawl — one Overpass call, Nan's go.")
    return found


def report_strays(recs):
    cr_ = [r for r in recs if "crafts" in (r.get("sub") or [])]
    band(f"STRAYS — craft-shelf records whose own name says otherwise",
         "Proposed for a look. Nothing is moved: shelves.json is additive and does\n"
         "not argue with the crawl, so relocating any of these is a curated decision.")
    n = 0
    for r in cr_:
        hits = read_name(STRAY_RULES, r)
        if hits and not read_name(CRAFT_RULES, r):
            n += 1
            print(f"  {'+'.join(hits)[:24]:26} {name_of(r)[:52]}  [{r['id']}]")
    print(f"\n  {n} of {len(cr_)} on the craft shelf name something else entirely.")


def sub_to_cat():
    """{sub -> cat} read off data/categories.json, never hardcoded here.

    WO-10 added two cats, `read` and `crafts`, and a record only reaches them by
    gaining a SECOND cat — the additive move the coworking sweep used to put Hub
    53 on the business shelf without taking it off the hotel one. Which cat a
    proposed sub belongs to is a fact the tree already states, so it is read
    from the tree: hardcoding it here is how the two drift apart.
    """
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    out = {}
    for c in cats["categories"]:
        for ch in c.get("children", []):
            sub = (ch.get("match") or {}).get("sub")
            if sub:
                out.setdefault(sub, c["key"])
    return out


def emit(recs, tags):
    """shelves.json-ready entries. Names and tags only — never access, never price."""
    already = set(json.loads(SHELVES.read_text())["shelves"])
    owner = sub_to_cat()
    out = {}

    def add(r, subs, why, src):
        if r["id"] in already or not subs:
            return
        e = out.setdefault(r["id"], {"note": f"{r.get('name')} — {why}",
                                     "add_cat": [], "add_sub": [], "source": src,
                                     # the record's own date: this attests when
                                     # that name was last seen, which is the
                                     # thing being cited.
                                     "fetched": r.get("updatedAt", "")})
        e["add_sub"] = sorted(set(e["add_sub"]) | set(subs))
        # only cats the record does not already hold; add_cat never restates
        # what the crawl already filed, and never removes it.
        want = {owner[s] for s in subs if s in owner} - set(r.get("cat") or [])
        e["add_cat"] = sorted(set(e["add_cat"]) | want)

    for r in recs:
        if "library" in lens_of(r):
            add(r, read_name(LIBRARY_RULES, r), "library kind read off its own name",
                f"osm name: {name_of(r)}")
        if "museums-galleries" in (r.get("cat") or []):
            hits = read_name(MUSEUM_RULES, r)
            add(r, hits, "museum kind read off its own name", f"osm name: {name_of(r)}")
            tag = tags.get(r["id"])
            if tag and MUSEUM_TAG.get(tag):
                add(r, [MUSEUM_TAG[tag]], f"OSM tags it museum={tag}",
                    f"osm tag: museum={tag}")
        if "crafts" in (r.get("sub") or []):
            add(r, read_name(CRAFT_RULES, r), "craft read off its own name",
                f"osm name: {name_of(r)}")
        bk = read_name(BOOK_RULES, r)
        if bk:
            add(r, bk, "name says books; crawled under another tag",
                f"osm name: {name_of(r)}")

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    ap.add_argument("--only", choices=("library", "museum", "craft", "books", "strays"),
                    help="run one report")
    args = ap.parse_args()

    recs = load()
    tags = museum_tags()

    if args.emit:
        emit(recs, tags)
        return

    print(f"culture audit — {len(recs)} records in cm + cr")
    print(f"museum=* subtags recovered from cache/overpass/: {len(tags)}")
    run = args.only
    if run in (None, "library"):
        report_library(recs)
    if run in (None, "museum"):
        report_museum(recs, tags)
    if run in (None, "craft"):
        report_craft(recs)
    if run in (None, "books"):
        report_books(recs)
    if run in (None, "strays"):
        report_strays(recs)
    print()
    print("Nothing above has been written anywhere. --emit proposes; a human pastes.")


if __name__ == "__main__":
    main()
