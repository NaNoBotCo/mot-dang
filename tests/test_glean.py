#!/usr/bin/env python3
"""glean.py routes what listers send to every destination it fits.

Runs on a handful of made-up Mot Dang records and listing rows written into a
temp dir; reads listing-sheet's own loader and resolve.py. Writes nothing
inside mot-dang.

    python3 tests/test_glean.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import facts  # noqa: E402
import glean  # noqa: E402

FAIL = []


def check(cond, why):
    if not cond:
        FAIL.append(why)


def rec(rid, name, sub, lat=None, lng=None, cat="realestate", **attrs):
    return {"id": rid, "province": "cm", "cat": [cat], "sub": [sub], "name": name,
            "nameTh": name if glean._is_thai(name) else None, "nameEn": None,
            "lat": lat, "lng": lng, "geoPrecision": "exact" if lat else "needs-pin",
            "attrs": dict(attrs), "sources": [{"type": "osm", "ref": "x", "fetched": "2026-08-01"}],
            "provenance": {}}


RECORDS = [
    rec("cm-condo-a", "ปันนา เรสซิเดนซ์", "condo", 18.8000, 98.9600,
        tambon="สุเทพ", amphoe="เมืองเชียงใหม่", buildingLevels="8"),
    rec("cm-condo-b", "Hill Tower Condo", "condo", tambon="ช้างเผือก"),
    rec("cm-condo-c", "ฟลอร่า คอนโด", "condo", 18.8200, 98.9700, tambon="ช้างเผือก"),
    rec("cm-seven", "7-Eleven Test", "convenience", 18.7700, 98.9800, cat="shopping"),
    rec("cm-agent", "Ping Valley Property", "agent", 18.7000, 98.9000),
]


def row(name, kind, agency, price, *, lat=None, lng=None, tambon="สุเทพ", offer="sale",
        facets=None, licence=None, photos=None, unit=None, cite="agency export 2026-09"):
    prop = {"name": name, "kind": kind, "province": "cm",
            "amphoe": "Mueang Chiang Mai", "address": f"{tambon or ''}, Mueang Chiang Mai"}
    if tambon:
        prop["tambon"] = tambon
    if lat is not None:
        prop["lat"], prop["lng"] = lat, lng
    if unit:
        prop["unit"] = unit
    if photos:
        prop["photos"] = photos
    src = {"cite": cite}
    if licence:
        src["licence"] = licence
    return {"property": prop,
            "offer": {"type": offer, "price_thb": price, "as_of": "2026-09-01", "status": "live"},
            "agency": {"name": agency, "contact": "office@example.com"},
            "source": src, "facets": facets or {}}


def rows():
    A = dict(lat=18.8000, lng=98.9601)      # ~10 m from cm-condo-a
    return {
        "a1": row("Punna Residence", "condo", "Northern Homes", 3_000_000, unit="101",
                  licence="CC BY 4.0", photos=["a.jpg"], **A,
                  facets={"bedrooms": 1, "floors": 12, "floor_level": 3, "year_built": 2015,
                          "juristic_name": "Punna Juristic Person",
                          "juristic_contact": "053-123456", "short_lets": "allowed",
                          "foreign_quota": "open",
                          "services": ["shared_pool", "lift", "aircon", "balcony", "gym"]}),
        "a2": row("Punna Residence", "condo", "Ping Valley Property", 3_400_000, unit="202",
                  photos=["b.jpg"], **A,
                  facets={"bedrooms": 1, "year_built": 2015, "short_lets": "not_allowed",
                          "services": ["lift", "fridge"]}),
        "a3": row("Punna Residence", "condo", "Lanna Land", 3_200_000, unit="303", **A,
                  facets={"bedrooms": 1}),
        "a4": row("Punna Residence", "condo", "Lanna Land", 12_000, unit="404", offer="rent",
                  **A, facets={"bedrooms": 2}),
        "b1": row("Hill Tower Condo", "condo", "Lanna Land", 2_000_000, tambon=None,
                  lat=18.8100, lng=98.9650, facets={"bedrooms": 1}),
        "c1": row("Flora Condo", "condo", "Lanna Land", 1_900_000, tambon=None,
                  lat=18.8200, lng=98.9701, facets={"bedrooms": 1}),
        # Latin tambon beside a Thai one: resolve.py binds it by its pin (a
        # tambon refuses only within one script, 2026-09-27)
        "p1": row("Punna Residence", "condo", "Lanna Land", 3_100_000, unit="505",
                  tambon="Su Thep", facets={"bedrooms": 1}, **A),
        "h1": row("Garden House", "house", "Northern Homes", 5_000_000, tambon=None,
                  lat=18.7700, lng=98.9801,
                  facets={"bedrooms": 3, "juristic_name": "Some Estate",
                          "services": ["garden", "security"]}),
        "u1": row("Nowhere Tower", "condo", "Lanna Land", 1_500_000, tambon="Nong Pa Khrang",
                  lat=18.7900, lng=99.0300, facets={"bedrooms": 1}),
        "u2": row("Unpinned Court", "condo", "Lanna Land", 1_400_000, tambon="Pa Daet",
                  facets={"bedrooms": 1}),
    }


def fake_locate(address, province):
    return {"lat": 18.75, "lng": 98.98, "precision": "tambon", "uncertainty_m": 2500,
            "via": "test", "matched": address}


def setup(td, which=None, sample_row=False):
    td = Path(td)
    lst = td / "listings"
    lst.mkdir(parents=True, exist_ok=True)
    rs = rows()
    for k, r in rs.items():
        if which is None or k in which:
            (lst / f"{k}.json").write_text(json.dumps(r), encoding="utf-8")
    if sample_row:
        s = row("Invented", "condo", "Sample Agency", 999_999, lat=18.9, lng=98.9,
                cite="INVENTED SAMPLE ROW — not a real offer")
        (lst / "zz-sample.json").write_text(json.dumps(s), encoding="utf-8")
    cur = td / "curated"
    cur.mkdir(exist_ok=True)
    return lst, cur


def make_ctx(td, lst, cur, records=None, sample=False, out=None, photos=None):
    td = Path(td)
    return glean.Context(copy.deepcopy(records or RECORDS), lst, out or td / "gleaned",
                         td / "incoming", curated_dir=cur, locate=fake_locate,
                         sample=sample, today="2026-09-27",
                         claims_path=td / "no-claims.json", photos_dir=photos or td / "photos")


def put_photos(td):
    """Write a.jpg and b.jpg where listing-sheet keeps them, by raw id."""
    sys.path.insert(0, str(glean.LS_ROOT))
    import sheet
    rs = rows()
    for k, n in (("a1", "a.jpg"), ("a2", "b.jpg")):
        p = dict(rs[k]["property"])
        d = Path(td) / "photos" / sheet.derive_id(p)
        d.mkdir(parents=True, exist_ok=True)
        (d / n).write_bytes(b"jpg")


def main():
    # 0. every listing-sheet service code has a side
    sys.path.insert(0, str(glean.LS_ROOT))
    import facets as LSF
    missing = sorted(set(LSF.SERVICES) - set(glean.SERVICE_SPLIT))
    check(not missing, f"SERVICE_SPLIT lacks {missing}")
    check(set(glean.ROUTES) >= {"asking_price", "photo", "pin", "amenity", "unbound"},
          "ROUTES lacks a listing field")

    with tempfile.TemporaryDirectory() as td:
        lst, cur = setup(td, sample_row=True)
        put_photos(td)
        ctx = make_ctx(td, lst, cur)
        res = glean.run(ctx)
        f = res["facts"]
        rv = res["review"]

        # 1. sample rows are refused outside --sample, and never written
        check(ctx.refused_samples == 1, f"sample row not refused: {ctx.refused_samples}")
        check(not any(glean.is_sample(r) for r in ctx.rows), "a sample row was kept")
        ledger = (Path(td) / "gleaned" / "ledger.jsonl").read_text(encoding="utf-8")
        check("Invented" not in ledger and "999999" not in ledger, "sample row in the ledger")

        # 2. unit-level fields never land on a building
        a = f.get("cm-condo-a", {})
        am = (a.get("amenities") or {}).get("value") or []
        check(set(am) == {"shared_pool", "lift", "gym"}, f"building amenities wrong: {am}")
        for ref, fs in f.items():
            for field in fs:
                check(field in facts.BUILDING_FIELDS or field == "pin",
                      f"{ref}.{field} is not a building field")
        check("cm-seven" not in f, "a house row's facts reached a 7-Eleven")
        check(not any(e["record"] == "cm-seven" for e in rv["off_shelf_binds"]),
              "resolve.py bound a house listing to a 7-Eleven")
        check(a.get("juristic_phone", {}).get("value") == "053123456", f"juristic phone: {a}")
        check(a.get("foreign_quota", {}).get("value") == {"status": "open", "as_of": "2026-09-01"},
              "foreign quota not dated")
        yb = a.get("year_built") or {}
        check(yb.get("value") == 2015 and {yb.get("source")} | set(yb.get("also") or [])
              == {"lister:northern-homes", "lister:ping-valley-property"},
              f"two listers agreeing on the year: {yb}")

        # 3. conflicts and disagreements go to a person
        check("storeys" not in a, "a storeys value that disagrees with the record was written")
        check(any(c["field"] == "storeys" and c["building"] == "cm-condo-a" for c in rv["conflicts"]),
              "the storeys conflict is not in review")
        check("short_lets" not in a, "short_lets written while listers disagree")
        check(any(d["field"] == "short_lets" for d in rv["lister_disagreements"]),
              "lister disagreement not in review")

        # 4. a pin for a building with none, and not for one that has one
        check(f.get("cm-condo-b", {}).get("pin", {}).get("value") == [18.81, 98.965],
              f"pin for unpinned building: {f.get('cm-condo-b')}")
        check("pin" not in a, "a pinned building got a pin")

        # 5. price cells under three withheld
        cells = res["prices"]["cells"]
        check(all(c["n"] >= glean.MIN_CELL for c in cells), "a cell under 3 was published")
        hit = [c for c in cells if c["tambon"] == "สุเทพ" and c["offer"] == "sale"
               and c["bedrooms"] == "1"]
        check(len(hit) == 1 and hit[0]["n"] == 4 and hit[0]["median"] == 3_150_000,
              f"สุเทพ 1-bed sale cell wrong: {hit}")
        check(res["prices"]["withheld"]["cells"] >= 3, f"withheld count: {res['prices']['withheld']}")
        check("3000000" not in json.dumps(res["prices"]) and "12000" not in json.dumps(res["prices"]),
              "a single listing's price is in prices.json")

        # 6. licence gate on pictures
        pics = res["pictures"].get("cm-condo-a") or []
        check(len(pics) == 1 and pics[0]["src"].endswith("/a.jpg")
              and pics[0]["licence"] == "CC BY 4.0", f"pictures: {pics}")

        # 7. building summary
        b = res["buildings"].get("cm-condo-a") or {}
        o = b.get("offers") or {}
        check(o.get("live") == 5 and o.get("sale_thb") == [3_000_000, 3_400_000]
              and o.get("rent_month_thb") == [12_000, 12_000], f"offers: {o}")
        check(b.get("pictures") == pics and "juristic_name" in b.get("facts", {}),
              "summary lacks facts or pictures")

        # 8. unbound rows go to review with a precision tier
        ub = {u["name"]: u for u in rv["unbound_buildings"]}
        check(ub.get("Nowhere Tower", {}).get("point", {}).get("precision") == "lister-pin",
              f"unbound pinned row: {ub.get('Nowhere Tower')}")
        check(ub.get("Unpinned Court", {}).get("point", {}).get("precision") == "tambon",
              f"unbound unpinned row: {ub.get('Unpinned Court')}")
        check("Garden House" not in ub, "a house went to review as a building")

        # 9. agencies, tambon pairs, brand candidates
        off = {x["slug"] for x in rv["agencies_off_shelf"]}
        check(off == {"northern-homes", "lanna-land"}, f"agencies off shelf: {off}")
        tp = {(p["latin"], p["thai"]) for p in rv["tambon_pairs"]}
        check(tp == {("Su Thep", "สุเทพ")}, f"pairs: {tp}")
        check(all(p["reading_agrees"] for p in rv["tambon_pairs"]), "Suthep reading disagrees")
        check("Punna Residence" not in ub,
              f"the Latin-tambon row stayed unbound: {ub.get('Punna Residence')}")
        check(any(b["sign"] == "flora" for b in rv["brand_candidates"]),
              f"brand candidates: {rv['brand_candidates']}")

        # 10. the ledger names a destination for every observation
        lines = [json.loads(x) for x in ledger.splitlines()]
        check(len(lines) == len(res["router"].obs), "ledger line count != observations")
        dests = {glean.FACTS, glean.PRICES, glean.PICTURES, glean.BUILDINGS,
                 glean.REVIEW, glean.LISTING}
        check(all(ln["went"] and all(w["to"] in dests for w in ln["went"]) for ln in lines),
              "a ledger line with no destination")

        # 11. idempotent: a second run writes nothing and changes no byte
        before = {p: p.read_bytes() for p in Path(td).rglob("*") if p.is_file()
                  and "listings" not in p.parts}
        ctx2 = make_ctx(td, lst, cur)
        res2 = glean.run(ctx2)
        after = {p: p.read_bytes() for p in before}
        check(res2["written"] == [], f"second run wrote {res2['written']}")
        check(before == after, "second run changed a file")

        # 12. gleaned facts apply through facts.load_all beside a reader's
        (cur / "facts.json").write_text(json.dumps({"facts": {"cm-condo-a": {
            "phone": {"value": "0811111111", "at": "2026-09-06", "suggestion": "s1"},
            "year_built": {"value": 2014, "at": "2026-09-06", "suggestion": "s2"}}}}))
        doc = facts.load_all(cur)
        fa = doc["facts"]["cm-condo-a"]
        check(fa["phone"]["value"] == "0811111111" and "juristic_name" in fa,
              "load_all did not merge both files")
        check(fa["year_built"]["value"] == 2014, "load_all let a gleaned fact over a reader's")
        recs = copy.deepcopy(RECORDS)
        n = facts.apply(recs, doc)
        r = recs[0]
        check(r.get("phone") == "0811111111", "reader fact did not apply")
        check(r["attrs"].get("juristicName") == "Punna Juristic Person", "gleaned fact did not apply")
        check(r["attrs"].get("buildingLevels") == "8", "a gleaned fact overwrote the record")
        check(r["attrs"]["gleanedFacts"]["juristic_name"]["source"] == "lister:northern-homes",
              "gleaned provenance is not lister:<agency>")
        check("juristic_name" not in r["attrs"].get("readerFacts", {}),
              "a gleaned fact wears the reader badge")
        check(any(s.get("type") == "lister" and s.get("via") == "northern-homes"
                  for s in r["sources"]), "no lister sources[] entry")
        rb = recs[1]
        check([rb["lat"], rb["lng"]] == [18.81, 98.965] and rb["attrs"]["pinVia"] == "lister-supplied",
              "gleaned pin did not apply")
        import provenance
        check(provenance.validate(rb) == [], f"provenance rejects the pin: {provenance.validate(rb)}")
        check(facts.apply(recs, doc) == 0, "second apply changed something")
        check(n >= 5, f"apply set {n}")
        # a gleaned fact meeting a different value already on the record
        clash = copy.deepcopy(RECORDS)
        clash[0]["attrs"]["juristicName"] = "Another Office"
        facts.apply(clash, doc)
        check(clash[0]["attrs"]["juristicName"] == "Another Office",
              "apply overwrote a record value with a gleaned one")
        # a later gleaned value replaces an earlier gleaned one
        later = copy.deepcopy(doc)
        later["facts"]["cm-condo-a"]["juristic_name"] = dict(
            later["facts"]["cm-condo-a"]["juristic_name"], value="Renamed Office", at="2026-09-20")
        facts.apply(recs, later)
        check(recs[0]["attrs"]["juristicName"] == "Renamed Office",
              "a later gleaned fact did not replace the earlier one")

    # 13. dry run writes nothing; the claims adapter logs fields, not values
    with tempfile.TemporaryDirectory() as td:
        lst, cur = setup(td, which={"a1"})
        (Path(td) / "claims.json").write_text(json.dumps({"claims": {"cm-condo-a": {
            "placeId": "cm-condo-a", "phone": "0899999999", "hours": "Mo-Su 08:00-20:00",
            "updatedAt": "2026-09-20T00:00:00Z"}}}))
        ctx = make_ctx(td, lst, cur)
        ctx.claims_path = Path(td) / "claims.json"
        res = glean.run(ctx, dry_run=True)
        check(res["written"] == [] and not (Path(td) / "gleaned").exists()
              and not (cur / facts.GLEANED_FILE).exists(), "dry run wrote a file")
        cl = [o for o in res["router"].obs.values() if o["field"] == "claim"]
        check(sorted(o["value"] for o in cl) == ["hours", "phone"], f"claims: {cl}")
        check("0899999999" not in json.dumps(glean.ledger_lines(ctx, res["router"])),
              "a claimed phone number was copied into the ledger")

    # 14. samples cannot be written inside mot-dang
    with tempfile.TemporaryDirectory() as td:
        lst, cur = setup(td, which={"a1"}, sample_row=True)
        ctx = make_ctx(td, lst, cur, sample=True, out=ROOT / "data" / "gleaned")
        try:
            glean.run(ctx, sources=("listings",), dry_run=True)
            check(False, "sample rows ran with output inside mot-dang")
        except glean.SampleRowRefused:
            pass
        ctx = make_ctx(td, lst, cur, sample=True)
        ctx.facts_out = ROOT / "data" / "curated" / facts.GLEANED_FILE
        try:
            glean.run(ctx, sources=("listings",))
            check(False, "sample rows written to data/curated")
        except glean.SampleRowRefused:
            pass
        out = subprocess.run([sys.executable, str(ROOT / "glean.py"), "--sample", "--no-register",
                              "--out", str(ROOT / "data" / "glean-scratch")],
                             capture_output=True, text=True)
        check(out.returncode != 0 and "SampleRowRefused" in out.stderr,
              "CLI took --out inside mot-dang for samples")
        check(not (ROOT / "data" / "glean-scratch").exists(), "CLI created a dir inside mot-dang")

    if FAIL:
        print("\n".join(FAIL))
        print(f"FAIL: {len(FAIL)}")
        return 1
    print("OK: glean routes building facts, prices, pictures, summaries, review and ledger; "
          "samples stay out of data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
