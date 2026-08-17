#!/usr/bin/env python3
"""Join the ONAB temple register (รหัสวัด) onto our wat records. Zero network.

WHAT THIS BRINGS
The National Office of Buddhism publishes a register of every temple in
Thailand — 43,858 of them, 2,578 in Chiang Mai and Chiang Rai. Each carries a
permanent code (รหัสวัด), the founding year, the nikaya, the temple's rank, its
wisung-khamsima status, and the full ตำบล/อำเภอ hierarchy. We hold 596 wat
records with none of that.

WHAT IT DOES NOT BRING, measured rather than assumed: contact details. The
register carries a phone on 6 temples nationwide and a website on 1 — none of
them here. Wats stay this site's least contactable shelf and only a person
standing at the gate will change that. What the register does carry is TIME
(founded_ce on 2,575 of 2,578) and PLACE (tambon/amphoe on all of them), which
is what the ancientness sort and the by-neighbourhood grouping are made of.

HOW THE JOIN WORKS
The register holds "สูงเม่น" in "เชียงใหม่"; we hold "Wat Sung Men" or
"วัดสูงเม่น". Neither side carries the other's spelling, so both go through
thairom.matchkey (the wat-registry project's own normaliser, the same one that
stamped 6,203 manuscripts) and are compared inside one province.

  1. gate to real temples — a record whose name does not begin วัด / Wat is a
     shrine, a spirit house or a monastery hall, and the register does not
     hold those. Matching them would be inventing a temple.
  2. narrow to the province the record is already filed under
  3. compare match keys; accept ONLY when exactly one candidate answers
  4. when several answer, narrow again by อำเภอ/ตำบล where the record STATES
     one — in an OSM addr field, or written out in the Thai description or
     the Wikipedia article already fetched for it. A stated district is a
     fact from the source, not a guess about it.
  5. everything still standing goes to the review file, never to a coin flip

251 name keys repeat inside a single province here, so steps 4 and 5 are not a
corner case; they are the reason the join is safe. The pin is deliberately not
used to break a tie: two temples of one name are usually two villages apart,
and picking the nearer one is exactly the guess this refuses to make.

OUTPUT
  data/curated/wat_registry.json     the join, keyed by place id
  cache/wat_registry_review.txt      what a human has to settle

Writing into data/curated/ follows the enrich.json arrangement: this importer
owns this one file and rewrites it wholesale; nothing else may touch it, and it
never writes data/canonical/, which the crawl rewrites out from under anything
hand-held. import_all.py only ever READS it.

    python3 importers/import_wat_registry.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT.parent
REGISTRY_REPO = PROJECTS / "wat-registry"
REGISTRY_DB = REGISTRY_REPO / "registry.db"

sys.path.insert(0, str(REGISTRY_REPO))
from thairom import matchkey, similarity  # noqa: E402

# The register's own edition. Marks travel with the year they were read in,
# the same discipline honours.json keeps for royal grades.
SOURCE = ("ONAB temple register (ทะเบียนวัด สำนักงานพระพุทธศาสนาแห่งชาติ), "
          "B.E. 2567 — Open Government Data of Thailand")

PROVINCE_TH = {"cm": "เชียงใหม่", "cr": "เชียงราย"}

THAI = re.compile(r"[฀-๿]")
# A temple announces itself. Everything else on the wat shelf — ศาล, spirit
# houses, monastery guest halls, foundations — is not in the register.
IS_TEMPLE = re.compile(r"^\s*(วัด|wat\b)", re.IGNORECASE)

# Below this a candidate is reported, never accepted. Same value the
# manuscript join uses without a district to narrow on.
THRESHOLD = 0.86


def names(r: dict) -> tuple[str, str]:
    """(thai, latin) for a record, resolving the pair the way the site does."""
    name = r.get("name") or ""
    th = r.get("nameTh") or (name if THAI.search(name) else "")
    en = r.get("nameEn") or ("" if THAI.search(name) else name)
    return th, en


# อำเภอ / ตำบล as a record states them: an OSM addr field, or spelled out in
# the Thai description or the th.wikipedia article the crawl already fetched.
AMPHOE_RE = re.compile(r"อ(?:ำเภอ|\.)\s*([ก-๙]+)")
TAMBON_RE = re.compile(r"ต(?:ำบล|\.)\s*([ก-๙]+)")


def district_hints(r: dict) -> tuple[set[str], set[str]]:
    """(amphoe, tambon) match keys this record actually states. Never inferred
    from the pin — only read from a field or from prose the source wrote."""
    a = r.get("attrs") or {}
    amphoe = {a["district"]} if a.get("district") else set()
    tambon = {a["subdistrict"]} if a.get("subdistrict") else set()
    prose = " ".join(str(a.get(k) or "") for k in
                     ("article", "summary", "summaryEn", "description",
                      "descriptionTh")) + " " + (r.get("address") or "")
    amphoe |= set(AMPHOE_RE.findall(prose))
    tambon |= set(TAMBON_RE.findall(prose))
    return ({matchkey(x) for x in amphoe if x},
            {matchkey(x) for x in tambon if x})


def by_district(cands: list[dict], amphoe: set[str], tambon: set[str]) -> list[dict]:
    """Candidates whose อำเภอ or ตำบล answers to something the record states.

    เมืองเชียงใหม่ is written "เมือง" as often as in full, so an amphoe key is
    accepted when either contains the other — a prefix, not a fuzzy score.
    """
    if not (amphoe or tambon):
        return cands
    keep = []
    for t in cands:
        ka = matchkey(t.get("amphoe_th") or "")
        kt = matchkey(t.get("tambon_th") or "")
        hit_a = any(ka and h and (ka.startswith(h) or h.startswith(ka)) for h in amphoe)
        hit_t = any(kt and h and kt == h for h in tambon)
        if hit_a or hit_t:
            keep.append(t)
    return keep or cands


def load_registry() -> dict[str, list[dict]]:
    """Register rows for our two provinces, bucketed by province key."""
    con = sqlite3.connect(f"file:{REGISTRY_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out: dict[str, list[dict]] = {"cm": [], "cr": []}
    for prov, th in PROVINCE_TH.items():
        rows = con.execute(
            "SELECT code, name_th, name_key, rank, sect, founded_be, founded_ce,"
            "       wisung, wisung_date, tambon_th, amphoe_th, phone, website"
            "  FROM temples WHERE changwat_th = ? ORDER BY code", (th,)).fetchall()
        out[prov] = [dict(r) for r in rows]
    con.close()
    return out


def load_wats() -> list[dict]:
    wats = []
    for prov in ("cm", "cr"):
        path = ROOT / "data" / "canonical" / f"{prov}.json"
        for r in json.loads(path.read_text()):
            if "wat" in (r.get("cat") or []):
                wats.append(r)
    return sorted(wats, key=lambda r: r["id"])


def candidates(key: str, rows: list[dict]) -> list[dict]:
    """Register rows whose key is the same, else the near ones above threshold."""
    exact = [t for t in rows if t["name_key"] == key]
    if exact:
        return exact
    near = []
    for t in rows:
        s = similarity(key, t["name_key"] or "")
        if s >= THRESHOLD:
            near.append((s, t))
    near.sort(key=lambda x: (-x[0], x[1]["code"]))
    return [t for _s, t in near]


def entry(t: dict, how: str) -> dict:
    """The curated record. Empty register fields are dropped, not carried as
    empty strings — an absent founding year has to read as absent."""
    out = {"code": t["code"], "name_th": t["name_th"], "matched_how": how,
           "source": SOURCE}
    for field in ("rank", "sect", "wisung", "wisung_date",
                  "tambon_th", "amphoe_th", "phone", "website"):
        if t.get(field):
            out[field] = t[field]
    for field in ("founded_be", "founded_ce"):
        if t.get(field) is not None:
            out[field] = t[field]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N wat records (a dry look, not a mode)")
    args = ap.parse_args()

    if not REGISTRY_DB.exists():
        print(f"no register at {REGISTRY_DB} — nothing to join")
        return

    registry = load_registry()
    wats = load_wats()
    if args.limit:
        wats = wats[:args.limit]

    matched: dict[str, dict] = {}
    review: list[str] = []
    skipped_not_temple = 0
    no_candidate = 0

    for r in wats:
        th, en = names(r)
        display = " · ".join(x for x in (th, en) if x) or r["id"]
        if not (IS_TEMPLE.search(th) or IS_TEMPLE.search(en)):
            skipped_not_temple += 1
            continue
        rows = registry.get(r["province"]) or []
        key = matchkey(th or en)
        if not key:
            continue
        cands = candidates(key, rows)
        if not cands:
            no_candidate += 1
            continue
        narrowed, how_where = cands, "province"
        if len(cands) > 1:
            amphoe, tambon = district_hints(r)
            picked = by_district(cands, amphoe, tambon)
            if len(picked) < len(cands):
                narrowed, how_where = picked, "district"
        if len(narrowed) == 1:
            t = narrowed[0]
            how = f"{how_where}+" + ("exact" if t["name_key"] == key else "fuzzy")
            matched[r["id"]] = entry(t, how)
            continue
        # Two or more temples answer to this name inside the province and the
        # record states no district that tells them apart. A wrong code would
        # put another temple's founding year on this page.
        review.append(
            f"{r['id']}  {display}\n"
            f"    {len(narrowed)} temples of this name in {PROVINCE_TH[r['province']]}"
            f" — pin: {r.get('lat')},{r.get('lng')}\n"
            + "".join(
                f"      {t['code']}  {t['name_th']}  "
                f"ต.{t.get('tambon_th') or '?'} อ.{t.get('amphoe_th') or '?'}  "
                f"founded {t.get('founded_ce') or '?'}\n"
                for t in narrowed[:8])
        )

    out = {
        "note": ("Generated by importers/import_wat_registry.py from the ONAB "
                 "temple register. Rewritten wholesale on every run — put hand-"
                 "held corrections in another curated file, not this one. "
                 "Ambiguous names are in cache/wat_registry_review.txt and are "
                 "deliberately absent here."),
        "source": SOURCE,
        "wats": dict(sorted(matched.items())),
    }
    path = ROOT / "data" / "curated" / "wat_registry.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    cache = ROOT / "cache"
    cache.mkdir(exist_ok=True)
    rpath = cache / "wat_registry_review.txt"
    rpath.write_text(
        f"{len(review)} wat record(s) whose name answers to more than one temple\n"
        f"in the same province. Each needs a person to say which — an อำเภอ, a\n"
        f"look at the pin, or a walk past the gate. Nothing here is in\n"
        f"data/curated/wat_registry.json until it is settled.\n\n"
        + "\n".join(review), encoding="utf-8")

    dated = sum(1 for e in matched.values() if e.get("founded_ce"))
    print(f"wat registry: {len(matched)} of {len(wats)} wat records joined "
          f"({dated} with a founding year)")
    print(f"  {skipped_not_temple} not temples (shrines, spirit houses) — never matched")
    print(f"  {no_candidate} temples the register does not carry under that name")
    print(f"  {len(review)} ambiguous → {rpath.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
