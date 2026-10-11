#!/usr/bin/env python3
"""Wire bearings_layer into build.py — four small insertions, by anchor text,
idempotent, and refused while a build holds the lock. WO-64.

    python3 importers/apply_bearings_hook.py --check   # say what would change
    python3 importers/apply_bearings_hook.py           # apply

WHY A SCRIPT AND NOT A PATCH. build.py is edited by several sessions a day
(its mtime was two minutes old when this layer was written), so a line-number
diff would rot before anyone applied it. Each insertion finds its anchor by
text and refuses if the anchor is missing or the hook is already there.

The four hooks:
  1. detail_page(): a "ทิศทาง · Bearings" row after the Map row — below the
     contacts and hours, exactly where Nan put it ("not ABOVE the most
     important information, but available").
  2. place_json(): `bearings` on the machine twin, so /api/v1 and the
     assistant can say "5 km due east of Tha Phae Gate" too.
  3. build(): bearings_layer.emit() beside moat_layer.emit() — /landmarks.html
     and docs/data/landmarks.json.
  4. the source tarball's module list, so the layer ships with the source.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build.py"
LOCK = ROOT / "cache" / "build.lock"

HOOKS = [
    # (name, anchor regex (must match exactly once), insertion AFTER the anchor, presence marker)
    ("detail_page bearings row",
     r'''(    else:\n        rows\.append\(f'<dt>\{bi\("แผนที่", "Map"\)\}</dt><dd><span class="badge pin">'\n(?:.*\n){0,6}?.*\+ bi\("ยังไม่มีพิกัด", "no pin yet"\) \+ "</span></dd>"\)\n)''',
     '''    # WO-64 — ทิศทาง. Where this stands in relation to the things people
    # steer by: the moat and its quarter, the nearest gate, what it is at or
    # across from, how far and which way from Tha Phae Gate. Below the
    # contacts on purpose (Nan: "not ABOVE the most important information,
    # but available"). Silent when the pin cannot support a single line.
    import bearings_layer as _bearings_layer
    _brow = _bearings_layer.row_html(
        r, bi, esc,
        href=lambda _lm, _from: (f"{place_slug(_lm)}.html" if _lm.get("province") == _from
                                 else f"../../{_lm['province']}/p/{place_slug(_lm)}.html"))
    if _brow:
        rows.append(_brow)
''',
     "_bearings_layer.row_html("),
    ("place_json bearings",
     r'''(    rec\["license"\] = LICENSE_LINE_EN\n)(    return rec\n)''',
     None,  # handled specially: insert BETWEEN the two groups
     'rec["bearings"]'),
    ("build() emit",
     r'''(    import moat_layer\n    print\("  moat:", moat_layer\.emit\(globals\(\), data\)\)\n)''',
     '''    import bearings_layer
    print("  bearings:", bearings_layer.emit(globals(), data))
''',
     "bearings_layer.emit(globals(), data)"),
    ("source tarball list",
     r'''("moat_layer\.py", "seven_layer\.py", "hom_layer\.py")''',
     None,  # handled specially: append inside the list
     '"bearings_layer.py"'),
]


def main():
    check = "--check" in sys.argv
    src = BUILD.read_text()
    if LOCK.exists() and not check:
        pid = (LOCK.read_text().split() or ["0"])[0]
        try:
            os.kill(int(pid), 0)
            alive = True
        except (OSError, ValueError):
            alive = False
        if alive:
            sys.exit(f"refused: a build (pid {pid}) holds {LOCK} — run again when it ends")
    out = src
    changed = []
    for name, anchor, insertion, marker in HOOKS:
        if marker in out:
            print(f"  present  {name}")
            continue
        ms = list(re.finditer(anchor, out))
        if len(ms) != 1:
            sys.exit(f"refused: anchor for {name!r} matched {len(ms)} times — build.py has moved; edit by hand")
        m = ms[0]
        if name == "place_json bearings":
            new = (m.group(1)
                   + '    rec["bearings"] = __import__("bearings_layer").for_json(r)   # WO-64\n'
                   + m.group(2))
        elif name == "source tarball list":
            new = m.group(1) + ', "bearings_layer.py"'
        else:
            new = m.group(1) + insertion
        out = out[:m.start()] + new + out[m.end():]
        changed.append(name)
        print(f"  {'would add' if check else 'added   '} {name}")
    if check or not changed:
        print("nothing written" if (check or not changed) else "")
        return
    BUILD.write_text(out)
    print(f"build.py updated: {', '.join(changed)}")
    print("next: python3 tests/test_bearings.py && python3 tests/test_build_lock.py; then a scratch build")


if __name__ == "__main__":
    main()
