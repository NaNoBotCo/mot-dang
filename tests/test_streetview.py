#!/usr/bin/env python3
"""streetview_layer.py and importers/harvest_streetview.py. No network.

    python3 tests/test_streetview.py
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import streetview_layer as SV  # noqa: E402
import harvest_streetview as HV  # noqa: E402


def _g():
    return {"att": lambda s: s.replace('"', "&quot;"),
            "bi": lambda th, en: "<span>%s</span><span>%s</span>" % (th, en),
            "bi_text": lambda th, en: "%s · %s" % (th, en)}


def _cell(d, key, rows):
    (d / ("%s.json" % key)).write_text(json.dumps(
        {"by": ["u"], "seq": {"s1": [2025, 0]}, "img": rows}))


class Cells(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        SV._GRID.clear()
        _cell(self.d, SV.cell_of(18.7885, 98.9875),
              [["111", 18.7885, 98.9875, 90, "s1", 1, "2025-01-02"],
               ["112", 18.7886, 98.9875, 90, "s1", 2, "2025-01-02"]])

    def tearDown(self):
        self.tmp.cleanup()
        SV._GRID.clear()

    def test_the_harvester_and_the_layer_cut_the_same_cells(self):
        for la, ln in ((18.7885, 98.9875), (18.80001, 98.99999), (13.95, 100.6)):
            self.assertEqual(SV.cell_of(la, ln), HV.cell_of(la, ln))

    def test_nearest_within_reach(self):
        self.assertEqual(SV.nearest(18.7885, 98.98752, self.d)[0], "111")

    def test_nothing_near_is_none(self):
        self.assertIsNone(SV.nearest(18.7900, 98.9875, self.d))

    def test_a_neighbouring_cell_counts(self):
        # just across the cell line from the photos
        self.assertIsNotNone(SV.nearest(18.7885, 98.99001, self.d, near_m=400))


class Button(unittest.TestCase):
    def test_no_photo_no_button(self):
        SV._GRID.clear()
        self.assertEqual(SV.button_html({"lat": 0.5, "lng": 0.5}, _g()), "")
        self.assertEqual(SV.button_html({"lat": None, "lng": None}, _g()), "")

    def test_the_button_names_the_photo_and_loads_our_script(self):
        orig = SV.nearest
        SV.nearest = lambda la, ln: ["999", la, ln, 0, "s", 1, None]
        try:
            h = SV.button_html({"lat": 18.79, "lng": 98.99}, _g(), depth=2)
        finally:
            SV.nearest = orig
        self.assertIn('data-svid="999"', h)
        self.assertIn('data-sv="18.79,98.99"', h)
        self.assertIn('src="../../streetview.js?v=%s"' % SV.version(), h)
        self.assertIn('aria-label="', h)


class OwnOrigin(unittest.TestCase):
    """The browser loads photos and cells from this site; Mapillary appears
    only in links a reader chooses to follow."""

    def test_viewer_fetches_only_our_own_paths(self):
        for u in re.findall(r"fetch\((.*?)\)\.then", SV.JS):
            self.assertTrue(u.startswith("base()+'data/streetview/"), u)
        self.assertIn("var src=base()+'streetphotos/sv/'", SV.JS)
        for src in re.findall(r"\.src=([^;]+);", SV.JS):
            self.assertTrue("base()" in src or src == "src", src)
        self.assertNotIn("graph.mapillary", SV.JS)
        self.assertNotIn("thumb_", SV.JS)

    def test_mapillary_is_only_in_hrefs(self):
        for line in SV.JS.splitlines():
            if "mapillary.com" in line:
                self.assertIn("href=", line)

    def test_map_button_loads_a_versioned_viewer(self):
        self.assertIn("streetview.js?v=%s" % SV.version(), SV.map_js())
        self.assertNotIn("mapillary", SV.map_js().lower())


class Frames(unittest.TestCase):
    def test_every_frame_carries_year_credit_and_licence(self):
        js = SV.JS
        self.assertIn("+543", js)
        self.assertIn("the street may have changed since", js)
        self.assertIn("Date unknown", js)
        self.assertIn("CC BY-SA 4.0", js)
        self.assertIn("mapillary.com/app/user/", js)


class Emit(unittest.TestCase):
    def test_emit_copies_cells_and_named_photos(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            img, idx, docs = t / "sv", t / "idx", t / "docs"
            img.mkdir(), idx.mkdir(), docs.mkdir()
            (img / "111.jpg").write_bytes(b"x" * 2000)
            (img / "stray.jpg").write_bytes(b"x" * 2000)
            _cell(idx, "1878_9898", [["111", 18.78, 98.98, 0, "s1", 1, None],
                                     ["missing", 18.78, 98.98, 0, "s1", 2, None]])
            o_img, o_idx = SV.IMG_DIR, SV.IDX_DIR
            SV.IMG_DIR, SV.IDX_DIR = img, idx
            try:
                r = SV.emit({"DOCS": docs})
            finally:
                SV.IMG_DIR, SV.IDX_DIR = o_img, o_idx
            self.assertEqual(r, {"cells": 1, "photos": 1})
            self.assertTrue((docs / "streetview.js").exists())
            self.assertTrue((docs / "data" / "streetview" / "1878_9898.json").exists())
            self.assertTrue((docs / "streetphotos" / "sv" / "111.jpg").exists())
            self.assertFalse((docs / "streetphotos" / "sv" / "stray.jpg").exists())


class Harvest(unittest.TestCase):
    def test_self_test(self):
        self.assertTrue(HV.self_test(say=lambda *_: None))

    def test_photos_ride_the_streetphotos_route(self):
        self.assertEqual(HV.OUT_IMG, SV.IMG_DIR)
        self.assertEqual(HV.OUT_IDX, SV.IDX_DIR)

    def test_the_mac_mirror_leaves_them_on_the_server(self):
        t = (ROOT / "importers" / "server_link.sh").read_text()
        self.assertIn("--exclude /assets/streetphotos/sv/", t)
        self.assertIn("--exclude /data/streetview/", t)

    def test_the_doodle_map_names_the_viewer_for_stamping(self):
        t = (ROOT / "assets" / "sites" / "doodle-map" / "map.js").read_text()
        self.assertRegex(t, r"streetview\.js(\?v=[0-9a-f]+)?'")


if __name__ == "__main__":
    unittest.main()
