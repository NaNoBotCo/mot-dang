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

EXIT CODE IS PART OF THE CONTRACT (WO-41 Phase 2): 0 when data/events.json
now holds this harvest, 1 when the run was refused and the previous file
stands. The walks read it — `|| say "events kept the snapshot"` in
morning_walk.sh now says something true rather than only catching a crash.
"""

import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

import ingest           # the shared write discipline (WO-41 Phase 2)
import read_newsletter  # the weekly newsletter: email in, no endpoint to fetch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "events")
REGISTRY = os.path.join(ROOT, "data", "sources.json")
OUT = os.path.join(ROOT, "data", "events.json")
LEADS = os.path.join(ROOT, "data", "contact_leads.json")
UA = "MotDangEvents/1.0 (+https://motdang.net/festivals.html; events for a local directory)"
TIMEOUT = 30
STALE_DAYS = 3          # dated events move fast; a 3-day-old snapshot is stale
# WO-41 Phase 2 — the guards that keep an empty basket from becoming the file.
# Both are about the PIPELINE's health, never about how busy the city is.
MIN_ROWS = 3            # fewer than this from four working feeds is a fault
QUORUM = 2              # of the ical groups + json sources that answered
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
    """iCal's own escaping — backslashes, not entities. See _html for those."""
    return (s.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
             .replace("\\;", ";").replace("\\\\", "\\")).strip()


def _html(s):
    """Decode HTML entities arriving from a web API, once, on the way in."""
    return html.unescape(s or "").strip()


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
    # Two more shapes the Chiang Mai groups write (2026-10-04): a line that
    # opens on the pin, "📍Downtown garden" (a pin inside a bold header,
    # "**📍 Sunday Brunch Gathering**", is a heading and is skipped), and a bold
    # line naming the place and the city, "**Spice Garden, Chiang Mai**".
    m = re.search(r"\\n📍\s*([^*\\][^\\]*?)\s*(?:\\n|$)", description or "")
    if m:
        v = re.sub(r"(?i)^(?:location|venue|where)\s*:\s*", "", _unescape(m.group(1)))
        return v.strip().rstrip(",.;"), "description"
    m = re.search(r"\\n\*\*([^*\\]{3,60}?)\\,\s*Chiang Mai\*\*", description or "")
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
        # A parser states the shape it needs. This one wants The Events
        # Calendar's {"events": [...]} envelope; anything else — a bare list,
        # a string, a null — belongs to some other kind of source and is not
        # this parser's to interpret. Raising a plain ValueError here (rather
        # than letting doc.get explode with an AttributeError) keeps the
        # failure inside the per-source net below, where one wrong source
        # costs its own rows and nothing else's.
        if not isinstance(doc, dict):
            raise ValueError(f"{source_id}: expected an events envelope, "
                             f"got a bare {type(doc).__name__}")
        batch = doc.get("events", [])
        for ev in batch:
            v = ev.get("venue") or {}
            org = ev.get("organizer") or []
            if isinstance(org, list):
                org = org[0] if org else {}
            events.append({
                "source": source_id,
                "uid": str(ev.get("id", "")),
                # WordPress hands these back HTML-encoded — "Qigong for Balance
                # &#038; Self-Empowerment". Decoded here, at the door, because
                # build.py escapes for output and a string that arrives already
                # encoded comes out the far end as visible &#038; on the page.
                # Decode once on the way IN, escape once on the way OUT.
                "title": _html(ev.get("title")),
                "start": ev.get("start_date", ""),
                "end": ev.get("end_date", ""),
                "tz": ev.get("timezone", ""),
                "all_day": bool(ev.get("all_day")),
                "url": ev.get("url", ""),
                "cost": _html(ev.get("cost")),
                "venue_name": _html(v.get("venue")),
                "venue_from": "feed" if v.get("venue") else "",
                "description": _html(re.sub(r"<[^>]+>", " ", ev.get("excerpt") or ""))[:600],
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



# ------------------------------------------------- Chiang Rai: dated in title
# Chiang Rai has no iCal or Events Calendar feed that a plain fetch reaches
# (checked 2026-10-10: the municipality renders client-side, tourismthailand.org
# and the Biennale site answer a bot wall). Chiang Rai Focus, the province's
# local news site, is a WordPress install whose posts API answers, and its press
# posts about events open on the dates, "15–26 ต.ค.69 | …". The title is the
# stated date; a post without that opening is not an event row and is skipped.
THAI_MONTHS = {"ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4, "พ.ค.": 5, "มิ.ย.": 6,
               "ก.ค.": 7, "ส.ค.": 8, "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12}
_M = "|".join(re.escape(m) for m in THAI_MONTHS)
_DASH = "[–—\\-]"
_TD_RANGE = re.compile(r"^\s*(\d{1,2})\s*(%s)?\s*%s\s*(\d{1,2})\s*(%s)\s*(\d{2,4})\s*\|\s*(.+)$" % (_M, _DASH, _M))
_TD_ONE = re.compile(r"^\s*(\d{1,2})\s*(%s)\s*(\d{2,4})\s*\|\s*(.+)$" % _M)


def _be_year(y):
    """'69' and '2569' are Buddhist-era years; '2026' is already Common Era."""
    y = int(y)
    if y < 100:
        y += 2500
    return y - 543 if y > 2400 else y


def parse_title_dates(title):
    """'15–26 ต.ค.69 | …' -> (start_iso, end_iso or None, rest). None if undated."""
    title = _html(title)
    m = _TD_RANGE.match(title)
    try:
        if m:
            d1, m1, d2, m2, yr, rest = m.groups()
            y = _be_year(yr)
            end = date(y, THAI_MONTHS[m2], int(d2))
            start = date(y, THAI_MONTHS[m1 or m2], int(d1))
            return start.isoformat(), end.isoformat(), rest.strip()
        m = _TD_ONE.match(title)
        if m:
            d1, m1, yr, rest = m.groups()
            return date(_be_year(yr), THAI_MONTHS[m1], int(d1)).isoformat(), None, rest.strip()
    except ValueError:
        pass  # 31 ก.ย. and the like: not a date, so not a row
    return None


_VENUE_AT = re.compile(r"(?:^|\s)ณ\s*(?!วัน)([^\s][^\n]{2,70}?)\s*(?=อำเภอ|อ\.|จังหวัด|จ\.|ตำบล|ต\.|\(|\s{2,}|$|[,;])")


def parse_wp_titledate(source_id, endpoint, refetch):
    """WordPress posts API; keeps the posts whose title opens on a stated date."""
    body, _ = cached(source_id, endpoint, refetch)
    posts = json.loads(body)
    if not isinstance(posts, list):
        raise ValueError(f"{source_id}: expected a list of posts, got a bare {type(posts).__name__}")
    events = []
    for p in posts:
        got = parse_title_dates((p.get("title") or {}).get("rendered"))
        if not got:
            continue
        start, end, title = got
        text = re.sub(r"\s+", " ", _html(re.sub(r"<[^>]+>", " ", (p.get("content") or {}).get("rendered") or "")))
        v = _VENUE_AT.search(text)
        venue = v.group(1).strip(" ,.") if v else ""
        events.append({
            "source": source_id,
            "uid": f"{source_id}-{p.get('id')}",
            "title": title,
            "start": start + " 00:00:00",
            "end": end,
            "tz": "Asia/Bangkok",
            "all_day": True,
            "url": p.get("link", ""),
            "cost": "",
            "venue_name": venue,
            "venue_from": "description" if venue else "",
            "description": ("%s – %s" % (start, end) if end else start) + (" · ณ " + venue if venue else ""),
            "city": "cr",
        })
    return events, []


# ---------------------------------------------- Chiang Rai: standing weeklies
CR_STANDING = os.path.join(ROOT, "data", "curated", "events_cr.json")


def cr_standing_rows(today=None):
    """Weekly and daily fixtures of Chiang Rai, from data/curated/events_cr.json.

    Same discipline as read_newsletter's weekly section: a rule is not a date.
    The file holds the rule, the page that states it and the day it was read;
    each occurrence inside the rule's horizon is marked from_rule so it never
    reads as an announced date. The window rolls with every harvest."""
    if not os.path.exists(CR_STANDING):
        return []
    with open(CR_STANDING) as fh:
        rules = json.load(fh).get("rules", [])
    today = today or date.today()
    out = []
    for r in rules:
        days = r["days"]            # weekday numbers, Monday 0
        clock = r.get("time")       # "19:00" when every source agrees, else null
        for i in range(int(r.get("horizon_days", 56))):
            d = today + timedelta(days=i)
            if d.weekday() not in days:
                continue
            out.append({
                "uid": "cr-w-%s-%s" % (r["id"], d.isoformat()),
                "start": "%s %s:00" % (d.isoformat(), clock or "00:00"),
                "all_day": clock is None, "tz": "Asia/Bangkok", "end": None,
                "title": r["title"], "description": r["description"],
                "url": r["url"], "source": r["source"],
                "venue_name": r.get("venue", ""), "venue_from": "title" if r.get("venue") else "",
                "recurring": True, "weekday": d.weekday(),
                "cost": r.get("cost"), "from_rule": True, "city": "cr",
            })
    return out


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


# Every channel a lead can carry. LINE, Facebook and a maps pin were being
# dropped on the floor here while the newsletter handed over 49 Facebook pages,
# 14 LINE handles and 19 Google Maps links in one issue — and LINE is the
# channel that actually answers in Thailand, ranking second only to the phone in
# build.py's channels(). A field this file does not copy is a field the
# catalogue never sees.
LEAD_FIELDS = ("phone", "website", "email", "address", "city",
               "facebook", "instagram", "lineId", "lineUrl", "maps", "whatsapp")


def dedupe_leads(leads):
    out = {}
    for l in leads:
        key = (l.get("venue_name") or "").lower().strip()
        if not key:
            continue
        cur = out.setdefault(key, {"venue_name": l["venue_name"], "sources": []})
        for f in LEAD_FIELDS:
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

    # .get, not [] — a verified source may legitimately carry no method here.
    # major-showtimes lost its method key when the Cineplex recipe moved out of
    # the tree, and the KeyError stopped every refetch dead, which is how the
    # events feed came to sit three days stale without anyone noticing. That
    # source has its own importer; it was never this harvester's to fetch.
    #
    # WO-41 Phase 2 — AND IT MUST YIELD EVENTS. data/sources.json is the whole
    # fleet's registry, not this harvester's private list: later orders
    # registered the OBEC school register, Open-Meteo and the cannabis map
    # there, all `method: json` and all verified. This harvester took every one
    # of them, and on 2026-08-25 the school register — a 17 MB JSON *list* —
    # met parse_tribe()'s doc.get() and killed the whole batch. Every morning
    # since, the events feed harvested nothing. The registry already says what
    # each source is for; asking it is the fix.
    fetchable = [s for s in sources
                 if s.get("status") == "verified"
                 and s.get("method") in ("ical", "json", "wp-titledate")
                 and "events" in (s.get("yields") or [])]
    print(f"🐜 {len(fetchable)} fetchable source(s) of {len(sources)} in the registry")

    # WO-41 Phase 2 — THE NET IS WIDE ON PURPOSE. It used to catch only
    # (URLError, HTTPError, OSError): the transport failures somebody had
    # thought of. A source whose payload had merely CHANGED SHAPE raised
    # straight past it and took the other sources' rows with it, which is
    # precisely how one school register silenced the whole events feed for
    # four days. Isolation has to hold against the failure nobody predicted,
    # so every exception a single source can raise stops at that source —
    # and is recorded by name rather than swallowed. KeyboardInterrupt and
    # SystemExit are not Exception subclasses and still stop the run.
    events, leads, failures, ok_sources = [], [], [], []
    for s in fetchable:
        if s["method"] == "ical":
            for group in s.get("groups", []):
                url = s["endpoint"].replace("{group}", group)
                try:
                    body, was_cached = cached(f"{s['id']}-{group}", url, refetch)
                    got = parse_ical(body, s["id"])
                    events.extend(got)
                    ok_sources.append(group)
                    print(f"   {'cache' if was_cached else 'fetch'}  {group}: {len(got)} event(s)")
                except Exception as ex:
                    failures.append((group, f"{type(ex).__name__}: {ex}"))
                    print(f"   FAIL   {group}: {type(ex).__name__}: {ex}")
        elif s["method"] == "json":
            try:
                got, got_leads = parse_tribe(s["id"], s["endpoint"], refetch)
                events.extend(got)
                leads.extend(got_leads)
                ok_sources.append(s["id"])
                print(f"   ok     {s['id']}: {len(got)} event(s), {len(got_leads)} contact lead(s)")
            except Exception as ex:
                failures.append((s["id"], f"{type(ex).__name__}: {ex}"))
                print(f"   FAIL   {s['id']}: {type(ex).__name__}: {ex}")
        elif s["method"] == "wp-titledate":
            try:
                got, _ = parse_wp_titledate(s["id"], s["endpoint"], refetch)
                events.extend(got)
                ok_sources.append(s["id"])
                print(f"   ok     {s['id']}: {len(got)} dated post(s)")
            except Exception as ex:
                failures.append((s["id"], f"{type(ex).__name__}: {ex}"))
                print(f"   FAIL   {s['id']}: {type(ex).__name__}: {ex}")

    # The weekly newsletter is the one source that arrives as EMAIL, so it has
    # no endpoint to fetch: a human drops the issue's text into
    # _incoming/newsletter/ and read_newsletter.py parses it off disk. It rides
    # this run rather than writing its own file so that it passes through the
    # same validate/atomic/never-destructive discipline as every other feed —
    # and so a bad parse is refused instead of published. No issue on disk is a
    # normal state, not a failure: it just means nobody has pasted this week's
    # in yet.
    issue = read_newsletter.latest_issue()
    if issue:
        try:
            got, got_leads, st = read_newsletter.read_issue(issue)
            events.extend(got)
            leads.extend(got_leads)
            ok_sources.append(read_newsletter.SOURCE_ID)
            print(f"   read   {read_newsletter.SOURCE_ID}: {st['events']} event(s) "
                  f"({st['events_dated']} dated, {st['events_weekly']} from weekly "
                  f"rules), {st['leads']} contact lead(s) — issue {st['issue']}")
        except Exception as ex:
            failures.append((read_newsletter.SOURCE_ID, f"{type(ex).__name__}: {ex}"))
            print(f"   FAIL   {read_newsletter.SOURCE_ID}: {type(ex).__name__}: {ex}")
    else:
        print(f"   none   {read_newsletter.SOURCE_ID}: no issue in "
              f"{read_newsletter.INCOMING}")

    # Chiang Rai's standing weeklies: rules in data/curated/events_cr.json, each
    # carrying the page that states it. A static file, so it is not a quorum source.
    cr_rows = cr_standing_rows()
    events.extend(cr_rows)
    print(f"   rules  events_cr.json: {len(cr_rows)} occurrence(s) projected")

    events = mark_recurring(events)
    events.sort(key=lambda e: (e.get("start") or "", e.get("title") or ""))
    horizon = (date.today() - timedelta(days=1)).isoformat()
    # A run of days that began before the horizon and is still going (an expo,
    # a farewell month) is upcoming by its end date; build.py reads it the same way.
    upcoming = [e for e in events if (e.get("end") or e.get("start") or "") >= horizon]
    leads = dedupe_leads(leads)

    # WO-41 Phase 2. This is where 69 good events were lost on 2026-08-24: the
    # write was unconditional, so a run that harvested nothing published
    # nothing over the top of everything. Both files now go through the shared
    # discipline — validated, atomic, and never destructive when the basket
    # comes home empty.
    #
    # MIN_ROWS is deliberately low. The question this guard answers is "did the
    # pipeline break", not "was it a busy week": a quiet fortnight in the city
    # is a true thing the site may print, while three events out of four
    # working feeds is a fault. Quorum carries the rest of the weight, because
    # a feed can be broken while still returning rows.
    ok = ingest.write(
        OUT, {"generated": date.today().isoformat(),
              "count": len(upcoming),
              "recurring": sum(1 for e in upcoming if e["recurring"]),
              "events": upcoming},
        count=len(upcoming), min_rows=MIN_ROWS,
        sources_ok=ok_sources, sources_failed=failures, quorum=QUORUM,
        label="events.json")
    # The leads file rides the same run and the same verdict: if the harvest
    # was not trustworthy enough to publish its events, its contact leads are
    # not trustworthy enough to overwrite the good ones either.
    if ok:
        ingest.write(LEADS, {"generated": date.today().isoformat(),
                             "count": len(leads), "leads": leads},
                     count=len(leads), min_rows=0,
                     sources_ok=ok_sources, sources_failed=failures,
                     label="contact_leads.json")
    else:
        ingest.refuse(LEADS, "the same harvest that could not publish events",
                      ok_sources, failures)
    # What was on stays on record after its day (Nan, 2026-10-04): the ledger
    # is what lets a venue's past evenings count toward its page and search.
    if ok:
        import event_ledger
        event_ledger.main([])
    if failures:
        print(f"⚠  {len(failures)} source(s) failed: {[f[0] for f in failures]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
