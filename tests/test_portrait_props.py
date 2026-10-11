"""Portrait props: tags → drawn props (doodles_layer.place_props, data/curated/portrait_props.json)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import doodles_layer  # noqa: E402

PROPS = json.loads((ROOT / "data/curated/portrait_props.json").read_text())["props"]
JS = (ROOT / "assets/front/doodler-props.js").read_text()


def test_drawn_props_have_drawers_and_drawers_have_rows():
    drawn = {k for k, p in PROPS.items() if p.get("drawn")}
    registered = set(re.findall(r"D\.addProp\('([a-z0-9-]+)'", JS))
    assert drawn == registered


def test_tags_call_for_drawn_props_only():
    r = {"id": "x", "cat": ["food"], "sub": ["cafe"], "name": "x"}
    assert doodles_layer.place_props(r, "cafe", ["open-late", "open-early"]) == ["lights", "rooster"]
    undrawn = next((p["tags"][0] for p in PROPS.values() if not p.get("drawn")), None)
    if undrawn:
        assert doodles_layer.place_props(r, "cafe", [undrawn]) == []


def test_not_scenes_and_facts():
    r = {"id": "x", "cat": ["transport"], "sub": ["parking"], "name": "x", "tags": ["parking"]}
    assert doodles_layer.place_props(r, "parking", ["parking"]) == []
    assert "props" not in doodles_layer.place_facts(r, scene="parking")
    assert doodles_layer.place_facts(r, scene="cafe")["props"] == ["parking"]


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("portrait props: all checks passed")
