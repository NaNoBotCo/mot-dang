#!/usr/bin/env python3
"""The games' shelves (sport_kind.py): badminton, football, tennis, basketball,
snooker, bowling, read off a sports place's own words.

    python3 tests/test_sport_kind.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sport_kind  # noqa: E402

FAILS = []


def t(name, fn):
    try:
        fn()
        print("  ok   " + name)
    except AssertionError as e:
        FAILS.append(name)
        print(f"  FAIL {name}\n       {e}")


def rec(name, sub=("sport",), cat=("sport",), **attrs):
    return {"id": "x-" + name, "name": name, "cat": list(cat), "sub": list(sub),
            "attrs": dict(attrs), "sources": []}


def run(*records):
    sport_kind.apply(list(records), "cm", {}, "2026-10-17")
    return records


def _thai_names():
    a, b, c = run(rec("สนามแบดมินตันวิทยุการบิน"), rec("สนามฟุตบอลหญ้าเทียม เพลินเพลย์"),
                  rec("สันกำแพงสนุกเกอร์&พูล"))
    assert a["sub"] == ["badminton"], a["sub"]
    assert b["sub"] == ["football"], b["sub"]
    assert c["sub"] == ["snooker"], c["sub"]
    assert a["attrs"]["sportVia"]["badminton"].startswith("name:"), a["attrs"]


def _two_games_two_shelves():
    r, = run(rec("แม่ริมสนุกเกอร์ & แม่ริมฟุตบอลคลับ"))
    assert r["sub"] == ["football", "snooker"], r["sub"]


def _directory_category_files_a_quiet_name():
    r, = run(rec("Chiangrai Bowl", overtureCategory="bowling_alley"))
    assert r["sub"] == ["bowling"], r["sub"]


def _osm_sport_tag():
    r, = run(rec("Lanna Courts", sportTag="soccer;basketball"))
    assert r["sub"] == ["football", "basketball"], r["sub"]
    assert sport_kind.osm_kinds({"leisure": "bowling_alley"}) == ["bowling"]
    assert sport_kind.osm_kinds({"leisure": "pitch", "sport": "boules"}) == []


def _gym_moves_only_on_its_name():
    named, quiet = run(rec("D-Home badminton sport&fitness", sub=("gym",)),
                       rec("Iron Gym", sub=("gym",), overtureCategory="badminton_court"))
    assert named["sub"] == ["gym", "badminton"], named["sub"]
    assert quiet["sub"] == ["gym"], quiet["sub"]


def _table_tennis_is_not_tennis():
    r, = run(rec("ชมรมเทเบิลเทนนิสเชียงใหม่"))
    assert r["sub"] == ["sport"], r["sub"]


def _turf_seller_is_not_a_pitch():
    r, = run(rec("จัดสวน หญ้าเทียม เชียงใหม่"), )
    assert r["sub"] == ["sport"], r["sub"]
    s, = run(rec("ร้านขายอุปกรณ์แบดมินตัน"))
    assert s["sub"] == ["sport"], s["sub"]


def _muay_thai_and_golf_left_alone():
    g, m = run(rec("Gassan Football Golf", sub=("golf",)),
               rec("Football Muay Thai Camp", cat=("sport", "muaythai"), sub=("camp",)))
    assert g["sub"] == ["golf"], g["sub"]
    assert m["sub"] == ["camp"], m["sub"]


def _idempotent():
    r = rec("CNX Badminton Court")
    run(r)
    once = json.dumps(r, sort_keys=True)
    run(r)
    assert json.dumps(r, sort_keys=True) == once


def _shelves_exist():
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    sport = next(c for c in cats["categories"] if c["key"] == "sport")
    keys = {ch["key"]: ch["match"] for ch in sport["children"]}
    for k in sport_kind.KINDS:
        assert keys.get(k) == {"sub": k}, (k, keys.get(k))


for name, fn in [
    ("Thai names file their game", _thai_names),
    ("a place for two games is on both shelves", _two_games_two_shelves),
    ("a directory category files a name that says no game", _directory_category_files_a_quiet_name),
    ("OSM's sport tag files a pitch; boules is not bowling", _osm_sport_tag),
    ("a gym joins a game's shelf only on its own name", _gym_moves_only_on_its_name),
    ("table tennis is not tennis", _table_tennis_is_not_tennis),
    ("a turf fitter or a gear shop is not a court", _turf_seller_is_not_a_pitch),
    ("muay thai and golf keep their own shelves", _muay_thai_and_golf_left_alone),
    ("the pass is idempotent", _idempotent),
    ("categories.json has a child for each game", _shelves_exist),
]:
    t(name, fn)

print(f"\n{len(FAILS)} failed" if FAILS else "\nall green")
sys.exit(1 if FAILS else 0)
