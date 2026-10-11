#!/usr/bin/env python3
"""Does the code compile, as git holds it (not as the folder holds it)?

    python3 tools/codecheck.py index          the staged files (the pre-commit hook)
    python3 tools/codecheck.py <commit>       every code file of a commit (build_code.py pack)

Compiles each .py and parses each .json under data/ with the newest Python on
the machine (the server builds with 3.14; the Mac's /usr/bin/python3 is 3.9 and
reads some f-strings differently). Prints one line per bad file, exit 1 if any.

On 2026-10-11 a commit put a line of one function inside another's f-string;
the server built it for an hour, failed, and published nothing.
"""

import json
import os
import shutil
import subprocess
import sys

NEWER = ("python3.14", "python3.13", "python3.12")


def newest_python():
    if sys.version_info >= (3, 12):
        return None
    for name in NEWER:
        for d in ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
        p = shutil.which(name)
        if p:
            return p
    return None


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def staged():
    out = git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
    return [p for p in out.decode("utf-8").split("\0") if p]


def in_commit(ref):
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "build_code", os.path.join(here, "..", "importers", "build_code.py"))
    bc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bc)
    return list(bc.committed(ref))


def blob(ref, path):
    return git("show", (":" if ref == "index" else ref + ":") + path)


def check(ref):
    paths = staged() if ref == "index" else in_commit(ref)
    bad = []
    for path in paths:
        if path.endswith(".py"):
            try:
                compile(blob(ref, path), path, "exec", dont_inherit=True)
            except SyntaxError as e:
                bad.append("%s:%s %s" % (path, e.lineno, e.msg))
        elif path.endswith(".json") and path.startswith("data/"):
            try:
                json.loads(blob(ref, path))
            except ValueError as e:
                bad.append("%s %s" % (path, e))
    return bad


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    py = newest_python()
    if py:
        os.execv(py, [py, os.path.abspath(__file__), *argv])
    bad = check(argv[0])
    for line in bad:
        print(line)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
