#!/usr/bin/env python3
"""Doodle votes and notes → weighted scores, voter flags and the payout ledger.

Nan, 2026-10-05: "a flexible and fuzzy scoring system, not discriminating between bots and humans,
paying $0.001 dollars per like/dislike + brief explanation. We should very strictly demonitize bots
that appear to be too aggressive, but otherwise pay fairly for feedback." Then: "I'd like both bots
and humans to leave notes about what's right/wrong with the picture, and get paid more for
thoroughness, up to 5 cents."

Reads cache/doodle_votes/events.jsonl (importers/sync_doodle_votes.py). Without it, falls back to the
public tallies in data/doodles/votes.json at weight 1, with no flags and no ledger.

  A VOTE is a voter's last word on one axis of one doodle version (a change replaces it, 0 takes it back).
  A NOTE is the voter's latest note on that doodle version: what is right and wrong with the picture.
  A VOTER is a hash of address and browser; a PAYEE is the payout address a voter gave. Neither says
  human or bot, and nothing here asks.

  THOROUGHNESS of a note, 0 to 1: the bytes it adds once compressed against every note other voters left
  on the same doodle before it (zlib with those notes as its dictionary), from NOVEL_FLOOR to NOVEL_FULL.
  Padding and repetition compress away; a note copied from an earlier one adds next to nothing.

  FLAGS, per voter and per payee, per Bangkok day — any one demonetizes that payee for the day and the
  DEMONETIZE_DAYS after it, and weighs the voter's votes at FLAGGED_WEIGHT:
    burst     BURST_N or more votes inside BURST_S seconds
    flood     more than DAY_MAX votes in a day
    copy      at least COPY_MIN notes and fewer than COPY_UNIQUE of them distinct
    thin      a payee's notes, at least THIN_MIN of them, more than THIN_SHARE too short to say anything
    onesided  at least ONESIDED_MIN votes, every one the same way
    many      one payee from SYBIL_VOTERS or more voters in a day, or one voter naming two payees

  WEIGHT of a vote: NOTELESS_WEIGHT without a usable note, else 1 + thoroughness/2 (up to 1.5);
  × FLAGGED_WEIGHT on a flagged day; × agreement (0.5 to 1.5: how often the voter sided with everyone
  else, once they have AGREE_MIN votes on doodles others voted on too).

  SCORE of a doodle on an axis: Beta(PRIOR + weighted ups, PRIOR + weighted downs). `mean` is the score,
  `low` the probability the drawing is below even on that axis: one stray thumb moves it a little, a
  crowd a lot.

  PICKS (Nan, 2026-10-05: "I want the .0001 dollar one to be choosing the better of 2 images"): a pick
  of two doodles from /doodles/pick/ is a win for one and a loss for the other on a third axis,
  `overall`, at PICK_WEIGHT; "can't tell" is half a win for each. A pair counts when it is two versions
  of one doodle or two drawn by different code (doodlerepo_layer.drawn_apart). Pick flags, per voter and payee per day: pickburst (PICK_BURST_N inside
  BURST_S seconds), pickflood (over PICK_DAY_MAX), side (at least SIDE_MIN picks, SIDE_SHARE or more on
  one side of the screen), tie (at least SIDE_MIN picks, SIDE_SHARE or more "can't tell").

  CHECK: a note worth JUDGE_FROM or more is held until tools/doodle_judge.py has shown it to Claude with
  the picture, and then pays by thoroughness × the check's score (0 to 1, how much of it is about this
  picture); its vote weighs 0.5 + that score as well. A refused check holds the note.

  PAY, per standing valid pick: PICK_PAY. Per voter per doodle version: PAY_MIN + (PAY_MAX − PAY_MIN) ×
  thoroughness (× the check's score at JUDGE_FROM or more), when a vote on it
  still stands, its note is usable, the voter named a payee, and that payee was not demonetized on the
  day the vote was first cast. A payee's day stops at PAYEE_DAY_CAP; what is over it is held.
  Paid amounts are read from cache/doodle_votes/paid.jsonl ({payee, usd, at, ref}), written by whoever
  pays; nothing here moves money.

    python3 tools/doodle_score.py           summary: voters, flags, the ledger
    python3 tools/doodle_score.py --flags   every flag with its day and reason
    python3 tools/doodle_score.py --json    everything, as JSON
"""
import datetime as dt
import json
import math
import re
import sys
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import doodlerepo_layer  # noqa: E402
EVENTS = ROOT / "cache" / "doodle_votes" / "events.jsonl"
PAID = ROOT / "cache" / "doodle_votes" / "paid.jsonl"
LEDGER = ROOT / "cache" / "doodle_votes" / "ledger.json"
VOTES = ROOT / "data" / "doodles" / "votes.json"
AXES = ("accuracy", "aesthetics")
SCORE_AXES = AXES + ("overall",)

PAY_MIN, PAY_MAX = 0.001, 0.05
PICK_PAY = 0.0001
PICK_WEIGHT = 0.5
PICK_BURST_N, PICK_DAY_MAX = 20, 1500
SIDE_MIN, SIDE_SHARE = 40, 0.9
PAYEE_DAY_CAP = 1.00
JUDGE_FROM = 0.005
JUDGED = ROOT / "cache" / "doodle_votes" / "judged.json"
NOVEL_FLOOR, NOVEL_FULL = 20, 500   # compressed bytes
PRIOR = 2.0
NOTE_MIN = 12          # visible characters
NOTELESS_WEIGHT = 0.5
FLAGGED_WEIGHT = 0.2
DEMONETIZE_DAYS = 7
BURST_N, BURST_S = 8, 60
DAY_MAX = 300
COPY_MIN, COPY_UNIQUE = 10, 0.7
THIN_MIN, THIN_SHARE = 10, 0.3
ONESIDED_MIN = 30
SYBIL_VOTERS = 4
AGREE_MIN = 5


def bkk_day(iso):
    return (dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) + dt.timedelta(hours=7)).date().isoformat()


def note_of(e):
    return e.get("note") or e.get("why") or ""


def usable(note):
    """A note that says something: NOTE_MIN visible characters, not one character repeated."""
    t = re.sub(r"\s+", "", note or "")
    return len(t) >= NOTE_MIN and len(set(t.lower())) >= 4


def norm(note):
    return re.sub(r"[^\w\u0E00-\u0E7F]+|[\d_]+", " ", (note or "").lower()).strip()


def novel_bytes(note, before):
    """Compressed bytes the note adds to the notes before it (zlib, those notes as the dictionary)."""
    def size(zd):
        c = zlib.compressobj(9, zlib.DEFLATED, 15, 9, zlib.Z_DEFAULT_STRATEGY, *([zd] if zd else []))
        return len(c.compress(norm(note).encode()) + c.flush()) - len(zlib.compressobj(9, zlib.DEFLATED, 15, 9, zlib.Z_DEFAULT_STRATEGY, *([zd] if zd else [])).flush())
    zd = " ".join(norm(n) for n in before).encode()[-32000:]
    return max(0, size(zd))


def thoroughness(note, before=()):
    if not usable(note):
        return 0.0
    return max(0.0, min(1.0, (novel_bytes(note, before) - NOVEL_FLOOR) / (NOVEL_FULL - NOVEL_FLOOR)))


def note_key(n):
    """A note's id for tools/doodle_judge.py: voter, doodle version and the words."""
    import hashlib
    return hashlib.sha256(("%s|%s|%s" % (n["voter"], n["doc"], n["note"])).encode()).hexdigest()[:16]


def judgments():
    return json.loads(JUDGED.read_text()) if JUDGED.exists() else {}


def note_usd(n, J):
    """(usd, state): state is 'paid', 'pending' (waiting for the check) or 'refused'."""
    usd = PAY_MIN + (PAY_MAX - PAY_MIN) * n["t"]
    if usd < JUDGE_FROM:
        return usd, "paid"
    j = J.get(note_key(n))
    if not j:
        return usd, "pending"
    if j.get("score") is None:
        return usd, "refused"
    return PAY_MIN + (PAY_MAX - PAY_MIN) * n["t"] * j["score"], "paid"


def load_events():
    if not EVENTS.exists():
        return []
    return [json.loads(x) for x in EVENTS.read_text().splitlines() if x.strip()]


def final_votes(events):
    """({(voter, id@v, axis): vote}, {(voter, id@v): note record}) — last sign, first cast, latest note, payee."""
    out, notes, payee_of = {}, {}, {}
    for e in sorted(events, key=lambda e: e["k"]):
        if e.get("kind") == "pick":
            if e.get("payee"):
                payee_of[e["voter"]] = e["payee"]
            continue
        doc = "%s@%s" % (e["id"], e["v"])
        if e.get("payee"):
            payee_of[e["voter"]] = e["payee"]
        for a, x in (e.get("votes") or {}).items():
            k = (e["voter"], doc, a)
            o = out.setdefault(k, {"voter": e["voter"], "doc": doc, "axis": a, "first": e["at"], "x": 0})
            o["x"] = x
        if note_of(e):
            n = notes.setdefault((e["voter"], doc), {"voter": e["voter"], "doc": doc, "first": e["at"]})
            n["note"], n["at"] = note_of(e), e["at"]
    for n in notes.values():
        n["payee"] = payee_of.get(n["voter"], "")
    for o in out.values():
        o["payee"] = payee_of.get(o["voter"], "")
    return out, notes


def final_picks(events):
    """{(voter, pair): pick} — the voter's last pick of each pair, with its first day and payee."""
    out, payee_of = {}, {}
    for e in sorted(events, key=lambda e: e["k"]):
        if e.get("payee"):
            payee_of[e["voter"]] = e["payee"]
        if e.get("kind") != "pick":
            continue
        k = (e["voter"], tuple(e["pair"]))
        o = out.setdefault(k, {"voter": e["voter"], "pair": tuple(e["pair"]), "first": e["at"]})
        o["won"] = e["won"]
    for o in out.values():
        o["payee"] = payee_of.get(o["voter"], "")
    return out


def fair_pair(pair, meta):
    """Two versions of one doodle, or two drawn by different code (doodlerepo_layer.drawn_apart)."""
    (a, va), (b, vb) = (x.rpartition("@")[::2] for x in pair)
    if a == b:
        return va != vb and a in meta
    return a in meta and b in meta and doodlerepo_layer.drawn_apart(*meta[a], a, *meta[b], b)


def repo_meta():
    vers, _, _ = doodlerepo_layer.load()
    return {i: (vs[-1]["c"], vs[-1].get("sub") or "") for i, vs in vers.items()}


def with_thoroughness(notes):
    """Each note's thoroughness against the notes other voters left on that doodle before it."""
    by_doc = defaultdict(list)
    for n in notes.values():
        by_doc[n["doc"]].append(n)
    for ns in by_doc.values():
        ns.sort(key=lambda n: n["at"])
        for j, n in enumerate(ns):
            n["t"] = thoroughness(n["note"], [m["note"] for m in ns[:j] if m["voter"] != n["voter"]])
    return notes


def flags(events):
    """{('voter'|'payee', who): {day: [reasons]}}"""
    F = defaultdict(lambda: defaultdict(list))
    by = defaultdict(list)
    payees_of_voter = defaultdict(set)
    for e in events:
        if e.get("kind") == "pick":
            continue
        n = len(e.get("votes") or {})
        for who in (("voter", e["voter"]),) + ((("payee", e["payee"]),) if e.get("payee") else ()):
            by[who].append((e["at"], n, note_of(e), e.get("votes") or {}, e["voter"]))
        if e.get("payee"):
            payees_of_voter[e["voter"]].add(e["payee"])
    picks = defaultdict(list)
    for e in events:
        if e.get("kind") == "pick":
            for who in (("voter", e["voter"]),) + ((("payee", e["payee"]),) if e.get("payee") else ()):
                picks[who].append((e["at"], e.get("side", "")))
    for who, rows in picks.items():
        days = defaultdict(list)
        for r in rows:
            days[bkk_day(r[0])].append(r)
        for day, rs in days.items():
            rs.sort()
            ts = [dt.datetime.fromisoformat(r[0].replace("Z", "+00:00")).timestamp() for r in rs]
            j = 0
            for i in range(len(ts)):
                while ts[i] - ts[j] > BURST_S:
                    j += 1
                if i - j + 1 >= PICK_BURST_N:
                    F[who][day].append("pickburst: %d picks inside %d s" % (i - j + 1, BURST_S))
                    break
            if len(rs) > PICK_DAY_MAX:
                F[who][day].append("pickflood: %d picks in a day" % len(rs))
            ties = sum(r[1] == "same" for r in rs)
            if len(rs) >= SIDE_MIN and ties / len(rs) >= SIDE_SHARE:
                F[who][day].append("tie: %d of %d picks can't tell" % (ties, len(rs)))
            sides = [r[1] for r in rs if r[1] in ("a", "b")]
            if len(sides) >= SIDE_MIN and max(sides.count("a"), sides.count("b")) / len(sides) >= SIDE_SHARE:
                F[who][day].append("side: %d of %d picks on one side" % (max(sides.count("a"), sides.count("b")), len(sides)))
    for who, rows in by.items():
        days = defaultdict(list)
        for r in rows:
            days[bkk_day(r[0])].append(r)
        for day, rs in days.items():
            rs.sort()
            ts = [dt.datetime.fromisoformat(r[0].replace("Z", "+00:00")).timestamp() for r in rs]
            j = 0
            for i in range(len(ts)):
                while ts[i] - ts[j] > BURST_S:
                    j += 1
                k = sum(r[1] for r in rs[j:i + 1])
                if k >= BURST_N:
                    F[who][day].append("burst: %d votes inside %d s" % (k, BURST_S))
                    break
            total = sum(r[1] for r in rs)
            if total > DAY_MAX:
                F[who][day].append("flood: %d votes in a day" % total)
            given = [r[2] for r in rs if r[2]]
            ns = [norm(w) for w in given]
            if len(ns) >= COPY_MIN and len(set(ns)) / len(ns) < COPY_UNIQUE:
                F[who][day].append("copy: %d distinct notes in %d" % (len(set(ns)), len(ns)))
            if who[0] == "payee":
                thin = sum(not usable(w) for w in given)
                if len(given) >= THIN_MIN and thin / len(given) > THIN_SHARE:
                    F[who][day].append("thin: %d of %d notes too short" % (thin, len(given)))
                vs = {r[4] for r in rs}
                if len(vs) >= SYBIL_VOTERS:
                    F[who][day].append("many: one payee from %d voters" % len(vs))
            signs = [x for r in rs for x in r[3].values() if x]
            if len(signs) >= ONESIDED_MIN and len(set(signs)) == 1:
                F[who][day].append("onesided: %d votes, all %s" % (len(signs), "up" if signs[0] > 0 else "down"))
            if who[0] == "voter" and len(payees_of_voter[who[1]]) > 1:
                F[who][day].append("many: one voter naming %d payees" % len(payees_of_voter[who[1]]))
    return F


def demonetized(F, who, day):
    d0 = dt.date.fromisoformat(day)
    return any(0 <= (d0 - dt.date.fromisoformat(fd)).days <= DEMONETIZE_DAYS for fd in F.get(who, {}))


def agreement(V):
    """{voter: 0.5–1.5} — how often a voter sided with everyone else's majority."""
    sums = defaultdict(lambda: [0, 0])
    for o in V.values():
        if o["x"]:
            sums[(o["doc"], o["axis"])][0 if o["x"] > 0 else 1] += 1
    hit, n = defaultdict(int), defaultdict(int)
    for o in V.values():
        if not o["x"]:
            continue
        up, down = sums[(o["doc"], o["axis"])]
        up, down = up - (o["x"] > 0), down - (o["x"] < 0)
        if up + down < 2 or up == down:
            continue
        n[o["voter"]] += 1
        hit[o["voter"]] += (up > down) == (o["x"] > 0)
    return {v: 0.5 + hit[v] / n[v] for v in n if n[v] >= AGREE_MIN}


def p_below_half(a, b, steps=400):
    """P(θ < 0.5) for θ ~ Beta(a, b), by Simpson's rule."""
    lnB = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    f = lambda x: math.exp((a - 1) * math.log(x) + (b - 1) * math.log(1 - x) - lnB) if 0 < x < 1 else 0.0
    h = 0.5 / steps
    s = f(1e-9) + f(0.5) + sum((4 if i % 2 else 2) * f(i * h) for i in range(1, steps))
    return min(1.0, max(0.0, s * h / 3))


def score(up, down):
    a, b = PRIOR + up, PRIOR + down
    return {"up": round(up, 3), "down": round(down, 3), "mean": round(a / (a + b), 3), "low": round(p_below_half(a, b), 3)}


def flagged(F, voter, payee, day):
    return demonetized(F, ("voter", voter), day) or bool(payee and demonetized(F, ("payee", payee), day))


def weighted():
    """({doc: {axis: [w_up, w_down]}}, {doc: {axis: [(weight, note)] of downs}}, events, votes, notes, flags)."""
    events = load_events()
    W, notes_down = defaultdict(lambda: {a: [0.0, 0.0] for a in SCORE_AXES}), defaultdict(lambda: defaultdict(list))
    if not events:
        t = json.loads(VOTES.read_text()).get("tallies", {}) if VOTES.exists() else {}
        for doc, r in t.items():
            for a in AXES:
                if isinstance(r.get(a), list):
                    W[doc][a] = [float(r[a][0]), float(r[a][1])]
        return W, notes_down, [], {}, {}, {}, {}
    V, N = final_votes(events)
    N, F = with_thoroughness(N), flags(events)
    ag, J = agreement(V), judgments()
    for o in V.values():
        if not o["x"]:
            continue
        n = N.get((o["voter"], o["doc"]))
        w = (1.0 + n["t"] / 2 if n and usable(n["note"]) else NOTELESS_WEIGHT) * ag.get(o["voter"], 1.0)
        j = J.get(note_key(n)) if n else None
        if j and j.get("score") is not None:
            w *= 0.5 + j["score"]
        if flagged(F, o["voter"], o["payee"], bkk_day(o["first"])):
            w *= FLAGGED_WEIGHT
        W[o["doc"]][o["axis"]][0 if o["x"] > 0 else 1] += w
        if o["x"] < 0 and n and usable(n["note"]):
            notes_down[o["doc"]][o["axis"]].append((w, n["note"]))
    K, meta = final_picks(events), repo_meta()
    for o in K.values():
        if not fair_pair(o["pair"], meta):
            continue
        w = PICK_WEIGHT * ag.get(o["voter"], 1.0)
        if flagged(F, o["voter"], o["payee"], bkk_day(o["first"])):
            w *= FLAGGED_WEIGHT
        for d in o["pair"]:
            if o["won"]:
                W[d]["overall"][0 if d == o["won"] else 1] += w
            else:   # can't tell
                W[d]["overall"][0] += w / 2
                W[d]["overall"][1] += w / 2
    return W, notes_down, events, V, N, F, K


def ledger(V, N, F, K=None):
    """{payee: {earned, paid, owed, notes, picks, days: {day: usd}, held: {day: usd}}}."""
    first_vote = {}
    for o in V.values():
        if o["x"]:
            k = (o["voter"], o["doc"])
            first_vote[k] = min(first_vote.get(k, o["first"]), o["first"])
    L = defaultdict(lambda: {"notes": 0, "picks": 0, "pending": 0.0, "days": defaultdict(float), "held": defaultdict(float)})
    J, items = judgments(), []
    for k, n in N.items():
        if k in first_vote and n["payee"] and usable(n["note"]):
            usd, state = note_usd(n, J)
            if state == "pending":
                L[n["payee"]]["pending"] += usd
            elif state == "refused":
                L[n["payee"]]["held"][bkk_day(first_vote[k])] += usd
            else:
                items.append(("notes", n["voter"], n["payee"], first_vote[k], usd))
    meta = repo_meta() if K else {}
    items += [("picks", o["voter"], o["payee"], o["first"], PICK_PAY) for o in (K or {}).values()
              if o["payee"] and fair_pair(o["pair"], meta)]
    for what, voter, payee, first, usd in sorted(items, key=lambda x: x[3]):
        day, P = bkk_day(first), L[payee]
        if flagged(F, voter, payee, day):
            P["held"][day] += usd
            continue
        room = max(0.0, PAYEE_DAY_CAP - P["days"][day])
        P["days"][day] += min(usd, room)
        if usd > room:
            P["held"][day] += usd - room
        P[what] += 1
    paid = defaultdict(float)
    if PAID.exists():
        for x in PAID.read_text().splitlines():
            if x.strip():
                r = json.loads(x)
                paid[r["payee"]] += float(r["usd"])
    out = {}
    for p, P in L.items():
        earned = round(sum(P["days"].values()), 6)
        out[p] = {"earned": earned, "paid": round(paid[p], 6), "owed": round(earned - paid[p], 6), "notes": P["notes"], "picks": P["picks"], "pending": round(P["pending"], 6),
                  "days": {d: round(u, 6) for d, u in P["days"].items()}, "held": {d: round(u, 6) for d, u in P["held"].items()}}
    return out


def main(a):
    W, _, events, V, N, F, K = weighted()
    if not events:
        print("no event log (cache/doodle_votes/events.jsonl): scores from public tallies, no flags, no ledger")
        return
    L = ledger(V, N, F, K)
    flat = [{"who": w[0], "id": w[1], "day": d, "why": r} for w, ds in F.items() for d, rs in ds.items() for r in rs]
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps({"pay": [PAY_MIN, PAY_MAX], "day_cap": PAYEE_DAY_CAP, "payees": L, "flags": flat}, ensure_ascii=False, indent=1))
    if "--json" in a:
        print(json.dumps({"payees": L, "flags": flat, "scores": {d: {x: score(*w[x]) for x in SCORE_AXES} for d, w in W.items()}},
                         ensure_ascii=False, indent=1))
        return
    print("%d events · %d voters · %d standing votes · %d notes · %d picks · %d doodle versions" % (
        len(events), len({e["voter"] for e in events}), sum(1 for o in V.values() if o["x"]), len(N), len(K), len(W)))
    print("flags: %d (%d voters, %d payees)" % (len(flat), len({f["id"] for f in flat if f["who"] == "voter"}),
                                                len({f["id"] for f in flat if f["who"] == "payee"})))
    if "--flags" in a:
        for f in sorted(flat, key=lambda f: (f["day"], f["who"], f["id"])):
            print("  %s  %-5s %-28s %s" % (f["day"], f["who"], f["id"][:28], f["why"]))
    print("ledger: %d payees · earned $%.3f · owed $%.3f · held $%.3f" % (
        len(L), sum(p["earned"] for p in L.values()), sum(p["owed"] for p in L.values()),
        sum(sum(p["held"].values()) for p in L.values())))
    for p, P in sorted(L.items(), key=lambda x: -x[1]["owed"])[:20]:
        held = sum(P["held"].values())
        print("  %-36s %4d notes %5d picks  owed $%.4f%s%s" % (p[:36], P["notes"], P["picks"], P["owed"],
              "  held $%.3f" % held if held else "", "  awaiting check $%.3f" % P["pending"] if P["pending"] else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
