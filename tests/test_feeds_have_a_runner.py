#!/usr/bin/env python3
"""Every watched feed names what refreshes it, and a walk calls the healer.

Run as a script: python3 tests/test_feeds_have_a_runner.py

Why (2026-09-25): ping.json had no caller from 2026-09-04, and the money,
cinema, lottery and event feeds depended on a morning walk that stood down
every day for two weeks. watch_data.py saw all of it and could only say so.
It now heals (--heal), which works only for a file that names its fetcher.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import watch_data  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  — %s" % (detail,)))


def main():
    watched = [c[0] for c in watch_data.CHECKS]
    unnamed = [f for f in watched if f not in watch_data.FETCHERS]
    check("every watched file names its fetcher", not unnamed, unnamed)
    missing = [a[0] for a, _ in watch_data.FETCHERS.values() if not (ROOT / a[0]).exists()]
    check("every named fetcher exists", not missing, missing)
    stray = [f for f in watch_data.FETCHERS if f not in watched]
    check("no fetcher is named for a file nobody watches", not stray, stray)

    walk = (ROOT / "importers" / "standing_walk.sh").read_text()
    live = [ln for ln in walk.splitlines() if not ln.lstrip().startswith("#")]
    check("the standing walk runs watch_data.py --heal",
          any(re.search(r"watch_data\.py\s+--heal", ln) for ln in live))

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
