#!/usr/bin/env python3
"""One issue of the weekly Chiang Mai events newsletter -> events + contact leads.

Stdlib only. No network: the issue arrives as email, so a human drops the text
into `_incoming/newsletter/YYYY-MM-DD.txt` and this reads it off disk. That is
why `steve-newsletter` is registered with method "manual" in data/sources.json.

WHAT IS TAKEN AND WHAT IS DELIBERATELY LEFT
-------------------------------------------
The body text is venue-supplied press-release copy the compiler pastes in — it
is not his writing and it is not ours. So this takes the FACTS a listing is
made of (when, where, how much, how to book) and never the prose. Every event's
`description` is generated here from those fields. Nothing is copied through.

The prose is still read, for the two things only a newsletter carries:

  1. CONTACT LEADS — phone / LINE / email / website / Facebook for a venue.
     One issue of this thing yields more first-party contact detail than any
     crawl we run, because venues type it into their own release.
  2. VENUES WE DO NOT HAVE. A listing naming a place the 14,493-record
     catalogue has never heard of IS the discovery signal. Those land in
     data/curated/venue_aliases.json `_missing_from_catalogue` for a human.

THE THREE SECTIONS DECAY AT DIFFERENT RATES, so they are parsed apart:
dated events (fast), weekly fixtures under a weekday header (slow), and
notices/promotions (slowest, and not events at all — they are contact leads
plus a standing offer, so they yield leads only).

A WEEKLY FIXTURE IS A RULE, NOT A DATE. The newsletter states the weekday; it
does not state the dates. So each weekly item is emitted with `recurring: True`
and the stated `weekday`, then projected onto its next occurrences inside a
bounded horizon, each marked `from_rule: True`. A projected date is never
allowed to look like an announced one — same discipline as festival_dates.json's
"a rule is not a date".

PAGE SEAMS. pdftotext gives a blank line at every page break, which splits one
listing into two blocks, and occasionally glues a bare weekday header onto the
tail of the block above it. Both are repaired here; the seams a rule cannot
call are pinned per issue in ISSUES, because a wrong split silently merges two
events and that is worse than a parse that stops.

    from read_newsletter import read_issue
    events, leads, stats = read_issue("_incoming/newsletter/2026-08-31.txt")
"""
import json
import os
import re
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCOMING = os.path.join(ROOT, "_incoming", "newsletter")
SOURCE_ID = "steve-newsletter"

# How far ahead a stated weekly rule is projected. The newsletter is weekly, so
# two occurrences covers the gap to the next issue plus a buffer, and nothing
# here has to outlive the source that asserted it. Projecting further would
# only pile up dates no one restated.
RULE_HORIZON_WEEKS = 2

# Per-issue seam repairs. A page break whose first block really does start a new
# listing, where no rule can tell — keyed by issue date, valued by the 1-based
# page index the seam follows. Hand-verified against the PDF, once per issue.
ISSUES = {
    "2026-08-31": {"new_item_after_page": {16, 17, 19, 20, 23, 29, 30, 31, 33}},
}

# PINS. Where a rule misreads a listing — a "9:30 PM" past the window the time
# is read from, "Oct 3 – 10 January 2027" taken as eight days, a venue named
# only after a colon — the correction is written down per issue, beside the
# issue, as `_incoming/newsletter/YYYY-MM-DD.pins.json`, hand-checked against
# the text. Each pin names a `match` substring of the listing and the fields it
# sets: title, venue, time ("HH:MM", or null for all-day), cost, dates (ISO,
# replaces the stated ones), times ({date: "HH:MM"}), end (ISO date), days
# (weekday names, for a fixture that runs on several), drop. `extra` holds
# dated listings the rules never reach — the Notices section's ticketed nights.
def _load_pins(issue_key):
    path = os.path.join(INCOMING, issue_key + ".pins.json")
    if not os.path.exists(path):
        return [], []
    doc = json.load(open(path, encoding="utf-8"))
    return doc.get("pins", []), doc.get("extra", [])


def _pin_for(text, pins):
    for p in pins:
        if p["match"] in text:
            return p
    return None


# A venue writes its own name differently in every release it sends in — "The
# Mellowship 20:30", "The Mellowship Jazz Club" — and each spelling would
# otherwise become its own contact lead and its own unmatched venue. This folds
# the spellings seen in the issues read so far onto one name each. Hand-verified;
# the value is the name to keep, and None drops a string that is not a venue at
# all. Match is on the lower-cased key.
CANON = {
    "the mellowship 20:30": "The Mellowship Jazz Club",
    "the mellowship": "The Mellowship Jazz Club",
    "theoldcityspa": "The Old City Spa",
    "steampunk studio": "STEAMpunk Studio",
    "yummy pizza family restaurant": "Yummy Pizza",
    "game tree café": "Game Tree Café",
    "game tree": "Game Tree Café",
    "one nimman soi 1": "One Nimman",
    "shangri la hotel": "Shangri-La Chiang Mai",
    "recharge at maa yoga studio & spa": "Maa Yoga Studio & Spa",
    "chiang mai holistic dates": "Chiang Mai Holistic",
    "chiang mai holistic weekly tuesdays": "Chiang Mai Holistic",
    "realspace. the best way to meet new people in chiang mai": "RealSpace",
    "the duke's early bird dinner": "The Duke's",
    "the dukes ruamchok branch": "The Duke's Ruamchok",
    "cross chiang mai riverside brunch & beyond at oxygen": "Cross Chiang Mai Riverside",
    "cross chiang mai riverside hotel registration": "Cross Chiang Mai Riverside",
    "oxygen dining room cross chiang mai riverside": "Oxygen Dining Room",
    "cnx cigars -bellevoye pairing night": "CNX Cigars",
    "centara riverside hotel chiang mai": "Centara Riverside Hotel",
    "137 pillars house": "137 Pillars House",
    "137 pillars trading club* guests": "137 Pillars House",
    "sacred grounds": "Sacred Grounds CNX",
    "kad kriangkrai in mae rim": "Kad Kriangkrai",
    "cowboy army riding club huay tung tao reservoir": "Cowboy Army Riding Club",
    "auf de au garden": "Auf der Au Garden",
    "dojo yoga & pilates 3": "Dojo Yoga & Pilates",
    "gooman's cnx in santitham": "GooMan's CNX",
    "faculty of fine art gallery": "Faculty of Fine Arts, Chiang Mai University",
    "berlin’s doner kebab lands in chiang mai": "Berlin's Doner Kebab",
    "intercontinental chiang mai the mae ping make": "InterContinental Chiang Mai The Mae Ping",
    "la friandise trust the chef a": "La Friandise",
    "le crystal restaurant rainy days menu 2,000 thb": "Le Crystal Restaurant",
    "favola chiang mai flavors of tuscany": "Favola",
    "kantary hills full and unlimited carvery night style": "Kantary Hills",
    "eat@rincome restaurant": "Eat@Rincome",
    "sip at ping restaurant": "Sip at Ping",
    "anantara resort": "Anantara Chiang Mai Resort",
    "dhara dhevi": "Dhara Dhevi Chiang Mai",
    "central festival": "Central Festival Chiang Mai",
    "travelodge hotel": "Travelodge Nimman",
    "dusit princess": "Dusit Princess Chiang Mai",
    "your father cnx": "Your Father Cafe",
    "thai 1": "Thai 1 On Bar & Grill",
    "business lounge": "Business Lounge The Brick Plus",
    "central airport plaza -discover english books": "Chiang Mai Hall",
    "lifelong learning payap": "Lifelong Learning Payap Center",
    "big bad wolf sale": "Chiang Mai Hall",     # the book fair's hall, not a place itself
    "payap life long learning center time": "Lifelong Learning Payap Center",
    "excire foto": None,    # an image tool the photographers' group demos, not a venue
    "17:00": None,          # the tail of "Lanna Rugby Club Every Thursday @ 17:00"
    "qxqc+645 suthep": None,   # a plus code, not a name
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

_NEW_BLOCK = re.compile(
    r"^(?:(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December|Sept\.?|Sep)\s+\d"
    r"|(?:%s)\s*$"
    r"|WEEKLY EVENTS|Notices\s*$|Hotel Restaurant Promotions)" % "|".join(DAYS),
    re.I)
_TRAILING_DAY = re.compile(r"\s(%s)$" % "|".join(DAYS))
_PAGE_FOOTER = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")
_MAIL_HEADER = re.compile(r"^\s*\d{1,2}/\d{1,2}/\d{2},\s+\d{1,2}:\d{2}\s+[AP]M\s+Mail\b")

URL = re.compile(r"https?://[^\s<>()\[\]\",]+")
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+66[\s\-]?(?:\(0\))?[\s\-]?\d[\d\s\-]{7,12}\d"
                   r"|\b0\d{1,2}[\s\-]?\d{3}[\s\-]?\d{3,4}\b"
                   r"|\b0\d{8,9}\b)")
# @handle, but never the tail of an email address and never a URL fragment.
HANDLE = re.compile(r"(?<![\w/@.])@([A-Za-z0-9_.]{3,30})\b")

# A date line: "September 1", "Sep 7", "September 5 / 12 / 19 / 26",
# "September 5 & 6", "September 10 – 11", "September 11 – 13".
DATE_HEAD = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Sept\.?|Sep)\s+"
    r"(\d{1,2}(?:\s*(?:[/&]|–|—|-|and|to)\s*\d{1,2})*)\s*:?\s*", re.I)

# A RANGE HAS TO BE TRIED FIRST. "6-11pm" carries its meridiem only on the end
# of the range, so a pattern that looks for <digits><am|pm> finds "11pm" and
# opens the evening five hours late — which is what put Game Tree's Catan night
# at 23:00. Match the whole span, then read the start hour under the meridiem
# the span states.
TIME_RANGE = re.compile(
    r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\s*[-–—]{1,2}\s*"
    r"(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)\b", re.I)
TIME = re.compile(
    r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)\b"
    r"|\b(\d{1,2})[:.](\d{2})\s*(?:hrs\.?)?\b(?!\s*(?:THB|baht))", re.I)
# Where a bold title stops and the body starts.
TITLE_STOP = re.compile(r"\s+[–—]\s+|\s+-\s+|\s*[:;|]\s+|\s+\(")
COST = re.compile(r"(\d[\d,]*)\s*(?:THB|baht|฿)\b|\b(?:฿)\s?(\d[\d,]*)", re.I)
FREE = re.compile(r"\b(free entry|free event|no cost|free to play|admission free"
                  r"|free admission|entry is free|participation is free|is free)\b", re.I)


# ------------------------------------------------------------------ blocks
def _blocks(path, issue_key):
    """Newsletter text -> one string per listing, page seams repaired."""
    raw = open(path, encoding="utf-8").read()
    pages, cur = [], []
    for line in raw.split("\n"):
        s = line.rstrip()
        if _MAIL_HEADER.match(s):
            continue
        if "outlook.live.com/mail/" in s or "mail.google.com/mail/" in s:
            pages.append("\n".join(cur))
            cur = []
            continue
        if _PAGE_FOOTER.match(s):
            continue
        cur.append(s.strip())
    if cur:
        pages.append("\n".join(cur))

    def paras(text):
        out = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
        return [p for p in out if p]

    pinned = ISSUES.get(issue_key, {}).get("new_item_after_page", set())
    blocks = []
    for i, page in enumerate(pages):
        ps = paras(page)
        if not ps:
            continue
        # The first block of a page is usually the tail of the last listing on
        # the page before. Rejoin unless it plainly starts a new one.
        if blocks and i not in pinned and not _NEW_BLOCK.match(ps[0]):
            blocks[-1] += " " + ps[0]
            ps = ps[1:]
        blocks.extend(ps)

    # A weekday header with no blank line of its own rides the block above it.
    out = []
    for b in blocks:
        m = _TRAILING_DAY.search(b)
        if m and len(b) > 40:
            out.append(b[:m.start()].strip())
            out.append(m.group(1))
        else:
            out.append(b)
    return out, len(pages)


def _sections(blocks):
    """-> (dated blocks, {weekday: [blocks]}, notice blocks)."""
    def find(pred, default=None):
        for i, b in enumerate(blocks):
            if pred(b):
                return i
        return default

    i_dated = find(lambda b: DATE_HEAD.match(b), 0)
    i_weekly = find(lambda b: b.startswith("WEEKLY EVENTS"), len(blocks))
    i_notice = find(lambda b: re.match(r"^Notices\b", b), len(blocks))

    dated = blocks[i_dated:i_weekly]
    buckets, day = {d: [] for d in DAYS}, None
    for b in blocks[i_weekly + 1:i_notice]:
        m = re.match(r"^(%s)\s*$" % "|".join(DAYS), b, re.I)
        if m:
            day = m.group(1).capitalize()
            continue
        if day:
            buckets[day].append(b)
    return dated, buckets, blocks[i_notice + 1:]


# ------------------------------------------------------------------ fields
def contacts_of(text):
    urls = [u.rstrip(".,;:") for u in URL.findall(text)]
    def pick(*needles):
        return [u for u in urls if any(n in u for n in needles)]
    maps = pick("goo.gl/maps", "maps.app.goo.gl", "maps.google")
    social = pick("facebook.com", "fb.me", "instagram.com", "whatsapp.com",
                  "wa.me", "meetup.com", "lin.ee", "forms.gle",
                  "docs.google.com/forms")
    emails = sorted(set(EMAIL.findall(text)))
    joined = " ".join(emails)
    return {
        "urls": urls,
        "emails": emails,
        "phones": sorted({re.sub(r"\s+", " ", p).strip() for p in PHONE.findall(text)}),
        "maps": maps,
        "facebook": pick("facebook.com", "fb.me"),
        "instagram": pick("instagram.com"),
        "whatsapp": pick("whatsapp.com", "wa.me"),
        "meetup": pick("meetup.com"),
        "line": pick("lin.ee"),
        "forms": pick("forms.gle", "docs.google.com/forms"),
        "websites": [u for u in urls if u not in maps and u not in social],
        "handles": sorted({"@" + m.group(1) for m in HANDLE.finditer(text)
                           if ("@" + m.group(1)) not in joined}),
    }


def event_url(c):
    """The listing's own link: Meetup, Facebook, a website or form, then its Instagram, LINE or
    WhatsApp. A map link locates the venue and is not the event's page, so it is not one."""
    return (c["meetup"] + c["facebook"] + c["websites"] + c["forms"]
            + c["instagram"] + c["line"] + c["whatsapp"] + [None])[0]


def _dates(head, year, default_month):
    """'5 / 12 / 19 / 26' under 'September' -> [date, ...]. Ranges expand."""
    month = MONTHS.get((head[0] or "").lower().rstrip("."), default_month)
    if (head[0] or "").lower().startswith("sep"):
        month = 9
    nums = [int(n) for n in re.findall(r"\d{1,2}", head[1])]
    if not nums:
        return []
    sep = head[1]
    out = []
    if re.search(r"–|—|(?<=\d)\s*-\s*(?=\d)|\bto\b", sep) and len(nums) == 2:
        lo, hi = sorted(nums)
        nums = list(range(lo, hi + 1)) if hi - lo <= 21 else nums
    for n in nums:
        try:
            out.append(date(year, month, n))
        except ValueError:
            continue
    return out


def _h24(hour, minute, meridiem):
    h = hour % 12 if meridiem else hour
    if meridiem and meridiem.lower() == "pm":
        h += 12
    return "%02d:%02d" % (h, minute) if h < 24 and minute < 60 else None


# "12 noon until 3pm" states a start of midday, but "noon" carries no am/pm for
# the range pattern to read, so the search fell through to "3pm" and opened the
# listing three hours after it ended.
NOON = re.compile(r"\b(?:12\s*)?noon\b|\bmidday\b", re.I)


def _time_of(text):
    """The hour a listing STARTS at -> 'HH:MM', else None when none is stated."""
    head = text[:320]
    n = NOON.search(head)
    m0 = TIME.search(head)
    if n and (not m0 or n.start() <= m0.start()):
        return "12:00"
    m = TIME_RANGE.search(head)
    if m:
        sh, sm, s_mer, eh, _em, e_mer = m.groups()
        sh, eh = int(sh), int(eh)
        # No meridiem on the start of the span: it inherits the end's, unless
        # that would run the span backwards ("11-2pm" starts in the morning).
        mer = s_mer or e_mer
        if not s_mer and sh % 12 > eh % 12:
            mer = "am" if e_mer.lower() == "pm" else "pm"
        got = _h24(sh, int(sm or 0), mer)
        if got:
            return got
    m = TIME.search(head)
    if not m:
        return None
    if m.group(3):
        return _h24(int(m.group(1)), int(m.group(2) or 0), m.group(3))
    return _h24(int(m.group(4)), int(m.group(5)), None)


def _cost_of(text):
    head = text[:420]
    m = COST.search(head)
    if m:
        return (m.group(1) or m.group(2)).replace(",", "") + " THB"
    return "free" if FREE.search(head) else None


# A listing that opens by shouting its weekday — "MONDAY – YOGA RESET at …" —
# repeats what the section header already said, and the band prints the day
# itself. Drop the shout, keep the name.
_TITLE_DAY_SHOUT = re.compile(
    r"^(?:every\s+)?(?:%s)s?\s*[-–—:]\s*" % "|".join(DAYS), re.I)


def _title_of(text, cap=110):
    """The name of the thing. Never a run-on into the body's press-release copy."""  # stylecheck: allow — code docstring
    t = _TITLE_DAY_SHOUT.sub("", text.strip())
    t = TITLE_STOP.split(t, 1)[0].strip(" .,–—-")
    t = re.sub(r"\s*\b\d{1,2}([:.]\d{2})?\s*(am|pm)\b.*$", "", t, flags=re.I).strip()
    if len(t) < 8 or len(t) > cap:
        # The split found nothing usable, so fall back to the first sentence —
        # and if even that runs long, cut at the last word inside the cap. The
        # old fallback took `cap` characters of whatever came next, which is how
        # "…City Center Escape into our peaceful garden next" became a title.
        rest = _TITLE_DAY_SHOUT.sub("", text.strip())
        t = re.split(r"(?<=[.!?])\s+", rest, 1)[0].strip(" .,–—-")
        if len(t) > cap:
            t = re.sub(r"\s+\S*$", "", t[:cap])
    return t.strip(" .,–—-") or text[:60].strip()


# Clauses that run on past the end of a venue name in press-release prose.
_VENUE_TAIL = re.compile(
    r"\s+(?:every|from|on|is|will|has|hosts?|invites?|presents?|which|where|"
    r"for|until|starting|located|open|we\b|our\b|this\b|the\s+quiz|join)\b.*$", re.I)


def _clean_venue(v):
    """Trim a venue string back to the name. Prose, not a database field."""
    v = TITLE_STOP.split(v)[0]
    v = re.split(r"[!?]", v)[0]
    v = re.split(r"\b\d{1,2}([:.]\d{2})?\s*(am|pm|noon)\b", v, flags=re.I)[0]
    v = _VENUE_TAIL.sub("", v)
    v = re.sub(r"\s+\d[\d\s\-./]{5,}$", "", v)          # a trailing phone number
    v = re.sub(r"\s*\.{2,}.*$", "", v)                   # "Ruamchok... 053-240-550"
    v = v.strip(" .,“\"'-–—")
    if not (3 <= len(v) <= 60):
        return None
    return CANON.get(v.lower(), v)


def _venue_of(text):
    """The venue a listing states, from its ' at X' / ' @X' tail. Never guessed.

    The capital is what tells a name from a common noun, but an English writer
    puts a lower-case "the" in front of one — "in the snooker room at the
    Gymkhana Club" — so the article is allowed ahead of the capital and then
    dropped. Requiring the capital immediately after "at" lost that venue
    entirely on the 2026-08-31 issue.
    """
    for m in re.finditer(r"\s(?:at|@)\s*(?:the\s+)?([A-Z0-9“\"][^,–—|;]{2,70})", text[:260]):
        v = _clean_venue(m.group(1))
        if v:
            return v
    return None


# Small words that sit inside a proper name rather than ending it.
_NAME_JOINERS = {"of", "de", "du", "la", "le", "at", "the", "and", "on", "in",
                 "van", "der", "den", "au", "aux", "el", "&"}


def _venue_from_notice(text):
    """A promotions notice opens with the venue's own name, then its prose.

    'Le Crystal Restaurant Rainy Days Menu 2,000 THB…' is a venue followed by an
    offer, so the name is the leading run of capitalised words: stop at the first
    plainly lower-case word that is not a joiner.
    """
    head = TITLE_STOP.split(text, 1)[0]
    out = []
    for tok in head.split()[:9]:
        bare = tok.strip("“\"'(),.")
        if not bare:
            continue
        low = bare.lower()
        if bare[0].islower() and low not in _NAME_JOINERS:
            break
        out.append(tok)
        if len(" ".join(out)) > 46:
            break
    while out and out[-1].strip("“\"'(),.").lower() in _NAME_JOINERS:
        out.pop()
    return _clean_venue(" ".join(out)) if out else None


def _describe(when, venue, cost, booking):
    """The listing line, built from fields. The source's prose is never copied."""
    bits = []
    if when:
        bits.append(when)
    if venue:
        bits.append("at " + venue)
    if cost:
        bits.append(cost)
    if booking:
        bits.append("booking: " + booking)
    return " · ".join(bits)


def _uid(kind, key):
    slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")[:70]
    return "newsletter-%s-%s" % (kind, slug)


# ------------------------------------------------------------------- read
def read_issue(path, horizon_weeks=RULE_HORIZON_WEEKS):
    """-> (events, leads, stats). Pure function of the file; no network."""
    issue_key = os.path.splitext(os.path.basename(path))[0]
    try:
        issued = date.fromisoformat(issue_key)
    except ValueError:
        issued = date.today()
    blocks, n_pages = _blocks(path, issue_key)
    dated, weekly, notices = _sections(blocks)
    pins, extra = _load_pins(issue_key)

    events, leads = [], []

    def lead_from(text, venue):
        c = contacts_of(text)
        if not venue:
            return c
        # FIELD NAMES ARE build.py's channels(), NOT ONES INVENTED HERE. A LINE
        # contact is `lineId` when it is an @handle and `lineUrl` when it is a
        # lin.ee link; a channel filed as plain "line" renders as nothing at all.
        # A venue that prints three numbers keeps all three: `phone` is
        # semicolon-separated by house convention, and channels() shows the first.
        channels = {
            "phone": "; ".join(c["phones"][:3]) if c["phones"] else None,
            "email": c["emails"][0] if c["emails"] else None,
            "website": c["websites"][0] if c["websites"] else None,
            "facebook": c["facebook"][0] if c["facebook"] else None,
            "instagram": c["instagram"][0] if c["instagram"] else None,
            "lineUrl": c["line"][0] if c["line"] else None,
            "lineId": c["handles"][0] if c["handles"] else None,
            "whatsapp": c["whatsapp"][0] if c["whatsapp"] else None,
            "maps": c["maps"][0] if c["maps"] else None,
        }
        if any(channels.values()):
            row = {"venue_name": venue, "source": SOURCE_ID}
            row.update({k: v for k, v in channels.items() if v})
            leads.append(row)
        return c

    # --- dated -----------------------------------------------------------
    for b in dated:
        m = DATE_HEAD.match(b)
        if not m:
            continue
        body = b[m.end():].strip()
        days = _dates((m.group(1), m.group(2)), issued.year, issued.month)
        pin = _pin_for(b, pins) or {}
        if pin.get("drop"):
            continue
        if "dates" in pin:
            days = [date.fromisoformat(x) for x in pin["dates"]]
        if not days:
            continue
        venue = pin["venue"] if "venue" in pin else _venue_of(body)
        title = pin.get("title") or _title_of(body)
        clock = pin["time"] if "time" in pin else _time_of(body)
        cost = pin["cost"] if "cost" in pin else _cost_of(body)
        c = lead_from(b, venue)
        url = event_url(c)
        for d in days:
            clock_d = (pin.get("times") or {}).get(d.isoformat(), clock)
            start = "%s %s:00" % (d.isoformat(), clock_d or "00:00")
            events.append({
                "uid": _uid("d", "%s-%s" % (d.isoformat(), title)),
                "start": start, "all_day": clock_d is None, "tz": "Asia/Bangkok",
                "end": pin.get("end"), "title": title,
                "description": _describe(
                    d.strftime("%-d %B %Y") + (" " + clock_d if clock_d else "")
                    + (" – " + date.fromisoformat(pin["end"]).strftime("%-d %B %Y")
                       if pin.get("end") else ""),
                    venue, cost, url),
                "url": url, "source": SOURCE_ID,
                "venue_name": venue or "", "venue_from": "title" if venue else "",
                "recurring": False, "weekday": None,
                "cost": cost, "from_rule": False,
            })

    # --- weekly fixtures: a stated rule, projected honestly ---------------
    for day, items in weekly.items():
        for b in items:
          pin = _pin_for(b, pins) or {}
          if pin.get("drop"):
              continue
          venue = pin["venue"] if "venue" in pin else _venue_of(b)
          title = pin.get("title") or _title_of(b)
          clock = pin["time"] if "time" in pin else _time_of(b)
          cost = pin["cost"] if "cost" in pin else _cost_of(b)
          c = lead_from(b, venue)
          url = event_url(c)
          for on in pin.get("days") or [day]:
            wd = DAYS.index(on)
            first = issued + timedelta(days=(wd - issued.weekday()) % 7)
            for w in range(horizon_weeks):
                d = first + timedelta(weeks=w)
                events.append({
                    "uid": _uid("w", "%s-%s-%s" % (on, title, d.isoformat())),
                    "start": "%s %s:00" % (d.isoformat(), clock or "00:00"),
                    "all_day": clock is None, "tz": "Asia/Bangkok", "end": None,
                    "title": title,
                    "description": _describe(
                        "every %s%s" % (on, " " + clock if clock else ""),
                        venue, cost, url),
                    "url": url, "source": SOURCE_ID,
                    "venue_name": venue or "", "venue_from": "title" if venue else "",
                    "recurring": True, "weekday": wd,
                    "cost": cost,
                    # This date was computed from a stated weekday, not announced.
                    "from_rule": True,
                })

    # --- notices: contact leads only, never events ------------------------
    # A standing hotel or restaurant offer is not a happening. What it carries
    # that the catalogue wants is the venue's own phone, LINE and booking page.
    for b in notices:
        if len(b) < 40:
            continue
        lead_from(b, _venue_from_notice(b))

    for x in extra:
        for ds in x["dates"]:
            clock = (x.get("times") or {}).get(ds, x.get("time"))
            d = date.fromisoformat(ds)
            events.append({
                "uid": _uid("d", "%s-%s" % (ds, x["title"])),
                "start": "%s %s:00" % (ds, clock or "00:00"),
                "all_day": clock is None, "tz": "Asia/Bangkok",
                "end": x.get("end"), "title": x["title"],
                "description": _describe(
                    d.strftime("%-d %B %Y") + (" " + clock if clock else ""),
                    x.get("venue"), x.get("cost"), x.get("url")),
                "url": x.get("url"), "source": SOURCE_ID,
                "venue_name": x.get("venue") or "",
                "venue_from": "title" if x.get("venue") else "",
                "recurring": False, "weekday": None,
                "cost": x.get("cost"), "from_rule": False,
            })

    # One fixture can arrive twice — "Thursday – Sunday" printed under both
    # Thursday and Sunday — and a pin spreading it across its days lands the
    # second copy on the same uid. Keep the first.
    _seen = set()
    events = [e for e in events if not (e["uid"] in _seen or _seen.add(e["uid"]))]

    stats = {
        "issue": issue_key, "pages": n_pages, "blocks": len(blocks),
        "dated_blocks": len(dated),
        "weekly_blocks": sum(len(v) for v in weekly.values()),
        "notice_blocks": len(notices),
        "events": len(events),
        "events_dated": sum(1 for e in events if not e["recurring"]),
        "events_weekly": sum(1 for e in events if e["recurring"]),
        "leads": len(leads),
        "by_day": {d: len(v) for d, v in weekly.items()},
    }
    return events, leads, stats


def latest_issue(folder=INCOMING):
    """Newest _incoming/newsletter/YYYY-MM-DD.txt, or None."""
    if not os.path.isdir(folder):
        return None
    got = sorted(f for f in os.listdir(folder) if re.match(r"^\d{4}-\d{2}-\d{2}\.txt$", f))
    return os.path.join(folder, got[-1]) if got else None


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else latest_issue()
    if not path:
        print("no issue in %s — drop the text in as YYYY-MM-DD.txt" % INCOMING)
        raise SystemExit(1)
    evs, lds, st = read_issue(path)
    print(json.dumps(st, ensure_ascii=False, indent=1))
    print("\nfirst 3 events:")
    for e in evs[:3]:
        print(" ", e["start"], "|", e["title"][:60], "|", e["venue_name"][:30])
    print("\nfirst 5 leads:")
    for l in lds[:5]:
        print(" ", json.dumps(l, ensure_ascii=False)[:150])
