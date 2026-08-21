#!/usr/bin/env python3
"""The facet vocabulary is written down in three places. Keep them one list.

data/facets.json is the schema. worker/worker.js validates against a hardcoded
copy, because a Cloudflare Worker cannot read the repo at request time. build.py
renders the ticks from the schema. If those drift, the failure is silent in the
worst possible way: a contributor stands in a shop, ticks "has a bakery", presses
save, gets a success message — and the worker quietly discards the key it does
not recognise. Nobody is told, and the fact is lost.

So this test is the thing that makes the duplication safe.

    python3 tests/test_facets.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def main():
    schema = json.loads((ROOT / "data" / "facets.json").read_text())
    sets = schema["sets"]
    print(f"facet schema: {len(sets)} set(s)")

    keys = set()
    for s in sets:
        for f in s["facets"]:
            check(f'{s["key"]}/{f["key"]} has both languages',
                  bool(f.get("th") and f.get("en")))
            check(f'{s["key"]}/{f["key"]} has an icon', bool(f.get("icon")))
            check(f'{s["key"]}/{f["key"]} has a question to ask a passer-by',
                  bool(f.get("ask_th") and f.get("ask_en")))
            keys.add(f["key"])

    # ---- worker vocabulary ------------------------------------------------
    js = (ROOT / "worker" / "worker.js").read_text()
    m = re.search(r"const FACET_KEYS = new Set\(\[(.*?)\]\)", js, re.S)
    check("worker declares FACET_KEYS", bool(m), "regex found no FACET_KEYS block")
    if m:
        wkeys = set(re.findall(r"'([a-z0-9]+)'", m.group(1)))
        missing = keys - wkeys
        extra = wkeys - keys
        check("worker accepts every schema facet", not missing,
              f"worker would silently drop: {sorted(missing)}")
        check("worker accepts nothing the schema lacks", not extra,
              f"worker accepts unknown keys: {sorted(extra)}")

    # ---- importer rules point at real facets ------------------------------
    imp = (ROOT / "importers" / "import_fixtures.py").read_text()
    for key in re.findall(r'\("([a-z0-9]+)", "[a-z_:]+", lambda', imp):
        check(f"importer rule '{key}' names a real facet", key in keys)

    # ---- a claim can never be opened by ticks alone -----------------------
    # Ticking a box must not lock a shop out of its own listing. This is the
    # one facet rule with a victim if it breaks, so it is asserted, not trusted.
    check("facets alone cannot create a claim",
          "FIELDS.some(([k]) => fields[k] !== undefined)" in js,
          "create-mode guard no longer requires a contact field")

    shelves()

    print()
    if failures:
        print(f"{len(failures)} failure(s): {failures}")
        return 1
    print("all facet checks passed")
    return 0


# Shelves that expect a sub nobody emits are invisible in the worst way: the
# shelf renders as a muted "the ants are still collecting" wireframe, which
# reads as "we have none of these" when in fact we had 35 tattoo studios, 56
# beauty salons and 40 vegetarian kitchens all along. Nothing errors, nothing
# logs, and the records sit in the data being findable only by search.
#
# So every {sub:} rule must either match records or be on this list, which is
# the set of shelves deliberately left waiting for data that does not exist in
# OSM yet. Adding a name here is a decision; forgetting one is a bug.
KNOWN_EMPTY = {
    # The schools shelf, added 2026-08-18 (WO-11). Nineteen of its twenty
    # children fill from the crawl and the two registers — including cooking,
    # dance and massage-school, which fill from names alone. Only this one is
    # empty, and for a reason that is not going to change by crawling harder:
    # OSM HAS NO TAG FOR A MONASTIC SCHOOL. โรงเรียนพระปริยัติธรรม is mapped
    # amenity=school like any other or not at all, and the register that names
    # them (ONAB `68_113`, Open Data Common, in data/sources.json) has not been
    # fetched yet. When it is, it joins through รหัสวัด to the temples these
    # schools sit inside, which is a thing no other directory of either
    # province can express — so this shelf is waiting on a known next step,
    # not on hope.
    # ("school", "monastic") lived here until 2026-08-21 with the reason above.
    # It is no longer true: the ONAB register (68_113, Open Data Common) WAS
    # fetched, and the shelf now holds 27 monastic schools — 13 of them pinned
    # at the temple the register says they stand in, which is the join that
    # comment predicted. A KNOWN_EMPTY reason that has stopped being true is
    # exactly the failure WO-22 paid for; it comes out the day it is fixed.

    # มวยไทย, added 2026-08-19 (WO-12). Stadium and camp are live off the
    # venues' own names and the curated stadiums; gear is not, and will not
    # be by crawling harder: no query group has ever asked for a boxing shop,
    # shop=sports rarely carries a sport=*, and the glove brands are sold from
    # Night Bazaar stalls with no OpenStreetMap record at all. It fills by
    # name and by walk — importers/audit_muaythai.py --only gear is the check.
    ("muaythai", "gear"),

    # เรียนทำอาหารไทย, added 2026-08-19 (WO-14). Eight of the nine children are
    # live off the schools' own names and their own sites (class, farm, home,
    # vegan, northern, dessert, carving, hotel). Vocational is not, and will
    # not be by crawling harder: the places that teach อาหาร for a trade — the
    # Polytechnic's short courses, the Skill Development Institute's
    # ผู้ประกอบอาหารไทย test, the vocational colleges' คหกรรม departments —
    # carry names that say "all trades" or "home economics", never "food", so
    # the name rule rightly refuses them, and on 2026-08-19 the Polytechnic's
    # site would not answer and the DSD page did not mention cooking. Each
    # enters the day its own page says it teaches อาหาร — audit_cooking.py
    # --only vocational is the list to work from.
    ("cooking", "vocational"),

    # ("beauty", "salon") was here from the first facet build, with the reason
    # "no OSM signal separates a salon from a hairdresser". That was true about
    # OpenStreetMap and false about the shops, and it kept a shelf empty for
    # months in front of readers who would have been served by it. เสริมสวย is
    # THE Thai word for a women's salon and it was sitting in sixty-two names
    # the whole time — เสริมสวยดาว, เสริมสวยอิงอร, ณัฏฐ์บิวตี้ซาลอน, มะซาลอน.
    # The signal was never in the tag; it was on the sign, in Thai. Removed
    # 2026-08-20 (WO-22), which is also when the barber shelf went from 6 to
    # 62 for exactly the same reason. importers/audit_beauty.py is the check,
    # and the lesson is written down in the note beside it: before a shelf is
    # declared unfillable, READ THE NAMES — in the language the shop wrote them.
    ("tattoo", "piercing"),   # shop=piercing is queried; none are mapped here yet
    ("tattoo", "removal"),    # needs curated field truth; OSM has no tag for it

    # The massage modalities, added 2026-08-17. Sixteen shelves went up; five
    # are live off the shops' own names (thai-traditional 52, blind-massage 2,
    # foot 2, oil 1, spa-body 1) and these eleven are waiting on the door
    # survey. They are on this list rather than off the tree because the words
    # are on shopfronts all over this city — the gap is that OSM records a
    # massage shop as shop=massage and stops, so no crawl can tell one from
    # another, and 237 of 294 names decline to say. A wireframe shelf reading
    # "the ants are still collecting" is the true statement here.
    ("massage", "prakhop"),          # herbal compress: an add-on, rarely in a name
    ("massage", "chap-sen"),         # deep sen work: named on the door menu, not the sign
    ("massage", "tok-sen"),          # Lanna, and genuinely offered here — nobody names it
    ("massage", "yam-khang"),        # Lanna, rare enough that finding one is the survey
    ("massage", "ratchasamnak"),     # court lineage: a training claim, asked not read
    ("massage", "office-syndrome"),  # heavily advertised, but on menus and in shop windows
    ("massage", "face"),             # facials sit inside beauty listings more often than massage
    ("massage", "cupping"),          # an add-on; the glass jars are visible, the name is not
    ("massage", "postpartum"),       # specialists exist; they advertise by phone and word of mouth
    ("massage", "prenatal"),         # a capability to ask about, never a shop name
    ("massage", "ap-ob-nuat"),       # populated ONLY from a venue's own name — see
                                     # importers/audit_massage.py. Nothing else is evidence,
                                     # so an empty shelf here is correct, not incomplete.

    # กัญชา-กระท่อม, added 2026-08-17. Three of the five children are live off
    # the crawl (dispensary, cannabis-cafe, kratom); these two are on the tree
    # because both are real trades here and neither leaves a trace a crawl can
    # read.
    ("cannabis", "clinic"),   # a คลินิกกัญชา carries amenity=clinic and nothing
                              # that says cannabis, so it is indistinguishable
                              # from every other clinic in the province. The
                              # sign on the door says it; no tag does.
    ("cannabis", "farm"),     # licensed plots exist in both provinces and OSM
                              # maps them, where it maps them at all, as
                              # landuse=farmland with no crop. A rule that
                              # guessed from that would file somebody's longan
                              # orchard as a grow.
}


def shelves():
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    subs = set()
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if not f.exists():
            continue
        for r in json.loads(f.read_text()):
            for cat in r.get("cat") or []:
                for s in r.get("sub") or []:
                    subs.add((cat, s))

    print("\nshelf rules")
    for c in cats["categories"]:
        for ch in c.get("children", []):
            m = ch.get("match") or {}
            if "sub" not in m:
                continue
            key = (c["key"], ch["key"])
            live = (c["key"], m["sub"]) in subs
            if live or key in KNOWN_EMPTY:
                continue
            near = sorted(s for (cat, s) in subs if cat == c["key"])
            check(f'{c["key"]}/{ch["key"]} finds records', False,
                  f"match sub={m['sub']!r} matches nothing; "
                  f"subs present here: {near}")

    # The mirror: records that reach no shelf at all are equally invisible,
    # just from the other direction. Asked per RECORD, not per (cat, sub) pair
    # — a place carrying cat ['sights','tattoo'] is on a shelf as soon as
    # either category claims its sub, and complaining about the other one would
    # be a false alarm every time.
    # A CHILD CLAIMS A RECORD THREE WAYS, NOT ONE. categories.json says so in
    # its own header — "{attr,value} on attrs, {lens} on attrs.lens, or {sub}
    # on record.sub" — and build.py honours all three. This check used to read
    # only `sub`, which was harmless while every attr-matched shelf happened to
    # hold records that carried no sub at all. The medical shelf broke that: its
    # children match on attrs.facilityType, its records now carry subs too, and
    # 469 รพ.สต. sitting on a perfectly good shelf were reported homeless.
    # Testing the proxy instead of the thing is how a green suite hides a real
    # gap and invents a fake one.
    claimed = {(c["key"], (ch.get("match") or {}).get("sub"))
               for c in cats["categories"] for ch in c.get("children", [])}
    claimed_attr = [(c["key"], m.get("attr"), m.get("value"))
                    for c in cats["categories"] for ch in c.get("children", [])
                    for m in [ch.get("match") or {}] if m.get("attr")]
    claimed_lens = {(c["key"], (ch.get("match") or {}).get("lens"))
                    for c in cats["categories"] for ch in c.get("children", [])}
    homeless = {}
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if not f.exists():
            continue
        for r in json.loads(f.read_text()):
            subs_ = r.get("sub") or []
            cats_ = r.get("cat") or []
            if not subs_ or not cats_:
                continue            # no sub at all: it lives on the parent shelf
            if any((c, s) in claimed for c in cats_ for s in subs_):
                continue
            attrs_ = r.get("attrs") or {}
            if any(c in cats_ and attrs_.get(k) == v
                   for c, k, v in claimed_attr):
                continue
            if any((c, l) in claimed_lens
                   for c in cats_ for l in (attrs_.get("lens") or [])):
                continue
            for c in cats_:
                for s in subs_:
                    homeless[(c, s)] = homeless.get((c, s), 0) + 1
    for (cat, s), n in sorted(homeless.items()):
        if n >= 25:
            check(f"{cat}/{s} ({n} records) reaches a shelf", False,
                  "no child of any of these records' categories claims this sub")


if __name__ == "__main__":
    sys.exit(main())
