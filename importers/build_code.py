#!/usr/bin/env python3
"""The server builds the code of a commit and the data of the folder.

    python3 importers/build_code.py pack <out.tar>        laptop: HEAD's code into a tar; prints the commit
    python3 importers/build_code.py overlay <tar> <repo>  server: the folder's code replaced by the tar's
    python3 importers/build_code.py left-out              code edited or added here and not committed
    python3 importers/build_code.py pending save          note the uncommitted code lines of right now
    python3 importers/build_code.py pending check         exit 0 once every noted line is committed

Sessions edit this tree while the walk sends it, and a half-edited build.py or
layer failed the build 58 times from 2026-09-20 to 10-05. On by
cache/build-from-commit (Nan, 2026-10-10: "build from a saved, committed copy,
not the folder other sessions are editing"): the walk sends HEAD's code beside
the folder, and the server puts it over whatever code the folder carried, so a
code edit reaches the site when its session commits it. Data — data/, the sites
under assets/<name>/, ledgers, tests' known-lists — still comes from the folder.

The code is CODE_EXT files at the top level, in CODE_DIRS, and assets/*.js.
"""

import os
import subprocess
import sys
import tarfile
from pathlib import Path

CODE_DIRS = ("importers", "publish", "tests", "tools", "fleetsearch", "worker", "worker-tt")
CODE_EXT = {".py", ".sh", ".js", ".mjs", ".cjs", ".sql", ".html", ".toml"}
TOP_EXT = {".py", ".sh", ".js"}
# Tool state and exports that sit among the code but are not the build's code.
SKIP_PARTS = {".wrangler", "node_modules", "__pycache__", "hf", "hf-dataset", ".git"}
FLAG = "cache/build-from-commit"


def is_code(rel):
    parts = rel.split("/")
    if any(p in SKIP_PARTS for p in parts):
        return False
    ext = os.path.splitext(rel)[1]
    if len(parts) == 1:
        return ext in TOP_EXT
    if parts[0] == "assets":
        return len(parts) == 2 and ext == ".js"
    return parts[0] in CODE_DIRS and ext in CODE_EXT


def git(*args, root="."):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True).stdout


def committed(ref="HEAD", root="."):
    """{path: blob id} of the code in a commit."""
    out = {}
    for line in git("ls-tree", "-r", "-z", ref, root=root).split(b"\0"):
        if not line:
            continue
        meta, path = line.split(b"\t", 1)
        path = path.decode("utf-8")
        mode, kind, blob = meta.decode().split()
        if kind == "blob" and is_code(path):
            out[path] = blob
    return out


def on_disk(repo):
    """Every code file under repo, as relative paths."""
    repo = Path(repo)
    found = [p.name for p in repo.iterdir() if p.is_file() and is_code(p.name)]
    if (repo / "assets").is_dir():
        found += ["assets/" + p.name for p in (repo / "assets").iterdir()
                  if p.is_file() and is_code("assets/" + p.name)]
    for d in CODE_DIRS:
        for dirpath, dirnames, filenames in os.walk(repo / d):
            dirnames[:] = [n for n in dirnames if n not in SKIP_PARTS]
            for n in filenames:
                rel = os.path.relpath(os.path.join(dirpath, n), repo).replace(os.sep, "/")
                if is_code(rel):
                    found.append(rel)
    return found


OK_LIST = "cache/codecheck-ok.txt"


def compiles(commit, root="."):
    """tools/codecheck.py on one commit; a commit that passed once is remembered."""
    ok = Path(root, OK_LIST)
    known = set(ok.read_text().split()) if ok.exists() else set()
    if commit in known:
        return True
    r = subprocess.run([sys.executable, "tools/codecheck.py", commit], cwd=root,
                       capture_output=True, text=True)
    if r.returncode == 0:
        with open(ok, "a") as fh:
            fh.write(commit + "\n")
        return True
    sys.stderr.write("commit %s does not compile:\n%s" % (commit[:10], r.stdout))
    return False


def newest_that_compiles(ref="HEAD", root=".", depth=30):
    """HEAD, or the newest commit before it whose code compiles (2026-10-11: a
    commit that did not compile stopped every build until a session fixed it)."""
    for commit in git("rev-list", "--first-parent", "-n", str(depth), ref, root=root).decode().split():
        if compiles(commit, root):
            return commit
    raise SystemExit("none of the last %d commits compiles" % depth)


def pack(out, ref="HEAD", root="."):
    commit = newest_that_compiles(ref, root)
    paths = sorted(committed(commit, root))
    tmp = Path(str(out) + ".part")
    with open(tmp, "wb") as fh:
        subprocess.run(["git", "-C", str(root), "archive", "--format=tar", commit, "--", *paths],
                       check=True, stdout=fh)
    os.replace(tmp, out)
    return commit


def overlay(tar, repo):
    repo = Path(repo)
    with tarfile.open(tar) as tf:
        members = [m for m in tf.getmembers() if m.isfile() and is_code(m.name)]
        keep = {m.name for m in members}
        gone = [rel for rel in on_disk(repo) if rel not in keep]
        for rel in gone:
            (repo / rel).unlink()
        # A new inode for every file, never one rewritten in place: server_walk.sh
        # is itself in the tar and is still running while this runs.
        for m in members:
            try:
                (repo / m.name).unlink()
            except FileNotFoundError:
                pass
        # filter= arrived in Python 3.12; the server runs 3.14, this Mac 3.9.
        extra = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        tf.extractall(repo, members=members, **extra)
    return len(members), gone


def left_out(root="."):
    """Code in the folder that differs from HEAD's: what this hand-off leaves behind."""
    out = []
    entries = iter(git("status", "--porcelain", "-z", "--untracked-files=all",
                       root=root).split(b"\0"))
    for line in entries:
        if len(line) < 4:
            continue
        code, rel = line[:2].decode(), line[3:].decode("utf-8")
        if "R" in code or "C" in code:
            next(entries, None)          # -z puts a rename's old path in the next entry
        if is_code(rel):
            what = "added" if code == "??" else "deleted" if "D" in code else "edited"
            out.append(what + " " + rel)
    return sorted(out)


# Nan, 2026-10-10: switch commit builds on "after they commit" — after the
# sessions whose uncommitted code the live site was built from commit it. The
# walk checks each round (standing_walk.sh) and turns cache/build-from-commit on
# when every line noted here is in HEAD. A file's lines count as committed when
# each one appears in HEAD's copy, so later edits to the same file do not hold
# it back. scratch_* files are not code anyone ships.
PENDING = "cache/build-from-commit.pending.json"


def _lines(text):
    return sorted({ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 4})


def pending_save(root="."):
    import json
    noted = {}
    for item in left_out(root):
        what, rel = item.split(" ", 1)
        if what == "deleted" or Path(rel).name.startswith("scratch_"):
            continue
        now = (Path(root) / rel).read_text(encoding="utf-8", errors="replace")
        if what == "edited":
            was = set(_lines(git("show", "HEAD:" + rel, root=root).decode("utf-8", "replace")))
            noted[rel] = [ln for ln in _lines(now) if ln not in was]
        else:
            noted[rel] = _lines(now)
    (Path(root) / PENDING).write_text(json.dumps(noted, ensure_ascii=False, indent=1))
    return noted


def pending_check(root="."):
    """The files still waiting, each with how many of its noted lines HEAD lacks."""
    import json
    noted = json.loads((Path(root) / PENDING).read_text())
    waiting = {}
    for rel, lines in noted.items():
        try:
            head = set(_lines(git("show", "HEAD:" + rel, root=root).decode("utf-8", "replace")))
        except subprocess.CalledProcessError:
            head = set()
        missing = [ln for ln in lines if ln not in head]
        if missing:
            waiting[rel] = len(missing)
    return waiting


def main(argv):
    if argv[:1] == ["pack"] and len(argv) == 2:
        print(pack(argv[1]))
    elif argv[:1] == ["overlay"] and len(argv) == 3:
        n, gone = overlay(argv[1], argv[2])
        print("%d code files from the commit; %d not in it removed%s"
              % (n, len(gone), (": " + ", ".join(gone[:12])) if gone else ""))
    elif argv == ["left-out"]:
        print("\n".join(left_out()))
    elif argv == ["pending", "save"]:
        noted = pending_save()
        print("%d files noted: %s" % (len(noted), ", ".join(sorted(noted))))
    elif argv == ["pending", "check"]:
        waiting = pending_check()
        print(", ".join("%s (%d lines)" % kv for kv in sorted(waiting.items())))
        sys.exit(1 if waiting else 0)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
