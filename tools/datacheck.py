#!/usr/bin/env python3
"""Which data files in a hand-off do not parse?

    python3 tools/datacheck.py <staging> <working>

Prints, one per line, each .json/.jsonl/.geojson under data/ and cache/ of the
staging folder that changed since the working tree's copy (size or mtime) and
does not parse. server_walk.sh leaves those out of its copy, so the build keeps
the copy that parsed last round.

The laptop sends its folder while launchd jobs and sessions are still writing
to it. On 2026-10-11 data/doodles/ledger.jsonl arrived with half a line at its
end and the build failed on it, with this round's code and with the last good
code both.
"""

import json
import os
import sys

DIRS = ("data", "cache")
EXT = (".json", ".jsonl", ".geojson")


def parses(path):
    with open(path, "rb") as fh:
        if path.endswith(".jsonl"):
            for line in fh:
                if line.strip():
                    json.loads(line)
        else:
            json.load(fh)


def changed(a, b):
    try:
        sb = os.stat(b)
    except FileNotFoundError:
        return True
    sa = os.stat(a)
    return sa.st_size != sb.st_size or int(sa.st_mtime) != int(sb.st_mtime)


def bad_files(stage, work):
    for d in DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(stage, d)):
            dirnames[:] = [n for n in dirnames if n not in ("__pycache__", "node_modules")]
            for n in filenames:
                if not n.endswith(EXT):
                    continue
                path = os.path.join(dirpath, n)
                rel = os.path.relpath(path, stage)
                if not changed(path, os.path.join(work, rel)):
                    continue
                try:
                    parses(path)
                except (ValueError, UnicodeDecodeError):
                    yield rel
                except OSError:
                    pass


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    for rel in bad_files(*argv):
        print(rel)


if __name__ == "__main__":
    main(sys.argv[1:])
