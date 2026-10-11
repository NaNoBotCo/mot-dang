#!/usr/bin/env python3
"""A school shelf is a claim about who attends, not a word in a name.

    python3 tests/test_school_shelves.py     # reads data/canonical + cache/overpass

WHY THIS EXISTS. `school_sub()` used to test INTL_NAME first and above
everything, so any education record with "International" or "นานาชาติ" in its
name went to the international-schools shelf. The rule was invisible for as
long as the crawl only ASKED for schools with that word in the name — every
record it saw really was one. It stopped being invisible the moment the shelf
was read by a second instrument.

    WVS ITC Worldwide Veterinary Service International Training Center
    (OSM node/1799458066, office=educational_institution, Hang Dong)

is veterinary continuing education. The Listing Sheet computes "distance to
the nearest international school" from cat=school-intl, and for the Areeya
Garden Home property in Nam Phrae it answered 1,587 m — telling a family
looking for a school for their children that their nearest one is a vet
school. Nothing on the Mot Dang page looked wrong; the error only became
visible where the shelf was used as an answer.

Three more rode in on the same word: CMU's International College of Digital
Innovation (tertiary), ISDSI (a study-abroad institute), and a language
school literally named "International language school".

WHAT SETTLES IT. Every one of the genuine international schools in these two
provinces carries amenity=school or amenity=kindergarten — the tag says "a
school children attend", which is the entire claim this shelf makes. The word
is kept as the signal it always was and gated on that tag. Nothing else is
lost: นานาชาติ was never the failure mode, all four false positives were
English-named.

FOUR CHECKS
1. **The word alone never shelves anything.** The four records above, fed to
   school_sub() as their own OSM tags, come back as something other than
   international — by name, so a future rewrite has to answer for each one.
2. **Nobody on school-intl got there on a word.** Every OSM-derived record on
   the shelf in data/canonical carries a school-or-kindergarten tag in the
   crawl cache it came from. Register records (OPEC) are exempt and must be:
   they are shelved from the ทะเบียน's own ประเภท column, which is the
   authority, and most have no OSM element at all.
3. **A general name word never out-ranks a specific tag.** ศูนย์ฝึกขับขี่
   ปลอดภัย กรีนวิง is amenity=driving_school and stays a driving school; the
   general `training` rule at the bottom of SCHOOL_NAME_SUB reached for it
   the first time it was written. Same shape as the bug above, one shelf over.
4. **The shelf is not empty.** A gate that passes by deleting the shelf has
   not fixed anything, so the international schools are counted and a floor
   held. WVS ITC itself is still in the corpus — it is a real place — and is
   asserted present, on a shelf that is not school-intl.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import import_overpass as M                                    # noqa: E402

# The tags that say "a school children attend". Kept here rather than imported
# so a change to the importer's set has to be made twice, on purpose.
SCHOOL_TAGS = {"school", "kindergarten"}

# The four the gate exists for, each with the shelf it must NOT land on and
# the reason in its own words. Tags are the real OSM tags, so the case dies
# honestly if a mapper retags the element rather than passing on stale input.
NOT_INTERNATIONAL = [
    ("node/1799458066",
     "WVS ITC Worldwide Veterinary Service International Training Center",
     "veterinary CPD — the Listing Sheet reported it to Nam Phrae as the "
     "nearest international school, 1,587 m"),
    ("way/539200937", "International College of Digital Innovation",
     "CMU's tertiary international college"),
    ("node/6536292554",
     "International Sustainable Development Studies Institute (ISDSI)",
     "a study-abroad institute for university students"),
    ("node/4365805591", "International language school",
     "a language school, and the tag says so: training=language"),
]

# Check 3: a specific tag beats a general name word.
TAG_BEATS_WORD = [
    ("way/1125998553", "cr", "driving",
     "amenity=driving_school — 'Safety Driving Training Center' in its "
     "English name must not reach the general training rule"),
]


def load_cache():
    """Every crawled element in both provinces, by 'type/id'."""
    out = {}
    for prov in ("cm", "cr"):
        d = ROOT / "cache" / "overpass" / prov
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                els = json.loads(f.read_text()).get("elements", [])
            except (ValueError, OSError):
                continue
            for e in els:
                if e.get("tags"):
                    out.setdefault((prov, f"{e['type']}/{e['id']}"), e["tags"])
    return out


def main():
    cache = load_cache()
    bad, skipped = [], []

    # 1 — the word alone never shelves anything.
    for ref, name, why in NOT_INTERNATIONAL:
        tags = cache.get(("cm", ref))
        if tags is None:
            skipped.append(f"{ref} ({name}) is not in the crawl cache — "
                           f"re-run the schools crawl before trusting a pass")
            continue
        sub = M.school_sub(tags, tags.get("name") or "")
        if sub == "international":
            bad.append(f"{ref} {name!r} -> sub 'international'; it is {why}")

    # 2 — nobody on school-intl got there on a word.
    intl = osm_intl = 0
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / f"{prov}.json"
        if not p.exists():
            skipped.append(f"data/canonical/{prov}.json is absent")
            continue
        for r in json.loads(p.read_text()):
            if "school-intl" not in (r.get("cat") or []):
                continue
            intl += 1
            if "-osm-" not in r["id"]:
                continue                       # register-shelved; see docstring
            osm_intl += 1
            ref = r["id"].split("-osm-", 1)[1].replace("-", "/", 1)
            tags = cache.get((prov, ref))
            if tags is None:
                skipped.append(f"{r['id']} is on school-intl but not in the "
                               f"crawl cache — cannot check its tag")
                continue
            if tags.get("amenity") not in SCHOOL_TAGS:
                bad.append(
                    f"{r['id']} {r.get('name')!r} is on school-intl with "
                    f"amenity={tags.get('amenity')!r} office="
                    f"{tags.get('office')!r} — no tag says children attend it, "
                    f"so the word in its name is the only thing shelving it")

    # 3 — a specific tag beats a general name word.
    for ref, prov, want, why in TAG_BEATS_WORD:
        tags = cache.get((prov, ref))
        if tags is None:
            skipped.append(f"{ref} is not in the crawl cache")
            continue
        sub = M.school_sub(tags, tags.get("name") or "")
        if sub != want:
            bad.append(f"{ref} {tags.get('name')!r} -> sub {sub!r}, "
                       f"expected {want!r}: {why}")

    # 4 — the shelf is not empty, and the vet school is still a place.
    FLOOR = 20
    if intl < FLOOR:
        bad.append(f"school-intl holds {intl} records, below the floor of "
                   f"{FLOOR} — a gate that passes by emptying the shelf has "
                   f"fixed nothing")
    held = False
    p = ROOT / "data" / "canonical" / "cm.json"
    if p.exists():
        for r in json.loads(p.read_text()):
            if r["id"] == "cm-osm-node-1799458066":
                held = True
                if "school-intl" in (r.get("cat") or []):
                    bad.append("WVS ITC is still on school-intl in "
                               "data/canonical/cm.json — the rule was fixed "
                               "but the corpus was not rebuilt")
                break
        if not held:
            bad.append("WVS ITC (cm-osm-node-1799458066) is gone from the "
                       "corpus — it is a real veterinary training centre in "
                       "Hang Dong and was to be retagged, never deleted")

    print(f"crawled elements       {len(cache):,}")
    print(f"on school-intl         {intl} ({osm_intl} from the crawl, "
          f"{intl - osm_intl} from the private register)")
    print(f"regression cases       {len(NOT_INTERNATIONAL) + len(TAG_BEATS_WORD)}")
    for m in skipped:
        print("  ~", m)
    for m in bad:
        print("  !", m)
    print("PASS" if not bad else f"FAIL ({len(bad)})")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
