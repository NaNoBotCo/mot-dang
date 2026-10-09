"""thaiscript.py — a Latin name read in Thai, and the map rows that carry readings.

  · a Thai or mixed name needs no Thai reading
  · sign words, Thai words in Latin, run-together Thai names, heads, initials
  · front_layer._nm gives a row the reading of the script it lacks, and nothing
    when the name already stands in both

Run: python3 -m unittest tests.test_thaiscript -v
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import thaiscript  # noqa: E402
import front_layer  # noqa: E402


class Reading(unittest.TestCase):
    def test_thai_needs_none(self):
        self.assertEqual(thaiscript.reading("วัดพระสิงห์"), "")
        self.assertEqual(thaiscript.reading("บ้านสบายใจ coffee"), "")
        self.assertEqual(thaiscript.reading(""), "")

    def test_sign_words(self):
        self.assertEqual(thaiscript.reading("Blue box coffee"), "บลู บ็อกซ์ คอฟฟี่")
        self.assertEqual(thaiscript.reading("MOON CAFE"), "มูน คาเฟ่")
        self.assertEqual(thaiscript.reading("Café"), "คาเฟ่")
        self.assertEqual(thaiscript.reading("7-Eleven"), "เซเว่น อีเลฟเว่น")

    def test_thai_words_in_latin_run_together(self):
        self.assertEqual(thaiscript.reading("Baan Suan Lamyai"), "บ้านสวนลำไย")
        self.assertEqual(thaiscript.reading("Khum Khantoke"), "คุ้มขันโตก")

    def test_head_goes_first(self):
        self.assertTrue(thaiscript.reading("Maeonwittayalai School").startswith("โรงเรียน"))
        self.assertEqual(thaiscript.reading("Art Gate Hotel"), "โรงแรม อาร์ต เกต")

    def test_initials_and_numbers(self):
        self.assertEqual(thaiscript.reading("BT Engineering"), "บีที เอ็นจิเนียริ่ง")
        self.assertEqual(thaiscript.reading("Chez 15").split()[-1], "15")

    def test_parenthetical_dropped(self):
        self.assertEqual(thaiscript.reading("Nest Garden (closed)"), thaiscript.reading("Nest Garden"))

    def test_rule_words_are_counted(self):
        th, guessed = thaiscript.read("Zorblax Cafe")
        self.assertTrue(th.endswith("คาเฟ่"))
        self.assertEqual(guessed, 1)


class MapRows(unittest.TestCase):
    def row(self, name, en=""):
        return front_layer._nm({"name": name, "nameEn": en, "province": "cm", "slug": "x"})

    def test_latin_only_gets_thai(self):
        r = self.row("Blue box coffee")
        self.assertEqual(r[3], "บลู บ็อกซ์ คอฟฟี่")

    def test_thai_only_gets_latin(self):
        r = self.row("วัดพระสิงห์")
        self.assertEqual(len(r), 4)
        self.assertTrue(r[3].startswith("Wat "))

    def test_both_scripts_get_nothing(self):
        self.assertEqual(len(self.row("วัดพระสิงห์", "Wat Phra Singh")), 3)

    def test_mixed_name_reads_whole_in_latin(self):
        # the English map shows no Thai: a mixed name gives its Latin half, or is read through
        self.assertEqual(self.row("ACC Clinic Center เชียงใหม่")[3], "ACC Clinic Center")
        self.assertEqual(self.row("โคแล็ป Colab Cowork & Cafe")[3], "Colab Cowork & Cafe")
        self.assertEqual(self.row("บ้านสบายใจ coffee")[3], "Ban Sabaichai Coffee")

    def test_thai_road_reads_as_road(self):
        self.assertTrue(front_layer._reading("ถนนห้วยแก้ว").endswith(" Road"))


if __name__ == "__main__":
    unittest.main()
