#!/usr/bin/env python3
"""Settle what can be settled in the temple review file. Zero network.

THE PILE. import_opendata's temple fold holds a register row OUT whenever any
unstamped record we already hold answers to the same name — 252 rows on
2026-08-20. That is the right default (a directory listing one temple twice is
worse than one listing it once) but it is over-cautious in a measurable way:
**every one of those cases is N register temples sharing a name across
DIFFERENT อำเภอ against ONE held record.** At most one of the N can be the
record we hold; the other N−1 are temples nobody has written down here. Holding
all N out drops ~180 real temples to avoid ~72 possible duplicates.

WHAT THIS SETTLES, and only this. A refutation, never a pick:

    A register row in อำเภอ X is NOT the held record if the held record's
    surveyed pin is more than REFUTE_M from every pin we know to stand in X.

That is a negative test, which is why it is safe. WO-1 refused to break these
ties with the pin — "picking the nearer one is exactly the guess this refuses
to make" — and that refusal stands here: this file never says which register
row a held record IS. It only says which ones it cannot be, and releases those
to be folded as the separate temples they are.

THE THRESHOLD IS MEASURED, NOT CHOSEN. Ground: every record with an exact pin
that states its own อำเภอ (attrs or address) — 1,129 in Chiang Mai, 930 in
Chiang Rai, 59 districts. For each of those pins, the distance to the nearest
OTHER pin of the same อำเภอ: median 840 m (cm) / 705 m (cr), p99 8.2 km / 5.9
km. At 12 km, refusing to believe a pin belongs to that district would be wrong
for 3 of 1,123 cm pins and 5 of 927 cr pins — **0.27% and 0.54%**. Those are
the error bars this runs on; rerun with --validate to reprint them.

The survivors are NOT settled and are not treated as settled. Where exactly one
register row survives, it is the likely twin of the held record and is written
to the shortlist for a person: stamping it would put a founding year and a
permanent code on that record, and a wrong stamp is another temple's history on
this temple's page.

    python3 importers/audit_temple_review.py            # settle + write
    python3 importers/audit_temple_review.py --validate # reprint the error bars
    python3 importers/audit_temple_review.py --dry-run  # print, write nothing

OUTPUT
  data/curated/temple_verdicts.json   released codes + the evidence for each
  cache/temple_shortlist.txt          what still needs a person, ranked
"""
import argparse
import collections
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "wat-registry"))
from geocode_local import _haversine, _norm            # noqa: E402

REGISTRY_DB = os.path.join(os.path.dirname(ROOT), "wat-registry", "registry.db")
OUT = os.path.join(ROOT, "data", "curated", "temple_verdicts.json")
SHORTLIST = os.path.join(ROOT, "cache", "temple_shortlist.txt")
PROVINCE_TH = {"cm": "เชียงใหม่", "cr": "เชียงราย"}
IS_TEMPLE = re.compile(r"^\s*(วัด|wat\b)", re.IGNORECASE)
AMP_IN_ADDR = re.compile(r"(?:อำเภอ|อ\.)\s*([ก-๙]+)")
MINE = re.compile(r"^(cm|cr)-(onab|dgth)-")
# Measured: see the docstring. 12 km is where a false refutation costs
# 0.27% (cm) / 0.54% (cr) — the p99 of same-district pin spacing plus room.
REFUTE_M = 12000

try:
    from thairom import matchkey
except ImportError:
    matchkey = None


def load_canonical():
    out = {}
    for prov in ("cm", "cr"):
        p = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
        out[prov] = json.loads(open(p, encoding="utf-8").read()) if os.path.exists(p) else []
    return out


def amphoe_ground(canon):
    """Every surveyed pin that states which อำเภอ it stands in.

    Read from attrs first, then from the address text — most records carry the
    district only in prose, and this is the whole reason the ground is dense
    enough to test against.
    """
    g = {"cm": collections.defaultdict(list), "cr": collections.defaultdict(list)}
    for prov, recs in canon.items():
        for r in recs:
            if r.get("lat") is None or (r.get("geoPrecision") or "exact") != "exact":
                continue
            a = r.get("attrs") or {}
            amp = None
            for c in (a.get("amphoe"), a.get("district")):
                if c and re.search(r"[ก-๙]", str(c)):
                    amp = _norm(str(c))
                    break
            if not amp:
                m = AMP_IN_ADDR.search(r.get("address") or "")
                if m:
                    amp = _norm(m.group(1))
            if amp:
                g[prov][amp].append((r["lat"], r["lng"], r["id"]))
    return g


def validate(canon, ground):
    """Reprint the error bars this file runs on: for every ground pin, how far
    is the nearest OTHER pin of the same district?"""
    for prov in ("cm", "cr"):
        ds = []
        for amp, pts in ground[prov].items():
            for lat, lng, rid in pts:
                others = [q for q in pts if q[2] != rid]
                if others:
                    ds.append(min(_haversine((lat, lng), (q[0], q[1])) for q in others))
        if not ds:
            continue
        ds.sort()
        p = lambda x: int(ds[int(len(ds) * x)])          # noqa: E731
        bad = sum(1 for d in ds if d > REFUTE_M)
        print(f"{prov}: {len(ds)} ground pins in {len(ground[prov])} อำเภอ — "
              f"nearest same-district pin: median {p(.5)}m, p95 {p(.95)}m, p99 {p(.99)}m")
        print(f"    at REFUTE_M={REFUTE_M}m a refutation would be wrong for "
              f"{bad}/{len(ds)} = {bad / len(ds):.2%}")


def groups(canon):
    """(prov, name key) -> (unstamped register rows, unstamped held records)."""
    joined = {}
    wj = os.path.join(ROOT, "data", "curated", "wat_registry.json")
    if os.path.exists(wj):
        joined = json.load(open(wj, encoding="utf-8")).get("wats") or {}
    stamped_codes = {v.get("code") for v in joined.values()}
    con = sqlite3.connect(f"file:{REGISTRY_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    reg = collections.defaultdict(list)
    for prov, th in PROVINCE_TH.items():
        for t in con.execute(
                "SELECT code,name_th,name_key,tambon_th,amphoe_th,founded_ce,rank"
                "  FROM temples WHERE changwat_th=?", (th,)):
            if t["code"] in stamped_codes:
                continue
            reg[(prov, t["name_key"])].append(dict(t))
    con.close()
    held = collections.defaultdict(list)
    for prov, recs in canon.items():
        for r in recs:
            if MINE.match(r.get("id") or "") or r["id"] in joined:
                continue
            names = [r.get("name") or "", r.get("nameTh") or "", r.get("nameEn") or ""]
            if not any(IS_TEMPLE.search(n) for n in names if n):
                continue
            k = matchkey(names[1] or names[0] or names[2])
            if k:
                held[(prov, k)].append(r)
    return {k: (rows, held.get(k) or []) for k, rows in reg.items() if held.get(k)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if matchkey is None or not os.path.exists(REGISTRY_DB):
        print("no ONAB register on disk — nothing to settle")
        return
    canon = load_canonical()
    ground = amphoe_ground(canon)
    if args.validate:
        validate(canon, ground)
        return

    released, shortlist = {}, []
    n_rows = n_pinless = 0
    for (prov, key), (rows, helds) in sorted(groups(canon).items()):
        n_rows += len(rows)
        pinned = [h for h in helds
                  if h.get("lat") is not None and (h.get("geoPrecision") or "exact") == "exact"]
        if not pinned:
            n_pinless += len(rows)
            shortlist.append((99, prov, rows, helds,
                              "no held record here carries a surveyed pin — nothing to test against"))
            continue
        survivors = []
        for t in rows:
            amp = _norm(t["amphoe_th"] or "")
            pts = ground[prov].get(amp) or []
            if not pts:
                survivors.append((t, None))
                continue
            # The nearest pin we know to stand in that district, from ANY held
            # record in the group: the row is refuted only if EVERY held
            # candidate is far from it.
            d = min(min(_haversine((h["lat"], h["lng"]), (q[0], q[1])) for q in pts)
                    for h in pinned)
            if d > REFUTE_M:
                near = min(pinned, key=lambda h: min(
                    _haversine((h["lat"], h["lng"]), (q[0], q[1])) for q in pts))
                released[t["code"]] = {
                    "name_th": t["name_th"], "province": prov,
                    "tambon": t["tambon_th"], "amphoe": t["amphoe_th"],
                    "why": "refuted",
                    "held_candidate": near["id"],
                    "km_from_that_amphoe": round(d / 1000, 1),
                    "ground_pins_in_amphoe": len(pts),
                }
            else:
                survivors.append((t, round(d)))
        if survivors:
            shortlist.append((len(survivors), prov, [t for t, _ in survivors], helds,
                              "survived the distance test — a person decides whether the held "
                              "record IS one of these (stamping it adds a code and a founding year)"))

    doc = {
        "_comment": (
            "Machine-settled verdicts on the temple review pile, by "
            "importers/audit_temple_review.py. A `released` code is a register "
            "row PROVEN not to be the record we already hold — its อำเภอ is "
            f"more than {REFUTE_M / 1000:.0f} km from every pin we know to stand "
            "there — so import_opendata folds it as the separate temple it is. "
            "This file never says which row a held record IS; that stays a "
            "person's call (cache/temple_shortlist.txt). Rewritten wholesale on "
            "every run; hand corrections belong in another curated file. "
            "Measured false-refutation rate at this threshold: 0.27% cm, 0.54% cr "
            "(--validate reprints it)."),
        "refute_m": REFUTE_M,
        "released": dict(sorted(released.items())),
    }
    if not args.dry_run:
        json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        # Fewest survivors first — those are the closest to settled. Sort on
        # the scalars only; the rows and records are dicts and never compare.
        shortlist.sort(key=lambda s: (s[0], s[1], s[2][0]["code"]))
        with open(SHORTLIST, "w", encoding="utf-8") as f:
            f.write("# Temples the machine could NOT settle — for a person.\n"
                    "# Each block: register rows that could still be the record we hold.\n"
                    "# Settling one means either (a) it is the same temple → stamp the held\n"
                    "#   record with that code, or (b) it is not → the row can be released.\n"
                    "# The rest of the pile is settled in data/curated/temple_verdicts.json.\n\n")
            for _n, prov, rows, helds, why in shortlist:
                f.write(f"[{prov}] {rows[0]['name_th']} — {why}\n")
                for t in rows:
                    f.write(f"    reg {t['code']}  ต.{t['tambon_th'] or '?'} "
                            f"อ.{t['amphoe_th'] or '?'}  founded {t['founded_ce'] or '?'}\n")
                for h in helds:
                    pin = (f"{h['lat']:.5f},{h['lng']:.5f}"
                           if h.get("lat") is not None else "no pin")
                    f.write(f"    held {h['id']}  {h.get('name')}  [{pin}]\n")
                f.write("\n")
    print(f"register rows in the pile: {n_rows}")
    print(f"  RELEASED (proven a different temple): {len(released)}")
    print(f"  still for a person: {n_rows - len(released)}"
          f" (of which {n_pinless} have no surveyed pin to test against)")
    print(f"  blocks in the shortlist: {len(shortlist)}")
    if not args.dry_run:
        print(f"→ {os.path.relpath(OUT, ROOT)} · {os.path.relpath(SHORTLIST, ROOT)}")


if __name__ == "__main__":
    main()
