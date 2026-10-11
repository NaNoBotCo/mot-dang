#!/usr/bin/env python3
"""The front page (home_next.py), built and read back.

The rules this holds, because they are Nan's and a later session will not know:
  · the stack is NEAR, then NOW, then SOON, in that order (2026-09-21)
  · nothing sits above the stack unless SHE calls out a festival — CALLOUT is None —
    except the one-line rain and festival-eve notices (2026-09-26)
  · the day's colour, the tiles by the hour, SOON against the clock (2026-09-26)
  · ONE search box, in the hero — not in the bar as well (2026-09-22: "remove
    search bar from top, search already appears directly below in body")
  · SOON is the next seven days; the months live on /calendar.html (2026-09-22)
  · nothing offers to translate the page: it is already bilingual (2026-09-22)
  · every number on the page is read from the file that owns it, never typed

    python3 tests/test_home_next.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import home_next  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAIL.append(name)


PAGE = home_next.render()
TEXT = re.sub(r"<[^>]+>", " ", PAGE)
# what a reader actually reads: no stylesheet, no script, no tags
PROSE = re.sub(r"<[^>]+>", " ",
               re.sub(r"<(style|script)\b.*?</\1>", " ", PAGE, flags=re.S)).lower()


def at(needle):
    i = PAGE.find(needle)
    return i if i >= 0 else 10 ** 9


# ---- the stack
near, now, soon = at('id="near"'), at('id="now"'), at('id="soon"')
check("near comes first", near < now < soon, f"near={near} now={now} soon={soon}")
check("all three sections are on the page", soon < 10 ** 9)
check("the shelves come after the stack", soon < at('id="shelves"'))

# ---- the callout is hers, and off by default
check("CALLOUT defaults to None", home_next.CALLOUT is None)
check("no band above the stack", PAGE.find('class="band', 0, near) == PAGE.find('class="band '), )
check("a callout would land above near",
      'callout_band' in (ROOT / "home_next.py").read_text())

# ---- the search: once, in the hero, and NOT in the bar as well (NaN, 2026-09-22)
head = PAGE[:at("</header>")]
check("no search box in the bar", "<form" not in head)
check("the search form is on the page once", PAGE.count('<form class="q') == 1)
check("it is the hero's", at('<form class="q big') < at('id="about"'))
check("the box is named q", 'name="q"' in PAGE)
check("Lucky is there", 'name="lucky"' in PAGE)
check("boolean has a door", 'find?adv=1' in PAGE)

# ---- nothing offers to translate a page that is already in two languages
check("the html element declines translation", 'translate="no"' in PAGE)
check("and Google is told in the words it reads",
      '<meta name="google" content="notranslate">' in PAGE)

# ---- SOON is seven days, and the longer view is one click away
check("seven days, no more", len(re.findall(r'<li class="ag[ "]', PAGE)) == 7,
      str(len(re.findall(r'<li class="ag[ "]', PAGE))))
check("no month grid on the front page", '<div class="cal">' not in PAGE)
check("the whole calendar is one click away", 'href="https://motdang.net/calendar.html"' in PAGE)

CAL = home_next.calendar_page()
check("the calendar page renders", len(CAL) > 20_000, str(len(CAL)))
check("it draws the months", '<div class="cal">' in CAL)
check("and lists them for a phone", 'class="agenda"' in CAL)
check("its bar reaches the front page", 'href="https://motdang.net/#near"' in CAL)
check("it declines translation too", 'content="notranslate"' in CAL)
for name in sorted(set(re.findall(r'<use href="#([a-z0-9-]+)"', CAL))):
    check(f"{name} is in the calendar page's sprite",
          f'id="{name}"' in CAL[:CAL.find("</defs>")])

# ---- the page makes no claim about where its photographs come from
# (NaN, 2026-09-22: "a hint of a promise forming, to only use commons images…
# I don't plan to do that and don't want to talk about it").
# The agenda's rows are other people's event titles ("Chiang Mai Photographers
# – Convenience Stores", 2026-09-25), not the page speaking, so they are left out.
def _without_agenda(h):
    """The agenda holds lists inside lists, so cut it at its own closing tag."""
    start = h.find('<ul class="agenda">')
    if start < 0:
        return h
    depth, i = 0, start
    for m in re.finditer(r"<(/?)ul\b", h[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            i = start + m.end()
            break
    return h[:start] + " " + _without_agenda(h[h.find(">", i) + 1:])


_OWN = re.sub(r"<(script|style)\b.*?</\1>", " ", PAGE, flags=re.S)
_OWN = re.sub(r"<[^>]+>", " ", _without_agenda(_OWN)).lower()
for word in ("commons", "photograph", "each credited"):
    check(f"the front page does not talk about {word}", word not in _OWN)

# ---- the numbers are read, not typed
P = home_next.P
allrec = P["totals"]["cm"] + P["totals"]["cr"]
check("the record count is the canonical count", f"{allrec:,}" in TEXT, f"{allrec:,}")
shelves = [s for s in P["shelves"] if s.get("cm", 0) + s.get("cr", 0) > 0]
check("every live shelf has a chip", all(f'href="https://motdang.net/cm/{s["key"]}/"' in PAGE
                                         for s in shelves))
check("an empty shelf is not printed",
      all(s["key"] not in PAGE for s in P["shelves"] if not s.get("cm", 0) + s.get("cr", 0)))
check("the link-rot figure is the swept figure", f'{P["linkhealth"]["ok"]:,}' in TEXT)
check("the searchable-pages figure is the crawl's",
      not home_next.FIND or f'{home_next.FIND["pages"]:,}' in TEXT)

# ---- the furniture a front page owes
check("canonical", '<link rel="canonical" href="https://motdang.net/">' in PAGE)
check("the publish guard's marker", 'id="md-home"' in PAGE)
check("the marker is JSON", isinstance(json.loads(
    re.search(r'id="md-home">(.*?)</script>', PAGE, re.S).group(1)), dict))
check("og:image is one of her frames", 'og:image" content="https://motdang.net/site/hero/' in PAGE)
check("a skip link", 'class="skip"' in PAGE or "Skip to content" in PAGE)

# ---- no sideways scroll on a phone. Measured 2026-09-21 inside a 390 px iframe
# (Chrome clamps a real window to 500 px on this Mac): scrollWidth equalled the
# viewport at 320, 360 and 390. Two grids had hard minimums of 20rem and 18rem and
# pushed a 320 px phone 58 px sideways; both take min(…,100%) now, and this holds it.
for rule in ("ul.links", ".grid.two", ".grid{"):
    i = home_next.EXTRA.find(rule)
    seg = home_next.EXTRA[i:i + 400]
    track = re.search(r"grid-template-columns:repeat\((?:auto-fill|auto-fit),minmax\(([^,]+),", seg)
    check(f"{rule} can shrink to the screen", bool(track) and track.group(1).startswith("min("),
          track.group(1) if track else "no track found")

# ---- the geofence (grafted 2026-09-21 evening). The edge fills the meta; the page
# reads it, and asks the reader's browser for nothing until the reader asks.
check("the meta the edge fills is there, and empty",
      '<meta name="md-where" content="">' in PAGE)
geo = json.loads(re.search(r'id="md-geo">(.*?)</script>', PAGE, re.S).group(1))
check("the payload carries her frames", len(geo["pics"]) > 20, str(len(geo.get("pics", []))))
check("every frame carries a coordinate",
      all(f.get("la") is not None for f in geo["pics"]))
check("every frame is in the build",
      all((ROOT / "docs" / f["j"]).exists() for f in geo["pics"]),
      "run importers/make_hero.py")
check("the two city centres are there", {c["k"] for c in geo["cities"]} == {"cm", "cr"})
check("the map's projection is published",
      all(k in geo["proj"] for k in ("w", "s", "e", "n", "kx", "scale", "pad")))
check("the drawn map is in the build",
      all((ROOT / "docs/site/map" / f"map-dots-{k}.png").exists() for k in ("light", "dark")),
      "homebits.dots() writes them when the page renders")
check("the reader's ring is on the map", 'id="me"' in PAGE)
check("nothing is fetched until the reader asks",
      "data/here/" in PAGE and PAGE.count("fetch(") == 1)
check("no third-party host in the page's own scripts",
      not re.search(r'(?:fetch|src)\(?["\']https?://(?!motdang\.net)', PAGE))

# ---- the bar gets out of the way (Nan, 2026-09-21: "menu bar and top bits should
# collapse/disappear on scroll, elegantly")
check("the bar folds before it leaves", "nav-tight" in home_next.EXTRA)
check("the bar leaves at every width, not only on a phone",
      "body.nav-away header.top{transform" in home_next.EXTRA)
check("a focus inside the bar brings it back", "focusin" in PAGE)
check("the fold is off for a reader who asked for less motion",
      "prefers-reduced-motion" in home_next.EXTRA)

# ---- the reader's own clock (NaN, 2026-09-26, "I love all of these")
magic = json.loads(re.search(r'id="md-magic">(.*?)</script>', PAGE, re.S).group(1))
check("seven day colours and Rahu's", set(magic["colours"]) == {*map(str, range(7)), "rahu"})
check("the notice slot sits between the hero and near",
      at('id="magic"') < near and PAGE.find('id="magic" hidden') > 0)
check("every need tile can be reordered", PAGE.count('class="need" data-k=') == len(home_next.NEEDS))
check("the hour bands name only real tiles",
      all(k in {n[0] for n in home_next.NEEDS} for *_, ks in home_next.NEED_HOURS for k in ks))
check("the hour bands cover the clock",
      sorted((a, b) for a, b, _ in home_next.NEED_HOURS)[0][0] == 5
      and all(x[1] == y[0] for x, y in zip(sorted(home_next.NEED_HOURS),
                                           sorted(home_next.NEED_HOURS)[1:]))
      and max(b for _, b, _ in home_next.NEED_HOURS) == 29)
check("a timed event carries its clock", 'data-s="' in PAGE)
check("each agenda day carries its date", PAGE.count(' data-d="') == 7)
check("festival and full-moon notices come from the dated files",
      all(e["href"].startswith(("https://motdang.net/festivals/", "https://motdang.net/full-moon/"))
          for e in magic["eves"]))
# The six are the register's now (sites_layer.best, Nan 2026-09-28: newest, most read,
# her picks); the full moon stays one tap away through /sites/.
import sites_layer  # noqa: E402
check("the full moon is on the front page or one tap away",
      'href="https://motdang.net/full-moon/"' in PAGE
      or ('href="https://motdang.net/sites/"' in PAGE
          and any(c["href"] == "full-moon/" for c in sites_layer.cards())))
check("the agenda links a published full moon to its page",
      not any(d in PAGE for d in ("2026-10-26",)) or "full-moon/2026-10-26/" in PAGE)
check("the rain line reads a baked forecast", all(len(h) == 3 for v in magic["wx"].values() for h in v))
check("no emoji in the plan chip", "\U0001f5fa" not in PAGE and "🗺" not in PAGE)
check("one emergency number to a line", PAGE.count('<span class="sub"><a href="tel:') == 3)

# ---- the language switch (2026-09-28: the bar's TH+EN was a link to "#")
_head = PAGE[:PAGE.find("</head>")]
check("the stored language is applied in <head>", "md-lang" in _head and 'class="notranslate lang-both"' in PAGE)
# Beer, 2026-10-02: two states, ไทย and EN; no TH+EN.
check("the switch has two buttons, no TH+EN",
      all(f'data-lang="{v}"' in PAGE for v in ("th", "en")) and 'data-lang="both"' not in PAGE
      and 'langsw"><a href="#"' not in PAGE)
check("a bare Thai · English label is split into its two halves",
      '<span class="th" lang="th">ค้นหา</span><span class="en" lang="en">Search</span>' in PAGE)
check("a label that does not split cleanly is left whole",
      home_next.homebits._pair("PM2.5 · ดีมาก · Very good") == "PM2.5 · ดีมาก · Very good")

# ---- the pictures are hers and present in the build
for m in set(re.findall(r"url\((site/hero/[a-z0-9-]+\.jpg)\)", PAGE)):
    f = ROOT / "docs" / m
    check(f"{m} is in the build", f.exists(), "not in docs/ — make_hero.py has not run")

print()
print(f"{len(FAIL)} failed" if FAIL else "all green")
sys.exit(1 if FAIL else 0)
