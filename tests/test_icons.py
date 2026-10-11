"""The sprite is one file, not a copy in every page (2026-09-10).

Both icon sprites used to be pasted inline into every page — 18 KB, identical,
60% of a place page. build.ICONS_SVG is that block written once to
docs/icons.svg, and page() points every <use href="#i-x"> at it on the way
out. These tests hold the seam: the file holds every id both sprites define,
a finished page carries no inline sprite and no bare "#i-" reference, and the
reference resolves from any depth, including the root-absolute 404 page.

    python3 tests/test_icons.py
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build     # noqa: E402  (runs the site's top level: loads data, writes nothing)
import glyphs    # noqa: E402


class Sprite(unittest.TestCase):
    def test_the_file_holds_every_id_from_both_sprites(self):
        ids = set(re.findall(r'<g id="([^"]+)"', build.ICONS_SVG))
        self.assertTrue(set(glyphs.IDS) <= ids, set(glyphs.IDS) - ids)
        self.assertTrue(set(glyphs.BUILD_IDS) <= ids, set(glyphs.BUILD_IDS) - ids)
        self.assertEqual(ids, set(build.SPRITE_IDS))
        self.assertTrue(build.ICONS_SVG.startswith("<svg"))
        self.assertTrue(build.ICONS_SVG.rstrip().endswith("</svg>"))
        self.assertEqual(build.ICONS_SVG.count("<defs>"), 1)

    def test_a_page_points_every_use_at_the_file(self):
        html = build.page("t", build.svg_icon("i-wat") + glyphs.icon("i-ant"), 2,
                          path="cm/tag/x.html")
        self.assertNotIn('<g id="i-wat">', html)          # no inline sprite
        self.assertNotIn('href="#i-', html)
        at = "../../icons.svg"
        self.assertIn(f'href="{at}#i-wat"', html)
        self.assertIn(f'href="{at}#i-ant"', html)
        self.assertIn(f'data-icons="{at}"', html)

    def test_root_absolute_page(self):
        html = build.page("t", build.svg_icon("i-wat"), 0, path="404.html", root="/")
        self.assertIn('href="/icons.svg#i-wat"', html)

    def test_page_local_uses_are_left_alone(self):
        out = build.point_uses_at_sprite('<use href="#pk3"></use><use href="#i-wat"></use>', "../")
        self.assertIn('href="#pk3"', out)
        self.assertIn('href="../icons.svg#i-wat"', out)


if __name__ == "__main__":
    unittest.main()
