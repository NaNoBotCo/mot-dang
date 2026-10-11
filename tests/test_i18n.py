#!/usr/bin/env python3
"""Burmese and Shan dictionaries (WO-112): data/i18n/{my,shn}.json against data/i18n/base.json.

    python3 tests/test_i18n.py

Hard: every dictionary id is in base.json; every slot in the English ({n}, {x1}) is in the translation, and
the translation holds no slot the English lacks (a slot written straight after a letter, "offer{x2}", is a
plural ending and may be left out); a translation holds letters of the Myanmar block (U+1000-109F) unless the
translation is the English kept as it is (a brand word, a unit, a pair of slots), and no Thai letters; the served file in i18n_layer is well formed.
Advisory: ids in base.json with no translation; base strings no longer written in the layers.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import i18n_layer as il  # noqa: E402

bad, note = [], []


def check(name, ok, why=""):
    if not ok:
        bad.append(name + (" — " + why if why else ""))


base = il.load_base()
ids = [k for k in base if not k.startswith("_")]
check("base.json has strings", len(ids) > 2000, str(len(ids)))
for sid in ids:
    row = base[sid]
    check("base %s has th and en" % sid, bool(row.get("th", "").strip()) and bool(row.get("en", "").strip()))

MYANMAR = re.compile("[က-႟]")
THAI = re.compile("[฀-๿]")

for lang in il.LANGS:
    tr = il.load_lang(lang)
    keys = [k for k in tr if not k.startswith("_")]
    missing = [k for k in keys if k not in base]
    check("%s: every key is in base.json" % lang, not missing, ", ".join(missing[:5]))
    for sid in keys:
        if sid not in base:
            continue
        en, val = base[sid]["en"], tr[sid]
        check("%s %s is text" % (lang, sid), isinstance(val, str) and val.strip() != "")
        if not isinstance(val, str):
            continue
        want, got = il.slots(en), il.slots(val)
        optional = il.suffix_slots(en)
        lacks = [s for s in want if s not in got and s not in optional]
        extra = [s for s in got if s not in want]
        check("%s %s slots match" % (lang, sid), not lacks and not extra,
              "English %s, translation %s" % (want, got))
        check("%s %s has no Thai letters" % (lang, sid), not THAI.search(val), val)
        check("%s %s has Myanmar-block letters" % (lang, sid),
              bool(MYANMAR.search(val)) or val.strip() == en.strip(),
              "%s -> %s" % (en, val))
    untr = [k for k in ids if k not in tr]
    if untr:
        note.append("%s: %d of %d base strings have no translation yet" % (lang, len(untr), len(ids)))
    d = il.served(lang, base, tr)
    check("%s served file has e, t, p" % lang, set(d) == {"lang", "e", "t", "p"} and d["lang"] == lang)
    n = len(d["e"]) + len(d["t"]) + len(d["p"])
    check("%s served file holds most of the dictionary" % lang, n > 0.9 * len(keys), "%d of %d" % (n, len(keys)))
    for en, val in d["e"].items():
        check("%s served e entry %r has no slot" % (lang, en), not il.SLOT.search(en))
    for k in d["t"]:
        check("%s served t key has the separator" % lang, il.SEP in k)

# advisory: how much of base.json is still written in the layers (the strings drift as pages change)
src = ""
for p in list(ROOT.glob("*.py")) + [ROOT / "data" / "categories.json", ROOT / "data" / "facets.json", ROOT / "data" / "tags.json"]:
    try:
        src += p.read_text(encoding="utf-8") + "\n"
    except OSError:
        pass
gone = [k for k in ids if base[k]["en"].split("{")[0].strip() and base[k]["en"].split("{")[0].strip() not in src]
if gone:
    note.append("%d base strings no longer appear in the layers (e.g. %s)" % (len(gone), ", ".join(gone[:4])))

for n in note:
    print("note: " + n)
print("i18n: %s" % ("ok" if not bad else "%d failing" % len(bad)))
for b in bad[:40]:
    print("FAIL  " + b)
sys.exit(1 if bad else 0)
