#!/usr/bin/env python3
"""The Treasury's condominium register — the official list of every registered
อาคารชุด in Chiang Mai and Chiang Rai, with its assessed value per square
metre. WO-27, door 6.

WHAT THIS IS AND IS NOT. ราคาประเมิน is the government's ASSESSED value, the
figure transfer fees and taxes are reckoned from. It is not a market price,
not an asking price, and not what anybody paid — and it is usually well below
all three. Every line this writes says so, in both languages, because a
number labelled "the price of a condo" would be wrong in the one direction
that costs a reader money. The register's own edition date travels with it
(honours.json discipline: a mark without a year rots into a lie).

WHY IT IS WORTH HAVING. The catalogue holds 53 buildings whose own name says
condominium. The Treasury registers 367 in Chiang Mai alone. That gap is the
most useful thing on this page: it is a measured count of what a crawl of
OpenStreetMap cannot see, and the unmatched names are a ready-made discovery
list — the same shape as the events layer's "not in the directory yet".

THE TRAPS, both measured on 2026-08-21:

  ENCODING. The file is cp874 (TIS-620), not UTF-8. Read as UTF-8 it decodes
  to mojibake and a search for เชียงใหม่ returns ZERO rows — which looks
  exactly like a province with no condominiums rather than a wrong codec.

  SIZE AND ORDER. It is one national CSV of 122,112 rows, 18.8 MB, ordered by
  province code. Chiang Mai is 50 and Chiang Rai 57, so they sit near the END:
  any size-capped read (the shared harvester stops at 6 MB) silently returns a
  file with no northern rows in it at all. This importer reads it whole and
  keeps only the north.

  MANY ROWS PER BUILDING. A building appears once per use category and floor
  band — วันพลัส คลองชล has dozens of rows from 54,000 to 55,600 baht/m².
  So a building's figure is a SPREAD, never a single welded number. That rule
  is the make_shelf_cards price lesson (2026-08-19), applied to somebody's
  home instead of a massage board.

    python3 importers/harvest_condo_register.py            # fetch if missing
    python3 importers/harvest_condo_register.py --refetch  # ask again
    python3 importers/harvest_condo_register.py --offline  # parse the snapshot

Output: data/curated/condo_register.json, owned wholesale by this importer
(the datagoth.json arrangement) — nothing else may write it.
"""
import argparse
import csv
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "datagoth"
OUT = ROOT / "data" / "curated" / "condo_register.json"
SNAP = CACHE / "condominium-valuation.csv"

# Announced, and without the word "bot" — the gdcatalog WAF rule measured in
# harvest_datagoth.py. Same manners: one fetch, snapshot-first, a pause.
UA = "MotDang/1.0 (+https://motdang.net/about.html; 530kings@proton.me)"
DATASET = "condominium-valuation"
CKAN = "https://data.go.th/api/3/action/package_show?id="
PROVINCES = {"เชียงใหม่": "cm", "เชียงราย": "cr"}


def pkg_show():
    req = urllib.request.Request(CKAN + urllib.parse.quote(DATASET),
                                 headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("result", {})


def fetch(refetch=False):
    """The snapshot, and the metadata that makes it citable."""
    meta_path = Path(str(SNAP) + ".meta.json")
    if SNAP.exists() and not refetch:
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        return SNAP.read_bytes(), meta
    doc = pkg_show()
    res = next((x for x in doc.get("resources", [])
                if (x.get("format") or "").upper() == "CSV"), None)
    if not res:
        raise SystemExit("condominium-valuation: no CSV resource on the dataset")
    meta = {
        "dataset": DATASET,
        "dataset_url": f"https://data.go.th/dataset/{DATASET}",
        "resource_url": res.get("url"),
        "title": doc.get("title"),
        "publisher": (doc.get("organization") or {}).get("title") or "",
        "licence": doc.get("license_title") or "not specified",
        "edition": (doc.get("metadata_modified") or "")[:10],
    }
    req = urllib.request.Request(res["url"], headers={"User-Agent": UA, "Accept": "*/*"})
    # Read WHOLE. The north is at the end of the file — see the docstring.
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
    CACHE.mkdir(parents=True, exist_ok=True)
    SNAP.write_bytes(raw)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False))
    print(f"  fetched {len(raw):,} bytes")
    time.sleep(3)
    return raw, meta


def _int(s):
    m = re.search(r"\d[\d,]*", (s or ""))
    return int(m.group(0).replace(",", "")) if m else None


def parse(raw):
    """Northern rows only, folded to one entry per building."""
    text = raw.decode("cp874", errors="replace")          # NOT utf-8 — see above
    rows = list(csv.DictReader(io.StringIO(text)))
    out = {}
    for r in rows:
        prov = PROVINCES.get((r.get("CHANGWAT_NAME") or "").strip())
        if not prov:
            continue
        name = (r.get("CONDO_NAME") or "").strip()
        if not name:
            continue
        val = _int(r.get("VAL_AMT_P_MET"))
        key = (prov, name)
        e = out.setdefault(key, {
            "province": prov, "name": name,
            "amphoe": (r.get("AMPHUR_NAME") or "").strip(),
            "tambon": "" if (r.get("TUMBON_NAME") or "").strip() in ("NULL", "") else (r.get("TUMBON_NAME") or "").strip(),
            "uses": [], "values": [], "rows": 0,
        })
        e["rows"] += 1
        use = (r.get("USE_CATG") or "").strip()
        if use and use not in e["uses"]:
            e["uses"].append(use)
        if val:
            e["values"].append(val)
    reg = []
    for e in out.values():
        vals = sorted(e.pop("values"))
        # A spread, never a welded single figure: a building carries a row per
        # use category and floor band, and the low and the high are both true.
        e["assessed_low"] = vals[0] if vals else None
        e["assessed_high"] = vals[-1] if vals else None
        e["uses"] = e["uses"][:6]
        reg.append(e)
    reg.sort(key=lambda e: (e["province"], e["name"]))
    return reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()

    if a.offline:
        if not SNAP.exists():
            raise SystemExit("no snapshot and --offline")
        raw = SNAP.read_bytes()
        mp = Path(str(SNAP) + ".meta.json")
        meta = json.loads(mp.read_text()) if mp.exists() else {}
    else:
        raw, meta = fetch(a.refetch)

    reg = parse(raw)
    cm = [e for e in reg if e["province"] == "cm"]
    cr = [e for e in reg if e["province"] == "cr"]
    print(f"  {len(reg)} registered condominium buildings kept "
          f"(cm {len(cm)}, cr {len(cr)}) from {len(raw):,} bytes")
    priced = [e for e in reg if e["assessed_low"]]
    print(f"  {len(priced)} carry an assessed value; "
          f"{sum(1 for e in priced if e['assessed_low'] != e['assessed_high'])} of those "
          f"are a spread rather than one figure")

    doc = {
        "_readme":
            "The Treasury's register of every registered condominium (อาคารชุด) in "
            "Chiang Mai and Chiang Rai, with the ASSESSED value per square metre. "
            "ราคาประเมิน is the figure transfer fees and taxes are reckoned from — it "
            "is NOT a market price, not an asking price, and not what anyone paid, and "
            "it is normally well below all three. Anything rendered from this file must "
            "say so. A building carries one row per use category and floor band, so its "
            "figure is a SPREAD (assessed_low–assessed_high), never a single welded "
            "number — the make_shelf_cards price lesson. Owned wholesale by "
            "importers/harvest_condo_register.py; nothing else may write it. Traps, both "
            "measured 2026-08-21: the source CSV is cp874, not UTF-8 (read as UTF-8 it "
            "silently yields ZERO northern rows), and the north sits at the END of a "
            "122,112-row national file, so any size-capped read returns a file with no "
            "Chiang Mai in it.",
        "source": meta,
        "generated": str(date.today()),
        "counts": {"cm": len(cm), "cr": len(cr), "priced": len(priced)},
        "buildings": reg,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
