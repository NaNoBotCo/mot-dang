#!/usr/bin/env python3
"""WO-57 item 1 — the lifeline page and the service worker hold their rules.

Each check exists because the thing it guards can break silently and the
failure only shows up at the hour nobody is watching.

  KIND KEYS ARE NOT CATALOGUE SUBS   The first draft keyed drinking water on
      the sub `water`, which the catalogue already spends on parks: 98 lakes
      and reservoirs went onto a lifeline page as somewhere to drink, the
      Ping among them. Any future kind added to chuai_layer.KINDS gets the
      same collision unless something counts.
  THE FOUR NUMBERS ARE TAPPABLE      A number printed as text on a phone is a
      number somebody has to retype while shaking. Each must be a tel: link,
      and each must still name the agency that issues it.
  THE PAYLOAD IS WHOLE AND SMALL     The page is one request on a bad
      connection: the array must parse, must not thin out below a floor, and
      must stay under a stated ceiling over the wire. A silent doubling here
      is a page that stops arriving where it is needed most.
  THE WORKER'S FLOOR IS THIS PAGE    sw.js must precache the lifeline and name
      it as the navigation fallback. A worker that caches everything but the
      page it exists for is worse than none.
  EVERY PAGE REGISTERS IT            The site is 23,000 pages; the worker is
      registered from the shared shell or from nowhere.

    python3 tests/test_chuai.py
"""
import gzip
import json
import os
import re
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
sys.path.insert(0, str(ROOT))

# Over the wire, gzipped — the number that actually reaches a phone. Set
# clear of where it landed (46 kB) so ordinary growth does not trip it and a
# doubling does.
MAX_GZ_KB = 70
MIN_ROWS = 1800

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


# ---- zero-network: the keys, the numbers ------------------------------
import chuai_layer  # noqa: E402

print("the kind keys")
subs = set()
for p in ("cm", "cr"):
    f = ROOT / "data" / "canonical" / f"{p}.json"
    if f.exists():
        for r in json.loads(f.read_text()):
            subs.update(r.get("sub") or [])
own = {k for k, _, _, _ in chuai_layer.KINDS}
clash = {k for k in own if k in subs} - {"hospital", "health-station",
                                         "pharmacy", "fuel"}
check("no lifeline kind key collides with a catalogue sub it does not mean",
      not clash, f"colliding: {sorted(clash)}")
check("drinking water is NOT keyed on the parks sub `water`",
      "water" not in own)

print("the numbers")
em = json.loads((ROOT / "data" / "curated" / "emergency.json").read_text())
nums = em["numbers"]
check("four numbers or more", len(nums) >= 4, len(nums))
check("every number names its issuer and a URL to check it",
      all(n.get("issuer") and n.get("issuer_url") for n in nums))
check("every number is digits only (a tel: link cannot carry prose)",
      all(re.fullmatch(r"\d+", n["tel"]) for n in nums),
      [n["tel"] for n in nums])

# ---- the built artefact ------------------------------------------------
page = DOCS / "chuai.html"
sw = DOCS / "sw.js"
if not page.exists():
    print("\n  docs/chuai.html is not built — artefact checks SKIPPED")
    print("  (build first, or point MD_DOCS at a scratch build)")
else:
    print("the page")
    html = page.read_text(encoding="utf-8")
    for n in nums:
        check(f"{n['tel']} is a tel: link", f'href="tel:{n["tel"]}"' in html)
    m = re.search(r'<script id="ch-data" type="application/json">(.*?)</script>',
                  html, re.S)
    check("the baked array is present", bool(m))
    if m:
        try:
            rows = json.loads(m.group(1))
        except Exception as e:      # noqa: BLE001 — the point is to name it
            rows = []
            check("the baked array parses", False, e)
        else:
            check("the baked array parses", True)
        check(f"at least {MIN_ROWS:,} lifeline rows", len(rows) >= MIN_ROWS,
              len(rows))
        check("every row carries a name and a pin",
              all(r[1] and isinstance(r[2], int) and isinstance(r[3], int)
                  for r in rows))
        check("every row's kind is one this layer draws",
              all(0 <= r[0] < len(chuai_layer.KINDS) for r in rows))
        kinds = {r[0] for r in rows}
        check("every kind has at least one row",
              len(kinds) == len(chuai_layer.KINDS),
              f"missing {sorted(set(range(len(chuai_layer.KINDS))) - kinds)}")
    gz = len(gzip.compress(html.encode())) / 1024
    check(f"the page stays under {MAX_GZ_KB} kB gzipped", gz <= MAX_GZ_KB,
          f"{gz:.0f} kB")
    # The position is asked for in near.js and handed to the page's own draw
    # function. This check used to look for "geolocation" in chuai.html and
    # passed for the wrong reason once the search moved into near.js — so it
    # now names both files and says what each must not contain.
    near = DOCS / "near.js"
    check("near.js is here (the lifeline page cannot search without it)",
          near.exists())
    if near.exists():
        nj = near.read_text(encoding="utf-8")
        check("the position is asked for in near.js", "getCurrentPosition" in nj)
        SENDS = ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket",
                 "new Image(", "location.href=", "location.search")
        leaks = [w for w in SENDS if w in nj]
        check("near.js sends the position nowhere", not leaks, leaks)
    body = re.sub(r"(?s).*?<script id=\"ch-data\"", "", html)
    leaks = [w for w in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket")
             if w in body]
    check("the lifeline page's own script makes no requests at all",
          not leaks, leaks)

    print("the worker")
    check("sw.js is built", sw.exists())
    if sw.exists():
        js = sw.read_text(encoding="utf-8")
        check("the lifeline is the navigation fallback",
              "LIFE='/chuai.html'" in js)
        check("the lifeline, its stylesheet and near.js are precached",
              "PRE=[LIFE,'/style.css','/chuai.css','/near.js']" in js)
        check("the precache is never trimmed away",
              "PRE.indexOf" in js)
        check("the cache version moves with the build",
              re.search(r"var V='md-\d{4}-\d{2}-\d{2}-[0-9a-f]{8}'", js) is not None)
        check("only same-origin GETs are handled",
              "req.method!=='GET'" in js and "self.location.origin" in js)

    print("the registration")
    # Every page built by build.page() carries data-root on <html>; that is
    # the shell the registration lives in. The twenty-two pages that do not
    # are meta-refresh stubs for records that moved and the brief — neither
    # goes through the shell, and neither should install a worker on its way
    # somewhere else.
    # WO-75 — get/ is the toys themselves, published verbatim from the repos that
    # build them. This suite is a check on the pages this site WRITES; making a
    # third-party game pass it would mean editing the game. downloads_layer.py
    # names any image without alt text in its own build line instead.
    pages = [p for p in DOCS.rglob("*.html")
             if not p.relative_to(DOCS).as_posix().startswith("get/")]
    sample = random.sample(pages, min(60, len(pages)))
    missing, stubs = [], 0
    for f in sample:
        t = f.read_text(encoding="utf-8")
        if 'data-root=' not in t:
            stubs += 1
            continue
        if "navigator.serviceWorker.register('/sw.js')" not in t:
            missing.append(f.relative_to(DOCS).as_posix())
    check(f"every sampled page built by the shell registers the worker "
          f"({len(sample) - stubs} of {len(sample)} sampled)",
          not missing, missing[:3])
    # Four kinds of page legitimately live outside the shell, and the point
    # of naming them is that a FIFTH one appearing is news: a page that
    # stopped going through build.page() has also stopped carrying the
    # header, the footer, the four numbers and the worker, and nothing else
    # would say so.
    ALLOWED = ("cm/p/", "cr/p/",        # meta-refresh stubs for moved records
               "widgets/",              # the chromeless iframe boards
               "brief/", "app/")        # the brief, and the phone app's own www
    shell_free = [f.relative_to(DOCS).as_posix() for f in pages
                  if 'data-root=' not in f.read_text(encoding="utf-8")]
    strays = [s for s in shell_free if not s.startswith(ALLOWED)]
    check(f"the {len(shell_free)} pages outside the shell are only the four "
          f"known kinds", not strays, strays[:4])

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all chuai checks passed")
