#!/usr/bin/env python3
"""Every archive data/basemap.json declares is an archive --tiles pushes.

The gap this closes shipped on 2026-08-27: the terrain DEM was declared,
built, symlinked and rendering locally, while publish/deploy.py knew one
hardcoded path — the basemap — so the DEM never reached the bucket and
/doi.html served a 404ing relief under a working-looking button. Three
contracts, all offline, fixtures only:

1. declared_archives() reads BOTH archives out of the real repo config, in
   declared order, and the assets/ copy of each exists on this machine —
   the url ↔ assets pairing build.py's docs/tiles symlinks rely on.
2. The parse rules: empty url is the off switch, an absolute url is hosted
   elsewhere, "./" trims, duplicates fold, an unreadable config refuses.
3. audit_tiles() names an absent or stale bucket copy and stays quiet when
   the bucket matches — with rclone faked, so no network and no bucket.

Plus the doi.js side of the same day: the DEM preflight must sit between
MDMAP.ready and everything the archive feeds — source, hillshade, #doibar —
so a declared-but-dead archive leaves the bar hidden and the drawn basin
standing. Checked as tripwires on the emitted JS (order of definition, the
ranged read, the PMTiles magic) and a node --check that it still parses.

Run: python3 tests/test_deploy_tiles.py
"""
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))          # geography_layer imports map_shell


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


deploy = _load("deploy_t", ROOT / "publish" / "deploy.py")
geography_layer = _load("geography_layer_t", ROOT / "geography_layer.py")

FAILS = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (" — " + detail if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def with_config(cfg_text, root=None):
    """declared_archives() against a throwaway config (and optional root)."""
    tmp = Path(tempfile.mkdtemp(prefix="deploy-tiles-"))
    (tmp / "basemap.json").write_text(cfg_text)
    old_bm, old_root = deploy.BASEMAP, deploy.ROOT
    deploy.BASEMAP = tmp / "basemap.json"
    if root is not None:
        deploy.ROOT = root
    try:
        return deploy.declared_archives()
    finally:
        deploy.BASEMAP, deploy.ROOT = old_bm, old_root
        shutil.rmtree(tmp, ignore_errors=True)


def fake_rclone(listings):
    """A subprocess stand-in: lsjson answered from a dict, everything else
    refused loudly — audit must never reach for any other rclone verb."""
    def run(args, env=None, capture_output=True, text=True):
        assert args[:2] == ["rclone", "lsjson"], args
        rc, out = listings.get(args[2], (1, ""))
        return types.SimpleNamespace(returncode=rc, stdout=out, stderr="")
    return run


def audit_output(cfg, files, listings):
    """Run audit_tiles with a scratch root, a scratch config and a faked
    rclone; hand back what it printed."""
    tmp = Path(tempfile.mkdtemp(prefix="deploy-audit-"))
    for rel, size in files.items():
        p = tmp / "assets" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)
    (tmp / "basemap.json").write_text(json.dumps(cfg))
    old_bm, old_root, old_run = deploy.BASEMAP, deploy.ROOT, deploy.subprocess.run
    deploy.BASEMAP, deploy.ROOT = tmp / "basemap.json", tmp
    deploy.subprocess.run = fake_rclone(listings)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            deploy.audit_tiles({}, "R2:test-bucket")
    finally:
        deploy.BASEMAP, deploy.ROOT, deploy.subprocess.run = old_bm, old_root, old_run
        shutil.rmtree(tmp, ignore_errors=True)
    return buf.getvalue()


def lsjson(entries):
    return (0, json.dumps([{"Path": n, "Name": n, "Size": s} for n, s in entries]))


def main():
    print("declared_archives, against the repo's own config:")
    pairs = deploy.declared_archives()
    keys = [k for _, k in pairs]
    check("basemap declared", "tiles/cm-cr.pmtiles" in keys, str(keys))
    check("terrain DEM declared — the archive --tiles forgot once",
          "tiles/cm-cr-terrain.pmtiles" in keys, str(keys))
    check("basemap first, as the config reads", keys[:1] == ["tiles/cm-cr.pmtiles"], str(keys))
    for local, key in pairs:
        check("assets/ holds %s" % key, local.exists(), str(local))

    print("declared_archives, parse rules:")
    base = {"url": "tiles/a.pmtiles", "terrain": {"url": "tiles/b.pmtiles"}}
    got = with_config(json.dumps(base))
    check("both archives, declared order",
          [k for _, k in got] == ["tiles/a.pmtiles", "tiles/b.pmtiles"], str(got))
    got = with_config(json.dumps({"url": "tiles/a.pmtiles", "terrain": {"url": ""}}))
    check("empty terrain url is the off switch",
          [k for _, k in got] == ["tiles/a.pmtiles"], str(got))
    got = with_config(json.dumps({"url": "tiles/a.pmtiles"}))
    check("no terrain block at all", [k for _, k in got] == ["tiles/a.pmtiles"], str(got))
    got = with_config(json.dumps({"url": "", "terrain": {"url": "tiles/b.pmtiles"}}))
    check("empty basemap url uploads no basemap",
          [k for _, k in got] == ["tiles/b.pmtiles"], str(got))
    got = with_config(json.dumps({"url": "https://pub-x.r2.dev/a.pmtiles",
                                  "terrain": {"url": "tiles/b.pmtiles"}}))
    check("absolute url is hosted elsewhere, skipped",
          [k for _, k in got] == ["tiles/b.pmtiles"], str(got))
    got = with_config(json.dumps({"url": "./tiles/a.pmtiles"}))
    check("leading ./ trimmed from the key", [k for _, k in got] == ["tiles/a.pmtiles"], str(got))
    got = with_config(json.dumps({"url": "tiles/a.pmtiles",
                                  "terrain": {"url": "tiles/a.pmtiles"}}))
    check("same file twice folds to once", [k for _, k in got] == ["tiles/a.pmtiles"], str(got))
    try:
        with_config("{not json")
        check("unreadable config refuses", False, "no SystemExit")
    except SystemExit:
        check("unreadable config refuses", True)

    print("audit_tiles, with rclone faked:")
    cfg = {"url": "tiles/a.pmtiles", "terrain": {"url": "tiles/b.pmtiles"}}
    files = {"tiles/a.pmtiles": 100, "tiles/b.pmtiles": 200}
    both = lsjson([("a.pmtiles", 100), ("b.pmtiles", 200)])
    out = audit_output(cfg, files, {"R2:test-bucket/tiles": both})
    check("bucket matches: says nothing", out == "", repr(out))
    out = audit_output(cfg, files,
                       {"R2:test-bucket/tiles": lsjson([("a.pmtiles", 100)])})
    check("absent archive is NAMED", "tiles/b.pmtiles" in out and "absent" in out, repr(out))
    check("absent archive points at the cure", "--tiles" in out, repr(out))
    check("present archive not accused", "tiles/a.pmtiles is" not in out, repr(out))
    out = audit_output(cfg, files,
                       {"R2:test-bucket/tiles": lsjson([("a.pmtiles", 100), ("b.pmtiles", 999)])})
    check("stale archive is NAMED", "tiles/b.pmtiles" in out and "999" in out, repr(out))
    out = audit_output(cfg, files, {"R2:test-bucket/tiles": (0, "[]")})
    check("empty prefix reads as absent, twice",
          out.count("absent") == 2, repr(out))
    out = audit_output(cfg, files, {})
    check("rclone failure says could-not-check, accuses nobody",
          "could not check" in out and "NOTE" not in out, repr(out))
    out = audit_output({"url": ""}, {}, {})
    check("nothing declared, nothing said", out == "", repr(out))

    print("doi.js preflight, tripwires on the emitted source:")
    js = geography_layer.JS
    order = [js.find("function arm("), js.find("addSource('doidem'"),
             js.find("doibar"), js.find("bytes=0-127")]
    check("arm() defined before source and bar, preflight after all three",
          -1 not in order and order == sorted(order), str(order))
    check("preflight is a ranged read", "Range" in js and "bytes=0-127" in js)
    check("preflight demands the PMTiles magic", "'PMTiles'" in js)
    check("arm() fires only inside the preflight's then",
          js.find("arm();") > js.find("bytes=0-127"), "")
    node = shutil.which("node")
    if node:
        tmp = Path(tempfile.mkdtemp(prefix="doi-js-"))
        f = tmp / "doi.js"
        f.write_text(js)
        p = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
        check("doi.js still parses under node", p.returncode == 0, p.stderr[:200])
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        print("  note: node not found — syntax check skipped")

    print("FAIL: " + ", ".join(FAILS) if FAILS else "PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
