#!/usr/bin/env python3
"""Pull doodle votes from the Cloudflare Worker.

Sibling of sync_toilets.py, same shape. A vote is a thumb up or down on one version of one
doodle, on accuracy and on aesthetics, with a note on what is right and wrong with the picture (worker.js putDoodleVote).

  data/doodles/votes.json          the tallies, public (GET /doodle-votes)
  cache/doodle_votes/events.jsonl  every change, with its note, voter hash and payout address
                                   (GET /doodle-vote-events, behind the key); appended, never rewritten

The key lives outside the repo, in ~/.mot-dang-doodle-votes.json {"eventsKey": "…"}, the same
arrangement as the showtimes recipe. Without it the tallies still sync. tools/doodle_score.py
reads both.

An unreachable worker or an empty answer leaves what is on disk alone.

    python3 importers/sync_doodle_votes.py
"""
import json
import os
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_URL = "https://mot-dang-claims.nanobotco.workers.dev"
OUT = os.path.join(ROOT, "data", "doodles", "votes.json")
EVENTS = os.path.join(ROOT, "cache", "doodle_votes", "events.jsonl")
KEYFILE = os.path.expanduser("~/.mot-dang-doodle-votes.json")
UA = "MotDangDoodleVoteSync/1.0 (+https://motdang.net/doodles/)"


def get(path, headers=None):
    req = urllib.request.Request(WORKER_URL + path, headers=dict({"User-Agent": UA}, **(headers or {})))
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def tallies():
    try:
        payload = get("/doodle-votes")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        print(f"doodle votes: worker unreachable ({err}), keeping the file on disk")
        return
    t = payload.get("tallies", {})
    if not t and os.path.exists(OUT) and json.load(open(OUT)).get("tallies"):
        print("doodle votes: worker returned none but the file on disk has some, keeping it")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"generated": payload.get("generated", ""), "tallies": t}, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"doodle votes: {len(t)} doodle version(s) -> {os.path.relpath(OUT, ROOT)}")


def events():
    if not os.path.exists(KEYFILE):
        print("doodle votes: no ~/.mot-dang-doodle-votes.json, events not pulled")
        return
    key = json.load(open(KEYFILE)).get("eventsKey", "")
    seen, last = set(), ""
    if os.path.exists(EVENTS):
        for line in open(EVENTS):
            if line.strip():
                k = json.loads(line)["k"]
                seen.add(k)
                last = max(last, k)
    try:
        payload = get("/doodle-vote-events?since=" + urllib.request.quote(last[4:]), {"x-md-key": key})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        print(f"doodle votes: events unreachable ({err}), keeping what is on disk")
        return
    new = [e for e in payload.get("events", []) if e.get("k") not in seen]
    os.makedirs(os.path.dirname(EVENTS), exist_ok=True)
    with open(EVENTS, "a") as fh:
        for e in sorted(new, key=lambda e: e["k"]):
            fh.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"doodle votes: {len(new)} new event(s) -> {os.path.relpath(EVENTS, ROOT)}")


def main():
    tallies()
    events()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
