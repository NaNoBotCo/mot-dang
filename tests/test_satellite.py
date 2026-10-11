#!/usr/bin/env python3
"""The satellite layer: what can silently break, asserted.

Three things this suite exists to catch, all of which have real precedent on
this site:

1. ABSENCE MUST BE A CLEAN OFF SWITCH, not a broken map. data/basemap.json
   with no satellite block, with an empty url, or missing entirely, has to
   leave every map exactly as it was — no control, no script tag, no source,
   no half-configured raster. This is the same contract map_shell keeps for
   the basemap and geography_layer keeps for the DEM, and it is the reason
   any of them could land before their archives existed.

2. THE LICENCE HAS TO BE WHERE THE IMAGERY IS. Sentinel-2 is CC-BY-SA 3.0
   IGO. The credit must name ESA / Copernicus and the licence in the config
   the page ships, in the control's own credit line, and in the text that
   gets drawn into a shared picture — because a picture travels with no page
   around it, which is why map_ground.credit_mark() exists at all.

3. THE ORDER. The raster goes ABOVE the paper fills and BELOW every line and
   every symbol, or the labels and roads are underneath a photograph and the
   map is unreadable. Checked against the REAL data/basemap_style.json, not
   against a copy of it, so a retuned style that adds a label layer fails
   here rather than in a reader's hands.

Plus the importer's offline contracts — the tile plan, the zoom-to-overview
rule, the UTM forward against a published coordinate, and a PMTiles archive
written by the writer and read back by map_ground's reader, byte for byte.

No network, no Pillow needed for the assertions that matter, fixtures only.
Run: python3 tests/test_satellite.py
"""
import importlib.util
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import map_shell                                            # noqa: E402
import sat_glyphs                                           # noqa: E402
import satellite_layer as sat                               # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bs = _load("build_satellite_t", ROOT / "importers" / "build_satellite.py")
map_ground = _load("map_ground_sat_t", ROOT / "map_ground.py")

STYLE = json.loads((ROOT / "data" / "basemap_style.json").read_text())
STYLE_IDS = [ly["id"] for ly in STYLE["layers"]]
STYLE_BY_ID = {ly["id"]: ly for ly in STYLE["layers"]}


def _bi(th, en):
    return th + " · " + en


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


class _Cfg:
    """Swap satellite_layer's view of data/basemap.json for the length of a
    test. Both modules are patched: satellite_layer reads the satellite block
    through map_shell.config(), and enabled() also asks map_shell.enabled()."""

    def __init__(self, cfg, basemap_live=True):
        self.cfg, self.live = cfg, basemap_live

    def __enter__(self):
        self._c, self._e = map_shell.config, map_shell.enabled
        map_shell.config = lambda: self.cfg
        map_shell.enabled = lambda: self.live
        return self

    def __exit__(self, *a):
        map_shell.config, map_shell.enabled = self._c, self._e


LIVE = {"url": "tiles/cm-cr.pmtiles", "maxzoom": 15,
        "satellite": {"url": "tiles/cm-cr-satellite.pmtiles",
                      "minzoom": 7, "maxzoom": 13}}


# ------------------------------------------------------------------ absence
class Absence(unittest.TestCase):
    def test_no_satellite_block_is_off(self):
        with _Cfg({"url": "tiles/cm-cr.pmtiles"}):
            self.assertFalse(sat.enabled())
            self.assertEqual(sat.head(0), "")
            self.assertEqual(sat.control("m", _bi, _esc, _bi), "")
            self.assertEqual(sat.sprite(), "")

    def test_empty_url_is_off(self):
        with _Cfg({"url": "tiles/cm-cr.pmtiles", "satellite": {"url": ""}}):
            self.assertFalse(sat.enabled())
            self.assertEqual(sat.control("m", _bi, _esc, _bi), "")

    def test_no_basemap_at_all_is_off(self):
        """An empty config is the documented state the site ships in."""
        with _Cfg({}):
            self.assertFalse(sat.enabled())
            self.assertEqual(sat.head(1), "")

    def test_satellite_without_a_live_basemap_is_off(self):
        """A raster layer with no map under it is not a layer of anything —
        and a page that loads MapLibre for it and then has no basemap is
        worse than the drawn SVG it replaced."""
        with _Cfg(LIVE, basemap_live=False):
            self.assertFalse(sat.enabled())

    def test_emit_is_a_silent_no_op_when_off(self):
        tmp = Path(tempfile.mkdtemp(prefix="sat-off-"))
        try:
            with _Cfg({"url": "tiles/cm-cr.pmtiles"}):
                r = sat.emit({"DOCS": tmp})
            self.assertEqual(r, {"enabled": False})
            self.assertEqual(sorted(p.name for p in tmp.iterdir()), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_js_returns_before_touching_anything_without_a_url(self):
        """The off switch has to be the FIRST thing the script does, not a
        branch inside a handler: a page with no archive should cost one
        property read, not a MapLibre call that throws."""
        body = sat.JS
        i_guard = body.index("if(!C.url")
        for call in ("addSource", "addLayer", "MDMAP.ready", "fetch("):
            self.assertLess(i_guard, body.index(call),
                            "%s runs before the empty-url guard" % call)


# -------------------------------------------------------------- attribution
class Attribution(unittest.TestCase):
    NAMES = ("Copernicus", "Sentinel", "ESA")

    def test_the_html_credit_names_esa_copernicus_and_the_licence(self):
        for n in self.NAMES:
            self.assertIn(n, sat.ATTRIBUTION_HTML)
        self.assertIn("CC BY-SA 3.0 IGO", sat.ATTRIBUTION_HTML)

    def test_the_picture_credit_names_them_too(self):
        """This is the string drawn into a shared picture's pixels, where
        there is no link to fall back on, so it must stand alone."""
        for n in self.NAMES:
            self.assertIn(n, sat.ATTRIBUTION_TEXT)
        self.assertIn("CC BY-SA 3.0 IGO", sat.ATTRIBUTION_TEXT)
        self.assertNotIn("<", sat.ATTRIBUTION_TEXT)

    def test_the_control_carries_the_credit_line(self):
        with _Cfg(LIVE):
            html = sat.control("xmap", _bi, _esc, _bi)
        self.assertIn("satcredit", html)
        self.assertIn("CC BY-SA 3.0 IGO", html)
        self.assertIn("Copernicus", html)

    def test_the_control_says_what_ten_metres_cannot_show(self):
        """A satellite button that does not say its resolution promises
        Google's picture and hands over ESA's."""
        with _Cfg(LIVE):
            html = sat.control("xmap", _bi, _esc, _bi)
        self.assertIn("10 metres", html)
        self.assertIn("๑๐ เมตร", html)
        for cannot in ("Not one roof at a time", "not a shop sign"):
            self.assertIn(cannot, html)

    def test_the_shipped_js_carries_the_credit_into_the_source(self):
        tmp = Path(tempfile.mkdtemp(prefix="sat-on-"))
        try:
            with _Cfg(LIVE):
                r = sat.emit({"DOCS": tmp})
            self.assertTrue(r["enabled"])
            js = (tmp / "satellite.js").read_text()
            cfg = json.loads(re.search(r"window\.MDSAT_CFG=(\{.*?\});\n", js,
                                       re.S).group(1))
            self.assertIn("Copernicus", cfg["attribution"])
            self.assertIn("CC BY-SA 3.0 IGO", cfg["attribution"])
            # onto the raster source, which is what MapLibre's own
            # non-compact attribution control reads
            self.assertIn("attribution:C.attribution", js)
            # and into the picture
            self.assertIn(json.dumps(sat.ATTRIBUTION_TEXT, ensure_ascii=False),
                          js)
            self.assertIn("%TEXT%", sat.JS)          # the placeholder is real
            self.assertNotIn("%TEXT%", js)           # and it was substituted
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_credit_rides_into_the_shared_picture(self):
        """The ODbL line is already drawn into the canvas by explore.js and
        here.js. The ESA one has to travel the same way — a picture is
        reposted with no page around it."""
        js = sat.JS
        self.assertIn("function stamp(canvas)", js)
        self.assertIn("getContext('2d')", js)
        self.assertIn("fillText", js)
        self.assertIn("window.MDSAT={stamp:stamp", js)
        # installed only while the imagery shows, and taken off again
        self.assertIn("wrapPicture()", js)
        self.assertIn("unwrapPicture()", js)
        self.assertIn("__mdsat", js)


# ------------------------------------------------------------------- order
class Order(unittest.TestCase):
    """Against the real style. A retuned basemap that adds a label layer or
    renames a road layer fails here, not in a reader's hands."""

    def _under_list(self):
        m = re.search(r"var UNDER=\[(.*?)\];", sat.JS, re.S)
        return re.findall(r"'([^']+)'", m.group(1))

    def _hide_list(self):
        m = re.search(r"var HIDE=\[(.*?)\];", sat.JS, re.S)
        return re.findall(r"'([^']+)'", m.group(1))

    def test_every_anchor_and_hidden_layer_exists_in_the_style(self):
        for lid in self._under_list() + self._hide_list():
            self.assertIn(lid, STYLE_IDS, "%s is not in basemap_style.json" % lid)

    def test_the_anchor_is_above_every_fill_the_paper_draws(self):
        """The raster is inserted BEFORE the first UNDER id present, so every
        layer earlier in the style — the cream ground and the landuse fills —
        ends up beneath the photograph."""
        anchor = next(l for l in self._under_list() if l in STYLE_IDS)
        i = STYLE_IDS.index(anchor)
        beneath = STYLE_IDS[:i]
        for lid in beneath:
            self.assertIn(STYLE_BY_ID[lid]["type"], ("background", "fill"),
                          "%s draws under the imagery but is not a fill" % lid)
        self.assertIn("earth", beneath)
        self.assertIn("landcover", beneath)

    def test_every_line_and_label_stays_on_top(self):
        anchor = next(l for l in self._under_list() if l in STYLE_IDS)
        i = STYLE_IDS.index(anchor)
        for lid in STYLE_IDS:
            ly = STYLE_BY_ID[lid]
            if ly["type"] in ("line", "symbol"):
                self.assertGreaterEqual(
                    STYLE_IDS.index(lid), i,
                    "%s (%s) would be drawn UNDER the imagery" % (lid, ly["type"]))

    def test_the_only_things_hidden_are_fills_that_would_cover_it(self):
        for lid in self._hide_list():
            ly = STYLE_BY_ID[lid]
            self.assertEqual(ly["type"], "fill",
                             "%s is hidden but is not a fill" % lid)
            anchor = next(l for l in self._under_list() if l in STYLE_IDS)
            self.assertGreater(STYLE_IDS.index(lid), STYLE_IDS.index(anchor),
                               "%s is already under the imagery; hiding it is "
                               "removing a layer for nothing" % lid)
        # water-line is NOT hidden: the moat and the Ping keep their outline.
        self.assertNotIn("water-line", self._hide_list())

    def test_no_label_or_road_layer_is_hidden(self):
        for lid in self._hide_list():
            self.assertNotIn("label", lid)
            self.assertNotIn("road", lid)

    def test_every_recoloured_layer_exists_and_is_restored(self):
        """INK changes live paint properties. Each target must exist, and the
        originals must be read off the map before anything is set — a restore
        from a guess is how a toggle leaves a map permanently retuned."""
        ink = re.findall(r"\['([^']+)','([^']+)',", sat.JS)
        self.assertTrue(ink)
        for lid, prop in ink:
            self.assertIn(lid, STYLE_IDS, "%s is recoloured but is not in the "
                                          "style" % lid)
        i_read = sat.JS.index("function readOriginals()")
        i_set = sat.JS.index("if(!saved)saved=readOriginals();")
        self.assertLess(i_read, i_set)
        self.assertIn("saved.paint.forEach", sat.JS)
        self.assertIn("saved.vis.forEach", sat.JS)

    def test_the_halos_actually_thicken(self):
        """The contrast fix has to be a real change, not a comment about
        one: the two symbol layers' halos must end up WIDER than the style's
        own values."""
        ink = dict(((a, b), c) for a, b, c in
                   re.findall(r"\['([^']+)','([^']+)',([^\]]+)\]", sat.JS))
        for lid in ("place-labels", "road-labels"):
            was = STYLE_BY_ID[lid]["paint"]["text-halo-width"]
            now = float(ink[(lid, "text-halo-width")])
            self.assertGreater(now, was, "%s halo did not thicken" % lid)

    def test_the_preflight_gates_everything_the_archive_feeds(self):
        """A declared archive that 404s must leave the control hidden and the
        drawn map standing — the 2026-08-27 failure, in this file's shape."""
        js = sat.JS
        self.assertLess(js.index("fetch(ABS,{headers:{Range:'bytes=0-127'}})"),
                        js.index("arm();"))
        self.assertIn("if(m!=='PMTiles')throw 0;", js)
        self.assertIn("bar.hidden=false;", js)
        self.assertLess(js.index("function arm()"), js.index("bar.hidden=false;"))


# ------------------------------------------------------------ cache-busting
class CacheBuster(unittest.TestCase):
    def test_head_carries_a_version_on_both_files(self):
        with _Cfg(LIVE):
            h = sat.head(0)
            v = sat.version()
        # no ?v= since 2026-09-10 (Nan): the Worker serves scripts and sheets with stale-while-revalidate instead
        self.assertTrue(v)
        self.assertIn('satellite.css"', h)
        self.assertIn('satellite.js"', h)
        self.assertNotIn("?v=", h)

    def test_depth_prefixes_the_paths(self):
        with _Cfg(LIVE):
            self.assertIn('href="../../satellite.css"', sat.head(2))

    def test_the_hash_moves_when_the_archive_url_does(self):
        """A changed tile url changes what the script DOES as surely as an
        edited line does — map_shell.version()'s reasoning, and the outage
        behind it was a map surface shipping without a ?v= at all."""
        with _Cfg(LIVE):
            a = sat.version()
        other = json.loads(json.dumps(LIVE))
        other["satellite"]["url"] = "tiles/other.pmtiles"
        with _Cfg(other):
            b = sat.version()
        self.assertNotEqual(a, b)

    def test_the_hash_is_eight_hex(self):
        with _Cfg(LIVE):
            self.assertRegex(sat.version(), r"^[0-9a-f]{8}$")


# ----------------------------------------------------------------- glyphs
class Glyphs(unittest.TestCase):
    def test_ids_do_not_collide_with_either_sprite(self):
        """A <use> resolves the first id it finds; a duplicate draws the
        wrong picture and never errors."""
        import glyphs
        build = (ROOT / "build.py").read_text()
        m = re.search(r'ICON_SPRITE = """(.*?)"""', build, re.S)
        build_ids = set(re.findall(r'<g id="([^"]+)"', m.group(1))) if m else set()
        self.assertTrue(build_ids, "could not read build.ICON_SPRITE")
        clash = set(sat_glyphs.IDS) & (set(glyphs.IDS) | build_ids)
        self.assertEqual(clash, set(), "already drawn elsewhere: %s" % sorted(clash))

    def test_no_glyph_carries_its_own_colour(self):
        for k in sat_glyphs.IDS:
            body = sat_glyphs.sprite([k])
            self.assertNotIn("fill=", body, "%s sets a fill" % k)
            self.assertNotIn("stroke=", body, "%s sets a stroke" % k)

    def test_every_mark_draws_inside_the_grid(self):
        for k in sat_glyphs.IDS:
            nums = [float(n) for n in
                    re.findall(r"-?\d+(?:\.\d+)?", sat_glyphs.sprite([k]))
                    if "id=" not in n]
            self.assertTrue(nums)
            self.assertGreaterEqual(min(nums), 0.0, k)
            self.assertLessEqual(max(nums), 24.0, k)

    def test_icon_is_hidden_without_a_label_and_named_with_one(self):
        self.assertIn("aria-hidden", sat_glyphs.icon("i-layers"))
        self.assertIn('aria-label="x"', sat_glyphs.icon("i-layers", label="x"))
        self.assertEqual(sat_glyphs.icon("i-nope"), "")

    def test_the_control_uses_drawn_marks_and_no_emoji(self):
        with _Cfg(LIVE):
            html = sat.control("m", _bi, _esc, _bi)
        self.assertIn("#i-layers", html)
        self.assertIn("#i-satellite", html)
        for ch in html:
            self.assertLess(ord(ch), 0x1F000, "emoji in the control: %r" % ch)


# --------------------------------------------------------------- importer
class Importer(unittest.TestCase):
    def test_the_fence_is_the_basemap_extract(self):
        self.assertEqual(bs.FENCE, (97.3, 17.0, 100.6, 20.5))

    def test_the_plan_counts_are_the_ones_in_the_note(self):
        self.assertEqual(len(bs.plan_tiles(13)), 8704)
        self.assertEqual(len(bs.plan_tiles(14)), 34223)
        x0, x1, y0, y1 = bs._tile_range(14, bs.FENCE)
        self.assertEqual((x1 - x0 + 1) * (y1 - y0 + 1), 25519)

    def test_utm_forward_against_a_published_coordinate(self):
        """ประตูท่าแพ, the coordinate every map on this site opens on:
        499272.9 E, 2077326.1 N in UTM zone 47N."""
        x, y = bs.utm_forward(18.7876, 98.9931, 47)
        self.assertAlmostEqual(x, 499272.9, delta=1.0)
        self.assertAlmostEqual(y, 2077326.1, delta=1.0)
        # the central meridian of zone 47 is 99°E: false easting, exactly
        x0, _ = bs.utm_forward(0.0, 99.0, 47)
        self.assertAlmostEqual(x0, 500000.0, delta=0.01)

    def test_the_overview_rule_never_reads_coarser_than_the_zoom_needs(self):
        # 5 levels is what a Sentinel-2 COG carries: 10, 20, 40, 80, 160 m.
        self.assertEqual(bs._level_for(14, 5), 0)       # 9.03 m/px
        self.assertEqual(bs._level_for(13, 5), 0)       # 18.07 -> level 0
        self.assertEqual(bs._level_for(12, 5), 1)       # 36.14 -> 20 m
        self.assertEqual(bs._level_for(7, 5), 4)        # clamped to the last
        for z in range(7, 15):
            self.assertLess(bs._level_for(z, 5), 5)

    def test_ranking_prefers_coverage_over_a_clean_swath_sliver(self):
        """The trap this catches is real and was measured on 2026-09-08:
        S2B_47QMA_20251202_0_L2A reports 0.000023% cloud and is 56.2%
        NOTHING. Ranked on cloud alone it wins and the mosaic gets a hole."""
        def feat(fid, cloud, nodata):
            return {"id": fid, "bbox": [98.0, 18.0, 99.1, 19.0],
                    "properties": {"grid:code": "MGRS-47QMA",
                                   "eo:cloud_cover": cloud,
                                   "s2:nodata_pixel_percentage": nodata,
                                   "datetime": "2025-12-02T04:13:05Z",
                                   "mgrs:utm_zone": 47},
                    "assets": {k: {"href": "x", "proj:transform": [10, 0, 0, 0, -10, 0],
                                   "proj:shape": [10980, 10980]}
                               for k in ("visual", "red", "green", "blue")},
                    "geometry": {}}
        plan = bs.rank([feat("sliver", 0.000023, 56.2),
                        feat("whole", 0.53, 11.5),
                        feat("whole-worse", 2.1, 11.6)])
        ids = [s["id"] for s in plan[0]["scenes"]]
        self.assertEqual(ids[0], "whole")
        self.assertNotIn("sliver", ids)

    def test_a_footprint_off_the_fence_is_dropped(self):
        f = {"id": "far", "bbox": [110.0, 10.0, 111.0, 11.0],
             "properties": {"grid:code": "MGRS-99XXX", "eo:cloud_cover": 0,
                            "s2:nodata_pixel_percentage": 0,
                            "datetime": "2025-12-02T00:00:00Z",
                            "mgrs:utm_zone": 47},
             "assets": {}, "geometry": {}}
        self.assertEqual(bs.rank([f]), [])

    def test_the_archive_round_trips_through_the_sites_own_reader(self):
        """The writer is correct because map_ground's reader — the only
        PMTiles reader on this machine, and the one map_ground uses in
        production — reads back every byte it wrote."""
        tmp = Path(tempfile.mkdtemp(prefix="sat-pmt-"))
        try:
            bs.TILE_CACHE = tmp / "tiles"
            tiles = [(7, 99, 57), (8, 199, 114), (12, 3175, 1830),
                     (13, 6350, 3661), (13, 6351, 3661)]
            for i, (z, x, y) in enumerate(tiles):
                p = bs._tile_path(z, x, y)
                p.parent.mkdir(parents=True, exist_ok=True)
                # A JPEG magic and some payload: the archive never decodes.
                p.write_bytes(b"\xff\xd8\xff\xe0" + bytes([i]) * (30 + i * 5))
            # one recorded absence, which must land as an ABSENT tile
            gap = bs._tile_path(13, 6352, 3661)
            gap.parent.mkdir(parents=True, exist_ok=True)
            gap.write_bytes(b"")

            out = tmp / "sat.pmtiles"
            r = bs.bind(tiles + [(13, 6352, 3661)], out, 13)
            self.assertEqual(r["tiles"], len(tiles))

            arc = map_ground._Archive(out)
            try:
                self.assertEqual(arc.tile_type, 3)          # jpeg
                self.assertEqual(arc.clustered, 1)
                self.assertEqual(arc.internal_compression, 2)
                self.assertEqual(arc.tile_compression, 1)   # jpeg carries its own
                self.assertEqual(arc.min_zoom, bs.MIN_Z)
                self.assertEqual(arc.max_zoom, 13)
                for z, x, y in tiles:
                    self.assertEqual(arc.tile(z, x, y),
                                     bs._tile_path(z, x, y).read_bytes(),
                                     "%d/%d/%d came back different" % (z, x, y))
                self.assertIsNone(arc.tile(13, 6352, 3661),
                                  "an empty tile must be ABSENT, not black")
                self.assertIsNone(arc.tile(13, 1, 1))
            finally:
                arc.close()

            head = out.open("rb").read(127)
            w, s, e, n = struct.unpack_from("<4i", head, 102)
            self.assertAlmostEqual(w / 1e7, bs.FENCE[0], places=4)
            self.assertAlmostEqual(s / 1e7, bs.FENCE[1], places=4)
            self.assertAlmostEqual(e / 1e7, bs.FENCE[2], places=4)
            self.assertAlmostEqual(n / 1e7, bs.FENCE[3], places=4)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_licence_rides_in_the_archives_own_metadata(self):
        """Share-alike travels with the adaptation. The mosaic IS one, so
        the file says so — a copy of this archive taken off the bucket still
        carries its licence."""
        tmp = Path(tempfile.mkdtemp(prefix="sat-meta-"))
        try:
            bs.TILE_CACHE = tmp / "tiles"
            p = bs._tile_path(13, 6350, 3661)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\xff\xd8\xff\xe0abc")
            out = tmp / "sat.pmtiles"
            bs.bind([(13, 6350, 3661)], out, 13)
            import gzip
            head = out.open("rb").read(127)
            mo, ml = struct.unpack_from("<2Q", head, 24)
            with out.open("rb") as fh:
                fh.seek(mo)
                md = json.loads(gzip.decompress(fh.read(ml)))
            self.assertEqual(md["license"], "CC BY-SA 3.0 IGO")
            self.assertIn("Copernicus", md["attribution"])
            self.assertIn("ESA", md["attribution"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_importer_names_what_is_missing_from_this_machine(self):
        """The docstring has to say what must be installed, because nothing
        in this pipeline can tell a reader that at runtime."""
        doc = bs.__doc__
        self.assertIn("brew install gdal", doc)
        self.assertIn("pip3 install rasterio", doc)
        for absent in ("rasterio", "numpy", "gdal"):
            self.assertIn(absent, doc)
        self.assertIn("CC-BY-SA 3.0 IGO", doc)


# ------------------------------------------------------------- it parses
class Parses(unittest.TestCase):
    def test_node_check(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not on this machine")
        tmp = Path(tempfile.mkdtemp(prefix="sat-js-"))
        try:
            with _Cfg(LIVE):
                sat.emit({"DOCS": tmp})
            f = tmp / "satellite.js"
            p = subprocess.run([node, "--check", str(f)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_emitted_css_has_no_absolute_machine_path(self):
        """`grep -rl "/Users/" docs/` must be empty before docs is committed."""
        self.assertNotIn("/Users/", sat.CSS)
        self.assertNotIn("/Users/", sat.JS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
