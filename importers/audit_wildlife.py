#!/usr/bin/env python3
"""What the corpus says about wildlife-and-plant goods, counted — WO-32.

Report only, no --emit. The finding mirrors WO-31's: the coverage is the
curated register (data/curated/wildlife.json), because the corpus's own
names say almost nothing — a bare word-scan meets namesakes (ตำบลสันผีเสื้อ,
Tiger Mart, orchid hotels), which is the WO-24 lesson measured again on a
new subject. The checks keep the register sound:

  1. the census        — the three scans souvenir_layer.py runs live
                         (farm-named · souvenir rows · namesakes), printed
                         with their hits so a wrong regex is visible
  2. the items         — every item row carries a Thai/EN name, a class in
                         both languages, a carry flag the layer knows, and
                         at least one dated source. A legal claim with no
                         source is the one thing this page must never ship,
                         so a bare row exits 1
  3. the tiers         — every laws[] row sourced and dated, same bar
  4. the flags         — carry values restricted to the four the page
                         renders; an unknown flag would render as "ask",
                         which for a prohibited thing is the page inventing
                         permission, so it exits 1 here instead

Run:  python3 importers/audit_wildlife.py
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "_souvenir_layer", str(ROOT / "souvenir_layer.py"))
_layer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_layer)
FARM_NAME_RX = _layer.FARM_NAME_RX
SHELF_NAME_RX = _layer.SHELF_NAME_RX
NAMESAKE_RX = _layer.NAMESAKE_RX

CARRY_OK = {"no", "papers", "ask", "ok"}


def names_of(r):
    return " ".join(str(v) for v in
                    (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)


def sourced(row):
    return any(s.get("ref") and s.get("fetched")
               for s in (row.get("sources") or []))


def main():
    recs = []
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            recs.append((prov, r))
    reg = json.loads((ROOT / "data" / "curated" / "wildlife.json").read_text())
    bad = 0

    print(f"== 1 · the census — {len(recs):,} records ==")
    farm = [(p, r) for p, r in recs if FARM_NAME_RX.search(names_of(r))]
    shelf = [(p, r) for p, r in recs if SHELF_NAME_RX.search(names_of(r))]
    namesake = [(p, r) for p, r in recs if NAMESAKE_RX.search(names_of(r))]
    print(f"   {len(farm)} record(s) whose own name says farm/nursery for these goods")
    for p, r in farm:
        print(f"   {p} | {names_of(r)[:64]} | {r['id']}")
    print(f"   {len(shelf)} record(s) on the souvenir-and-handicraft rows")
    for p, r in shelf:
        print(f"   {p} | {names_of(r)[:64]} | {r['id']}")
    print(f"   {len(namesake)} bare-word hits (เสือ/ผีเสื้อ/กล้วยไม้ …) — namesakes,")
    print("   set aside on purpose: the WO-24 lesson, measured again here.")

    print("\n== 2 · the items — data/curated/wildlife.json ==")
    items = reg.get("items") or []
    print(f"   {len(items)} item(s)")
    for it in items:
        probs = []
        if not (it.get("name_th") and it.get("name_en")):
            probs.append("missing a name")
        if not (it.get("class_th") and it.get("class_en")):
            probs.append("missing its class")
        if not (it.get("carry_th") and it.get("carry_en")):
            probs.append("missing its carry sentence")
        if not sourced(it):
            probs.append("NO DATED SOURCE")
        if probs:
            bad += 1
            print(f"   BAD  {it.get('key')}: " + ", ".join(probs))
        else:
            print(f"   ok   {it.get('key')} [{it.get('carry')}]")

    print("\n== 3 · the tiers ==")
    for lw in reg.get("laws") or []:
        if not sourced(lw):
            bad += 1
            print(f"   BAD  {lw.get('key')}: NO DATED SOURCE")
        else:
            print(f"   ok   {lw.get('key')}")

    print("\n== 4 · the flags ==")
    for it in items:
        if it.get("carry") not in CARRY_OK:
            bad += 1
            print(f"   BAD  {it.get('key')}: carry={it.get('carry')!r} is not one "
                  f"of {sorted(CARRY_OK)} — would render as 'ask'")
    if not bad:
        print(f"   all carry flags among {sorted(CARRY_OK)}")

    if bad:
        print(f"\n{bad} problem(s) — the register is not fit to render")
        sys.exit(1)
    print("\nregister sound")


if __name__ == "__main__":
    main()
