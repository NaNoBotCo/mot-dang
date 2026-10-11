"""A place page's footer prints its record's own last-changed date (2026-09-11).

Nan chose "(b), the record's own last-changed date". The build's date had
already left every footer (it changed every page every day); this puts a date
back on place pages only, and it is the record's, so an unchanged place's page
is byte-for-byte the same on any build day. Other pages print no date.

    python3 tests/test_record_date.py
"""
import ast
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build          # noqa: E402  (runs the site's top level: loads data, writes nothing)
import refine_layer   # noqa: E402


class RecordDate(unittest.TestCase):
    def setUp(self):
        self._claims = build.CLAIMS
        build.CLAIMS = {}

    def tearDown(self):
        build.CLAIMS = self._claims

    def test_updated_at(self):
        self.assertEqual(build.record_date({"id": "a", "updatedAt": "2026-07-27"}), "2026-07-27")

    def test_a_timestamp_is_cut_to_its_day(self):
        self.assertEqual(build.record_date({"id": "a", "updatedAt": "2026-09-07T10:00:00Z"}),
                         "2026-09-07")

    def test_a_later_owner_confirmation_wins(self):
        build.CLAIMS = {"a": {"confirmedAt": "2026-09-09T08:00:00Z"}}
        self.assertEqual(build.record_date({"id": "a", "updatedAt": "2026-07-27"}), "2026-09-09")

    def test_an_earlier_confirmation_does_not(self):
        build.CLAIMS = {"a": {"confirmedAt": "2026-06-01"}}
        self.assertEqual(build.record_date({"id": "a", "updatedAt": "2026-07-27"}), "2026-07-27")

    def test_nothing_usable_is_empty(self):
        for bad in (None, "", "soon", "27/07/2026"):
            self.assertEqual(build.record_date({"id": "a", "updatedAt": bad}), "")


class Footer(unittest.TestCase):
    def test_a_place_page_prints_its_record_date(self):
        html = build.page("t", "<p>x</p>", 2, path="cm/p/x.html", updated="2026-07-27")
        self.assertIn("ปรับปรุง 2026-07-27 (พ.ศ. 2569)", html)
        self.assertIn("updated 2026-07-27 (B.E. 2569)", html)

    def test_the_buddhist_year_follows_the_record(self):
        html = build.page("t", "", 2, path="cm/p/x.html", updated="2024-01-01")
        self.assertIn("(พ.ศ. 2567)", html)

    def test_a_page_about_no_record_prints_no_date(self):
        for html in (build.page("t", "", 1, path="cm/index.html"),
                     build.page("t", "", 2, path="cm/p/x.html", updated="")):
            self.assertNotIn("ปรับปรุง", html)
            self.assertNotIn(f"updated {build.BUILD_DATE}", html)

    def test_the_same_place_page_is_identical_on_two_build_days(self):
        saved = build.BUILD_DATE, build.BE_BUILD
        try:
            out = []
            for day, be in (("2026-09-11", 2569), ("2027-01-02", 2570)):
                build.BUILD_DATE, build.BE_BUILD = day, be
                out.append(build.page("t", "<p>x</p>", 2, path="cm/p/x.html",
                                      updated="2026-07-27"))
            self.assertEqual(out[0], out[1])
        finally:
            build.BUILD_DATE, build.BE_BUILD = saved

    def test_the_footer_alone(self):
        bi = build.bi
        with_date = refine_layer.bare_footer("../../", bi, build.emergency_foot, "x", 0, "", "",
                                             record_date="2026-09-07")
        without = refine_layer.bare_footer("../../", bi, build.emergency_foot, "x", 0, "", "")
        self.assertIn("updated 2026-09-07 (B.E. 2569)", with_date)
        self.assertNotIn("ปรับปรุง", without)


class Wiring(unittest.TestCase):
    def test_detail_page_passes_the_record_date(self):
        tree = ast.parse((ROOT / "build.py").read_text(encoding="utf-8"))
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "detail_page")
        calls = [c for c in ast.walk(fn) if isinstance(c, ast.Call)
                 and getattr(c.func, "id", None) == "page"]
        self.assertTrue(any(k.arg == "updated" for c in calls for k in c.keywords))


if __name__ == "__main__":
    unittest.main(verbosity=1)
