#!/usr/bin/env python3
"""commons_layer.py — Commons photographs of the north, strung through the site.

importers/commons_pool.py chooses, tags and fetches the pictures into
data/curated/commons_pool.json + assets/site/ + assets/band/. build.py adds them
to SITE_ART (so every art() caller draws from them) and this module puts them
where a picture can stand in for a sentence:

  around(r)           a place page: pictures OF it, then the nearest ones
                      around it, each a link to the place it shows
  net_pics(key, ...)  a net: pictures of its jewels, then of its subject
  jewel_thumb(pid)    one small picture for a jewel's row in a net
  festival_pics(f)    a festival page: pictures of that festival or its venue
  month_pics(m)       the festivals hub: pictures taken in that month
  CSS                 appended to style.css by build.py

Every strip carries its own credit line: photographer, licence, a link to the
file. The tiles are the linked-image formula — picture, scrim, spacer, words —
with an <img loading="lazy"> as the picture layer, so a strip below the fold
costs nothing until it is scrolled to.

bind(data, place_href) is called once per build, after PLACE_HREF.
"""
import json
import math
import re
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POOL = ROOT / "data" / "curated" / "commons_pool.json"
ASSETS = ROOT / "assets"

CSS = """
/* ---- commons pictures: tiles are picture · scrim · spacer · words ---- */
.cpics{margin:1rem 0}
.cpics h2{font-size:1rem;margin:0 0 .4rem}
.cpics .row{display:grid;grid-template-columns:repeat(auto-fill,minmax(9.5rem,1fr));gap:.4rem}
.cpics.big .row{grid-template-columns:repeat(auto-fill,minmax(14rem,1fr))}
.cpics a.shot{position:relative;display:block;border-radius:.6rem;overflow:hidden;background:#e9e2d6;
  color:#fff;text-decoration:none}
.cpics .bg{position:absolute;inset:0}
.cpics .bg img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s}
.cpics a.shot:hover .bg img{transform:scale(1.04)}
.cpics .scrim{position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(20,12,4,.72))}
.cpics .sp{display:block;padding-top:68%}
.cpics.big .sp{padding-top:62%}
.cpics .tx{position:absolute;left:.45rem;right:.45rem;bottom:.35rem;font-size:.8rem;line-height:1.25;
  text-shadow:0 1px 2px rgba(0,0,0,.6);display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:4;
  overflow:hidden}
.cpics .tx .d{display:block;font-size:.72rem;opacity:.85}
.cpics .cred{font-size:.72rem;color:var(--muted,#776);margin:.35rem 0 0;line-height:1.45}
.cpics .cred a{color:inherit}
.net .jthumb{float:right;width:3.2rem;height:2.4rem;object-fit:cover;border-radius:.35rem;margin:0 0 .2rem .5rem}
.net li::after{content:"";display:block;clear:both}
@media (prefers-reduced-motion:reduce){.cpics a.shot:hover .bg img{transform:none}}
"""

_PICKS = []
_GRID = defaultdict(list)
_OF = defaultdict(list)
_BY_MONTH = defaultdict(list)
_REC = {}
_HREF = {}
_USED = defaultdict(int)
CELL = 0.01


def load():
    if _PICKS:
        return _PICKS
    try:
        picks = json.loads(POOL.read_text(encoding="utf-8")).get("picks", [])
    except (OSError, ValueError):
        return _PICKS
    for p in picks:
        if not p.get("usable") or not p.get("file"):
            continue
        if not (ASSETS / p["file"]).exists():
            continue
        _PICKS.append(p)
        if p.get("lat") is not None:
            _GRID[(int(p["lat"] / CELL), int(p["lng"] / CELL))].append(p)
        for pid in p.get("places") or []:
            _OF[pid].append(p)
        if p.get("month") and "people" not in p.get("topic", []) and "elsewhere" not in p.get("place", []):
            _BY_MONTH[p["month"]].append(p)
    return _PICKS


def bind(data, place_href):
    load()
    _REC.clear()
    for recs in data.values():
        for r in recs:
            _REC[r["id"]] = r
    _HREF.clear()
    _HREF.update(place_href)


def picks():
    return list(load())


def _band(p):
    b = ASSETS / "band" / (p["slug"] + ".jpg")
    return ("band/" if b.exists() else "site/") + p["slug"] + ".jpg"


def _km(a1, o1, a2, o2):
    r = 6371.0
    p1, p2 = math.radians(a1), math.radians(a2)
    dp, dl = math.radians(a2 - a1), math.radians(o2 - o1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def near(lat, lng, km, n, avoid=(), people=False):
    load()
    reach = int(km / (111 * CELL)) + 1
    k0 = (int(lat / CELL), int(lng / CELL))
    rows = []
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            for p in _GRID.get((k0[0] + dy, k0[1] + dx), ()):
                if p["slug"] in avoid or (not people and "people" in p.get("topic", [])):
                    continue
                d = _km(lat, lng, p["lat"], p["lng"])
                if d <= km:
                    rows.append((d, p))
    rows.sort(key=lambda x: (x[0], x[1]["slug"]))
    out, seen_art = [], defaultdict(int)
    for d, p in rows:
        # one photographer's burst at one corner is one picture, not four
        if seen_art[p.get("artist")] >= 2:
            continue
        seen_art[p.get("artist")] += 1
        out.append((d, p))
        if len(out) >= n:
            break
    return out


def of_place(pid):
    load()
    return list(_OF.get(pid, ()))


def _short(s, n):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    s = re.sub(r"^(this is a photo of a monument in thailand identified by the id.*)$", "", s, flags=re.I)
    if len(s) <= n:
        return s
    cut = s[:n - 1].rstrip()
    if " " in cut[n // 2:]:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:·-") + "…"


def _artist(a):
    a = re.sub(r"\s*\(.*?\)\s*", " ", a or "").strip()
    a = re.split(r"\s+(?:Own work|Attribution|CC[- ]BY|https?://)", a)[0].strip()
    return _short(a, 34) or "Wikimedia Commons"


def credit_line(ps, h):
    bi, esc, att = h["bi"], h["esc"], h["att"]
    seen, bits = set(), []
    for p in ps:
        key = (p.get("artist"), p.get("licence"))
        if p.get("artist") == "NaN Peacock" or key in seen:
            continue
        seen.add(key)
        bits.append('<a href="%s" rel="noopener">%s</a> (%s)' % (
            att(p.get("page") or "#"), esc(_artist(p.get("artist"))), esc(p.get("licence") or "")))
    if not bits:
        return ""
    return '<p class="cred">%s %s · %s</p>' % (
        bi("ภาพ:", "Photos:"), " · ".join(bits), bi("ผ่าน Wikimedia Commons", "via Wikimedia Commons"))


def tile(p, h, base, here_id=None, words=None, sub=None):
    """One picture as a link. To the place it shows when it shows a listed one."""
    esc, att = h["esc"], h["att"]
    pid = next((x for x in (p.get("places") or []) if x in _HREF and x != here_id), None)
    if pid:
        href = base + _HREF[pid] + ".html"
        rec = _REC.get(pid)
        text = words or (h["name_bi"](rec) if rec else esc(_short(p.get("description"), 60)))
    else:
        href = p.get("page") or "#"
        text = words or esc(_short(p.get("description"), 60))
    alt = att(_short(p.get("description"), 160))
    _USED[p["slug"]] += 1
    return ('<a class="shot" href="%s"%s><span class="bg"><img src="%s%s" alt="%s" loading="lazy" '
            'decoding="async"></span><span class="scrim"></span><span class="sp"></span>'
            '<span class="tx">%s%s</span></a>' % (
                att(href), "" if pid else ' rel="noopener"', base, att(_band(p)), alt, text,
                ('<span class="d">%s</span>' % sub) if sub else ""))


def strip(rows, h, base, title=None, cls="", anchor=None):
    """rows: [(pick, words or None, sub or None, here_id)]"""
    if not rows:
        return ""
    tiles = "".join(tile(p, h, base, here_id=hid, words=w, sub=s) for p, w, s, hid in rows)
    head = ("<h2>%s</h2>" % title) if title else ""
    return '<section class="cpics%s"%s>%s<div class="row">%s</div>%s</section>' % (
        (" " + cls) if cls else "", (' id="%s"' % anchor) if anchor else "", head, tiles,
        credit_line([r[0] for r in rows], h))


def _dist(km, h):
    if km < 1:
        m = int(round(km * 1000 / 50.0) * 50) or 50
        return h["bi"]("%d ม." % m, "%d m" % m)
    return h["bi"]("%.1f กม." % km, "%.1f km" % km)


def around(r, h, base="../../", main_title=None, n=4, km=0.9):
    """Pictures of this place (other than the one leading the page), then the nearest."""
    if r.get("lat") is None and not of_place(r["id"]):
        return ""
    rows, avoid = [], set()
    for p in of_place(r["id"]):
        if p.get("title") == main_title:
            continue
        rows.append((p, h["esc"](_short(p.get("description"), 60)) or None, h["bi"]("ที่นี่", "here"), r["id"]))
        avoid.add(p["slug"])
        if len(rows) >= 2:
            break
    names = [x.lower() for x in (r.get("nameEn"), r.get("name"), r.get("nameTh")) if x and len(x) >= 6]
    if r.get("lat") is not None:
        for d, p in near(r["lat"], r["lng"], km, n + 3, avoid=avoid | {x["slug"] for x in of_place(r["id"])}):
            if p.get("title") == main_title:
                continue
            hay = ((p.get("title") or "") + " " + (p.get("description") or "")).lower()
            if d < 0.3 and any(nm in hay for nm in names):
                rows.append((p, h["esc"](_short(p.get("description"), 60)) or None,
                             h["bi"]("ที่นี่", "here"), r["id"]))
                continue
            rows.append((p, None, _dist(d, h), r["id"]))
            if len(rows) >= n:
                break
    if not rows:
        return ""
    return strip(rows, h, base, title=h["bi"]("รอบ ๆ ที่นี่", "Around here"))


# ---------------------------------------------------------------- nets

# What each net is ABOUT, as a picture: words read against a picture's
# title + description, or a topic. A net's own jewels come first.
NET_SUBJECT = {
    "yunnan": dict(rx=r"\byunnan|\bban haw\b|baan haw|บ้านฮ่อ|\bmosque|มัสยิด|mae salong|santikhiri|แม่สลอง", topic=None),
    "visa": dict(rx=r"border|mae sai|immigration|friendship bridge|ด่าน|chiang khong|airport", topic="border"),
    "ship": dict(rx=r"truck|freight|railway|station|airport|port|pier|ท่าเรือ", topic="transport"),
    "roofs": dict(rx=r"house|teak|kalae|ka-lae|village|roof|เรือน|บ้าน|ka lae", topic=None),
    "hands": dict(rx=r"garden|plant|flower|nursery|craft|workshop|ต้นไม้|สวน", topic="nature"),
    "amulets": dict(rx=r"amulet|พระเครื่อง|kamthieng|คำเที่ยง", topic="amulets"),
    "chamcha": dict(rx=r"chamcha|จามจุรี|san kamphaeng|bo sang|umbrella|ร่ม|craft|handicraft", topic="craft"),
    "lanterns": dict(rx=r"yi ?peng|yee ?peng|loy ?krathong|loi ?krathong|lantern|khom|ยี่เป็ง|ลอยกระทง|โคม", topic=None),
    "strings": dict(rx=r"music|concert|orchestra|guitar|violin|ดนตรี|salo|saw|phin|sueng", topic=None),
    "races": dict(rx=r"marathon|running|race|\brun\b|stadium|700 year|วิ่ง", topic="sport"),
    "silk": dict(rx=r"silk|weav|loom|textile|cloth|teen ?jok|tin ?chok|ตีนจก|ผ้า|ทอ", topic="textile"),
    "thaiviwat": dict(rx=r"night bazaar|chiang rai.*(market|bazaar|clock)|clock tower|หอนาฬิกา", topic=None),
}


def _subject_pics(key, n, avoid, salt=""):
    sub = NET_SUBJECT.get(key)
    if not sub:
        return []
    rx = re.compile(sub["rx"], re.I) if sub.get("rx") else None
    rows = []
    for p in load():
        if p["slug"] in avoid or "people" in p.get("topic", []) or "elsewhere" in p.get("place", []):
            continue
        hay = (p.get("title") or "") + " " + (p.get("description") or "")
        hit = (rx and rx.search(hay)) or (sub.get("topic") and sub["topic"] in p.get("topic", []))
        if hit:
            rows.append(p)
    # Local first; the north before elsewhere; stable order.
    # Stable per page (pages render in forked children, so a shared counter
    # would make the choice depend on the chunking), and different page to page.
    rows.sort(key=lambda p: (-(len(p.get("description") or "") > 20),
                             zlib.crc32((salt + "|" + p["slug"]).encode())))
    return rows[:n]


def net_pics(key, net, here_id, h, base="../../", n=4):
    ids = [j["id"] for s in net.get("strands", []) for j in s.get("jewels", [])]
    rows, avoid = [], set()
    for pid in ids:
        if pid == here_id:
            continue
        for p in of_place(pid)[:1]:
            if p["slug"] not in avoid:
                rows.append((p, None, None, here_id))
                avoid.add(p["slug"])
        if len(rows) >= n:
            break
    for p in _subject_pics(key, n - len(rows), avoid, salt=key + "|" + str(here_id)):
        rows.append((p, None, None, here_id))
    if not rows:
        return ""
    return strip(rows, h, base, cls="netpics")


def jewel_thumb(pid, base, h):
    """A jewel's own picture: hers first (build's place_thumb), then the pool's."""
    src = ""
    if h.get("thumb"):
        try:
            src = h["thumb"](pid) or ""
        except Exception:                            # noqa: BLE001
            src = ""
    if not src:
        ps = of_place(pid)
        src = _band(ps[0]) if ps else ""
    if not src:
        return ""
    return '<img class="jthumb" src="%s%s" alt="" loading="lazy" decoding="async">' % (base, h["att"](src))


# ---------------------------------------------------------------- festivals and months

FESTIVAL_RX = {
    "bo-sang-umbrella": r"bo ?sang|bor ?sang|บ่อสร้าง|umbrella|parasol|ร่ม",
    "wild-himalayan-cherry-season": r"cherry|sakura|nang ?phaya ?suea ?khrong|นางพญาเสือโคร่ง|prunus",
    "cm-flower-festival": r"flower festival|flower parade|ไม้ดอก|buak hat|บวกหาด",
    "chinese-new-year": r"chinese new year|lunar new year|ตรุษจีน|warorot|chinatown|dragon dance|lion dance",
    "lisu-new-year": r"lisu|ลีซู",
    "makha-bucha": r"makha|มาฆ|wian tian|เวียนเทียน|candle",
    "singha-balloon-fiesta": r"balloon|บอลลูน",
    "muay-thai-day": r"muay|มวย|boxing",
    "poi-luang": r"poi ?luang|ปอยหลวง|tung|ตุง|fon|ฟ้อน",
    "nai-khanom-tom-day": r"muay|มวย|boxing",
    "thai-elephant-day": r"elephant|ช้าง",
    "poy-sang-long": r"poy ?sang|sang ?long|ปอยส่างลอง|shan|novice",
    "songkran-pi-mai-muang": r"songkran|สงกรานต์|water festival|pi mai",
    "cr-lychee-fair": r"lychee|ลิ้นจี่",
    "inthakhin": r"inthakhin|อินทขิล|city pillar|เสาอินทขิล",
    "visakha-doi-suthep-walk": r"doi suthep|ดอยสุเทพ|khruba srivichai|ครูบาศรีวิชัย",
    "visakha-bucha": r"visakha|วิสาขบูชา|wian tian|candle",
    "suep-chata-mueang": r"chata|ชะตาเมือง|city pillar|inthakhin",
    "asalha-bucha": r"asalha|อาสาฬห|candle",
    "khao-phansa": r"phansa|พรรษา|candle procession|novice|monks?\b",
    "akha-swing-festival": r"akha|อาข่า|swing",
    "tan-kuay-salak": r"salak|สลาก|offering",
    "ok-phansa": r"phansa|พรรษา|tak bat|alms",
    "kin-je": r"vegetarian|kin ?je|เจ|jay",
    "yi-peng-loi-krathong": r"yi ?peng|yee ?peng|loy ?krathong|loi ?krathong|lantern|khom|ยี่เป็ง|ลอยกระทง|โคม|krathong",
    "cm-design-week": r"design|exhibition|gallery|art",
    "cm-winter-fair": r"winter fair|fair|งานฤดูหนาว",
    "cr-flower-festival": r"flower festival|flower|ไม้ดอก|swan|singha park",
    "doi-tung-flower-season": r"doi tung|ดอยตุง|mae fah luang|garden",
    "hmong-new-year": r"hmong|ม้ง",
    "nye-countdown": r"fireworks|countdown|new year",
    "phu-chi-fa-sea-of-mist": r"phu ?chi ?fa|ภูชี้ฟ้า|sea of (mist|fog|clouds)|ทะเลหมอก",
    "royal-project-fair": r"royal project|โครงการหลวง|royal park|rajapruek|ราชพฤกษ์",
    "pu-sae-ya-sae": r"pu sae|ย่าแสะ|spirit|offering",
    "cr-red-cross-fair": r"chiang rai.*(fair|festival)",
    "kings-birthday": r"king|royal|พระราช",
    "mothers-day": r"queen|jasmine|มะลิ",
    "fathers-day": r"canna|royal",
}


def festival_pics(f, h, base="../", n=4):
    rx = FESTIVAL_RX.get(f.get("id"))
    if not rx:
        return ""
    rx = re.compile(rx, re.I)
    months = set(f.get("months") or [f.get("month")])
    prov = f.get("province")
    rows = []
    for p in load():
        hay = (p.get("title") or "") + " " + (p.get("description") or "")
        if not rx.search(hay):
            continue
        local = prov in p.get("place", []) or (prov in (None, "both", "all") and
                                                set(p.get("place", [])) & {"cm", "cr", "lanna"})
        rows.append((not local, "elsewhere" in p.get("place", []), p.get("month") not in months,
                     "people" in p.get("topic", []), _USED[p["slug"]], p["slug"], p))
    rows.sort(key=lambda x: x[:6])
    picked, by = [], defaultdict(int)
    for x in rows:
        a = x[-1].get("artist")
        if by[a] >= 2:
            continue
        by[a] += 1
        picked.append(x[-1])
        if len(picked) >= n:
            break
    if not picked:
        return ""
    return strip([(p, None, None, None) for p in picked], h, base, cls="big festpics")


def month_pics(m, h, base="", n=6):
    load()
    ps = sorted(_BY_MONTH.get(m, ()), key=lambda p: (_USED[p["slug"]], -len(p.get("topic", [])), p["slug"]))
    out, seen_place, seen_art = [], set(), defaultdict(int)
    for p in ps:
        loc = (round(p["lat"], 2), round(p["lng"], 2)) if p.get("lat") is not None else p["slug"]
        if loc in seen_place or seen_art[p.get("artist")] >= 2:
            continue
        seen_place.add(loc)
        seen_art[p.get("artist")] += 1
        out.append(p)
        if len(out) >= n:
            break
    if not out:
        return ""
    return strip([(p, None, None, None) for p in out], h, base, cls="monthpics")


def counts():
    load()
    return {"pool": len(_PICKS), "located": sum(len(v) for v in _GRID.values()),
            "places_pictured": len(_OF), "drawn": len(_USED)}


# ---------------------------------------------------------------- the full moon

OBS_RX = {
    "tan_khao_mai": r"new rice|rice harvest|harvest|paddy|ข้าวใหม่|นาข้าว|rice field",
    "makha": r"makha|มาฆ|wian ?tian|เวียนเทียน|candle",
    "six_peng": r"doi suthep|ดอยสุเทพ|khruba|ครูบา",
    "haripunchai": r"haripunchai|hariphunchai|หริภุญชัย|lamphun|ลำพูน",
    "visakha": r"visakha|วิสาข|wian ?tian|เวียนเทียน|candle|doi suthep",
    "asanha": r"asalha|asanha|อาสาฬห|khao ?phansa|เข้าพรรษา|candle",
    "salak": r"salak|สลาก|offering",
    "ok_phansa": r"ok ?phansa|ออกพรรษา|tak ?bat|ตักบาตร|alms|monks",
    "yi_peng": r"yi ?peng|yee ?peng|loy ?krathong|loi ?krathong|lantern|khom|ยี่เป็ง|ลอยกระทง|โคม|krathong",
    "plain": r"monks|alms|ตักบาตร|chedi|wat ",
}


def observance_picks(key, n=1, avoid=()):
    rx = OBS_RX.get(key) or OBS_RX["plain"]
    rx = re.compile(rx, re.I)
    rows = []
    for p in load():
        if p["slug"] in avoid:
            continue
        hay = (p.get("title") or "") + " " + (p.get("description") or "")
        if not rx.search(hay):
            continue
        rows.append((("elsewhere" in p.get("place", [])), (p.get("width") or 0) < (p.get("height") or 0),
                     "people" in p.get("topic", []), _USED[p["slug"]], p["slug"], p))
    rows.sort(key=lambda x: x[:5])
    out = [x[-1] for x in rows[:n]]
    for p in out:
        _USED[p["slug"]] += 1
    return out


def band(p, kicker, base, esc, att, line=""):
    """The minisite formula, full width: photograph, scrim, tint, words, credit."""
    return ('<section class="band" style="background-image:url(%s%s)"><div class="in">'
            '<span class="kicker">%s</span>%s</div>'
            '<p class="cred"><a href="%s" rel="noopener">%s</a> · %s · Wikimedia Commons</p></section>' % (
                base, att("site/%s.jpg" % p["slug"]), kicker,
                ('<p>%s</p>' % line) if line else "",
                att(p.get("page") or "#"), esc(_artist(p.get("artist"))), esc(p.get("licence") or "")))


# ---------------------------------------------------------------- one picture of a place

_CI = None
_PH = None


def place_picture(pid):
    """{src, by, link} for a place: its own photograph, else a Commons one OF it.

    src is root-relative (no leading slash). Used by the record JSON (the map's
    tap card reads it) and by the front page's calendar for an event's venue."""
    global _CI, _PH
    if _PH is None:
        _PH = {}
        d = ASSETS / "photos"
        try:
            cred = json.loads((d / "credits.json").read_text())
        except (OSError, ValueError):
            cred = {}
        if d.exists():
            for f in d.iterdir():
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    c = cred.get(f.stem) or {}
                    _PH[f.stem] = {"src": ("band/place/%s.jpg" % f.stem
                                           if (ASSETS / "band" / "place" / (f.stem + ".jpg")).exists()
                                           else "photos/" + f.name),
                                   "by": ", ".join(x for x in (c.get("author"), c.get("license")) if x),
                                   "link": c.get("source") or ""}
    if pid in _PH:
        return _PH[pid]
    if _CI is None:
        try:
            _CI = json.loads((ROOT / "data" / "commons_images.json").read_text()).get("images", {})
        except (OSError, ValueError):
            _CI = {}
    ci = _CI.get(pid) or {}
    if ci.get("file") and (ASSETS / ci["file"]).exists():
        slug = ci["file"].rsplit("/", 1)[-1][:-4]
        return {"src": _band({"slug": slug}), "by": "%s, %s" % (_artist(ci.get("artist")), ci.get("licence") or ""),
                "link": ci.get("full") or ""}
    ps = of_place(pid)
    if ps:
        p = ps[0]
        return {"src": _band(p), "by": "%s, %s" % (_artist(p.get("artist")), p.get("licence") or ""),
                "link": p.get("page") or ""}
    return None
