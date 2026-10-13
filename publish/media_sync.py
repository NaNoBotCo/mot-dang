#!/usr/bin/env python3
"""Send the pictures a build listed to the bucket mot-dang-media.

    python3 publish/media_sync.py probe       exit 0 when this host can write the bucket
    python3 publish/media_sync.py sync        upload what the bucket lacks or holds changed
    python3 publish/media_sync.py sync -n     say what it would upload

The build (media_layer.py, MD_MEDIA_BUCKET=1) writes cache/media-manifest.txt:
one path per line, relative to assets/ and to the site root alike
(photos/x.jpg is assets/photos/x.jpg and motdang.net/photos/x.jpg). This reads
that list, lists the bucket once, and uploads each listed file that is missing,
has another size, or is newer than the bucket's copy and differs in content.
rclone copy only: nothing in the bucket is deleted, here or by the site sync.

The credentials are deploy.py's (~/.mot-dang-r2.json or R2_* in the
environment). The key on motdang-build covers mot-dang-site only until the
token is edited to include mot-dang-media; probe says which it is, and
importers/publish_steps.sh publishes the old way while it says no.
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy                                      # noqa: E402  creds(), rclone_env()

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MANIFEST = ROOT / "cache" / "media-manifest.txt"
BUCKET = "mot-dang-media"
DEST = "R2:%s" % BUCKET
PREFIXES = ("streetphotos/", "photos/", "inat/", "og/")
SLACK_S = 2          # a file newer than its object by less than this is the same moment


def rclone(args, env, **kw):
    return subprocess.run(["rclone"] + args, env=env, text=True, **kw)


def probe(env):
    """Write one small object and read the bucket's top level."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(time.strftime("%Y-%m-%dT%H:%M:%S\n"))
        tmp = fh.name
    try:
        p = rclone(["copyto", tmp, "%s/_probe/last.txt" % DEST, "--s3-no-head", "--retries", "1",
                    "--low-level-retries", "1"], env, capture_output=True)
    finally:
        os.unlink(tmp)
    if p.returncode != 0:
        why = [ln for ln in (p.stderr or "").splitlines() if "ERROR" in ln or "Failed" in ln]
        print("media: %s is not writable from this host — %s"
              % (BUCKET, (why[-1] if why else "rclone failed")[-160:]))
        return 1
    return 0


def listed():
    """Manifest paths that are files under assets/ and inside the four prefixes."""
    try:
        rows = [ln.strip() for ln in MANIFEST.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return None, 0
    out, gone = [], 0
    for rel in rows:
        if not rel.startswith(PREFIXES) or ".." in rel.split("/"):
            continue
        if (ASSETS / rel).is_file():
            out.append(rel)
        else:
            gone += 1
    return out, gone


def bucket_table(env):
    """{key: (size, mtime, md5)} for every object, one listing pass.

    lsf, not lsjson: lsjson --hash asks the bucket about each object in turn
    (ten minutes for 47,000), while lsf reads the md5 off the listing in
    seconds. --use-server-modtime keeps the time off the listing too (without
    it rclone reads each object's metadata, one request each). The times are
    when the object was written, in this host's own zone, as rclone prints them.
    """
    p = rclone(["lsf", "-R", "--files-only", "--fast-list", "--use-server-modtime", "--format", "psth",
                "--hash", "md5", "--separator", "\t", DEST], env, capture_output=True)
    if p.returncode != 0:
        sys.exit("media: could not list %s\n%s" % (DEST, (p.stderr or "")[-300:]))
    table = {}
    for ln in p.stdout.splitlines():
        parts = ln.split("\t")
        if len(parts) < 4:
            continue
        try:
            t = time.mktime(time.strptime(parts[2][:19], "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            t = 0
        table[parts[0]] = (int(parts[1]), t, parts[3].lower())
    return table


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wanted(rels, table):
    """The listed files the bucket needs: missing, another size, or newer and
    different. Newer alone is not enough — a card redrawn with the same pixels
    is not worth a PUT."""
    out = []
    for rel in rels:
        st = (ASSETS / rel).stat()
        have = table.get(rel)
        if have is None or have[0] != st.st_size:
            out.append(rel)
        elif st.st_mtime > have[1] + SLACK_S and have[2] and md5_of(ASSETS / rel) != have[2]:
            out.append(rel)
    return out


def sync(env, dry):
    rels, gone = listed()
    if rels is None:
        print("media: no %s — the build has not listed anything; nothing to send" % MANIFEST.name)
        return 0
    table = bucket_table(env)
    need = wanted(rels, table)
    print("media: %d listed, %d in the bucket, %d to send%s"
          % (len(rels), len(table), len(need), ("; %d listed and not on disk" % gone) if gone else ""))
    if dry or not need:
        for r in need[:20]:
            print("  would send " + r)
        return 0
    lst = Path(tempfile.mkstemp(suffix=".txt")[1])
    try:
        lst.write_text("".join(r + "\n" for r in need), encoding="utf-8")
        t0 = time.time()
        p = rclone(["copy", str(ASSETS), DEST, "--files-from", str(lst), "--no-traverse",
                    "--ignore-times", "--transfers", "24", "--s3-no-head", "--stats", "30s",
                    "--stats-one-line", "--stats-log-level", "NOTICE"], env)
    finally:
        lst.unlink(missing_ok=True)
    if p.returncode != 0:
        print("media: rclone failed (%d)" % p.returncode)
        return 1
    print("media: sent %d picture(s) in %.0f s" % (len(need), time.time() - t0))
    return 0


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "sync"
    try:
        env = deploy.rclone_env(deploy.creds())
    except SystemExit as e:
        print("media: %s" % e)
        return 1
    if subprocess.run(["which", "rclone"], capture_output=True).returncode != 0:
        print("media: rclone not installed")
        return 1
    if cmd == "probe":
        return probe(env)
    if cmd == "sync":
        return sync(env, "-n" in argv or "--dry-run" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
