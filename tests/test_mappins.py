"""mappins_layer.py: the icon pins on every map."""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import mappins_layer  # noqa: E402


def _lum(hx):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


class Pins(unittest.TestCase):
    def test_white_glyph_reads_on_every_disc(self):
        for k, (_, col) in list(mappins_layer.KINDS.items()) + [("_", mappins_layer.OTHER)]:
            ratio = 1.05 / (_lum(col) + 0.05)
            self.assertGreaterEqual(ratio, 4.5, f"{k} {col} {ratio:.2f}")

    def test_glyphs_match_the_directory_rows(self):
        src = (ROOT / "build.py").read_text()
        block = re.search(r"^CAT_ICON = \{(.*?)^\}", src, re.S | re.M).group(1)
        cat = dict(re.findall(r'"([\w-]+)": "(i-[\w-]+)"', block))
        cat["school"] = "i-school"
        for k, g in cat.items():
            self.assertIn(k, mappins_layer.KINDS, k)
            self.assertEqual(mappins_layer.KINDS[k][0], g, k)

    def test_every_glyph_has_paths(self):
        for k, v in mappins_layer.table().items():
            self.assertTrue(v[1], k)

    def test_js_parses(self):
        with tempfile.TemporaryDirectory() as d:
            mappins_layer.emit(d)
            subprocess.run(["node", "--check", str(Path(d) / "pins.js")], check=True)
            subprocess.run(["node", "--check", str(ROOT / "assets/sites/doodle-map/map.js")], check=True)

    def test_stamp_names_scripts_by_content(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            for s in ("doodle-map", "doodle-chiang-rai"):
                shutil.copytree(ROOT / "assets/sites" / s, Path(d) / "sites" / s)
            self.assertEqual(mappins_layer.stamp_doodle(d), 2)
            js = (Path(d) / "sites/doodle-map/map.js").read_text()
            self.assertIn("/pins.js?v=" + mappins_layer.version(), js)
            for s in ("doodle-map", "doodle-chiang-rai"):
                self.assertRegex((Path(d) / "sites" / s / "index.html").read_text(), r'map\.js\?v=[0-9a-f]{8}"')


if __name__ == "__main__":
    unittest.main()
