#!/usr/bin/env python3
"""Bring the thumbs and notes down to this machine, to be read by a person.

Readers give a thumb up, a thumb down and an optional paragraph on any item
through POST /feedback on the claims Worker (assets/feedback.js). Notes can carry
a phone number or an email, so there is no public GET for them: the event log
answers only to the FEEDBACK_KEY secret, sent as x-md-key. The key is the file
~/.tokens/MD_FEEDBACK_KEY (`~/.claude/bin/token get MD_FEEDBACK_KEY`). With no
such file this makes one, saves it to the Mac and the server, and sets it as the
Worker's secret.

    python3 importers/sync_feedback.py            # pull what is new, rewrite the summary
    python3 importers/sync_feedback.py --offline  # rewrite the summary from the file on disk
    python3 importers/sync_feedback.py --item place:cm-osm-node-1   # one item's notes

Writes _incoming/feedback/ (gitignored, so a note's contact details cannot ride
into a commit):
    events.jsonl   every vote change and note, one per line, kept between runs
    summary.txt    per item: thumbs up, thumbs down, notes; most thumbs-down first
"""
import argparse
import json
import os
import secrets
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_URL = "https://mot-dang-claims.nanobotco.workers.dev"
OUT_DIR = os.path.join(ROOT, "_incoming", "feedback")
EVENTS = os.path.join(OUT_DIR, "events.jsonl")
SUMMARY = os.path.join(OUT_DIR, "summary.txt")
TOKEN = os.path.expanduser("~/.claude/bin/token")
TOKEN_FILE = os.path.expanduser("~/.tokens/MD_FEEDBACK_KEY")
UA = "MotDangFeedbackSync/1.0 (+https://motdang.net/)"


def key():
    """The events key; made, saved and set on the Worker when there is none."""
    if not os.path.exists(TOKEN_FILE):
        os.makedirs(os.path.dirname(TOKEN_FILE), mode=0o700, exist_ok=True)
        fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(secrets.token_urlsafe(32))
        subprocess.run([TOKEN, "push", "MD_FEEDBACK_KEY"], check=False)
        val = open(TOKEN_FILE).read().strip()
        subprocess.run(["npx", "wrangler", "secret", "put", "FEEDBACK_KEY"], input=val, text=True,
                       cwd=os.path.join(ROOT, "worker"), check=True, capture_output=True)
        print("feedback: made MD_FEEDBACK_KEY and set FEEDBACK_KEY on the Worker")
    return subprocess.run([TOKEN, "get", "MD_FEEDBACK_KEY"], capture_output=True, text=True,
                          check=True).stdout.strip()


def get(path, headers):
    req = urllib.request.Request(WORKER_URL + path, headers=dict({"User-Agent": UA}, **headers))
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def load():
    out = []
    if os.path.exists(EVENTS):
        for line in open(EVENTS, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    return out


def pull():
    have = load()
    seen = {e["k"] for e in have}
    last = max((e["at"] for e in have), default="")
    try:
        payload = get("/feedback-events?since=" + urllib.request.quote(last), {"x-md-key": key()})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        print(f"feedback: worker unreachable ({err}), keeping what is on disk")
        return have
    new = [e for e in payload.get("events", []) if e.get("k") not in seen]
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(EVENTS, "a", encoding="utf-8") as fh:
        for e in sorted(new, key=lambda e: (e["at"], e["k"])):
            fh.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"feedback: {len(new)} new event(s) -> {os.path.relpath(EVENTS, ROOT)}")
    return have + new


def summarise(events):
    """Per item: each reader's latest vote, and every note, from the event log."""
    items = {}
    for e in sorted(events, key=lambda e: (e["at"], e["k"])):
        it = items.setdefault(e["item"], {"votes": {}, "notes": [], "at": ""})
        it["at"] = max(it["at"], e["at"])
        if e["k"].startswith("fb-vote:"):
            it["votes"][e["who"]] = e["x"]
        elif e.get("note"):
            it["notes"].append(e)
            it["votes"][e["who"]] = e.get("x", it["votes"].get(e["who"], 0))
    rows = []
    for name, it in items.items():
        up = sum(1 for x in it["votes"].values() if x == 1)
        down = sum(1 for x in it["votes"].values() if x == -1)
        rows.append((name, up, down, it["notes"], it["at"]))
    rows.sort(key=lambda r: (-r[2], -len(r[3]), -r[1], r[0]))
    return rows


def write_summary(rows):
    lines = [f"{len(rows)} item(s); {sum(r[1] for r in rows)} up, {sum(r[2] for r in rows)} down, "
             f"{sum(len(r[3]) for r in rows)} note(s)", ""]
    for name, up, down, notes, at in rows:
        lines.append(f"{name}   up {up}  down {down}  notes {len(notes)}   last {at[:10]}")
        for n in notes:
            mark = {1: "up", -1: "down"}.get(n.get("x"), "-")
            txt = " ".join(n["note"].split())
            cr = (n.get("credit") or {}).get("name")
            tag = f" CREDIT:{cr} ref {n.get('ref', '')}" if cr else ""
            lines.append(f"    [{n['at'][:10]} {mark} {n.get('lang', '')}{tag}] {txt[:300]}")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(SUMMARY, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"feedback: {len(rows)} item(s) -> {os.path.relpath(SUMMARY, ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="summarise the file on disk, no request")
    ap.add_argument("--item", help="print one item's notes in full")
    a = ap.parse_args()
    events = load() if a.offline else pull()
    rows = summarise(events)
    write_summary(rows)
    if a.item:
        for e in events:
            if e["item"] == a.item and e.get("note"):
                print(f"[{e['at']} x={e.get('x')} {e.get('lang', '')}] {e['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
