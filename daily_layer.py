"""daily_layer.py — ของวันนี้, the band across the top of the front page.

WHAT IT IS FOR
--------------
Nan, 2026-09-16: content above everything else on the front page whose one job
is to delight — "magical, helpful, and useful", changing daily as needed,
harmonious and fresh, "with visuals and tools preferred over words", able to be
"strongly geofenced", carrying "translated/pronunciation helper" readings and
the city's own trade slang throughout, and leaning on pictures and on data
drawn as pictures rather than on sentences.

WHAT IT IS MADE OF
------------------
Each card is something this repo already computes, drawn where a person will
meet it in the morning rather than three pages in:

  ภาพ    one of the 145 pictures Nan picked, licensed and shipped in
         docs/site/ — seven of them baked here, one shown a day.
  วัน    the day's สีประจำวัน, its ค่ำ and whether it is วันพระ, from
         data/fortune.json and data/sky.json.
  คำ     a trade word out of data/trade_lexicon.json with its RTGS reading,
         its English gloss and how many places in the catalogue carry it —
         the pronunciation helper asked for, built out of the city's own
         working vocabulary rather than a phrasebook. Each gloss in that file
         carries a `glossVia` naming where it came from.
  เปิด   how many places in this city are open at this minute, off the 4,359
         records that carry their own hours, with the day's curve behind it.
  ฝุ่น    today's PM2.5 in its PCD band, and the door to the clean-air rooms.
  เดิน   the plan page's own demo: one leg as the crow flies, on foot and on
         a scooter, which are three different numbers.
  ห้องน้ำ the nearest-toilet finder, which has an app of its own to install.
  พาไป   the dice, scoped to the city the reader last chose.

WHERE THE DATA COMES FROM
-------------------------
The whole payload is one inline <script type="application/json"> of a few
kilobytes, so the band makes no request of its own: 45 days of almanac, seven pictures, fourteen words and both cities'
forecasts. The reader's own clock picks today's, so the band is right every
morning whether or not a build ran — and a day past the end of the window
removes its card rather than showing a stale one with today's date on it.
data/fortune.json is 1.36 MB and is deliberately not fetched on this page; that
is the reason the almanac is baked small here instead of read from it.

The geofencing reads `md-city` in localStorage — the city the reader last
tapped — and `md-origin` where MDLOC already holds one. It calls no geolocation
API, which is the same shape map.js has: a permission dialog at the top of the
front page would be a worse opening than any card here is a better one.
"""

import datetime
import json
import math

# The reading and the gloss ride in `title` and `aria-label` rather than on the
# page. Nan, 2026-09-02: "a lot of shit that is printed on the page should
# actually be a tool tip at most" — and a band whose job is to delight cannot
# also be a glossary. The word-of-the-day card is the exception and prints all
# three, because the printing IS the card.
WINDOW_DAYS = 45
PIC_DAYS = 7
WORD_DAYS = 14


def _rd(text):
    """RTGS for a Thai string, from the site's own romaniser. Never typed."""  # stylecheck: allow — code docstring
    try:
        import translit
        return translit.reading(text)
    except Exception:
        return ""


def helper(th, en, reading=None):
    """ไทย · RTGS · English — the three slots that make a word sayable and
    then knowable, for the title of anything on this band that shows Thai."""
    rd = reading if reading is not None else _rd(th)
    return " · ".join(x for x in (th, rd, en) if x)


def almanac(fortune_days, sky_days, start, n=WINDOW_DAYS):
    """The small per-day table. Only what the disc and its line need: the
    colour, the day, the ค่ำ, and whether it is วันพระ.

    The window opens the day BEFORE the build's own, because the reader's
    clock is the one that picks the entry and a reader west of here is on
    yesterday's date while the build stamped today's. One day of slack costs
    about a hundred bytes and is the difference between a card and no card.
    """
    try:
        start = (datetime.date.fromisoformat(str(start)[:10])
                 - datetime.timedelta(days=1)).isoformat()
    except ValueError:
        pass
    out, keys = {}, sorted(fortune_days)
    for iso in keys:
        if iso < start or len(out) >= n:
            continue
        t = (fortune_days[iso] or {}).get("thai") or {}
        moon = ((sky_days.get(iso) or {}).get("moon")) or {}
        if not t.get("hex"):
            continue
        out[iso] = {"hex": t["hex"], "th": t.get("th", ""), "en": t.get("en", ""),
                    "cth": t.get("colour_th", ""), "cen": t.get("colour_en", ""),
                    "mth": moon.get("thai_label_th", ""),
                    "men": moon.get("thai_label_en", ""),
                    "phra": 1 if moon.get("wan_phra") else 0}
    return out


def words(lexicon, n=WORD_DAYS, floor=6):
    """The words of the fortnight, out of the trade lexicon.

    Commonest first and then spread by stride rather than simply taking the top
    fourteen: the head of that list is six ways of saying motorcycle repair,
    and a fortnight of the same trade is not a word of the day. `floor` keeps
    a word off the card unless the catalogue can actually show the reader
    places that carry it — a word with two doors behind it is a dictionary
    entry, not a shelf.
    """
    def thai_enough(word):
        # The lexicon is mined from shopfronts and a shopfront can be a
        # number: "50" is in there, with the gloss "50 (as written on the
        # sign)". A correct record; not a word of the day.
        return sum(1 for c in word if "\u0e01" <= c <= "\u0e5b") >= 2

    rows = [(k, v) for k, v in (lexicon.get("tags") or {}).items()
            if v.get("gloss") and v.get("reading") and (v.get("n") or 0) >= floor
            and not v.get("suspect") and thai_enough(k)]
    rows.sort(key=lambda kv: (-(kv[1].get("n") or 0), kv[0]))
    if not rows:
        return []
    # A golden-ratio stride over the eligible list, the same walk the katha
    # shuffle takes over its corpus: maximally even, no clustering, and the
    # same fortnight for everybody so two readers comparing phones agree.
    # Coprime with the length, or the walk revisits a short cycle and the
    # fortnight repeats. gcd, not "does not divide evenly" — 14 and 4 share a
    # factor without either dividing the other.
    stride = max(1, int(round(len(rows) / 1.6180339887)))
    while stride > 1 and math.gcd(stride, len(rows)) != 1:
        stride -= 1
    out, seen, i = [], set(), 0
    while len(out) < n and len(seen) < len(rows):
        if i not in seen:
            seen.add(i)
            k, v = rows[i]
            out.append({"th": k, "rd": v["reading"], "en": v["gloss"],
                        "n": v.get("n") or 0})
        i = (i + stride) % len(rows)
    return out


def _now_cell(iso):
    """(weekday 0=Mon, hour) for the moment this build ran.

    The server cannot know what o'clock the page is being read at, and the
    script rewrites this cell from the reader's own clock within a frame. What
    is baked is therefore only what was true when the page was made — which is
    the build's own hour, not a fixed midday that was never true of anything.
    Monday is 0 on both sides: Python's weekday() and the JS (getDay()+6)%7.
    """
    try:
        d = datetime.date.fromisoformat(str(iso)[:10])
    except ValueError:
        return 0, datetime.datetime.now().hour
    return d.weekday(), datetime.datetime.now().hour


def _curve_svg(hours, now):
    """A day of opening hours as 24 columns, the hour the reader is in picked
    out. The scale is the day's own peak, so the shape is about this city."""
    top = max(hours) or 1
    W, H = 108.0, 26.0
    step = W / 24.0
    o = ['<svg viewBox="0 0 %.0f %.0f" aria-hidden="true">' % (W, H)]
    for i, v in enumerate(hours):
        h = max(1.2, v / top * (H - 2))
        o.append('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1"/>'
                 % ("on" if i == now else "", i * step + .6, H - h, step - 1.2, h))
    o.append("</svg>")
    return "".join(o)


def _room_svg():
    """A door, for the clean-air rooms count."""
    return ('<svg class="rm" viewBox="0 0 12 12" aria-hidden="true" width="9" height="9">'
            '<rect x="1.6" y="1" width="8.8" height="10" rx="1"/>'
            '<circle cx="8.4" cy="6.2" r=".9" fill="#fff"/></svg>')


def _crow_svg():
    return ('<svg class="pm" viewBox="0 0 12 12" aria-hidden="true" width="11" height="11">'
            '<path d="M1 9 11 3" stroke="currentColor" stroke-width="1.3" fill="none" '
            'stroke-dasharray="2 1.6" stroke-linecap="round"/></svg>')


def _walk_svg():
    return ('<svg class="pm" viewBox="0 0 12 12" aria-hidden="true" width="11" height="11">'
            '<circle cx="6.2" cy="1.9" r="1.2"/>'
            '<path d="M6.2 3.6 4.6 6.6l1.9 1.3.6 2.8M4.6 6.6 3 8.8M6.5 7.9 8.6 6.4" '
            'stroke="currentColor" stroke-width="1.2" fill="none" stroke-linecap="round" '
            'stroke-linejoin="round"/></svg>')


def _ride_svg():
    return ('<svg class="pm" viewBox="0 0 14 12" aria-hidden="true" width="13" height="11">'
            '<circle cx="2.7" cy="8.6" r="2.2" fill="none" stroke="currentColor" stroke-width="1.2"/>'
            '<circle cx="11.1" cy="8.6" r="2.2" fill="none" stroke="currentColor" stroke-width="1.2"/>'
            '<path d="M4.9 8.6h3.6l1.7-4M8.3 4.6h2.4M2.7 7 4.4 4.6h2.9" '
            'stroke="currentColor" stroke-width="1.2" fill="none" stroke-linecap="round" '
            'stroke-linejoin="round"/></svg>')


def _loo_svg():
    """The two-figure mark, drawn here rather than borrowed from the sprite:
    the sprite's i-loo is a line icon sized for a row, and this card wants a
    single solid mark that reads at a glance across a moving strip."""
    return ('<svg viewBox="0 0 34 24" aria-hidden="true" width="34" height="24">'
            '<circle cx="9" cy="4.4" r="2.6"/>'
            '<path d="M6.4 8h5.2l1.8 7h-2.1l-.5 7H7.2l-.5-7H4.6Z"/>'
            '<circle cx="25" cy="4.4" r="2.6"/>'
            '<path d="M25 8c2.4 0 3.4 1.2 3.9 3l1.2 4.4h-2l-.6-2.2-1 8.8h-3'
            'l-.3-5h-.4l-.3 5h-3l-1-8.8-.6 2.2h-2L16.1 11c.5-1.8 1.5-3 3.9-3Z"/>'
            '</svg>')


def open_curve(lamps):
    """How many places are open, by weekday and hour, per province.

    data/open_lamps.json is 684 KB — 4,359 places against 880 week-schedules —
    and the front page cannot carry it. What the front page actually wants is
    one number, the one for the hour the reader is standing in, and the shape
    of the day around it. That is 7 x 24 integers a province: about a
    kilobyte, and the reader's own clock indexes it.

    Counted at the hour's midpoint, which is what the number means: how many
    are open at half past. A place open 08:00-08:20 does not make the 08:00
    cell, and a cell is not a promise about the whole hour — the lamp pages
    are where a reader goes for one place's own times.
    """
    places = lamps.get("places") or []
    scheds = lamps.get("schedules") or []
    out = {}
    for pv in ("cm", "cr"):
        grid = [[0] * 24 for _ in range(7)]
        for rec in places:
            k = rec.get("k")
            if rec.get("p") != pv or not isinstance(k, int) or k >= len(scheds):
                continue
            spans = scheds[k] or []
            for wd in range(7):
                base = wd * 1440
                for hr in range(24):
                    mid = base + hr * 60 + 30
                    for a, b in spans:
                        if a <= mid < b:
                            grid[wd][hr] += 1
                            break
        out[pv] = grid
    return out


def air_now(places, rooms=0, keys=("cm", "cr"), ids=("chiang-mai", "chiang-rai")):
    """Today's PM2.5 per city, with the PCD band it falls in, and how many
    clean-air rooms the register holds. The number is modelled rather than
    measured at street level — the widget page says so and this card links to
    the page that does."""
    by_id = {p.get("id"): p for p in places or []}
    out = {"rooms": rooms}
    for key, pid in zip(keys, ids):
        p = by_id.get(pid)
        if not p or p.get("pm25") is None:
            continue
        b = p.get("band") or {}
        out[key] = {"pm": p["pm25"], "th": b.get("th", ""), "en": b.get("en", ""),
                    "c": b.get("colour", "#888")}
    return out


def band(*, days, pics, word_rows, rand_href, bi, att, esc, r="",
         openc=None, air=None, plan=None, places=None, today="",
         picture_credit_href="pictures.html"):
    """The band itself. Everything it shows for the build's own day is
    server-rendered, so it is whole with no script; the script swaps in the
    reader's day and the reader's city."""
    if not (days or pics or word_rows or openc or air):
        return ""
    # The build's own day for the server render, not the first key in the
    # window — the window opens a day early for readers west of here, so
    # sorted()[0] is yesterday and the card would paint yesterday's colour
    # for the moment before the script runs, and keep it with no script.
    d0 = days.get(today) or (days.get(sorted(days)[0]) if days else {}) or {}
    pic0 = pics[0] if pics else None
    w0 = word_rows[0] if word_rows else None
    openc = openc or {}
    air = air or {}
    places = places or {}
    pl0 = (places.get("cm") or [None])[0]

    cards = []

    # ---- ห้องน้ำ ---------------------------------------------------------
    # Nan, 2026-09-17: "toilet finder should be easy to find." It was one
    # tinynote at the foot of one page. It is the first card now, because on
    # the list of things a person in a strange part of this city needs in the
    # next four minutes it is at the top, and because nothing else here has an
    # app of its own to install.
    cards.append(
        '<a class="t96card loo" href="%stoilets.html" title="%s" aria-label="%s">'
        '<span class="loomark">%s</span><b>%s</b></a>'
        % (r, att(helper("ห้องน้ำใกล้ฉัน", "the nearest toilet")),
           att(bi_label(bi, "ห้องน้ำใกล้ฉัน", "the nearest toilet")),
           _loo_svg(), bi("ห้องน้ำ", "toilets")))

    # ---- the picture -----------------------------------------------------
    # OUT, 2026-09-17, when the band was re-cut to lead with the instruments.
    # It was the one card that was neither unique to this site nor a tool: a
    # photograph of the city as decoration, next to seven cards that answer
    # something. The place card below carries a photograph and a door, which
    # is the same warmth doing a job. `pics` is still baked into the payload
    # and this block is four lines from returning.
    # ---- เปิดอยู่ตอนนี้ --------------------------------------------------
    # How many places in this city are open at this minute. Nobody else here
    # can say it: it comes off 4,359 places' own opening hours, folded to
    # 7 x 24 counts (open_curve) so the front page carries a kilobyte instead
    # of 684 KB, and the reader's own clock picks the cell. The curve behind
    # the number is the day's own shape, which is the part a number alone
    # cannot say — the city wakes at eight and is still 1,400 strong at nine
    # at night.
    cm_curve = (openc.get("cm") or [])
    if cm_curve:
        wd, hr = _now_cell(today)
        cards.append(
            '<a class="t96card openc" id="tdopen" href="%smap.html" title="%s" aria-label="%s">'
            '<b id="tdopenn">%s</b>'
            '<span class="ocurve" id="tdopencurve">%s</span></a>'
            % (r, att(helper("เปิดอยู่ตอนนี้", "open right now")),
               att(bi_label(bi, "เปิดอยู่ตอนนี้", "open right now")),
               esc("{:,}".format(cm_curve[wd][hr])),
               _curve_svg(cm_curve[wd], hr)))

    # ---- ฝุ่น -------------------------------------------------------------
    # The number in the band's own ink, and the door to the one page that
    # answers what a person does about it — the clean-air rooms กรมอนามัย
    # keeps a register of, with their pins and phones checked.
    if air.get("cm"):
        a0 = air["cm"]
        cards.append(
            '<a class="t96card air" id="tdair" href="%sfoon.html" title="%s" aria-label="%s">'
            '<b id="tdairn" style="color:%s">%s<sup>µg</sup></b>'
            '<span class="aband" id="tdairband">%s</span>'
            '<span class="arooms">%s</span></a>'
            % (r, att(helper("ฝุ่น PM2.5", "PM2.5 dust")),
               att(bi_label(bi, "ฝุ่นวันนี้ และห้องปลอดฝุ่น",
                            "today’s dust, and the clean-air rooms")),
               att(a0["c"]), esc("%.0f" % a0["pm"]),
               bi(a0.get("th", ""), a0.get("en", "")),
               # The rooms line is a count and a room mark, not a sentence: at
               # 104 px "2,428 ห้องปลอดฝุ่น" wrapped and left ฝุ่น hanging on a
               # line of its own. The card's own title says what they are.
               ('%s %s' % (_room_svg(), esc("{:,}".format(air["rooms"])))
                if air.get("rooms") else "")))

    # ---- เดิน ≠ ขี่ --------------------------------------------------------
    # The same two stops measured three ways. It is the plan page's own demo
    # number, read from the sidecar make_plan_demo.py writes, so the card
    # cannot advertise a run the tool would not reproduce.
    if plan and plan.get("footM") and plan.get("rideM"):
        mx = max(plan["crowM"], plan["footM"], plan["rideM"]) or 1
        rows = (("crow", plan["crowM"]), ("foot", plan["footM"]),
                ("ride", plan["rideM"]))
        # A bar with no mark beside it is a length, not a measurement. Three
        # marks say which leg is which without spending a word: a dotted hop
        # for the crow, the walker, the scooter.
        marks = {"crow": _crow_svg(), "foot": _walk_svg(), "ride": _ride_svg()}
        bars = "".join(
            '<span class="pb">%s<i class="k-%s" style="width:%.0f%%"></i>'
            '<u>%s</u></span>' % (marks[k], k, v / mx * 100.0, esc("%d" % v))
            for k, v in rows)
        cards.append(
            '<a class="t96card plan" href="%splan.html" title="%s" aria-label="%s">'
            '<span class="pbars">%s</span></a>'
            % (r, att(helper("เดินกับขี่ ต่างกัน", "walking and riding differ")),
               att(bi_label(bi, "สองจุดเดียวกัน วัดสามแบบ",
                            "the same two stops, measured three ways")),
               bars))

    # ---- the day ---------------------------------------------------------
    if d0:
        cards.append(
            '<a class="t96card day" id="tdday" href="%swidgets.html#w-fortune" '
            'title="%s" aria-label="%s">'
            '<span class="disc" id="tddisc" style="background:%s"></span>'
            '<b id="tddayname">%s</b>'
            '<span class="kham" id="tdkham">%s</span></a>'
            % (r,
               att(helper("วันนี้", "today")),
               att(helper(d0.get("th", ""), d0.get("en", ""))),
               att(d0["hex"]), bi(d0.get("th", ""), d0.get("en", "")),
               bi(d0.get("mth", ""), d0.get("men", ""))))

    # ---- the word --------------------------------------------------------
    # The one card that prints all three slots, because the three slots ARE
    # the card: the word as it is written on the shopfront, the way to say it,
    # and what it means. The count is a door — tapping it lists the places
    # that carry the word.
    if w0:
        cards.append(
            '<a class="t96card word" id="tdword" href="%ssearch.html?tag=%s" '
            'title="%s" aria-label="%s">'
            '<b class="wth" id="tdwth" lang="th">%s</b>'
            '<span class="wrd" id="tdwrd">%s</span>'
            '<span class="wen" id="tdwen" lang="en">%s</span>'
            '<span class="wn" id="tdwn">%s</span></a>'
            % (r, att(_q(w0["th"])),
               att(helper("คำวันนี้", "the word of the day")),
               att(helper(w0["th"], w0["en"], w0["rd"])),
               esc(w0["th"]), esc(w0["rd"]), esc(w0["en"]),
               esc("%d" % w0["n"])))

    # ---- the place of the day -------------------------------------------
    # A photograph OF somewhere, which is a different promise from the picture
    # card above it: that one is the city as furniture, this one is a door with
    # a real doorway behind it. 112 places in assets/photos/ carry a
    # photograph of themselves, freely licensed and downloaded with its
    # credit; this shows one of them, in the city the reader last chose, a
    # different one every day. Strongly geofenced, as asked — and by the city
    # the reader tapped rather than by a position nobody was asked for.
    if pl0:
        cards.append(
            '<div class="t96card place">'
            '<a class="picgo" id="tdplace" href="%s%s" title="%s" aria-label="%s">'
            '<img id="tdplaceimg" src="%s%s" width="520" height="347" alt="%s" '
            'decoding="async" loading="lazy">'
            '<span class="nm" id="tdplacenm">%s</span></a>'
            '<span class="by" id="tdplaceby">%s</span></div>'
            % (r, att(pl0["href"]), att(helper(pl0.get("th") or "", pl0.get("en") or "",
                                               pl0.get("rd") or "")),
               att(helper("ที่วันนี้", "today’s place")),
               r, att(pl0["f"]), att(pl0.get("alt") or ""),
               esc(pl0.get("th") or pl0.get("en") or ""),
               esc(pl0.get("by") or "")))

    # ---- the dice --------------------------------------------------------
    # Geofenced by the city the reader last chose, and a real address with no
    # script — never a dead "#" that scrolls to the top and calls it a trip.
    cards.append(
        '<a class="t96card go" id="tdgo" href="%s%s" title="%s" aria-label="%s">'
        '<svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true" '
        'fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/>'
        '<path d="m15.5 8.5-1.8 5.2-5.2 1.8 1.8-5.2Z"/></svg></a>'
        % (r, att(rand_href), att(helper("สุ่มพาไป", "take me somewhere")),
           att(helper("สุ่มพาไป", "take me somewhere"))))

    payload = json.dumps({"days": days, "pics": pics, "words": word_rows,
                          "open": openc, "air": air, "places": places},
                         ensure_ascii=False, separators=(",", ":"))
    return ('<section class="today96" aria-label="%s"><div class="tdstrip">%s</div>'
            '<script type="application/json" id="td96">%s</script></section>'
            % (att(helper("ของวันนี้", "today")), "".join(cards), payload))


def bi_label(bi, th, en):
    return "%s · %s" % (th, en)


def _q(s):
    import urllib.parse
    return urllib.parse.quote(s)


CSS = r"""
/* ── ของวันนี้ — the band above everything (Nan, 2026-09-16) ─────────────
   One strip, scrolled sideways with a thumb on a phone and laid out in a row
   on a desk. It sits above the wordmark because that is where it was asked
   for, and it is held to one card's height so the front page is still one
   screen on a 375×812 phone. */
.today96{width:100%;margin:0}
.today96 .tdstrip{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x proximity;
 -webkit-overflow-scrolling:touch;padding:2px 0 6px;scrollbar-width:none}
.today96 .tdstrip::-webkit-scrollbar{display:none}
.today96 .t96card{flex:none;scroll-snap-align:start;position:relative;display:flex;
 flex-direction:column;align-items:center;justify-content:center;gap:3px;
 height:104px;min-width:104px;padding:8px 12px;box-sizing:border-box;
 border:1px solid var(--hair,#d8d2c4);border-radius:14px;background:#fff;
 color:var(--ink);text-decoration:none;overflow:hidden}
.today96 .t96card:focus-visible{outline:2px solid var(--ant);outline-offset:2px}
/* the picture */
.today96 .pic{width:168px;padding:0}
.today96 .pic .picgo{display:block;width:100%;height:100%}
.today96 .pic img{width:100%;height:100%;object-fit:cover;display:block}
.today96 .pic .by{position:absolute;left:0;right:0;bottom:0;padding:3px 7px;font-size:9.5px;
 color:#fff;text-decoration:none;background:linear-gradient(transparent,rgba(30,22,14,.72));
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.today96 .pic .by:hover,.today96 .pic .by:focus-visible{text-decoration:underline}
/* the place of the day */
.today96 .place{width:178px;padding:0}
.today96 .place .picgo{display:block;width:100%;height:100%;position:relative}
.today96 .place img{width:100%;height:100%;object-fit:cover;display:block}
.today96 .place .nm{position:absolute;left:0;right:0;bottom:0;padding:14px 8px 4px;font-size:12px;
 font-weight:600;color:#fff;background:linear-gradient(transparent,rgba(30,22,14,.82));
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.today96 .place .by{position:absolute;top:5px;right:7px;font-size:9px;color:#fff;
 background:rgba(26,18,10,.68);border-radius:6px;padding:1px 5px;max-width:84%;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* the day. Wider than a square because in both-languages mode it carries
   "วันพุธ · Wednesday" over "ขึ้น 6 ค่ำ · waxing day 6", and a name cut in half
   is worse than a card that takes another thirty pixels. */
.today96 .day{width:124px;text-align:center}
.today96 .day .disc{width:28px;height:28px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(0,0,0,.08);flex:none}
.today96 .day b{font-size:12.5px;font-weight:600;line-height:1.15;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.today96 .day .kham{font-size:10px;color:var(--meta,#5c574c);line-height:1.15;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.today96 .day.phra .disc{box-shadow:inset 0 0 0 1px rgba(0,0,0,.08),0 0 0 3px var(--gold,#C9A227)}
/* the word */
.today96 .word{width:172px;align-items:flex-start;justify-content:center;gap:1px;text-align:left}
.today96 .word .wth{font-size:15px;font-weight:600;line-height:1.2;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.today96 .word .wrd{font-size:10.5px;color:var(--ant);letter-spacing:.02em;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.today96 .word .wen{font-size:11px;color:var(--meta,#5c574c);line-height:1.2;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.today96 .word .wn{position:absolute;top:6px;right:8px;font-size:10px;color:var(--meta,#5c574c)}
/* ห้องน้ำ — the first card, and the widest mark on the strip */
.today96 .loo{width:92px;gap:5px}
.today96 .loo .loomark svg{fill:var(--ant);display:block}
.today96 .loo b{font-size:12px;font-weight:600}
/* เปิดอยู่ตอนนี้ — the number, and the day's shape behind it */
.today96 .openc{width:132px;gap:4px}
.today96 .openc b{font-size:21px;font-weight:700;line-height:1;
 font-variant-numeric:tabular-nums;color:var(--ant-dark,#8f2a21)}
.today96 .ocurve svg{width:108px;height:26px;display:block}
.today96 .ocurve rect{fill:var(--hair,#d8d2c4)}
.today96 .ocurve rect.on{fill:var(--ant,#c13a2e)}
/* ฝุ่น */
.today96 .air{width:104px;gap:2px}
.today96 .air b{font-size:22px;font-weight:700;line-height:1;font-variant-numeric:tabular-nums}
.today96 .air b sup{font-size:9px;font-weight:400;margin-left:1px;vertical-align:super}
.today96 .air .aband{font-size:11px;line-height:1.1;text-align:center}
.today96 .air .arooms{font-size:9.5px;color:var(--meta,#5c574c);
 display:inline-flex;align-items:center;gap:3px;white-space:nowrap}
.today96 .air .arooms .rm{fill:var(--meta,#5c574c)}
/* เดิน ≠ ขี่ — three measurements of one leg */
.today96 .plan{width:136px}
.today96 .pbars{display:flex;flex-direction:column;gap:5px;width:100%}
.today96 .pb{display:flex;align-items:center;gap:5px}
.today96 .pb .pm{flex:none;color:var(--meta,#5c574c);fill:var(--meta,#5c574c)}
.today96 .pb i{height:7px;border-radius:4px;display:block;min-width:4px}
.today96 .pb u{font-size:9.5px;text-decoration:none;color:var(--meta,#5c574c);
 font-variant-numeric:tabular-nums;white-space:nowrap}
.today96 .pb i.k-crow{background:var(--hair,#d8d2c4)}
.today96 .pb i.k-foot{background:#C2401C}
.today96 .pb i.k-ride{background:#2B4E86}
/* the dice */
.today96 .go{width:64px;min-width:64px;color:var(--ant)}
html.easyread .today96 .t96card{height:120px}
html.easyread .today96 .day b{font-size:15px}
html.easyread .today96 .word .wth{font-size:17px}
@media (max-width:420px){.today96 .t96card{height:96px}.today96 .pic{width:150px}
 .today96 .place{width:158px}}
@media (min-width:1024px){
 .today96 .tdstrip{overflow:visible;flex-wrap:wrap;justify-content:center}
}
"""

JS = r"""
// ── ของวันนี้ — the band reads the reader's own clock and the reader's own
// city, so it is right in the morning whether or not a build ran overnight.
// It works off the inline payload; the one fetch is the dice, on a tap.
(function(){
  if(typeof document==='undefined'||!document.querySelector)return;
  var host=document.querySelector('.today96');if(!host)return;
  var D={};try{D=JSON.parse(document.getElementById('td96').textContent);}catch(e){return;}
  var now=new Date();
  var iso=now.getFullYear()+'-'+String(now.getMonth()+1).padStart(2,'0')+'-'+String(now.getDate()).padStart(2,'0');
  var city='cm';try{city=localStorage.getItem('md-city')||'cm';}catch(e){}
  if(!(D.open&&D.open[city]))city='cm';
  var R=document.documentElement.getAttribute('data-root')||'';
  // md.js's own pair-writer where it is loaded (it is, on every page) —
  // building the pair by hand is what left "แรม 4 ค่ำWaning" jammed together
  // on the sky tile, and a second copy of the rule would drift from the first.
  var bi=window.mdBi||function(th,en){return '<span class="th" lang="th">'+th+'</span>'+
    (en?'<span class="th" lang="th"> · </span><span class="en" lang="en">'+en+'</span>':'');};
  // Days since an epoch the reader's own clock can compute: the rotations
  // below must not depend on when the site was built, or a skipped walk
  // freezes the picture and the word on whatever the last build chose.
  var dayNo=Math.floor(Date.UTC(now.getFullYear(),now.getMonth(),now.getDate())/864e5);

  // ---- the day ---------------------------------------------------------
  var dayCard=document.getElementById('tdday'),d=D.days&&D.days[iso];
  if(dayCard){
    if(!d){dayCard.remove();}            // past the window: say nothing rather than something old
    else{
      var disc=document.getElementById('tddisc');if(disc)disc.style.background=d.hex;
      var nm=document.getElementById('tddayname');if(nm)nm.innerHTML=bi(d.th,d.en);
      var kh=document.getElementById('tdkham');if(kh)kh.innerHTML=bi(d.mth||'',d.men||'');
      dayCard.classList.toggle('phra',!!d.phra);
      // วันพระ: the card's door becomes the wat rounds, which is the thing a
      // person is likely to be looking for on that day and no other.
      if(d.phra)dayCard.setAttribute('href',R+'wats/');
      dayCard.setAttribute('aria-label',d.th+' · '+d.en+(d.phra?' · วันพระ · wan phra':''));
      // The whole page borrows the day's colour, the way the widget pages do.
      try{document.documentElement.style.setProperty('--day',d.hex);}catch(e){}
    }
  }
  // ---- the picture -----------------------------------------------------
  var pics=D.pics||[],img=document.getElementById('tdpicimg');
  if(img&&pics.length){
    var p=pics[dayNo%pics.length];
    if(img.getAttribute('src')!==R+p.f){img.setAttribute('src',R+p.f);}
    img.setAttribute('alt',p.alt||'');img.setAttribute('width',p.w);img.setAttribute('height',p.h);
    var a=document.getElementById('tdpic');if(a){a.setAttribute('href',R+p.href);a.setAttribute('title',p.alt||'');}
    var by=document.getElementById('tdpicby');if(by)by.textContent=p.by||'';
  }
  // ---- the place of the day, in the reader's own city -------------------
  var pls=((D.places||{})[city])||[],plImg=document.getElementById('tdplaceimg');
  if(plImg&&pls.length){
    var pl=pls[dayNo%pls.length],pa=document.getElementById('tdplace');
    plImg.setAttribute('src',R+pl.f);plImg.setAttribute('alt',pl.alt||'');
    if(pa){pa.setAttribute('href',R+pl.href);
      pa.setAttribute('title',[pl.th,pl.rd,pl.en].filter(Boolean).join(' · '));}
    var pn=document.getElementById('tdplacenm');if(pn)pn.textContent=pl.th||pl.en||'';
    var pb=document.getElementById('tdplaceby');if(pb)pb.textContent=pl.by||'';
  }else if(plImg&&!pls.length){
    var pc=document.getElementById('tdplace');if(pc&&pc.parentNode)pc.parentNode.remove();
  }
  // ---- the word --------------------------------------------------------
  var ws=D.words||[];
  if(ws.length){
    var w=ws[dayNo%ws.length],card=document.getElementById('tdword');
    var set=function(id,v){var el=document.getElementById(id);if(el)el.textContent=v;};
    set('tdwth',w.th);set('tdwrd',w.rd);set('tdwen',w.en);set('tdwn',String(w.n));
    if(card){card.setAttribute('href',R+'search.html?tag='+encodeURIComponent(w.th));
      card.setAttribute('aria-label',w.th+' · '+w.rd+' · '+w.en);}
  }
  // ---- เปิดอยู่ตอนนี้, for this city and this hour ----------------------
  // The whole point of the card: a static page cannot know what o'clock it is
  // being read at, so the count is picked here, from the week baked above.
  (function(){
    var grid=((D.open||{})[city])||null,n=document.getElementById('tdopenn'),
        c=document.getElementById('tdopencurve');
    if(!grid||!n||!c){var card=document.getElementById('tdopen');
      if(card&&!grid)card.remove();return;}
    var wd=(now.getDay()+6)%7,hr=now.getHours(),day=grid[wd]||[];
    if(!day.length)return;
    n.textContent=(day[hr]||0).toLocaleString();
    var top=Math.max.apply(null,day)||1,W=108,H=26,step=W/24,o=[];
    o.push('<svg viewBox="0 0 '+W+' '+H+'" aria-hidden="true">');
    day.forEach(function(v,i){var h=Math.max(1.2,v/top*(H-2));
      o.push('<rect class="'+(i===hr?'on':'')+'" x="'+(i*step+0.6).toFixed(1)+
             '" y="'+(H-h).toFixed(1)+'" width="'+(step-1.2).toFixed(1)+
             '" height="'+h.toFixed(1)+'" rx="1"/>');});
    o.push('</svg>');c.innerHTML=o.join('');
    var card=document.getElementById('tdopen');
    if(card)card.setAttribute('aria-label',(day[hr]||0).toLocaleString()+' '+
      'เปิดอยู่ตอนนี้ · open right now');
  })();
  // ---- ฝุ่น, for this city ----------------------------------------------
  (function(){
    var a=((D.air||{})[city]),n=document.getElementById('tdairn'),
        b=document.getElementById('tdairband');
    if(!a){var card=document.getElementById('tdair');if(card&&!((D.air||{}).cm))card.remove();return;}
    if(n){n.innerHTML=Math.round(a.pm)+'<sup>µg</sup>';n.style.color=a.c;}
    if(b)b.innerHTML=bi(a.th||'',a.en||'');
  })();
  // ---- the dice, scoped to that city ------------------------------------
  // md.js owns `.rand` and rolls the whole site; this one stays inside the
  // city the reader is standing in, which is what "take me somewhere" means
  // to somebody who is somewhere.
  var go=document.getElementById('tdgo');
  if(go)go.addEventListener('click',function(ev){
    ev.preventDefault();
    fetch(R+'data/index.json').then(function(r){return r.json();}).then(function(idx){
      var pool=(idx||[]).filter(function(x){return x.p===city;});
      if(!pool.length)pool=idx||[];
      if(!pool.length)return;
      var pick=pool[Math.floor(Math.random()*pool.length)];
      location.href=R+pick.p+'/p/'+pick.s+'.html';
    }).catch(function(){location.href=go.getAttribute('href');});
  });
})();
"""
