#!/usr/bin/env python3
"""Publish the built site to R2. Stdlib + rclone; no GitHub anywhere in the path.

    python3 publish/deploy.py            # dry run, prints exactly what would change
    python3 publish/deploy.py --yes      # actually sync
    python3 publish/deploy.py --tiles    # also push the 116 MB basemap archive

WHY A WRAPPER AND NOT JUST `rclone sync`
----------------------------------------
`rclone sync` makes the destination match the source, which means it DELETES
whatever is in the bucket and not in docs/. That is the behaviour we want —
retired pages should stop being served — and it is also one bad build away from
emptying the site. build.py wipes docs/ at the start of every run, so a build
that dies halfway leaves a real directory holding a handful of files, and a
sync of that would be indistinguishable from "the operator meant to delete
27,000 pages".

So this refuses to sync a suspiciously small tree, refuses to sync one with
local paths in it, and shows the deletions before it makes them. The floor is a
count, not a guess: a healthy build is ~27,500 files, and anything under FLOOR
is a broken build rather than a small site.

CREDENTIALS
-----------
Never in the repo. Either export them:

    export R2_ACCOUNT_ID=...        # Cloudflare account id
    export R2_ACCESS_KEY_ID=...     # R2 > Manage API tokens > Create (Object R+W)
    export R2_SECRET_ACCESS_KEY=...

or put them in ~/.mot-dang-r2.json as {"accountId":…,"accessKeyId":…,"secretAccessKey":…},
the same arrangement as ~/.mot-dang-showtimes.json and the LINE channel token.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TILES = ROOT / "assets" / "tiles" / "cm-cr.pmtiles"
BUCKET = "mot-dang-site"

# A healthy build is ~27,577 files. Anything much under this is a broken or
# half-finished build, and syncing it would delete most of the site.
FLOOR = 20000


def creds():
    c = {"accountId": os.environ.get("R2_ACCOUNT_ID"),
         "accessKeyId": os.environ.get("R2_ACCESS_KEY_ID"),
         "secretAccessKey": os.environ.get("R2_SECRET_ACCESS_KEY")}
    if not all(c.values()):
        p = Path.home() / ".mot-dang-r2.json"
        if p.exists():
            try:
                f = json.loads(p.read_text())
                for k in c:
                    c[k] = c[k] or f.get(k)
            except (ValueError, OSError):
                pass
    missing = [k for k, v in c.items() if not v]
    if missing:
        sys.exit("missing R2 credentials: %s\n(see the docstring at the top of "
                 "this file)" % ", ".join(missing))
    return c


def gate():
    """The same checks a human is supposed to run before publishing, made
    impossible to forget. Both have bitten this project before."""
    if not DOCS.is_dir():
        sys.exit("no docs/ — run python3 build.py first")
    n = sum(1 for p in DOCS.rglob("*") if p.is_file())
    print("  files in docs/: %s" % f"{n:,}")
    if n < FLOOR:
        sys.exit("REFUSING: only %s files, floor is %s. That is a broken build, "
                 "not a small site — syncing it would delete the rest of the "
                 "bucket. Rebuild, then try again." % (f"{n:,}", f"{FLOOR:,}"))
    hits = subprocess.run(["grep", "-rl", "/Users/", str(DOCS)],
                          capture_output=True, text=True).stdout.strip()
    if hits:
        sys.exit("REFUSING: local paths in the output —\n" +
                 "\n".join(hits.splitlines()[:5]))
    print("  no local paths, count sane")
    return n


def rclone_env(c):
    """rclone configured entirely through the environment, so no credential
    ever lands in a config file on disk."""
    e = dict(os.environ)
    e.update({
        "RCLONE_CONFIG_R2_TYPE": "s3",
        "RCLONE_CONFIG_R2_PROVIDER": "Cloudflare",
        "RCLONE_CONFIG_R2_ACCESS_KEY_ID": c["accessKeyId"],
        "RCLONE_CONFIG_R2_SECRET_ACCESS_KEY": c["secretAccessKey"],
        "RCLONE_CONFIG_R2_ENDPOINT":
            "https://%s.r2.cloudflarestorage.com" % c["accountId"],
        # R2 ignores ACLs; setting one makes it 400.
        "RCLONE_CONFIG_R2_NO_CHECK_BUCKET": "true",
    })
    return e


def run(args, env, quiet=False):
    p = subprocess.run(args, env=env, text=True,
                       capture_output=quiet)
    if p.returncode != 0:
        if quiet:
            sys.stderr.write(p.stdout or "")
            sys.stderr.write(p.stderr or "")
        sys.exit("rclone failed (%d)" % p.returncode)
    return p.stdout or ""


def main():
    go = "--yes" in sys.argv
    with_tiles = "--tiles" in sys.argv

    if not subprocess.run(["which", "rclone"], capture_output=True).returncode == 0:
        sys.exit("rclone not installed — brew install rclone")

    print("mot-dang → r2://%s" % BUCKET)
    gate()
    c = creds()
    env = rclone_env(c)
    dest = "R2:%s" % BUCKET

    # Content types are NOT set here on purpose: the Worker derives them from
    # the key's extension, so the bucket can stay dumb and a wrong guess at
    # upload time cannot mis-serve a page.
    common = ["--checksum",           # compare by hash, not mtime — build.py
                                      # rewrites every file every run
              # The basemap is NOT part of the site sync and must survive it.
              # `sync` is a mirror: anything in the bucket with no counterpart
              # under docs/ is deleted, and the 116 MB archive is uploaded by
              # --tiles below rather than built into docs/ — so without this
              # line the first ordinary content deploy after the basemap went
              # live would quietly delete it, and every map page would pull a
              # megabyte of MapLibre and then 404 on the tiles. Re-uploading is
              # 116 MB and nobody would connect the two events.
              "--exclude", "tiles/**",
              "--transfers", "32", "--checkers", "32",
              "--fast-list", "--stats", "10s", "--stats-one-line"]

    if not go:
        print("\n  DRY RUN — nothing will change. Add --yes to do it.\n")
        run(["rclone", "sync", str(DOCS), dest, "--dry-run", "-v"] + common, env)
        print("\n  (lines above marked 'Skipped' are what would happen)")
        return

    print("\n  syncing…")
    run(["rclone", "sync", str(DOCS), dest] + common, env)
    print("  site synced")

    if with_tiles:
        if not TILES.exists():
            sys.exit("no %s — see data/basemap.json for the extract command" % TILES)
        mb = TILES.stat().st_size / 1e6
        print("\n  uploading basemap (%.0f MB, only changes when re-extracted)…" % mb)
        run(["rclone", "copyto", str(TILES), "%s/tiles/cm-cr.pmtiles" % dest,
             "--checksum", "--stats", "10s", "--stats-one-line"], env)
        print("  basemap uploaded — set url in data/basemap.json to "
              "\"tiles/cm-cr.pmtiles\" and rebuild to switch it on")

    print("\ndone. https://motdang.net/")


if __name__ == "__main__":
    main()
