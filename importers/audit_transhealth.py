#!/usr/bin/env python3
"""What the corpus says about trans health, counted — WO-26.

Report only, no --emit: there is nothing to emit, and that is the finding.
The beauty audit's lesson (importers/audit_beauty.py) was that a shelf can lie
because nobody read the Thai names; this audit read them, and here the names
genuinely say nothing. The four reports keep the hole visible so it cannot be
mistaken for coverage, and check that the curated register standing in for the
corpus stays sound:

  1. the name scan       — every record whose name matches TRANS_NAME_RX
                           (imported from transhealth_layer so this report and
                           the page's own sentence cannot drift apart)
  2. the register        — every row in data/curated/transhealth.json resolved
                           against canonical; an unresolvable place id here is
                           a page row silently missing, so it exits 1
  3. the welcome tags    — every record carrying attrs.lgbtq / lgbtqTrans
                           (importers/import_all.py:apply_lgbtq)
  4. the duplicate watch — register place ids whose name appears on more than
                           one record, the pairs a person still has to judge
                           (they are also in transhealth.json unverified[])

Run:  python3 importers/audit_transhealth.py
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "_transhealth_layer", str(ROOT / "transhealth_layer.py"))
_layer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_layer)
TRANS_NAME_RX = _layer.TRANS_NAME_RX


def names_of(r):
    return " ".join(str(v) for v in
                    (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)


def main():
    recs = []
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            recs.append((prov, r))
    by_id = {r["id"]: (p, r) for p, r in recs}
    reg = json.loads((ROOT / "data" / "curated" / "transhealth.json").read_text())
    bad = 0

    print(f"== 1 · the name scan — {len(recs):,} records ==")
    hits = [(p, r) for p, r in recs if TRANS_NAME_RX.search(names_of(r))]
    print(f"   {len(hits)} record(s) name this care in their own sign")
    for p, r in hits:
        print(f"   {p} | {names_of(r)[:64]} | {r['id']}")
    if not hits:
        print("   0 of them — the register is the coverage, and this line is "
              "the reason it exists")

    print("\n== 2 · the register, resolved ==")
    grades = {}
    for row in reg.get("rows", []):
        g = row.get("grade", "?")
        grades[g] = grades.get(g, 0) + 1
        pid = row.get("place")
        if pid is None:
            print(f"   {row['key']:<16} {g:<17} (no place record by design)")
            continue
        if pid in by_id:
            p, r = by_id[pid]
            print(f"   {row['key']:<16} {g:<17} -> {p} {names_of(r)[:44]}")
        else:
            print(f"   {row['key']:<16} {g:<17} -> UNRESOLVED id {pid}")
            bad += 1
    for v in reg.get("venues", []):
        if v["place"] not in by_id:
            print(f"   venue           -> UNRESOLVED id {v['place']}")
            bad += 1
    print("   grades:", ", ".join(f"{k} {v}" for k, v in sorted(grades.items())))

    print("\n== 3 · lgbtq welcome tags in attrs ==")
    tagged = [(p, r) for p, r in recs
              if (r.get("attrs") or {}).get("lgbtq")
              or (r.get("attrs") or {}).get("lgbtqTrans")]
    for p, r in tagged:
        a = r["attrs"]
        vals = " ".join(f"{k}={a[k]}" for k in ("lgbtq", "lgbtqTrans") if a.get(k))
        print(f"   {p} | {names_of(r)[:44]} | {vals} | {r['id']}")
    if not tagged:
        print("   none — expected only before the first import_all.py run "
              "after apply_lgbtq landed")

    print("\n== 4 · the duplicate watch ==")
    reg_ids = [row["place"] for row in reg.get("rows", []) if row.get("place")]
    watched = 0
    for pid in reg_ids:
        if pid not in by_id:
            continue
        _, r0 = by_id[pid]
        nm = (r0.get("name") or "").strip()
        if not nm:
            continue
        same = [r["id"] for _, r in recs if (r.get("name") or "").strip() == nm]
        if len(same) > 1:
            watched += 1
            print(f"   {nm[:40]} appears {len(same)}x: {', '.join(same)}")
    if not watched:
        print("   no register place shares its exact name with another record")
    print("\n(unresolved ids:", bad, "— non-zero exits 1 so a renamed or "
          "re-crawled id cannot silently drop a page row)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
