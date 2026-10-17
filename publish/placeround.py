"""The weekly place round (Nan, 2026-10-13: "do a and b together").

R2 bills every object a publish writes. About one change a day to the place
template rewrote every place page (100k–190k objects, measured 10–12 Oct), so
place pages now go up on two clocks:

  - every publish: a place page whose own record changed since its last upload
    (build.py writes cache/place-inputs.json, one hash per page, from the
    record and its photo), and every page of a place that is new;
  - once a week: everything else under <prov>/p/ — template changes, neighbour
    lists, deletions of places that left.

A full round runs when the last one is 7 days old, when no record of one
exists, when cache/place-inputs.json is missing, or when the file named by
FULL_NOW exists (a session that needs a place-page fix live today touches it;
the round removes it).

    python3 publish/placeround.py            # what the next publish would do
"""
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "cache" / "place-inputs.json"
PUBLISHED = Path(os.environ.get("MD_PLACE_PUBLISHED") or (ROOT / "cache" / "place-published.json"))
FULL_NOW = Path(os.environ.get("MD_PLACE_FULL_NOW") or (ROOT / "cache" / "place-full-now"))
DAYS = 7


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _published():
    try:
        return json.loads(PUBLISHED.read_text())
    except (OSError, ValueError):
        return None


def why_full():
    """The reason this publish is a full place round, or None."""
    if FULL_NOW.exists():
        return "asked for (%s)" % FULL_NOW.name
    if not INPUTS.exists():
        return "no cache/place-inputs.json from this build"
    pub = _published()
    if not pub or "full_at" not in pub:
        return "no full place round on record"
    age = _now() - dt.datetime.fromisoformat(pub["full_at"])
    if age >= dt.timedelta(days=DAYS):
        return "last full place round %d days ago" % age.days
    return None


def plan():
    """None for a full round, else (exclude globs, place files to upload)."""
    if why_full():
        return None
    cur = json.loads(INPUTS.read_text())
    seen = _published().get("hashes", {})
    provs = sorted({k.split("/", 1)[0] for k in cur})
    globs = ["/%s/p/**" % p for p in provs]
    ups = sorted(k for k, h in cur.items() if seen.get(k) != h)
    return globs, ups


def covered(key):
    """True when a bucket key is a place file the weekly round looks after."""
    parts = key.split("/")
    return len(parts) == 3 and parts[1] == "p"


def record(full, uploaded=()):
    """After a publish that succeeded: what is now live, by input hash."""
    if not INPUTS.exists():
        return
    cur = json.loads(INPUTS.read_text())
    pub = _published() or {}
    if full:
        pub = {"full_at": _now().isoformat(timespec="seconds"), "hashes": cur}
        FULL_NOW.unlink(missing_ok=True)
    else:
        hashes = pub.setdefault("hashes", {})
        for k in uploaded:
            if k in cur:
                hashes[k] = cur[k]
    tmp = PUBLISHED.with_suffix(".tmp")
    tmp.write_text(json.dumps(pub, sort_keys=True))
    tmp.replace(PUBLISHED)


if __name__ == "__main__":
    w = why_full()
    if w:
        print("next publish: full place round — %s" % w)
    else:
        globs, ups = plan()
        pub = _published()
        print("next publish: %d place file(s) with changed records; the rest wait for the "
              "full round (last %s)" % (len(ups), pub["full_at"]))
