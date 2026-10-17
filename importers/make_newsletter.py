#!/usr/bin/env python3
"""The weekly issue: the next seven days of one-off events, from data/events.json.

Weekly fixtures are left to events.html, linked at the foot; an issue of them
would be the same list every week. Each line links to its anchor on
events.html. The issue is written to _incoming/newsletter-out/<date>.json
every run; --send POSTs it to the site Worker (publish/newsletter.js), which
holds the Resend key and the list, and which sends only to its test address
until NEWSLETTER_LIVE is "true".

    python3 importers/make_newsletter.py               # write the issue, print it
    python3 importers/make_newsletter.py --send        # and send it
    python3 importers/make_newsletter.py --date 2026-10-19
"""
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_incoming", "newsletter-out")
SITE = "https://motdang.net"
ENDPOINT = SITE + "/newsletter/send"

TH_DAY = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
TH_MON = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def anchor(title):
    """build.py _ev_anchor, so a link lands on the event's row."""
    return "ev-" + (re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:80] or "x")


def day_head(d):
    return "%s %d %s · %s" % (TH_DAY[d.weekday()], d.day, TH_MON[d.month - 1], d.strftime("%a %-d %b"))


def _norm(title):
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def clean_venue(v):
    """A meetup venue arrives as '**Venue:** Spice Garden'."""
    return re.sub(r"^\W*venue\W*", "", re.sub(r"\*+", "", v or ""), flags=re.I).strip()


def dedupe(rows):
    """Two sources listing one evening: same start, one title inside the other."""
    out = []
    for e in rows:
        n = _norm(e["title"])
        if any(o["start"] == e["start"] and (n in _norm(o["title"]) or _norm(o["title"]) in n) for o in out):
            continue
        out.append(e)
    return out


def pick(events, first):
    last = first + timedelta(days=6)
    running, by_day, seen = [], {}, set()
    for e in events:
        if e.get("recurring") or e.get("from_rule"):
            continue
        start = date.fromisoformat(e["start"][:10])
        end = date.fromisoformat(e["end"][:10]) if e.get("end") else start
        key = (e.get("title"), e.get("venue_name"))
        if end > start and start <= last and end >= first:
            if key not in seen:
                seen.add(key)
                running.append(e)
        elif first <= start <= last:
            by_day.setdefault(start, []).append(e)
    for d in by_day:
        by_day[d] = dedupe(sorted(by_day[d], key=lambda e: (not e.get("all_day"), e["start"])))
    running.sort(key=lambda e: e["start"])
    return running, dict(sorted(by_day.items()))


def line_parts(e, with_dates=False):
    when = ""
    if with_dates:
        s = date.fromisoformat(e["start"][:10])
        n = date.fromisoformat(e["end"][:10])
        when = "%s–%s" % (s.strftime("%-d %b"), n.strftime("%-d %b"))
    elif not e.get("all_day"):
        when = e["start"][11:16]
    rest = " · ".join(x for x in (clean_venue(e.get("venue_name")), e.get("cost")) if x)
    return when, e["title"], rest, SITE + "/events.html#" + anchor(e["title"])


def compose(events, first):
    running, by_day = pick(events, first)
    last = first + timedelta(days=6)
    span = "%d–%d %s" % (first.day, last.day, last.strftime("%b")) if first.month == last.month \
        else "%s – %s" % (first.strftime("%-d %b"), last.strftime("%-d %b"))
    subject = "มดแดง · งานในเมือง · What's on, %s" % span
    n = len(running) + sum(len(v) for v in by_day.values())

    t = ["มดแดง · What's on, %s" % span, ""]
    h = ['<div style="font:15px/1.45 system-ui,sans-serif;max-width:40rem">',
         '<h1 style="font-size:20px">มดแดง · What\'s on, %s</h1>' % html.escape(span)]

    def add(head, rows, with_dates=False):
        t.append(head)
        h.append('<h2 style="font-size:16px;margin:1.2em 0 .3em">%s</h2><ul style="padding-left:1.1em;margin:0">' % html.escape(head))
        for e in rows:
            when, title, rest, url = line_parts(e, with_dates)
            t.append("  " + "  ".join(x for x in (when, title) if x) + (" — " + rest if rest else ""))
            t.append("    " + url)
            h.append('<li>%s<a href="%s">%s</a>%s</li>' % (
                ("<b>%s</b> " % html.escape(when)) if when else "", html.escape(url),
                html.escape(title), (" — " + html.escape(rest)) if rest else ""))
        t.append("")
        h.append("</ul>")

    if running:
        add("ทั้งสัปดาห์ · Running this week", running, with_dates=True)
    for d, rows in by_day.items():
        add(day_head(d), rows)

    t += ["งานประจำสัปดาห์และงานทั้งหมด · Weekly and all events: %s/events.html" % SITE, "",
          "เลิกรับ · Unsubscribe: {{UNSUB}}"]
    h += ['<p style="margin-top:1.5em"><a href="%s/events.html">งานประจำสัปดาห์และงานทั้งหมด · Weekly and all events</a></p>' % SITE,
          '<p style="font-size:13px;color:#666"><a href="{{UNSUB}}">เลิกรับ · Unsubscribe</a></p></div>']
    return {"issue": first.isoformat(), "subject": subject, "count": n,
            "text": "\n".join(t) + "\n", "html": "\n".join(h)}


def token():
    try:
        return subprocess.run([os.path.expanduser("~/.claude/bin/token"), "get", "NEWSLETTER_TOKEN"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        p = os.path.expanduser("~/.tokens/NEWSLETTER_TOKEN")
        return open(p).read().strip() if os.path.exists(p) else ""


def send(issue):
    tok = token()
    if not tok:
        print("newsletter: no NEWSLETTER_TOKEN; not sent")
        return 1
    req = urllib.request.Request(ENDPOINT, data=json.dumps(issue).encode(), method="POST", headers={
        "authorization": "Bearer " + tok, "content-type": "application/json",
        "user-agent": "motdang make_newsletter.py"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)
    except urllib.error.HTTPError as ex:
        print("newsletter: send refused, HTTP %s %s" % (ex.code, ex.read()[:300]))
        return 1
    except Exception as ex:
        print("newsletter: send failed, %s: %s" % (type(ex).__name__, ex))
        return 1
    print("newsletter: %s %s — sent %s, already %s, confirmed on list %s, failed %s" % (
        out.get("issue"), "LIVE" if out.get("live") else "test only", out.get("sent"),
        out.get("already"), out.get("confirmed"), out.get("failed")))
    return 0 if out.get("ok") else 1


def main():
    args = sys.argv[1:]
    first = date.fromisoformat(args[args.index("--date") + 1]) if "--date" in args else date.today()
    doc = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))
    issue = compose(doc["events"], first)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, issue["issue"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(issue, f, ensure_ascii=False, indent=1)
    print("newsletter: %d event(s) -> %s" % (issue["count"], path))
    if issue["count"] == 0:
        print("newsletter: nothing dated this week; not sent")
        return 1
    if "--send" in args:
        return send(issue)
    if "--quiet" not in args:
        print(issue["subject"]); print(issue["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
