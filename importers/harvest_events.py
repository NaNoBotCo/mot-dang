#!/usr/bin/env python3
"""Harvest events from the registry in data/sources.json into data/events.json.

Two things come out of one pass, because the sources carry both:

  1. EVENTS — what is on, and when. Dated one-offs decay in days; weekly
     recurring nights barely decay at all, so they are marked and kept longer.
  2. CONTACT LEADS — phone / website / email that a source states about a
     venue. These feed the contact-coverage mission, which is the thing the
     catalogue is actually short of. An events feed that also tells us a
     museum's phone number is worth more than one that doesn't.

Snapshot-first and resumable, same shape as check_links.py and
crawl_overpass.py: every fetch lands in cache/events/ with the date it was
taken, so a rerun only touches what is missing or stale, and build.py never
makes a network call.

    python3 importers/harvest_events.py             # fetch what is stale
    python3 importers/harvest_events.py --refetch   # ignore cache
    python3 importers/harvest_events.py --list      # show registry, fetch nothing
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "events")
REGISTRY = os.path.join(ROOT, "data", "sources.json")
OUT = os.path.join(ROOT, "data", "events.json")
LEADS = os.path.join(ROOT, "data", "contact_leads.json")
UA = "MotDangEvents/1.0 (+https://motdang.net/festivals.html; events for a local directory)"
TIMEOUT = 30
STALE_DAYS = 3          # dated events move fast; a 3-day-old snapshot is stale
PAUSE = 2.0             # gentle between live fetches, same manners as the crawler


# ------------------------------------------------------------------ fetching
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


def cached(key, url, refetch=False):
    """Return text for url, from cache/events/<key>.json unless stale."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, key + ".json")
    if not refetch and os.path.exists(path):
        try:
            with open(path) as fh:
                snap = json.load(fh)
            taken = datetime.strptime(snap["fetched"], "%Y-%m-%d").date()
            if (date.today() - taken).days < STALE_DAYS:
                return snap["body"], True
        except (ValueError, KeyError, json.JSONDecodeError):
            pass  # unreadable snapshot: refetch rather than trust it
    body = fetch(url)
    with open(path, "w") as fh:
        json.dump({"url": url, "fetched": date.today().isoformat(), "body": body}, fh)
    time.sleep(PAUSE)
    return body, False


# -------------------------------------------------------------- ical parsing
def _unfold(text):
    """RFC 5545 line unfolding: a leading space or tab continues the line above."""
    out = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and out:
            out[-1] += raw[1:]
        else:
            out.append(raw)
    return out


def _ical_value(line):
    """Split 'DTSTART;TZID=Asia/Bangkok:20260731T130000' into (name, params, value)."""
    if ":" not in line:
        return None, {}, ""
    head, value = line.split(":", 1)
    parts = head.split(";")
    name = parts[0].upper()
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.upper()] = v
    return name, params, value


def _ical_dt(value, params):
    """Return (iso_string, all_day). Keeps local wall time; TZID noted separately."""
    v = value.strip()
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", v):
        try:
            return datetime.strptime(v, "%Y%m%d").date().isoformat(), True
        except ValueError:
            return v, True
    v = v.rstrip("Z")
    try:
        return datetime.strptime(v, "%Y%m%dT%H%M%S").isoformat(sep=" "), False
    except ValueError:
        return v, False


def _unescape(s):
    return (s.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
             .replace("\\;", ";").replace("\\\\", "\\")).strip()


def venue_from_text(title, description):
    """Recover a venue when the feed does not state one.

    Meetup's iCal carries no LOCATION property at all (verified: 0 across every
    Chiang Mai feed checked), so the venue survives only in prose — either a
    '📍 **Location:**' line in the description or an '@ '/'at ' tail on the
    title. Recovers about half of them. Whatever it finds is marked as inferred,
    never as stated, because a guessed venue must not be mistaken for a fact.
    """
    # Run against the RAW description, where "\n" is still a literal backslash-n
    # separator. Unescaping first turns those into spaces and the capture then
    # runs on into the next paragraph.
    m = re.search(r"\*\*Location:\*\*\s*((?:\\,|[^\\])+)", description or "")
    if m:
        return _unescape(m.group(1)).strip().rstrip(",.;"), "description"
    m = re.search(r"\s+@\s+(.+)$", title or "")
    if m:
        return m.group(1).strip().rstrip(",.;"), "title"
    m = re.search(r"\s+at\s+([A-Z][^,]*)$", title or "")
    if m:
        return m.group(1).strip().rstrip(",.;"), "title"
    return None, None


def parse_ical(text, source_id):
    """Extract VEVENTs. Meetup pre-expands weekly recurrences into separate events."""
    events, cur = [], None
    for line in _unfold(text):
        s = line.strip()
        if s == "BEGIN:VEVENT":
            cur = {}
            continue
        if s == "END:VEVENT":
            if cur and cur.get("title") and cur.get("start"):
                events.append(cur)
            cur = None
            continue
        if cur is None:
            continue
        name, params, value = _ical_value(s)
        if name == "SUMMARY":
            cur["title"] = _unescape(value)
        elif name == "DTSTART":
            cur["start"], cur["all_day"] = _ical_dt(value, params)
            cur["tz"] = params.get("TZID", "")
        elif name == "DTEND":
            cur["end"], _ = _ical_dt(value, params)
        elif name == "LOCATION":
            cur["venue_name"] = _unescape(value)
        elif name == "URL":
            cur["url"] = value.strip()
        elif name == "UID":
            cur["uid"] = value.strip()
        elif name == "DESCRIPTION":
            cur["_raw_description"] = value
            cur["description"] = _unescape(value)[:600]
    for e in events:
        e["source"] = source_id
        if e.get("venue_name"):
            e["venue_from"] = "feed"
        else:
            guess, how = venue_from_text(e.get("title", ""), e.pop("_raw_description", ""))
            e["venue_name"], e["venue_from"] = (guess or ""), (how or "")
        e.pop("_raw_description", None)
    return events


# ------------------------------------------------------- the events calendar
def parse_tribe(source_id, endpoint, refetch):
    """The Events Calendar REST API — paginated; venue carries real contact data."""
    events, leads, page, seen_pages = [], [], 1, 0
    while True:
        url = endpoint + ("&" if "?" in endpoint else "?") + f"page={page}"
        body, was_cached = cached(f"{source_id}-p{page}", url, refetch)
        try:
            doc = json.loads(body)
        except json.JSONDecodeError:
            break
        batch = doc.get("events", [])
        for ev in batch:
            v = ev.get("venue") or {}
            org = ev.get("organizer") or []
            if isinstance(org, list):
                org = org[0] if org else {}
            events.append({
                "source": source_id,
                "uid": str(ev.get("id", "")),
                "title": (ev.get("title") or "").strip(),
                "start": ev.get("start_date", ""),
                "end": ev.get("end_date", ""),
                "tz": ev.get("timezone", ""),
                "all_day": bool(ev.get("all_day")),
                "url": ev.get("url", ""),
                "cost": (ev.get("cost") or "").strip(),
                "venue_name": (v.get("venue") or "").strip(),
                "venue_from": "feed" if v.get("venue") else "",
                "description": re.sub(r"<[^>]+>", " ", ev.get("excerpt") or "")[:600].strip(),
            })
            # A venue stated by the organiser is a contact lead, not a guess.
            if v.get("venue") and (v.get("phone") or v.get("website")):
                leads.append({
                    "source": source_id,
                    "venue_name": v["venue"].strip(),
                    "phone": (v.get("phone") or "").strip() or None,
                    "website": (v.get("website") or "").strip() or None,
                    "address": (v.get("address") or "").strip() or None,
                    "city": (v.get("city") or "").strip() or None,
                })
            if org.get("email"):
                leads.append({
                    "source": source_id,
                    "venue_name": (org.get("organizer") or "").strip(),
                    "email": org["email"].strip(),
                    "phone": None, "website": None, "address": None, "city": None,
                })
        seen_pages += 1
        total_pages = int(doc.get("total_pages") or 1)
        if page >= total_pages or seen_pages > 20 or not batch:
            break
        page += 1
    return events, leads


# ------------------------------------------------------------------ shaping
def mark_recurring(events):
    """A title appearing on the same weekday two-plus times is a weekly fixture.

    Those are the slow-decaying ones worth keeping on a venue page; one-off
    dated events are not. Cheap heuristic, no recurrence rules needed, because
    Meetup hands us pre-expanded occurrences.
    """
    by_key = {}
    for e in events:
        try:
            d = datetime.fromisoformat(e["start"].replace(" ", "T")).date()
        except ValueError:
            continue
        by_key.setdefault((e["source"], e["title"], d.weekday()), []).append(e)
    for group in by_key.values():
        if len(group) >= 2:
            wd = datetime.fromisoformat(group[0]["start"].replace(" ", "T")).weekday()
            for e in group:
                e["recurring"] = True
                e["weekday"] = wd
    for e in events:
        e.setdefault("recurring", False)
        e.setdefault("weekday", None)
    return events


def dedupe_leads(leads):
    out = {}
    for l in leads:
        key = (l.get("venue_name") or "").lower().strip()
        if not key:
            continue
        cur = out.setdefault(key, {"venue_name": l["venue_name"], "sources": []})
        for f in ("phone", "website", "email", "address", "city"):
            if l.get(f) and not cur.get(f):
                cur[f] = l[f]
        if l["source"] not in cur["sources"]:
            cur["sources"].append(l["source"])
    return sorted(out.values(), key=lambda x: x["venue_name"].lower())


# --------------------------------------------------------------------- main
def main():
    refetch = "--refetch" in sys.argv
    with open(REGISTRY) as fh:
        registry = json.load(fh)
    sources = registry["sources"]

    if "--list" in sys.argv:
        print(f"🐜 {len(sources)} source(s) in the registry:")
        for s in sources:
            print(f"  [{s['status']:>19}] {s['cadence']:>9}  {s['id']:<24} {s['name']}")
        return

    fetchable = [s for s in sources
                 if s["status"] == "verified" and s["method"] in ("ical", "json")]
    print(f"🐜 {len(fetchable)} fetchable source(s) of {len(sources)} in the registry")

    events, leads, failures = [], [], []
    for s in fetchable:
        if s["method"] == "ical":
            for group in s.get("groups", []):
                url = s["endpoint"].replace("{group}", group)
                try:
                    body, was_cached = cached(f"{s['id']}-{group}", url, refetch)
                    got = parse_ical(body, s["id"])
                    events.extend(got)
                    print(f"   {'cache' if was_cached else 'fetch'}  {group}: {len(got)} event(s)")
                except (urllib.error.URLError, urllib.error.HTTPError, OSError) as ex:
                    failures.append((group, str(ex)))
                    print(f"   FAIL   {group}: {ex}")
        elif s["method"] == "json":
            try:
                got, got_leads = parse_tribe(s["id"], s["endpoint"], refetch)
                events.extend(got)
                leads.extend(got_leads)
                print(f"   ok     {s['id']}: {len(got)} event(s), {len(got_leads)} contact lead(s)")
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as ex:
                failures.append((s["id"], str(ex)))
                print(f"   FAIL   {s['id']}: {ex}")

    events = mark_recurring(events)
    events.sort(key=lambda e: (e.get("start") or "", e.get("title") or ""))
    horizon = (date.today() - timedelta(days=1)).isoformat()
    upcoming = [e for e in events if (e.get("start") or "") >= horizon]
    leads = dedupe_leads(leads)

    with open(OUT, "w") as fh:
        json.dump({"generated": date.today().isoformat(),
                   "count": len(upcoming),
                   "recurring": sum(1 for e in upcoming if e["recurring"]),
                   "events": upcoming}, fh, ensure_ascii=False, indent=1)
    with open(LEADS, "w") as fh:
        json.dump({"generated": date.today().isoformat(),
                   "count": len(leads), "leads": leads}, fh, ensure_ascii=False, indent=1)

    print(f"🐜 {len(upcoming)} upcoming event(s) "
          f"({sum(1 for e in upcoming if e['recurring'])} recurring) -> {OUT}")
    print(f"🐜 {len(leads)} contact lead(s) -> {LEADS}")
    if failures:
        print(f"⚠  {len(failures)} source(s) failed: {[f[0] for f in failures]}")


if __name__ == "__main__":
    main()
