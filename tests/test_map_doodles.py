#!/usr/bin/env python3
"""Map doodles: every drawing keeps the contract, the manifest and the files agree, a place finds its doodle.

    python3 tests/test_map_doodles.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import map_doodles as md  # noqa: E402


def test_contract():
    bad = {i: md.check_one(md.SVG / (i + ".svg")) for i in md.ids()}
    bad = {i: b for i, b in bad.items() if b}
    assert not bad, bad


def test_manifest_matches_files():
    man = json.loads(md.MANIFEST.read_text())
    ids = [r["id"] for r in man]
    assert len(ids) == len(set(ids)), "an id twice in map-doodles.json"
    assert set(ids) == set(md.ids()), sorted(set(ids) ^ set(md.ids()))
    for r in man:
        assert r["group"] in ("landmark", "kind"), r["id"]
        assert r.get("en") and r.get("th"), r["id"]
        if r["group"] == "landmark":
            assert -90 <= r["lat"] <= 90 and -180 <= r["lng"] <= 180, r["id"]
        else:
            assert r.get("set"), r["id"]


def test_sprite_has_every_drawing():
    sprite = md.SPRITE.read_text()
    missing = [i for i in md.ids() if 'id="d-%s"' % i not in sprite]
    assert not missing, missing


def test_match():
    assert md.match({"amenity": "place_of_worship", "religion": "buddhist"}) == "buddhist-temple"
    assert md.match({"man_made": "lighthouse"}) == "lighthouse"
    assert md.match({"wikidata": "Q243"}) == "eiffel-tower"
    assert md.match({}, "wat") == "buddhist-temple"
    assert md.match({"shop": "nothing-like-this"}) is None
    for kind, i in md.MD_KINDS.items():
        assert (md.SVG / (i + ".svg")).exists(), (kind, i)


def test_js_table_matches_python():
    js = (md.SITE / "map-doodles.js").read_text()
    for kind, i in md.MD_KINDS.items():
        key = kind if kind.replace("-", "").isalpha() and "-" not in kind else "'%s'" % kind
        assert ("%s: '%s'" % (key, i)) in js, (kind, i)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
