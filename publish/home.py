#!/usr/bin/env python3
"""Publish the front page alone: docs/index.html, docs/calendar.html, docs/site/hero/
and docs/site/map/.

The full mirror is deploy.py and takes the whole tree; this copies the two
things the front page is made of and touches nothing else in the bucket.
Rollback is the same command after `git checkout docs/index.html`.

    python3 publish/home.py            # dry run
    python3 publish/home.py --yes
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import deploy  # noqa: E402

DOCS = deploy.DOCS
DEST = "R2:%s" % deploy.BUCKET


def main():
    go = "--yes" in sys.argv
    env = deploy.rclone_env(deploy.creds())
    dry = [] if go else ["--dry-run"]
    home = DOCS / "index.html"
    hero = DOCS / "site" / "hero"
    # the drawn map, two frames, written by homebits.dots() when the page is rendered
    dots = DOCS / "site" / "map"
    if not home.exists() or home.stat().st_size < 20_000 or "md-home" not in home.read_text():
        sys.exit("docs/index.html is not the front page home_layer writes — build it first")
    if len(list(hero.glob("*.webp"))) < 20:
        sys.exit("docs/site/hero holds too few frames — run importers/make_hero.py")
    if "site/map/map-dots" in home.read_text() and len(list(dots.glob("*.png"))) < 2:
        sys.exit("the page draws a map but docs/site/map is empty — build it first")
    cmds = [
        ["rclone", "copyto", str(home), DEST + "/index.html", "--checksum", "-v"] + dry,
        ["rclone", "sync", str(hero), DEST + "/site/hero", "--checksum", "-v"] + dry,
    ]
    # only when the page being published actually draws the map: the front page is
    # home_layer's scenes again (2026-09-21 evening) and does not.
    if "site/map/map-dots" in home.read_text() and dots.exists():
        cmds.append(["rclone", "sync", str(dots), DEST + "/site/map", "--checksum", "-v"] + dry)
    # the page the front page's seven days link to: publishing one without the other
    # leaves a button pointing at a 404
    cal = DOCS / "calendar.html"
    if "calendar.html" in home.read_text():
        if not cal.exists():
            sys.exit("the front page links to calendar.html and docs/ has none — build it first")
        cmds.append(["rclone", "copyto", str(cal), DEST + "/calendar.html",
                     "--checksum", "-v"] + dry)
    # the way back: home_layer's scenes page, so switching the front page back is a
    # rebuild of one file and not a deploy of the whole tree
    scenes = DOCS / "home-scenes.html"
    if scenes.exists():
        cmds.append(["rclone", "copyto", str(scenes), DEST + "/home-scenes.html",
                     "--checksum", "-v"] + dry)
    for c in cmds:
        print(" ".join(c[:4]))
        r = subprocess.run(c, env=env)
        if r.returncode:
            sys.exit(r.returncode)
    print("front page %s" % ("published" if go else "— dry run; add --yes"))


if __name__ == "__main__":
    main()
