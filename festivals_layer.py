#!/usr/bin/env python3
"""The festivals layer, part two: a page per festival, the year wheel, and the
recurring-festival calendar feed.

Why this is a separate module rather than more of build.py: build.py is a busy
file and this is a self-contained surface — a canon (data/festivals.json), one
generated drawing, one page per entry, one feed. Everything here runs off
build.py's own helpers, which are handed over in a globals dict, so there is
exactly one definition of page(), bi() and share_block() on the site.

Two models, deliberately not one:

  Festival — the recurring canon. Timeless, hand-curated, carries a date *rule*
             and never a date. That is the whole file at data/festivals.json.
  Event    — a dated instance in one year at one venue, from data/events.json.
             An event links back to a festival when it is an instance of one.

The canon is written once; only the instances need a routine crawl. That split
is what lets 33 festival pages exist without a crawler behind them yet.

Entry point: emit(globals_of_build, events, data). Also runnable on its own
against an already-built docs/ for iterating on the drawing:

    python3 festivals_layer.py
"""
import base64
import datetime
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ------------------------------------------------------------------ palette
# One colour per family of festival, chosen to survive being printed in grey
# and to read at dot size. Inline hex, not CSS variables: the wheel is also
# written out as a standalone .svg that has no stylesheet to inherit from.
FAMILY = [
    ("religious", "#B8912E", "งานบุญ ประเพณีล้านนา", "Merit & Lanna tradition"),
    ("hilltribe", "#3F5AA6", "ประเพณีชาติพันธุ์บนดอย", "Highland community traditions"),
    ("arts", "#B4341A", "ศิลปะ หัตถกรรม งานใหญ่", "Arts, craft & the big civic events"),
    ("seasonal", "#3F7F4F", "ฤดูกาล ดอกไม้ ธรรมชาติ", "Seasons, flowers & natural highlights"),
    ("royal", "#6E4A9E", "วันสำคัญของชาติ", "National & royal days"),
    ("market", "#C0641B", "ตลาด อาหาร ชุมชนจีน", "Markets, food & the Chinese community"),
]
FAMILY_COLOR = {k: c for k, c, _, _ in FAMILY}

# A festival's tags decide its family; first match wins, so order is the rule.
# Merit is tested before nation: Makha Bucha is tagged "national" because it is
# a national holiday, but it belongs with the merit days on the wheel, not with
# the royal ones — which is why "royal" here means only the explicit tag.
TAG_FAMILY = [
    ({"hilltribe", "akha", "hmong", "lisu", "shan"}, "hilltribe"),
    ({"religious", "lanna", "city-spirit", "temple-fair", "ordination",
      "pilgrimage"}, "religious"),
    ({"royal"}, "royal"),
    ({"chinese", "market", "food"}, "market"),
    ({"flowers", "seasonal", "agriculture", "viewpoint", "harvest"}, "seasonal"),
    ({"art", "design", "craft", "parade", "countdown", "family", "lanterns",
      "fair", "heritage", "flagship"}, "arts"),
]


def family_of(f):
    tags = set(f.get("tags") or [f.get("tag")])
    for keys, fam in TAG_FAMILY:
        if tags & keys:
            return fam
    return "seasonal"


MONTH_ABBR_TH = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                 "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

# ------------------------------------------------------------------- wheel
W = 760
CX = CY = W / 2
R_RIM_OUT = 362
R_RIM_IN = 322
R_LABEL = 342
R_TRACK_TOP = 300
TRACK_GAP = 23
TRACKS = 7


def _pt(r, deg):
    a = math.radians(deg - 90)
    return CX + r * math.cos(a), CY + r * math.sin(a)


def _arc(r, d0, d1):
    x0, y0 = _pt(r, d0)
    x1, y1 = _pt(r, d1)
    large = 1 if (d1 - d0) % 360 > 180 else 0
    return f"M{x0:.1f},{y0:.1f} A{r:.0f},{r:.0f} 0 {large} 1 {x1:.1f},{y1:.1f}"


def _wedge(r0, r1, d0, d1):
    x0, y0 = _pt(r1, d0)
    x1, y1 = _pt(r1, d1)
    x2, y2 = _pt(r0, d1)
    x3, y3 = _pt(r0, d0)
    large = 1 if (d1 - d0) % 360 > 180 else 0
    return (f"M{x0:.1f},{y0:.1f} A{r1:.0f},{r1:.0f} 0 {large} 1 {x1:.1f},{y1:.1f} "
            f"L{x2:.1f},{y2:.1f} A{r0:.0f},{r0:.0f} 0 {large} 0 {x3:.1f},{y3:.1f} Z")


def _span(f):
    """Angular span of a festival, in degrees clockwise from the top of the year.

    A one-month entry gets a short mark in the middle of its month. A seasonal
    entry that runs November to February gets a real arc that wraps past the
    top of the wheel, because that is what the reader needs to see: the cool
    season is one thing, not four separate things.
    """
    months = f.get("months") or [f["month"]]
    if len(months) <= 1:
        c = (f["month"] - 1) * 30 + 15
        return c - 9, c + 9
    start = months[0]
    d0 = (start - 1) * 30 + 2
    d1 = d0 + len(months) * 30 - 4
    return d0, d1


def _overlaps(a0, a1, b0, b1, pad=6.0):
    """Do two arcs collide on the wheel? Compared modulo the year, so an arc
    that wraps past December is tested against January properly."""
    for shift in (-360, 0, 360):
        if a0 - pad < b1 + shift and b0 + shift < a1 + pad:
            return True
    return False


def wan_phra_year(year):
    """Every วันพระ in a calendar year, as (day-of-year angle, is-a-full-half).

    Reuses importers/make_sky.py's moon_for — the same mean-synodic formula the
    moon tile already publishes, shared with coucal-clock and wichaa.net/moon,
    so the wheel cannot contradict the widget wall two pages away. It is an
    approximation of the official Thai lunar calendar, not the calendar itself:
    the wheel says so in its key, and no festival date is derived from it.
    """
    import sys
    sys.path.insert(0, str(ROOT / "importers"))
    try:
        from make_sky import moon_for
    except ImportError:
        return []
    dim = [0, 31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    out = []
    d = datetime.date(year, 1, 1)
    while d.year == year:
        m = moon_for(datetime.datetime(d.year, d.month, d.day, 20, 0))
        if m["wan_phra"]:
            deg = (d.month - 1) * 30 + (d.day - 1) / dim[d.month] * 30
            out.append((deg, m["thai_day"] == 15))
        d += datetime.timedelta(days=1)
    return out


def wheel_svg(fests, today, base, day_color="#C2401C"):
    """The year as a wheel: months around the rim, one mark per festival, today
    where today is. It is the infographic, the share card and the navigation
    device in one drawing — every mark is a link to that festival's page."""
    order = sorted(fests, key=lambda f: (min(f.get("months") or [f["month"]]) if len(f.get("months") or []) <= 1
                                         else f["months"][0], f["month"]))
    tracks = [[] for _ in range(TRACKS)]
    placed = []
    for f in order:
        d0, d1 = _span(f)
        for ti, occupied in enumerate(tracks):
            if not any(_overlaps(d0, d1, b0, b1) for b0, b1 in occupied):
                occupied.append((d0, d1))
                placed.append((f, ti, d0, d1))
                break
        else:  # more collisions than tracks — put it on the innermost ring
            tracks[-1].append((d0, d1))
            placed.append((f, TRACKS - 1, d0, d1))

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'viewBox="0 0 {W} {W}" width="{W}" height="{W}" role="img" '
           f'aria-labelledby="wheeltitle wheeldesc" class="yearwheel">',
           '<title id="wheeltitle">ปฏิทินเทศกาลเชียงใหม่-เชียงราย ทั้งปี · '
           'The Chiang Mai and Chiang Rai festival year</title>',
           '<desc id="wheeldesc">Twelve months clockwise from January at the top. Each mark is one '
           'recurring festival, coloured by family: gold for merit-making and Lanna tradition, indigo '
           'for highland community traditions, red for arts and the big civic events, green for '
           'seasonal and natural highlights, purple for national and royal days, orange for markets '
           'and the Chinese community. The pointer shows today.</desc>',
           f'<rect width="{W}" height="{W}" fill="#FBF6EE"/>']

    # month band
    for m in range(1, 13):
        d0, d1 = (m - 1) * 30, m * 30
        shade = "#F2E9DA" if m % 2 else "#EADFCE"
        out.append(f'<path d="{_wedge(R_RIM_IN, R_RIM_OUT, d0, d1)}" fill="{shade}"/>')
        lx, ly = _pt(R_LABEL, d0 + 15)
        out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" '
                   f'font-family="Sarabun,Noto Sans Thai,sans-serif" font-size="17" '
                   f'fill="#8F2E13" font-weight="700">{MONTH_ABBR_TH[m]}</text>')
        x0, y0 = _pt(R_RIM_IN, d0)
        x1, y1 = _pt(R_RIM_OUT, d0)
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                   f'stroke="#FBF6EE" stroke-width="2"/>')

    # วันพระ ticks, just inside the month band. Every wan phra in the year is a
    # standing "go to a wat" day, so the wheel carries them as texture — short
    # marks for the 8th of each half, long ones for the 15th.
    for deg, is_full in wan_phra_year(today.year):
        r0 = R_RIM_IN - (20 if is_full else 11)
        x0, y0 = _pt(r0, deg)
        x1, y1 = _pt(R_RIM_IN - 3, deg)
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                   f'stroke="#B8912E" stroke-width="{2.2 if is_full else 1.4}" '
                   f'opacity="{0.6 if is_full else 0.35}"/>')

    # faint month spokes across the tracks, so the eye can carry a mark back
    # to its month without counting rings
    r_in = R_TRACK_TOP - TRACKS * TRACK_GAP - 6
    for m in range(12):
        x0, y0 = _pt(r_in, m * 30)
        x1, y1 = _pt(R_RIM_IN, m * 30)
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                   f'stroke="#EADFCE" stroke-width="1"/>')

    for f, ti, d0, d1 in placed:
        r = R_TRACK_TOP - ti * TRACK_GAP
        col = FAMILY_COLOR[family_of(f)]
        dashed = f.get("confidence") == "needs-verification"
        seasonal = len((f.get("months") or [])) > 1
        href = f'{base}festivals/{f["id"]}.html'
        cap = f'{f["name_th"]} · {f["name_en"]} — {f["window_th"]}'
        dash = 'stroke-dasharray="7 5" ' if dashed else ''
        out.append(f'<a xlink:href="{_x(href)}" href="{_x(href)}"><title>{_x(cap)}</title>')
        out.append(f'<path d="{_arc(r, d0, d1)}" fill="none" stroke="{col}" '
                   f'stroke-width="{9 if seasonal else 11}" stroke-linecap="round" '
                   f'{dash}opacity="0.92"/>')
        out.append('</a>')

    # today
    dim = [0, 31, 29 if today.year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    tdeg = (today.month - 1) * 30 + (today.day - 1) / dim[today.month] * 30
    x0, y0 = _pt(r_in - 14, tdeg)
    x1, y1 = _pt(R_RIM_OUT + 4, tdeg)
    out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
               f'stroke="{day_color}" stroke-width="2.5" opacity="0.85"/>')
    dx, dy = _pt(r_in - 14, tdeg)
    out.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="5" fill="{day_color}"/>')

    # hub
    out.append(f'<circle cx="{CX}" cy="{CY}" r="{r_in - 26:.0f}" fill="#FFFFFF" stroke="#EADFCE"/>')
    out.append(f'<text x="{CX}" y="{CY - 20}" text-anchor="middle" '
               f'font-family="Sarabun,Noto Sans Thai,sans-serif" font-size="26" font-weight="800" '
               f'fill="#8F2E13">เทศกาลทั้งปี</text>')
    out.append(f'<text x="{CX}" y="{CY + 8}" text-anchor="middle" '
               f'font-family="Sarabun,Noto Sans Thai,sans-serif" font-size="15" fill="#2A1E16">'
               f'เชียงใหม่ · เชียงราย</text>')
    out.append(f'<text x="{CX}" y="{CY + 34}" text-anchor="middle" '
               f'font-family="Sarabun,Noto Sans Thai,sans-serif" font-size="14" fill="#9B8B78">'
               f'{len(fests)} รายการ · มดแดง</text>')
    out.append(f'<text x="{CX}" y="{CY + 58}" text-anchor="middle" '
               f'font-family="Sarabun,Noto Sans Thai,sans-serif" font-size="12.5" fill="{day_color}">'
               f'วันนี้ {today.day} {MONTH_ABBR_TH[today.month]} {today.year + 543}</text>')
    out.append('</svg>')
    return "".join(out)


def _x(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# --------------------------------------------------------------- event link
_WORD = re.compile(r"[^\wก-๙]+", re.UNICODE)


def _norm(s):
    return _WORD.sub(" ", (s or "").lower()).strip()


def announced_dates():
    """Confirmed dates from importers/harvest_festivals.py, keyed by festival id.

    Only rows the harvester was willing to call `announced` — a canon festival
    matched, a date parsed, from an official source, in a plausible month, in
    the future, and out of a headline that was announcing rather than
    reporting. Everything else it found is held as a candidate and never
    reaches a page.
    """
    p = ROOT / "data" / "festival_dates.json"
    if not p.exists():
        return {}
    out = {}
    for r in json.loads(p.read_text()).get("rows", []):
        if r.get("status") != "announced" or not r.get("festival_id"):
            continue
        out.setdefault(r["festival_id"], []).append(r)
    for rows in out.values():
        rows.sort(key=lambda r: r["date_start"])
    return out


def _date_range_text(r, g):
    a, b = r["date_start"], r["date_end"]
    da = datetime.date.fromisoformat(a)
    db = datetime.date.fromisoformat(b)
    th = f'{da.day} {g["MONTH_TH"][da.month]} {da.year + 543}'
    en = f'{da.day} {g["MONTH_EN"][da.month]} {da.year}'
    if b != a:
        th += f' – {db.day} {g["MONTH_TH"][db.month]} {db.year + 543}'
        en += f' – {db.day} {g["MONTH_EN"][db.month]} {db.year}'
    return th, en


def instances_of(f, events):
    """Dated instances of a festival, from the crawl.

    Strict on purpose, the same way match_venue is: a festival page that claims
    a wrong date is worse than one that says the dates for this year are not
    announced yet. Only a full name match counts.
    """
    keys = [_norm(f["name_th"]), _norm(f["name_en"].split("—")[0])]
    keys = [k for k in keys if len(k) >= 6]
    if not keys:
        return []
    hits = []
    for e in events:
        hay = _norm(f'{e.get("title", "")} {e.get("description", "")[:200]}')
        if any(k in hay for k in keys):
            hits.append(e)
    hits.sort(key=lambda e: e.get("start") or "")
    return hits


def venue_places(f, idx, g):
    """Festival venues resolved to catalogue records, so a wat page can carry
    the festival it hosts. Reuses build.py's strict venue matcher — the same
    rule that keeps a stranger's phone number off someone else's event."""
    out, seen = [], set()
    for v in f.get("venues") or []:
        for raw in (v.get("th"), v.get("en")):
            if not raw:
                continue
            cleaned = re.split(r"[—(/·]|,", raw)[0].strip()
            for cand in (raw, cleaned):
                r, how = g["match_venue"](cand, idx)
                if r and r["id"] not in seen:
                    seen.add(r["id"])
                    out.append(r)
                    break
    return out


# ---------------------------------------------------------------------- ICS
def festivals_ics(fests, g, year, announced=None):
    """A calendar of the recurring canon.

    Three kinds of entry, and no fourth. A fixed-date festival gets a VEVENT
    with a yearly rule. A festival whose dates an official source has actually
    announced gets a one-off VEVENT for that year. And a lunar festival whose
    date a published Thai calendar already carries — hand-checked into
    data/festival_calendar.json, one source per row — gets a one-off VEVENT
    naming that source. A festival with none of the three has no date to
    publish and does not get invented one — it simply is not in the feed.
    Said plainly in the calendar description so nobody subscribes expecting
    the feed to guess.
    """
    esc = g["_ics_esc"]
    body = []
    by_id = {f["id"]: f for f in fests}
    dated = set()
    for fid, rows in (announced or {}).items():
        for r in rows[:2]:
            dated.add((fid, int(r["date_start"][:4])))
    import answers_layer
    cal, cal_src = answers_layer.calendar_rows()
    for (fid, y), r in sorted(cal.items()):
        f = by_id.get(fid)
        # an official announcement for that festival-year outranks the
        # published-calendar row, so the feed never carries both
        if not f or y not in (year, year + 1) or (fid, y) in dated:
            continue
        start = datetime.date.fromisoformat(r["date_start"])
        end = datetime.date.fromisoformat(r["date_end"]) + datetime.timedelta(days=1)
        s = cal_src[r["source"]]
        body.append(
            "BEGIN:VEVENT\r\n"
            f"UID:lunar-{fid}-{r['date_start']}@motdang.net\r\n"
            f"DTSTAMP:{year}0101T000000Z\r\n"
            f"DTSTART;VALUE=DATE:{start:%Y%m%d}\r\n"
            f"DTEND;VALUE=DATE:{end:%Y%m%d}\r\n"
            f"SUMMARY:{esc(f['name_th'] + ' · ' + f['name_en'])}\r\n"
            f"DESCRIPTION:{esc('Published Thai lunar-calendar date, checked against ' + s['name_en'] + '. ' + s['url'])}\r\n"
            f"URL:{esc(g['BASE'] + 'festivals/' + fid + '.html')}\r\n"
            "END:VEVENT\r\n")
    for fid, rows in (announced or {}).items():
        f = by_id.get(fid)
        if not f:
            continue
        for i, r in enumerate(rows[:2]):
            start = datetime.date.fromisoformat(r["date_start"])
            end = datetime.date.fromisoformat(r["date_end"]) + datetime.timedelta(days=1)
            body.append(
                "BEGIN:VEVENT\r\n"
                f"UID:announced-{fid}-{r['date_start']}-{i}@motdang.net\r\n"
                f"DTSTAMP:{year}0101T000000Z\r\n"
                f"DTSTART;VALUE=DATE:{start:%Y%m%d}\r\n"
                f"DTEND;VALUE=DATE:{end:%Y%m%d}\r\n"
                f"SUMMARY:{esc(f['name_th'] + ' · ' + f['name_en'])}\r\n"
                f"DESCRIPTION:{esc('Dates announced by ' + r['source_name_en'] + '. ' + r['source_url'])}\r\n"
                f"URL:{esc(g['BASE'] + 'festivals/' + fid + '.html')}\r\n"
                "END:VEVENT\r\n")
    for f in fests:
        if f.get("timing_type") != "fixed":
            continue
        # "13–15 เมษายน" must yield the 13th, not the 15th — hence the optional
        # range group, so the match starts at the first day of the span.
        months_th = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                     "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
        m = re.search(r"(\d{1,2})(?:\s*[–—-]\s*\d{1,2})?\s+(" + "|".join(months_th) + ")",
                      f["window_th"])
        if not m:
            continue  # "usually the third weekend of January" is not a date
        day, mon = int(m.group(1)), months_th.index(m.group(2)) + 1
        days = f.get("duration_days") or 1
        start = datetime.date(year, mon, day)
        end = start + datetime.timedelta(days=days)
        body.append(
            "BEGIN:VEVENT\r\n"
            f"UID:festival-{f['id']}@motdang.net\r\n"
            f"DTSTAMP:{year}0101T000000Z\r\n"
            f"DTSTART;VALUE=DATE:{start:%Y%m%d}\r\n"
            f"DTEND;VALUE=DATE:{end:%Y%m%d}\r\n"
            "RRULE:FREQ=YEARLY\r\n"
            f"SUMMARY:{esc(f['name_th'] + ' · ' + f['name_en'])}\r\n"
            f"DESCRIPTION:{esc(f['blurb_en'][:350])}\r\n"
            f"URL:{esc(g['BASE'] + 'festivals/' + f['id'] + '.html')}\r\n"
            "END:VEVENT\r\n")
    name = "มดแดง — เทศกาลที่มีวันแน่นอน / Mot Dang festivals with dates"
    desc = ("Three kinds of entry. Recurring festivals with a fixed Gregorian date, "
            "as yearly rules. Festivals whose dates an official source has "
            "actually announced, as one-off events carrying the announcing body in "
            "the description. And lunar festivals whose dates a published Thai "
            "calendar already carries, as one-off events naming that calendar. "
            "Anything else is deliberately absent: it has a date rule, not a date. "
            "The rules themselves are at https://motdang.net/festivals.html")
    return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Mot Dang//motdang.net//EN\r\n"
            f"CALSCALE:GREGORIAN\r\nMETHOD:PUBLISH\r\nX-WR-CALNAME:{esc(name)}\r\n"
            "X-WR-TIMEZONE:Asia/Bangkok\r\n"
            f"X-WR-CALDESC:{esc(desc)}\r\n"
            + "".join(body) + "END:VCALENDAR\r\n")


# ------------------------------------------------------------------- styles
CSS = """
/* festivals layer — loaded only by the festival pages, so the main
   stylesheet stays the size it is. */
.wheelwrap{margin:1rem 0 .4rem;text-align:center}
.wheelwrap svg{max-width:100%;height:auto;border:1px solid var(--soft);border-radius:1rem;background:#fff}
.wheelkey{display:flex;flex-wrap:wrap;gap:.5rem .95rem;justify-content:center;margin:.5rem 0 1.1rem;
font-size:.84rem;color:var(--ink)}
.wheelkey span{display:inline-flex;align-items:center;gap:.35rem}
.wheelkey i{width:.85rem;height:.85rem;border-radius:.3rem;display:inline-block}
.comingup{border:1px solid var(--soft);border-left:5px solid var(--day);border-radius:.8rem;
background:#fff;padding:.75rem 1rem;margin:1rem 0}
.comingup h2{margin:.1rem 0 .5rem;font-size:1.05rem}
.comingup ul{margin:.2rem 0;padding-left:1.1rem}
.comingup li{margin:.2rem 0}
.comingup .cuwhen{color:var(--mute);font-size:.85rem}
.festhead{border-bottom:3px double var(--ant);padding-bottom:.5rem;margin-bottom:.8rem}
.festmeta{display:flex;flex-wrap:wrap;gap:.4rem;margin:.5rem 0 .9rem}
.festmeta span{background:var(--soft);border-radius:.5rem;padding:.15rem .55rem;font-size:.82rem}
.festbody{max-width:44rem}
.festbody h2{font-size:1.08rem;margin:1.3rem 0 .35rem}
.merit{background:#fff;border:1px solid var(--soft);border-left:5px solid #B8912E;
border-radius:.7rem;padding:.7rem 1rem;margin:.7rem 0}
.verify{background:#FFF6E9;border:1px solid #E4C98F;border-radius:.7rem;padding:.65rem 1rem;
margin:.7rem 0;font-size:.9rem}
.venuelist{list-style:none;padding:0;margin:.4rem 0}
.venuelist li{padding:.3rem 0;border-bottom:1px dashed var(--soft)}
.instances{margin:.5rem 0}
.festnav{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.4rem 0 .6rem}
.festnav a{background:#fff;border:1px solid var(--soft);border-radius:.6rem;padding:.3rem .7rem;
text-decoration:none;font-size:.88rem}
.festhere{margin:1.2rem 0;padding:.8rem 1rem;background:#fff;border:1px solid var(--soft);
border-radius:.8rem}
.festhere h2{margin:.1rem 0 .5rem;font-size:1.02rem}
.festhere ul{margin:.2rem 0;padding-left:1.1rem}
"""


# -------------------------------------------------------------------- pages
def _prov_label(f, g):
    return g["FEST_PROV_LABEL"][f["province"]]


def festival_ld(f, g, places):
    """schema.org for a recurring festival: a Festival with an eventSchedule,
    not an Event with a made-up date. Google reads Event markup directly, and
    the honest shape of this thing is 'happens every year, roughly then'."""
    sched = {"@type": "Schedule", "repeatFrequency": "P1Y",
             "byMonth": (f.get("months") or [f["month"]]),
             "scheduleTimezone": "Asia/Bangkok",
             "description": f["rule_en"]}
    if f.get("duration_days"):
        sched["duration"] = f"P{f['duration_days']}D"
    doc = {
        "@context": "https://schema.org", "@type": "Festival",
        "name": f["name_en"], "alternateName": f["name_th"],
        "description": f["blurb_en"],
        "url": g["BASE"] + f"festivals/{f['id']}.html",
        "eventSchedule": sched,
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "isAccessibleForFree": True,
        "inLanguage": ["th", "en"],
    }
    locs = [{"@type": "Place", "name": v["en"],
             "address": {"@type": "PostalAddress",
                         "addressRegion": _prov_label(f, g)[1],
                         "addressCountry": "TH"}}
            for v in (f.get("venues") or [])]
    for r in places:
        if r.get("lat") is not None:
            locs.append({"@type": "Place", "name": g["name_of"](r),
                         "geo": {"@type": "GeoCoordinates",
                                 "latitude": r["lat"], "longitude": r["lng"]}})
    if locs:
        doc["location"] = locs if len(locs) > 1 else locs[0]
    return f'<script type="application/ld+json">{json.dumps(doc, ensure_ascii=False)}</script>'


def build_festival_page(f, g, events, idx, prov_of, neighbours):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    prov_th, prov_en = _prov_label(f, g)
    icon = g["FEST_TIMING_ICON"].get(f["timing_type"], "📅")
    places = venue_places(f, idx, g)
    inst = instances_of(f, events)

    meta = [f'<span>{icon} {bi(f["window_th"], f["window_en"])}</span>',
            f'<span>📍 {bi(prov_th, prov_en)}</span>']
    if f.get("duration_days"):
        dur = bi("ราว {} วัน".format(f["duration_days"]),
                 "about {} days".format(f["duration_days"]))
        meta.append(f'<span>⏳ {dur}</span>')
    for t in (f.get("tags") or [])[:4]:
        meta.append(f'<span>#{esc(t)}</span>')

    parts = [f'<div class="festhead"><h1>{bi(f["name_th"], f["name_en"])}</h1>'
             f'<div class="festmeta">{"".join(meta)}</div></div>',
             f'<div class="festbody"><p>{bi(f["blurb_th"], f["blurb_en"])}</p>']

    # Hand-checked published lunar dates (data/festival_calendar.json via
    # answers_layer) — the rule stays first, then the dates the published
    # calendars already put under that rule, each with its source. A broken
    # calendar file fails the build here on purpose rather than quietly
    # dropping dates from 33 pages.
    import answers_layer
    _cal, _cal_src = answers_layer.calendar_rows()
    _today = datetime.date.fromisoformat(g["BUILD_DATE"])
    cal_rows = [(_cal[(f["id"], y)], _cal_src[_cal[(f["id"], y)]["source"]])
                for y in (_today.year, _today.year + 1)
                if (f["id"], y) in _cal]

    parts.append(f'<h2>{bi("วันไหน", "When it falls")}</h2>'
                 f'<p>{bi(f["rule_th"], f["rule_en"])}</p>')
    if cal_rows:
        lis = []
        for r, s in cal_rows:
            th, en = _date_range_text(r, g)
            note = (f'<br><span class="tinynote">{bi(esc(r.get("note_th", "")), esc(r.get("note_en", "")))}</span>'
                    if r.get("note_th") else "")
            lis.append(
                f'<li><b>{bi(th, en)}</b> '
                f'<span class="evwhen">🌕 {bi("ตามปฏิทินจันทรคติที่เผยแพร่แล้ว", "published lunar-calendar date")}</span> — '
                f'<a href="{att(s["url"])}" rel="noopener nofollow">{bi("ที่มา", "source")}</a>{note}</li>')
        parts.append(
            f'<ul class="instances">{"".join(lis)}</ul>'
            f'<p class="tinynote"><a href="../festival-dates.html">'
            f'{bi("ดูวันเทศกาลทุกงาน ปีนี้และปีหน้า", "All festival dates, this year and next")} →</a></p>')

    if f.get("auspicious_th"):
        parts.append(f'<h2>{bi("ความหมายและอานิสงส์", "What the day is for")}</h2>'
                     f'<p>{bi(f["auspicious_th"], f["auspicious_en"])}</p>')
    if f.get("merit_th"):
        parts.append(f'<div class="merit"><b>🙏 {bi("ไปยังไง เตรียมอะไร", "How to take part")}</b><br>'
                     f'{bi(f["merit_th"], f["merit_en"])}</div>')

    o = f.get("observance")
    if o:
        marks = []
        if o["public_holiday"]:
            marks.append(f'<span class="festmark">🏦 {bi("วันหยุดราชการ", "public holiday")}</span>')
        if o["dry_day"]:
            marks.append(f'<span class="festmark">🚫 {bi("วันงดขายสุรา", "no alcohol sales")}</span>')
        parts.append(f'<h2>{bi("วันนี้อะไรปิด", "What is shut")}</h2>'
                     f'<div class="festplan">{"".join(marks)}'
                     f'<span class="festplannote">{bi(o["note_th"], o["note_en"])}</span></div>')

    if f.get("venues"):
        rows = []
        pmap = {g["name_of"](r): r for r in places}
        for v in f["venues"]:
            link = ""
            for nm, r in pmap.items():
                if nm and (nm in v.get("th", "") or nm in v.get("en", "")):
                    pv = prov_of.get(r["id"])
                    if pv:
                        link = (f' — <a href="../{pv}/p/{g["place_slug"](r)}.html">'
                                f'{bi("ดูหน้าสถานที่", "place page")}</a>')
                    break
            rows.append(f'<li>{bi(v["th"], v.get("en", ""))}{link}</li>')
        parts.append(f'<h2>{bi("จัดที่ไหน", "Where it happens")}</h2>'
                     f'<ul class="venuelist">{"".join(rows)}</ul>')

    ann = (g.get("_ANNOUNCED") or {}).get(f["id"]) or []
    if ann:
        rows = []
        for r in ann[:3]:
            th, en = _date_range_text(r, g)
            who = bi("ประกาศโดย " + r["source_name_th"],
                     "announced by " + r["source_name_en"])
            rows.append(
                f'<li><b>{bi(th, en)}</b><br>'
                f'<span class="evwhen">{who}</span> '
                f'<a href="{att(r["source_url"])}" rel="noopener nofollow">'
                f'{bi("ดูประกาศ", "the announcement")}</a></li>')
        parts.append(f'<h2>{bi("ประกาศแล้ว", "Announced")}</h2>'
                     f'<ul class="instances announced">{"".join(rows)}</ul>')

    if inst:
        evlink = f' · <a href="../events.html">{bi("ดูหน้างาน", "events page")}</a>'
        rows = "".join(
            f'<li><b>{esc(e.get("title", ""))}</b><br>'
            f'<span class="evwhen">{g["event_when"](e)}</span>{evlink}</li>'
            for e in inst[:6])
        parts.append(f'<h2>{bi("ปีนี้มีอะไรบ้าง", "Dated instances we have")}</h2>'
                     f'<ul class="instances">{rows}</ul>')
    elif not ann and not cal_rows:
        nodate = bi(
            "ยังไม่มีวันที่ยืนยันของปีนี้ในระบบ — หน้านี้บอกกฎของวัน ไม่ใช่วันที่เดาเอา "
            "ถ้ารู้วันแล้วบอกมดแดงได้ที่หน้าลงงาน",
            "No confirmed dates for this year are in the system yet. This page gives the rule, "
            "not a guessed date — if you know the dates, tell us on the listing page.")
        parts.append(
            f'<h2>{bi("ปีนี้วันไหน", "This year’s dates")}</h2>'
            f'<p class="tinynote">{nodate}'
            f' · <a href="../list-your-event.html">{bi("ลงวันงาน", "send us the dates")}</a></p>')

    if f.get("verify_th"):
        parts.append(f'<div class="verify">⚠️ {bi(f["verify_th"], f["verify_en"])}</div>')

    conf = f.get("confidence")
    src_th = ("ที่มาของหน้านี้: ความรู้ทั่วไป ไม่ใช่การสำรวจภาคสนาม "
              + ("รายการนี้ยังรอการยืนยันจากแหล่งทางการหรือคนในพื้นที่" if conf == "needs-verification"
                 else "ชื่อและลักษณะงานเชื่อถือได้ ส่วนวันที่ให้ดูประกาศของปีนั้น ๆ"))
    src_en = ("Where this comes from: general knowledge, not a field crawl. "
              + ("This entry is still waiting on confirmation from an official source or someone on the ground."
                 if conf == "needs-verification"
                 else "The name and character of the festival are solid; for dates, follow that year's announcement."))
    parts.append(f'<p class="myhint">{bi(src_th, src_en)}</p></div>')

    prev_f, next_f = neighbours
    nav = []
    if prev_f:
        nav.append(f'<a href="{prev_f["id"]}.html">← {bi(prev_f["name_th"], prev_f["name_en"])}</a>')
    nav.append(f'<a href="../festivals.html">🎉 {bi("ปฏิทินทั้งปี", "The whole year")}</a>')
    if next_f:
        nav.append(f'<a href="{next_f["id"]}.html">{bi(next_f["name_th"], next_f["name_en"])} →</a>')
    parts.append(f'<div class="festnav">{"".join(nav)}</div>')
    parts.append(g["share_block"](g["BASE"] + f'festivals/{f["id"]}.html',
                                  f'{f["name_th"]} · {f["name_en"]} — มดแดง'))

    crumbs = (f'<a href="../index.html">มดแดง</a> › '
              f'<a href="../festivals.html">{bi("เทศกาล-ฤดูกาล", "Festivals")}</a> › '
              f'{bi(f["name_th"], f["name_en"])}')
    head = (f'<link rel="stylesheet" href="../festivals.css">'
            + festival_ld(f, g, places))
    return g["page"](f'{f["name_th"]} · {f["name_en"]}', "".join(parts), depth=1,
                     crumbs=crumbs, path=f'festivals/{f["id"]}.html',
                     desc=f["blurb_th"][:180], extra_head=head)


def coming_up(fests, today, depth=0, g=None, limit=5):
    """The strip that makes the canon useful on any given day: what is on this
    month and next, in the order the year actually arrives."""
    bi = g["bi"]
    def dist(f):
        best = 99
        for m in (f.get("months") or [f["month"]]):
            best = min(best, (m - today.month) % 12)
        return best
    soon = sorted([f for f in fests if dist(f) <= 1], key=lambda f: (dist(f), f["month"]))
    if not soon:
        return ""
    r = "../" * depth
    ann_all = g.get("_ANNOUNCED") or {}
    rows = []
    for f in soon[:limit]:
        when = bi("เดือนนี้", "this month") if dist(f) == 0 else bi("เดือนหน้า", "next month")
        ann = ann_all.get(f["id"])
        if ann:
            th, en = _date_range_text(ann[0], g)
            detail = bi("📌 " + th + " (ประกาศแล้ว)", "📌 " + en + " (announced)")
        else:
            detail = f'{when} · {bi(f["window_th"], f["window_en"])}'
        rows.append(f'<li><a href="{r}festivals/{f["id"]}.html">{bi(f["name_th"], f["name_en"])}</a> '
                    f'<span class="cuwhen">— {detail}</span></li>')
    more = (f'<p class="tinynote"><a href="{r}festivals.html">'
            f'{bi("ดูปฏิทินเทศกาลทั้งปี", "See the whole festival year")} →</a></p>')
    return (f'<div class="comingup"><h2>🎉 {bi("ใกล้ถึงแล้ว", "Coming up")}</h2>'
            f'<ul>{"".join(rows)}</ul>{more}</div>')


def season_banner(today, g, depth=0):
    """Standing seasonal prompts — the ones a directory with 300 wats in it can
    make and a listings site cannot.

    Kathina is the sharp one: for the month after Ok Phansa a wat may still be
    waiting for a host, and the small out-of-town wats are the ones nobody has
    spoken for. That is merit matchmaking, and it needs exactly what this site
    already has — every wat, by district, with a phone number.
    """
    bi = g["bi"]
    r = "../" * depth
    if today.month in (10, 11):
        text = bi("หนึ่งเดือนหลังออกพรรษาคือช่วงทอดกฐิน วัดหนึ่งรับกฐินได้ปีละครั้งเดียว "
                  "และวัดเล็ก ๆ นอกเมืองมักยังไม่มีเจ้าภาพจอง — ลองเปิดดูวัดตามอำเภอแล้วโทรถามได้เลย",
                  "For the month after Ok Phansa, a wat may host a kathina — once a year, one host "
                  "only, and the small wats outside town are usually the ones still unspoken for. "
                  "Browse the wats by district and ring one to ask.")
        return (f'<div class="comingup"><h2>🧡 {bi("ฤดูกฐิน", "Kathina season")}</h2>'
                f'<p>{text}</p>'
                f'<p class="tinynote"><a href="{r}cm/wat/index.html">'
                f'{bi("วัดในเชียงใหม่", "Wats in Chiang Mai")}</a> · '
                f'<a href="{r}cr/wat/index.html">{bi("วัดในเชียงราย", "Wats in Chiang Rai")}</a> · '
                f'<a href="{r}festivals/ok-phansa.html">{bi("ออกพรรษาคืออะไร", "what Ok Phansa is")}</a></p></div>')
    if today.month in (5, 6):
        text = bi("ปลายพฤษภาคมถึงต้นมิถุนายนคือช่วงบูชาเสาอินทขีลที่วัดเจดีย์หลวง "
                  "เป็นพิธีฝากดวงเมืองเชียงใหม่ไว้อีกหนึ่งปี ใครก็ไปใส่ขันดอกได้",
                  "Late May into early June is the Inthakhin flower offering at Wat Chedi Luang — "
                  "Chiang Mai putting its own fortune in the city pillar's keeping for another "
                  "year. Anyone may take part.")
        return (f'<div class="comingup"><h2>🌸 {bi("ช่วงใส่ขันดอก", "Khan dok season")}</h2>'
                f'<p>{text}</p>'
                f'<p class="tinynote"><a href="{r}festivals/inthakhin.html">'
                f'{bi("อ่านเรื่องอินทขีล", "About Inthakhin")}</a></p></div>')
    return ""


def festivals_here(place_id, fests_by_place, g, depth=2):
    """The payoff of the venue matching: a wat page that says what it hosts."""
    mine = fests_by_place.get(place_id) or []
    if not mine:
        return ""
    bi = g["bi"]
    r = "../" * depth
    rows = "".join(
        f'<li><a href="{r}festivals/{f["id"]}.html">{bi(f["name_th"], f["name_en"])}</a> — '
        f'<span class="evwhen">{bi(f["window_th"], f["window_en"])}</span></li>' for f in mine)
    caveat = bi("วันที่เป็นช่วงตามธรรมเนียม ไม่ใช่วันยืนยันของปีนี้ ถามที่วัดหรือผู้จัดอีกครั้ง",
                "These are the customary windows, not confirmed dates for this year — "
                "check with the wat or the organiser")
    return (f'<div class="festhere"><h2>🎉 {bi("งานประจำปีที่นี่", "The festival year here")}</h2>'
            f'<ul>{rows}</ul>'
            f'<p class="tinynote">{caveat}</p></div>')


# --------------------------------------------------------------------- hub
def build_hub(fests, g, today, wheel):
    bi, esc = g["bi"], g["esc"]
    key = "".join(f'<span><i style="background:{c}"></i>{bi(th, en)}</span>'
                  for _, c, th, en in FAMILY)
    key += (f'<span><i style="background:#B8912E;width:.25rem"></i>'
            f'{bi("ขีดเล็กรอบขอบ = วันพระ (โดยประมาณ)", "rim ticks = wan phra, approximate")}</span>'
            f'<span><i style="background:repeating-linear-gradient(90deg,#9B8B78 0 4px,transparent 4px 7px)"></i>'
            f'{bi("เส้นประ = รอการยืนยัน", "dashed = awaiting verification")}</span>')
    tiles = (f'<div class="tilerow">'
             f'<div class="tile"><b>{len(fests)}</b><span>{bi("เทศกาล-ฤดูกาล", "festivals & seasons")}</span></div>'
             f'<div class="tile"><b>12</b><span>{bi("เดือนตลอดปี", "months covered")}</span></div>'
             f'<div class="tile"><b>{sum(1 for f in fests if f.get("merit_th"))}</b>'
             f'<span>{bi("มีวิธีร่วมงาน", "with how-to-take-part")}</span></div>'
             f'</div>')
    intro_th = ("ปฏิทินเทศกาลและฤดูกาลน่าไปของเชียงใหม่-เชียงราย ตลอดปี ทั้งงานบุญ ประเพณีล้านนา "
                "ประเพณีชาติพันธุ์บนดอย และฤดูกาลธรรมชาติ — วงล้อข้างล่างคือทั้งปีในภาพเดียว กดที่เส้นไหนก็เข้าไปอ่านงานนั้นได้")
    intro_en = ("A year-round calendar of Chiang Mai and Chiang Rai's recurring festivals, Lanna and "
                "highland traditions, and natural seasons. The wheel below is the whole year in one "
                "drawing — every mark is a link to that festival.")
    caveat_th = ("หมายเหตุความซื่อตรง: รายการนี้มาจากความรู้ทั่วไป ไม่ใช่ผลการสำรวจภาคสนาม งานที่ผูกกับปฏิทินจันทรคติ "
                 "ให้ช่วงเดือนโดยประมาณ ไม่ใช่วันที่แน่นอน และรายการที่ขีดเป็นเส้นประในวงล้อคือรายการที่ยังรอการยืนยัน")
    caveat_en = ("Where this comes from: general knowledge, not a field crawl. Lunar entries give a "
                 "typical month window, never an asserted day, and a dashed mark on the wheel means the "
                 "entry is still waiting on verification.")
    sections = []
    for m in range(1, 13):
        items = [f for f in fests if f["month"] == m]
        if not items:
            continue
        cards = "".join(
            g["festival_card"](f).replace(
                f'<h3>{bi(f["name_th"], f["name_en"])}</h3>',
                f'<h3><a href="festivals/{f["id"]}.html">{bi(f["name_th"], f["name_en"])}</a></h3>')
            for f in items)
        sections.append(f'<h2 id="m{m}">{bi(g["MONTH_TH"][m], g["MONTH_EN"][m])}</h2>'
                        f'<div class="festgrid">{cards}</div>')
    monthnav = " · ".join(f'<a href="#m{m}">{g["MONTH_TH"][m]}</a>' for m in range(1, 13))
    body = (f'<h1>🎉 {bi("เทศกาล-ฤดูกาล", "Festivals & Seasons")}</h1>'
            f'<p>{bi(intro_th, intro_en)}</p>{tiles}'
            f'{season_banner(today, g, depth=0)}'
            f'{coming_up(fests, today, depth=0, g=g)}'
            f'<div class="wheelwrap">{wheel}</div>'
            f'<div class="wheelkey">{key}</div>'
            f'<p class="tinynote">📅 <a href="festival-dates.html">'
            f'{bi("วันเทศกาลปีนี้และปีหน้า — ทุกงาน หน้าเดียว", "Festival dates for this year and next, on one page")}</a> · '
            f'🗓 <a href="festivals.ics">festivals.ics</a> — '
            f'{bi("ปฏิทินเฉพาะงานที่มีวันที่แน่นอน (สมัครรับในปฏิทินได้เลย) · งานตามจันทรคติอยู่ใน events.ics เมื่อยืนยันวันแล้ว", "the fixed-date festivals as a subscribable calendar; lunar and announced ones join events.ics once their dates are confirmed")} · '
            f'<a href="data/festivals.json">festivals.json</a> · '
            f'<a href="festival-wheel.svg">{bi("ดาวน์โหลดวงล้อ", "download the wheel")}</a></p>'
            f'<p class="myhint">{bi(caveat_th, caveat_en)}</p>'
            f'<p class="tinynote">{monthnav}</p>'
            f'{"".join(sections)}'
            f'{g["share_block"](g["BASE"] + "festivals.html", "เทศกาล-ฤดูกาล มดแดง · Mot Dang festivals & seasons")}')
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "Chiang Mai & Chiang Rai festivals and seasonal highlights",
          "numberOfItems": len(fests),
          "itemListElement": [
              {"@type": "ListItem", "position": i + 1,
               "url": g["BASE"] + f'festivals/{f["id"]}.html',
               "name": f["name_en"]} for i, f in enumerate(fests)]}
    head = ('<link rel="stylesheet" href="festivals.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    return g["page"]("เทศกาล-ฤดูกาล เชียงใหม่-เชียงราย", body, depth=0,
                     path="festivals.html", desc=intro_th, extra_head=head)


# ------------------------------------------------------------------- driver
def emit(g, events, data):
    """Write the whole layer into docs/. Called from build.py after
    build_festivals_page(); rewrites festivals.html on top of it so the hub and
    the detail pages are generated by the same code."""
    DOCS = g["DOCS"]
    fests = g["FESTIVALS"]
    today = datetime.date.fromisoformat(g["BUILD_DATE"])
    fdir = DOCS / "festivals"
    fdir.mkdir(exist_ok=True)
    (DOCS / "festivals.css").write_text(CSS)

    idx = g["_venue_index"](data)
    prov_of = {r["id"]: p["key"] for p in g["PROVINCES"] for r in data[p["key"]]}
    records_by_id = {r["id"]: r for p in g["PROVINCES"] for r in data[p["key"]]}
    # Confirmed dates from the announcement harvester. Kept in g so the page
    # builders read the same dict the hub and the calendar do.
    g["_ANNOUNCED"] = ann = announced_dates()

    wheel = wheel_svg(fests, today, g["BASE"])
    (DOCS / "festival-wheel.svg").write_text(wheel)
    (DOCS / "festivals.html").write_text(build_hub(fests, g, today, wheel))
    (DOCS / "festivals.ics").write_text(festivals_ics(fests, g, today.year, ann))
    fd = ROOT / "data" / "festival_dates.json"
    if fd.exists():
        (DOCS / "data" / "festival_dates.json").write_text(fd.read_text())

    fests_by_place = {}
    for i, f in enumerate(fests):
        prev_f = fests[i - 1] if i else None
        next_f = fests[i + 1] if i + 1 < len(fests) else None
        for r in venue_places(f, idx, g):
            fests_by_place.setdefault(r["id"], []).append(f)
        (fdir / f'{f["id"]}.html').write_text(
            build_festival_page(f, g, events, idx, prov_of, (prev_f, next_f)))

    # The band on a place page. Written by post-processing rather than by
    # threading a new argument through build.py's record renderer — this layer
    # stays one file, and the place pages keep exactly one owner.
    touched = 0
    for pid, mine in fests_by_place.items():
        pv = prov_of.get(pid)
        if not pv:
            continue
        rec = records_by_id.get(pid)
        if not rec:
            continue
        path = DOCS / pv / "p" / f'{g["place_slug"](rec)}.html'
        if not path.exists():
            continue
        html = path.read_text()
        band = festivals_here(pid, fests_by_place, g, depth=2)
        if band and "<footer>" in html:
            html = html.replace('</head>', '<link rel="stylesheet" href="../../festivals.css"></head>', 1)
            path.write_text(html.replace("<footer>", band + "<footer>", 1))
            touched += 1

    # The homepage strip goes into the sidebar slot build.py leaves for it.
    # The anchor is a marker comment rather than a Thai heading: a heading can
    # be reworded or restyled by anyone touching the homepage and this would
    # silently stop injecting. A marker only disappears on purpose.
    home = DOCS / "index.html"
    if home.exists():
        html = home.read_text()
        anchor = "<!--MD:COMINGUP-->"
        if anchor in html:
            strip = coming_up(fests, today, depth=0, g=g, limit=3)
            html = html.replace('</head>', '<link rel="stylesheet" href="festivals.css"></head>', 1)
            html = html.replace(
                anchor, f'<div class="sidecard gold comingupcard">{strip}</div>' if strip else "", 1)
            home.write_text(html)
        else:
            print("  ! homepage has no <!--MD:COMINGUP--> slot — strip not injected")

    return {"festivals": len(fests), "place_bands": touched,
            "announced": sum(len(v) for v in ann.values()),
            "with_instances": sum(1 for f in fests if instances_of(f, events))}


def main(wheel_only=False):
    """Run the layer against an already-built docs/.

    Useful two ways: --wheel iterates on the drawing without a 90-second site
    build, and the bare form re-lays the whole layer over an existing docs/ if
    build.py was run without the hook.
    """
    if wheel_only:
        fests = json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]
        out = ROOT / "docs" / "festival-wheel.svg"
        out.parent.mkdir(exist_ok=True)
        out.write_text(wheel_svg(fests, datetime.date.today(), "https://motdang.net/"))
        print(f"wrote {out} — {len(fests)} festivals")
        return
    import sys
    sys.path.insert(0, str(ROOT))
    import build  # importing does not build: build() runs under __main__ only
    if not (build.DOCS / "index.html").exists():
        raise SystemExit("docs/ is not built yet — run python3 build.py first")
    data = build.load()
    print(emit(vars(build), build.enrich_events(data, build.PHOTO_FILES), data))


if __name__ == "__main__":
    import sys
    main(wheel_only="--wheel" in sys.argv)
