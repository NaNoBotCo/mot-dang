"""feedback_layer: the slot, the script tag and the minisite stamp."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import feedback_layer as fb  # noqa: E402


class Slot(unittest.TestCase):
    def test_slot_names_the_item(self):
        self.assertEqual(fb.slot("place:cm-osm-node-1"), '<div data-fb="place:cm-osm-node-1"></div>')

    def test_item_the_worker_would_refuse_gets_no_slot(self):
        for bad in ("", "a" * 121, "place:x y", 'place:"><script>', "place:x?y=1", None):
            self.assertEqual(fb.slot(bad), "", bad)

    def test_script_tag_follows_depth(self):
        self.assertEqual(fb.script_tag("../../"), '<script src="../../feedback.js" defer></script>')


class Stamp(unittest.TestCase):
    def test_stamp_once_per_site_and_skip_apps(self):
        with tempfile.TemporaryDirectory() as t:
            sites = Path(t) / "sites"
            for slug, body in (("a-site", "<html><body><p>x</p></body></html>"),
                               ("doodles", "<html><body></body></html>"),
                               ("no-body", "<p>fragment</p>")):
                (sites / slug).mkdir(parents=True)
                (sites / slug / "index.html").write_text(body)
            (sites / "empty").mkdir()
            self.assertEqual(fb.stamp_sites(t), ["a-site"])
            html = (sites / "a-site" / "index.html").read_text()
            self.assertEqual(html.count('data-fb="site:a-site"'), 1)
            self.assertTrue(html.index("data-fb") < html.index("</body>"))
            self.assertIn('src="/feedback.js"', html)
            self.assertEqual(fb.stamp_sites(t), [])
            self.assertEqual((sites / "a-site" / "index.html").read_text(), html)
            self.assertNotIn("data-fb", (sites / "doodles" / "index.html").read_text())


class Wiring(unittest.TestCase):
    """build.py puts the slot where the pages are written and copies the script."""

    def test_build_wiring(self):
        src = (ROOT / "build.py").read_text()
        self.assertIn('feedback_layer.slot("place:" + r["id"])', src)
        self.assertIn("feedback_layer.script_tag(r)", src)
        self.assertIn('assets" / "feedback.js", DOCS / "feedback.js"', src)
        self.assertIn("feedback_layer.stamp_sites(DOCS)", src)
        self.assertIn('fb=f"shelf:{key}/{c}/{child[\'key\']}"', src)


if __name__ == "__main__":
    unittest.main()
