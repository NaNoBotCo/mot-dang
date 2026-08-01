#!/usr/bin/env python3
"""Does choosing the errands together actually beat choosing them one by one?

    python3 tests/test_errands.py

The errand solver on plan.html rests on one claim: when you need a pharmacy AND
an ATM AND som tam, picking the nearest of each independently is not the same
answer as picking the three that make the shortest single round — and is often
worse. If that claim is false the feature is decoration, so it is measured here
rather than asserted.

This reimplements the solver's search in Python over the same road graph the
browser uses, and runs it on real errand combinations from real starting points.
Two things must hold:

1. **The joint answer is never longer than the naive one.** It searches a
   superset — the naive pick is one of the combinations it considers — so a
   loss means a bug in the search, not a bad day.
2. **It is sometimes strictly shorter.** If it never wins, the premise is wrong
   and the page should stop claiming it.

The page itself only claims a saving when there is one, and says so plainly
when the nearest-of-each is just as good.
"""
import json
import math
import random
import sys
from itertools import permutations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
from routing import Graph, hav                                   # noqa: E402

CAND = 6          # candidates per errand, same as the page
NOWAY = 1e7


def best_open_path(matrix, start, rest):
    """Shortest open path from `start` through every index in `rest`."""
    best, best_len = None, float("inf")
    for order in permutations(rest):
        seq = (start,) + order
        total = 0.0
        for i in range(len(seq) - 1):
            v = matrix[seq[i]][seq[i + 1]]
            total += NOWAY if v is None else v
        if total < best_len:
            best, best_len = seq, total
    return best, best_len


def main():
    g = Graph.load()
    if g is None:
        print("no data/road_graph.json — nothing to check")
        return 0
    area = g.area
    records = []
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / ("%s.json" % prov)
        if f.exists():
            records += json.loads(f.read_text())
    inbox = [r for r in records if r.get("lat") is not None
             and area["s"] < r["lat"] < area["n"]
             and area["w"] < r["lng"] < area["e"]]

    bysub = {}
    for r in inbox:
        for s in r.get("sub") or []:
            bysub.setdefault(s, []).append(r)
    for c in ("essentials", "food", "medical", "beauty"):
        bysub.setdefault(c, [])
    for r in inbox:
        for c in r.get("cat") or []:
            if c in bysub:
                bysub[c].append(r)

    kinds = [k for k, v in bysub.items() if len(v) >= CAND]
    if len(kinds) < 2:
        print("not enough errand kinds inside the routable box to test")
        return 0

    rnd = random.Random(20260801)      # fixed: a flaky test is worse than none
    trials, wins, losses = 0, 0, 0
    savings = []
    for _ in range(24):
        picked = rnd.sample(kinds, rnd.choice([2, 3]))
        anchor = rnd.choice(inbox)
        a = (anchor["lat"], anchor["lng"])
        slots = []
        for k in picked:
            pool = sorted(bysub[k], key=lambda r: hav(a, (r["lat"], r["lng"])))[:CAND]
            slots.append(pool)
        pts = [a] + [(r["lat"], r["lng"]) for pool in slots for r in pool]
        M = g.matrix(pts, "foot")
        # index of each candidate in pts
        idx, at = [], 1
        for pool in slots:
            idx.append(list(range(at, at + len(pool))))
            at += len(pool)

        joint = float("inf")
        for combo in product(*idx):
            _o, L = best_open_path(M, 0, list(combo))
            joint = min(joint, L)
        naive_combo = [group[0] for group in idx]      # nearest of each
        _o, naive = best_open_path(M, 0, naive_combo)
        if joint >= NOWAY / 2 or naive >= NOWAY / 2:
            continue                                    # unroutable, not a case
        trials += 1
        if joint > naive + 1e-6:
            losses += 1
        elif naive - joint > 1.0:
            wins += 1
            savings.append(naive - joint)

    print("routable trials          %d" % trials)
    print("joint beat nearest-of-each %d" % wins)
    print("joint LOST to it         %d   (must be 0 — it searches a superset)" % losses)
    if savings:
        savings.sort()
        print("saving when it wins      median %.0f m · best %.0f m"
              % (savings[len(savings) // 2], savings[-1]))
    if not trials:
        print("no routable trials — cannot judge")
        return 0
    if losses:
        print("FAIL — the search returned a worse answer than one of its own options")
        return 1
    if not wins:
        print("FAIL — never better than the naive pick, so the feature claims "
              "something it does not deliver")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
