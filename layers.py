"""The layers build.py runs, one at a time, each on its own.

    layers.start(DOCS, FINAL)            once, when build() has its output folder
    layers.run("toilets", lambda: ...)   one layer; its result, or a line saying it failed
    layers.finish()                      once, at the end: the ledger and a summary

A layer that raises does not end the build (2026-10-11: one torn ledger line in
doodlerepo_layer cost all 272,000 pages, round after round). Its error is
printed, and the files it wrote last time it worked are copied from the live
tree (FINAL, docs/) into this build's tree (docs.next/) where this build has
not written them, so its pages stay up a round old instead of dropping out.

The ledger, MD_LAYER_STATE or cache/layers.json, holds for each layer: seconds,
whether it worked, its error, the files it wrote under the output folder, and
the files it read from disk outside it. A layer that fails keeps its last good
list of outputs. tools/layers_report.py reads it.

MD_LAYER_STRICT=1 re-raises instead, for a session testing its own layer.
"""

import builtins
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get("MD_LAYER_STATE") or ROOT / "cache" / "layers.json")
STRICT = os.environ.get("MD_LAYER_STRICT") == "1"

_docs = None       # this build's output folder
_final = None      # the live tree, or None for a build in place
_prev = {}         # the ledger as the last build left it
_now = {}          # this build's rows
_order = []


def start(docs, final=None):
    global _docs, _final, _prev
    _docs, _final = Path(docs).resolve(), (Path(final).resolve() if final else None)
    try:
        _prev = json.loads(STATE.read_text()).get("layers", {})
    except (OSError, ValueError):
        _prev = {}


class _Watch:
    """Notes every file opened for writing under the output folder, and every
    file read outside it, while one layer runs."""

    def __init__(self):
        self.wrote, self.read = set(), set()

    def _note(self, path, mode):
        try:
            p = Path(os.fspath(path)).resolve()
        except (TypeError, ValueError, OSError):
            return
        s = str(p)
        docs = str(_docs)
        if s.startswith(docs + os.sep):
            if any(c in mode for c in "wax+"):
                self.wrote.add(s[len(docs) + 1:])
        elif "r" in mode and "+" not in mode and s.startswith(str(ROOT) + os.sep):
            self.read.add(s[len(str(ROOT)) + 1:])

    def __enter__(self):
        w = self
        self.saved = (Path.write_text, Path.write_bytes, Path.read_text, Path.read_bytes,
                      Path.open, builtins.open, shutil.copyfile, shutil.copy2,
                      shutil.copy, shutil.copytree)
        wt, wb, rt, rb, po, bo, cf, c2, cp, ct = self.saved

        def write_text(self, *a, **k):
            w._note(self, "w")
            return wt(self, *a, **k)

        def write_bytes(self, *a, **k):
            w._note(self, "w")
            return wb(self, *a, **k)

        def read_text(self, *a, **k):
            w._note(self, "r")
            return rt(self, *a, **k)

        def read_bytes(self, *a, **k):
            w._note(self, "r")
            return rb(self, *a, **k)

        def path_open(self, mode="r", *a, **k):
            w._note(self, mode)
            return po(self, mode, *a, **k)

        def open_(file, mode="r", *a, **k):
            if not isinstance(file, int):
                w._note(file, mode)
            return bo(file, mode, *a, **k)

        def copyfile(src, dst, *a, **k):
            w._note(src, "r")
            out = cf(src, dst, *a, **k)
            w._note(out, "w")
            return out

        def copy2(src, dst, *a, **k):
            w._note(src, "r")
            out = c2(src, dst, *a, **k)
            w._note(out, "w")
            return out

        def copy(src, dst, *a, **k):
            w._note(src, "r")
            out = cp(src, dst, *a, **k)
            w._note(out, "w")
            return out

        def copytree(src, dst, *a, **k):
            out = ct(src, dst, *a, **k)
            for dirpath, _, files in os.walk(out):
                for n in files:
                    w._note(os.path.join(dirpath, n), "w")
            return out

        Path.write_text, Path.write_bytes = write_text, write_bytes
        Path.read_text, Path.read_bytes, Path.open = read_text, read_bytes, path_open
        builtins.open = open_
        shutil.copyfile, shutil.copy2, shutil.copy, shutil.copytree = copyfile, copy2, copy, copytree
        return self

    def __exit__(self, *exc):
        (Path.write_text, Path.write_bytes, Path.read_text, Path.read_bytes,
         Path.open, builtins.open, shutil.copyfile, shutil.copy2,
         shutil.copy, shutil.copytree) = self.saved
        return False


def _restore(name):
    """The files this layer wrote when it last worked, from the live tree, where
    this build has not written them. Returns how many were put back."""
    if _final is None or _docs is None:
        return 0
    n = 0
    for rel in _prev.get(name, {}).get("outputs", []):
        dst, src = _docs / rel, _final / rel
        if dst.exists() or not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def run(name, fn):
    """fn() as layer `name`. Its result, or, if it raised, a line saying so."""
    if _docs is None:   # build() did not call start(): a script importing build
        return fn()
    _order.append(name)
    t0 = time.monotonic()
    watch = _Watch()
    try:
        with watch:
            result = fn()
    except Exception as e:  # noqa: BLE001 — one layer, not the build
        if STRICT:
            raise
        secs = time.monotonic() - t0
        err = "%s: %s" % (type(e).__name__, e)
        tb = traceback.extract_tb(e.__traceback__)[-1]
        back = _restore(name)
        last = _prev.get(name, {})
        _now[name] = {"ok": False, "seconds": round(secs, 1), "error": err[:400],
                      "where": "%s:%s" % (os.path.basename(tb.filename), tb.lineno),
                      "outputs": last.get("outputs", []), "reads": last.get("reads", []),
                      "wrote_before_failing": len(watch.wrote), "restored": back,
                      "last_ok": last.get("last_ok")}
        print("  !! layer %s FAILED (%s at %s); %d file(s) of its last good build put back"
              % (name, err[:200], _now[name]["where"], back), file=sys.stderr)
        return "FAILED, %d file(s) from the last good build" % back
    _now[name] = {"ok": True, "seconds": round(time.monotonic() - t0, 1),
                  "outputs": sorted(watch.wrote), "reads": sorted(watch.read),
                  "last_ok": time.strftime("%Y-%m-%dT%H:%M:%S")}
    return result


def failed():
    return [n for n in _order if not _now[n]["ok"]]


def finish():
    if _docs is None:
        return
    rows = dict(_prev)
    rows.update(_now)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".part")
    tmp.write_text(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "order": _order,
                               "failed": failed(), "layers": rows},
                              ensure_ascii=False, indent=0))
    os.replace(tmp, STATE)
    slow = sorted(_order, key=lambda n: -_now[n]["seconds"])[:5]
    print("layers: %d run, %d failed%s; slowest %s" % (
        len(_order), len(failed()), (" (" + ", ".join(failed()) + ")") if failed() else "",
        ", ".join("%s %.0fs" % (n, _now[n]["seconds"]) for n in slow)))
