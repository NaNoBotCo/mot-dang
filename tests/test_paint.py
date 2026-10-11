#!/usr/bin/env python3
"""WO-79 — colour by. What can silently be wrong, asserted.

Run either way:

    python3 tests/test_paint.py
    python3 -m unittest tests.test_paint -v

WHAT IS ASSERTED, AND WHY EACH ONE IS HERE

  · THREE STATES OF OPENNESS, never two, and the third one's words say
    "no hours posted" rather than "closed" or "unknown". A future session
    tidying this into open/closed would be publishing a claim about 58,330
    businesses that none of them made, and the tidy-up would look like an
    improvement.
  · A ramp is ONE HUE. Held to within 8-bit quantisation, which is measured
    here rather than assumed — see paint_layer.HUE_QUANT.
  · Six inks is the cap for anything categorical. A seventh says two shelves
    are one shelf.
  · Every ink clears the site's own contrast floor on paper.
  · No emoji in anything a reader sees. glyphs.py exists so that the site's
    marks are drawn; an emoji that crept back into a label would render as
    whatever the reader's phone decided.
  · A dormant dimension is not offered AND names the data change that wakes
    it. A dimension listed with no `needs` and no data is a control that does
    nothing.

WHAT IS PRINTED, NOT ASSERTED

  The colour-vision floor of the six shipping inks. It fails, today, at
  ΔE00 3.81 — and it is NOT asserted, because a failing assertion here would
  mean this suite goes red until somebody changes the site's palette, and
  which six inks the site paints in is Nan's call, not a test's. The number
  is printed on every run so it cannot be forgotten, and it is written up in
  notes/maps-grow-2026-09-08.txt §11.
"""

import colorsys
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import explore_layer  # noqa: E402
import paint_layer as P  # noqa: E402

# Anything in the pictographic planes, plus the dingbats and misc symbols the
# glyph sweep already knows about.
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF\U0000FE0F\U0001F000-\U0001F02F]")


class _G(dict):
    """The slice of build.py's globals these functions actually use."""

    def __init__(self):
        import html
        super().__init__(
            bi=lambda th, en: "%s · %s" % (th, en),
            bi_text=lambda th, en: "%s · %s" % (th, en),
            att=lambda s: html.escape(str(s), quote=True),
            esc=lambda s: html.escape(str(s)),
        )


class Openness(unittest.TestCase):
    """THREE, NEVER TWO. Absent is not closed."""

    def setUp(self):
        self.dim = P.BY_KEY["open"]

    def test_there_are_exactly_three_states(self):
        self.assertEqual(len(self.dim["values"]), 3,
                         "openness must have three states: open, shut, "
                         "no hours posted")

    def test_the_buckets_are_named_what_they_mean(self):
        self.assertEqual([b["bucket"] for b in self.dim["values"]],
                         ["open", "shut", "nohours"])

    def test_the_third_state_is_not_called_closed_or_unknown(self):
        third = self.dim["values"][2]
        for word in ("closed", "unknown", "ปิด"):
            self.assertNotIn(word, third["en"].lower().replace("closed", "")
                             if word == "closed" else third["en"].lower(),
                             "the no-hours state must not be worded as closed "
                             "or unknown")
        # The English says outright what it is NOT.
        self.assertIn("not the same as closed", third["en"].lower())
        self.assertIn("ยังไม่มีใครบอก", third["th"])

    def test_each_state_has_its_own_ink(self):
        inks = [b["ink"] for b in self.dim["values"]]
        self.assertEqual(len(set(inks)), 3, "two states share an ink")

    def test_open_reuses_the_ring_green_so_two_controls_cannot_disagree(self):
        # explore_layer draws the open-now ring in this exact value.
        self.assertIn("'circle-stroke-color':'%s'" % P.OPEN_INK,
                      explore_layer.JS.replace(" ", ""),
                      "the open state must be the same jade as the open-now ring")

    def test_the_three_survive_colour_vision(self):
        r = P.cvd_report([b["ink"] for b in self.dim["values"]],
                         [b["bucket"] for b in self.dim["values"]])
        self.assertTrue(r["survives"],
                        "openness inks collide under CVD: floor %.2f (%s/%s)"
                        % (r["floor"], *r[min(
                            (k for k in r if k not in ("floor", "survives",
                                                       "normal vision")),
                            key=lambda k: r[k]["min_de00"])]["pair"]))

    def test_the_js_paints_all_three_and_defaults_to_nohours(self):
        js = P._js()
        for b in ("by.open", "by.shut", "by.nohours"):
            self.assertIn(b, js)
        # Before the lamp file arrives, nothing may be called shut.
        self.assertIn("if(!lamps.hours)return by.nohours", js)


class Ramps(unittest.TestCase):
    """One hue. Lightness only. The retune lesson, asserted."""

    def ramps(self):
        return [d for d in P.LIVE if d["kind"] == "ramp"]

    def test_there_is_at_least_one(self):
        self.assertTrue(self.ramps())

    def test_hue_and_saturation_are_held(self):
        for d in self.ramps():
            stops = P.inks_of(d)
            h0, _l, s0 = colorsys.rgb_to_hls(*P._rgb(stops[0]))
            for s in stops:
                h, _, sat = colorsys.rgb_to_hls(*P._rgb(s))
                self.assertLessEqual(
                    abs(h - h0), P.HUE_QUANT,
                    "%s ramp: %s drifts %.2f deg from the base hue — a ramp "
                    "must move lightness ONLY (maps-gemba 2026-08-20 §2e)"
                    % (d["key"], s, abs(h - h0) * 360))
                self.assertLessEqual(
                    abs(sat - s0), P.SAT_QUANT,
                    "%s ramp: %s drifts %.4f in saturation — boosting "
                    "saturation is what produced the lime-green map"
                    % (d["key"], s, abs(sat - s0)))

    def test_lightness_moves_monotonically(self):
        for d in self.ramps():
            ls = [colorsys.rgb_to_hls(*P._rgb(s))[1] for s in P.inks_of(d)]
            self.assertEqual(ls, sorted(ls, reverse=True),
                             "%s ramp does not run light to dark" % d["key"])

    def test_every_stop_is_legible_on_paper(self):
        for d in self.ramps():
            for s in P.inks_of(d):
                self.assertGreaterEqual(
                    P.contrast(s, P.PAPER), P.DOT_BAR,
                    "%s ramp: %s is %.2f:1 on paper — under the %.1f:1 floor, "
                    "a dot nobody can see" % (d["key"], s,
                                              P.contrast(s, P.PAPER), P.DOT_BAR))

    def test_the_distance_bands_are_the_rings_own_ladder(self):
        d = P.BY_KEY["dist"]
        self.assertEqual(d["values"]["edges"],
                         [m for m, _th, _en in explore_layer.RING_M],
                         "the distance bands must BE explore_layer.RING_M — "
                         "two ladders on one screen is two answers to one "
                         "question")
        self.assertEqual(len(P.inks_of(d)), len(explore_layer.RING_M) + 1,
                         "n edges need n+1 bands (the last one is 'beyond')")

    def test_the_distance_paint_uses_the_maps_own_distance_expression(self):
        js = P._js()
        self.assertIn("['distance',pt]", js.replace(" ", ""),
                      "distance colouring must use MapLibre's `distance` "
                      "expression — the same one the ring filters with — not "
                      "a second implementation")


class Cap(unittest.TestCase):
    def test_six_inks_is_the_cap_for_categorical(self):
        for d in P.DIMENSIONS:
            if d["kind"] != "categorical" or not d["values"]:
                continue
            self.assertFalse(
                P.over_cap(d),
                "%s offers %d inks; six is the cap and a seventh would have "
                "to repeat one, which says two buckets are one bucket"
                % (d["key"], len(P.inks_of(d))))

    def test_the_cap_is_explore_layers_own(self):
        self.assertEqual(explore_layer.MAX_ON, len(explore_layer.INKS))

    def test_a_ramp_is_exempt_and_says_so(self):
        # A ramp may have ten stops; it is one hue, read as an amount.
        self.assertGreater(len(P.inks_of(P.BY_KEY["rank"])),
                           explore_layer.MAX_ON)
        self.assertFalse(P.over_cap(P.BY_KEY["rank"]))


class TheTable(unittest.TestCase):
    """A new dimension is data, not a module."""

    def test_every_row_has_the_five_fields(self):
        for d in P.DIMENSIONS:
            for k in ("key", "label_th", "label_en", "kind", "values"):
                self.assertIn(k, d, "%s is missing %s" % (d.get("key"), k))
            self.assertIn(d["kind"], ("ramp", "categorical"))

    def test_keys_are_unique(self):
        keys = [d["key"] for d in P.DIMENSIONS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_kind_is_the_default(self):
        self.assertEqual(P.DEFAULT, "kind")
        self.assertIn("kind", [d["key"] for d in P.LIVE])

    def test_a_dormant_row_is_not_offered(self):
        offered = {d["key"] for d in P.LIVE}
        for d in P.DORMANT:
            self.assertNotIn(d["key"], offered)
            self.assertNotIn('"key": "%s"' % d["key"], P._js())

    def test_every_dormant_row_names_what_unblocks_it(self):
        for d in P.DORMANT:
            need = d["needs"] or ""
            self.assertGreater(len(need), 40,
                               "%s must say exactly what data change wakes it"
                               % d["key"])
            self.assertIn("geojson", need.lower(),
                          "%s: name the file and function that must change"
                          % d["key"])

    def test_tag_and_tambon_are_the_dormant_ones(self):
        self.assertEqual({d["key"] for d in P.DORMANT}, {"tag", "tambon"})

    def test_no_dimension_name_is_hardcoded_outside_the_table(self):
        """A key that appears in the CSS or the control builder would mean a
        new dimension is not just a row."""
        src = (ROOT / "paint_layer.py").read_text()
        body = src.split("DIMENSIONS = (")[1].split("BY_KEY = ")[0]
        after = src.split("BY_KEY = ")[1]
        # The JS legitimately branches per dimension (each paints differently);
        # the Python that builds the control must not.
        py = after.split("JS = r\"\"\"")[0]
        for key in ("tag", "tambon"):
            self.assertNotIn('"%s"' % key, py,
                             "%s is named outside the table" % key)
        self.assertIn(key, body)


class Legend(unittest.TestCase):
    """The control IS the legend."""

    def setUp(self):
        self.g = _G()
        self.sel, self.keys = P.control_html(self.g)

    def test_every_option_wears_its_ink(self):
        for d in P.LIVE:
            first = P.inks_of(d)[0]
            self.assertIn('value="%s" style="background:%s' % (d["key"], first),
                          self.sel,
                          "the %s option does not carry its ink" % d["key"])

    def test_a_legend_strip_exists_for_every_live_dimension(self):
        for d in P.LIVE:
            self.assertIn('data-p="%s"' % d["key"], self.keys)

    def test_the_strip_carries_the_actual_inks(self):
        """The guaranteed carrier — <option> backgrounds are not honoured
        everywhere, so the swatches below the bar are what must always be
        there."""
        for d in P.LIVE:
            if d["key"] == "kind":
                continue      # the shelf chips are already its legend
            for ink in P.inks_of(d):
                self.assertIn(ink, self.keys,
                              "%s ink %s never appears in the legend"
                              % (d["key"], ink))

    def test_only_the_default_strip_is_visible(self):
        shown = re.findall(r'<div class="pkey" data-p="([a-z]+)"(?! hidden)>',
                           self.keys)
        self.assertEqual(shown, [P.DEFAULT])

    def test_a_zero_count_is_still_drawn(self):
        """A bucket that vanishes when empty is a map that looks tidier than
        the data is."""
        self.assertIn('<span class="pn"></span>', self.keys)
        self.assertNotIn("display:none", P.CSS.split(".pn{")[1].split("}")[0])

    def test_the_swatch_is_the_same_dot_the_map_draws(self):
        self.assertIn("width:12px;height:12px;border-radius:50%", P.CSS)
        self.assertIn("width:12px;height:12px;border-radius:50%",
                      explore_layer.CSS)


class NoEmoji(unittest.TestCase):
    """Drawn glyphs, never system emoji. WO-77."""

    def test_no_emoji_in_the_control_or_the_legend(self):
        g = _G()
        sel, keys = P.control_html(g)
        for name, blob in (("the select", sel), ("the legend", keys)):
            hit = EMOJI.findall(blob)
            self.assertEqual(hit, [], "%s carries emoji: %r" % (name, hit))

    def test_no_emoji_in_the_shipped_js_or_css(self):
        for name, blob in (("paint.js", P._js()), ("paint.css", P.CSS)):
            self.assertEqual(EMOJI.findall(blob), [],
                             "%s carries emoji" % name)

    def test_no_emoji_in_any_label_in_the_table(self):
        for d in P.DIMENSIONS:
            for k in ("label_th", "label_en"):
                self.assertEqual(EMOJI.findall(d[k]), [], "%s.%s" % (d["key"], k))
            for b in (d["values"] or ()) if d["kind"] == "categorical" else ():
                for k in ("th", "en"):
                    self.assertEqual(EMOJI.findall(b[k]), [],
                                     "%s bucket %s" % (d["key"], b["bucket"]))

    def test_the_control_uses_a_drawn_glyph(self):
        import glyphs
        sel, _ = P.control_html(_G())
        m = re.search(r'<use href="#([a-z0-9-]+)">', sel)
        self.assertIsNotNone(m, "the control draws no glyph")
        self.assertIn(m.group(1), glyphs.KNOWN,
                      "%s is not in either sprite — <use> would draw nothing"
                      % m.group(1))


class Shipping(unittest.TestCase):
    def test_the_js_is_valid_json_where_it_claims_to_be(self):
        js = P._js()
        m = re.search(r"var DIMS=(\[.*?\]), DEFAULT=(\S+?);", js, re.S)
        self.assertIsNotNone(m)
        dims = json.loads(m.group(1))
        self.assertEqual([d["key"] for d in dims], [d["key"] for d in P.LIVE])
        self.assertEqual(json.loads(m.group(2)), P.DEFAULT)

    def test_the_version_changes_when_the_js_does(self):
        v = P.version()
        self.assertRegex(v, r"^[0-9a-f]{8}$")
        old = P.JS
        try:
            P.JS = old + "/* x */"
            self.assertNotEqual(P.version(), v)
        finally:
            P.JS = old

    def test_it_never_adds_a_layer_or_a_source(self):
        """This layer owns circle-color and nothing else. addLayer or
        addSource here would be a second map constructor by the back door —
        the thing CLAUDE.md forbids."""
        js = P._js()
        for forbidden in ("addSource", "addLayer", "new maplibregl"):
            self.assertNotIn(forbidden, js)

    def test_it_never_fetches(self):
        self.assertNotIn("fetch(", P._js(),
                         "the lamp file is explore.js's to fetch; a second "
                         "fetch of the same file is a second answer")


def _print_the_measurement():
    inks = [i for i, _ in explore_layer.INKS]
    names = [lbl.split(" · ")[-1] for _, lbl in explore_layer.INKS]
    r = P.cvd_report(inks, names)
    print("\n--- PRINTED, NOT ASSERTED: the six shipping inks under "
          "colour-vision simulation ---")
    for k in ("normal vision",) + tuple(P.CVD_MODELS):
        print("  %-28s min DE00 %6.2f   %s / %s"
              % (k, r[k]["min_de00"], r[k]["pair"][0], r[k]["pair"][1]))
    print("  floor %.2f — %s (working floor for a dot on a map: %.0f)"
          % (r["floor"], "survives" if r["survives"] else "DOES NOT SURVIVE",
             P.JND))
    print("  Which six inks the site paints in is Nan's; see "
          "notes/maps-grow-2026-09-08.txt section 11.\n")


if __name__ == "__main__":
    _print_the_measurement()
    unittest.main(verbosity=2)
