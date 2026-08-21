#!/usr/bin/env python3
"""The build lock is the one guard whose failure destroys work, so it is tested.

`ONE build.py AT A TIME` was a rule enforced by remembering to check, and it
failed twice in one afternoon: `ps aux | grep build.py` came back clean and a
second build started in the same second, wiped docs/ and killed the first
mid-write. build.take_build_lock() makes it structural. These are the four
behaviours that have to hold, and the third one is the one people get wrong.

    python3 tests/test_build_lock.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def main():
    import build

    tmp = Path(tempfile.mkdtemp()) / "build.lock"
    build.LOCK = tmp
    build._lock_held = False

    # 1. a free lock is taken, and says who holds it
    build.take_build_lock()
    check("takes a free lock", tmp.exists())
    held = build._lock_holder()
    check("records our own pid", held is not None and held[0] == os.getpid(),
          f"holder={held}")

    # 2. a SECOND build refuses while the first is alive. Run it in a real
    #    subprocess: this is the case that matters and it must not depend on
    #    anything in this interpreter's memory.
    probe = (
        "import sys, pathlib; sys.path.insert(0, %r);"
        "import build; build.LOCK = pathlib.Path(%r);"
        "build.take_build_lock(); print('TOOK IT')" % (str(ROOT), str(tmp))
    )
    r = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    check("a second build is refused while the first lives",
          r.returncode != 0 and "TOOK IT" not in r.stdout,
          f"rc={r.returncode} out={r.stdout.strip()[:60]}")
    check("the refusal names the holding pid and what to do",
          str(os.getpid()) in (r.stdout + r.stderr)
          and "scratch" in (r.stdout + r.stderr).lower(),
          "message should name the pid and offer the scratch-build escape")

    # 3. a STALE lock is taken over, not obeyed for ever. A lock left by a
    #    SIGKILLed build must never brick the repo.
    build.release_build_lock()
    dead = 999_999                      # a pid that cannot be running
    while build._alive(dead):
        dead -= 1
    tmp.write_text(f"{dead}\n2020-01-01T00:00:00\n")
    build._lock_held = False
    build.take_build_lock()
    held = build._lock_holder()
    check("a stale lock is cleared and taken",
          held is not None and held[0] == os.getpid(), f"holder={held}")

    # 4. release removes it, and release never deletes somebody else's lock
    build.release_build_lock()
    check("release removes the lock", not tmp.exists())

    build.take_build_lock()
    tmp.write_text("424242\n2020-01-01T00:00:00\n")   # somebody else took over
    build.release_build_lock()
    check("release leaves a lock that is no longer ours", tmp.exists())
    tmp.unlink(missing_ok=True)

    # 5. a scratch build is never locked — clear_docs() documents that workflow
    #    and tests/test_plan_routes.js relies on it.
    build._lock_held = False
    real_docs, build.DOCS = build.DOCS, Path(tempfile.mkdtemp())
    build.take_build_lock()
    check("a scratch build takes no lock", not tmp.exists())
    build.DOCS = real_docs

    print()
    if failures:
        print(f"{len(failures)} failure(s): {failures}")
        return 1
    print("build lock holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
