#!/usr/bin/env python3
"""Ground truth for the doodler: the pictures of what each drawing draws, and its rank by them.

Nan, 2026-10-12: "do groundtruthing in support of the doodler, and prioritize items with more ground
truth." Then: "Ground truth is the new backlinks."

A drawing pool is what doodle_redo.py redraws: place:<scene> (the place portraits one scene draws),
band:<set> (a front-band scene) and sight:<name> (a landmark the skyline, the band, the doodle map
or the map doodles draw). Its ground truth is every picture of its subject on disk, weighed by who
took it:

    own     her own photographs tied to a place (data/curated/own_pictures.json)   × 3
    field   her ride captures by kind (data/curated/field_points.json)              × 2
    street  street-level photographs per place (data/street_photos.json, own_photos.json)  × 1
    commons Wikimedia Commons per place (data/commons_images.json) and the topic pools
            (data/curated/commons_pool.json, image_picks.json), matched by the scene's own words × 1

A place portrait counts the pictures of the places that scene draws; a band scene the pictures whose
title or description its words take (the doodler's own setOf); a sight the pictures of its record.
`score` is the weighted count; `refs` the best dozen to open before drawing: hers first.

    python3 tools/doodle_truth.py                write data/curated/doodle_truth.json, print the top
    python3 tools/doodle_truth.py --show 30      print more
    python3 tools/doodle_truth.py --pool place:wat   one pool's refs
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import doodles_layer  # noqa: E402

OUT = ROOT / "data/curated/doodle_truth.json"
W = {"own": 3, "field": 2, "street": 1, "commons": 1}
REFS = 12
FIELD_SCENE = {"spirit-house": "place:spirithouse", "market": "place:freshmarket", "street-art": "band:studio"}


def _j(p, default=None):
    p = ROOT / p
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return default


def records():
    for prov in ("cm", "cr"):
        rows = _j(f"data/canonical/{prov}.json", []) or []
        for r in rows if isinstance(rows, list) else rows.get("records", []):
            yield r


# the doodler's setOf over picture titles, with every scene file loaded (as tools/art_check.py)
NODE = r"""
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm';
const FRONT = process.argv[2], noop = () => {};
const ctx = { window: { MDSKY: { paper: noop, jag: noop, circ: noop, grain: noop, sights: { cm: [], cr: [] }, landscape: () => [] } }, console, Date, Math };
ctx.window.window = ctx.window; vm.createContext(ctx);
const files = ['doodler.js', ...fs.readdirSync(FRONT).filter(f => /^doodler-.*\.js$/.test(f)).sort()];
for (const f of files) vm.runInContext(fs.readFileSync(path.join(FRONT, f), 'utf8'), ctx, { filename: f });
const D = ctx.window.MDDOODLER, T = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
process.stdout.write(JSON.stringify(T.map(t => { const s = D.setOf({ t: t, v: '', c: '' }); return s === 'social' ? '' : s; })));
"""


def band_sets(titles):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as a, tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as b:
        json.dump(titles, a)
        b.write(NODE)
    try:
        r = subprocess.run(["node", b.name, str(ROOT / "assets/front"), a.name], capture_output=True, text=True, timeout=300, check=True)
        return json.loads(r.stdout)
    finally:
        os.unlink(a.name)
        os.unlink(b.name)


def build():
    pools = {}

    def add(pool, kind, ref):
        p = pools.setdefault(pool, {"own": 0, "field": 0, "street": 0, "commons": 0, "refs": []})
        p[kind] += 1
        p["refs"].append(dict(ref, kind=kind))

    scene_of, name_of = {}, {}
    for r in records():
        s = doodles_layer.place_scene(r)
        if s:
            scene_of[r["id"]] = s
        name_of[r["id"]] = r.get("nameEn") or r.get("name") or ""

    # her own photographs, by the place they show
    for p in (_j("data/curated/own_pictures.json", {}) or {}).get("picks", []):
        if p.get("usable") not in (True, "True"):
            continue
        ids = {p.get("placeId"), *(p.get("places") or [])} - {None, ""}
        for pid in ids:
            if pid in scene_of:
                add("place:" + scene_of[pid], "own", {"title": p.get("title", ""), "file": "assets/" + p.get("file", ""), "place": pid})
    # her ride captures, by kind
    for p in (_j("data/curated/field_points.json", {}) or {}).get("points", []):
        pool = FIELD_SCENE.get(p.get("kind"))
        if pool:
            add(pool, "field", {"title": p.get("title", ""), "file": p.get("photo", ""), "lat": p.get("lat"), "lng": p.get("lng")})
    # street-level and Commons photographs per place
    for f in ("data/own_photos.json", "data/street_photos.json"):
        for pid, ph in ((_j(f, {}) or {}).get("photos") or {}).items():
            if pid in scene_of:
                add("place:" + scene_of[pid], "street", {"title": name_of.get(pid, ""), "url": ph.get("url") or ph.get("file", ""), "place": pid})
    for pid, ci in ((_j("data/commons_images.json", {}) or {}).get("images") or {}).items():
        if pid in scene_of:
            add("place:" + scene_of[pid], "commons", {"title": ci.get("title", ""), "url": ci.get("thumb", ""), "place": pid})
    # band scenes: pictures whose words the scene takes
    pics = []
    for f in ("data/curated/commons_pool.json", "data/curated/image_picks.json", "data/curated/own_pictures.json"):
        for p in (_j(f, {}) or {}).get("picks", []):
            pics.append(p)
    titles = [" ".join(str(p.get(k) or "") for k in ("title", "description", "description_th")).replace("File:", "")[:300] for p in pics]
    for p, s in zip(pics, band_sets(titles)):
        if s:
            own = p.get("artist") == "NaN Peacock"
            add("band:" + s, "own" if own else "commons", {"title": p.get("title", ""), "url": p.get("thumb") or p.get("src") or "",
                                                           "file": ("assets/" + p["file"]) if own and p.get("file") else ""})
    # sights: the records of the landmarks art_check.py finds drawn by more than one engine
    try:
        import art_check
        for line in art_check.hands():
            subj = line.split(":")[0]
            words = [w for w in subj.split() if len(w) > 2]
            if len(words) < 2:   # "gate" alone names no one place
                continue
            for pid, nm in name_of.items():
                if words and all(re.search(r"\b" + re.escape(w) + r"\b", nm, re.I) for w in words):
                    for p in pools.get("place:" + scene_of.get(pid, "-"), {}).get("refs", []):
                        if p.get("place") == pid:
                            add("sight:" + subj, p["kind"], p)
                    ci = ((_j("data/commons_images.json", {}) or {}).get("images") or {}).get(pid)
                    if ci:
                        add("sight:" + subj, "commons", {"title": ci.get("title", ""), "url": ci.get("thumb", ""), "place": pid})
    except Exception as e:   # the sights are a bonus; the rest stands without them
        print("sights skipped:", e)

    out = {}
    for pool, p in pools.items():
        refs = sorted(p["refs"], key=lambda r: -W[r["kind"]])
        seen, keep = set(), []
        for r in refs:
            k = r.get("file") or r.get("url") or r.get("title")
            if k and k not in seen:
                seen.add(k)
                keep.append(r)
            if len(keep) >= REFS:
                break
        out[pool] = {"score": sum(W[k] * p[k] for k in W), **{k: p[k] for k in W}, "refs": keep}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["score"]))


def main(argv):
    if "--pool" in argv:
        d = _j(str(OUT.relative_to(ROOT)), {}) or {}
        p = d.get("pools", {}).get(argv[argv.index("--pool") + 1])
        print(json.dumps(p, ensure_ascii=False, indent=1) if p else "no such pool")
        return
    pools = build()
    OUT.write_text(json.dumps({"about": "Ground truth per doodle pool (tools/doodle_truth.py): pictures of what each drawing draws, "
                                         "weighted own 3, field 2, street 1, Commons 1. Higher score goes first.",
                               "weights": W, "pools": pools}, ensure_ascii=False, indent=1))
    n = int(argv[argv.index("--show") + 1]) if "--show" in argv else 15
    for pool, p in list(pools.items())[:n]:
        print(f'{p["score"]:6}  {pool:28} own {p["own"]:4} · field {p["field"]:3} · street {p["street"]:5} · commons {p["commons"]:4}')
    print(f"{len(pools)} pools → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
