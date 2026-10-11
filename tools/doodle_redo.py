#!/usr/bin/env python3
"""The doodles voted low, worst first: what the doodle topper redraws next.

Nan, 2026-10-05: "humans and bots … thumbs-up/thumbs-down doodles based on accuracy and
aesthetics. A new doodle for low scoring doodles should be prioritized." Then: "a flexible and
fuzzy scoring system, not discriminating between bots and humans."

Weighted votes come from tools/doodle_score.py. Only a doodle's latest version counts: a new
version starts at zero. Doodles drawn by one piece of code are pooled, because that code is what
gets redrawn:

    band:<set>[:<variant>]   front-page airings and scenes   → assets/front/<FILES[set]>
    place:<scene>            place portraits of one scene    → the same file
    cover:<kind>             cover drawings                  → assets/front/doodles.js
    minisite:<site>          a minisite's drawing            → that minisite's own repository

A pool's `low` on an axis (accuracy, aesthetics, and overall from picks of the better of two) is the
probability its drawing is below even there (doodle_score.score); its priority is the highest of the three. A pool at REDO_AT or above is due. The reasons printed under
it are what voters wrote: notes about a drawing, from strangers.

    python3 tools/doodle_redo.py            the pools due, worst first
    python3 tools/doodle_redo.py --all      every pool with a vote
    python3 tools/doodle_redo.py --json     the same, as JSON
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import doodlerepo_layer  # noqa: E402
import doodle_score  # noqa: E402

AXES = doodle_score.SCORE_AXES
REDO_AT = 0.8


def files():
    """doodler.js FILES: scene → the file that draws it (absent: doodler.js itself)."""
    src = (ROOT / "assets/front/doodler.js").read_text()
    m = re.search(r"var FILES = \{(.*?)\};", src, re.S)
    return dict(re.findall(r"'?([a-z0-9-]+)'?\s*:\s*'([^']+)'", m.group(1))) if m else {}


def pool(i, last, p, F):
    """(pool key, file to edit) for a doodle's latest version."""
    c, sub = last["c"], last.get("sub") or ""
    if c in ("front", "scene"):
        s, va = (p or {}).get("set") or sub, (p or {}).get("variant") or ""
        f = "assets/front/skyline.js" if s == "latin" else "assets/front/" + F.get(s, "doodler.js")
        return "band:" + s + (":" + va if va else ""), f
    if c == "place":
        return "place:" + sub, "assets/front/" + F.get(sub, "doodler.js")
    if c == "cover":
        return "cover:" + ((p or {}).get("k") or sub or i[2:]), "assets/front/doodles.js"
    return "minisite:" + sub, "~/Developer/claude code projects/%s/" % sub


def pools():
    W, why_down, *_ = doodle_score.weighted()
    vers, gone, params = doodlerepo_layer.load()
    F = files()
    out = {}
    for doc, w in W.items():
        i, _, v = doc.rpartition("@")
        vs = vers.get(i)
        if not vs or i in gone or str(vs[-1]["v"]) != v:
            continue   # a vote on an older version, or a doodle that has left
        last = vs[-1]
        k, f = pool(i, last, params.get(last["ph"]), F)
        P = out.setdefault(k, {"pool": k, "file": f, "doodles": [], "w": {a: [0.0, 0.0] for a in AXES}, "why": {a: [] for a in AXES}})
        P["doodles"].append((sum(w[a][1] - w[a][0] for a in AXES), i, last["v"]))
        for a in AXES:
            P["w"][a][0] += w[a][0]
            P["w"][a][1] += w[a][1]
            P["why"][a] += why_down.get(doc, {}).get(a, [])
    rows = []
    for P in out.values():
        r = {"pool": P["pool"], "file": P["file"], "n": len(P["doodles"]),
             "worst": [{"id": i, "v": v} for _, i, v in sorted(P["doodles"], key=lambda x: (-x[0], x[1]))[:3]]}
        for a in AXES:
            r[a] = doodle_score.score(*P["w"][a])
            r[a]["why"] = [w for _, w in sorted(P["why"][a], key=lambda x: -x[0])[:3]]
        r["priority"] = max(r[a]["low"] for a in AXES)
        r["due"] = r["priority"] >= REDO_AT
        rows.append(r)
    return sorted(rows, key=lambda r: (-r["priority"], r["pool"]))


def main(a):
    rows = pools()
    if "--all" not in a:
        rows = [r for r in rows if r["due"]]
    if "--json" in a:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    if not rows:
        print("no doodle is voted low" if "--all" not in a else "no votes yet")
        return
    for r in rows:
        ax = "  ".join("%s %.0f%% low (%.1f↑ %.1f↓)" % (x, 100 * r[x]["low"], r[x]["up"], r[x]["down"]) for x in AXES)
        print("%s%-30s %s  · %d doodle(s) · %s" % ("DUE " if r["due"] else "    ", r["pool"], ax, r["n"], r["file"]))
        for w in r["worst"]:
            print("      /doodles/d/?id=%s&v=%d" % (w["id"], w["v"]))
        for x in AXES:
            for w in r[x]["why"]:
                print("      %s down: %s" % (x, json.dumps(w[:140], ensure_ascii=False)))


if __name__ == "__main__":
    main(sys.argv[1:])
