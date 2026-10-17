#!/usr/bin/env python3
"""refile.py: gold shops, couriers, internet providers and the trades, moved to
the shelves a reader would open.

    python3 tests/test_refile.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import refile  # noqa: E402

FAILS = []


def t(name, fn):
    try:
        fn()
        print("  ok   " + name)
    except AssertionError as e:
        FAILS.append(name)
        print(f"  FAIL {name}\n       {e}")


def rec(name, cat, sub, oc=None):
    return {"id": "x-" + name, "name": name, "cat": list(cat), "sub": list(sub),
            "attrs": {"overtureCategory": oc} if oc else {}, "sources": []}


def run(*records):
    refile.apply(list(records), "cm", {}, "2026-10-17")
    return records


def _gold_leaves_crafts():
    g, silver, market = run(rec("ห้างทองเยาวราช", ["shopping"], ["crafts"], "jewelry_store"),
                            rec("Ponsawan Silver", ["shopping"], ["crafts"], "jewelry_store"),
                            rec("กาดทองคำ ย่านสันป่าข่อย", ["market"], ["fresh"]))
    assert g["sub"] == ["gold"], g["sub"]
    assert silver["sub"] == ["crafts"], silver["sub"]
    assert market["sub"] == ["fresh"], market["sub"]


def _gold_soft_word_needs_a_jewellery_category():
    a, b = run(rec("ทองแสงชัย", ["shopping"], ["crafts"], "jewelry_store"),
               rec("มังกรทอง", ["food"], [], "restaurant"))
    assert a["sub"] == ["gold"], a["sub"]
    assert b["sub"] == [] and b["cat"] == ["food"], b


def _courier_leaves_the_bus_shelf():
    j, noodle, cafe = run(rec("J&T Express สาขาพร้าว", ["transport"], ["bus"], "transportation"),
                          rec("เย็นตาโฟหน้าปณ.สารภี", ["food"], [], "thai_restaurant"),
                          rec("โรตีกาแฟและส่งพัสดุ", ["food"], [], "restaurant"))
    assert j["cat"] == ["essentials"] and j["sub"] == ["parcel"], j
    assert noodle["cat"] == ["food"] and noodle["sub"] == [], noodle
    assert cafe["cat"] == ["food", "essentials"] and cafe["sub"] == ["parcel"], cafe


def _kerry_off_post_thailand_post_stays():
    k, p = run(rec("Kerry Express", ["essentials"], ["post"], "freight_and_cargo_service"),
               rec("ที่ทำการไปรษณีย์ อมก๋อย", ["essentials"], ["post"], "post_office"))
    assert k["sub"] == ["parcel"], k["sub"]
    assert p["sub"] == ["post"], p["sub"]


def _internet_leaves_water_and_gas():
    a, g, h = run(rec("AIS Fibre เมืองเชียงราย", ["essentials"], ["utilities"], "internet_service_provider"),
                  rec("ชินแก๊ส", ["essentials"], ["utilities"]),
                  rec("ลายไทยเกสท์เฮาส์", ["hotel"], ["guesthouse"]))
    assert a["sub"] == ["internet"], a["sub"]
    assert g["sub"] == ["utilities"], g["sub"]
    assert h["sub"] == ["guesthouse"], h["sub"]


def _trades_join_and_keep_home():
    b, m, cafe = run(rec("รับสร้างบ้าน ตามงบประมาณ", ["repair"], ["home"]),
                     rec("พร้าววัสดุก่อสร้าง", ["repair"], ["home"]),
                     rec("กาแฟนายช่าง", ["repair"], ["home"], "electrician"))
    assert b["sub"] == ["home", "builder"], b["sub"]
    assert m["sub"] == ["home", "materials"], m["sub"]
    assert cafe["sub"] == ["home"], cafe["sub"]


def _idempotent():
    r = rec("Flash Home Express สาขาวัดศรีมูลเรือง", ["shopping"], ["mall"], "shopping")
    run(r)
    once = json.dumps(r, sort_keys=True)
    run(r)
    assert json.dumps(r, sort_keys=True) == once


def _shelves_exist():
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    have = {(c["key"], (ch.get("match") or {}).get("sub")) for c in cats["categories"]
            for ch in c.get("children", [])}
    for pair in [("shopping", "gold"), ("essentials", "parcel"), ("essentials", "internet"),
                 ("repair", "builder"), ("repair", "materials"),
                 ("repair", "electric-plumbing"), ("repair", "aircon")]:
        assert pair in have, pair


for name, fn in [
    ("a gold shop leaves crafts; silver and a market named ทองคำ do not", _gold_leaves_crafts),
    ("bare ทอง counts only on a jewellery shop", _gold_soft_word_needs_a_jewellery_category),
    ("a courier leaves the bus shelf; a shop beside the post office does not", _courier_leaves_the_bus_shelf),
    ("Kerry leaves post; Thailand Post stays", _kerry_off_post_thailand_post_stays),
    ("a fibre shop leaves water and gas; a gas shop and a guesthouse stay", _internet_leaves_water_and_gas),
    ("the trades join their shelf and keep repair/home", _trades_join_and_keep_home),
    ("the pass is idempotent", _idempotent),
    ("categories.json has each new child", _shelves_exist),
]:
    t(name, fn)

print(f"\n{len(FAILS)} failed" if FAILS else "\nall green")
sys.exit(1 if FAILS else 0)
