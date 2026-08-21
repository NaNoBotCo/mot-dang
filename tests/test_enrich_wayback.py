#!/usr/bin/env python3
"""enrich_wayback.py — reading a dead business's own site out of the archive.

This importer is the loosest thing in the enrichment path and it knows it. Its
sibling only trusts schema.org and `tel:` links; this one reads plain text,
because the sites it visits are a decade old and print their number as words.
Every guard that earns it that licence is checked here, on fixtures, with no
network:

1. The snapshot must be fetched with the `id_` modifier. Without it the Archive
   wraps the page in its own toolbar, and the harvester would read
   archive.org's Facebook link and file it as the shop's.
2. A number in a web-designer credit is not the shop's number.
3. An email is taken only at the site's own domain — the designer's sits at the
   designer's.
4. A fax number is not a phone number.
5. Nothing archived may displace a fact the crawl already holds. This is the
   one that would do real damage: an OSM phone updated last year must not be
   overwritten by a 2016 snapshot.
6. Every recovered field carries `archivedOn`, and build.py turns that into
   words on the page. A recovered fact that renders like a fresh one is the
   whole failure mode this importer was designed around.

Run: python3 tests/test_enrich_wayback.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))

import enrich_wayback as ew  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print("%-4s %s%s" % ("ok" if ok else "FAIL", name, "" if ok else "  — " + detail))
    if not ok:
        fails.append(name)


# ------------------------------------------------------------ 1. the id_ form
u = ew.raw_snapshot_url("https://web.archive.org/web/20240418080749/https://x.co/",
                        "20240418080749", "https://x.co/")
check("the snapshot url asks for raw bytes, not the toolbar", "id_/" in u, u)
check("the snapshot url keeps the timestamp", "20240418080749" in u, u)

# ------------------------------------------------- 2. the designer's number
credit = """<html><body>
  <p>Welcome to Baan Somchai</p>
  <p>web design and hosting by IC-MyHost, Tel. 02-555-1234</p>
</body></html>"""
got, how = ew.harvest_text(credit, "http://baansomchai.com/")
check("a number inside a web-design credit is refused",
      "phone" not in got, "took %s" % got.get("phone"))

# ---------------------------------------------------- 3. whose email is it
# Written as these pages actually are: the contact block is words, not markup.
# A `mailto:` link is the sibling harvester's job — page_text() strips tags, so
# this pass cannot see one, and the two are merged precisely so neither has to
# cover the other's ground.
mixed = """<html><body>
  Tel. +66 53 284 295
  Reservations: sales@baansomchai.com
  <p>site by webguy@agency.co.th</p>
</body></html>"""
got, how = ew.harvest_text(mixed, "http://www.baansomchai.com/")
check("the phone is read out of plain text", got.get("phone") == "053-284295",
      "got %r" % got.get("phone"))
check("the email at the site's own domain is taken",
      (got.get("attrs") or {}).get("email") == "sales@baansomchai.com",
      "got %r" % (got.get("attrs") or {}).get("email"))
check("the designer's email is not taken",
      "agency.co.th" not in json.dumps(got))
check("how() says the phone came from text, not from markup",
      "text" in (how.get("phone") or ""), how.get("phone"))

# And the pair together must cover a page that puts the address in a link and
# the number in prose — which is the common shape.
from enrich_sites import harvest as structured  # noqa: E402
half_markup = """<html><body>
  <p>โทร. 081-234-5678</p>
  <a href="mailto:info@baansomchai.com">email us</a>
</body></html>"""
merged, mhow = ew.merge_harvests(*structured(half_markup, "http://baansomchai.com/"),
                                 *ew.harvest_text(half_markup, "http://baansomchai.com/"))
check("merged: the Thai-labelled phone in prose is found",
      merged.get("phone") == "081-234-5678", "got %r" % merged.get("phone"))
check("merged: the mailto address is found by the structured pass",
      (merged.get("attrs") or {}).get("email") == "info@baansomchai.com",
      "got %r" % (merged.get("attrs") or {}).get("email"))

# ------------------------------------------------------------- 4. fax is not phone
faxonly = "<html><body>Fax. +66 53 206 168<br>Address: 4 soi 5</body></html>"
got, _ = ew.harvest_text(faxonly, "http://baansomchai.com/")
check("a fax number is not filed as a phone", "phone" not in got,
      "took %s" % got.get("phone"))

# ------------------------------------------- 5. the merge never overrules the crawl
primary, phow = {}, {}
extra = {"phone": "053-111111", "attrs": {"email": "a@b.com"}}
merged, _ = ew.merge_harvests(primary, phow, extra, {"phone": "text"})
check("text fills a field the structured pass left empty",
      merged.get("phone") == "053-111111")
primary = {"phone": "053-999999"}
merged, _ = ew.merge_harvests(primary, {"phone": "schema.org"}, extra, {"phone": "text"})
check("structured data wins over text for the same field",
      merged.get("phone") == "053-999999", merged.get("phone"))

# The rule that matters most lives in main(); assert the source states it,
# because a refactor that drops it is silent and destructive.
src = open(os.path.join(ROOT, "importers", "enrich_wayback.py"), encoding="utf-8").read()
check("main() still fills only fields the record lacks",
      re.search(r"if got\.get\(k\) and not r\.get\(k\)", src) is not None)
check("attrs likewise only fill empty keys",
      re.search(r"if not have\.get\(k\)", src) is not None)

# ------------------------------------------------------ 6. dating the recovered fact
check("entries are licensed as archived, not as a live site",
      '"archived-official-site"' in src)
check("per-field provenance carries the snapshot date",
      '"archivedOn": shot' in src)
build_src = open(os.path.join(ROOT, "build.py"), encoding="utf-8").read()
check("build.py badges an archived channel with its year",
      "archived-official-site" in build_src and "จากเว็บเดิม" in build_src,
      "the page would show a recovered number as though it were current")
check("archived opening hours get the same dating",
      build_src.count("archived-official-site") >= 2)

# ------------------------------------------------------------- age arithmetic
check("a snapshot with no timestamp is treated as ancient",
      ew.snapshot_age_years("") > 50)
check("this year's snapshot is under a year old",
      ew.snapshot_age_years("2026" + "0801") < 1.5)

print("\n%s" % ("PASS" if not fails else "FAIL: " + ", ".join(fails)))
raise SystemExit(1 if fails else 0)
