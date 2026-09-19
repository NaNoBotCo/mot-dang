#!/usr/bin/env python3
"""Publish the front page alone: docs/index.html and docs/site/hero/.

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
    if not home.exists() or home.stat().st_size < 20_000 or "md-home" not in home.read_text():
        sys.exit("docs/index.html is not the front page home_layer writes — build it first")
    if len(list(hero.glob("*.webp"))) < 20:
        sys.exit("docs/site/hero holds too few frames — run importers/make_hero.py")
    cmds = [
        ["rclone", "copyto", str(home), DEST + "/index.html", "--checksum", "-v"] + dry,
        ["rclone", "sync", str(hero), DEST + "/site/hero", "--checksum", "-v"] + dry,
    ]
    for c in cmds:
        print(" ".join(c[:4]))
        r = subprocess.run(c, env=env)
        if r.returncode:
            sys.exit(r.returncode)
    print("front page %s" % ("published" if go else "— dry run; add --yes"))


if __name__ == "__main__":
    main()
