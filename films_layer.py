#!/usr/bin/env python3
"""/films.html — หนัง, Films: the cinemas of Chiang Mai and Chiang Rai, by day.

The front page's Films tile draws today's shows for one province. This page
holds the whole of data/showtimes.json (importers/make_showtimes.py, Major
Cineplex): a tab per day in the file, a section per cinema, a row per film,
and a chip per show with its end time.

THE ONE SUM. End = start + the film's running time as Major lists it. The
adverts and trailers before the film are not in it; the notes say so.

WHAT THE BROWSER ADDS. The page is complete as built. films.js reads the
reader's clock in Bangkok time and marks each show: started (dimmed), running
now (outlined, minutes left), next. It draws the playhead on the timeline
strips and hides the tabs of days already gone.

PLACE LINKS. Each Major screen is matched to its record in data/canonical by
id (PLACE below, matched by hand on 2026-10-03 against name and position).
The IMAX hall shares the Central Festival record. The Big C screen is the
overture record at Ban Du; the other overture record for it has no pin and
its pinWas lands in the same spot.

Entry point: emit(globals_of_build, data). Standalone, over a built docs/:
    python3 films_layer.py
"""
import datetime
import json
import shutil
import zlib
from pathlib import Path

import shelflife

ROOT = Path(__file__).resolve().parent

PLACE = {
    "91": "cm-osm-node-2865865701",
    "92": "cm-osm-node-2865865701",
    "40": "cm-osm-node-3347633197",
    "61": "cr-osm-node-6725710285",
    "188": "cr-ovt-bd951a4f-fc04-4eb9-a927-6fbb0e7e7549",
}

# Screens in the catalogue with no times in the file. SF refuses automated
# requests (see importers/make_showtimes.py).
OTHERS = [
    {"id": "cm-osm-node-2717002069", "province": "cm",
     "th": "เอสเอฟเอ็กซ์ ซีเนม่า เมญ่า", "en": "SFX Cinema Maya",
     "url": "https://www.sfcinemacity.com/"},
]

GENRES = {
    "แอ็คชัน": "Action", "แอ็กชัน": "Action", "สยองขวัญ": "Horror",
    "ผจญภัย": "Adventure", "แอนิเมชัน": "Animation", "อนิเมชัน": "Animation",
    "ตลก": "Comedy", "แฟนตาซี": "Fantasy", "เพลง": "Music", "มิวสิคัล": "Musical",
    "อาชญากรรม": "Crime", "ชีวิต": "Drama", "ดราม่า": "Drama",
    "โรแมนติก": "Romance", "ระทึกขวัญ": "Thriller", "วิทยาศาสตร์": "Science fiction",
    "ไซไฟ": "Science fiction", "สารคดี": "Documentary", "ครอบครัว": "Family",
    "สงคราม": "War", "ประวัติศาสตร์": "History", "กีฬา": "Sport",
    "ลึกลับ": "Mystery", "ชีวประวัติ": "Biography", "คอนเสิร์ต": "Concert",
    "อนิเมะ": "Anime", "เด็ก": "Children",
}

SOUND = {
    "TH/EN": ("เสียงไทย ซับอังกฤษ", "Thai sound, English subtitles"),
    "EN/TH": ("เสียงอังกฤษ ซับไทย", "English sound, Thai subtitles"),
    "TH/--": ("เสียงไทย ไม่มีซับ", "Thai sound, no subtitles"),
    "EN/--": ("เสียงอังกฤษ ไม่มีซับ", "English sound, no subtitles"),
    "EN/EN": ("เสียงอังกฤษ ซับอังกฤษ", "English sound, English subtitles"),
}

FORMAT = {
    "type-laser": ("ระบบเลเซอร์", "Laser"),
    "type-digital": ("ระบบดิจิทัล", "Digital"),
    "Type-IMAX-Laser-2D": ("ไอแมกซ์ เลเซอร์ 2D", "IMAX Laser 2D"),
    "theatre-kids": ("โรงหนังเด็ก", "Kids' cinema"),
}

PROV = {"cm": ("เชียงใหม่", "Chiang Mai"), "cr": ("เชียงราย", "Chiang Rai")}
WD_TH = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
WD_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MO_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.",
         "ต.ค.", "พ.ย.", "ธ.ค."]
MO_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
         "Nov", "Dec"]
SMALL = {"and", "at", "of", "the", "in", "on", "a", "an", "to", "with", "for"}
DEFAULT_MIN = 110   # a film with no listed length is drawn this long, dashed


def latin(slug):
    """Major's own address for the film, as a title: saming-kao-kwang -> Saming Kao Kwang."""
    if not slug:
        return ""
    w = slug.split("-")
    return " ".join(x if (i and x in SMALL) else x[:1].upper() + x[1:]
                    for i, x in enumerate(w))


def mins(t):
    h, m = int(t[:2]), int(t[3:5])
    m += h * 60
    return m + 1440 if h < 5 else m   # a show after midnight belongs to the night before


def hm(m):
    return "%02d:%02d" % ((m // 60) % 24, m % 60)


def runtime(bi, n):
    if not n:
        return bi("ความยาวไม่ระบุ", "running time not listed")
    h, m = divmod(n, 60)
    th = (f"{h} ชม. {m} นาที" if h else f"{m} นาที") + f" ({n} นาที)"
    en = (f"{h} h {m} min" if h else f"{m} min") + f" ({n} min)"
    return bi(th, en)


def day_label(bi, d):
    x = datetime.date.fromisoformat(d)
    return bi(f"{WD_TH[x.weekday()]} {x.day} {MO_TH[x.month - 1]}",
              f"{WD_EN[x.weekday()]} {x.day} {MO_EN[x.month - 1]}")


def genres_html(bi, gs):
    return " · ".join(bi(g, GENRES.get(g, "")) for g in gs)


def place_links(g, c, by_id):
    """(place page path, map hash) for a cinema, or (None, None)."""
    r = by_id.get(PLACE.get(c["id"]) or c.get("place") or "")
    if not r or r.get("lat") is None:
        return None, None
    slug = g["place_slug"](r)
    path = f'{r["province"]}/p/{slug}.html'
    mp = (f'map.html#17/{r["lat"]:.5f}/{r["lng"]:.5f}/'
          f'{r["province"]}-whats-on/pin={r["province"]}:{slug}')
    return path, mp


def lanes(shows):
    """Greedy interval split: a show goes on the first lane free at its start."""
    ends, out = [], []
    for s in shows:
        for i, e in enumerate(ends):
            if e <= s["a"]:
                ends[i] = s["b"]
                out.append(i)
                break
        else:
            ends.append(s["b"])
            out.append(len(ends) - 1)
    return out, max(1, len(ends))


def film_shows(f):
    """A film's shows at one cinema as {a, b, t, screen, sound, fmt}."""
    n = f.get("minutes") or DEFAULT_MIN
    rows = f.get("shows") or [{"t": t} for t in f.get("times") or []]
    out = []
    for s in rows:
        a = mins(s["t"])
        out.append({**s, "a": a, "b": a + n})
    out.sort(key=lambda s: (s["a"], s.get("screen") or ""))
    return out


def hue(title):
    return zlib.crc32(title.encode()) % 360


def strip_html(g, films, h0, h1):
    """A row per film, a block per show as long as the film. The text
    equivalent is the chip list beside it, so the strip is aria-hidden."""
    bi, att = g["bi"], g["att"]
    span = (h1 - h0) * 60.0

    def x(m):
        return 100.0 * (m - h0 * 60) / span

    ticks = "".join(
        f'<span class="fm-hr{" odd" if (h - h0) % 2 else ""}" style="left:{x(h * 60):.3f}%">'
        f'{h % 24:02d}</span>' for h in range(h0, h1 + 1))
    rows = []
    for f, key in films:
        ss = film_shows(f)
        ln, n = lanes(ss)
        hu = hue(f["title"])
        blocks = "".join(
            f'<i class="fm-blk{" nolen" if not f.get("minutes") else ""}" data-a="{s["a"]}" '
            f'data-b="{s["b"]}" style="left:{x(s["a"]):.3f}%;width:{x(s["b"]) - x(s["a"]):.3f}%;'
            f'top:{l * 14}px" title="{att(hm(s["a"]) + "–" + hm(s["b"]))}"></i>'
            for s, l in zip(ss, ln))
        rows.append(
            f'<div class="fm-row" style="--hu:{hu}">'
            f'<a class="fm-rt" href="#{key}">{bi(f["title"], latin(f.get("slug")))}</a>'
            f'<div class="fm-track" style="height:{n * 14}px;--span:{h1 - h0}">{blocks}</div></div>')
    return (f'<div class="fm-strip" aria-hidden="true" data-h0="{h0}" data-h1="{h1}">'
            f'<div class="fm-hrs">{ticks}</div>{"".join(rows)}'
            f'<div class="fm-plw"><b class="fm-play" hidden></b></div></div>')


def film_block(g, c, f, key):
    bi, esc = g["bi"], g["esc"]
    ss = film_shows(f)
    groups = {}
    for s in ss:
        groups.setdefault((s.get("sound") or "", s.get("fmt") or ""), []).append(s)
    parts = []
    for (snd, fmt), rows in groups.items():
        lab = []
        if snd:
            st = SOUND.get(snd)
            lab.append(bi(*st) + f' <span class="fm-code">{esc(snd)}</span>' if st else esc(snd))
        if fmt in FORMAT:
            lab.append(bi(*FORMAT[fmt]))
        chips = "".join(
            f'<li class="fm-show" data-a="{s["a"]}" data-b="{s["b"]}">'
            f'<span class="fm-t"><b>{hm(s["a"])}</b> → {hm(s["b"]) if f.get("minutes") else "?"}</span>'
            + (f'<span class="fm-hall">{hall(bi, s["screen"])}</span>' if s.get("screen") else "")
            + '<span class="fm-st"></span></li>' for s in rows)
        parts.append(f'<div class="fm-grp">'
                     + (f'<p class="fm-gh">{" · ".join(lab)}</p>' if lab else "")
                     + f'<ul class="fm-shows">{chips}</ul></div>')
    first = ss[0]
    return (f'<article class="fm-film" id="{key}" style="--hu:{hue(f["title"])}">'
            f'<h4>{bi(f["title"], latin(f.get("slug")))}</h4>'
            f'<p class="fm-meta">{runtime(bi, f.get("minutes"))}'
            + (f' · {genres_html(bi, f.get("genres") or [])}' if f.get("genres") else "")
            + f' · {bi(f"{len(ss)} รอบ", f"{len(ss)} shows")}</p>'
            f'<p class="fm-next" data-next>{bi("รอบแรก " + hm(first["a"]), "First show " + hm(first["a"]))}</p>'
            + "".join(parts) + '</article>')


def hall(bi, name):
    if name.startswith("Theatre "):
        return bi("โรง " + name[8:], name)
    return bi(name, name)


def film_index(g, cines, day, cine_names):
    """Cards across both provinces for one day, most shows first. The counts
    and sound lines come per scope (both / cm / cr); the CSS shows the one
    matching the province buttons."""
    bi, att = g["bi"], g["att"]
    by = {}
    for c in cines:
        for fi, f in enumerate(c["days"].get(day) or []):
            e = by.setdefault(f["title"], {"f": f, "at": [], "shows": []})
            ss = film_shows(f)
            e["at"].append((c, ss, f"{c['_dk']}-f{fi}"))
            e["shows"] += [[s["a"], s["b"], cine_names.index(c["id"])] for s in ss]

    def scoped(e, sc):
        at = [x for x in e["at"] if sc == "all" or x[0]["province"] == sc]
        n, k = sum(len(x[1]) for x in at), len(at)
        snds = sorted({s.get("sound") for x in at for s in x[1] if s.get("sound")})
        return n, k, snds

    cards = []
    for title, e in sorted(by.items(), key=lambda kv: -len(kv[1]["shows"])):
        f = e["f"]
        e["shows"].sort()
        provs = sorted({x[0]["province"] for x in e["at"]})
        scopes = [("all " + provs[0], scoped(e, "all"))] if len(provs) == 1 else \
            [("all", scoped(e, "all"))] + [(p, scoped(e, p)) for p in provs]
        count = snd = ""
        for sc, (n, k, snds) in scopes:
            count += (f'<span class="fm-sc" data-sc="{sc}">'
                      + bi(f"{n} รอบ ที่ {k} โรง", f"{n} shows at {k} cinema" + ("s" if k > 1 else ""))
                      + '</span>')
            if snds:
                snd += (f'<span class="fm-sc" data-sc="{sc}">'
                        + " · ".join(bi(*SOUND[x]) if x in SOUND else x for x in snds) + '</span>')
        at = "".join(f'<li data-prov="{c["province"]}"><a href="#{key}">{bi(c["th"], c["en"])}</a> '
                     f'<span class="fm-n">{bi(f"{len(ss)} รอบ", f"{len(ss)} shows")}</span></li>'
                     for c, ss, key in e["at"])
        first = e["shows"][0]
        cards.append(
            f'<li class="fm-card" style="--hu:{hue(title)}" data-in="{" ".join(provs)}" '
            f'data-shows="{att(json.dumps(e["shows"], separators=(",", ":")))}">'
            f'<h3>{bi(title, latin(f.get("slug")))}</h3>'
            f'<p class="fm-meta">{runtime(bi, f.get("minutes"))}'
            + (f' · {genres_html(bi, f.get("genres") or [])}' if f.get("genres") else "")
            + '</p>'
            f'<p class="fm-count">{count}</p>'
            + (f'<p class="fm-snd">{snd}</p>' if snd else "")
            + f'<p class="fm-next" data-next>{bi("รอบแรก " + hm(first[0]), "First show " + hm(first[0]))}</p>'
            f'<ul class="fm-at">{at}</ul></li>')
    return f'<ul class="fm-cards">{"".join(cards)}</ul>'


def cinema_section(g, c, day, by_id, h0, h1):
    bi, att = g["bi"], g["att"]
    films = c["days"].get(day) or []
    path, mp = place_links(g, c, by_id)
    links = []
    if c.get("url"):
        links.append(f'<a class="fm-book" href="{att(c["url"])}" rel="noopener">'
                     f'{bi("รอบและตั๋วที่เว็บเมเจอร์", "Times and tickets at Major")} →</a>')
    if path:
        links.append(f'<a href="{att(path)}">{bi("หน้าโรงหนังในมดแดง", "Mot Dang page")}</a>')
    if mp:
        links.append(f'<a href="{att(mp)}">{bi("แผนที่", "Map")}</a>')
    head = (f'<header class="fm-ch"><h3>{bi(c["th"], c["en"])}</h3>'
            f'<p class="fm-prov">{bi(*PROV[c["province"]])} · '
            f'{bi(f"{len(films)} เรื่อง", f"{len(films)} films")}</p>'
            f'<p class="fm-links">{" · ".join(links)}</p></header>')
    if not films:
        return (f'<section class="fm-cine" data-prov="{c["province"]}">{head}'
                f'<p class="fm-none">{bi("วันนี้ไม่มีรอบในข้อมูล", "No shows in the listing for this day")}</p></section>')
    keyed = [(f, f"{c['_dk']}-f{i}") for i, f in enumerate(films)]
    keyed.sort(key=lambda fk: min(s["a"] for s in film_shows(fk[0])))
    return (f'<section class="fm-cine" data-prov="{c["province"]}" id="{c["_dk"]}">{head}'
            + strip_html(g, keyed, h0, h1)
            + "".join(film_block(g, c, f, k) for f, k in keyed) + '</section>')


def build_page(g, doc, by_id):
    bi, bi_text, att, esc = g["bi"], g["bi_text"], g["att"], g["esc"]
    cines = doc["cinemas"]
    days = [d for d in doc.get("dates") or [] if any(d in c["days"] for c in cines)]
    cine_names = [c["id"] for c in cines]
    names_js = [[c["th"], c["en"], c["id"], c["province"]] for c in cines]

    tabs = "".join(
        f'<button type="button" class="fm-tab" data-day="{d}" '
        f'aria-pressed="{"true" if i == 0 else "false"}">{day_label(bi, d)}</button>'
        for i, d in enumerate(days))
    provs = "".join(
        f'<button type="button" class="fm-pv" data-pv="{k}" aria-pressed="{"true" if k == "all" else "false"}">{lab}</button>'
        for k, lab in (("all", bi("ทั้งสองจังหวัด", "Both provinces")),
                       ("cm", bi(*PROV["cm"])), ("cr", bi(*PROV["cr"]))))

    panes = []
    total = 0
    for i, d in enumerate(days):
        for c in cines:
            c["_dk"] = f'd{i}-c{c["id"]}'
        allshows = [s for c in cines for f in c["days"].get(d) or [] for s in film_shows(f)]
        total += len(allshows)
        h0 = min(s["a"] for s in allshows) // 60
        h1 = -(-max(s["b"] for s in allshows) // 60)
        idx = film_index(g, cines, d, cine_names)
        secs = "".join(cinema_section(g, c, d, by_id, h0, h1) for c in cines)
        panes.append(
            f'<div class="fm-day" data-day="{d}"{"" if i == 0 else " hidden"}>'
            f'<h2 class="fm-dh">{bi("หนัง", "Films")} · {day_label(bi, d)}</h2>{idx}'
            f'<h2 class="fm-dh">{bi("โรง", "Cinemas")} · {day_label(bi, d)}</h2>'
            f'<p class="fm-key">'
            + bi("แถบสีหนึ่งแถบคือหนึ่งรอบ ยาวเท่าความยาวหนัง เส้นสีทองคือเวลาตอนนี้ แถบสีเทาคือรอบที่เริ่มไปแล้ว",
                 "Each block is one show, as long as the film. The gold line is now; "
                 "grey blocks have started.")
            + f'</p>{secs}</div>')

    films_n = len({f["title"] for c in cines for v in c["days"].values() for f in v})
    now = (f'<div class="fm-now" id="fm-now" aria-live="polite">'
           f'<p class="fm-big" id="fm-nowline">'
           + bi(f"{films_n} เรื่อง {len(cines)} โรง {total} รอบ ใน {len(days)} วัน",
                f"{films_n} films, {len(cines)} cinemas, {total} shows over {len(days)} days")
           + '</p><p id="fm-nextline"></p></div>')

    others = "".join(
        f'<li><b>{bi(o["th"], o["en"])}</b> · {bi(*PROV[o["province"]])}<br>'
        + bi("รอบของ SF ไม่อยู่ในหน้านี้ ดูที่เว็บของ SF", "SF's showtimes are not on this page; they are on SF's own site.")
        + f' <a href="{att(o["url"])}" rel="noopener">sfcinemacity.com</a>'
        + (lambda p: f' · <a href="{att(p[0])}">{bi("หน้าโรงหนังในมดแดง", "Mot Dang page")}</a>'
           f' · <a href="{att(p[1])}">{bi("แผนที่", "Map")}</a>' if p[0] else "")(
            place_links(g, {"id": "", "place": o["id"]}, by_id))
        + '</li>' for o in OTHERS)

    gen = doc.get("generated") or ""
    notes = (
        f'<section class="fm-notes"><h2>{bi("โรงอื่น", "Other cinemas")}</h2>'
        f'<ul>{others}</ul>'
        f'<h2>{bi("ที่มา", "Sources")}</h2><ul>'
        f'<li>{bi(f"รอบฉาย ความยาวหนัง ประเภทหนัง โรง และเสียง/ซับ จากเว็บเมเจอร์ ซีนีเพล็กซ์ อ่านเมื่อ {gen}", f"Showtimes, running times, genres, halls and sound/subtitles: Major Cineplex’s own site, read {gen}.")}</li>'
        f'<li>{bi("เวลาจบ = เวลาเริ่ม + ความยาวหนัง ไม่ได้รวมโฆษณาและตัวอย่างหนังก่อนเรื่อง", "End time = start + the film’s running time. Adverts and trailers before the film are not in the sum.")}</li>'
        f'<li>{bi("TH/EN = เสียงไทย ซับอังกฤษ · EN/TH = เสียงอังกฤษ ซับไทย · TH/-- = เสียงไทย ไม่มีซับ", "TH/EN = Thai sound, English subtitles · EN/TH = English sound, Thai subtitles · TH/-- = Thai sound, no subtitles")}</li>'
        f'<li>{bi("ชื่อหนังอักษรโรมันมาจากที่อยู่หน้าหนังเรื่องนั้นในเว็บเมเจอร์", "Latin-letter titles are each film’s address on Major’s site.")}</li>'
        f'<li>{bi("เวลาทั้งหมดเป็นเวลาประเทศไทย รอบที่เริ่มแล้วและรอบที่กำลังฉายคิดจากนาฬิกาของเครื่องที่เปิดหน้านี้", "Times are Thailand time. Started and running shows follow the clock of the device reading this page.")}</li>'
        f'<li><a href="data/showtimes.json">showtimes.json</a></li>'
        f'</ul></section>')

    stale = (f'<p class="fm-stale">'
             + bi("รอบฉายในหน้านี้เก่าเกินไปแล้ว ดูรอบล่าสุดที่เว็บเมเจอร์",
                  "The showtimes here are too old to use; Major's site has the current ones.")
             + ' <a href="https://www.majorcineplex.com/" rel="noopener">majorcineplex.com</a></p>')

    body = (
        f'<h1>🎬 {bi("หนัง", "Films")}</h1>'
        f'<p class="lede">'
        + bi("รอบฉายของโรงเมเจอร์ ซีนีเพล็กซ์ในเชียงใหม่และเชียงราย แยกตามวัน พร้อมความยาวหนังและเวลาจบของแต่ละรอบ",
             "Showtimes at the Major Cineplex screens in Chiang Mai and Chiang Rai, by day, "
             "with each film's running time and the time each show ends.")
        + '</p>'
        + shelflife.guard("showtimes", gen, (
            now
            + f'<div class="fm-bar"><div class="fm-tabs" role="group" aria-label="{att(bi_text("วัน", "Day"))}">{tabs}</div>'
            f'<div class="fm-pvs" role="group" aria-label="{att(bi_text("จังหวัด", "Province"))}">{provs}</div></div>'
            f'<p class="fm-gone" id="fm-gone" hidden>'
            + bi("วันในข้อมูลนี้ผ่านไปหมดแล้ว", "The days in this listing have passed.")
            + '</p>'
            f'<div class="fm-panes" id="fm-panes" data-pv="all">{"".join(panes)}</div>'
            f'<script type="application/json" id="fm-names">{json.dumps(names_js, ensure_ascii=False)}</script>'),
            stale_html=stale)
        + notes
        + g["share_block"](g["BASE"] + "films.html",
                           bi_text("หนัง รอบฉายเชียงใหม่ เชียงราย", "Films: Chiang Mai and Chiang Rai showtimes")))

    v = version()
    return g["page"](
        "หนัง · Films — รอบฉายเชียงใหม่ เชียงราย", body, depth=0, path="films.html",
        desc="รอบหนังทุกโรงเมเจอร์ในเชียงใหม่และเชียงราย แยกตามวัน พร้อมเวลาจบของแต่ละรอบ · "
             "Showtimes at the Major Cineplex screens in Chiang Mai and Chiang Rai, by day, "
             "with the end time of each show.",
        extra_head=f'<link rel="stylesheet" href="films.css?v={v}">'
                   f'<script src="films.js?v={v}" defer></script>',
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("หนัง", "Films")), total


def version():
    return "%08x" % (zlib.crc32((JS + CSS).encode()) & 0xFFFFFFFF)


def emit(g, data):
    DOCS, ROOT_ = g["DOCS"], g["ROOT"]
    src = ROOT_ / "data" / "showtimes.json"
    if not src.exists():
        return "SKIPPED — no data/showtimes.json (importers/make_showtimes.py)"
    doc = json.loads(src.read_text(encoding="utf-8"))
    if not doc.get("cinemas"):
        return "SKIPPED — showtimes.json has no cinemas"
    by_id = dict(g.get("PLACE_BY_ID") or {})
    if not by_id:
        by_id = {r["id"]: r for rs in (data or {}).values() for r in rs}
    html, total = build_page(g, doc, by_id)
    (DOCS / "films.css").write_text(CSS)
    (DOCS / "films.js").write_text(JS)
    (DOCS / "films.html").write_text(html)
    (DOCS / "data").mkdir(exist_ok=True)
    shutil.copyfile(src, DOCS / "data" / "showtimes.json")
    linked = sum(1 for c in doc["cinemas"] if place_links(g, c, by_id)[0])
    return (f'{len(doc["cinemas"])} cinemas ({linked} with place pages), '
            f'{total} shows, page {len(html.encode()) / 1024:.0f} kB')


CSS = """/* /films.html — หนัง, generated by films_layer.py */
.fm-now{background:#121019;color:#f7f3ea;border-radius:14px;padding:12px 16px;margin:10px 0 12px}
.fm-now p{margin:0;font-size:1.05rem}
.fm-now .fm-big{font-size:1.3rem;font-weight:700}
.fm-now a{color:#ffd48a}
.fm-bar{display:flex;flex-wrap:wrap;gap:8px 16px;margin:0 0 12px}
.fm-tabs,.fm-pvs{display:flex;flex-wrap:wrap;gap:6px}
.fm-tab,.fm-pv{font:inherit;font-size:1rem;font-weight:700;min-height:44px;padding:6px 14px;
 border:2px solid var(--ink);border-radius:999px;background:var(--card);color:var(--ink);cursor:pointer}
.fm-tab[aria-pressed=true],.fm-pv[aria-pressed=true]{background:var(--ink);color:#f7f3ea}
.fm-tab[hidden]{display:none}
.fm-gone,.fm-stale{font-weight:700}
.fm-dh{margin:18px 0 8px}
.fm-key{font-size:1rem;color:var(--ink)}
.fm-cards{list-style:none;padding:0;margin:0 0 8px;display:grid;gap:10px;
 grid-template-columns:repeat(auto-fill,minmax(min(100%,19rem),1fr))}
.fm-card{background:var(--card);border:2px solid var(--ink);border-left:10px solid hsl(var(--hu),60%,42%);
 border-radius:12px;padding:10px 12px;min-width:0}
.fm-card h3{margin:0 0 4px;font-size:1.2rem;overflow-wrap:anywhere}
.fm-card p{margin:2px 0;font-size:1rem}
.fm-count{font-weight:700}
.fm-at{list-style:none;padding:0;margin:6px 0 0}
.fm-at li{margin:2px 0}
.fm-n{white-space:nowrap}
.fm-next{font-weight:700}
.fm-next .fm-soon{background:#ffd48a;color:#1a1208;border-radius:6px;padding:0 6px}
.fm-panes[data-pv=cm] [data-prov=cr],.fm-panes[data-pv=cr] [data-prov=cm],
.fm-panes[data-pv=cm] .fm-card:not([data-in~=cm]),.fm-panes[data-pv=cr] .fm-card:not([data-in~=cr]){display:none}
.fm-sc{display:none}
.fm-panes[data-pv=all] .fm-sc[data-sc~=all],.fm-panes[data-pv=cm] .fm-sc[data-sc~=cm],
.fm-panes[data-pv=cr] .fm-sc[data-sc~=cr]{display:inline}
.fm-cine{background:var(--card);border:2px solid var(--ink);border-radius:14px;padding:12px;margin:0 0 16px;min-width:0}
.fm-ch h3{margin:0;font-size:1.3rem;overflow-wrap:anywhere}
.fm-ch p{margin:2px 0;font-size:1rem}
.fm-links a{font-weight:700}
.fm-book{white-space:normal}
.fm-strip{position:relative;background:#121019;color:#f7f3ea;border-radius:10px;padding:30px 10px 10px;margin:10px 0 12px;overflow:hidden}
.fm-hrs{position:absolute;left:10px;right:10px;top:6px;height:20px}
.fm-hr{position:absolute;transform:translateX(-50%);font:700 1rem/1 ui-monospace,Menlo,monospace;color:#f7f3ea}
.fm-hr:first-child{transform:none}
.fm-hr:last-child{transform:translateX(-100%)}
.fm-row{margin:0 0 8px}
.fm-rt{display:block;color:#f7f3ea!important;text-decoration:none;font-weight:700;font-size:1rem;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0 0 3px}
.fm-rt .en{color:#f7f3ea}
.fm-track{position:relative;background:rgba(255,255,255,.07);border-radius:3px;
 background-image:repeating-linear-gradient(90deg,transparent 0,transparent calc(100%/var(--span,1) - 1px),rgba(255,255,255,.12) 0,rgba(255,255,255,.12) calc(100%/var(--span,1)))}
.fm-blk{position:absolute;height:12px;border-radius:2px;min-width:3px;
 background:hsl(var(--hu),75%,62%);box-shadow:inset 0 0 0 1px rgba(0,0,0,.35)}
.fm-blk.nolen{background:repeating-linear-gradient(90deg,hsl(var(--hu),75%,62%) 0 6px,transparent 6px 9px)}
.fm-blk.gone{background:#55505c}
.fm-blk.on{background:hsl(var(--hu),90%,72%);box-shadow:0 0 0 2px #fff}
.fm-plw{position:absolute;left:10px;right:10px;top:26px;bottom:4px;pointer-events:none}
.fm-play{position:absolute;top:0;bottom:0;width:3px;margin-left:-1px;background:#ffc266;border-radius:2px}
.fm-play:before{content:"";position:absolute;top:-6px;left:-5px;border:6.5px solid transparent;border-top-color:#ffc266}
.fm-film{border-top:2px solid var(--rule);padding:10px 0 4px;border-left:6px solid hsl(var(--hu),60%,42%);padding-left:10px;margin-top:6px}
.fm-film h4{margin:0 0 2px;font-size:1.15rem;overflow-wrap:anywhere}
.fm-film p{margin:2px 0;font-size:1rem}
.fm-gh{font-weight:700;margin:8px 0 4px!important}
.fm-code{font:700 .95rem ui-monospace,Menlo,monospace;border:1.5px solid var(--ink);border-radius:4px;padding:0 4px;white-space:nowrap}
.fm-shows{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:6px}
.fm-show{display:flex;flex-direction:column;border:2px solid var(--ink);border-radius:8px;padding:4px 10px;
 background:#fffdf7;color:var(--ink);font-size:1rem;min-width:7.5rem}
.fm-t{font-variant-numeric:tabular-nums;white-space:nowrap}
.fm-t b{font-size:1.15rem}
.fm-hall{font-size:1rem}
.fm-st:empty{display:none}
.fm-st{font-weight:700}
.fm-show.gone{background:#e6dfd2;border-color:#8a7d6a;color:#3d3226}
.fm-show.gone .fm-t b{text-decoration:line-through}
.fm-show.on{background:#121019;color:#f7f3ea;border-color:#121019;box-shadow:0 0 0 3px #ffc266}
.fm-show.on .fm-t b{text-decoration:none}
.fm-show.next{box-shadow:0 0 0 3px #1f6b57}
.fm-none{font-weight:700}
.fm-notes ul{padding-left:1.2rem}
.fm-notes li{margin:4px 0;font-size:1rem}
@media (max-width:520px){.fm-hr.odd{display:none}.fm-cine{padding:10px 8px}.fm-strip{padding:30px 8px 8px}
 .fm-hrs,.fm-plw{left:8px;right:8px}
 .fm-show{flex-direction:row;flex-wrap:wrap;align-items:baseline;column-gap:.7em;width:100%;box-sizing:border-box}}
"""

JS = r"""/* /films.html — marks started, running and next shows by the reader's clock in Bangkok time */
(function(){
'use strict';
var panes=document.getElementById('fm-panes');if(!panes)return;
var NAMES=[];try{NAMES=JSON.parse(document.getElementById('fm-names').textContent);}catch(e){}
var $$=function(q,el){return [].slice.call((el||document).querySelectorAll(q));};
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function bi(th,en){return '<span class="bi"><span class="th" lang="th">'+esc(th)+'</span><span class="en" lang="en"><span class="th" lang="th"> · </span>'+esc(en)+'</span></span>';}
function hm(m){m=((m%1440)+1440)%1440;return ('0'+Math.floor(m/60)).slice(-2)+':'+('0'+m%60).slice(-2);}
function bkk(){var d=new Date(Date.now()+7*3600e3);return {day:d.toISOString().slice(0,10),m:d.getUTCHours()*60+d.getUTCMinutes()};}
function dk(day,now){return Math.round((Date.parse(day)-Date.parse(now.day))/864e5);}
function words(n){return n<60?[n+' นาที',n+' min']:[Math.floor(n/60)+' ชม. '+(n%60)+' นาที',Math.floor(n/60)+' h '+(n%60)+' min'];}
var tabs=$$('.fm-tab'),pvs=$$('.fm-pv'),sel=null;
tabs.forEach(function(b){b.dataset.orig=b.innerHTML;});
function dayIdx(){return tabs.map(function(t){return t.dataset.day;}).indexOf(sel);}
function nextText(a,b,r,today,ci){
 var c=ci==null?null:NAMES[ci],s=bi('รอบต่อไป '+hm(a)+' → '+hm(b),'Next show '+hm(a)+' → '+hm(b));
 if(today){var w=words(a-r);s+=' <span class="fm-soon">'+bi('อีก '+w[0],'in '+w[1])+'</span>';}
 if(c)s+=' · <a href="#d'+dayIdx()+'-c'+esc(c[2])+'">'+bi(c[0],c[1])+'</a>';
 return s;}
var NONE=function(today){return today?bi('วันนี้ไม่มีรอบเหลือแล้ว','No more shows today'):bi('วันนี้ไม่มีรอบ','No shows this day');};
function paint(){
 if(!sel)return;var now=bkk(),k=dk(sel,now),r=now.m-k*1440,today=k===0;
 var pane=document.querySelector('.fm-day[data-day="'+sel+'"]');if(!pane)return;
 $$('.fm-film',pane).forEach(function(f){var nx=null;
  $$('.fm-show',f).forEach(function(s){
   var a=+s.dataset.a,b=+s.dataset.b,on=a<=r&&r<b,gone=a<=r;
   s.classList.toggle('gone',gone&&!on);s.classList.toggle('on',on);s.classList.remove('next');
   s.querySelector('.fm-st').innerHTML=on?bi('กำลังฉาย เหลือ '+words(b-r)[0],'Showing now, '+words(b-r)[1]+' left'):'';
   if(!gone&&(!nx||a<+nx.dataset.a))nx=s;});
  if(nx)nx.classList.add('next');
  var p=f.querySelector('[data-next]');
  if(p)p.innerHTML=nx?nextText(+nx.dataset.a,+nx.dataset.b,r,today,null):NONE(today);});
 $$('.fm-blk',pane).forEach(function(e){var a=+e.dataset.a,b=+e.dataset.b;
  e.classList.toggle('on',a<=r&&r<b);e.classList.toggle('gone',a<=r&&r>=b);});
 $$('.fm-strip',pane).forEach(function(s){
  var h0=+s.dataset.h0*60,h1=+s.dataset.h1*60,pl=s.querySelector('.fm-play');
  if(r<h0||r>h1){pl.hidden=true;return;}
  pl.hidden=false;pl.style.left=(100*(r-h0)/(h1-h0)).toFixed(3)+'%';});
 var running=0,cines={},best=null;
 var pv=panes.dataset.pv;
 $$('.fm-card',pane).forEach(function(c){
  var ss=[];try{ss=JSON.parse(c.dataset.shows);}catch(e){}
  ss=ss.filter(function(s){return pv==='all'||(NAMES[s[2]]||[])[3]===pv;});
  if(!ss.length)return;
  var nx=null;ss.forEach(function(s){if(s[0]>r&&(!nx||s[0]<nx[0]))nx=s;
   if(s[0]<=r&&r<s[1]){running++;cines[s[2]]=1;}});
  var p=c.querySelector('[data-next]');
  if(p)p.innerHTML=nx?nextText(nx[0],nx[1],r,today,nx[2]):NONE(today);
  if(nx&&(!best||nx[0]<best.s[0]))best={s:nx,t:c.querySelector('h3').innerHTML};});
 var line=document.getElementById('fm-nowline'),nl=document.getElementById('fm-nextline');
 if(today){var nc=Object.keys(cines).length;
  line.innerHTML=running?bi('ตอนนี้ '+hm(now.m)+' · กำลังฉาย '+running+' รอบ ใน '+nc+' โรง',
   'Now '+hm(now.m)+' · '+running+' show'+(running===1?'':'s')+' running at '+nc+' cinema'+(nc===1?'':'s')):
   bi('ตอนนี้ '+hm(now.m)+' · ไม่มีรอบที่กำลังฉาย','Now '+hm(now.m)+' · no show running');
  nl.innerHTML=best?'<b>'+best.t+'</b><br>'+nextText(best.s[0],best.s[1],r,true,best.s[2]):NONE(true);}
 else{var t=tabs[dayIdx()];line.innerHTML=bi('รอบฉาย','Showtimes')+' · '+t.innerHTML;
  nl.innerHTML=best?'<b>'+best.t+'</b><br>'+nextText(best.s[0],best.s[1],r,false,best.s[2]):'';}}
function show(day){sel=day;
 tabs.forEach(function(b){b.setAttribute('aria-pressed',b.dataset.day===day?'true':'false');});
 $$('.fm-day').forEach(function(p){p.hidden=p.dataset.day!==day;});paint();}
function setPv(v){panes.dataset.pv=v;
 pvs.forEach(function(b){b.setAttribute('aria-pressed',b.dataset.pv===v?'true':'false');});
 paint();}
function relabel(){var now=bkk(),first=null;
 tabs.forEach(function(b){var k=dk(b.dataset.day,now);b.hidden=k<0;if(k>=0&&!first)first=b.dataset.day;
  b.innerHTML=k===0?bi('วันนี้','Today'):k===1?bi('พรุ่งนี้','Tomorrow'):b.dataset.orig;});
 return first;}
var first=relabel();
document.getElementById('fm-gone').hidden=!!first;
if(!first){panes.hidden=true;document.getElementById('fm-now').hidden=true;return;}
tabs.forEach(function(b){b.addEventListener('click',function(){show(b.dataset.day);});});
pvs.forEach(function(b){b.addEventListener('click',function(){setPv(b.dataset.pv);});});
show(first);
setInterval(function(){var f=relabel();
 if(!f){location.reload();return;}
 if(tabs.some(function(t){return t.dataset.day===sel&&t.hidden;}))show(f);else paint();},60e3);
})();
"""


def main():
    import build  # importing does not build: build() runs under __main__ only
    if not (build.DOCS / "index.html").exists():
        raise SystemExit("docs/ is not built yet — run python3 build.py first")
    data = {p: json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text())
            for p in ("cm", "cr")}
    print(emit(vars(build), data))


if __name__ == "__main__":
    main()
