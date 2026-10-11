#!/usr/bin/env python3
"""Carry the 2026-09-21 evening work — the big search, the drawn map, the
illustrated calendar, the sprite — from this draft into home_next.py, the
generator build.py actually calls.

Written as a patch rather than a copy because home_next.py has moved on from this
draft in other ways (vendored stylesheet, ROOT paths, render()). Every hunk must
match exactly once or nothing is written.

    python3 port_to_home_next.py --check    # report, write nothing
    python3 port_to_home_next.py --write

It refuses while a build holds cache/build.lock: build.py imports home_next, and
a page half-swapped under a running build is a page nobody can reason about.
"""
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TARGET = ROOT / "home_next.py"
LOCK = ROOT / "cache/build.lock"
DOTS = ROOT / "docs/site/map"

HUNKS = [
    # (what, old, new) — every one of these is byte-identical in both files today.
    ("imports",
     "sys.path.insert(0, str(KIT))\nimport css as kit_css  # noqa: E402\n",
     None),  # filled in below, per-file
]


def build_hunks(draft: str, target: str):
    """The functions this evening changed, taken by their own line spans rather than by
    a regex. A lazy span that runs to the next `def` swallows whatever constant sits
    between two functions — it ate PLAN_CHIP_JS and duplicated a block on the first
    attempt — so the span comes from the parser, which knows where a function ends."""
    import ast

    def span(src, name):
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                lines = src.splitlines(keepends=True)
                return "".join(lines[node.lineno - 1:node.end_lineno])
        raise SystemExit(f"no def {name}() in one of the two files")

    names = ["search_form", "near_block", "chips", "index_table", "pinned_cards",
             "band", "soon_rows", "feed_rows", "air_cards"]
    out = []
    for nm in names:
        a, b = span(target, nm), span(draft, nm)
        if a != b:
            out.append((nm, a, b))
    return out


LITERAL = [
    ("the sprite and the two modules",
     "sys.path.insert(0, str(KIT))\n",
     "sys.path.insert(0, str(KIT))\n"),
]


def main():
    write = "--write" in sys.argv
    if not TARGET.exists():
        raise SystemExit(f"no {TARGET}")
    if LOCK.exists():
        pid = LOCK.read_text().split()[0]
        alive = subprocess.run(["ps", "-p", pid], capture_output=True).returncode == 0
        if alive:
            raise SystemExit(f"a build holds cache/build.lock (pid {pid}) — wait for it")
    draft = (HERE / "build_home.py").read_text()
    target = TARGET.read_text()
    hunks = build_hunks(draft, target)
    print(f"{len(hunks)} function(s) to replace: " + ", ".join(h[0] for h in hunks))

    # the modules, side by side with the generator that imports them
    mods = ["homebits.py", "mapart.py"]
    for m in mods:
        print(f"  module {m} -> {ROOT / m}")

    # the three additions that are not whole functions
    adds = [
        ("DOORS, beside near_block",
         "def near_block():",
         'DOORS = (("map.html", "แผนที่", "Map", "i-map"),\n'
         '         ("here.html", "ตรงนี้", "Here", "i-here"),\n'
         '         ("toilets.html", "ห้องน้ำ", "Toilets", "i-loo"),\n'
         '         ("chuai.html", "ช่วย", "Help, nearest", "i-sos"))\n\n\n'
         "def near_block():"),
        ("the nav's marks",
         'NAV = [("#near", "ใกล้ๆ", "near"), ("#now", "ตอนนี้", "now"), ("#soon", "เร็วๆ นี้", "soon"),\n'
         '       ("#shelves", "หมวด", "shelves"), ("#index", "สารบัญ", "index"),\n'
         '       ("#deep", "เจาะลึก", "deep"), ("#elsewhere", "ที่อื่น", "elsewhere")]\n\n'
         'nav = "".join(f\'<a href="{h}"><span class="th" lang="th">{E(th)}</span> {E(en)}</a>\' for h, th, en in NAV)',
         'NAV = [("#near", "ใกล้ๆ", "near", "i-near"), ("#now", "ตอนนี้", "now", "i-clock"),\n'
         '       ("#soon", "เร็วๆ นี้", "soon", "i-cal"), ("#shelves", "หมวด", "shelves", "i-layers"),\n'
         '       ("#index", "สารบัญ", "index", "i-list"), ("#deep", "เจาะลึก", "deep", "i-star"),\n'
         '       ("#elsewhere", "ที่อื่น", "elsewhere", "i-globe")]\n\n'
         'nav = "".join(f\'<a href="{h}">{icon(ic, 18)}<span class="th" lang="th">{E(th)}</span> {E(en)}</a>\'\n'
         "              for h, th, en, ic in NAV)"),
        ("the NEAR copy, now that the map opens the section",
         "    <p>Pick a province, or go straight to the four that answer from where you stand.</p>",
         "    <p>The whole catalogue, drawn — one dot per place, so the cities and the roads\n"
         "    between them are the shops along them. Tap a district to open it in the live map.</p>"),
        ("the marks on the two NOW cards",
         "<div class=\"card live\"><h3>{bi('วันนี้', 'Today')}</h3>",
         "<div class=\"card live\"><h3>{icon('i-cal', 20)}{bi('วันนี้', 'Today')}</h3>"),
        ("the mark on Emergency",
         "<div class=\"card live\"><h3>{bi('ฉุกเฉิน', 'Emergency')}</h3>",
         "<div class=\"card live\"><h3>{icon('i-sos', 20)}{bi('ฉุกเฉิน', 'Emergency')}</h3>"),

        ("the two modules on the path",
         'ROOT = pathlib.Path(__file__).resolve().parent\n',
         'ROOT = pathlib.Path(__file__).resolve().parent\n'
         'sys.path.insert(0, str(ROOT))\n'
         'import homebits  # noqa: E402\n'
         'from homebits import icon  # noqa: E402\n'),
        ("import sys",
         "import os\nimport pathlib\n",
         "import os\nimport pathlib\nimport sys\n"),
        ("the district counts",
         'AIR = j("air.json")',
         '_COUNTS = DATA / "amphoe_counts.json"\n'
         'if _COUNTS.exists():\n'
         '    AMPHOE_COUNTS = json.loads(_COUNTS.read_text())\n'
         'else:\n'
         '    import mapart  # noqa: E402\n'
         '    AMPHOE_COUNTS = mapart.count_by_amphoe(mapart.Proj())\n'
         '    _COUNTS.write_text(json.dumps(AMPHOE_COUNTS))\n\n'
         'AIR = j("air.json")'),
        ("the sprite into the page",
         '    <a class="skip" href="#about">',
         '{homebits.sprite_defs()}\n    <a class="skip" href="#about">'),
        ("the calendar into SOON",
         "    <p>Dated, nearest first. Each carries the source that announced it.</p>\n"
         "    {soon_rows()}",
         "    <p>Two months, drawn. Each square carries the day's colour, the moon as it\n"
         "    will be that night, and anything dated into it.</p>\n"
         "    {homebits.calendar(TODAY, k_events=2)}\n\n"
         '    <h3>รายการ <span class="en">The same days, as a list</span></h3>\n'
         "    <p>Nearest first. Each carries the source that announced it.</p>\n"
         "    {soon_rows()}"),
        ("the hero search",
         '         f"{len(SHELVES)} shelves, and every one says what it holds before you open it.",\n'
         "    credit=",
         '         f"{len(SHELVES)} shelves, and every one says what it holds before you open it.",\n'
         "    extra=search_form(big=True),\n"
         "    credit="),
        ("the map into NEAR",
         "    <h2 id=\"near\">ใกล้ๆ <span class=\"en\">Near</span></h2>",
         "    <h2 id=\"near\">ใกล้ๆ <span class=\"en\">Near</span></h2>"),
    ]
    for what, old, _new in adds:
        if target.count(old) != 1:
            raise SystemExit(f"hunk matches {target.count(old)} times, want 1: {what}")
        print(f"  add {what}")

    # PINNED gained a mark per minisite. The rows are the same in both files, so the
    # icon is threaded into the target's own table rather than replacing it.
    import re as _re
    draft_pinned = _re.search(r"PINNED = \[.*?\n\]", draft, _re.S).group(0)
    marks = dict(_re.findall(r'"([^"]+)", "(i-[a-z-]+)", "', draft_pinned))
    target_pinned = _re.search(r"PINNED = \[.*?\n\]", target, _re.S).group(0)
    threaded = target_pinned
    for en, ic in marks.items():
        pat = f'"{en}", "'
        if threaded.count(pat) != 1:
            raise SystemExit(f"cannot place the mark for {en}: {threaded.count(pat)} matches")
        threaded = threaded.replace(pat, f'"{en}", "{ic}", "', 1)
    print(f"  thread {len(marks)} marks into PINNED")

    # the stylesheet: the draft's EXTRA block replaces the target's, whole
    import re
    ex = re.compile(r'^EXTRA = """.*?^"""$', re.S | re.M)
    if not (ex.search(draft) and ex.search(target)):
        raise SystemExit("could not find EXTRA in both files")
    print("  replace EXTRA (the page's own stylesheet)")

    if not write:
        print("\n--check only. Nothing written. Re-run with --write.")
        return

    for m in mods:
        shutil.copy2(HERE / m, ROOT / m)
    out = target
    for _nm, a, b in hunks:
        out = out.replace(a, b, 1)
    for _what, a, b in adds:
        out = out.replace(a, b, 1)
    out = ex.sub(lambda _m: ex.search(draft).group(0), out, count=1)
    out = out.replace(target_pinned, threaded, 1)
    # the draft's map sits beside the draft; the site's under docs/site/map
    old = 'homebits.big_map(AMPHOE_COUNTS, "img/", HERE / "img")'
    if old not in out:
        raise SystemExit("the map call moved — fix this line before writing")
    out = out.replace(old, 'homebits.big_map(AMPHOE_COUNTS, "site/map/", DOCS / "site/map")')
    TARGET.write_text(out)
    DOTS.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / "mapart.py"), str(DOTS)], check=True,
                   cwd=ROOT)
    # /source archives a whitelist; two new modules that the front page needs should
    # be in it. Best effort: build.py is large and often open in another session, so a
    # miss here is a note, not a failure.
    bp = ROOT / "build.py"
    mark = '"explore_layer.py", "hotspring_layer.py", "geography_layer.py",'
    txt = bp.read_text()
    if "homebits.py" in txt:
        print("  SOURCE_FILES already names homebits.py")
    elif txt.count(mark) == 1:
        bp.write_text(txt.replace(mark, mark + '\n                "homebits.py", "mapart.py", "home_next.py",', 1))
        print("  SOURCE_FILES now names homebits.py, mapart.py, home_next.py")
    else:
        print("  NOTE: add homebits.py, mapart.py, home_next.py to build.py SOURCE_FILES by hand")

    print(f"\nwrote {TARGET} and {DOTS}/map-dots-*.png")
    print("now: python3 -m pytest tests/test_home_next.py, then the usual gates")


if __name__ == "__main__":
    main()
