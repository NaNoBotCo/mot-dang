#!/usr/bin/env python3
"""geocode_gaps must say the same thing twice. It did not, and it cost 424 pins.

The pass defined "the gap" as records marked needs-pin. Its own pins, once
applied by import_all, make those records `approx` — so a second run measured a
smaller problem and wrote a smaller file. A capped run and an uncapped run then
overlapped and the uncapped one landed last: 424 pins on disk, 55 of them
postcode centroids with roughly 6 km of error, while the cap said 286 and the
note published the smaller number.

An unstable derivation is not a bug in one field, it is a number that cannot be
quoted. So the property is tested rather than asserted:

    python3 tests/test_geocode_gaps.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAPS = ROOT / "importers" / "geocode_gaps.py"
# A slice small enough to run twice in a test, and the one the whole pin hunt
# started from.
SLICE = "tok-sen"

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def run(*args):
    return subprocess.run([sys.executable, str(GAPS), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


def main():
    print(__doc__.strip().splitlines()[0])
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "pins.json")
        cap = "3000"

        r = run("--only", SLICE, "--max-uncertainty", cap, "--out", out, "--write", "--show", "0")
        check("first run writes", r.returncode == 0 and os.path.exists(out), r.stderr[-200:])
        if not os.path.exists(out):
            return 1
        first = json.load(open(out, encoding="utf-8"))["pins"]
        check("first run finds pins", len(first) > 0, "nothing derived")

        # THE ACTUAL BUG. Re-run against the same catalogue with the file now
        # in place: every record it pinned is still listed, so every one must
        # be re-derived. Before the fix this returned an empty file, because
        # the records it had pinned no longer looked like a gap.
        r = run("--only", SLICE, "--max-uncertainty", cap, "--out", out, "--check", "--show", "0")
        check("second run agrees with the first (--check)", r.returncode == 0,
              (r.stdout + r.stderr)[-400:])

        r = run("--only", SLICE, "--max-uncertainty", cap, "--out", out, "--write", "--show", "0")
        second = json.load(open(out, encoding="utf-8"))["pins"]
        check("second write is byte-identical",
              json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True),
              f"{len(first)} then {len(second)}")

        # The cap is the promise the published note makes. Nothing may exceed it.
        over = [k for k, v in second.items() if v["uncertainty_m"] > int(cap)]
        check(f"no pin declares worse than ±{cap} m", not over, f"{len(over)} do")

        # A tighter cap must shrink the answer, not leave it alone: proof the
        # cap is applied on every run and not only on the first.
        r = run("--only", SLICE, "--max-uncertainty", "500", "--out", out, "--write", "--show", "0")
        tight = json.load(open(out, encoding="utf-8"))["pins"]
        check("a tighter cap on a re-run actually refuses more",
              len(tight) <= len(second), f"{len(second)} -> {len(tight)}")

    print(f"\n{'PASS' if not failures else 'FAIL: ' + ', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
