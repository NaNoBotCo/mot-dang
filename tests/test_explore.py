"""WO-77 · WO-74 Ph 0–2 on /map.html — what the explore map promises.

Mechanics, not taste:

  · the view is the URL: the hash's fifth part carries tag / r / ev and the
    reader reads back what the writer wrote
  · every chip carries its total, so a count in view can be drawn over it
  · the ring, the events door and the list twin are in the markup
  · the bar wears drawn glyphs and no emoji
  · on the page the map comes first, then the controls, the shelves, and the
    words last, one sentence each (item 28)
  · with no view in the hash, explore.js builds the box on the city the
    front page remembers in localStorage md-city, and only a province key
    counts as a city (item 31)
  · explore.js compiles (node) — a syntax error here is a blank map

Run: python3 -m unittest tests.test_explore -v
"""

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import explore_layer as X  # noqa: E402
import glyphs  # noqa: E402

EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def _js():
    return X._js()


class Markup(unittest.TestCase):
    def _page(self):
        from html import escape
        bi = lambda th, en, sep=" · ": f"{th}{sep}{en}"
        att = lambda s: escape(str(s), quote=True)
        g = {
            "bi": bi, "bi_text": bi, "att": att, "esc": lambda s: escape(str(s)),
            "page": lambda title, body, **k: body, "share_block": lambda *a: "",
            "BASE": "https://motdang.net/", "map_shell": __import__("map_shell"),
            "CATS": {"wat": {"th": "วัด", "en": "Wats"}, "food": {"th": "ของกิน", "en": "Food"}},
            "CAT_ORDER": ["wat", "food"],
            "_EXPLORE_COUNTS": {("cm", "wat"): 1524, ("cm", "food"): 4178, ("cr", "wat"): 3},
            "PROVINCES": [{"key": "cm", "th": "เชียงใหม่", "en": "Chiang Mai"},
                          {"key": "cr", "th": "เชียงราย", "en": "Chiang Rai"}],
            "MOAT_POLY": [(18.79, 98.98), (18.79, 99.0), (18.78, 99.0), (18.78, 98.98)],
        }
        return X.build_page(g)

    def test_chips_carry_their_total(self):
        html = self._page()
        self.assertIn('data-x="cm-wat" data-total="1524"', html)
        self.assertIn('data-x="cm-food" data-total="4178"', html)
        self.assertNotIn('data-x="cr-wat"', html, "a shelf under the floor of 8 gets no chip")

    def test_the_ring_the_events_door_and_the_list_twin(self):
        html = self._page()
        for i in ('id="xring"', 'id="xev"', 'id="xlist"', 'id="xcross"', 'id="xhere"', 'id="xopen"'):
            self.assertIn(i, html, i)
        for m, _, _ in X.RING_M:
            self.assertIn(f'<option value="{m}">', html)

    def test_the_map_comes_before_the_words(self):
        html = self._page()
        marks = ['<h1>', 'id="xmap"', '<div class="xbar">', 'id="xhint"',
                 '<div class="xpick">', '<p class="lede">', '<div class="xdir">']
        at = [html.index(m) for m in marks]
        self.assertEqual(at, sorted(at), marks)

    def test_the_lede_is_one_sentence_each(self):
        html = self._page()
        lede = re.search(r'<p class="lede">(.*?)</p>', html).group(1)
        th, en = lede.split(" · ", 1)
        self.assertEqual(en.count("."), 1, en)
        self.assertTrue(en.endswith("."), en)
        self.assertNotIn("—", lede)
        self.assertLess(len(en.split()), 20, en)

    def test_the_bar_wears_glyphs_not_emoji(self):
        html = self._page()
        bar = re.search(r'(?s)<div class="xbar">(.*?)</div>', html).group(1)
        self.assertIsNone(EMOJI.search(bar), EMOJI.findall(bar))
        for g in ("i-here", "i-lamp", "i-cal", "i-ring", "i-camera", "i-x"):
            self.assertIn(f'href="#{g}"', bar, g)
            self.assertIn(g, glyphs.KNOWN)


class Script(unittest.TestCase):
    def test_the_hash_carries_the_view(self):
        js = _js()
        for needle in ("function viewParams", "tag=", "r=", "ev=1", "out.tag=v",
                       "function countInView", "function filterExpr", "'-stack'",
                       "data/events.geojson", "search.html?near="):
            self.assertIn(needle, js, needle)

    def test_the_remembered_city_opens_the_map(self):
        js = _js()
        self.assertNotIn("%CITY%", js)
        self.assertIn("localStorage.getItem('md-city')", js)
        for k, c in X.map_shell.CENTERS.items():
            self.assertIn('"%s": {"lng": %s, "lat": %s, "zoom": %s}'
                          % (k, c["lng"], c["lat"], X.CITY_ZOOM), js, k)
        # the hash still wins: the box is set to the city only with no view
        # in the link, and the jumpTo in ready() sits on the no-view branch
        self.assertLess(js.index("if(!readHash())"), js.index("md-city"))
        self.assertIn("el.dataset.lat=v0.lat;el.dataset.lng=v0.lng;el.dataset.zoom=v0.zoom", js)
        self.assertLess(js.index("var want=readHash()"), js.rindex("md-city"))
        # an inherited key ('constructor', '__proto__') is not a city
        self.assertIn("Object.prototype.hasOwnProperty.call(CITY,c0)&&CITY[c0]", js)
        self.assertIn("Object.prototype.hasOwnProperty.call(CITY,city)&&CITY[city]", js)

    @unittest.skipUnless(shutil.which("node"), "node not on PATH")
    def test_explore_js_compiles(self):
        r = subprocess.run(["node", "--check", "-"], input=_js(), text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr[:400])


if __name__ == "__main__":
    unittest.main()
