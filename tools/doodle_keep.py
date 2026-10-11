"""The doodles motdang.net/doodles/ shows: data/doodles/keep.json.

Nan, 2026-10-11: keep about 200 of the 80,505 to start, the unique ornate ones, and add
selectively from new batches; the whole collection lives on GitHub (FULL_URL).

  python3 tools/doodle_keep.py first [N]       the first list: every doodle in use now, then
                                               the most ornate place portraits, one per drawing,
                                               to N in all (default 200)
  python3 tools/doodle_keep.py candidates [N]  doodles in the ledger and off the list, most ornate first
  python3 tools/doodle_keep.py add ID...       keep these
  python3 tools/doodle_keep.py drop ID...      stop keeping these
  python3 tools/doodle_keep.py compact         cut ledger.jsonl and params.jsonl to the kept
                                               doodles (the whole ledger is on GitHub first)

Ornate: how many things the drawing carries beyond its kind — hills, a river, a road,
props, floors, a brand, opening hours and the like, each prop counted. One per drawing:
two portraits of the same kind with the same things drawn differ only in their words.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import doodlerepo_layer  # noqa: E402

STORE = doodlerepo_layer.STORE
KEEP = STORE / "keep.json"
FULL_URL = "https://github.com/nanobotco/motdang-doodles"
DRAWN = ("hills", "river", "road", "props", "levels", "facility", "brand", "inside",
         "oldCity", "specialty", "services", "moo", "hours")


def kept():
    try:
        return json.loads(KEEP.read_text())["ids"]
    except (OSError, ValueError, KeyError):
        return None


def write(ids, total=None):
    try:
        total = total or json.loads(KEEP.read_text()).get("total")
    except (OSError, ValueError):
        pass
    KEEP.write_text(json.dumps({"_": "the doodles motdang.net/doodles/ shows (tools/doodle_keep.py)",
                                "full": FULL_URL, "total": total, "ids": ids}, ensure_ascii=False, indent=1) + "\n")


def _feats(params, last):
    return ((params.get(last["ph"]) or {}).get("f") or {})


def score(f):
    props = f.get("props") if isinstance(f.get("props"), list) else []
    return sum(1 for k in DRAWN if f.get(k)) + len(props)


def signature(params, last):
    p = params.get(last["ph"]) or {}
    f = p.get("f") or {}
    props = f.get("props") if isinstance(f.get("props"), list) else []
    return (last.get("c"), p.get("set") or last.get("sub"), tuple(k for k in DRAWN if f.get(k)),
            tuple(sorted(map(str, props))), str(f.get("levels")))


def ranked(vers, gone, params, skip=()):
    """Place portraits, most ornate first, one per drawing, at most two of a kind."""
    best = {}
    for i, vs in vers.items():
        last = vs[-1]
        if i in skip or last.get("c") != "place":
            continue
        s = score(_feats(params, last))
        sig = signature(params, last)
        if sig not in best or (s, i) > best[sig][:2]:
            best[sig] = (s, i, sig[1])
    out, per = [], {}
    for s, i, kind in sorted(best.values(), key=lambda x: (-x[0], x[1])):
        if per.get(kind, 0) < 2:
            per[kind] = per.get(kind, 0) + 1
            out.append((s, i))
    return out


def first(n=200):
    vers, gone, params = doodlerepo_layer.load()
    live = sorted(i for i, vs in vers.items() if vs[-1].get("c") != "place" and i not in gone)
    ids = live + [i for s, i in ranked(vers, gone, params, set(live))][:max(0, n - len(live))]
    write(ids, len(vers))
    print("kept %d: %d in use now, %d place portraits" % (len(ids), len(live), len(ids) - len(live)))


def candidates(n=40):
    vers, gone, params = doodlerepo_layer.load()
    have = set(kept() or [])
    new = [(vs[-1].get("c"), i) for i, vs in vers.items() if i not in have and vs[-1].get("c") != "place"]
    for c, i in sorted(new, key=lambda x: vers[x[1]][-1]["from"], reverse=True)[:n]:
        last = vers[i][-1]
        print("%s  %-8s %s  %s" % (last["from"], c, i, last.get("en") or last.get("th") or ""))
    for s, i in ranked(vers, gone, params, have)[:n]:
        last = vers[i][-1]
        print("%s  place %d  %s  %s" % (last["from"], s, i, last.get("en") or last.get("th") or ""))


def compact():
    """Only the kept doodles' rows stay in the store (gone, relabel and version rows alike)."""
    ids = set(kept() or [])
    if not ids:
        raise SystemExit("no keep.json")
    led, pf = STORE / "ledger.jsonl", STORE / "params.jsonl"
    stat = (led.stat().st_mtime_ns, pf.stat().st_mtime_ns)
    rows, phs = [], set()
    for raw in led.read_bytes().split(b"\n"):
        if raw.strip():
            r = json.loads(raw)
            if r["id"] in ids:
                rows.append(raw)
                if "ph" in r:
                    phs.add(r["ph"])
    prm = [raw for raw in pf.read_bytes().split(b"\n") if raw.strip() and json.loads(raw)["ph"] in phs]
    if stat != (led.stat().st_mtime_ns, pf.stat().st_mtime_ns):
        raise SystemExit("the ledger changed while it was read; run again")
    for path, lines in ((led, rows), (pf, prm)):
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(b"\n".join(lines) + b"\n")
        tmp.replace(path)
    print("ledger %d rows, params %d" % (len(rows), len(prm)))


if __name__ == "__main__":
    a = sys.argv[1:] or ["candidates"]
    if a[0] == "first":
        first(int(a[1]) if len(a) > 1 else 200)
    elif a[0] == "candidates":
        candidates(int(a[1]) if len(a) > 1 else 40)
    elif a[0] in ("add", "drop"):
        ids = kept() or []
        ids = ids + [i for i in a[1:] if i not in ids] if a[0] == "add" else [i for i in ids if i not in a[1:]]
        write(ids)
        print("kept %d" % len(ids))
    elif a[0] == "compact":
        compact()
