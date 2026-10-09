#!/usr/bin/env python3
"""The real-estate section: the place-page rows (listings_layer.place_row) and
the doors on /realestate.html (realestate_layer.emit).

    python3 tests/test_realestate_section.py

Runs against fixtures and a scratch DOCS; reads data/canonical for the page
test and writes nothing inside the repo.
"""
import html
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import listings_layer as L  # noqa: E402

FAILS = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


esc = html.escape


def bi(th, en, sep=" · ", raw=False):
    return f"{th}{sep}{en}"


# ---- place_row ---------------------------------------------------------------
L._join = {"b1": {"id": "md-b1", "n": 3, "live": 2, "sold": 1},
           "b2": {"id": "md-b2", "n": 1, "live": 0, "sold": 1}}
L._gleaned = {
    "b1": {"offers": {"live": 2, "sold": 1, "sale_thb": [3200000, 4100000],
                      "rent_month_thb": [12000, 15000], "as_of": "2026-09-20"},
           "facts": {"juristic_name": {"value": "Nitibukkhon A", "from": "Agency A", "at": "2026-09-20"},
                     "amenities": {"value": ["shared_pool", "lift"], "from": "Agency A", "at": "2026-09-20"},
                     "mystery_field": {"value": "x"}},
           "pictures": [{"src": "listings/photos/p1/1.jpg", "credit": "Agency A", "licence": "CC BY 4.0"},
                        {"src": "listings/photos/p1/2.jpg", "credit": "Agency A"}]},
}

row = L.place_row({"id": "b1"}, bi, esc, base="../../")
check("for sale ฿3.2M–฿4.1M" in row, "sale range prints")
check("to rent ฿12,000–฿15,000/month" in row, "monthly rent range prints")
check("as of 2026-09-20" in row, "as-of date prints")
check('href="../../listings/#md-b1"' in row, "links to the building's rows on the sheet")
check("Nitibukkhon A" in row and "per lister Agency A" in row, "a building fact prints with who said it")
check("mystery_field" not in row, "a field with no label is not rendered")
check(row.count("<img") == 1, "only the picture with a licence renders")
check("CC BY 4.0" in row and "Agency A" in row, "the picture carries its credit and licence")

row2 = L.place_row({"id": "b2"}, bi, esc)
check("1 sold" in row2 and "<img" not in row2, "sold-only building: count, no pictures")
check(L.place_row({"id": "nothing"}, bi, esc) == "", "no join, no glean: empty")
check(L.place_row({}, bi, esc) == "", "no id: empty")

L._gleaned = {}
row3 = L.place_row({"id": "b1"}, bi, esc)
check("2 live offers" in row3, "without glean output the count and link still print")

# ---- the doors ---------------------------------------------------------------
import realestate_layer as R  # noqa: E402

L._join = {"b1": {"id": "md-b1", "n": 2, "live": 2}}
data = {}
for p in ("cm", "cr"):
    doc = json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text(encoding="utf-8"))
    data[p] = doc["records"] if isinstance(doc, dict) and "records" in doc else doc

with tempfile.TemporaryDirectory() as tmp:
    docs = Path(tmp)
    g = dict(page=lambda title, body, **k: body, bi=bi, esc=esc, att=esc,
             place_slug=lambda r: r["id"], name_bi=lambda r: esc(r.get("name") or ""),
             BASE="https://motdang.net/", DOCS=docs, share_block=lambda *a, **k: "",
             PROVINCES=[{"key": "cm"}, {"key": "cr"}], shelf_og=None,
             svg_icon=lambda n, s=26, c="rowicon": f'<svg class="{c}"><use href="#{n}"/></svg>')
    R.emit(g, data)
    page = (docs / "realestate.html").read_text(encoding="utf-8")

check('<nav class="re-doors"' in page, "the section doors render")
check('href="listings/"' in page and "Listings (2)" in page.replace('<span class="re-count">', "").replace("</span>", ""),
      "the Listings door carries the live count")
check('id="words"' in page and 'id="shelves"' in page, "the in-page doors have their anchors")
try:
    join_live = bool(json.loads((ROOT / "data" / "config.json").read_text()).get("listerJoin"))
except (OSError, ValueError):
    join_live = False
check(("listings/join" in page) == join_live, "the join door shows only when data/config.json says the Worker is live")
check("&#127968;" not in page and "&#128220;" not in page, "no emoji in the section header (ICON-POLICY)")
for phrase in ("ranked for money", "ซื้ออันดับ"):
    check(phrase not in page, f"the retired ranking claim is gone: {phrase!r}")

print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nall passed")
sys.exit(1 if FAILS else 0)
