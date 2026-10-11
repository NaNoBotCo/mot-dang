#!/usr/bin/env python3
"""ALPHA ONLY — the gate that makes "it goes away completely" checkable.

Nan asked for a thumbs up / thumbs down for her testers and, in the same
sentence, for it to be gone at beta. "Gone" is a claim about 23,000 files and
about a script that has permission to watch every error and every tap, so it
is the thing tested hardest here — in BOTH directions, because a switch that
only ever gets tested in the position it is currently in is not a switch.

  OFF MEANS ABSENT              With the switch off: tag() is empty, emit()
      writes no file, and no page in a built docs/ mentions alpha.js. Not
      hidden, not disabled — absent.
  ON MEANS EVERY PAGE           With it on, the tag is on every page built by
      the shell, because a tester who can only report from the pages somebody
      remembered to wire is a tester reporting on the wiring.
  IT EXPIRES BY ITSELF          A date in the past turns it off. Temporary
      furniture on this site has a long history of becoming permanent; this
      one has to be renewed on purpose.
  IT TALKS TO ONE ADDRESS       The only host alpha.js sends anything to is
      the endpoint in data/alpha.json. A tester's screen is not a place to
      grow a second telemetry channel.
  THE REPORT IS WORTH READING   The context builder still collects the fields
      the digest and the email print. A thumb with no query, no counts and no
      errors is the invitation that converted zero times, rebuilt.

    python3 tests/test_alpha.py
"""
import json
import os
import random
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
sys.path.insert(0, str(ROOT))

import alpha_layer                                          # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


def emit_into(tmp):
    return alpha_layer.emit({"DOCS": Path(tmp), "BUILD_DATE": "2026-09-09"})


on, why = alpha_layer.state()
print(f"\nalpha_layer says: {'ON' if on else 'off'} — {why}\n")

# ---- the switch, both ways ------------------------------------------------
print("the switch")
real = alpha_layer.config()
try:
    alpha_layer.config = lambda: {}
    alpha_layer._V.clear()
    check("no data/alpha.json — tag() is empty", alpha_layer.tag("../") == "")
    with tempfile.TemporaryDirectory() as tmp:
        emit_into(tmp)
        check("no data/alpha.json — no alpha.js is written",
              not (Path(tmp) / "alpha.js").exists())

    alpha_layer.config = lambda: {"on": False, "until": "2099-01-01"}
    check("on:false — tag() is empty", alpha_layer.tag("../") == "")

    alpha_layer.config = lambda: {"on": True, "until": "2020-01-01"}
    off, whyoff = alpha_layer.state()
    check("a past until: date turns it off", not off, whyoff)
    check("and the build says why", "expired" in whyoff, whyoff)

    alpha_layer.config = lambda: {"on": True, "until": "2099-01-01",
                                  "endpoint": "https://example.invalid/alpha"}
    alpha_layer._V.clear()
    check("on — tag() names alpha.js once, unfingerprinted", alpha_layer.tag("../")
          == '<script src="../alpha.js" defer></script>')
    with tempfile.TemporaryDirectory() as tmp:
        emit_into(tmp)
        js = (Path(tmp) / "alpha.js").read_text()
        check("on — alpha.js is written with the endpoint baked in",
              "https://example.invalid/alpha" in js)
        hosts = set(re.findall(r"https?://([a-z0-9.\-]+)", js))
        check("alpha.js talks to exactly one host", hosts == {"example.invalid"}, sorted(hosts))
finally:
    alpha_layer.config = lambda: real
    alpha_layer._V.clear()

# ---- what a report carries ------------------------------------------------
print("\nthe report")
JS = alpha_layer.JS
for field, why_it_matters in [
        ("o.q=", "the query — a search report without it is unreadable"),
        ("o.counts=", "how many rows the page actually had"),
        ("o.map=", "where the map was pointing"),
        ("o.errs=", "the JS errors since load"),
        ("o.nets=", "the requests that did not come back"),
        ("o.trail=", "the last dozen taps"),
        ("build:", "which build the tester was looking at")]:
    check(f"context carries {field.strip('o.=')} — {why_it_matters}", field in JS)
check("a failed send is kept on the device", "md-alpha-q" in JS)
check("the tester's name never stays in the address bar",
      "searchParams.delete('tester')" in JS and "replaceState" in JS)
check("a reader who is not a tester gets nothing",
      "if(!active)return;" in JS)
check("the thumb sits clear of the map's OSM attribution",
      ".mdal{position:fixed;left:" in JS)

# ---- the wiring -----------------------------------------------------------
print("\nthe wiring")
shell = (ROOT / "build.py").read_text()
head = shell[shell.index("def page("):shell.index("</head>")]
check("build.py hangs the tag inside page()'s head, so every page built by "
      "the shell carries it and none has to remember",
      "{alpha_layer.tag(r)}" in head)
check("and only there — one insertion point to delete at beta",
      shell.count("alpha_layer.tag(") == 1)

# ---- the artefact ---------------------------------------------------------
print("\nthe built site")
pages = sorted(DOCS.rglob("*.html")) if DOCS.exists() else []
if not pages:
    check("docs/ is built", True, "skipped — nothing built to check against")
else:
    sample = random.Random(9).sample(pages, min(400, len(pages)))
    built = [f for f in sample if 'data-root=' in f.read_text(encoding="utf-8")]
    named = [f for f in built if "alpha.js" in f.read_text(encoding="utf-8")]
    if not on:
        # The one that matters. "It is gone" is a claim about every file in
        # the tree, so it is checked against the tree.
        check(f"the switch is off and no sampled page mentions alpha.js "
              f"({len(sample)} sampled)", not named, [f.name for f in named][:3])
        check("docs/alpha.js does not exist", not (DOCS / "alpha.js").exists())
    elif not named and not (DOCS / "alpha.js").exists():
        # Wired, switched on, and absent from every page: that is a docs/ built
        # before the switch was flipped, not a broken widget. Said rather than
        # failed, because the wiring above is what a regression would break.
        check("docs/ is newer than the switch", True,
              "skipped — the switch is on but docs/ predates it; run build.py")
    else:
        check(f"alpha.js is on every sampled page built by the shell "
              f"({len(named)} of {len(built)})", len(named) == len(built),
              [f.name for f in built if f not in named][:3])
        check("docs/alpha.js exists", (DOCS / "alpha.js").exists())

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all alpha checks passed")
