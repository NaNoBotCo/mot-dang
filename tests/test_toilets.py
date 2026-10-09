"""The toilet minisite's bake: Nan's word (`stated` in data/toilets.json)
against a tier's habit and a field report.

    python3 tests/test_toilets.py

No build needed; bake() runs over a handful of records into a temp docs/.
"""
from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import toilets_layer as tl  # noqa: E402


def key_of(r):
    i = tl.said_index(r)
    return None if i is None else tl.SAID[i]["key"]


def test_her_word_matches_by_kind_and_by_place():
    if not tl.SAID:
        return "data/toilets.json carries no `stated`"
    assert key_of({"sub": ["fuel"], "name": "PTT Station"}) == "ptt"
    assert key_of({"sub": ["fuel"], "name": "Shell"}) is None
    assert key_of({"cat": ["sights", "wat"], "name": "วัดเจดีย์หลวง"}) == "wat"
    assert key_of({"cat": ["wat"], "name": "วัดร้างป่าแดด"}) is None
    assert key_of({"sub": ["pharmacy"], "name": "BIG C HANG DONG"}) == "bigc-makro"
    assert key_of({"name": "บิ๊กซีเอ็กซ์ตร้า เชียงใหม่"}) == "bigc-makro"
    assert key_of({"sub": ["cafe"], "name": "Big Coffee"}) is None          # a word, not a prefix
    assert key_of({"sub": ["tech"], "name": "BIG Camera"}) is None
    assert key_of({"name": "Mini Big C สาขาหายยา"}) is None
    assert key_of({"sub": ["hotel-full"], "attrs": {"rooms": 12}}) is None
    assert key_of({"sub": ["hotel-full"], "attrs": {"stars": 4}}) == "hotel"
    garden = [p["id"] for p in tl._STATED.get("places") or [] if p.get("id")]
    if garden:
        assert key_of({"id": garden[0], "sub": ["thai"], "name": "Garden Restaurant"}) == garden[0]


def bake(tmp: Path, recs, reports=None):
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    g = {"DOCS": tmp, "CLAIMS": {}, "PROVINCES": [{"key": "cm"}], "BUILD_DATE": "2026-09-23",
         "place_slug": lambda r: r["id"], "bi_text": lambda a, b: f"{a} · {b}",
         "LINE_OA_ID": "", "CLAIMS_WORKER_URL": "", "MOAT_POLY": []}
    orig = tl.load_reports
    tl.load_reports = lambda: reports or {}
    try:
        stats = tl.bake(g, {"cm": recs})
    finally:
        tl.load_reports = orig
    head = json.loads((tmp / "data" / "toilets.json").read_text())
    cust = json.loads((tmp / "data" / "toilets-customers.json").read_text())
    ix = {c: i for i, c in enumerate(head["columns"])}
    rows = {r[ix["id"]]: r for r in head["places"] + cust["places"]}
    return stats, head, rows, ix, {r[ix["id"]] for r in head["places"]}


def test_a_report_outranks_her_word_and_her_word_outranks_the_habit(tmp):
    if not tl.SAID:
        return "data/toilets.json carries no `stated`"
    at = {"lat": 18.787, "lng": 98.993, "geoPrecision": "exact"}
    recs = [
        {**at, "id": "w1", "cat": ["wat"], "name": "วัดหนึ่ง"},               # tier + her word
        {**at, "id": "w2", "cat": ["sights", "wat"], "name": "วัดสอง"},      # her word only
        {**at, "id": "w3", "cat": ["wat"], "name": "วัดสาม"},                # reported free
        {**at, "id": "w4", "cat": ["wat"], "name": "วัดสี่"},                # reported none
        {**at, "id": "f1", "sub": ["fuel"], "name": "Shell"},                # habit only
        {**at, "id": "c1", "sub": ["cafe"], "name": "Big Coffee"},           # habit only
    ]
    stats, head, rows, ix, walk = bake(tmp, recs, {"w3": {"report": "toiletfree"},
                                                   "w4": {"report": "toiletnone"}})
    said = lambda rid: rows[rid][ix["said"]]
    assert "w4" not in rows                                   # somebody stood there: none
    assert head["said"][said("w1")]["key"] == "wat" and rows["w1"][ix["tier"]] is not None
    assert head["said"][said("w2")]["key"] == "wat" and rows["w2"][ix["tier"]] is None
    assert "w2" in walk                                       # a kind she named walks in
    assert rows["w3"][ix["report"]] == "toiletfree"           # the report is what renders
    assert said("f1") is None and said("c1") is None
    assert stats["said"] == 2
    assert "x.kind==='s'" in tl.JS                         # the page renders her word


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            with tempfile.TemporaryDirectory() as d:
                skip = fn(Path(d)) if inspect.signature(fn).parameters else fn()
            print(f"  {'skip' if skip else 'ok  '} {name}" + (f" — {skip}" if skip else ""))
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}\n       {e!r}")
    print("all passed" if not failures else f"{failures} FAILED")
    sys.exit(1 if failures else 0)
