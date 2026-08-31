#!/usr/bin/env python3
"""Publish the built site to R2. Stdlib + rclone; no GitHub anywhere in the path.

    python3 publish/deploy.py            # dry run, prints exactly what would change
    python3 publish/deploy.py --yes      # actually sync
    python3 publish/deploy.py --tiles    # also push the tile archives (~280 MB:
                                         # basemap + terrain DEM, whatever
                                         # data/basemap.json declares)

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

import atexit
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASEMAP = ROOT / "data" / "basemap.json"
BUCKET = "mot-dang-site"
BUILD_LOCK = ROOT / "cache" / "build.lock"
_lock_held = False

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


def _lock_holder():
    """(pid, started) from cache/build.lock, or None if it is unreadable."""
    try:
        lines = BUILD_LOCK.read_text().splitlines()
        return int(lines[0].strip()), (lines[1].strip() if len(lines) > 1 else "?")
    except (OSError, ValueError, IndexError):
        return None


def _alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def hold_docs(patience_s=600):
    """Take build.py's OWN lock for the length of the mirror.

    WHY A PUBLISH TAKES THE *BUILD* LOCK. `rclone sync` is a mirror: it reads
    docs/ as it goes and deletes from the bucket whatever has stopped existing
    locally. build.py opens by wiping docs/. Those two together are how the
    site went to 2,479 objects on 2026-08-19 — a build started at 11:56:34
    while a sync fired at 11:50:41 was still walking the tree, and rclone
    faithfully mirrored the disappearance of 25,000 pages.

    build.take_build_lock() already refuses to start when cache/build.lock is
    held by a live pid, and already treats a lock whose process is gone as
    stale. So holding that same file, in that same format, is all it takes:
    a build launched mid-publish now refuses itself, by its own existing rule,
    with no change to build.py at all.

    The standing walk's own guards are not enough here — they serialise walk
    ROUNDS against each other, and the build that did the damage was run
    directly, outside any walk.
    """
    global _lock_held
    BUILD_LOCK.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + patience_s
    while True:
        try:
            fd = os.open(str(BUILD_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            held = _lock_holder()
            if held is None:
                BUILD_LOCK.unlink(missing_ok=True)   # unreadable: stale
                continue
            pid, started = held
            if not _alive(pid):
                print("  note: clearing a stale build lock from pid %s (started %s)"
                      % (pid, started))
                BUILD_LOCK.unlink(missing_ok=True)
                continue
            if time.time() > deadline:
                sys.exit("REFUSING: pid %s has been building since %s. Publishing "
                         "now would mirror a half-written docs/ onto the bucket "
                         "and delete the live site. Wait for that build."
                         % (pid, started))
            print("  waiting for pid %s to finish building (started %s)…"
                  % (pid, started))
            time.sleep(10)
        else:
            os.write(fd, ("%d\n%s\n" % (
                os.getpid(),
                datetime.datetime.now().isoformat(timespec="seconds"))).encode())
            os.close(fd)
            _lock_held = True
            atexit.register(release_docs)
            print("  docs/ held for the mirror (build lock, pid %d)" % os.getpid())
            return


def release_docs():
    """atexit, so Ctrl-C and a crash both give it back; SIGKILL does not, which
    is what the stale check above is for."""
    global _lock_held
    if not _lock_held:
        return
    _lock_held = False
    held = _lock_holder()
    if held is not None and held[0] != os.getpid():
        return                                   # somebody else's now; leave it
    BUILD_LOCK.unlink(missing_ok=True)


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


def declared_archives():
    """(local file, bucket key) for every tile archive data/basemap.json
    declares — the basemap under "url", the elevation DEM under "terrain.url".

    The config is what the built pages actually fetch, so --tiles pushes
    exactly that set and nothing hardcoded here. This function replaced a
    single hardcoded path the day after the DEM shipped dark: the terrain
    archive was declared on 2026-08-27, built, symlinked, rendered locally —
    and never uploaded, because --tiles only knew the basemap. Every reader
    of /doi.html got a 404ing relief while every deploy reported success.

    A key is the declared relative url verbatim; the local copy sits under
    assets/ at the same path (assets/tiles/x.pmtiles ↔ tiles/x.pmtiles, the
    pairing build.py's docs/tiles symlinks already rely on). An empty url is
    the documented off switch and asks for nothing; an absolute url is hosted
    elsewhere and is not ours to upload.
    """
    try:
        cfg = json.loads(BASEMAP.read_text())
    except (OSError, ValueError) as e:
        sys.exit("cannot read %s: %s" % (BASEMAP, e))
    out = []
    for u in (cfg.get("url"), (cfg.get("terrain") or {}).get("url")):
        if not u or "://" in u:
            continue
        key = u.lstrip("./")
        pair = (ROOT / "assets" / key, key)
        if pair not in out:
            out.append(pair)
    return out


def audit_tiles(env, dest):
    """Compare the bucket's copy of each declared archive against assets/.

    Advisory on purpose: a missing or stale archive never blocks the page
    sync — 27,000 pages should not be held hostage to a 161 MB upload — but
    it is named, every deploy, until somebody runs --tiles. The failure this
    catches is the one above: a declared archive with nothing behind it is a
    404 the site serves in silence, and the standing walk's log is the one
    place a person would see it.

    `rclone lsjson` of a missing prefix on R2 answers exit 0 and an empty
    list (verified 2026-08-28), so absence parses like presence; a non-zero
    exit is a real can't-check (network, credentials) and says only that.
    """
    declared = declared_archives()
    if not declared:
        return
    by_dir = {}
    for local, key in declared:
        d = key.rsplit("/", 1)[0] if "/" in key else ""
        by_dir.setdefault(d, []).append((local, key))
    for d, pairs in sorted(by_dir.items()):
        p = subprocess.run(["rclone", "lsjson", "%s/%s" % (dest, d)],
                           env=env, capture_output=True, text=True)
        if p.returncode != 0:
            print("  (could not check %s/ against the bucket)" % (d or "."))
            continue
        try:
            sizes = {o["Path"]: o.get("Size") for o in json.loads(p.stdout)}
        except (ValueError, TypeError, KeyError):
            print("  (could not read the bucket listing for %s/)" % (d or "."))
            continue
        for local, key in pairs:
            have = sizes.get(key.rsplit("/", 1)[-1])
            want = local.stat().st_size if local.exists() else None
            if have is None:
                print("  NOTE: %s is declared in data/basemap.json but absent "
                      "from the bucket — the live site 404s on it until "
                      "publish/deploy.py --yes --tiles runs." % key)
            elif want is not None and want != have:
                print("  NOTE: %s is %s bytes in the bucket, %s in assets/ — "
                      "a re-extracted archive that --tiles has not pushed yet."
                      % (key, f"{have:,}", f"{want:,}"))


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
              # The tile archives are NOT part of the site sync and must
              # survive it. `sync` is a mirror: anything in the bucket with no
              # counterpart under docs/ is deleted, and the archives (basemap
              # + terrain DEM, ~280 MB together) are uploaded by --tiles below
              # rather than built into docs/ — so without this line the first
              # ordinary content deploy after the basemap went live would
              # quietly delete it, and every map page would pull a megabyte of
              # MapLibre and then 404 on the tiles. Re-uploading is ~280 MB
              # and nobody would connect the two events.
              "--exclude", "tiles/**",
              "--transfers", "32", "--checkers", "32",
              "--fast-list", "--stats", "10s", "--stats-one-line"]

    if not go:
        print("\n  DRY RUN — nothing will change. Add --yes to do it.\n")
        run(["rclone", "sync", str(DOCS), dest, "--dry-run", "-v"] + common, env)
        print("\n  (lines above marked 'Skipped' are what would happen)")
        audit_tiles(env, dest)
        return

    hold_docs()
    n_after = sum(1 for p in DOCS.rglob("*") if p.is_file())
    if n_after < FLOOR:
        sys.exit("REFUSING: docs/ fell to %s files while taking the lock — "
                 "something wiped it. Rebuild, then try again." % f"{n_after:,}")
    print("\n  syncing…")
    run(["rclone", "sync", str(DOCS), dest] + common, env)
    print("  site synced")

    if with_tiles:
        archives = declared_archives()
        if not archives:
            print("\n  --tiles: data/basemap.json declares no archives to push")
        for local, key in archives:
            if not local.exists():
                sys.exit("no %s — data/basemap.json declares %s but the file "
                         "is not on this machine (that file says how each "
                         "archive is made)" % (local, key))
        for local, key in archives:
            mb = local.stat().st_size / 1e6
            print("\n  uploading %s (%.0f MB, only changes when re-extracted)…"
                  % (key, mb))
            run(["rclone", "copyto", str(local), "%s/%s" % (dest, key),
                 "--checksum", "--stats", "10s", "--stats-one-line"], env)
        if archives:
            print("  tile archives uploaded — data/basemap.json already "
                  "points the site at them")
    else:
        audit_tiles(env, dest)

    print("\ndone. https://motdang.net/")


if __name__ == "__main__":
    main()
