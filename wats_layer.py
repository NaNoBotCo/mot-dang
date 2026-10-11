#!/usr/bin/env python3
"""/wats — ไหว้พระ ๙ วัด, the wat-visit site: the rounds, and every wat on them.

Replaces /merit.html, which was one page holding ten cards, a straight-line
sketch map each, and nine names per card. What it never showed a reader was the
wat: 63 of the wats on it had a photograph on this disk and 67 had an
encyclopaedia entry, and the page rendered neither. So the shape here is a
minisite, in the house pattern (/roads, /muay-thai, /loop):

    /wats/                 the practice, the rounds, and all 92 wats by quarter
    /wats/round-01.html    one round: the line on the streets, leg by leg
    /wats/w/<wat>.html     one wat: picture, names, what it is, where it sits

WHAT A PAGE HERE MAY SAY ABOUT A WAT. The words come from the encyclopaedia
with the article, the licence and the revision beside them, or from the
catalogue record, which names its own source. Royal grade is shown where the
Sangha assigned one, because the Sangha assigned it. The order of a round is
the shortest way round and is not a ranking, which is written on the page in
those words. Nothing here pairs a wat with a weekday: the birthday Buddha is a
real tradition and "these nine are for people born on a Tuesday" is not.

Entry point: emit(globals_of_build, data) — hooked in build.py where
build_merit_page() used to be. Emits wats/ + wats.css, copies data/wats.json to
docs/data/wats.json, returns the page count.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

import map_shell                                     # noqa: E402

DATA = ROOT / "data" / "wats.json"
WIKI = ROOT / "data" / "curated" / "wat_wiki.json"

CSS = """/* /wats — the wat rounds. Loaded only by the pages under /wats/. */
.wathero{position:relative;border-radius:1rem;overflow:hidden;margin:0 0 1rem;
  background:#2A1E16}
.wathero img{display:block;width:100%;height:clamp(9rem,34vw,17rem);
  object-fit:cover;opacity:.82}
.wathero .scrim{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(42,30,22,.1) 0%,rgba(42,30,22,.82) 72%)}
.wathero .words{position:absolute;left:0;right:0;bottom:0;padding:.9rem 1rem}
.wathero h1{color:#fff;margin:0;text-shadow:0 1px 6px rgba(0,0,0,.5)}
.wathero p{color:#F6EEE2;margin:.25rem 0 0;font-size:.95rem}
.watcredit{display:inline-block;margin:.3rem 0 0;font-size:.78rem;
  color:#F0E4D2;text-decoration:none;opacity:.9}
.watlede{font-size:1.02rem;margin:.6rem 0}
.watrule{font-weight:600;margin:.2rem 0 1rem}
.watcard{background:#fff;border:1px solid var(--soft);border-radius:.8rem;
  padding:.8rem .9rem;margin:0 0 1rem}
.watcard h2{margin:.1rem 0 .2rem;font-size:1.12rem}
.watmeta{color:var(--muted);margin:.1rem 0 .55rem;font-size:.92rem}
.watmap{display:block;min-width:20rem;margin:.3rem 0}
.wathint{font-size:.9rem;color:var(--muted);margin:.35rem 0}
.watmode{display:inline-block;border-radius:1rem;padding:.05rem .5rem;
  font-size:.8rem;font-weight:700;background:#EFE3CE;color:#5A4527;
  vertical-align:.1rem;margin-right:.35rem}
.watmode.ride{background:#DCE8F3;color:#254A70}
/* The numbers are stops in walking order, never a score. */
ol.watstops{list-style:none;counter-reset:wst;padding-left:0;margin:.5rem 0}
ol.watstops>li{counter-increment:wst;position:relative;
  padding:.3rem 0 .3rem 2.4rem;min-height:1.9rem}
ol.watstops>li::before{content:counter(wst);position:absolute;left:0;top:.28rem;
  width:1.6rem;height:1.6rem;border-radius:50%;background:#C9A227;color:#fff;
  font-weight:700;font-size:.9rem;text-align:center;line-height:1.6rem}
ol.watstops img{width:2.6rem;height:2.6rem;object-fit:cover;border-radius:.3rem;
  float:right;margin:0 0 .2rem .5rem}
.watleg{color:var(--muted);font-size:.85rem}
.watgrid{display:grid;gap:.6rem;
  grid-template-columns:repeat(auto-fill,minmax(13rem,1fr));margin:.5rem 0 1rem}
.watgrid a{display:block;padding:.45rem .55rem;border:1px solid var(--soft);
  border-radius:.5rem;background:#fff;text-decoration:none}
.watdays{background:#fff;border:1px solid var(--soft);border-radius:.8rem;
  padding:.8rem .9rem;margin:0 0 1rem}
.watdays ul{list-style:none;padding-left:0;margin:.5rem 0 0;
  display:grid;gap:.4rem;grid-template-columns:repeat(auto-fill,minmax(12rem,1fr))}
.watdays li{line-height:1.45}
.daydot{display:inline-block;width:.8rem;height:.8rem;border-radius:50%;
  margin-right:.4rem;vertical-align:-.05rem;border:1px solid rgba(0,0,0,.15)}
.watstop{border-top:1px solid var(--soft);padding:.9rem 0 .2rem}
.watstop h3{margin:.1rem 0 .3rem}
.watstop .photo,.watpage .photo{width:100%;max-width:26rem;border-radius:.6rem;
  display:block;margin:.3rem 0}
.phototag{font-size:.8rem;color:var(--muted);margin:.15rem 0 .5rem}
.watsays{background:#FBF6EE;border-left:3px solid #C9A227;border-radius:.3rem;
  padding:.5rem .7rem;margin:.5rem 0}
.watsays p{margin:.2rem 0}
.watsrc{font-size:.8rem;color:var(--muted);margin:.25rem 0 0}
.watfacts{list-style:none;padding-left:0;margin:.4rem 0}
.watfacts li{padding:.12rem 0}
.watnear{font-size:.92rem;color:var(--muted)}
.watnav{display:flex;gap:.6rem;flex-wrap:wrap;margin:1rem 0}
"""


# Five of the 115 credit lines hold a paragraph where a name goes: Wat Chiang
# Man's photographer wrote 607 characters of how he would like his pictures
# handled, and a page that prints the whole thing under the photograph is
# four lines of link text. The licence asks for the photographer, so that is
# what is shown, and the tag links to the file page where the rest of what he
# wrote stands in full.
_TAKEN_BY = re.compile(
    r"(?:photo (?:was )?taken by|photograph(?:ed)? by|image by|by)\s+([^.;,()]{2,60})",
    re.I)


def photographer(name):
    a = re.sub(r"\s+", " ", name or "").strip()
    if len(a) <= 60:
        return a
    m = _TAKEN_BY.search(a)
    if m:
        return m.group(1).strip(" .")
    cut = a[:60]
    return (cut[:cut.rfind(" ")] if " " in cut else cut).rstrip(" ,;") + "…"


def load(path, default):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    bi_text = g["bi_text"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    name_th, name_en, name_text = g["name_th"], g["name_en"], g["name_text"]
    honour_badges = g["honour_badges"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block, breadcrumb_ld = g["share_block"], g["breadcrumb_ld"]
    ad_box, art_one = g["ad_box"], g["art_one"]
    band_pic_file, band_credit = g["band_pic_file"], g["band_credit"]
    PHOTO_FILES, PHOTO_CREDITS = g["PHOTO_FILES"], g["PHOTO_CREDITS"]
    COMMONS_IMAGES, MOAT_POLY = g["COMMONS_IMAGES"], g["MOAT_POLY"]
    PROVINCES = g["PROVINCES"]

    doc = load(DATA, {})
    rounds = doc.get("rounds") or []
    if not rounds:
        return 0
    wiki = load(WIKI, {})
    by_id = {r["id"]: r for p in PROVINCES for r in data[p["key"]]}
    counts = doc.get("counts", {})

    out = DOCS / "wats"
    (out / "w").mkdir(parents=True, exist_ok=True)
    (DOCS / "wats.css").write_text(CSS)
    (DOCS / "data").mkdir(exist_ok=True)
    if DATA.exists():
        shutil.copyfile(DATA, DOCS / "data" / "wats.json")

    head = '<link rel="stylesheet" href="%swats.css">'

    def km(m):
        return "—" if not m else ("%.1f" % (m / 1000.0))

    def wat_href(rec, depth):
        return "%swats/w/%s.html" % ("../" * depth, place_slug(rec))

    def cat_href(rec, depth):
        return "%s%s/p/%s.html" % ("../" * depth, rec["province"], place_slug(rec))

    # ---- pictures --------------------------------------------------------
    def picture(rec, depth, cls="photo"):
        """A photograph of this wat, with the credit the licence asks for.

        Two sources, in this order: the copy downloaded into assets/photos/
        with its credits.json entry, and a Commons file matched to this record
        by name and distance, linked at Commons rather than copied. A wat with
        neither gets no picture — a stand-in photograph of a different wat
        would be the one mistake this whole page is against.
        """
        r_ = "../" * depth
        fname = PHOTO_FILES.get(rec["id"])
        if fname:
            credit = PHOTO_CREDITS.get(rec["id"]) or {}
            by = photographer(credit.get("author"))
            alt = bi_text(
                "รูปถ่าย %s%s" % (name_th(rec),
                                  (" ถ่ายโดย %s" % by) if by else ""),
                "Photograph of %s, a wat in Chiang Mai%s"
                % (name_en(rec), (", by %s" % by) if by else ""))
            img = ('<img class="%s" src="%sphotos/%s" alt="%s" loading="lazy">'
                   % (cls, r_, att(fname), att(alt)))
            tag = ""
            if credit.get("source"):
                tag = ('<p class="phototag">📷 <a href="%s" rel="noopener">%s</a>'
                       ' — %s, via Wikimedia Commons</p>'
                       % (att(credit["source"]),
                          esc(by or "Wikimedia Commons"),
                          esc(credit.get("license") or "")))
            return img + tag
        ci = COMMONS_IMAGES.get(rec["id"])
        if ci and ci.get("thumb"):
            # commons_pool.py copies its matches into our tree (`file`).
            _src = (r_ + ci["file"] if ci.get("file") and (ROOT / "assets" / ci["file"]).exists()
                    else ci["thumb"])
            img = ('<img class="%s" src="%s" alt="%s" loading="lazy">'
                   % (cls, att(_src),
                      att(ci.get("description") or name_text(rec))))
            tag = ('<p class="phototag">📷 <a href="%s" rel="noopener">%s</a>'
                   ' — %s, via Wikimedia Commons</p>'
                   % (att(ci.get("full") or "#"),
                      esc(photographer(ci.get("artist")) or "Wikimedia Commons"),
                      esc(ci.get("licence") or "")))
            return img + tag
        return ""

    def thumb(rec, depth):
        """The same picture at list size, or nothing."""
        r_ = "../" * depth
        fname = PHOTO_FILES.get(rec["id"])
        if fname:
            # alt="" on purpose: the wat's name is the link right beside it, and
            # a second reading of the same name is noise in a screen reader.
            return ('<img src="%sphotos/%s" alt="" loading="lazy">'
                    % (r_, att(fname)))
        ci = COMMONS_IMAGES.get(rec["id"])
        if ci and ci.get("file") and (ROOT / "assets" / ci["file"]).exists():
            _b = "band/" + ci["file"].rsplit("/", 1)[-1]
            return '<img src="%s%s" alt="" loading="lazy">' % (
                r_, att(_b if (ROOT / "assets" / _b).exists() else ci["file"]))
        if ci and ci.get("thumb"):
            return '<img src="%s" alt="" loading="lazy">' % att(ci["thumb"])
        return ""

    # ---- what the encyclopaedia says ------------------------------------
    def says(rec):
        """The wat in words, Thai and English, each with its own credit.

        Three places hold this: the catalogue record's own summary (a Thai lead
        and sometimes a ประวัติ section, from the crawl that cites the article),
        and data/curated/wat_wiki.json, which adds the English lead by the Thai
        article's langlink and the Thai lead for the wats the crawl never
        queued — Wat Phra Singh among them. Each block names its article, its
        licence and the revision it was read at, because the licence asks for
        exactly that.
        """
        a = rec.get("attrs") or {}
        canon = a.get("summary") or {}
        extra = wiki.get(rec["id"]) or {}
        blocks = []

        def credit_line(title, url, licence, rev):
            return ('<p class="watsrc">%s · <a href="%s" rel="noopener">%s</a>'
                    ' — %s%s</p>'
                    % (bi("จากวิกิพีเดีย", "From Wikipedia"), att(url),
                       esc(title), esc(licence or "CC BY-SA 4.0"),
                       (", " + esc(rev)) if rev else ""))

        th = None
        if canon.get("lang") == "th" and canon.get("text"):
            th = {"text": canon["text"], "url": canon.get("url"),
                  "title": canon.get("title"), "license": canon.get("license"),
                  "revision": ""}
        elif (extra.get("th") or {}).get("text"):
            th = extra["th"]
        if th:
            body = ['<p lang="th" class="th">%s</p>' % esc(th["text"])]
            for sec in (canon.get("sections") or []):
                if sec.get("kind") in ("history", "heritage") and sec.get("text"):
                    body.append('<p lang="th" class="th"><strong>%s</strong> %s</p>'
                                % (esc(sec.get("heading") or ""),
                                   esc(sec["text"][:900])))
            blocks.append('<div class="watsays">%s%s</div>'
                          % ("".join(body),
                             credit_line(th.get("title") or "", th.get("url") or "#",
                                         th.get("license"), th.get("revision"))))
        en = extra.get("en") or {}
        if en.get("text"):
            blocks.append('<div class="watsays"><p lang="en" class="en">%s</p>%s</div>'
                          % (esc(en["text"]),
                             credit_line(en.get("title") or "", en.get("url") or "#",
                                         en.get("license"), en.get("revision"))))
        elif th:
            blocks.append('<p class="watsrc en" lang="en">%s</p>'
                          % esc("The encyclopaedia entry for this wat is in Thai "
                                "only; it is above, with its article."))
        return "".join(blocks)

    def facts(rec):
        """What the record itself holds, each line only where it is filled."""
        a = rec.get("attrs") or {}
        rows = []
        if a.get("sect") and a["sect"] != "unknown":
            rows.append((bi("นิกาย", "Order"), esc(a["sect"])))
        if a.get("heritage"):
            rows.append((bi("ทะเบียนโบราณสถาน", "Heritage register"),
                         esc(a["heritage"])))
        if rec.get("address"):
            rows.append((bi("ที่ตั้ง", "Address"), esc(rec["address"])))
        if a.get("tambon"):
            rows.append((bi("ตำบล", "Tambon"), esc(a["tambon"])))
        if rec.get("phone"):
            rows.append((bi("โทร", "Phone"),
                         '<a href="tel:%s">%s</a>' % (att(rec["phone"]),
                                                      esc(rec["phone"]))))
        if not rows:
            return ""
        return ('<ul class="watfacts">%s</ul>'
                % "".join("<li><strong>%s</strong> %s</li>" % (k, v)
                          for k, v in rows))

    # ---- the map ---------------------------------------------------------
    def round_map(rnd, depth, full=False):
        """The round drawn on the streets it is walked along.

        Every leg carries the line `Graph.route` returned, so the drawing bends
        round a block the way a person does. The old map joined the nine stops
        with straight lines and said so in the caption, which is how a reader
        ended up with a line through Wat Phra Singh's wall and the moat.
        """
        stops = rnd.get("stops") or []
        legs = rnd.get("foot_legs") or []
        pts = [(s["lat"], s["lng"]) for s in stops]
        line_pts = [p for lg in legs for p in (lg.get("line") or [])]
        allp = pts + [tuple(p) for p in line_pts]
        import math
        lats = [p[0] for p in allp]
        lngs = [p[1] for p in allp]
        span = max(max(lats) - min(lats),
                   (max(lngs) - min(lngs))
                   * math.cos(math.radians(sum(lats) / len(lats))), 1e-4)
        pad = span * 0.12
        n, s_, w, e = max(lats) + pad, min(lats) - pad, min(lngs) - pad, max(lngs) + pad
        kx = math.cos(math.radians((n + s_) / 2))
        W = 720.0
        H = max(240.0, min(620.0, W * ((n - s_) / ((e - w) * kx or 1e-9))))

        def X(lng):
            return (lng - w) / (e - w) * W

        def Y(lat):
            return (n - lat) / (n - s_) * H

        label = bi_text(
            "แผนที่เส้นทางไหว้พระ ๙ วัด %s เส้นทางเดินจริงตามถนน ระยะราว %s "
            "กิโลเมตร จุดที่ ๑ ถึง ๙ คือลำดับที่เดิน"
            % (rnd.get("area_th", ""), km(rnd.get("foot_m"))),
            "Map of a nine-wat round %s, drawn along the streets it is walked "
            "on, about %s km. Points 1 to 9 are the order of walking."
            % (rnd.get("area_en", ""), km(rnd.get("foot_m"))))
        svg = ['<svg viewBox="0 0 %.0f %.0f" width="100%%" class="watmap" '
               'role="img" aria-label="%s">' % (W, H, att(label)),
               '<rect class="mdmap-bg" width="%.0f" height="%.0f" fill="#FBF6EE"/>'
               % (W, H)]
        if MOAT_POLY:
            mlat = [p[0] for p in MOAT_POLY]
            mlng = [p[1] for p in MOAT_POLY]
            if min(mlat) < n and max(mlat) > s_ and min(mlng) < e and max(mlng) > w:
                ring = " ".join("%.1f,%.1f" % (X(p[1]), Y(p[0])) for p in MOAT_POLY)
                svg.append('<polygon points="%s" fill="none" stroke="#2a78d6" '
                           'stroke-width="2" stroke-dasharray="5 4" opacity=".55">'
                           '<title>คูเมืองเชียงใหม่ · the old city moat</title>'
                           '</polygon>' % ring)
        for i, lg in enumerate(legs):
            line = lg.get("line")
            if not line or len(line) < 2:
                continue
            # The walk in from the pin to the street, drawn thin and grey — the
            # metres beside the leg include it, and /plan.html draws the same
            # stub in the same colour for the same reason.
            for pin, end in ((stops[i], line[0]),
                             (stops[(i + 1) % len(stops)], line[-1])):
                svg.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                           'stroke="#8a7a62" stroke-width="2" '
                           'stroke-dasharray="3 3" opacity=".7"/>'
                           % (X(pin["lng"]), Y(pin["lat"]), X(end[1]), Y(end[0])))
            d = " ".join("%.1f,%.1f" % (X(p[1]), Y(p[0])) for p in line)
            svg.append('<polyline points="%s" fill="none" stroke="#C9A227" '
                       'stroke-width="4" stroke-linejoin="round" '
                       'stroke-linecap="round" opacity=".85"/>' % d)
        for i, st in enumerate(stops, 1):
            cx, cy = X(st["lng"]), Y(st["lat"])
            rec = by_id.get(st["id"])
            nm = name_text(rec) if rec else (st.get("name") or "")
            # A stop is a numbered wat and stays one size; the line is metres
            # and grows with the ground.
            svg.append('<g data-mdpin="%.1f,%.1f">' % (cx, cy))
            svg.append('<circle cx="%.1f" cy="%.1f" r="12" fill="#C9A227" '
                       'stroke="#7A5C00" stroke-width="1.5"><title>%s</title>'
                       '</circle>' % (cx, cy, att("%d. %s" % (i, nm))))
            svg.append('<text x="%.1f" y="%.1f" text-anchor="middle" '
                       'font-size="12" font-weight="700" fill="#fff">%d</text>'
                       % (cx, cy + 4, i))
            svg.append('</g>')
        svg.append("</svg>")
        return map_shell.mount(
            "watmap-%s" % att(rnd.get("slug") or "x"), "".join(svg),
            lat=(n + s_) / 2, lng=(w + e) / 2,
            mpu=(e - w) * 111320.0 * kx / W, full=full)

    def wat_map(rec, depth):
        import math
        lat, lng = rec["lat"], rec["lng"]
        W, H = 720.0, 360.0
        span = 0.006
        n, s_, w, e = lat + span / 2, lat - span / 2, lng - span, lng + span
        kx = math.cos(math.radians(lat))
        svg = ['<svg viewBox="0 0 %.0f %.0f" width="100%%" class="watmap" '
               'role="img" aria-label="%s">'
               % (W, H, att(bi_text("แผนที่ที่ตั้ง %s" % name_th(rec),
                                    "Map of where %s stands" % name_en(rec)))),
               '<rect class="mdmap-bg" width="%.0f" height="%.0f" fill="#FBF6EE"/>'
               % (W, H),
               '<g data-mdpin="%.1f,%.1f"><circle cx="%.1f" cy="%.1f" r="11" '
               'fill="#C9A227" stroke="#7A5C00" stroke-width="1.5">'
               '<title>%s</title></circle></g>'
               % (W / 2, H / 2, W / 2, H / 2, att(name_text(rec))),
               "</svg>"]
        return map_shell.mount("watmap-one-%s" % att(place_slug(rec)),
                               "".join(svg), lat=lat, lng=lng, zoom=16,
                               mpu=(e - w) * 111320.0 * kx / W)

    # ---- the rounds ------------------------------------------------------
    def mode_chip(rnd):
        if rnd.get("mode") == "foot":
            return ('<span class="watmode">%s</span>'
                    % bi("เดินได้", "on foot"))
        return ('<span class="watmode ride">%s</span>'
                % bi("ขี่รถ", "by scooter"))

    def stop_rows(rnd, depth):
        rows = []
        stops = rnd.get("stops") or []
        legs = rnd.get("foot_legs") or []
        for i, st in enumerate(stops):
            rec = by_id.get(st["id"])
            if rec:
                nm = ('<a href="%s">%s</a>%s'
                      % (att(wat_href(rec, depth)), name_bi(rec),
                         honour_badges(rec)))
                pic = thumb(rec, depth)
            else:
                nm, pic = esc(st.get("name") or ""), ""
            nxt = legs[i] if i < len(legs) else {}
            to = stops[(i + 1) % len(stops)]
            to_rec = by_id.get(to["id"])
            # One language per half. name_text() returns the pair, so putting it
            # inside a Thai sentence read "ถึง วัดดวงดี · Wat Duang Di · 388 m
            # on to วัดดวงดี · Wat Duang Di" — both names twice, in both halves.
            leg = ('<br><span class="watleg">%s</span>'
                   % bi("เดินต่อ %s ถึง %s"
                        % (metres_plain(nxt.get("m"), "th"),
                           name_th(to_rec) if to_rec else (to.get("name") or "")),
                        "%s on to %s"
                        % (metres_plain(nxt.get("m"), "en"),
                           name_en(to_rec) if to_rec else (to.get("name") or ""))))
            rows.append("<li>%s%s%s</li>" % (pic, nm, leg))
        return "".join(rows)

    def metres_plain(m, lang):
        if m is None:
            return "—"
        if m < 1000:
            return "%d ม." % m if lang == "th" else "%d m" % m
        return ("%.1f กม." % (m / 1000.0)) if lang == "th" else ("%.1f km" % (m / 1000.0))

    def plan_pill(rnd, depth):
        keys = []
        for st in rnd.get("stops") or []:
            rec = by_id.get(st["id"])
            if rec:
                keys.append("%s:%s" % (rec["province"], place_slug(rec)))
        if not keys:
            return ""
        return ('<p><a class="pill dark" href="%splan.html?stops=%s">%s</a></p>'
                % ("../" * depth, att(",".join(keys)),
                   bi("เปิดในตัววางแผน ทีละช่วง",
                      "Open in the planner, leg by leg")))

    def walk_vs_ride(rnd):
        walk, ride = rnd.get("foot_m"), rnd.get("ride_m")
        if walk and ride and ride > walk * 1.05:
            return ('<p class="wathint">%s</p>'
                    % bi("เดินใกล้กว่าขี่รถ เพราะถนนเดินรถทางเดียวบังคับรถ "
                         "ไม่บังคับคนเดิน",
                         "The walk is shorter than the ride — one-way streets "
                         "bind a scooter and not a person on foot."))
        return ""

    def round_card(rnd):
        return (
            '<div class="watcard" id="%s"><h2>%s%s</h2>'
            '<p class="watmeta">%s</p>%s%s'
            '<ol class="watstops">%s</ol>'
            '<p><a class="pill" href="%s.html">%s</a></p>%s</div>'
            % (att(rnd.get("slug", "")), mode_chip(rnd),
               bi(rnd.get("th", ""), rnd.get("en", "")),
               bi("เดิน %s กม. · ขี่รถ %s กม."
                  % (km(rnd.get("foot_m")), km(rnd.get("ride_m"))),
                  "%s km on foot · %s km riding"
                  % (km(rnd.get("foot_m")), km(rnd.get("ride_m")))),
               round_map(rnd, 1), walk_vs_ride(rnd),
               stop_rows(rnd, 1), att(rnd.get("slug", "")),
               bi("เปิดรอบนี้ ทีละวัด", "Open this round, wat by wat"),
               plan_pill(rnd, 1)))

    # ---- the index -------------------------------------------------------
    hero_pic = art_one(topic="wat", place="cm", local=True, key="wats-hero")
    hero = ""
    if hero_pic:
        hero = (
            '<div class="wathero"><img src="../%s" alt="%s" loading="eager">'
            '<div class="scrim"></div><div class="words"><h1>%s</h1><p>%s</p>%s'
            '</div></div>'
            % (att(band_pic_file(hero_pic)),
               att(bi_text("ภาพวัดในเชียงใหม่ โดย %s"
                           % (hero_pic.get("artist") or "ช่างภาพ"),
                           "A wat in Chiang Mai, photographed by %s"
                           % (hero_pic.get("artist") or "an unnamed photographer"))),
               bi("ไหว้พระ ๙ วัด", "Nine wats, one round"),
               bi("%d รอบ · %d วัดในเขตเมือง · เรียงตามถนนจริง"
                  % (len(rounds), counts.get("wats_placed", 0)),
                  "%d rounds · %d wats in the city · ordered along the real streets"
                  % (len(rounds), counts.get("wats_placed", 0))),
               ('<a class="watcredit" href="../pictures.html">📷 %s</a>'
                % esc(band_credit(hero_pic.get("artist") or "")))
               if hero_pic.get("artist") else ""))
    else:
        hero = "<h1>%s</h1>" % bi("ไหว้พระ ๙ วัด", "Nine wats, one round")

    lede = ('<p class="watlede">%s</p><p class="watrule">%s</p>'
            % (bi(doc.get("practice_th", ""), doc.get("practice_en", "")),
               bi(doc.get("not_a_ranking_th", ""), doc.get("not_a_ranking_en", ""))))
    # Nan, 2026-09-28: a stamp for each wat, collected in the Mot Dang LINE chat.
    import linedoor
    if linedoor.ON:
        lede += ('<p class="watrule"><a href="%s" rel="noopener">%s</a></p>'
                 % (att(linedoor.url(linedoor.PASSPORT + "wats")),
                    bi("เก็บตราประทับทุกวัดใน LINE — ส่งตำแหน่งที่แต่ละวัด",
                       "Collect a stamp at each wat in LINE: share your location at each one")))

    days = "".join(
        '<li><span class="daydot" style="background:%s"></span>%s<br>'
        '<span class="tinynote">%s</span></li>'
        % (att(d.get("hex", "#ccc")), bi(d.get("th", ""), d.get("en", "")),
           esc(d.get("buddha_th", "")) + " · " + esc(d.get("buddha_en", "")))
        for d in doc.get("birthday_buddhas", []))
    daystrip = ""
    if days:
        daystrip = (
            '<div class="watdays"><h2>%s</h2><p>%s</p><ul>%s</ul></div>'
            % (bi("พระประจำวันเกิด — ไว้มองหาเวลาไปถึง",
                  "The Buddha of your birth weekday — what to look for"),
               bi("ที่วัดไหนก็มองหาได้ ไม่ได้ผูกกับวัดใดวัดหนึ่งหรือรอบใด",
                  "Look for it at any wat. It is not tied to a particular wat "
                  "or to any of the rounds below."),
               days))

    # Every wat, grouped by where it stands — a name-dump sorted ก→ฮ tells a
    # reader nothing about which of these are near each other.
    quarters = [("ในเวียง", "Inside the walls"),
                ("นอกเวียงด้านเหนือ", "North of the walls"),
                ("นอกเวียงด้านตะวันออก", "East of the walls"),
                ("นอกเวียงด้านใต้", "South of the walls"),
                ("นอกเวียงด้านตะวันตก", "West of the walls")]
    where = {}
    for w in doc.get("wats") or []:
        rec = by_id.get(w["id"])
        if not rec:
            continue
        if w.get("inside_walls"):
            k = 0
        else:
            import math
            mlat = sum(p[0] for p in MOAT_POLY) / len(MOAT_POLY) if MOAT_POLY else w["lat"]
            mlng = sum(p[1] for p in MOAT_POLY) / len(MOAT_POLY) if MOAT_POLY else w["lng"]
            dlat = w["lat"] - mlat
            dlng = (w["lng"] - mlng) * math.cos(math.radians(mlat))
            if abs(dlat) >= abs(dlng):
                k = 1 if dlat > 0 else 3
            else:
                k = 2 if dlng > 0 else 4
        where.setdefault(k, []).append((rec, w))

    all_wats = []
    for k, (th, en) in enumerate(quarters):
        group = sorted(where.get(k, []), key=lambda x: name_text(x[0]))
        if not group:
            continue
        cells = []
        for rec, w in group:
            on = "" if w.get("on_a_round") else (
                ' <span class="watleg">%s</span>'
                % bi("ยังไม่อยู่ในรอบไหน", "not on a round"))
            cells.append('<a href="w/%s.html">%s%s</a>'
                         % (att(place_slug(rec)), name_bi(rec), on))
        all_wats.append('<h3>%s <span class="count">(%d)</span></h3>'
                        '<div class="watgrid">%s</div>'
                        % (bi(th, en), len(group), "".join(cells)))

    how = (
        '<div class="soiabout"><h2>%s</h2><p>%s</p><p>%s</p>'
        '<p class="tinynote">%s</p></div>'
        % (bi("รอบพวกนี้มาจากไหน", "Where these rounds come from"),
           bi("มดเอาวัด %d แห่งในเขตที่มีข้อมูลถนน จัดเป็นรอบละ ๙ วัด "
              "แล้วหาลำดับที่สั้นที่สุดจริง ๆ ด้วยระยะทางบนถนน ทั้งเดินและขี่รถ "
              "วัดหนึ่งอยู่ได้รอบเดียว รอบที่เดินได้อยู่บนสุด"
              % counts.get("wats_placed", 0),
              "We take the %d wats inside the area we hold road data for, group "
              "them into rounds of nine, and solve each round exactly: the "
              "shortest closed order by distance along the streets, walking and "
              "riding measured separately. No wat is on two rounds. The rounds "
              "you can walk lead." % counts.get("wats_placed", 0)),
           bi("รอบทุกรอบวาดตามถนนที่เดินจริง ไม่ใช่เส้นตรงลากผ่านตึก",
              "Each round is drawn along the streets it is walked on, not as "
              "straight lines between the stops."),
           bi("ในเขตนี้มี %d รายการอยู่ใต้หมวดวัด — ตัดออก %d รายการที่ไม่ใช่วัด "
              "(ศาล เทวาลัย โบสถ์ วิหารที่อยู่ในวัดอื่น) %d รายการที่ทะเบียนปักหมุด "
              "ไว้กลางตำบลไม่ใช่หน้าวัด %d รายการที่มีแต่ในแหล่งอื่นไม่มีในแผนที่ "
              "และรวมการปักหมุดซ้ำ %d ครั้ง"
              % (counts.get("under_the_lens", 0),
                 counts.get("not_named_as_a_wat", 0),
                 counts.get("at_a_centroid", 0),
                 counts.get("only_in_another_source", 0),
                 counts.get("second_mappings_folded", 0)),
              "%d records sit under the wat lens inside this area. Set aside: %d "
              "that are not wats — shrines, a Hindu temple, a Christian hall, "
              "buildings standing inside another wat; %d placed by a register at "
              "the middle of a tambon rather than at their own gate; %d held only "
              "by a source other than the map. %d second mappings of a wat "
              "already listed were folded."
              % (counts.get("under_the_lens", 0),
                 counts.get("not_named_as_a_wat", 0),
                 counts.get("at_a_centroid", 0),
                 counts.get("only_in_another_source", 0),
                 counts.get("second_mappings_folded", 0)))))

    body = (
        '%s%s%s%s<h2>%s <span class="count">(%d)</span></h2>%s'
        '<h2>%s <span class="count">(%d)</span></h2>%s%s%s'
        % (hero, lede, ad_box("wats/", 1), daystrip,
           bi("รอบ ๙ วัด", "The rounds"), len(rounds),
           "".join(round_card(r) for r in rounds),
           bi("วัดทั้งหมดในเขตเมือง", "Every wat in the city area"),
           counts.get("wats_placed", 0), "".join(all_wats), how,
           share_block(BASE + "wats/", "ไหว้พระ ๙ วัด มดแดง")))
    (out / "index.html").write_text(page(
        "ไหว้พระ ๙ วัด", body, 1,
        crumbs='<a href="../index.html">%s</a> › %s'
               % (bi("หน้าแรก", "Home"), bi("ไหว้พระ ๙ วัด", "Nine wats")),
        path="wats/",
        desc="ไหว้พระ ๙ วัด เชียงใหม่ — %d รอบ เรียงตามถนนจริง วัด %d แห่ง "
             "พร้อมรูปและประวัติ · Nine-wat rounds in Chiang Mai, ordered along "
             "the real streets, with pictures and what each wat is."
             % (len(rounds), counts.get("wats_placed", 0)),
        extra_head=(head % "../")
        + breadcrumb_ld([("หน้าแรก", BASE), ("ไหว้พระ ๙ วัด", BASE + "wats/")])))
    pages = 1

    # ---- one page per round ---------------------------------------------
    for i, rnd in enumerate(rounds):
        stops = rnd.get("stops") or []
        legs = rnd.get("foot_legs") or []
        secs = []
        for j, st in enumerate(stops):
            rec = by_id.get(st["id"])
            if not rec:
                continue
            nxt = legs[j] if j < len(legs) else {}
            to = stops[(j + 1) % len(stops)]
            to_rec = by_id.get(to["id"])
            secs.append(
                '<div class="watstop" id="stop-%d"><h3>%d. %s%s</h3>%s%s%s'
                '<p><a href="%s">%s</a> · <a href="%s">%s</a></p>'
                '<p class="watleg">%s</p></div>'
                % (j + 1, j + 1, name_bi(rec), honour_badges(rec),
                   picture(rec, 1), facts(rec), says(rec),
                   att(wat_href(rec, 1)), bi("หน้าวัดนี้", "This wat’s page"),
                   att(cat_href(rec, 1)),
                   bi("ในสารบัญ (เวลา เบอร์ ใกล้เคียง)",
                      "In the directory — hours, phone, what is near"),
                   bi("ช่วงต่อไป %s ถึง %s"
                      % (metres_plain(nxt.get("m"), "th"),
                         name_th(to_rec) if to_rec else ""),
                      "Next leg: %s on to %s"
                      % (metres_plain(nxt.get("m"), "en"),
                         name_en(to_rec) if to_rec else ""))))
        nav = []
        if i:
            nav.append('<a class="pill" href="%s.html">← %s</a>'
                       % (att(rounds[i - 1]["slug"]),
                          bi(rounds[i - 1]["area_th"], rounds[i - 1]["area_en"])))
        if i + 1 < len(rounds):
            nav.append('<a class="pill" href="%s.html">%s →</a>'
                       % (att(rounds[i + 1]["slug"]),
                          bi(rounds[i + 1]["area_th"], rounds[i + 1]["area_en"])))
        title = bi_text("ไหว้พระ ๙ วัด %s" % rnd.get("area_th", ""),
                        "Nine wats, %s" % rnd.get("area_en", ""))
        rbody = (
            '<h1>%s%s</h1><p class="watmeta">%s</p>%s%s%s'
            '<div class="watnav">%s<a class="pill" href="./">%s</a></div>%s%s'
            % (mode_chip(rnd), bi(rnd.get("th", ""), rnd.get("en", "")),
               bi("เดิน %s กม. · ขี่รถ %s กม. · ๙ วัด"
                  % (km(rnd.get("foot_m")), km(rnd.get("ride_m"))),
                  "%s km on foot · %s km riding · nine wats"
                  % (km(rnd.get("foot_m")), km(rnd.get("ride_m")))),
               # Not full=True: a one-finger pan belongs on a page that IS a
               # map, and this one carries nine wats under it to scroll to.
               round_map(rnd, 1), walk_vs_ride(rnd),
               plan_pill(rnd, 1), "".join(nav),
               bi("ทุกรอบ", "All the rounds"), "".join(secs),
               share_block(BASE + "wats/" + rnd["slug"] + ".html",
                           "ไหว้พระ ๙ วัด มดแดง")))
        (out / (rnd["slug"] + ".html")).write_text(page(
            title, rbody, 1,
            crumbs='<a href="../index.html">%s</a> › <a href="./">%s</a> › %s'
                   % (bi("หน้าแรก", "Home"), bi("ไหว้พระ ๙ วัด", "Nine wats"),
                      bi(rnd.get("area_th", ""), rnd.get("area_en", ""))),
            path="wats/" + rnd["slug"] + ".html",
            desc="ไหว้พระ ๙ วัด %s — เดิน %s กม. เรียงตามถนนจริง · A nine-wat "
                 "round %s, %s km on foot, ordered along the real streets."
                 % (rnd.get("area_th", ""), km(rnd.get("foot_m")),
                    rnd.get("area_en", ""), km(rnd.get("foot_m"))),
            extra_head=(head % "../")
            + breadcrumb_ld([("หน้าแรก", BASE),
                             ("ไหว้พระ ๙ วัด", BASE + "wats/"),
                             (rnd.get("area_th", ""),
                              BASE + "wats/" + rnd["slug"] + ".html")])))
        pages += 1

    # ---- one page per wat ------------------------------------------------
    round_of = {}
    for rnd in rounds:
        for j, st in enumerate(rnd.get("stops") or []):
            round_of[st["id"]] = (rnd, j)

    from math import cos, radians

    def near(w, n=3):
        def d(a, b):
            return ((a["lat"] - b["lat"]) ** 2
                    + ((a["lng"] - b["lng"]) * cos(radians(a["lat"]))) ** 2) ** .5
        others = [q for q in (doc.get("wats") or []) if q["id"] != w["id"]]
        others.sort(key=lambda q: d(w, q))
        return others[:n]

    for w in doc.get("wats") or []:
        rec = by_id.get(w["id"])
        if not rec:
            continue
        rnd, pos = round_of.get(w["id"], (None, None))
        on = ""
        if rnd is not None:
            on = ('<p>%s</p>'
                  % bi('อยู่ในรอบ <a href="../%s.html">%s</a> — จุดที่ %d'
                       % (att(rnd["slug"]), rnd["th"], pos + 1),
                       'On the round <a href="../%s.html">%s</a>, stop %d'
                       % (att(rnd["slug"]), rnd["en"], pos + 1), raw=True))
        else:
            on = ('<p class="watleg">%s</p>'
                  % bi("ยังไม่อยู่ในรอบไหน — วัดที่ใกล้กันพอจะครบ ๙ วัดถูกจัดไปแล้ว",
                       "Not on a round: the wats close enough to make nine are "
                       "already on one."))
        others = []
        for q in near(w):
            qr = by_id.get(q["id"])
            if qr:
                others.append('<a href="%s.html">%s</a>'
                              % (att(place_slug(qr)), name_bi(qr)))
        wbody = (
            '<h1>%s%s</h1>%s%s%s%s'
            '<p><a href="%s">%s</a></p>'
            '<p class="watnear">%s %s</p>%s%s'
            % (name_bi(rec), honour_badges(rec, small=False),
               picture(rec, 2), facts(rec), says(rec), on,
               att(cat_href(rec, 2)),
               bi("ในสารบัญ — เวลา เบอร์ ของใกล้เคียง",
                  "In the directory — hours, phone, what is near"),
               bi("วัดที่ใกล้ที่สุด", "Nearest wats") + " — ",
               " · ".join(others),
               wat_map(rec, 2),
               share_block(BASE + "wats/w/" + place_slug(rec) + ".html",
                           name_text(rec))))
        (out / "w" / (place_slug(rec) + ".html")).write_text(page(
            name_text(rec), wbody, 2,
            crumbs='<a href="../../index.html">%s</a> › <a href="../">%s</a> › %s'
                   % (bi("หน้าแรก", "Home"), bi("ไหว้พระ ๙ วัด", "Nine wats"),
                      name_bi(rec)),
            path="wats/w/" + place_slug(rec) + ".html",
            desc=bi_text("%s — วัดในเชียงใหม่ ที่ตั้ง รูป และประวัติเท่าที่มีแหล่งอ้างอิง"
                         % name_th(rec),
                         "%s, a wat in Chiang Mai: where it stands, a picture, "
                         "and what is recorded about it." % name_en(rec)),
            extra_head=(head % "../../")
            + breadcrumb_ld([("หน้าแรก", BASE),
                             ("ไหว้พระ ๙ วัด", BASE + "wats/"),
                             (name_text(rec),
                              BASE + "wats/w/" + place_slug(rec) + ".html")])))
        pages += 1

    return pages
