#!/usr/bin/env python3
"""A stated view reaches the facts list as the statement it is.

Nan, 2026-09-23: "put the balcony view on the record" — Medileaves, the
old-city moat from a third-floor balcony. viewOf / viewFrom render as two
rows, in both tongues when written "ไทย / English"; nothing is inferred.

    python3 tests/test_view_stated.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


REC = {"id": "cm-weedth-4d28bd97", "province": "cm", "cat": ["cannabis", "sights"],
       "sub": ["dispensary", "viewpoint"], "name": "Medileaves", "attrs": {
           "viewOf": "คูเมืองเชียงใหม่ / the old city moat",
           "viewFrom": "ระเบียงชั้น 3 / the third-floor balcony"},
       "sources": [], "lat": 18.787, "lng": 98.993, "geoPrecision": "approx"}

html = "".join(build.known_facts(REC))
check("view of — both tongues", "คูเมืองเชียงใหม่" in html and "the old city moat" in html, html[:300])
check("seen from — both tongues", "ระเบียงชั้น 3" in html and "third-floor balcony" in html)
check("no bearing invented", "Faces" not in html)

bare = dict(REC, attrs={"viewOf": "the moat"})
html = "".join(build.known_facts(bare))
check("a one-tongue value still renders", "the moat" in html)

none = dict(REC, attrs={})
check("nothing stated, nothing shown", "View of" not in "".join(build.known_facts(none)))

print("FAILED: " + ", ".join(failures) if failures else "all ok")
sys.exit(1 if failures else 0)
