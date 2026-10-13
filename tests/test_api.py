"""🔌 The API's contract, held by a test rather than by good intentions.

An API is a promise about keys. The promise is worth exactly as much as the
thing that catches you breaking it, and there are four places here that state
the shape — api_layer.py's frozen lists, publish/api.js's copies of them, the
generated schema.json, and the generated openapi.json. Any two of them can
drift apart in an afternoon's editing and nothing would look wrong until
somebody's app went quiet.

So the lists are asserted against each other, and then against the artefacts
the build actually wrote. Adding a key is allowed and passes. Removing,
renaming or retyping one fails here, which is the point: that change is not
forbidden, it is just not a v1 change, and the test is where you find out.

Two more things are checked because they are the rules that make this data
worth taking, and a rule nobody tests is a rule that decays:

  * A row NEVER says "false" where it means "unknown". A place carrying a
    parsed schedule must also carry the hours string it was parsed from;
    a row with neither is simply absent from the schedule table.
  * A row never claims a photograph it does not have.

Run against docs/ if it is built. If it is not, the artefact half SKIPS and
says so — this is a gate on what shipped, and a green tick over an unbuilt
tree would be a lie.
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
sys.path.insert(0, str(ROOT))

import api_layer  # noqa: E402
import media_layer  # noqa: E402

V1 = DOCS / "api" / "v1"
BUILT = (V1 / "index.json").exists()


def _js_list(name):
    """Pull an exported const array out of publish/api.js.

    Read rather than imported: node is not a dependency of the Python suite,
    and the only thing needed here is the list of names, which a regex can get
    without pretending to be a JavaScript engine."""
    src = (ROOT / "publish" / "api.js").read_text()
    m = re.search(r"export const " + name + r"\s*=\s*\[(.*?)\];", src, re.S)
    if not m:
        raise AssertionError(f"publish/api.js has no exported {name}")
    return re.findall(r'"([^"]+)"', m.group(1))


class TheTwoCopiesAgree(unittest.TestCase):
    """api_layer.py bakes; api.js serves. They state the same shape twice
    because they run in different languages, so a test has to be the thing
    that keeps them one shape."""

    def test_result_keys(self):
        self.assertEqual(
            api_layer.RESULT_KEYS + api_layer.RESULT_KEYS_CONDITIONAL,
            _js_list("RESULT_KEYS"))

    def test_envelope_keys(self):
        self.assertEqual(api_layer.ENVELOPE_KEYS, _js_list("ENVELOPE_KEYS"))

    def test_schema_version(self):
        src = (ROOT / "publish" / "api.js").read_text()
        m = re.search(r"export const SCHEMA_VERSION\s*=\s*(\d+)", src)
        self.assertEqual(int(m.group(1)), api_layer.SCHEMA_VERSION)

    def test_limits_agree(self):
        src = (ROOT / "publish" / "api.js").read_text()
        got = {k: int(re.search(r"export const " + k + r"\s*=\s*(\d+)", src).group(1))
               for k in ("LIMIT_DEFAULT", "LIMIT_MAX", "RADIUS_DEFAULT", "RADIUS_MAX")}
        # The descriptor promises these numbers to every reader; the engine
        # enforces them. A descriptor that overstates the cap is a broken
        # promise even though nothing errors.
        self.assertEqual(got["LIMIT_DEFAULT"], 20)
        self.assertEqual(got["LIMIT_MAX"], 200)
        self.assertEqual(got["RADIUS_DEFAULT"], 2000)
        self.assertEqual(got["RADIUS_MAX"], 50000)


class TheGeneratedSpecSaysTheSameThing(unittest.TestCase):
    """schema.json and openapi.json are generated from the frozen lists, so
    this checks the generator, not a hand-written file — which is exactly why
    they are generated."""

    def setUp(self):
        self.schema = api_layer.schema("https://motdang.net/")
        self.spec = api_layer.openapi("https://motdang.net/")

    def test_schema_carries_the_frozen_lists(self):
        self.assertEqual(self.schema["result"]["always"], api_layer.RESULT_KEYS)
        self.assertEqual(self.schema["envelope"], api_layer.ENVELOPE_KEYS)
        self.assertEqual(self.schema["bulkIndexRow"]["keys"], api_layer.INDEX_ROW_KEYS)
        self.assertEqual(self.schema["vocabularies"]["has"], api_layer.HAS_VALUES)

    def test_every_conditional_key_is_explained(self):
        for k in api_layer.RESULT_KEYS_CONDITIONAL:
            self.assertIn(k, self.schema["result"]["conditional"],
                          f"{k} appears conditionally and nothing says when")

    def test_openapi_documents_every_endpoint_the_worker_routes(self):
        # The routes publish/worker.js actually answers, read off the source
        # rather than listed again here — a second list is a second thing to
        # forget to update.
        w = (ROOT / "publish" / "worker.js").read_text()
        routed = set(re.findall(r'path === "(/[a-z.]*)"', w))
        routed.discard("/health")          # documented below, checked separately
        for p in routed:
            self.assertIn(p if p != "/" else "/", self.spec["paths"],
                          f"worker answers {p} and openapi.json does not mention it")
        self.assertIn("/health", self.spec["paths"])
        self.assertIn("/places/{idOrSlug}", self.spec["paths"])

    def test_openapi_documents_every_query_param(self):
        params = {p["name"] for p in self.spec["paths"]["/places"]["get"]["parameters"]}
        # The engine's accepted params, read off api.js's parser.
        src = (ROOT / "publish" / "api.js").read_text()
        block = src[src.index("export function parseQuery"):src.index("export function echoQuery")]
        used = set(re.findall(r'sp\.get\("([a-z_]+)"\)', block))
        self.assertEqual(used - params, set(),
                         "api.js reads params openapi.json does not document")

    def test_terms_are_named_everywhere_a_reader_lands(self):
        for blob in (self.schema, self.spec["info"]["license"]):
            self.assertIn("terms.html", json.dumps(blob, ensure_ascii=False))


class AShutPlaceLightsNoLamp(unittest.TestCase):
    """A record data/curated/status.json marks closed or moved carries no
    `sched`, so openNow is null for it — never true from hours that no longer
    hold. Run on a stub corpus: no build needed."""

    def test_closed_and_moved_rows_carry_no_schedule(self):
        def rec(i, state=None):
            r = {"id": i, "province": "cm", "name": i, "cat": [], "hours": "Mo-Su 08:00-17:00"}
            if state:
                r["status"] = {"state": state, "since": "2026-09-01", "source": "test"}
            return r
        g = {"PROVINCES": [{"key": "cm", "th": "", "en": ""}], "CATS": {}, "CAT_ORDER": [],
             "BASE": "https://motdang.net/", "BUILD_DATE": "2026-09-11",
             "ant_bits": lambda r: {}, "facet_bits": lambda r: {},
             "name_pair": lambda r: (r["name"], ""), "place_slug": lambda r: r["id"],
             "name_of": lambda r: r["name"], "ant_rank": lambda r: 0}
        data = {"cm": [rec("a"), rec("b", "closed"), rec("c", "moved")]}
        real = api_layer._schedule_table
        api_layer._schedule_table = lambda g: ([[0, 1]], {"a": 0, "b": 0, "c": 0}, "")
        try:
            ix = api_layer.build_index(g, data, {}, {})
        finally:
            api_layer._schedule_table = real
        by = {r["id"]: r for r in ix["places"]}
        self.assertIn("sched", by["a"])
        self.assertNotIn("sched", by["b"], "a closed place still carries its schedule")
        self.assertNotIn("sched", by["c"], "a moved place still carries its schedule")
        self.assertEqual(ix["hours"]["withKnownHours"], 1)


@unittest.skipUnless(BUILT, f"SKIPPED — no {V1}/index.json; build.py has not run")
class TheBuiltIndex(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ix = json.loads((V1 / "index.json").read_text())
        cls.rows = cls.ix["places"]

    def test_row_keys_are_inside_the_frozen_set(self):
        allowed = set(api_layer.INDEX_ROW_KEYS)
        for r in self.rows:
            extra = set(r) - allowed
            self.assertEqual(extra, set(),
                             f"{r['id']} carries undeclared keys {extra}")

    def test_every_row_carries_the_keys_that_are_never_optional(self):
        required = ["id", "slug", "province", "name", "cat", "geoPrecision",
                    "antRank", "has", "osmDerived", "q"]
        for r in self.rows:
            for k in required:
                self.assertIn(k, r, f"{r.get('id')} is missing {k}")

    def test_ids_are_unique(self):
        # An id is the key /api/v1/places/{id} promises to resolve exactly.
        ids = [r["id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)), "two records share an id")

    def test_no_id_is_also_some_other_records_slug(self):
        # The lookup tries ids first, so an id that is also a different
        # record's page slug would shadow that page with the wrong record.
        by_slug = {}
        for r in self.rows:
            by_slug.setdefault(r["slug"], []).append(r["id"])
        clashes = [(r["id"], by_slug[r["id"]]) for r in self.rows
                   if r["id"] in by_slug and by_slug[r["id"]] != [r["id"]]]
        self.assertEqual(clashes, [], f"id/slug namespace collisions: {clashes[:3]}")

    def test_a_shared_slug_is_never_two_different_places(self):
        """place_slug() drops the Thai — it has to, because git on macOS
        re-normalizes non-ASCII filenames — so a Thai-only name slugs to its
        bare digits and two records can land on one stem. Today all 75 shared
        slugs are one shop entered in two curated registers, which is a
        duplicate-record problem and not a lost page. This is the test that
        tells you the day that stops being true: two DIFFERENT places on one
        slug means one of them has no page and the other is standing in for
        it, which is the failure place_slug's own docstring records losing
        339 pages to. The API refuses to guess between them either way — see
        slugCandidates() and the 300 in openapi.json."""
        by_slug = {}
        for r in self.rows:
            by_slug.setdefault(r["slug"], []).append(r)
        clobbered = {s: sorted({x["name"] for x in v})
                     for s, v in by_slug.items()
                     if len(v) > 1 and len({x["name"] for x in v}) > 1}
        self.assertEqual(clobbered, {},
                         f"a page slug is carrying two different places: "
                         f"{list(clobbered.items())[:3]}")

    def test_vocabularies_hold(self):
        has_ok = set(api_layer.HAS_VALUES)
        geo_ok = {"exact", "block", "approx", "needs-pin"}
        prov_ok = {p["key"] for p in self.ix["provinces"]}
        for r in self.rows:
            self.assertIn(r["province"], prov_ok)
            self.assertIn(r["geoPrecision"], geo_ok, f"{r['id']}: {r['geoPrecision']}")
            self.assertLessEqual(set(r["has"]), has_ok, f"{r['id']}: {r['has']}")
            self.assertTrue(0 <= r["antRank"] <= 9, f"{r['id']}: {r['antRank']}")

    def test_a_schedule_is_never_invented(self):
        """The rule the whole open-now feature rests on. A row may only point
        at a schedule if it carries the hours string that schedule was parsed
        from — otherwise the API would be answering "open" from a source the
        place page cannot show the reader."""
        n = len(self.ix["schedules"])
        withhours = 0
        for r in self.rows:
            if "sched" in r:
                withhours += 1
                self.assertIn("hours", r, f"{r['id']} has a schedule and no hours string")
                self.assertTrue(0 <= r["sched"] < n, f"{r['id']}: sched out of range")
        self.assertEqual(withhours, self.ix["hours"]["withKnownHours"])
        # And the count is real, not a rounding of the corpus.
        self.assertLess(withhours, len(self.rows),
                        "every place suddenly has hours — check the parser")

    def test_a_pin_is_never_invented(self):
        for r in self.rows:
            if r["geoPrecision"] == "needs-pin":
                self.assertNotIn("lat", r, f"{r['id']} needs a pin and has coordinates")
            if "lat" in r:
                self.assertIn("lng", r)
                self.assertTrue(5 < r["lat"] < 25 and 90 < r["lng"] < 110,
                                f"{r['id']} is not in northern Thailand: {r['lat']},{r['lng']}")

    def test_a_photograph_is_never_claimed(self):
        for r in self.rows:
            if "photo" in r:
                self.assertIn("photo", r["has"])
                self.assertTrue(media_layer.in_build(DOCS, "photos/" + r["photo"]),
                                f"{r['id']} points at a missing photo {r['photo']}")

    def test_the_haystack_is_never_empty(self):
        # ?q= tests against `q`; a row with an empty one is unfindable by text
        # no matter what a reader types, which is a silent hole.
        for r in self.rows:
            self.assertTrue(r["q"].strip(), f"{r['id']} has an empty match blob")

    def test_counts_are_the_real_ones(self):
        self.assertEqual(self.ix["count"], len(self.rows))
        self.assertEqual(sum(p["count"] for p in self.ix["provinces"]), len(self.rows))
        for c in self.ix["categories"]:
            self.assertEqual(c["count"],
                             sum(1 for r in self.rows if c["key"] in r["cat"]))

    def test_the_index_matches_what_the_pages_published(self):
        """One corpus, two renderings. A place in the API with no page means
        the API is offering something a reader cannot open."""
        for r in self.rows[::97]:              # every 97th, so the test stays quick
            self.assertTrue((DOCS / r["province"] / "p" / f"{r['slug']}.json").exists(),
                            f"{r['id']} is in the API and has no .json sibling")

    def test_nothing_is_filtered_out(self):
        """The decision of 2026-09-05: raw information, the caller runs their
        own filters. The first draft inherited the search index's exclusion of
        held() records — no pin, two facts or fewer — which made
        ?cat=realestate answer 147 condos against a shelf listing 348, and put
        a silent 1,711-row gap between this API and our own bulk dataset.

        An invisible filter is the one thing an API must not do: the caller
        cannot widen it and cannot tell it happened. So this asserts the API
        carries every record the corpus holds, and that the fields which let a
        caller re-apply that filter themselves are actually present."""
        import build
        canonical = sum(len(build.load()[p["key"]]) for p in build.PROVINCES)
        self.assertEqual(len(self.rows), canonical,
                         "the API is publishing a narrower set than the corpus holds")
        # And the two fields that make the narrowing a caller's own choice.
        thin = [r for r in self.rows if r["geoPrecision"] == "needs-pin"]
        self.assertTrue(thin, "no unpinned records — geoPrecision cannot be filtered on")
        self.assertTrue(any(r["antRank"] <= 2 for r in thin),
                        "nothing for ?min_ants= to exclude — check ant_rank")


@unittest.skipUnless(BUILT, f"SKIPPED — no {V1}/index.json; build.py has not run")
class TheBuiltPages(unittest.TestCase):

    def test_the_four_files_shipped(self):
        for f in ("api/v1/index.json", "api/v1/schema.json",
                  "api/v1/openapi.json", "api/index.html", "terms.html"):
            self.assertTrue((DOCS / f).exists(), f"{f} was not written")

    def test_the_terms_say_the_thing_they_exist_to_say(self):
        t = (DOCS / "terms.html").read_text()
        for phrase in ("CC BY 4.0", "ODbL", "motdang.net", "osmDerived"):
            self.assertIn(phrase, t, f"the terms page never mentions {phrase}")

    def test_the_api_page_links_the_terms_and_the_schema(self):
        p = (DOCS / "api" / "index.html").read_text()
        self.assertIn("terms.html", p)
        self.assertIn("schema.json", p)

    def test_llms_txt_tells_a_machine_the_api_exists(self):
        # The bot-facing file is the one an agent reads first. An API it does
        # not name is an API no agent will find.
        llms = (DOCS / "llms.txt").read_text()
        self.assertIn("api/v1/places", llms)
        self.assertIn("terms.html", llms)


if __name__ == "__main__":
    unittest.main(verbosity=2)
