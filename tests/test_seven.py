#!/usr/bin/env python3
"""WO-38 — the branch layer holds its own rules. Zero network, no build needed.

What is held, and why each thing can break silently without this:

  RADII IN STEP   build.py's SEVEN_DUP_M and audit_convenience.py's DUP_M are
                  the same number written twice (the audit must run standalone;
                  build.py must not import an importer at page time). If they
                  drift, the audit calls a pair a duplicate that the site is
                  rendering as a double — one catalogue, two stories.
  CTX INTEGRITY   after _fill_seven_ctx: every twin is same-brand, inside
                  [SEVEN_DUP_M, SEVEN_TWIN_MAX_M]; every anchor is a named
                  non-convenience record within SEVEN_ANCHOR_MAX_M. A wrong
                  neighbour puts a stranger's name on a shop's page — the
                  venue-matching lesson from the events layer, held here too.
  THE BAND        renders on a convenience record (the door to /seven.html at
                  minimum), renders NOTHING on any other record, and never
                  renders a distance below SEVEN_DUP_M.
  THE RULE COPY   seven_from_name refuses the three witnessed cases: the
                  denial way, the beer stall in 7-Eleven livery, and any
                  name with residue past the brand.

    python3 tests/test_seven.py
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


# ---- the radii, one number written twice ------------------------------
import build  # noqa: E402  (module-level data loads; build() is not called)

spec = importlib.util.spec_from_file_location(
    "audit_convenience", ROOT / "importers" / "audit_convenience.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)   # defines main(); the __main__ guard keeps it from running

print("radii")
check("SEVEN_DUP_M is written the same in build.py and the audit",
      build.SEVEN_DUP_M == audit.DUP_M,
      f"build {build.SEVEN_DUP_M} vs audit {audit.DUP_M}")

# ---- the name rule's witnessed refusals -------------------------------
import import_overpass as io  # noqa: E402

print("the name rule")
check("a bare sign fills the brand",
      io.seven_from_name({}, "convenience", "7-Eleven") == "7-Eleven")
check("the doubled probe (name + name:en) still fills",
      io.seven_from_name({}, "convenience", "7-Eleven 7-Eleven") == "7-Eleven")
check("the slash spelling fills",
      io.seven_from_name({}, "convenience", "7-Eleven 7/11") == "7-Eleven")
check("a mapper's denial refuses",
      io.seven_from_name({"not:brand:wikidata": "Q259340"},
                         "convenience", "7-Eleven") is None)
check("the beer stall in seven livery refuses",
      io.seven_from_name({}, "convenience",
                         "7-11 หลอด biers Bier Stube") is None)
check("a condominium shelf refuses",
      io.seven_from_name({}, "condo", "เซเว่น สตาร์") is None)
check("เซเว่นอีเลฟเว่น in full Thai fills",
      io.seven_from_name({}, "convenience", "เซเว่นอีเลฟเว่น") == "7-Eleven")

# ---- ctx integrity over the real records ------------------------------
print("ctx integrity (real canonical records)")
data = {}
for prov in ("cm", "cr"):
    f = ROOT / "data" / "canonical" / f"{prov}.json"
    data[prov] = json.loads(f.read_text()) if f.exists() else []
build._fill_seven_ctx(data)
by_id = {r["id"]: r for rs in data.values() for r in rs}
n_twin = n_anchor = 0
bad = []
for cid, ctx in build.SEVEN_CTX.items():
    c = by_id[cid]
    if "convenience" not in (c.get("sub") or []):
        bad.append(f"{cid} not convenience")
    tw = ctx.get("twin")
    if tw:
        o, d = tw
        n_twin += 1
        if not (build.SEVEN_DUP_M <= d <= build.SEVEN_TWIN_MAX_M):
            bad.append(f"{cid} twin at {d:.0f} m")
        if (c.get("attrs") or {}).get("brand") != (o.get("attrs") or {}).get("brand"):
            bad.append(f"{cid} twin brand mismatch")
    for o, d in ctx.get("anchors") or []:
        n_anchor += 1
        if d > build.SEVEN_ANCHOR_MAX_M:
            bad.append(f"{cid} anchor at {d:.0f} m")
        if "convenience" in (o.get("sub") or []):
            bad.append(f"{cid} anchor is itself a convenience store")
        if not (o.get("name") or o.get("nameTh") or o.get("nameEn")):
            bad.append(f"{cid} anchor has no name to stand behind")
check("every twin and anchor inside its measured radius, same brand, named",
      not bad, "; ".join(bad[:4]))
check("the ctx is not empty (twins and anchors both found)",
      n_twin > 0 and n_anchor > 0, f"twins {n_twin} anchors {n_anchor}")

# ---- the band ---------------------------------------------------------
print("the band")
seven = next((r for r in data["cm"]
              if (r.get("attrs") or {}).get("brand") == "7-Eleven"
              and r.get("lat") is not None), None)
band = build.seven_band(seven) if seven else ""
check("a branch page gets the band, with the door to /seven.html",
      bool(seven) and "sevenband" in band and "../../seven.html" in band)
check("the band is bilingual", 'lang="th"' in band or "lang='th'" in band)
wat = next((r for r in data["cm"] if "wat" in (r.get("cat") or [])), None)
check("a temple gets no band", wat is not None and build.seven_band(wat) == "")

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all seven checks passed")
