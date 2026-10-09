#!/usr/bin/env python3
"""The second axis, gated. `kind` says what a place IS; `cat` says what it sells.

Nan, 2026-09-06: "Mot Dang admits a place by its counter — this is flat wrong."
The counter rule was three functions; the replacement rule is two sentences —
admitted when a source says it exists and what it is for, PUBLISHED when the
record answers a question someone could ask OF THAT KIND OF PLACE. This test
guards the half that decides which question that is.

What it will not let happen:
  · a kind with no answer-set — a kind nothing can answer is a kind that
    condemns its members to noindex forever, which is the counter rule wearing
    a new hat;
  · an answer-set naming an attrs key that no record in the corpus carries —
    that is a promise of evidence we do not hold;
  · a rule that claims everything, or that no record matches;
  · silent growth of the unclassified pile. A residue is honest; an unwatched
    residue is how a shelf sat empty for a month.
  · a wat with its sect, founding year and register name failing the gate. 562
    of them do today, on the old rule, for want of a telephone.

    python3 tests/test_kinds.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import kind_layer as K            # noqa: E402

# There is no cap on the residue. There was one — 40, chosen on a day when the
# residue was 16, by a session, never put to Nan. She saw it and said: remove
# it (2026-09-08). The count is reported instead, on the same principle she
# set for the page-weight medians the same morning: "report the medians, don't
# cap them." A number in a log is information; the same number in an `if` is a
# rule nobody agreed to. See notes/gate-audit-2026-09-08.txt.

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def main():
    K.load(ROOT)
    records = []
    for p in ("cm", "cr"):
        records += json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text())
    tally = K.stamp(records)
    print(f"kinds: {len(K.KINDS)} · rules: {len(K.DOC['rules'])} · records: {len(records)}")

    # ── the taxonomy is complete and bilingual ────────────────────────────
    for key, k in K.KINDS.items():
        check(f"{key}: both languages", bool(k.get("th") and k.get("en")))
        check(f"{key}: glossed in both", bool(k.get("gloss_th") and k.get("gloss_en")))
        check(f"{key}: has an answer-set", key in K.DOC["answers"],
              "a kind nothing can answer is condemned to noindex")
        a = K.DOC["answers"].get(key) or {}
        check(f"{key}: says what it is asked, in both",
              bool(a.get("say_th") and a.get("say_en")))

    # ── every rule earns its place ────────────────────────────────────────
    for r in K.DOC["rules"]:
        check(f"rule {r['kind']}: names a kind that exists", r["kind"] in K.KINDS)

    # ── no orphan rule: each one must actually claim something ────────────
    # …unless it says in writing that it expects nothing yet. That is the
    # test_facets KNOWN_EMPTY discipline: a shelf may be empty, but only out
    # loud, with a reason, and the reason comes out the day it fills.
    text_of = K._text
    for i, (kind, pred, why) in enumerate(K._RULES):
        rule = K.DOC["rules"][i]
        hit = any(pred(r, text_of(r)) for r in records)
        if rule.get("expects_none"):
            check(f"rule {i} ({kind}) still expects nothing — reason on file",
                  not hit, "IT FILLED. Delete expects_none; the reason is now stale.")
            continue
        check(f"rule {i} ({kind}) matches at least one record", hit,
              "a rule that claims nothing is a rule that was never true here")

    # ── an answer-set may not promise evidence the corpus does not hold ───
    import edge_layer as _E
    projected = _E.ways(ROOT)
    attr_keys = set()
    for r in records + projected:
        attr_keys.update((r.get("attrs") or {}).keys())
    field_keys = set()
    for r in records + projected:
        field_keys.update(r.keys())
    for key, a in K.DOC["answers"].items():
        if key == "_doc":
            continue
        for at in (a.get("attrs") or []):
            check(f"{key}: attrs.{at} is a key the corpus actually carries",
                  at in attr_keys, "promised evidence we do not hold")
        for f in (a.get("fields") or []):
            check(f"{key}: field '{f}' exists on some record", f in field_keys)
        # `future` is exempt on purpose — those are the slots the field work
        # lands into, declared early so nothing is rewritten when it arrives.

    # ── the residue is reported ───────────────────────────────────────────
    # What it is: records the kind rules could not place. Worth seeing, worth
    # nobody's build failing over. Printed with what it is made of, because
    # "40 unplaced" is a number and "40 unplaced, all of them sights with no
    # sub" is something a person can act on.
    unc = tally.get(K.UNCLASSIFIED, 0)
    if unc:
        shelves = {}
        for r in records:
            if K.kinds_of(r) == [K.UNCLASSIFIED]:
                # `cat` is a list on some records and a string on others.
                c = r.get("cat") or "?"
                c = c[0] if isinstance(c, list) and c else ("?" if isinstance(c, list) else c)
                shelves[c] = shelves.get(c, 0) + 1
        made = ", ".join(f"{n} {c}" for c, n in
                         sorted(shelves.items(), key=lambda x: -x[1])[:5])
        print(f"  ..    unclassified residue: {unc}" + (f" — {made}" if made else ""))
    else:
        print("  ..    unclassified residue: none")

    # ── every kind has members, or says why not ──────────────────────────
    # `way` is the one exception and it is written down: a way is PROJECTED from
    # data/streets.json at build time, never held in data/canonical, so it is
    # asserted below by projection instead of by tally.
    PROJECTED = {"way"}
    for key in K.KINDS:
        n = tally.get(key, 0)
        print(f"    {key:16s} {n:6d}")
        if key in PROJECTED:
            continue
        check(f"{key}: holds at least one record", n > 0,
              "an empty kind is a shelf nobody filled — see go/shelves")

    # ── THE POINT OF THE WHOLE EXERCISE ──────────────────────────────────
    # A wat the state register describes fully must pass the second gate. On
    # the old rule it did not, because it has no telephone.
    def old_gate(r):
        return bool(r.get("phone") or r.get("hours")
                    or r.get("website") or r.get("address"))

    failed_old = [r for r in records if not old_gate(r)]
    rescued = [r for r in failed_old if K.answered(r)]
    by_kind = {}
    for r in rescued:
        for k in (r.get("kind") or []):
            by_kind[k] = by_kind.get(k, 0) + 1
    print(f"    failed the shop-shaped gate: {len(failed_old)}")
    print(f"    of those, answer on their own kind: {len(rescued)}")
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"      {k:16s} {n}")
    check(f"records rescued from noindex by the kind-aware gate: {len(rescued)}",
          len(rescued) > 500,
          "the register facts are held and were being thrown away")
    # This was `by_kind['wat'] > 500` until 2026-09-07, and it broke without
    # the gate changing at all: the Overture fold gave 238 register-described
    # wats an ADDRESS, so they now clear even the shop-shaped gate and leave
    # the rescued population by getting better. A count over a moving corpus
    # drifts on its own — the same trap as the romaniser's corpus floor
    # (WO-72). The property underneath does not drift, so it is the one
    # asserted: a wat the register describes fully is never a failed shop.
    registered = [r for r in records
                  if "wat" in (r.get("kind") or [])
                  and (r.get("attrs") or {}).get("watCode")]
    stranded = [r for r in registered if not old_gate(r) and not K.answered(r)]
    print(f"    register-described wats: {len(registered)}"
          f" · failing the shop-shaped gate: "
          f"{sum(1 for r in registered if not old_gate(r))}"
          f" · rescued: {sum(1 for r in registered if not old_gate(r) and K.answered(r))}")
    check("every register-described wat that fails the shop-shaped gate is rescued",
          not stranded,
          f"{len(stranded)} left at noindex, e.g. {stranded[0]['id'] if stranded else ''}")

    # And a record with NOTHING but a name still fails — the gate must not
    # become a rubber stamp.
    empty = {"id": "x", "cat": ["food"], "name": "ก๋วยเตี๋ยว", "attrs": {}}
    empty["kind"] = K.kinds_of(empty)
    check("a name-only record still fails the gate", not K.answered(empty),
          "the second gate must be a gate, not a rubber stamp")

    # ── THE NINE ANTS, RE-CUT ────────────────────────────────────────────
    # Nine is ก้าว and a full swarm is a complete listing; the count may not
    # drift kind to kind or the chip stops meaning one thing.
    for key in list(K.KINDS) + [K.UNCLASSIFIED]:
        slots = (K.DOC.get("ant_slots") or {}).get(key)
        check(f"{key}: has four ant slots", bool(slots) and len(slots) == 4,
              "five universal + four kind slots = nine, on every axis")
        for sl in (slots or []):
            check(f"{key}: slot {sl[0]} is bilingual", len(sl) == 3 and sl[1] and sl[2])

    # `commerce` must be byte-identical to the nine that existed before the
    # axis did — the shopping shelves may not move by a pixel.
    HISTORIC = ["nameTh", "nameEn", "phone", "line", "hours", "web",
                "photo", "claimed", "fresh"]
    comm = ["nameTh", "nameEn"] + \
        [s[0].split("|")[0].replace("attrs.", "") for s in K.DOC["ant_slots"]["commerce"]] + \
        ["photo", "claimed", "fresh"]
    check("commerce keeps the historic nine, in order", comm == HISTORIC,
          f"{comm}")

    # A slot may only name a fact the corpus can carry, or a declared future
    # field. Otherwise the strip asks a reader for something that has nowhere
    # to land — a promise of evidence we cannot take.
    FUTURE = {"holds", "access", "parent", "serves", "ownWords",
              # the edge's own, decision J — a shrine's and a way's facts have
              # nowhere to live until the field work lands, and the slots are
              # cut now so nothing is rewritten when it does.
              "honours", "keeper", "offerings", "observedOn", "approach",
              "runsFrom", "runsTo", "passable", "floods", "donor", "potable"}
    CHANNEL = {"phone", "line", "hours", "web", "photo", "claimed", "fresh"}
    for key, slots in (K.DOC.get("ant_slots") or {}).items():
        for sl in slots:
            for one in sl[0].split("|"):
                one = one.strip()
                bare = one.replace("attrs.", "")
                ok = (one.startswith("attrs.") and bare in attr_keys) \
                    or bare in field_keys or bare in CHANNEL or bare in FUTURE
                check(f"{key}: slot '{one}' can be answered", ok,
                      "nothing in the corpus or the schema could ever fill it")

    # ── a record is asked as its FIRST kind, and the most specific rule wins ─
    lib = [r for r in records
           if "ห้องสมุด" in (r.get("name") or "") or "หอสมุด" in (r.get("name") or "")]
    if lib:
        firsts = {r["kind"][0] for r in lib}
        check(f"a place NAMED a library is asked as an institution ({len(lib)} of them)",
              firsts == {"institution"},
              f"first kinds: {firsts} — a name that says so outranks a category")

    # ── held(): the pin gate must no longer be counted in shop facts ──────
    def rank_as(r, kind):
        saved = r.get("kind")
        r["kind"] = [kind]
        n = sum(1 for k, _t, _e in K.ant_slots(r) if K.slot_value(r, k)) \
            + sum(1 for f in ("nameTh", "nameEn") if r.get(f))
        r["kind"] = saved
        return n
    nopin = [r for r in records if (r.get("geoPrecision") or "exact") == "needs-pin"]
    was = [r for r in nopin if rank_as(r, "commerce") <= 2]
    now = [r for r in nopin if rank_as(r, (r.get("kind") or ["commerce"])[0]) <= 2]
    print(f"    needs-pin {len(nopin)} · held on shop facts {len(was)} "
          f"· held on their own kind {len(now)}")
    check(f"held() releases records it was holding for the wrong reason "
          f"({len(was)} → {len(now)})", len(now) < len(was),
          "a record with no pin is waiting; it should not also be judged as a failed shop")

    # ── THE EDGE (decision J, 2026-09-06) ────────────────────────────────
    import edge_layer as E

    edge = K.DOC.get("edge") or {}
    check("the edge is described at all", len(edge) == 4,
          "shelters · sacred · ways · water")
    for key, e in edge.items():
        check(f"edge/{key}: named in both languages", bool(e.get("th") and e.get("en")))
        check(f"edge/{key}: says what a reader wants to know",
              bool(e.get("wants")) and len(e["wants"]) >= 4)
        check(f"edge/{key}: names its source", bool(e.get("source")))
        check(f"edge/{key}: carries vernacular", len(e.get("terms") or []) >= 8,
              "the Thai IS the only place this class lives — see go/disease")
        for term in (e.get("terms") or []):
            check(f"edge/{key}: term {term[0]} has a reading and a gloss",
                  len(term) == 3 and all(term), str(term))
            check(f"edge/{key}: term {term[0]} is written in Thai",
                  any("\u0e00" <= ch <= "\u0e7f" for ch in term[0])
                  or term[0].isascii(), "a Thai term written only in Latin is unfindable")
        for k in (e.get("kind") or []):
            check(f"edge/{key}: maps to a kind that exists", k in K.KINDS, k)

    # A sacred rule may not claim a trade record. ธนาคาร carries นาค;
    # โรงเรียนเจ้าพ่อหลวงอุปถัมภ์ is a school under royal patronage; อารักษ์ is a
    # road AND a vet clinic; "Slee Banyan" is a restaurant whose name says nothing.
    # All four bit the first pass and every one of them is now held out.
    sacred = [r for r in records if "sacred" in (r.get("kind") or [])]
    TRADE = {"food", "hotel", "massage", "beauty", "shopping", "repair",
             "realestate", "cannabis", "pets", "medical", "school", "cooking"}
    claimed_trade = [r for r in sacred if TRADE & set(r.get("cat") or [])]
    check(f"no trade record is claimed as sacred ({len(sacred)} sacred)",
          not claimed_trade,
          "; ".join((r.get("name") or "")[:30] for r in claimed_trade[:5]))
    check("a courthouse is not a shrine",
          not any("ศาลจังหวัด" in (r.get("name") or "") or "ศาลแขวง" in (r.get("name") or "")
                  for r in sacred))

    # ── WAYS: projected, not imported ────────────────────────────────────
    w = E.ways(ROOT)
    sois = [r for r in w if r["attrs"]["wayKind"] == "soi"]
    print(f"    ways projected: {len(w)} ({len(sois)} sois)")
    check(f"ways project from streets.json: {len(w)}", len(w) > 1000,
          "1,077 named ways were modelled on disk and never admitted as records")
    check(f"sois among them: {len(sois)}", len(sois) > 400)
    check("every way is Thai-named", all(r.get("name") for r in w))
    check("no way pretends to be a point",
          all(r["lat"] is None and r["geoPrecision"] == "line" for r in w),
          "a soi is a LINE; giving it a pin would put a dot in the middle of a lane")
    check("every way carries the count of what stands along it",
          all("alongCount" in r["attrs"] for r in w))
    check("a way answers its own gate",
          all(K.answered(r) for r in w[:200]),
          "length, parent and junctions are what a way owes")
    check("way ids do not collide with canonical ids",
          not ({r["id"] for r in w} & {r["id"] for r in records}))
    check("ways stand on no shopping shelf", all(r["cat"] == [] for r in w),
          "a soi is not for sale")

    print()
    if failures:
        print(f"FAILED {len(failures)}")
        for f in failures[:20]:
            print("   ", f)
        return 1
    print("all good")
    return 0


if __name__ == "__main__":
    sys.exit(main())
