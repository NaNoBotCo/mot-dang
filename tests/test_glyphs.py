"""WO-77 — the chrome glyphs.

What can silently break, asserted; what is a matter of taste, printed.

  · no id in glyphs.py collides with build.ICON_SPRITE — <use> takes the
    first match and a duplicate draws the wrong picture without an error
  · every glyph draws something, and draws it inside the 24 grid with the
    stroke margin the .rowicon rule needs
  · no glyph carries its own colour (the filled ant and the filter knobs are
    the named exceptions; anything else with fill= or stroke= is a bug)
  · every EMOJI target exists, in one sprite or the other
  · icon() with a label is announced; without one it is hidden

Coverage — which emoji in build.py still have no drawn glyph — is PRINTED,
not asserted: a new emoji in a new feature should not fail this suite, it
should show up in the list.

Run: python3 -m unittest tests.test_glyphs -v
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import glyphs  # noqa: E402

_BUILD = (ROOT / "build.py").read_text()
_m = re.search(r'ICON_SPRITE = """(.*?)"""', _BUILD, re.S)
BUILD_IDS = set(re.findall(r'<g id="([^"]+)"', _m.group(1))) if _m else set()

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_ALLOWED_FILL = {"i-ant-solid", "i-filter"}


class Ids(unittest.TestCase):
    def test_no_collision_with_build_sprite(self):
        self.assertTrue(BUILD_IDS, "could not read build.ICON_SPRITE")
        clash = set(glyphs.IDS) & BUILD_IDS
        self.assertEqual(clash, set(), f"ids already in build.ICON_SPRITE: {sorted(clash)}")

    def test_build_ids_pinned_to_the_real_sprite(self):
        self.assertEqual(set(glyphs.BUILD_IDS), BUILD_IDS,
                         "glyphs.BUILD_IDS drifted from build.ICON_SPRITE — update the tuple")

    def test_ids_are_i_prefixed_and_unique(self):
        self.assertEqual(len(set(glyphs.IDS)), len(glyphs.IDS))
        for k in glyphs.IDS:
            self.assertRegex(k, r"^i-[a-z0-9-]+$")

    def test_every_emoji_target_exists(self):
        every = set(glyphs.IDS) | BUILD_IDS
        missing = {e: g for e, g in glyphs.EMOJI.items() if g not in every}
        self.assertEqual(missing, {})
        for k in list(glyphs.CAT_ICON_MORE.values()) + [p[1] for p in glyphs.PATHS]:
            self.assertIn(k, every)


class Drawing(unittest.TestCase):
    def test_every_glyph_draws_something(self):
        for k in glyphs.IDS:
            body = glyphs._G[k]
            self.assertRegex(body, r"<(path|circle|ellipse|rect|line|polyline)\b", k)

    def test_inside_the_grid(self):
        # Absolute coordinates only need checking; relative deltas are short
        # by construction. A number past 24 or under 0 in an absolute
        # command is a stroke the .rowicon rule will clip.
        for k in glyphs.IDS:
            for d in re.findall(r'\bd="([^"]+)"', glyphs._G[k]):
                for cmd, args in re.findall(r"([MLHVCSQTAZmlhvcsqtaz])([^MLHVCSQTAZmlhvcsqtaz]*)", d):
                    if cmd.islower():
                        continue
                    for n in _NUM.findall(args):
                        v = float(n)
                        self.assertTrue(-0.5 <= v <= 24.5, f"{k}: {cmd}{args.strip()} leaves the grid")
            for attr in ("cx", "cy", "x", "y"):
                for n in re.findall(rf'\b{attr}="(-?[\d.]+)"', glyphs._G[k]):
                    self.assertTrue(0 <= float(n) <= 24, f"{k}: {attr}={n}")

    def test_no_colour_of_its_own(self):
        for k in glyphs.IDS:
            if k in _ALLOWED_FILL:
                continue
            self.assertNotIn("fill=", glyphs._G[k], k)
            self.assertNotIn("stroke=", glyphs._G[k], k)
            self.assertNotIn("style=", glyphs._G[k], k)

    def test_sprite_is_one_svg_with_all_ids(self):
        s = glyphs.SPRITE
        self.assertTrue(s.startswith("<svg") and s.endswith("</svg>"))
        self.assertEqual(s.count("<g id="), len(glyphs.IDS))
        sub = glyphs.sprite(["i-map-not-here", "i-ant", "i-here"])
        self.assertEqual(sub.count("<g id="), 2)


class Icon(unittest.TestCase):
    def test_decorative_by_default(self):
        h = glyphs.icon("i-ant")
        self.assertIn('aria-hidden="true"', h)
        self.assertIn('href="#i-ant"', h)

    def test_labelled_when_it_stands_alone(self):
        h = glyphs.icon("i-here", label="ตรงนี้ · where I am")
        self.assertIn('role="img"', h)
        self.assertIn('aria-label="ตรงนี้ · where I am"', h)
        self.assertNotIn("aria-hidden", h)

    def test_unknown_id_draws_nothing(self):
        self.assertEqual(glyphs.icon("i-nope"), "")

    def test_emoji_swap_is_chrome_only(self):
        out = glyphs.emoji_to_icon("📍 ตรงนี้ · 🗺 map")
        self.assertIn("#i-here", out)
        self.assertIn("#i-map", out)
        self.assertNotIn("📍", out)


class Coverage(unittest.TestCase):
    def test_print_what_is_still_emoji_in_build(self):
        # Printed, never asserted.
        chrome = re.findall(r"[\U0001F300-\U0001FAFF☀-➿⭐⬆〰〽]", _BUILD)
        left = sorted({c for c in chrome if c not in glyphs.EMOJI})
        sys.stderr.write(f"\n  emoji in build.py with no drawn glyph yet ({len(left)}): {' '.join(left)}\n")
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
