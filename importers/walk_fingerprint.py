#!/usr/bin/env python3
"""What would a rebuild actually change? — the standing walk's change gate.

    python3 importers/walk_fingerprint.py diff  cache/last-published.json
    python3 importers/walk_fingerprint.py write cache/last-published.json

`diff` prints one changed path per line (empty output = nothing to publish).
`write` records the current state after a publish. Stdlib only.

WHY THIS IS NOT JUST `find -newer`
----------------------------------
mtimes are useless here. `sync_claims.py`, `sync_toilets.py`, `import_all.py`,
`build_streets.py` and `build_open_lamps.py` all rewrite their output every
single run whether or not one fact changed, so every file in data/ is "new"
every twenty minutes and an mtime gate rebuilds 36,000 pages forever to say
exactly the same thing.

WHY IT IS NOT A PLAIN CONTENT HASH EITHER
-----------------------------------------
That was the first attempt and it failed the same way for a subtler reason:
those writers stamp the moment of writing INTO their output —

    data/claims.json          "generated": "2026-08-18T14:34:01.749Z"
    data/open_lamps.json      "generated": "2026-08-07"
    data/streets.json         "generated": ...

so the bytes differ every run even when nothing came in. A timestamp recording
when we last asked is not news about the town. VOLATILE_KEYS are therefore
dropped from the TOP LEVEL of any JSON before it is hashed — top level only,
because "generated" nested inside a record could be a real fact about a place
and is not ours to ignore.

If a future importer stamps a key that is not in this set, the gate does not
break quietly: it rebuilds every round, and `diff` names the offending file in
the walk's log every time. That is the intended failure — visible and cheap to
read, not silent.
"""

import hashlib
import json
import sys
from pathlib import Path

# Directories that are never inputs to a build: build output, scratch, the
# suggestion inbox (which carries senders' emails and reaches nothing on its
# own), and the basemap archive — 116 MB that changes only when it is
# re-extracted by hand and never rides in docs/ anyway.
SKIP_DIRS = {".git", "docs", "cache", "_incoming", "node_modules",
             ".venv", "__pycache__", "tiles"}

# Top-level JSON keys that record WHEN we looked, not WHAT we found.
VOLATILE_KEYS = {"generated", "fetched", "fetchedAt", "updated", "updatedAt",
                 "builtAt", "buildDate", "timestamp", "asOf", "retrieved"}


def digest(path):
    """A hash of what this file MEANS, with the clock taken out of it.

    Measured, not assumed: re-running all five pre-gate writers with nothing
    new to report changes exactly one file, data/claims.json, because the
    claims worker stamps `generated` at response time. streets.json and
    open_lamps.json carry a `generated` DATE, which is stable within a day and
    would only ever move the gate once — but it is the same kind of fact and
    is dropped for the same reason.

    The byte scan is a fast path, not a filter: nearly every file skips the
    parse entirely, and only the handful that mention one of these keys pays
    for json.loads. Scanning the whole file rather than a prefix because a
    stamp is not guaranteed to be near the top.
    """
    raw = path.read_bytes()
    if path.suffix != ".json":
        return hashlib.sha256(raw).hexdigest()
    if not any(('"%s"' % k).encode() in raw for k in VOLATILE_KEYS):
        return hashlib.sha256(raw).hexdigest()
    try:
        doc = json.loads(raw)
    except ValueError:
        return hashlib.sha256(raw).hexdigest()
    if isinstance(doc, dict):
        doc = {k: v for k, v in doc.items() if k not in VOLATILE_KEYS}
        raw = json.dumps(doc, sort_keys=True,
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def manifest(root="."):
    out = {}
    root = Path(root)
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts):
            continue
        try:
            out[str(rel)] = digest(p)
        except OSError:
            pass
    return out


def main(argv):
    if len(argv) != 2 or argv[0] not in ("diff", "write"):
        sys.exit(__doc__)
    mode, store = argv[0], Path(argv[1])
    now = manifest()

    if mode == "write":
        store.write_text(json.dumps(now, sort_keys=True, indent=0))
        return 0

    if not store.exists():
        print("(no previous publish recorded)")
        return 0
    try:
        was = json.loads(store.read_text())
    except ValueError:
        print("(unreadable fingerprint store — treating as changed)")
        return 0

    for path in sorted(set(was) | set(now)):
        a, b = was.get(path), now.get(path)
        if a == b:
            continue
        print("%s %s" % ("added  " if a is None else
                         "removed" if b is None else "changed", path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
