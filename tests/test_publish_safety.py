#!/usr/bin/env python3
"""Tests for publish/safety.py — the guards added after the 2026-09-08 outage.

Run as a script:  python3 tests/test_publish_safety.py

Run as a SCRIPT, not through `unittest discover`: several test files in this
repo are written this way and discovery finds nothing in them.

THE TEST THAT MATTERS is test_the_outage_tree_is_refused(). It builds a
miniature of exactly what was on disk when the site went down — a docs/ with
a huge cm/ and nothing else — and asserts the checks refuse it. The old FLOOR
guard passed that tree at four times its threshold. If someone ever removes
these checks, that test is the one that should stop them.
"""

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

PUBLISH = Path(__file__).resolve().parent.parent / "publish"
sys.path.insert(0, str(PUBLISH))
import safety                                                    # noqa: E402


def _load(name, path):
    """deploy.py by path: it imports safety from its own directory and runs
    nothing at import, so only its functions come in."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


deploy = _load("deploy_ps", PUBLISH / "deploy.py")

# One line of rclone --use-json-log output, as v1.75.0 writes it at the end
# of a sync (the `stats` object is what rc core/stats answers).
STATS_LINE = json.dumps({
    "time": "2026-09-10T22:27:01.343823+07:00", "level": "notice",
    "msg": "   87.900 KiB / 87.900 KiB, 100%, 0 B/s, ETA -\n",
    "stats": {"bytes": 1288490189, "checks": 199000, "deletedDirs": 0,
              "deletes": 4115, "elapsedTime": 3553.2, "errors": 0,
              "eta": None, "fatalError": False, "listed": 33, "renames": 0,
              "retryError": False, "speed": 0, "totalBytes": 1288490189,
              "totalChecks": 199000, "totalTransfers": 27613,
              "transferTime": 3550.0, "transfers": 27613},
    "source": "accounting/stats.go:551"})

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name,
                         "" if cond else "  — " + detail))


def whole_site(root, cm=1200, cr=150, data=25):
    """A synthetic tree that has everything the checks ask for."""
    root = Path(root)
    for rel in safety.ALWAYS + safety.WHEN_BASEMAP:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    for name, n in (("cm", cm), ("cr", cr), ("data", data)):
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            (d / ("f%d.html" % i)).write_text("x")
    return root


def main():
    print("publish/safety.py")

    # ---- the required-path set -------------------------------------------
    check("basemap on ⇒ map + vendor + glyphs are required",
          set(safety.WHEN_BASEMAP) <= set(safety.required())
          if safety.basemap_on() else True)
    check("index.html is always required", "index.html" in safety.ALWAYS)
    check("404.html is always required", "404.html" in safety.ALWAYS)
    check("both provinces are required",
          "cm/index.html" in safety.ALWAYS and "cr/index.html" in safety.ALWAYS)

    with tempfile.TemporaryDirectory() as td:
        good = whole_site(Path(td) / "good")

        # ---- a whole site passes -----------------------------------------
        check("a whole tree raises no complaint",
              safety.check_tree(good, say=lambda *_: None) == [],
              str(safety.check_tree(good, say=lambda *_: None)))

        # ---- THE OUTAGE TREE ---------------------------------------------
        # 2026-09-08: docs/ held cm/ (77,107 files) and data/ and a few root
        # assets. Total count 80,105 — four times FLOOR=20,000 — so the only
        # guard in the path waved it through and rclone deleted the rest of
        # the site. Miniature of that tree here.
        out = Path(td) / "outage"
        (out / "cm").mkdir(parents=True)
        for i in range(1200):                     # stands in for the 77,107
            (out / "cm" / ("p%d.html" % i)).write_text("x")
        (out / "cm" / "index.html").write_text("x")
        (out / "data").mkdir()
        for i in range(25):
            (out / "data" / ("d%d.geojson" % i)).write_text("x")
        for rel in ("md.js", "style.css", "robots.txt"):
            (out / rel).write_text("x")

        n = sum(1 for p in out.rglob("*") if p.is_file())
        check("outage tree clears the old total-count floor (that was the hole)",
              n > 1000)
        problems = safety.check_tree(out, say=lambda *_: None)
        check("outage tree is REFUSED by the new checks", problems != [])
        missing = safety.required_missing(out)
        check("front page named as missing", "index.html" in missing)
        check("cr/ named as missing", "cr/index.html" in missing)
        check("cr/ short-fall reported",
              any(n_ == "cr" for n_, _, _ in safety.subtree_shortfalls(out)))

        # ---- deletion verdicts -------------------------------------------
        ok, msg = safety.deletion_verdict(["cm/p/old-shop.html"], prune=False)
        check("a handful of retired pages is allowed", ok, msg)

        many = ["cm/p/x%d.html" % i for i in range(safety.DELETE_CEILING + 1)]
        ok, msg = safety.deletion_verdict(many, prune=False)
        check("a mass deletion is refused without --prune", not ok)
        ok, _ = safety.deletion_verdict(many, prune=True)
        check("--prune allows a mass deletion said out loud", ok)

        for pre in safety.NEVER_PRUNE:
            ok, msg = safety.deletion_verdict([pre + "anything"], prune=True)
            check("deleting %s is refused even with --prune" % pre, not ok)

        # ---- the bounded form: --prune-up-to N ---------------------------
        # 2026-09-10: a hand publish needed 4,115 deletions, above the
        # ceiling; the standing walk cannot type --prune, so it could never
        # have retired that churn. A bound lets it, for a whole tree only.
        churn = ["cm/p/y%d.html" % i for i in range(4115)]
        ok, msg = safety.deletion_verdict(churn, prune_up_to=6000, tree_ok=True)
        check("under the bound, with a whole tree, passes", ok, msg)
        check("the bound is named in the log line", "--prune-up-to 6,000" in msg, msg)
        over = ["cm/p/z%d.html" % i for i in range(6001)]
        ok, msg = safety.deletion_verdict(over, prune_up_to=6000, tree_ok=True)
        check("over the bound refuses", not ok)
        check("over the bound names the bound as the ceiling", "6,000" in msg, msg)
        ok, msg = safety.deletion_verdict(churn[:10], prune_up_to=6000, tree_ok=False)
        check("a failed tree check refuses even under the bound", not ok)
        ok, _ = safety.deletion_verdict(churn[:10], prune_up_to=6000, tree_ok=True)
        check("a whole tree with ten deletions passes under the bound", ok)
        ok, _ = safety.deletion_verdict(churn[:101], prune_up_to=100, tree_ok=True)
        check("a bound below the ceiling is still the bound", not ok)
        ok, _ = safety.deletion_verdict(churn, prune=False)
        check("neither flag: 4,115 still refused (default unchanged)", not ok)
        ok, _ = safety.deletion_verdict(over, prune=True, prune_up_to=6000)
        check("--prune keeps its meaning beside a bound", ok)
        for pre in safety.NEVER_PRUNE:
            ok, _ = safety.deletion_verdict([pre + "x"], prune_up_to=6000, tree_ok=True)
            check("deleting %s is refused under a bound too" % pre, not ok)

        # ---- the preview lists both sides, not rclone's chatter ----------
        listed = ["index.html", "cm/a.html", "tiles/cm-cr.pmtiles", "old.html"]

        def fake_run(args, env, quiet=False):
            assert args[:2] == ["rclone", "lsf"], args
            return "\n".join(listed)

        (Path(td) / "loc").mkdir()
        (Path(td) / "loc" / "index.html").write_text("x")
        (Path(td) / "loc" / "cm").mkdir()
        (Path(td) / "loc" / "cm" / "a.html").write_text("x")
        gone = safety.deletions_preview("R2:b", {}, fake_run,
                                        root=Path(td) / "loc")
        check("preview finds the retired page", gone == ["old.html"], str(gone))
        check("preview does not call the tile archive a deletion",
              not any(g.startswith("tiles/") for g in gone))

    # ---- rclone's stats reach the log ------------------------------------
    # Before 2026-09-10 rclone's stats went nowhere (INFO under a NOTICE
    # default), so a change to --transfers could not be measured.
    stats = deploy.rclone_stats(STATS_LINE)
    check("the stats object is read off a --use-json-log line",
          stats is not None and stats["transfers"] == 27613)
    check("a line without stats is None",
          deploy.rclone_stats('{"level":"notice","msg":"Deleted: x"}') is None)
    check("a non-JSON line is None", deploy.rclone_stats("rclone: panic\n") is None)
    line = deploy.rclone_summary(stats)
    for want in ("27,613 file(s)", "1.2 GiB", "59m 13s", "7.8 file(s)/s",
                 "deleted 4,115", "0 error(s)"):
        check("summary carries %s" % want, want in line, line)
    check("the summary is one line", "\n" not in line)
    bad = dict(stats, errors=3, lastError="couldn't copy x: errno -1")
    check("errors and the last one are named",
          "3 error(s) — last: couldn't copy x" in deploy.rclone_summary(bad),
          deploy.rclone_summary(bad))
    check("a scoped sync says its prefix",
          deploy.rclone_summary(stats, scope="listings").startswith(
              "  rclone (listings/):"))
    check("no stats line still writes something",
          "no stats line seen" in deploy.rclone_summary(None))
    check("the text a reader sees is rclone's own message",
          deploy.rclone_text(STATS_LINE) ==
          "2026-09-10 22:27:01 NOTICE:    87.900 KiB / 87.900 KiB, 100%, 0 B/s, ETA -",
          deploy.rclone_text(STATS_LINE))
    check("a non-JSON line passes through", deploy.rclone_text("plain\n") == "plain")
    check("stats are logged at NOTICE, so they show at rclone's default level",
          "--stats-log-level" in Path(PUBLISH / "deploy.py").read_text())

    # ---- 2026-09-25: the front page asked for two frames the tree lacked --
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        whole_site(root)
        (root / "index.html").write_text(
            '<link rel="icon" href="/logo/fav.svg"><link rel="canonical" href="https://motdang.net/">'
            '<picture><source srcset="site/map/map-dots-dark.png" media="(prefers-color-scheme:dark)">'
            '<img src="site/map/map-dots-light.png" alt=""></picture>'
            '<img srcset="https://motdang.net/site/hero/a.webp 1x, /site/hero/a@2x.webp 2x">'
            '<a href="find?q=x">search</a><script src="https://cdn.example.org/x.js"></script>')
        gaps = safety.referenced_missing(root)
        check("a front page asking for files the tree lacks is named, file by file",
              {p for _, p in gaps} == {"logo/fav.svg", "site/map/map-dots-dark.png",
                                        "site/map/map-dots-light.png", "site/hero/a.webp",
                                        "site/hero/a@2x.webp"}, gaps)
        check("check_tree refuses that tree",
              any("front pages ask for" in p for p in safety.check_tree(root, say=lambda *_: None)))
        for p in ("logo/fav.svg", "site/map/map-dots-dark.png", "site/map/map-dots-light.png",
                  "site/hero/a.webp", "site/hero/a@2x.webp"):
            (root / p).parent.mkdir(parents=True, exist_ok=True)
            (root / p).write_text("x")
        check("with the files present, links, canonicals and other hosts are not asked for",
              safety.referenced_missing(root) == [], safety.referenced_missing(root))

    # ---- deletions the change announced (Nan, 2026-10-11) ----------------
    # That day: 2,949 per-tag GeoJSON files and 1,212 doodle shards were cuts
    # she had asked for, beside ~100 ordinary churn. The ceiling refused all.
    tags = ["data/cm-tag-t%d.geojson" % i for i in range(2949)]
    shards = ["doodles/data/v/%d.json" % i for i in range(1212)]
    churn = ["cm/p/old%d.html" % i for i in range(108)]
    ann = [{"id": "tag-geojson", "until": "2026-10-25",
            "remove": {"data/c[mr]-tag-*.geojson": 2950}},
           {"id": "doodles-kept", "until": "2026-10-25",
            "remove": {"doodles/data/": 1212}, "add": {"doodles/": 3}}]
    ok, msg = safety.deletion_verdict(tags + shards + churn, announced=ann)
    check("announced cuts within 10% plus ordinary churn pass", ok, msg)
    check("the log line says how many were announced", "4,161 of them announced" in msg, msg)
    ok, _ = safety.deletion_verdict(tags + shards + churn)
    check("the same deletions without announcements refuse", not ok)
    extra = ["data/cr-tag-x%d.geojson" % i for i in range(400)]
    ok, msg = safety.deletion_verdict(tags + extra, announced=ann)
    check("more than announced (+13%) refuses", not ok, msg)
    check("the refusal names the pattern", "data/c[mr]-tag-*.geojson" in msg, msg)
    ok, msg = safety.deletion_verdict(tags[:2700] + churn, announced=ann)
    check("fewer than announced publishes, and says so", ok and "under" in msg, msg)
    stale = ["cm/p/limb%d.html" % i for i in range(safety.DELETE_CEILING + 1)]
    ok, msg = safety.deletion_verdict(tags + stale, announced=ann)
    check("unannounced loss past the ceiling still refuses beside an announcement",
          not ok and "no announcement covers" in msg, msg)
    ok, _ = safety.deletion_verdict(["vendor/maplibre-gl.js"],
                                    announced=[{"id": "v", "until": "2099-01-01",
                                                "remove": {"vendor/": 1}}])
    check("an announcement cannot open vendor/ glyphs/ api/", not ok)
    rest, groups = safety.expected_split(tags[:3] + ["cm/x.html"],
                                         [{"id": "a", "remove": {"data/": 50}},
                                          {"id": "b", "remove": {"data/cm-tag-": 3}}])
    check("a key counts against the longest pattern it matches",
          [g["found"] for g in groups] == [0, 3] and rest == ["cm/x.html"], groups)
    _, groups = safety.expected_split(tags + shards, ann)
    check("cuts within their bands are used up",
          safety.expected_used(groups) == ["doodles-kept", "tag-geojson"], groups)
    _, groups = safety.expected_split(shards, ann)
    check("a cut that has not landed stays in force",
          safety.expected_used(groups) == ["doodles-kept"], groups)
    lines = safety.additions_lines(["doodles/index.html", "cm/new.html"], ann)
    check("additions are counted and set against an announced add",
          "additions: 2" in lines[0] and any("doodles-kept doodles/: 1 to add" in l for l in lines),
          lines)

    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "expected.json"
        f.write_text(json.dumps({"announced": ann + [
            {"id": "old", "until": "2026-10-01", "remove": {"x/": 1}},
            {"remove": {"y/": 1}}]}))
        act, said = safety.load_expected(f, today="2026-10-11", done={"doodles-kept"})
        check("load: active, used-up and expired sorted apart",
              [a["id"] for a in act] == ["tag-geojson"], act)
        check("load: the expired and the malformed are said",
              any("expired" in s for s in said) and any("ignored" in s for s in said), said)
        f.write_text("{not json")
        act, said = safety.load_expected(f, today="2026-10-11", done=set())
        check("load: an unreadable file applies nothing and says so", act == [] and said, said)
        act, said = safety.load_expected(Path(td) / "none.json", done=set())
        check("load: no file, nothing to say", act == [] and said == [])

    # ---- the smoke list --------------------------------------------------
    paths = [p for p, _ in safety.SMOKE]
    check("smoke asks for the front page", "/" in paths)
    check("smoke asks for both provinces", "/cm/" in paths and "/cr/" in paths)
    check("smoke includes a must-404 URL, so 'everything is 200' is caught",
          any(want == 404 for _, want in safety.SMOKE))

    # ---- files newer than the build (Lanna Craft, 2026-10-10) -------------
    import datetime
    utc = datetime.timezone.utc
    listing = json.dumps([
        {"Path": "sites/lanna-craft/index.html", "ModTime": "2026-10-10T14:27:44.123456789Z"},
        {"Path": "sites/old/index.html", "ModTime": "2026-10-09T01:00:00Z"},
        {"Path": "sites/edge/index.html", "ModTime": "2026-10-10T12:30:00Z"},
        {"Path": "sites/odd/index.html", "ModTime": "not a time"}])
    fake = lambda args, env, quiet=False: listing                # noqa: E731
    since = datetime.datetime(2026, 10, 10, 13, 8, 42, tzinfo=utc)   # the 20:08 hand-off
    got = safety.uploaded_since("R2:x", {}, fake, ["a"], since)
    check("a live file uploaded after the build's source is kept",
          "sites/lanna-craft/index.html" in got, got)
    check("one uploaded within the grace before it is kept too",
          "sites/edge/index.html" in got, got)
    check("an older one is left to the sync", "sites/old/index.html" not in got, got)
    check("an unreadable upload time keeps the file", "sites/odd/index.html" in got, got)
    check("no candidates asks the bucket nothing",
          safety.uploaded_since("R2:x", {}, None, [], since) == [])

    # ---- a direct upload needs its site in assets/ ------------------------
    check("a minisite file with no folder in assets/ is refused",
          not deploy.in_source("sites/no-such-site-here/index.html"))
    check("a file the build writes at the top of a copied folder passes",
          deploy.in_source("sites/index.html"))
    check("a file outside the copied folders passes", deploy.in_source("data/flightboard.json"))

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
