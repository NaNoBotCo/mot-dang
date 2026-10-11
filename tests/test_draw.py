#!/usr/bin/env python3
"""tests/test_draw.py — the reader's own GIS (draw_layer.py, R1+R2).

What can silently break, asserted; what is a matter of taste, printed.

  · the emitted JS carries its own version — a map surface shipped without a
    cache-buster is the outage map_shell.version() has the scar from, and this
    file's `?v=` is on the same footing
  · every exported format ROUND-TRIPS: what fromText() reads back out of
    toGeoJSON / toGPX / toKML is the geometry that went in, to the metre —
    including the one documented loss, a polygon leaving as GPX and returning
    as a closed line, which is asserted as a loss so it cannot quietly become
    a different one
  · the licence line is inside all three files. ODbL requires the credit and a
    file travels with no page around it, so a missing line is a licence breach,
    not a cosmetic slip
  · no emoji anywhere a reader sees. This site draws its own marks; an emoji is
    whatever the reader's phone decides it is (tests/test_glyphs.py)
  · the hash REFUSES an oversized drawing rather than truncating it, through
    the same predicate the page uses
  · the five new glyphs collide with neither existing sprite and keep the
    24-grid stroke-only contract

The round-trip half runs the REAL draw.js under node, with a thirty-line DOM
stand-in. It is not a Python re-implementation of the exporters: two
implementations of one format is exactly the "one source of truth per channel"
scar in CLAUDE.md, and the second copy is the one that would rot. With no node
on the machine those cases skip and say so — the structural assertions still
run and still fail on a missing licence line.

Run: python3 tests/test_draw.py
 or: python3 -m unittest tests.test_draw -v
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import draw_layer  # noqa: E402
import glyphs  # noqa: E402
import glyphs_draw  # noqa: E402

NODE = shutil.which("node")
JS = draw_layer._js()

# ── the shapes every case uses: a pin, a walk, and a plot ───────────────────
# Real Chiang Mai coordinates, at the precision the encoder keeps (5 dp).
POINT = {"type": "Feature", "properties": {},
         "geometry": {"type": "Point", "coordinates": [98.99310, 18.78760]}}
LINE = {"type": "Feature", "properties": {},
        "geometry": {"type": "LineString", "coordinates": [
            [98.99310, 18.78760], [98.99420, 18.78810],
            [98.99530, 18.78700], [98.99610, 18.78650]]}}
POLY = {"type": "Feature", "properties": {},
        "geometry": {"type": "Polygon", "coordinates": [[
            [98.98900, 18.79000], [98.99100, 18.79000],
            [98.99100, 18.78840], [98.98900, 18.78840],
            [98.98900, 18.79000]]]}}
SHAPES = [POINT, LINE, POLY]


# ── the node harness ────────────────────────────────────────────────────────
# draw.js is an IIFE that gives up unless a bar, a map holder, MDMAP and the
# three libraries are all present. None of them exists in node, so this is the
# smallest set of stand-ins that lets it reach `window.MDDRAW = {...}` — and no
# more than that: MDMAP.ready() deliberately never fires its callback, so
# terra-draw is never touched and nothing below is testing a mock.
HARNESS = r"""
const fs=require('fs');
const src=fs.readFileSync(process.argv[2],'utf8');
const bar={getAttribute(){return 'xmap';},hidden:true,
  addEventListener(){},contains(){return false;},querySelectorAll(){return [];}};
global.window=global;
global.document={
  querySelector(sel){return sel.indexOf('.mdd')===0?bar:null;},
  getElementById(id){return id==='xmap'?{}:null;}
};
global.MDMAP={ready(){ /* never fires: no map here, and none needed */ }};
global.terraDraw={};global.terraDrawMaplibreGlAdapter={};
global.mdturf={length(){return 0;},area(){return 0;}};
(0,eval)(src);
const D=global.MDDRAW;
if(!D){console.log(JSON.stringify({error:'MDDRAW never exported'}));process.exit(0);}
const IN=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));

function geoms(list){return (list||[]).map(f=>f.geometry);}
const gj=D.toGeoJSON(IN), gpx=D.toGPX(IN), kml=D.toKML(IN);

// an oversized drawing: one long line, well past the cap
const big={type:'Feature',properties:{},geometry:{type:'LineString',coordinates:[]}};
for(let i=0;i<2000;i++)big.geometry.coordinates.push([98.99+i*0.0007,18.78+i*0.0005]);

console.log(JSON.stringify({
  files:{geojson:gj,gpx:gpx,kml:kml},
  back:{
    geojson:geoms(D.fromText(gj)),
    gpx:geoms(D.fromText(gpx)),
    kml:geoms(D.fromText(kml))
  },
  hash:{
    token:D.encode(IN),
    token_line_only:D.encode([IN[1]]),
    decoded:geoms(D.decode(D.encode(IN))),
    part_small:D.hashPart(IN),
    part_big:D.hashPart([big]),
    big_len:D.encode([big]).length,
    max:D.MAX
  },
  attrib:D.ATTRIB, odbl:D.ODBL,
  units:{
    rai:D.fmtArea(1600), quarter_rai:D.fmtArea(400),
    small:D.fmtArea(120), hectare:D.fmtArea(16000),
    metres:D.fmtLen(250), km:D.fmtLen(2500)
  },
  ring_pts:D.ring(98.99,18.79,500).geometry.coordinates[0].length,
  junk:D.fromText('this is not a map at all')
},null,0));
"""

_RUN = {}


def run_node():
    """Run draw.js under node once and cache the result for every case."""
    if "out" in _RUN:
        return _RUN["out"]
    d = Path(tempfile.mkdtemp(prefix="mddraw-"))
    try:
        (d / "draw.js").write_text(JS, encoding="utf-8")
        (d / "harness.cjs").write_text(HARNESS, encoding="utf-8")
        (d / "in.json").write_text(json.dumps(SHAPES), encoding="utf-8")
        p = subprocess.run(
            [NODE, str(d / "harness.cjs"), str(d / "draw.js"), str(d / "in.json")],
            capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise AssertionError("node harness failed:\n" + p.stderr[-2000:])
        _RUN["out"] = json.loads(p.stdout)
        return _RUN["out"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def near(a, b, tol=2e-5):
    """Precision 5 is about 1.1 m. Two coordinates that agree to 2e-5 degrees
    agree to about two metres, which is inside the encoding's own rounding and
    is the honest bar for a sketch tool."""
    return abs(a - b) <= tol


def coords_near(a, b, tol=2e-5):
    if isinstance(a, (int, float)):
        return isinstance(b, (int, float)) and near(a, b, tol)
    return len(a) == len(b) and all(coords_near(x, y, tol) for x, y in zip(a, b))


needs_node = unittest.skipUnless(NODE, "node not on this machine — round-trip skipped")


# ── the cache-buster ────────────────────────────────────────────────────────

class Version(unittest.TestCase):
    def test_head_carries_the_version_on_our_own_files(self):
        if not draw_layer.enabled():
            self.skipTest("basemap off or vendored libraries missing")
        h = draw_layer.head()
        v = draw_layer.version()
        # no ?v= since 2026-09-10 (Nan): the Worker serves scripts and sheets with stale-while-revalidate instead
        self.assertTrue(v)
        self.assertIn('draw.js"', h)
        self.assertIn('draw.css"', h)
        self.assertNotIn("?v=", h)
        # The vendored libraries are pinned files under names that only change
        # when somebody replaces them, so they keep plain names — map_shell's
        # rule, kept here so the two pages agree.
        self.assertIn("vendor/terra-draw.js", h)
        self.assertNotIn("vendor/terra-draw.js?v", h)

    def test_head_urls_and_head_cannot_disagree(self):
        if not draw_layer.enabled():
            self.skipTest("basemap off or vendored libraries missing")
        for u in draw_layer.head_urls():
            self.assertIn(u, draw_layer.head())

    def test_version_moves_when_the_content_moves(self):
        was = draw_layer.version()
        old = draw_layer.CREDIT
        try:
            draw_layer.CREDIT = old + " "
            self.assertNotEqual(draw_layer.version(), was,
                                "version() ignored a change to what the script does")
        finally:
            draw_layer.CREDIT = old
        self.assertEqual(draw_layer.version(), was)

    def test_version_is_a_crc32_hex(self):
        self.assertRegex(draw_layer.version(), r"^[0-9a-f]{8}$")


# ── the three files ─────────────────────────────────────────────────────────

class Licence(unittest.TestCase):
    """ODbL requires the credit and requires it to stay visible. A file is
    where it has to be, because a file travels with no page around it."""

    @needs_node
    def test_the_line_is_inside_all_three(self):
        out = run_node()
        for fmt, text in out["files"].items():
            self.assertIn(out["odbl"], text, f"{fmt} lost the ODbL line")
            self.assertIn(out["attrib"], text, f"{fmt} lost the credit line")
            self.assertIn("motdang.net", text, f"{fmt} lost the domain")

    @needs_node
    def test_geojson_carries_it_per_feature_too(self):
        out = run_node()
        j = json.loads(out["files"]["geojson"])
        self.assertEqual(j["attribution"], out["attrib"])
        self.assertEqual(j["license"], out["odbl"])
        for f in j["features"]:
            self.assertEqual(f["properties"]["attribution"], out["attrib"],
                             "a feature copied out of the collection would lose credit")

    @needs_node
    def test_gpx_and_kml_carry_it_where_the_apps_show_it(self):
        out = run_node()
        gpx, kml = out["files"]["gpx"], out["files"]["kml"]
        self.assertIn("<copyright author=\"OpenStreetMap contributors\">", gpx)
        self.assertIn("opendatacommons.org/licenses/odbl", gpx)
        self.assertIn("<desc>", gpx)
        self.assertIn("<description>", kml)
        # and as a comment, for anyone reading the file rather than opening it
        self.assertIn("<!-- ", gpx)
        self.assertIn("<!-- ", kml)

    def test_the_constants_themselves_say_odbl(self):
        self.assertIn("ODbL", draw_layer.ODBL)
        self.assertIn("OpenStreetMap", draw_layer.ODBL)
        self.assertIn("motdang.net", draw_layer.CREDIT)


class RoundTrip(unittest.TestCase):
    @needs_node
    def test_geojson_is_lossless(self):
        out = run_node()
        back = out["back"]["geojson"]
        self.assertEqual(len(back), 3)
        for got, want in zip(back, [f["geometry"] for f in SHAPES]):
            self.assertEqual(got["type"], want["type"])
            self.assertTrue(coords_near(got["coordinates"], want["coordinates"]),
                            f"{want['type']} moved: {got['coordinates']}")

    @needs_node
    def test_kml_is_lossless(self):
        out = run_node()
        back = out["back"]["kml"]
        self.assertEqual([g["type"] for g in back],
                         ["Point", "LineString", "Polygon"])
        for got, want in zip(back, [f["geometry"] for f in SHAPES]):
            self.assertTrue(coords_near(got["coordinates"], want["coordinates"]))

    @needs_node
    def test_gpx_loses_the_polygon_and_only_the_polygon(self):
        """GPX 1.1 has no polygon type. A drawn area leaves as a CLOSED track,
        which is what OsmAnd and Organic Maps draw, and returns as a line. That
        is a real one-way loss; it is asserted here so it cannot silently
        become a DIFFERENT loss — a dropped shape, or an unclosed ring."""
        out = run_node()
        back = out["back"]["gpx"]
        self.assertEqual([g["type"] for g in back],
                         ["Point", "LineString", "LineString"],
                         "GPX round trip changed shape in an unexpected way")
        self.assertTrue(coords_near(back[0]["coordinates"],
                                    POINT["geometry"]["coordinates"]))
        self.assertTrue(coords_near(back[1]["coordinates"],
                                    LINE["geometry"]["coordinates"]))
        ring = POLY["geometry"]["coordinates"][0]
        self.assertTrue(coords_near(back[2]["coordinates"], ring),
                        "the area came back as a line, but not the same line")
        self.assertTrue(coords_near(back[2]["coordinates"][0],
                                    back[2]["coordinates"][-1]),
                        "the area came back as an OPEN line — the ring lost its close")

    @needs_node
    def test_a_file_it_cannot_read_is_refused_whole(self):
        """Half-reading a file a reader trusted is how a boundary comes back
        with three of its five corners."""
        self.assertFalse(run_node()["junk"])


# ── the hash ────────────────────────────────────────────────────────────────

class Hash(unittest.TestCase):
    @needs_node
    def test_the_codec_round_trips(self):
        out = run_node()
        back = out["hash"]["decoded"]
        self.assertEqual([g["type"] for g in back],
                         ["Point", "LineString", "Polygon"])
        for got, want in zip(back, [f["geometry"] for f in SHAPES]):
            self.assertTrue(coords_near(got["coordinates"], want["coordinates"]))

    @needs_node
    def test_the_token_is_url_fragment_safe(self):
        """The whole reason the alphabet was swapped off polyline's: a
        character a browser percent-encodes costs three, and an encoding that
        grows in the address bar is not an encoding."""
        t = run_node()["hash"]["token"]
        self.assertTrue(t)
        self.assertRegex(t, r"^[A-Za-z0-9_.-]+$")
        self.assertTrue(t.startswith("1."), "the format version is missing")

    @needs_node
    def test_oversized_drawings_are_refused_not_truncated(self):
        h = run_node()["hash"]
        self.assertGreater(h["big_len"], h["max"])
        self.assertEqual(h["part_big"], "",
                         "an over-cap drawing was put in the hash anyway")
        self.assertTrue(h["part_small"].startswith("d="))
        self.assertLessEqual(len(h["part_small"]) - 2, h["max"])

    @needs_node
    def test_the_js_cap_is_the_python_cap(self):
        self.assertEqual(run_node()["hash"]["max"], draw_layer.MAX_HASH_CHARS)

    @needs_node
    def test_python_and_js_encoders_agree(self):
        """draw_layer._enc_prototype exists to make the docstring's numbers
        re-takeable. If it drifts from the JS the measurements become fiction,
        so it is pinned to the real encoder on a fixed input."""
        out = run_node()
        line = LINE["geometry"]["coordinates"]
        # One shape on its own, so the encoder starts from the same (0,0) the
        # prototype does — in a multi-shape drawing every delta chains off the
        # shape before it, which is the whole reason the encoding is compact.
        want = "1.l" + draw_layer._enc_prototype(line)
        self.assertEqual(out["hash"]["token_line_only"], want,
                         "the Python prototype no longer encodes what the JS does")

    def test_the_measurement_still_supports_the_cap(self):
        cap = draw_layer.hash_capacity()
        self.assertEqual(cap["cap_chars"], draw_layer.MAX_HASH_CHARS)
        # The claim in the docstring: hundreds of vertices, not the note's ~40.
        self.assertGreater(cap["vertices_worst"], 300)
        for spacing, cost in cap["chars_per_vertex"].items():
            self.assertGreater(cost, 2.5, f"{spacing} m looks too good to be real")
            self.assertLess(cost, 8.0, f"{spacing} m costs more than the docstring says")


# ── the units ───────────────────────────────────────────────────────────────

class Units(unittest.TestCase):
    """ไร่ leads. A tool that answered '5,660 m²' to somebody holding a chanote
    would be a foreign tool."""

    @needs_node
    def test_rai_leads_and_the_ladder_is_right(self):
        u = run_node()["units"]
        self.assertIn("ไร่", u["rai"]["th"])
        self.assertTrue(u["rai"]["th"].startswith("1 ไร่"), u["rai"]["th"])
        self.assertIn("งาน", u["quarter_rai"]["th"])
        # under a งาน, ตารางวา alone — which is how a small plot is quoted
        self.assertIn("ตร.ว.", u["small"]["th"])
        self.assertNotIn("ไร่", u["small"]["th"])
        self.assertIn("m²", u["rai"]["en"])
        self.assertIn("ha", u["hectare"]["en"])

    @needs_node
    def test_lengths_switch_at_a_kilometre(self):
        u = run_node()["units"]
        self.assertIn("ม.", u["metres"]["th"])
        self.assertIn("กม.", u["km"]["th"])
        self.assertIn(" m", u["metres"]["en"])
        self.assertIn(" km", u["km"]["en"])

    def test_the_python_constants_are_the_thai_ladder(self):
        self.assertEqual(draw_layer.RAI_M2, 1600)
        self.assertEqual(draw_layer.NGAN_M2, 400)
        self.assertEqual(draw_layer.WA_M2, 4)
        self.assertEqual(draw_layer.RAI_M2, 4 * draw_layer.NGAN_M2)
        self.assertEqual(draw_layer.NGAN_M2, 100 * draw_layer.WA_M2)

    @needs_node
    def test_the_ring_closes(self):
        self.assertEqual(run_node()["ring_pts"], 65)


# ── no emoji, anywhere a reader looks ───────────────────────────────────────

# Deliberately broad. `·` (00B7), `²` (00B2) and `©` (00A9) are typography and
# stay; everything a phone would render as a coloured picture is out.
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF←-⇿⌀-➿⬀-⯿"
    "☀-⛿️‍⃣]")


class _G(dict):
    """The three build.py helpers controls_html needs, as stand-ins. Importing
    build.py runs the whole site's top level (glyphs.py says so and it is still
    true), and none of these three is what is under test here."""
    def __init__(self):
        super().__init__(
            bi=lambda th, en, sep=" · ", raw=False: f"{th}{sep}{en}",
            bi_text=lambda th, en, sep=" · ": f"{th}{sep}{en}",
            att=lambda s: str(s).replace('"', "&quot;"),
        )


class NoEmoji(unittest.TestCase):
    def test_the_bar_draws_marks_not_emoji(self):
        html = draw_layer.controls_html(_G())
        found = EMOJI.findall(html)
        self.assertEqual(found, [], f"emoji in the toolbar: {found}")

    def test_the_script_prints_no_emoji(self):
        found = EMOJI.findall(JS)
        self.assertEqual(found, [], f"emoji in draw.js: {found}")

    def test_the_stylesheet_and_the_glyphs_too(self):
        for name, text in (("draw.css", draw_layer.CSS),
                           ("glyphs_draw", glyphs_draw.SPRITE)):
            self.assertEqual(EMOJI.findall(text), [], f"emoji in {name}")

    def test_every_control_carries_a_drawn_mark_and_a_name(self):
        html = draw_layer.controls_html(_G())
        for key, gid, th, en in draw_layer.TOOLS:
            self.assertIn(f'data-mdd="{key}"', html)
            self.assertIn(f'href="#{gid}"', html, f"{key} has no mark")
        # every <use> on the bar points at an id one of the three sprites draws
        for gid in set(re.findall(r'href="#([^"]+)"', html)):
            self.assertIn(gid, glyphs_draw.KNOWN, f"{gid} is in no sprite")

    def test_the_bar_is_bilingual_throughout(self):
        html = draw_layer.controls_html(_G())
        thai = re.compile("[฀-๿]")
        self.assertTrue(thai.search(html), "no Thai on the bar")
        self.assertIn("save as GeoJSON", html)
        self.assertIn("Touch a tool", html)
        # every accessible name carries both halves
        for label in re.findall(r'aria-label="([^"]*)"', html):
            self.assertIn(" · ", label, f"one-language label: {label}")


# ── the five new marks ──────────────────────────────────────────────────────

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


class Glyphs(unittest.TestCase):
    def test_no_collision_with_either_existing_sprite(self):
        clash = set(glyphs_draw.IDS) & glyphs.KNOWN
        self.assertEqual(clash, set(),
                         f"a <use> would draw the wrong picture: {sorted(clash)}")

    def test_ids_are_i_prefixed_and_unique(self):
        self.assertEqual(len(set(glyphs_draw.IDS)), len(glyphs_draw.IDS))
        for k in glyphs_draw.IDS:
            self.assertRegex(k, r"^i-[a-z0-9-]+$")

    def test_stroke_only_no_colour_of_its_own(self):
        """Colour is the row's, always — the .rowicon rule in build.py. A fill=
        or stroke= inside the sprite is a mark that ignores its context."""
        s = glyphs_draw.SPRITE
        self.assertNotIn("fill=", s)
        self.assertNotIn("stroke=", s.replace("stroke-dasharray=", ""))
        self.assertNotIn("style=", s.replace('style="position:absolute"', ""))

    def test_every_mark_draws_inside_the_24_grid(self):
        for k in glyphs_draw.IDS:
            body = glyphs_draw.sprite([k])
            nums = [abs(float(n)) for n in _NUM.findall(
                re.sub(r'id="[^"]*"', "", body).split("<defs>")[1])]
            self.assertTrue(nums, f"{k} draws nothing")
            # the .rowicon stroke is 1.6, so a path at 0 or 24 is clipped
            self.assertLessEqual(max(nums), 24.0, f"{k} runs off the grid")

    def test_icon_is_hidden_by_default_and_named_when_asked(self):
        self.assertIn("aria-hidden", glyphs_draw.icon("i-poly"))
        named = glyphs_draw.icon("i-poly", label="รูปปิด · area")
        self.assertIn('role="img"', named)
        self.assertIn('aria-label="รูปปิด · area"', named)

    def test_icon_refuses_an_id_nothing_draws(self):
        self.assertEqual(glyphs_draw.icon("i-does-not-exist"), "")

    def test_the_marks_this_bar_uses_all_resolve(self):
        for gid in glyphs_draw.USED:
            self.assertIn(gid, glyphs_draw.KNOWN)


# ── what is taste, printed ──────────────────────────────────────────────────

class Printed(unittest.TestCase):
    def test_print_the_numbers(self):
        import gzip

        def gz(s):
            return len(gzip.compress(s.encode("utf-8"), 9))

        print("\n  --- draw_layer, measured now ---")
        print("  version           ", draw_layer.version())
        print("  enabled           ", draw_layer.enabled())
        print("  draw.js           %6d B raw  %6d B gz" % (len(JS.encode()), gz(JS)))
        print("  draw.css          %6d B raw  %6d B gz"
              % (len(draw_layer.CSS.encode()), gz(draw_layer.CSS)))
        tot = 0
        for f in draw_layer.VENDOR:
            p = ROOT / "assets" / "vendor" / f
            if not p.exists():
                print("  MISSING           ", f)
                continue
            b = p.read_bytes()
            g = len(gzip.compress(b, 9))
            if f.endswith(".js"):
                tot += g
            print("  %-26s %8d B raw %7d B gz" % (f, len(b), g))
        print("  vendored JS total  %d B gz" % tot)
        print("  hash              ", json.dumps(draw_layer.hash_capacity(),
                                                 ensure_ascii=False))
        if not NODE:
            print("  node NOT FOUND — the round-trip cases skipped")
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
