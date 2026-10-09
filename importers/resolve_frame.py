#!/usr/bin/env python3
"""Pin a photograph by what else is standing in it.

    python3 importers/resolve_frame.py --demo
    python3 importers/resolve_frame.py --anchors anchors.json
    python3 importers/resolve_frame.py --validate

WHY THIS EXISTS. LINE strips EXIF from anything sent as a photo — it re-encodes
the file and only one empty ExifOffset tag survives. Every picture that reaches
the desk from the team album therefore arrives with no coordinates, no capture
time, and no prospect of either. The obvious fixes all end in "so send it a
different way", which is a workflow change asked of a person, and people do not
owe the pipeline a change of habit. So the pin has to come out of the picture.

It can, because a shopfront is never photographed alone. The frame that holds
the subject also holds its neighbours' signs, and a neighbour is a record we
already surveyed. One chain name is useless — "Pharma Choice" is 19 branches
in this catalogue and picking one would be a guess. But the same frame also
showed a J-neon, the words ROOF TOP, and the word SLEEP, and those resolve to
Johns Place, THC Roof top bar and Sleep Mai: 62 m, 141 m and 97 m apart, all
on ถนนมูลเมือง. Three independent anchors agreeing on one block turn 19
candidates into 1, and the agreement is the evidence — not any single read.

WHAT THAT MEANS FOR THE READING STEP. The background is not clutter to be
cropped away before the "real" work; the background IS the geocode. A vision
pass that returns only the subject's name has thrown the coordinates away. Read
every legible string in the frame and say which one the photo is *about*.

WHAT IT RETURNS, and how sure it is. Never a bare coordinate — the same
discipline as geocode_local.py, for the same reason: a shop placed on the right
block is useful, and a shop placed on the right block while claiming to be a
surveyed pin is a lie the map tells confidently.

  record — the subject anchor itself matched a record we hold, and that record
           sits inside the winning cluster. The pin is that record's own
           surveyed pin. Best case: we have identified the place, not just
           the street.
  block  — the subject is not in the catalogue (a new shop, a shuttered unit),
           but its neighbours are. The pin is the weighted centroid of the
           supporting neighbours and the stated uncertainty is their spread.
           This is the case that matters most: it is how a place we have never
           held gets a usable pin the first time somebody photographs it.
  none   — not enough agreement. Returns None and says why. An unresolved photo
           is a question for a person, not a gap for a bot to close.

REFUSALS ARE THE POINT. This module says no more often than it says yes, and
the thresholds are deliberately the ones the LINE bot already files by — 0.80
and clear of the runner-up. Three guards:

  * one corroborating sign is never enough, however good the match. A chain
    name plus a single coincidence is the exact shape of a confident error,
    and the validation says so: it is where 11 of 17 of them came from.
  * a runner-up cluster more than a radius away has to lose by a margin.
  * an anchor whose folded form is nothing but stop words matches nothing at
    all. That is BUG-0001, reported in the room on 2026-09-07: a photo filed
    under a record named "This is" at 92% because the sentence naming the shop
    contained the words "this is". A name made of stop words is not a name.

Reads docs/data/index.json read-only and writes nothing. It takes no build
lock, and it never touches data/ — a resolved pin is a candidate for a person
to promote, like every other row the desk produces.
"""
import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "docs", "data", "index.json")

# A frame of streetfront. Two shops either side of the subject are within this;
# the far side of a block is not. Widened only by --radius, and saying so.
RADIUS_M = 150.0

# The bot's existing filing discipline, kept deliberately identical.
MIN_CONFIDENCE = 0.80

# Two CORROBORATING signs, not two anchors. Counting the subject toward its own
# corroboration lets a chain name plus one coincidence through, and that is
# measurably where the wrong answers come from: on a 400-frame validation,
# demanding a second corroborator cut confidently-wrong accepts from 17 to 6
# and cost 9% of the right ones. One neighbour can coincide anywhere in a city
# of chains; two neighbours agreeing on one block is a much harder accident.
MIN_CORROBORATORS = 2

# Folded forms that are not names. An anchor made only of these matches
# nothing — see BUG-0001 in the docstring.
STOP = {
    "the", "a", "an", "this", "is", "it", "at", "in", "of", "and", "to", "for",
    "on", "by", "or", "we", "you", "my", "our", "here", "there", "that", "with",
    "open", "closed", "new", "old", "no", "yes", "please", "shop", "store",
    "place", "welcome", "sale", "left", "right", "photo", "picture",
    "ร้าน", "ที่", "และ", "ของ", "นี้", "นี่", "เปิด", "ปิด", "ขาย", "ให้",
}


def _fold(s):
    """Fold a place name to comparable tokens, in either script.

    Two things get stripped before anything else. The generated bearing tail —
    172 records read like `Car park · 570 m from Tha Phae Gate`, and matching
    on that tail files a photo of the gate under a car park. And the trailing
    distance phrase itself, for the records that carry it without the dot.
    """
    s = (s or "").lower()
    s = s.split(" · ")[0]
    s = re.sub(r"\b\d+(?:\.\d+)?\s*(?:m|km|เมตร|กม\.?)\s+(?:from|to|จาก)\b.*$", " ", s)
    s = re.sub(r"[^\w฀-๿]+", " ", s)
    return " ".join(s.split())


def _tokens(s):
    return [t for t in _fold(s).split() if t]


def _is_stopword_only(text):
    toks = _tokens(text)
    return (not toks) or all(t in STOP for t in toks)


def _metres(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class FrameResolver:
    """Resolve a photograph's location from the names standing in it."""

    NAME_FIELDS = ("n", "e", "r", "a")

    def __init__(self, index_path=INDEX, records=None):
        self.records = records if records is not None else json.load(
            open(index_path, encoding="utf-8"))
        self._folded = []
        self._postings = {}
        for i, rec in enumerate(self.records):
            toks = set()
            for f in self.NAME_FIELDS:
                v = rec.get(f)
                if isinstance(v, str):
                    toks.update(_tokens(v))
            self._folded.append(toks)
            for t in toks:
                self._postings.setdefault(t, set()).add(i)
        self._addr_blob = None  # built lazily; only house-number anchors need it

    # ---------- step 1: an anchor becomes candidate records ----------

    def candidates(self, text, kind="name", province=None):
        """Records this one string could be naming, each with a 0..1 score."""
        if kind == "housenumber":
            return self._house_number_candidates(text, province)
        if _is_stopword_only(text):
            return []
        toks = set(_tokens(text))
        if not toks:
            return []
        seen = set()
        for t in toks:
            seen |= self._postings.get(t, set())
        folded_anchor = _fold(text)
        info_anchor = self._info(toks)
        out = []
        for i in seen:
            rec = self.records[i]
            if province and rec.get("p") != province:
                continue
            shared = toks & self._folded[i]
            if not shared:
                continue
            # How much of what was read off the sign is accounted for by this
            # record's name. Anchored on the ANCHOR, not the record: a sign
            # saying "Johns Place" fully explains itself against a record
            # called "Johns Place: Daughter and Son", and should not be
            # penalised for the words the record carries and the sign does not.
            #
            # Measured in INFORMATION, not in words. Counting words makes
            # "P Place" a half-match for "Johns Place" and "Top Charoen
            # Optical" a half-match for "Roof top", because `place` and `top`
            # are everywhere and `johns` is not. Sharing a common word is
            # not evidence; sharing a rare one nearly settles it.
            score = (self._info(shared) / info_anchor) if info_anchor else 0.0
            for f in self.NAME_FIELDS:
                v = rec.get(f)
                if isinstance(v, str) and folded_anchor and folded_anchor in _fold(v):
                    score = max(score, 0.95)
                    break
            if score >= 0.5:
                out.append((i, score))
        return out

    def _house_number_candidates(self, text, province=None):
        """A house number is matched literally, never tokenised.

        `29/3` split into `29` and `3` would match half the catalogue. Kept
        whole it matches almost nothing — only 69 of 25,582 records carry a
        house-number token at all — which is exactly why a hit is decisive.
        """
        if self._addr_blob is None:
            self._addr_blob = [
                " ".join(str(r.get(f, "")) for f in ("a", "k", "n", "e", "r"))
                for r in self.records]
        num = (text or "").strip()
        if not re.fullmatch(r"\d{1,4}(?:/\d{1,3})?", num):
            return []
        pat = re.compile(r"(?<![\d/])" + re.escape(num) + r"(?![\d/])")
        out = []
        for i, blob in enumerate(self._addr_blob):
            if province and self.records[i].get("p") != province:
                continue
            if pat.search(blob):
                out.append((i, 1.0))
        return out

    # ---------- step 2: rarity ----------

    def _idf(self, token):
        return math.log(len(self.records) / (1 + len(self._postings.get(token, ()))))

    def _info(self, tokens):
        """How much a set of words narrows the catalogue, in nats."""
        return sum(max(0.0, self._idf(t)) for t in tokens)

    def _weight(self, n_candidates):
        """A name matching two records is worth more than one matching two
        hundred. This is the guitar-shop lesson in one line: the rare word is
        the question, and weighing every word equally buries it."""
        if n_candidates <= 0:
            return 0.0
        return math.log(1.0 + len(self.records) / n_candidates)

    # ---------- step 3-6: the frame votes ----------

    def resolve(self, anchors, province="cm", radius=RADIUS_M,
                min_confidence=MIN_CONFIDENCE, min_corroborators=MIN_CORROBORATORS):
        """anchors: [{"text": str, "role": "subject"|"neighbour", "kind": ...}]

        Returns a dict that always explains itself, resolved or not.
        """
        prepared = []
        for a in anchors:
            text = a.get("text", "")
            kind = a.get("kind", "name")
            cands = self.candidates(text, kind=kind, province=province)
            pinned = [(i, s) for i, s in cands
                      if self.records[i].get("lat") and self.records[i].get("lng")]
            prepared.append({
                "text": text,
                "role": a.get("role", "neighbour"),
                "kind": kind,
                "candidates": cands,
                "pinned": pinned,
                "weight": self._weight(len(cands)),
                "stopword_only": kind == "name" and _is_stopword_only(text),
            })

        # Every pinned candidate is a place one of these signs could be naming.
        points = []
        for ai, a in enumerate(prepared):
            for i, s in a["pinned"]:
                rec = self.records[i]
                points.append((ai, i, s, (rec["lat"], rec["lng"])))

        if not points:
            return self._refuse(prepared, "no anchor matched a record that carries a pin")

        # WHICH POSITIONS ARE WORTH TESTING. If the subject anchor matched
        # anything we hold, the only positions worth testing are the subject's
        # own candidates: the question is which of Pharma Choice's 19 branches
        # this is, and a block on the other side of town that happens to hold
        # a guest house called Sleep is not a rival answer to that question.
        # Scoring every point in the frame instead lets generic neighbours
        # accumulate support somewhere the subject provably is not.
        #
        # When the subject matched nothing — a new shop, a shuttered unit —
        # there is no such constraint, and the neighbours have to agree among
        # themselves. That is the weaker case, and it reports itself as one.
        subject_points = [t for t in points if prepared[t[0]]["role"] == "subject"]
        hypotheses = subject_points or points

        scored = []
        for _, _, _, p in hypotheses:
            support, by_anchor = 0.0, {}
            for ai, i, s, q in points:
                if _metres(p, q) <= radius:
                    contribution = s * prepared[ai]["weight"]
                    if contribution > by_anchor.get(ai, (0.0, None))[0]:
                        by_anchor[ai] = (contribution, i)
            support = sum(v[0] for v in by_anchor.values())
            # A chain name cannot tell its own branches apart: all 19 Pharma
            # Choices match "Pharma Choice" equally well, so the subject's
            # self-match is a constant that every hypothesis collects and no
            # hypothesis is distinguished by. Counting it in the margin makes
            # the runner-up look like real disagreement when it is only the
            # null answer. The corroborating anchors are the whole evidence,
            # so they alone set the confidence.
            corroboration = sum(c for ai, (c, _) in by_anchor.items()
                                if prepared[ai]["role"] != "subject")
            scored.append((corroboration, support, p, by_anchor))
        scored.sort(key=lambda t: (-t[0], -t[1]))

        corroboration, support, point, by_anchor = scored[0]
        runner = next((c for c, _, q, _ in scored if _metres(q, point) > radius), 0.0)
        distinct = len(by_anchor)
        confidence = ((corroboration - runner) / corroboration
                      if corroboration > 0 else 0.0)

        supporting = []
        for ai, (contribution, i) in sorted(by_anchor.items(),
                                            key=lambda kv: -kv[1][0]):
            rec = self.records[i]
            supporting.append({
                "anchor": prepared[ai]["text"],
                "role": prepared[ai]["role"],
                "record": rec.get("s"),
                "name": rec.get("e") or rec.get("n"),
                "metres_from_pin": round(_metres(point, (rec["lat"], rec["lng"])), 1),
                "weight": round(prepared[ai]["weight"], 2),
            })

        corroborators = sum(1 for s in supporting if s["role"] != "subject")
        if corroborators < min_corroborators:
            return self._refuse(
                prepared,
                f"only {corroborators} corroborating sign agreed; a name plus one "
                f"coincidence is where the confident errors come from",
                supporting=supporting, confidence=round(confidence, 3))
        if confidence < min_confidence:
            return self._refuse(
                prepared,
                f"confidence {confidence:.2f} below {min_confidence:.2f}; a rival block "
                f"corroborated {round(runner, 2)} against {round(corroboration, 2)}",
                supporting=supporting, confidence=round(confidence, 3))

        # Which anchor is the photo ABOUT, and do we already hold it?
        subject_rec, precision = None, "block"
        for ai, (_, i) in by_anchor.items():
            if prepared[ai]["role"] == "subject":
                subject_rec, precision = self.records[i], "record"
                break

        if precision == "record":
            pin = (subject_rec["lat"], subject_rec["lng"])
            uncertainty = 0.0
        else:
            wsum = sum(c for c, _ in by_anchor.values())
            lat = sum(self.records[i]["lat"] * c for c, i in by_anchor.values()) / wsum
            lng = sum(self.records[i]["lng"] * c for c, i in by_anchor.values()) / wsum
            pin = (lat, lng)
            uncertainty = max(
                _metres(pin, (self.records[i]["lat"], self.records[i]["lng"]))
                for _, i in by_anchor.values())

        return {
            "resolved": True,
            "precision": precision,
            "pin": [round(pin[0], 6), round(pin[1], 6)],
            "uncertainty_m": round(uncertainty, 1),
            "confidence": round(confidence, 3),
            "corroboration": round(corroboration, 2),
            "anchors_agreeing": distinct,
            "subject_record": subject_rec.get("s") if subject_rec else None,
            "subject_name": (subject_rec.get("e") or subject_rec.get("n")) if subject_rec else None,
            "supporting": supporting,
            "why": self._why(precision, distinct, confidence, supporting),
        }

    def _refuse(self, prepared, reason, supporting=None, confidence=0.0):
        return {
            "resolved": False,
            "precision": "none",
            "pin": None,
            "confidence": confidence,
            "reason": reason,
            "supporting": supporting or [],
            "anchors": [{"text": a["text"], "role": a["role"],
                         "candidates": len(a["candidates"]),
                         "pinned_candidates": len(a["pinned"]),
                         "stopword_only": a["stopword_only"]}
                        for a in prepared],
            "why": f"Not resolved: {reason}. This photo is a question for a person.",
        }

    @staticmethod
    def _why(precision, distinct, confidence, supporting):
        names = ", ".join(f"{s['anchor']}→{s['name']} ({s['metres_from_pin']:.0f} m)"
                          for s in supporting[:4])
        if precision == "record":
            return (f"The subject anchor matched a record we hold, and {distinct} anchors "
                    f"in the frame agree on that block at {confidence:.2f}: {names}. "
                    f"The pin is that record's own surveyed pin.")
        return (f"The subject is not in the catalogue, but {distinct} anchors in the frame "
                f"agree on one block at {confidence:.2f}: {names}. The pin is their "
                f"weighted centre and the uncertainty is their spread — the block is "
                f"known, the door is not.")


# ---------- the frames we actually have, as a measurable set ----------

DEMO = [
    {
        "message_id": "630732167076905233",
        "note": "Pharma Choice (right) + vacant shophouse (left), east side of old city",
        "expect": "resolved",
        "anchors": [
            {"text": "Pharma Choice", "role": "subject"},
            {"text": "Johns Place", "role": "neighbour"},
            {"text": "Roof top", "role": "neighbour"},
            {"text": "Sleep", "role": "neighbour"},
            {"text": "29/3", "role": "neighbour", "kind": "housenumber"},
        ],
    },
    {
        "message_id": "630732167076905233-subject-only",
        "note": "the same chain name with nothing else read — must refuse",
        "expect": "refused",
        "anchors": [{"text": "Pharma Choice", "role": "subject"}],
    },
    {
        "message_id": "630725814551839248",
        "note": "Get Er to the Greek storefront, nothing else legible in frame",
        "expect": "refused",
        "anchors": [{"text": "Get Er to the Greek", "role": "subject"}],
    },
    {
        "message_id": "bug-0001-regression",
        "note": "BUG-0001: a sentence of stop words must name nothing",
        "expect": "refused",
        "anchors": [
            {"text": "This is", "role": "subject"},
            {"text": "the", "role": "neighbour"},
        ],
    },
]


def validate(resolver, n=400, radius=RADIUS_M, seed=7):
    """Measure the thing rather than assert it, the way geocode_local does.

    Ground truth is the catalogue's own geometry. Take a pinned record, call
    its name the subject, call its three physically nearest neighbours the
    other signs in the frame, and see whether the resolver puts the subject
    back where it started. Neighbours are the CLOSEST ones, not the rarest —
    picking the most informative neighbours would be marking my own homework,
    and a camera does not choose its background by how unusual it is.

    Two controls, because a resolver that says yes to everything scores well
    on the first number alone:

      lonely   — subject with no neighbours at all. Must refuse. This is the
                 shape of most real photos of an isolated shopfront, and the
                 refusal rate here is the honest ceiling on how much of the
                 album this can ever pin.
      transplant — subject with three neighbours borrowed from a random other
                 block. Must refuse. Anything it accepts here is a confident
                 wrong answer, which is the only kind that does damage.

    Read this as an upper bound. Real anchors are OCR fragments off a lit sign
    at an angle; these are clean catalogue strings. It measures the matching
    and the voting, not the reading.
    """
    import random
    rnd = random.Random(seed)
    recs = resolver.records
    pinned = [i for i, r in enumerate(recs)
              if r.get("lat") and r.get("lng") and r.get("p") == "cm"
              and (r.get("e") or r.get("n"))]
    # Coarse grid so neighbour lookup is not 25k comparisons per frame.
    cell = 0.0025  # ~275 m
    grid = {}
    for i in pinned:
        k = (int(recs[i]["lat"] / cell), int(recs[i]["lng"] / cell))
        grid.setdefault(k, []).append(i)

    def neighbours_of(i, limit=3):
        r = recs[i]
        p = (r["lat"], r["lng"])
        gy, gx = int(r["lat"] / cell), int(r["lng"] / cell)
        near = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for j in grid.get((gy + dy, gx + dx), ()):
                    if j == i:
                        continue
                    # A second branch of the same chain next door is a
                    # duplicate, not a corroborating neighbour.
                    if _fold(recs[j].get("e") or recs[j].get("n") or "") == \
                       _fold(r.get("e") or r.get("n") or ""):
                        continue
                    d = _metres(p, (recs[j]["lat"], recs[j]["lng"]))
                    if d <= radius:
                        near.append((d, j))
        near.sort()
        return [j for _, j in near[:limit]]

    sample = rnd.sample(pinned, min(n, len(pinned)))
    stats = {"frames": 0, "resolved": 0, "correct": 0, "errors": [],
             "lonely_resolved": 0, "lonely_frames": 0,
             "transplant_resolved": 0, "transplant_frames": 0, "no_neighbours": 0}

    def name(i):
        return recs[i].get("e") or recs[i].get("n")

    for i in sample:
        nb = neighbours_of(i)
        if not nb:
            stats["no_neighbours"] += 1
            continue
        stats["frames"] += 1
        anchors = [{"text": name(i), "role": "subject"}] + \
                  [{"text": name(j), "role": "neighbour"} for j in nb]
        out = resolver.resolve(anchors, radius=radius)
        if out["resolved"]:
            stats["resolved"] += 1
            if out["subject_record"] == recs[i].get("s"):
                stats["correct"] += 1
            stats["errors"].append(
                _metres((recs[i]["lat"], recs[i]["lng"]), tuple(out["pin"])))

        # control 1: nothing else in the frame
        stats["lonely_frames"] += 1
        if resolver.resolve([{"text": name(i), "role": "subject"}],
                            radius=radius)["resolved"]:
            stats["lonely_resolved"] += 1

        # control 2: neighbours from somewhere else entirely
        other = rnd.choice(sample)
        onb = neighbours_of(other)
        if onb and _metres((recs[i]["lat"], recs[i]["lng"]),
                           (recs[other]["lat"], recs[other]["lng"])) > radius * 4:
            stats["transplant_frames"] += 1
            fake = [{"text": name(i), "role": "subject"}] + \
                   [{"text": name(j), "role": "neighbour"} for j in onb]
            out2 = resolver.resolve(fake, radius=radius)
            if out2["resolved"] and out2["subject_record"] == recs[i].get("s"):
                pass  # it found the right place despite the noise; not a false accept
            elif out2["resolved"]:
                stats["transplant_resolved"] += 1

    errs = sorted(stats["errors"])
    med = errs[len(errs) // 2] if errs else None
    f = stats["frames"] or 1
    print(f"frames with at least one neighbour : {stats['frames']}"
          f"   (skipped, nothing within {radius:.0f} m: {stats['no_neighbours']})")
    print(f"resolved                           : {stats['resolved']}  "
          f"({100 * stats['resolved'] / f:.1f}%)")
    print(f"  of those, subject correct        : {stats['correct']}  "
          f"({100 * stats['correct'] / (stats['resolved'] or 1):.1f}%)")
    print(f"  median pin error                 : "
          f"{('%.0f m' % med) if med is not None else 'n/a'}")
    print(f"CONTROL lonely subject resolved    : {stats['lonely_resolved']} of "
          f"{stats['lonely_frames']}   (must be 0)")
    print(f"CONTROL transplanted neighbours    : {stats['transplant_resolved']} of "
          f"{stats['transplant_frames']} wrongly accepted   (must be ~0)")
    return stats


def _run_demo(resolver, radius=RADIUS_M):
    ok = True
    for frame in DEMO:
        out = resolver.resolve(frame["anchors"], radius=radius)
        got = "resolved" if out["resolved"] else "refused"
        mark = "ok " if got == frame["expect"] else "FAIL"
        if got != frame["expect"]:
            ok = False
        print(f"[{mark}] {frame['message_id']}")
        print(f"       {frame['note']}")
        print(f"       expected {frame['expect']}, got {got}")
        if out["resolved"]:
            print(f"       {out['precision']}  {out['pin']}  ±{out['uncertainty_m']} m  "
                  f"conf {out['confidence']}  anchors {out['anchors_agreeing']}")
            for s in out["supporting"]:
                print(f"         · {s['anchor']:<16} → {s['name']}  "
                      f"{s['metres_from_pin']:.0f} m  w={s['weight']}")
        else:
            print(f"       {out['reason']}")
        print()
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--anchors", help="JSON file: a list of anchor objects")
    ap.add_argument("--demo", action="store_true",
                    help="run the frames already sent to the ops channel")
    ap.add_argument("--validate", nargs="?", type=int, const=400, default=None,
                    metavar="N", help="measure against the catalogue's own geometry")
    ap.add_argument("--province", default="cm")
    ap.add_argument("--radius", type=float, default=RADIUS_M)
    ap.add_argument("--index", default=INDEX)
    args = ap.parse_args()

    if not os.path.exists(args.index):
        raise SystemExit(f"no index at {args.index} — a build may be rewriting it; "
                         f"try again, or pass --index with a snapshot")
    resolver = FrameResolver(args.index)

    if args.demo:
        raise SystemExit(0 if _run_demo(resolver, args.radius) else 1)

    if args.validate is not None:
        validate(resolver, n=args.validate, radius=args.radius)
        raise SystemExit(0)

    if not args.anchors:
        ap.error("give --anchors FILE or --demo")
    anchors = json.load(open(args.anchors, encoding="utf-8"))
    if isinstance(anchors, dict):
        anchors = anchors.get("anchors", [])
    out = resolver.resolve(anchors, province=args.province, radius=args.radius)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
