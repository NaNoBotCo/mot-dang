"""Pictures that ride beside the site, not inside docs/ (Nan, 2026-10-13, "B").

streetphotos/, photos/, inat/ and og/ were 5 GB of the server's docs/ and went to
the bucket mot-dang-site with every page. They have their own bucket,
mot-dang-media, and their own Worker (worker-media/). Page URLs are the same.

    MD_MEDIA_BUCKET=1   the build lists what it would have copied into docs/ in
                        cache/media-manifest.txt and copies nothing;
                        publish/media_sync.py sends the listed files from assets/
                        to the bucket before the site publishes, and
                        publish/deploy.py leaves the four prefixes alone.
    unset               the build copies into docs/ as before and the site sync
                        carries them.

importers/publish_steps.sh sets the variable when the host can write the bucket
(media_sync.py probe), so a host without that key keeps publishing the old way.

A listed path is relative to assets/ and to the site root alike
(assets/photos/x.jpg is photos/x.jpg on the site). The list is a set of
sources for rclone copy: nothing in it deletes anything.
"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIXES = ("streetphotos", "photos", "inat", "og")
MANIFEST = ROOT / "cache" / "media-manifest.txt"
_listed = set()


def on():
    return os.environ.get("MD_MEDIA_BUCKET") == "1"


def put(src, docs, rel):
    """One file for the site root path `rel`. With the bucket on it is listed;
    otherwise it is copied into docs/ as the build always did."""
    if on():
        _listed.add(rel)
        return
    dest = Path(docs) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)


def put_tree(src_dir, docs, rel_dir):
    """A folder of pictures under assets/, whole (photos/landmarks/<id>/…)."""
    src_dir = Path(src_dir)
    if not on():
        shutil.copytree(src_dir, Path(docs) / rel_dir, dirs_exist_ok=True)
        return
    for p in sorted(src_dir.rglob("*")):
        if p.is_file():
            _listed.add("%s/%s" % (rel_dir, p.relative_to(src_dir).as_posix()))


def flush(path=None):
    """Write the list. Atomic, and only when the bucket is on."""
    if not on():
        return 0
    path = Path(path) if path else MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_text("".join(r + "\n" for r in sorted(_listed)), encoding="utf-8")
    os.replace(tmp, path)
    print("  media: %d picture(s) listed for mot-dang-media (%s)" % (len(_listed), path.name))
    return len(_listed)


def listed(path=None):
    """The set a build wrote, or None when there is no list."""
    path = Path(path) if path else MANIFEST
    try:
        return {ln.rstrip("\n") for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}
    except OSError:
        return None


def in_build(docs, rel):
    """True when the build shipped `rel`: in docs/, or, with the bucket on, in
    the list. For the gates that ask whether a card a page names exists."""
    if (Path(docs) / rel).exists():
        return True
    if on():
        got = listed()
        return got is not None and rel in got
    return False
