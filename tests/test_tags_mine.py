#!/usr/bin/env python3
"""🏷 The mined vocabulary and the discovery rails — WO-76, no build needed.

    python3 tests/test_tags_mine.py

tests/test_tags.py is the gate on the ARTEFACT and needs docs/ built. This one
is the gate on the ENGINE and runs against data/ alone, so it can be run while
another session holds the build.

What it guards:

1. **A mined tag is still derived.** Every mined def carries the field and the
   value it came from, and every record the tag claims really holds that value.
2. **The floor holds.** No mined tag below its family's `min`, and none that
   would draw a page in neither province.
3. **Slugs are claimed once.** A mined tag never shadows a hand-written or a
   brand tag, and no two mined tags collide.
4. **The `field` family describes the record, not the place.** A stub really is
   thin; a record with a phone is never a stub.
5. **The hours parser reads what the corpus holds**, and reads nothing out of
   a string it cannot parse — an unparsed string earns no tag, because a shop
   with no hours recorded is not a shop that is shut.
6. **The rails point somewhere.** Every co-occurrence pair is real and mutual,
   and the `state` family — which is about the entry — stays off them.
7. **COVERAGE DOES NOT REGRESS.** The whole point of the work order: before it,
   6.4% of records carried a tag. The floor here is set well under where it
   landed (100%) and well over where it started.
"""
import collections
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tags_layer          # noqa: E402
import tags_mine           # noqa: E402

MIN_COVERAGE = 0.80        # was 0.064 before WO-76; landed at 1.000


def _load():
    doc = json.loads((ROOT / "data" / "tags.json").read_text())
    lp = ROOT / "data" / "curated" / "tag_labels.json"
    labels = json.loads(lp.read_text()) if lp.exists() else {}
    recs = []
    for p in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{p}.json"
        if f.exists():
            recs += json.loads(f.read_text())
    return doc, labels, recs


class TestMine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc, cls.labels, cls.recs = _load()
        if not cls.recs:
            raise unittest.SkipTest("no data/canonical — nothing to mine")
        (cls.defs, cls.by_id, cls.gaps, cls.sources,
         cls.also) = tags_mine.mine_all(cls.recs, cls.doc, cls.labels)
        cls.by_slug = {d["slug"]: d for d in cls.defs}
        cls.rec_by_id = {r["id"]: r for r in cls.recs}

    def test_every_mined_tag_names_its_source_and_value(self):
        for d in self.defs:
            self.assertEqual(d["rule"]["kind"], "mined", d["slug"])
            self.assertTrue(d["rule"]["source"], d["slug"])
            self.assertTrue(d["rule"]["value"], d["slug"])
            self.assertTrue(d["th"] or d["en"], f"{d['slug']} has neither name")

    def test_every_assignment_is_in_the_record(self):
        """Spot-check every mined tag: the value is really on the record.

        A tag may now be earned by more than one field — sub `cafe` and
        overtureCategory `coffee_shop` are the same tag on purpose (2026-09-08,
        `map_existing`) — so the def carries every pair that earns it in
        `earned_by`, and a member has to carry ONE of them. What is not allowed is a
        member that carries none: that would be a tag nobody can trace.
        """
        for slug, d in self.by_slug.items():
            pairs = [(d["rule"]["source"], d["rule"]["value"])]
            pairs += [(a["source"], a["value"]) for a in (d.get("earned_by") or [])]
            holders = [pid for pid, ss in self.by_id.items() if slug in ss]
            self.assertTrue(holders, f"{slug} claims no record")
            for pid in holders[:5]:
                rec = self.rec_by_id[pid]
                self.assertTrue(
                    any(val in tags_mine._values(rec, src) for src, val in pairs),
                    f"{slug}: {pid} carries none of {pairs}")

    def test_floor_holds(self):
        floors = {m["key"]: int(m.get("min", 8)) for m in self.doc["mined"]}
        fam_min = {}
        for m in self.doc["mined"]:
            fam_min.setdefault(m["family"], []).append(floors[m["key"]])
        for d in self.defs:
            self.assertGreaterEqual(d["members"], min(fam_min[d["family"]]), d["slug"])

    def test_slugs_are_claimed_once(self):
        hand = {t["slug"] for t in self.doc["tags"]}
        seen = set()
        for d in self.defs:
            self.assertNotIn(d["slug"], hand, f"{d['slug']} shadows a hand-written tag")
            self.assertNotIn(d["slug"], seen, f"{d['slug']} minted twice")
            seen.add(d["slug"])

    def test_field_rules_describe_the_record(self):
        stub = next(t for t in self.doc["tags"] if t["slug"] == "stub")
        has_phone = next(t for t in self.doc["tags"] if t["slug"] == "has-phone")
        thin = {"id": "x", "name": "ร้านหนึ่ง", "lat": None, "attrs": {}}
        fat = {"id": "y", "name": "ร้านสอง", "phone": "053-000000", "website": "https://x",
               "hours": "Mo-Su 08:00-17:00", "lat": 18.79, "lng": 98.98,
               "address": "ถนนหนึ่ง", "attrs": {"facebook": "f", "email": "e", "desc": "d"}}
        self.assertTrue(tags_layer._match(stub["rule"], thin, {}, {}, {}))
        self.assertIsNone(tags_layer._match(stub["rule"], fat, fat["attrs"], {}, {}))
        self.assertIsNone(tags_layer._match(has_phone["rule"], thin, {}, {}, {}))
        self.assertTrue(tags_layer._match(has_phone["rule"], fat, fat["attrs"], {}, {}))

    def test_hours_parser(self):
        spans = tags_layer._hours_spans("Mo-Fr 06:00-11:00; Sa 18:00-02:00")
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[1][1], 18 * 60)
        self.assertEqual(spans[1][2], 26 * 60)            # past midnight, not before opening
        self.assertEqual(tags_layer._hours_spans("24/7")[0][2], 24 * 60)
        # a person's newline is a separator, and three-letter days are days
        self.assertEqual(len(tags_layer._hours_spans("Sat, Sun 08:00-10:00\nMon-Fri 08:00-23:00")), 2)
        for junk in ("", None, "by appointment", "ตามนัด", "☎"):
            self.assertEqual(tags_layer._hours_spans(junk), [], repr(junk))
        rule = {"kind": "hours", "closes_after": "21:00"}
        self.assertTrue(tags_layer._hours_match(rule, "Mo-Su 10:00-23:00"))
        self.assertIsNone(tags_layer._hours_match(rule, "Mo-Su 10:00-17:00"))
        self.assertIsNone(tags_layer._hours_match(rule, "by appointment"))

    def test_state_family_is_off_the_rails(self):
        fam = {f["key"]: f for f in self.doc["families"]}
        self.assertIs(fam["state"].get("rails"), False)

    def test_coverage_does_not_regress(self):
        n = len(self.recs)
        mined_hits = len(self.by_id)
        # the hand rules add the state family on top; mining alone must carry most of it
        self.assertGreater(mined_hits / n, 0.90,
                           f"mining reaches only {mined_hits / n:.1%} of {n:,} records")

    def test_the_whole_layer_tags_nearly_everything(self):
        """The end-to-end number, through build's own globals."""
        try:
            import build
        except Exception as e:                                  # pragma: no cover
            self.skipTest(f"build.py not importable: {e}")
        data = {p["key"]: json.loads(
            (ROOT / "data" / "canonical" / f'{p["key"]}.json').read_text())
            for p in build.PROVINCES}
        T = tags_layer.assign(build.__dict__, data)
        n = sum(len(v) for v in data.values())
        tagged = sum(1 for v in T["by_id"].values() if v)
        self.assertGreater(tagged / n, MIN_COVERAGE,
                           f"only {tagged:,}/{n:,} records tagged ({tagged / n:.1%})")
        # every defined tag reaches a page in at least one province
        floor = T["min_tag"]
        blind = [s for s in T["order"]
                 if max(T["counts"][p["key"]][s] for p in build.PROVINCES) < floor]
        self.assertEqual([s for s in blind if s != "ngv"], [],
                         "tags defined that would draw no page anywhere")
        # rails: every pair is mutual, real and never from a rails:false family
        no_rail = {f["key"] for f in T["doc"]["families"] if f.get("rails") is False}
        for prov, rows in T["pairs"].items():
            for a, pairs in list(rows.items())[:200]:
                self.assertNotIn(T["defs"][a]["family"], no_rail)
                for b, cnt in pairs:
                    self.assertIn(b, T["defs"], f"{a} pairs with unknown {b}")
                    self.assertNotIn(T["defs"][b]["family"], no_rail)
                    back = dict(rows.get(b) or [])
                    if a in back:
                        self.assertEqual(back[a], cnt, f"{prov}: {a}/{b} disagree")


class TestProlific(unittest.TestCase):
    """🏷 2026-09-08, Nan: "tag every record you can — make tags prolific. Some
    tags can/should be inferred."

    What that added, and what each of these keeps honest:

      * the sub-shelf and the name are fields too, so 99.5% of records now
        carry a tag ABOUT THE PLACE rather than 79.1%;
      * a value may JOIN a tag that already says the same thing, which is what
        keeps one axis one axis — and may never join one that means something
        else. The first cut mapped 7,516 restaurants onto a brand tag called
        "Restaurant" (six records had that word typed into their brand box);
      * a name may only say what the fields have already proved on that shelf,
        which is what stops นวดแผนไทย earning a cuisine.
    """

    @classmethod
    def setUpClass(cls):
        try:
            import build
        except Exception as e:                                  # pragma: no cover
            raise unittest.SkipTest(f"build.py not importable: {e}")
        cls.build = build
        cls.data = {p["key"]: json.loads(
            (ROOT / "data" / "canonical" / f'{p["key"]}.json').read_text())
            for p in build.PROVINCES}
        cls.T = tags_layer.assign(build.__dict__, cls.data)
        cls.recs = [r for v in cls.data.values() for r in v]

    def _fam(self):
        return {s: d.get("family", "?") for s, d in self.T["defs"].items()}

    def test_nearly_every_record_says_something_about_the_place(self):
        fam = self._fam()
        by = self.T["by_id"]
        real = sum(1 for r in self.recs
                   if any(fam.get(s) != "state" for s in (by.get(r["id"]) or [])))
        n = len(self.recs)
        self.assertGreater(real / n, 0.95,
                           f"only {real:,}/{n:,} ({real / n:.1%}) carry a tag about the "
                           f"place rather than about our entry for it")

    def test_a_record_carries_more_than_one_thing(self):
        fam = self._fam()
        by = self.T["by_id"]
        mean = sum(sum(1 for s in (by.get(r["id"]) or []) if fam.get(s) != "state")
                   for r in self.recs) / len(self.recs)
        self.assertGreater(mean, 2.0, f"mean of {mean:.2f} tags about the place")

    def test_a_value_never_joins_a_tag_from_another_family(self):
        # A CURATED merge is a person deciding two words are one tag, and it is
        # allowed to cross a family: Nan merged the cuisine-overture
        # `vegetarian_restaurant` into the diet tag `vegetarian` on 2026-09-08.
        # What is not allowed is the automatic map_existing doing it by itself.
        curated = set((self.T["doc"].get("merge", {}).get("into") or {}))
        for slug, d in self.T["defs"].items():
            if slug in curated:
                continue
            for a in (d.get("earned_by") or []):
                src = a["source"]
                # One field can feed several families — attrs.overtureCategory
                # feeds both `cuisine` and `kind` — so the question is whether a
                # route of the tag's OWN family exists on that field, not what
                # the first spec on it happens to be.
                routes = [m["family"] for m in self.T["doc"]["mined"]
                          if m["source"] == src]
                if routes:
                    self.assertIn(d.get("family"), routes,
                                  f"{slug} ({d.get('family')}) took {src} values, "
                                  f"which only feed {sorted(set(routes))}")

    def test_a_brand_is_never_a_kind_of_place(self):
        """A word that names a kind of place is not a chain."""
        skip = {str(x).strip().casefold() for x in (self.T["doc"].get("brand_skip") or [])}
        for slug, d in self.T["defs"].items():
            if d.get("family") != "brand":
                continue
            self.assertNotIn(slug, skip, f"brand tag {slug} names a kind of place")
            self.assertNotIn((d.get("en") or "").strip().casefold(), skip, slug)

    def test_a_name_only_says_what_the_shelf_already_proved(self):
        """Every name-earned tag stands on a shelf where a field-earned member
        of the same tag already stands."""
        by, via = self.T["by_id"], self.T["via"]
        shelves = collections.defaultdict(set)
        for r in self.recs:
            for s in (by.get(r["id"]) or []):
                if not str(via[r["id"]].get(s, "")).startswith("name:"):
                    for c in (r.get("cat") or []):
                        shelves[s].add(c)
        checked = 0
        for r in self.recs:
            for s in (by.get(r["id"]) or []):
                if str(via[r["id"]].get(s, "")).startswith("name:"):
                    checked += 1
                    self.assertTrue(set(r.get("cat") or []) & shelves[s],
                                    f"{s} was read off {r['id']}'s name on a shelf "
                                    f"where no field earned it")
        self.assertGreater(checked, 1000, "the name is earning almost nothing")

    def test_a_word_has_to_be_a_word(self):
        """Thai matches are at least three characters; Latin ones are whole
        words of at least four, so `bar` never lights up Barber."""
        spec = self.T["doc"].get("name_tags") or {}
        words = set()
        for slug, d in self.T["defs"].items():
            if d.get("family") in set(spec.get("families") or []):
                words |= tags_mine._words_for(d, spec.get("aliases") or {})
        self.assertTrue(words)
        for w in words:
            if tags_mine._THAI.search(w):
                self.assertGreaterEqual(len(w), 3, w)
            else:
                self.assertGreaterEqual(len(w), 4, w)

    def test_every_mined_tag_has_both_names(self):
        """A chip with nothing on it cannot be read, typed or remembered.
        2026-09-08: the 406 that had only an English word are labelled; a Thai
        value whose English half is an RTGS READING is the designed fallback
        and counts, because a reading is still something a reader can say."""
        naked = [d["slug"] for d in self.T["defs"].values()
                 if d.get("mined") and not (d.get("th") and d.get("en"))]
        self.assertEqual(naked, [], f"{len(naked)} mined tags have no label")

    def test_a_merge_keeps_every_member_traceable(self):
        """A merged tag carries the (field, value) pairs it swallowed, so a
        member of the coffee tag can still be shown the word it actually
        carries — cafe, coffee_shop, coffee or tea_room."""
        into = (self.T["doc"].get("merge", {}).get("into") or {})
        self.assertTrue(into, "nothing merged; the curated list is empty")
        for target, sources in into.items():
            if target not in self.T["defs"]:
                continue
            got = {(a["source"], a["value"])
                   for a in (self.T["defs"][target].get("earned_by") or [])}
            self.assertTrue(got, f"{target} merged {sources} and says nothing about it")
            for s in sources:
                self.assertNotIn(s, self.T["defs"],
                                 f"{s} was merged into {target} and is still its own tag")

    def test_provenance_says_which_word_it_read(self):
        via = self.T["via"]
        named = [(pid, s, h) for pid, d in via.items() for s, h in d.items()
                 if str(h).startswith("name:")]
        self.assertGreater(len(named), 1000)
        for pid, s, h in named[:400]:
            self.assertGreater(len(h.split(":", 1)[1]), 2, f"{s} on {pid}: {h}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
