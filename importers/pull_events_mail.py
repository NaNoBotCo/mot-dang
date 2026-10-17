#!/usr/bin/env python3
"""Mail to events@motdang.net, read off the ear (../ear: a Worker that stores
inbound mail in R2 + D1 and answers a token-gated API).

Each new message on the `events` door is written to
_incoming/events-mail/<id>.txt (from, subject, body) and marked handled on the
ear. A message that reads as Steve's weekly email (its four-part split names
"EVENTS THAT RARELY CHANGE") is also offered to fetch_newsletter.save_issue, the
same path the Google Doc copy takes, so whichever arrives first becomes the issue.

    python3 importers/pull_events_mail.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_newsletter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_incoming", "events-mail")
EAR = "https://ear.nanobotco.workers.dev"
TOKEN = os.path.expanduser("~/.config/nanobot/ear_token")
DOOR = "events"


def api(path, method="GET"):
    req = urllib.request.Request(EAR + path, method=method, headers={
        "Authorization": "Bearer " + open(TOKEN).read().strip(),
        "User-Agent": "motdang pull_events_mail.py"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    try:
        mail = [m for m in api("/list")["mail"] if (m.get("door") or "") == DOOR]
    except Exception as ex:
        print("events mail: the ear did not answer (%s: %s)" % (type(ex).__name__, ex))
        return 1
    os.makedirs(OUT, exist_ok=True)
    for m in mail:
        body = m.get("body_text") or ""
        with open(os.path.join(OUT, m["id"] + ".txt"), "w", encoding="utf-8") as f:
            f.write("From: %s\nSubject: %s\nDate: %s\nAttachments: %s\n\n%s" % (
                m.get("from_addr"), m.get("subject"), m.get("ts"), m.get("n_att"), body))
        if "EVENTS THAT RARELY CHANGE" in body.upper():
            fetch_newsletter.save_issue(body)
        api("/handled/" + m["id"], method="POST")
        print("events mail: %s from %s — %s" % (m["id"], m.get("from_addr"), (m.get("subject") or "")[:60]))
    print("events mail: %d new" % len(mail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
