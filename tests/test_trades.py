"""WO-76 — /trades.html, the trade vocabulary as an index.

What is checked here is the MECHANICS, not the coverage. The lexicon is at
1,782 of 1,782 glossed today; a test that demanded that would fail the first
time a crawl found a word nobody had read yet, and would then be an argument
for not crawling. So coverage is printed, and the things that can silently
break are asserted:

  · Thai dictionary order — the bug this page was written to avoid is filing
    เปลี่ยนยาง, แก้ทรง and ไวนิล in a heap after ฮ, which is where codepoint
    order puts every word beginning with a leading vowel.
  · every row is a link, and the link carries the term itself
  · a reading is never just the Thai repeated back
  · the letter rail and the blocks agree, and no letter is drawn empty

Run: python3 -m unittest tests.test_trades -v
"""

import json
import re
import sys
import unittest
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import trades_layer as T  # noqa: E402

LEX = json.loads((ROOT / "data" / "trade_lexicon.json").read_text())["tags"]
THAI_RE = re.compile(r"[\u0e00-\u0e7f]")


def _esc(s):
    return escape(str(s), quote=False)


def _att(s):
    return escape(str(s), quote=True)


def _bi(th, en, sep=" · ", raw=False):
    th, en = (th or "").strip(), (en or "").strip()
    if not en or en == th:
        return f'<span class="th" lang="th">{_esc(th)}</span>'
    return (f'<span class="bi"><span class="th" lang="th">{_esc(th)}</span>'
            f'<span class="en" lang="en">{_esc(sep)}{_esc(en)}</span></span>')


class ThaiOrder(unittest.TestCase):
    def test_leading_vowel_files_under_its_consonant(self):
        """เปลี่ยนยาง is looked up under ป, not after ฮ."""
        for term, letter in (("เปลี่ยนยาง", "ป"), ("แก้ทรง", "ก"), ("ไวนิล", "ว"),
                             ("โคมลอย", "ค"), ("ใบเสร็จ", "บ"),
                             ("ซ่อมมอเตอร์ไซค์", "ซ")):
            self.assertEqual(T.initial(term), letter, term)

    def test_tone_marks_do_not_split_a_letter(self):
        """ซ่อม and ซอม sort together; a mai ek is not a letter."""
        self.assertEqual(T.thai_key("ซ่อม"), T.thai_key("ซอม"))

    def test_latin_terms_go_to_their_own_block(self):
        for term in ("CNC", "Invisalign", "coworkingspace", "50"):
            self.assertEqual(T.initial(term), "")

    def test_every_term_lands_in_exactly_one_block(self):
        groups = T.rows(LEX)
        seen = [t for _, items in groups for t, _ in items]
        self.assertEqual(len(seen), len(LEX))
        self.assertEqual(len(set(seen)), len(LEX))

    def test_no_block_is_empty_and_letters_are_in_alphabet_order(self):
        groups = T.rows(LEX)
        self.assertTrue(all(items for _, items in groups))
        letters = [c for c, _ in groups if c != "#"]
        order = [T.THAI_ALPHABET.index(c) for c in letters]
        self.assertEqual(order, sorted(order))
        if "#" in [c for c, _ in groups]:
            self.assertEqual(groups[-1][0], "#", "the Latin block goes last")


class Rows(unittest.TestCase):
    def setUp(self):
        self.html = T.body(LEX, _bi, _esc, _att)

    def test_every_term_is_a_link_to_its_own_search(self):
        hrefs = set(re.findall(r'href="search\.html\?tag=([^"]+)"', self.html))
        missing = [t for t in LEX if _esc(t) not in hrefs]
        self.assertEqual(missing, [], f"{len(missing)} terms with no link")

    def test_row_count_matches_the_lexicon(self):
        self.assertEqual(self.html.count("<li>"), len(LEX))

    def test_the_rail_names_every_block(self):
        groups = T.rows(LEX)
        self.assertEqual(len(re.findall(r'href="#t-\d+"', self.html)), len(groups))
        self.assertEqual(len(re.findall(r'<h2 id="t-\d+"', self.html)), len(groups))

    def test_a_thai_terms_reading_is_never_the_thai_repeated(self):
        """A reading has to say something the Thai does not already say.

        Latin-written terms (Clean, daikin, X-RAY, cnc — 36 of them) come out
        of the generator reading as themselves, which is correct: that IS how
        the sign is said. _row() drops the column for those rather than
        printing the word twice; this checks the Thai side, where a reading
        equal to the term would mean the letter rules gave up."""
        for term, e in LEX.items():
            if not THAI_RE.search(term):
                continue
            r = (e.get("reading") or "").strip()
            if r:
                self.assertNotEqual(r.lower(), term.strip().lower(), term)

    def test_a_redundant_reading_is_never_drawn(self):
        """Clean · Clean — the same word twice — reaches no reader."""
        self.assertNotIn("<b lang=\"th\">Clean</b> <i>Clean</i>", self.html)
        for m in re.finditer(r'<b lang="th">([^<]+)</b> <i>([^<]+)</i>', self.html):
            self.assertNotEqual(m.group(1).lower(), m.group(2).lower(), m.group(0))

    def test_no_row_carries_a_suspect_reading(self):
        """A reading the rules could not finish is worse than none: it prints a
        word with a syllable missing. The generator marks those `suspect` and
        they are meant to be fixed in the curated overrides, not shipped."""
        bad = [t for t, e in LEX.items() if e.get("suspect")]
        self.assertEqual(bad, [], f"{len(bad)} suspect readings would print")


class Coverage(unittest.TestCase):
    """Reported, not enforced — see the module docstring."""

    def test_report(self):
        n = len(LEX)
        gloss = sum(1 for e in LEX.values() if (e.get("gloss") or "").strip())
        read = sum(1 for e in LEX.values() if (e.get("reading") or "").strip())
        print(f"\n  trade terms {n:,} · glossed {gloss:,} ({gloss * 100 // n}%)"
              f" · readings {read:,} ({read * 100 // n}%)")
        self.assertGreater(n, 0)


if __name__ == "__main__":
    unittest.main()
