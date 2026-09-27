#!/usr/bin/env python3
"""The three pieces the front page grew on 2026-09-21: the drawn sprite, the big
map, and the illustrated calendar.

ICONS. The site's own sprite (docs/icons.svg, built by build.py from ICON_SPRITE
and glyphs.SPRITE) is the only mark this page draws. The symbols this page uses
are inlined into it — a subset, not the whole 18 kB file — so the page needs no
second request and works from file:// while it is still a draft. A name that is
not in the sprite raises: a missing icon is a thing to draw, not to fall back
from.
"""
from __future__ import annotations

import datetime
import difflib
import html
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
MD = pathlib.Path.home() / "Developer/claude code projects/mot-dang"
BASE = "https://motdang.net/"

# The sprite comes from the generator itself when one is running — build.py imports
# home_next, so its ICONS_SVG is already in memory — and from the file build.py writes
# otherwise. docs/ is gitignored, so on a clone with no build yet there is neither, and
# that is an error worth saying out loud rather than drawing nothing.
_BUILD = sys.modules.get("build")
_ICONS = MD / "docs/icons.svg"
if _BUILD is not None and getattr(_BUILD, "ICONS_SVG", None):
    SPRITE = _BUILD.ICONS_SVG
elif _ICONS.exists():
    SPRITE = _ICONS.read_text()
else:
    raise SystemExit("no sprite: run build.py once so docs/icons.svg exists")


def _symbols(svg):
    """Every <g id=…>…</g> in the sprite, nesting included. A regex that stops at the
    first </g> loses the icons drawn as groups of groups, and one that ignores the
    attributes after the id loses i-search."""
    out = {}
    for m in re.finditer(r'<g id="([^"]+)"[^>]*>', svg):
        depth, j = 1, m.end()
        while depth:
            t = re.compile(r"</?g\b").search(svg, j)
            if not t:
                break
            depth += -1 if svg[t.start():t.start() + 3] == "</g" else 1
            j = t.end()
        end = svg.find(">", j - 1) + 1
        out[m.group(1)] = svg[m.start():end]
    return out


_SYM = _symbols(SPRITE)
_USED: set[str] = set()

# build.py's CAT_ICON, read from the generator rather than copied, so a shelf that
# gains a mark there gains it here.
if _BUILD is not None and getattr(_BUILD, "CAT_ICON", None):
    CAT_ICON = dict(_BUILD.CAT_ICON)
else:
    _B = (MD / "build.py").read_text()
    CAT_ICON = eval(re.search(r"^CAT_ICON = (\{.*?^\})", _B, re.S | re.M).group(1))
    CAT_ICON.update(eval(re.search(r"^CAT_ICON_MORE = (\{.*?\})",
                                   (MD / "glyphs.py").read_text(), re.M).group(1)))


def E(x):
    return html.escape("" if x is None else str(x), quote=True)


def icon(name, size=20, cls="rowicon"):
    """One <use> of the sprite, decorative by contract — always beside a label."""
    if name not in _SYM:
        raise KeyError(f"{name} is not in the sprite — draw it in build.py's "
                       f"ICON_SPRITE before using it")
    _USED.add(name)
    return (f'<svg class="{cls}" aria-hidden="true" focusable="false" width="{size}" '
            f'height="{size}" viewBox="0 0 24 24"><use href="#{name}"></use></svg>')


def sprite_defs():
    """Only the symbols the page actually drew."""
    body = "\n".join(_SYM[n] for n in sorted(_USED))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" '
            f'style="position:absolute" aria-hidden="true"><defs>{body}</defs></svg>')


# ---------------------------------------------------------------- the map

import mapart  # noqa: E402

MAP_CREDIT = ("Administrative boundaries: OCHA COD-AB Thailand, Royal Thai Survey "
              "Department, CC BY-IGO · pins © OpenStreetMap contributors, ODbL")


def dots(out_dir):
    """The two frames of the picture, drawn if they are not already there. docs/ is
    gitignored and swept, so the page draws its own map rather than depending on a
    file somebody remembered to keep."""
    out_dir = pathlib.Path(out_dir)
    want = [out_dir / f"map-dots-{k}.png" for k in ("light", "dark")]
    if all(p.exists() for p in want):
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    pj = mapart.Proj()
    pts = [(x, y) for _pv, _k, x, y in mapart.points()]
    for p, ink, glow in zip(want, ((0xC8, 0x54, 0x2B), (0x8A, 0x63, 0x2A)),
                            ((0xE0, 0x32, 0x2B), (0xFF, 0xC2, 0x3D))):
        mapart.render_dots(pj, pts, p, ink, glow)


def projection():
    """The numbers the page needs to turn a coordinate into a point on the drawn map."""
    pj = mapart.Proj()
    return {"w": pj.w, "s": pj.s, "e": pj.e, "n": pj.n, "kx": pj.kx,
            "scale": pj.scale, "pad": pj.pad, "W": int(pj.width), "H": int(pj.height)}


def big_map(counts, src="img/", ensure=None):
    """Every pin drawn, the districts over it, and a way into the live map from any
    of them. The picture is a PNG because 88,901 places as SVG circles is half a
    megabyte; the shapes are SVG because they carry a name and a link."""
    if ensure:
        dots(ensure)
    pj = mapart.Proj()
    w, h = int(pj.width), int(pj.height)
    shapes = []
    for pr, d in mapart.amphoe_paths(pj, counts):
        c = counts.get(pr["pcode"], 0)
        name = f'{pr["name"]} · {pr["nameEn"]}'
        # the district's own centre, so the live map opens where the reader tapped
        xs = [p for r in mapart._rings(
            next(f for f in mapart.AMPHOE if f["properties"]["pcode"] == pr["pcode"])
            ["geometry"]) for p in r]
        lat = sum(p[1] for p in xs) / len(xs)
        lon = sum(p[0] for p in xs) / len(xs)
        # the live map reads #zoom/lat/lng/shelf,shelf, and lands on bare basemap when
        # no shelf is named — so a district hands over its two largest.
        pv = pr["province"]
        shapes.append(
            f'<a href="{BASE}map.html#11/{lat:.4f}/{lon:.4f}/{pv}-food,{pv}-wat" class="amp">'
            f'<path d="{d}"><title>{E(name)} — {c:,} places</title></path></a>')
    marks = []
    for th, en, lat, lon, pv in mapart.CITY:
        x, y = pj.xy(lon, lat)
        marks.append(
            f'<g class="city"><circle cx="{x:.0f}" cy="{y:.0f}" r="13"/>'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" class="dot"/>'
            f'<text x="{x + 22:.0f}" y="{y - 6:.0f}" class="cth">{E(th)}</text>'
            f'<text x="{x + 22:.0f}" y="{y + 16:.0f}" class="cen">{E(en)}</text></g>')
    return f"""<figure class="bigmap">
<div class="plate" style="aspect-ratio:{w}/{h}">
 <picture>
  <source srcset="{src}map-dots-dark.png" media="(prefers-color-scheme:dark)">
  <img src="{src}map-dots-light.png" width="{w}" height="{h}" loading="eager" decoding="async"
       alt="Every place in the catalogue, drawn as one dot each: Chiang Mai city at the centre, Chiang Rai to the north-east, and the highways between them picked out by the shops along them.">
 </picture>
 <svg class="over" viewBox="0 0 {w} {h}" aria-label="The districts of both provinces, each a link into the live map">
  <g class="amps">{''.join(shapes)}</g>
  <g class="cities">{''.join(marks)}</g>
  <g id="me" hidden><circle r="26" class="halo"/><circle r="9" class="pip"/></g>
 </svg>
</div>
<figcaption><span class="src">{E(MAP_CREDIT)}</span></figcaption>
</figure>"""


# ---------------------------------------------------------------- the calendar

THAI_WD = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]
EN_WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def moon(illum, waxing, r=11):
    """The moon as it is that night, not a glyph of it: a disc, and the lit part
    bounded by the terminator ellipse. Waning mirrors."""
    illum = max(0.0, min(1.0, illum or 0.0))
    rx = r * abs(1 - 2 * illum)
    sweep = 1 if illum > .5 else 0
    lit = (f'M0 {-r}A{r} {r} 0 0 1 0 {r}A{rx:.2f} {r} 0 0 {sweep} 0 {-r}')
    flip = "" if waxing else f' transform="scale(-1,1)"'
    return (f'<svg class="moon" viewBox="{-r-1} {-r-1} {2*r+2} {2*r+2}" width="{2*r+2}" '
            f'height="{2*r+2}" aria-hidden="true">'
            f'<circle r="{r}" class="dark"/>'
            f'<path d="{lit}" class="lit"{flip}/>'
            f'<circle r="{r}" class="rim"/></svg>')


def calendar(today, months=2, k_events=2, alive=None):
    """Two months, drawn. Every day carries its Thai colour, its moon and its lunar
    day; the dated things sit in the square they fall in."""
    F, S, byday = _cal_data()

    out = []
    y, m = today.year, today.month
    for _ in range(months):
        first = datetime.date(y, m, 1)
        nxt = datetime.date(y + (m == 12), m % 12 + 1, 1)
        start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)
        cells = []
        d = start
        while d < nxt or d.weekday() != 6:
            cells.append(day_cell(d, d.month == m, today, F, S, byday, k_events, alive))
            d += datetime.timedelta(days=1)
            if len(cells) > 41:
                break
        head = "".join(f'<div class="wd"><span class="th" lang="th">{t}</span>'
                       f'<span class="en">{e}</span></div>'
                       for t, e in zip(THAI_WD, EN_WD))
        out.append(f'<div class="month"><h3>{E(TH_MONTH[m])} '
                   f'<span class="en">{first.strftime("%B %Y")}</span>'
                   f'<span class="be">พ.ศ. {y + 543}</span></h3>'
                   f'<div class="cal"><div class="wds">{head}</div>'
                   f'<div class="days">{"".join(cells)}</div></div></div>')
        y, m = y + (m == 12), m % 12 + 1
    return f'<div class="cals">{"".join(out)}</div>'


def same_event(a, b):
    """The newsletter says "Payap presents Lanna Thai Music", the calendar says
    "Lanna Thai Music: An Interactive Lecture…". One event, two spellings. The shared
    run of characters is what gives it away."""
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(
        0, len(a), 0, len(b))
    return m.size >= 14


def dedupe(evs):
    """One row per event per day: the longer title wins, and a row with a source link
    beats one without."""
    kept: list = []
    for e in evs:
        t = (e.get("title") or "").strip()
        if not t:
            continue
        for i, prev in enumerate(kept):
            pt = (prev.get("title") or "").strip()
            if same_event(t.lower(), pt.lower()):
                if (bool(e.get("url")), len(t)) > (bool(prev.get("url")), len(pt)):
                    kept[i] = e
                break
        else:
            kept.append(e)
    return kept


_FM = None


def _full_moons():
    """{date: (peng_th, peng_en)} from the published table, once."""
    global _FM
    if _FM is None:
        try:
            import fullmoon_layer
            _FM = fullmoon_layer.full_moon_dates()
        except Exception:  # noqa: BLE001 — the calendar draws without it
            _FM = {}
    return _FM


def _cal_data():
    """The three files the calendar reads, and the events keyed by the day they fall
    on — one row per event, however many feeds announced it."""
    F = json.loads((MD / "data/fortune.json").read_text())["days"]
    S = json.loads((MD / "data/sky.json").read_text())["days"]
    EV = json.loads((MD / "data/events.json").read_text())["events"]
    byday: dict[str, list] = {}
    for e in EV:
        d = (e.get("start") or "")[:10]
        if d:
            byday.setdefault(d, []).append(e)
    return F, S, {d: dedupe(v) for d, v in byday.items()}


def horizon(byday, today, cap=6):
    """How many months the dated things actually reach. Counted, never typed."""
    ahead = [d for d in byday if d >= today.isoformat()]
    if not ahead:
        return 2
    last = datetime.date.fromisoformat(max(ahead))
    m = (last.year - today.year) * 12 + (last.month - today.month) + 1
    return max(2, min(cap, m))


def agenda(today, days=7, alive=None, marked_after=None, fold=None):
    """The same days as the grid, down the page instead of across it — which is the
    only shape that renders whole on a phone (NaN, 2026-09-22: the calendar "doesn't
    fully render contents, everything gets cut off").

    The first `marked_after` days are all listed; past that only days that carry
    something. marked_after defaults to the whole run.

    fold=(first, rest) shows that many titles on the first day and on every later one,
    and puts the others behind a "+N" the reader opens. None lists every title.
    """
    F, S, byday = _cal_data()
    marked_after = days if marked_after is None else marked_after
    rows, month = [], None
    for i in range(days):
        d = today + datetime.timedelta(days=i)
        iso = d.isoformat()
        s = (S.get(iso) or {}).get("moon") or {}
        evs = byday.get(iso, [])
        if i >= marked_after and not evs and not s.get("wan_phra"):
            continue
        if (d.year, d.month) != month:
            month = (d.year, d.month)
            rows.append(f'<li class="agm"><span class="th" lang="th">{E(TH_MONTH[d.month])}</span> '
                        f'<span class="en">{d.strftime("%B %Y")}</span></li>')
        k = None if fold is None else fold[0] if i == 0 else fold[1]
        rows.append(_agenda_row(d, today, F, S, byday, alive, k))
    return f'<ul class="agenda">{"".join(rows)}</ul>'


def _agenda_row(d, today, F, S, byday, alive=None, k=None):
    iso = d.isoformat()
    t = (F.get(iso) or {}).get("thai") or {}
    s = (S.get(iso) or {}).get("moon") or {}
    cls = ["ag"]
    if s.get("wan_phra"):
        cls.append("phra")
    if d == today:
        cls.append("now")
    hexa = t.get("hex")
    swatch = (f'<span class="col" style="--c:{E(hexa)}" title="{E(t.get("colour_th", ""))} · '
              f'{E(t.get("colour_en", ""))}"></span>' if hexa else "")
    when = "วันนี้ · today" if d == today else (
        "พรุ่งนี้ · tomorrow" if d == today + datetime.timedelta(days=1) else "")
    head = (f'<div class="agd"><b>{d.day}</b>'
            f'<span class="wd"><span class="th" lang="th">{THAI_WD[(d.weekday() + 1) % 7]}</span>'
            f'{EN_WD[(d.weekday() + 1) % 7]}</span>{swatch}</div>')
    bits = []
    if when:
        bits.append(f'<p class="tag">{when}</p>')
    lab = ""
    if s.get("thai_label_th"):
        lab = E(s["thai_label_th"])
        if s.get("wan_phra"):
            lab = f'{icon("i-lotus", 14)}<b>วันพระ</b> {lab}'
    bits.append(f'<p class="lun">{moon(s.get("illum"), s.get("waxing"), 9) if s else ""}'
                f'<span class="th" lang="th">{lab}</span></p>')
    fm = _full_moons().get(iso)
    if fm:  # the published full moon, and its page (NaN, 2026-09-27)
        bits.append(f'<p class="fmday"><a href="https://motdang.net/full-moon/{iso}/">'
                    f'{icon("i-fullmoon", 14)} วันเพ็ญ {E(fm[0])} · full moon at the wat</a></p>')
    evs = byday.get(iso, [])
    if evs:
        li = []
        for e in evs:
            tt = (e.get("title") or "").strip()
            # A timed event carries its clock, Bangkok time, so the front page can drop
            # it once it is over and count down to the next one (NaN, 2026-09-26).
            at = ""
            st = e.get("start") or ""
            if not e.get("all_day") and len(st) >= 16 and st[:10] == iso:
                at = f' data-s="{E(st[11:16])}"'
                en = e.get("end") or ""
                if len(en) >= 16 and en[:10] == iso:
                    at += f' data-e="{E(en[11:16])}"'
            if e.get("url") and (alive is None or alive(e["url"])):
                li.append(f'<li{at}><a href="{E(e["url"])}" rel="noopener">{E(tt)}</a></li>')
            else:
                li.append(f"<li{at}>{E(tt)}</li>")
        if k is not None and len(li) > k + 1:
            li = li[:k] + [f'<li class="more"><details><summary>+{len(li) - k}</summary>'
                           f'<ul class="ev">{"".join(li[k:])}</ul></details></li>']
        bits.append(f'<ul class="ev">{"".join(li)}</ul>')
    return (f'<li class="{" ".join(cls)}" data-d="{iso}">{head}'
            f'<div class="agb">{"".join(bits)}</div></li>')


TH_MONTH = {1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน", 5: "พฤษภาคม",
            6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม", 9: "กันยายน", 10: "ตุลาคม",
            11: "พฤศจิกายน", 12: "ธันวาคม"}


def day_cell(d, in_month, today, F, S, byday, k, alive=None):
    iso = d.isoformat()
    f = F.get(iso) or {}
    t = f.get("thai") or {}
    s = (S.get(iso) or {}).get("moon") or {}
    cls = ["day"]
    if not in_month:
        # not "out": that class already marks an outbound link on this page, and
        # `display:inline-flex` on a calendar square lays the day out sideways.
        cls.append("oth")
    if d < today:
        cls.append("past")
    if d == today:
        cls.append("now")
    if s.get("wan_phra"):
        cls.append("phra")
    bits = []
    hexa = t.get("hex")
    swatch = (f'<span class="col" style="--c:{E(hexa)}" title="{E(t.get("colour_th",""))} · '
              f'{E(t.get("colour_en",""))}"></span>' if hexa else "")
    bits.append(f'<div class="hd"><b>{d.day}</b>{swatch}'
                + (moon(s.get("illum"), s.get("waxing")) if s else "") + "</div>")
    if s.get("thai_label_th"):
        lab = E(s["thai_label_th"])
        if s.get("wan_phra"):
            lab = f'{icon("i-lotus", 14)}<b>วันพระ</b> {lab}'
        bits.append(f'<p class="lun th" lang="th">{lab}</p>')
    fm = _full_moons().get(iso)
    if fm:
        bits.append(f'<p class="lun fmday"><a href="https://motdang.net/full-moon/{iso}/">'
                    f'{icon("i-fullmoon", 12)} วันเพ็ญ · full moon</a></p>')
    evs = byday.get(iso, [])
    if evs:
        li = []
        for e in evs[:k]:
            tt = (e.get("title") or "").strip()
            tt = tt if len(tt) < 46 else tt[:43] + "…"
            # `alive` is the caller's judgement of the URL — the last sweep's status,
            # so a square never carries a link the publish gate calls dead.
            if e.get("url") and (alive is None or alive(e["url"])):
                li.append(f'<li><a href="{E(e["url"])}" rel="noopener">{E(tt)}</a></li>')
            else:
                li.append(f"<li>{E(tt)}</li>")
        more = (f'<li class="more">+{len(evs) - k} more</li>' if len(evs) > k else "")
        bits.append(f'<ul class="ev">{"".join(li)}{more}</ul>')
    if d == today:
        bits.append('<p class="tag">วันนี้ · today</p>')
    return f'<div class="{" ".join(cls)}">{"".join(bits)}</div>'


# ---------------------------------------------------------------- the geofence

# Grafted from home_layer.py's front page (NaN, 2026-09-21 evening: "graft the
# geofence onto it and swap the front page"). The edge fills meta[name=md-where]
# with cf.city|lat|lon|tz|country — publish/worker.js withWhere() does it for every
# HTML response, so the page needs no key, no fetch and no permission to know roughly
# where it is being read. The reader's own choice beats the edge, and a tap on ตรงนี้
# beats both.
#
# Nothing here is fetched at load. The nine cells of data/here/ are fetched only when
# the reader asks — home_layer's rule, and the reason the front page stayed quick.

NEAR_KINDS = ("food", "wat", "market", "massage", "medical", "shopping",
              "whats-on", "essentials", "hotel")


def geo_payload(shelves, proj, cities, needs=None):
    """Everything the page needs to answer from where it is read, baked at build
    time: the frames with their coordinates, the two city centres, the map's own
    projection, the marks the near-list draws with, and the needs a tile can ask
    for — each a list of [shelf, sub] pairs ("" = the whole shelf) and the page a
    tile falls back to."""
    frames = []
    for f in json.loads((MD / "docs/site/hero/index.json").read_text()):
        if not f.get("bg"):
            continue
        frames.append({"j": f"site/hero/{f['slug']}.jpg", "w": f"site/hero/{f['slug']}.webp",
                       "W": f["w"], "H": f["h"], "p": f["pool"], "s": f["scene"],
                       "ic": 1 if f.get("ic") else 0, "la": f.get("la"), "lo": f.get("lo")})
    for k in NEAR_KINDS:
        icon(CAT_ICON[k], 20)          # so the sprite subset carries what the list draws
    icon("i-phone", 18)
    return {"cities": cities, "pics": frames, "proj": proj,
            "kinds": {k: CAT_ICON[k] for k in NEAR_KINDS},
            "needs": needs or {},
            "shelves": [s["key"] for s in shelves]}


GEO_JS = r"""<script>
(function(){
var D=JSON.parse(document.getElementById('md-geo').textContent);
var META=((document.querySelector('meta[name=md-where]')||{}).content||'').split('|');
var EDGE=META.length>=3&&+META[1]?{city:META[0],lat:+META[1],lon:+META[2]}:null;
var FIX=null,FAR=false,CITY='cm';
function km(a,b,c,d){var R=6371,x=(c-a)*Math.PI/180,y=(d-b)*Math.PI/180;
 var s=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(y/2)*Math.sin(y/2);
 return 2*R*Math.asin(Math.sqrt(s));}
function read(k){try{return localStorage.getItem(k);}catch(e){return null;}}
function store(k,v){try{localStorage.setItem(k,v);}catch(e){}}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function mark(id,size){return '<svg class="rowicon" aria-hidden="true" width="'+(size||18)+
 '" height="'+(size||18)+'" viewBox="0 0 24 24"><use href="#'+id+'"></use></svg>';}
function here(){return FIX||(EDGE?{lat:EDGE.lat,lon:EDGE.lon}:null);}

/* ---- which province the page speaks to: the reader's own choice, else the edge's
   guess, else Chiang Mai. */
function guess(){var c=read('md-city');if(c==='cm'||c==='cr')return c;
 if(EDGE){var best=null,bd=1e9;D.cities.forEach(function(x){var d=km(EDGE.lat,EDGE.lon,x.lat,x.lon);
  if(d<bd){bd=d;best=x.k;}});if(bd<150)return best;FAR=true;}
 return 'cm';}
function setCity(c,remember){CITY=c;if(remember)store('md-city',c);
 document.querySelectorAll('[data-city]').forEach(function(a){
  a.classList.toggle('on',a.dataset.city===c);});
 document.querySelectorAll('[data-href]').forEach(function(el){
  el.setAttribute('href',el.dataset.href.replace('{c}',c));});
 document.querySelectorAll('[data-cm][data-cr] .n').forEach(function(n){
  n.textContent=(+n.parentNode.closest('[data-cm]').dataset[c]).toLocaleString();});
 var cards=document.getElementById('aircards');
 if(cards){var mine=cards.querySelector('[data-air="'+c+'"]');
  if(mine)cards.insertBefore(mine,cards.firstChild);}
 where();}
function where(){
 var el=document.getElementById('where');if(!el)return;
 var c=D.cities.filter(function(x){return x.k===CITY;})[0],p=here();
 var d=p?km(p.lat,p.lon,c.lat,c.lon):null;
 var lede=FIX?'ตรงนี้ · you are here':(EDGE?'ประมาณจากเครือข่าย · from your network':
  'ค่าเริ่มต้น · the default');
 el.innerHTML=mark('i-near',18)+'<b>'+esc(c.th)+' · '+esc(c.en)+'</b>'+
  (d!=null&&d>2&&d<400?'<span class="d" title="ระยะเส้นตรง · straight-line distance">'+(d<1?Math.round(d*1000)+' m':Math.round(d)+' km')+'</span>':'')+
  '<span class="src">'+esc(FAR&&EDGE&&EDGE.city?EDGE.city+' → ':'')+lede+'</span>';
 you(p);
}

/* ---- the drawn map: a ring where the reader is, in the map's own projection */
function you(p){
 var g=document.getElementById('me');if(!g)return;
 if(!p){g.setAttribute('hidden','');return;}
 var P=D.proj;
 if(p.lon<P.w||p.lon>P.e||p.lat<P.s||p.lat>P.n){g.setAttribute('hidden','');return;}
 var x=P.pad+(p.lon-P.w)*P.kx*P.scale,y=P.pad+(P.n-p.lat)*P.scale;
 g.setAttribute('transform','translate('+x.toFixed(1)+','+y.toFixed(1)+')');
 g.removeAttribute('hidden');
 var b=document.getElementById('openmap');
 if(b)b.href=b.dataset.href+'#14/'+p.lat.toFixed(4)+'/'+p.lon.toFixed(4)+'/'+CITY+'-food,'+CITY+'-wat';
}

/* ---- the pictures follow the reader: home_layer's own scoring, three bands */
function pool(h){return h>=5&&h<10?'morning':h<17?'day':h<19?'dusk':'night';}
function score(f,scene,P,want,portrait){
 var s=1;
 if(f.s===scene)s*=1.8;
 if(f.p===want)s*=1.5;
 s*=(portrait?(f.H>=f.W):(f.W>f.H))?1.25:1;
 if(P){
  if(FAR&&!FIX)return f.ic?s:0;
  if(f.la==null)s*=0.85;
  else{var d=km(P.lat,P.lon,f.la,f.lo);s*=d<1?14:d<5?7:d<15?3:d<50?1.2:(f.ic?0.8:0.15);}
 }else s*=f.ic?1.3:1;
 return s;}
function pictures(){
 var P=here();
 /* No position, no swap. The three frames the build baked in are already in flight by
    the time this runs, so swapping without a reason costs the reader a second set of
    photographs and buys nothing; with a position the swap is the whole point — the
    frames come from the square kilometre they are standing in. */
 if(!P)return;
 var now=new Date(),want=pool(now.getHours());
 var portrait=innerHeight>innerWidth,used={},seed=now.getDate()*7+Math.floor(now.getHours()/3);
 document.querySelectorAll('.band[data-scene]').forEach(function(el,si){
  var scene=el.dataset.scene,best=null,bs=0;
  D.pics.forEach(function(f,i){
   if(used[f.j])return;
   var v=score(f,scene,P,want,portrait);if(v<=0)return;
   v*=1+(((i*31+seed+si*7)%17)/160);
   if(v>bs){bs=v;best=f;}});
  if(!best)return;used[best.j]=1;
  el.style.backgroundImage='image-set(url('+best.w+') type("image/webp"),url('+best.j+'))';
  if(!el.style.backgroundImage)el.style.backgroundImage='url('+best.j+')';});}

/* ---- near: the cells around the reader, fetched only when the reader asks, and
   kept, so a second tile answers without a second download. The edge's guess is a
   city, not a person, so nothing here measures from it — a list needs a real fix. */
var CELLS={};
function cell(la,ln){return Math.floor(la*100)+'_'+Math.floor(ln*100);}
function get(k){if(!CELLS[k])CELLS[k]=fetch('data/here/'+k+'.json')
 .then(function(r){return r.ok?r.json():[];}).catch(function(){return [];});return CELLS[k];}
function around(lat,lon,ring){var keys=[];
 for(var i=-ring;i<=ring;i++)for(var j=-ring;j<=ring;j++)keys.push(cell(lat+i*0.01,lon+j*0.01));
 return Promise.all(keys.map(get)).then(function(all){
  return [].concat.apply([],all).map(function(r){
   return {la:r[0],ln:r[1],p:r[2],slug:r[3],th:r[4],en:r[5],cat:r[6],sub:r[7],hours:r[9],
           tel:r[10],d:km(lat,lon,r[0],r[1])};}).sort(function(a,b){return a.d-b.d;});});}
function kinds(h){return h<10?['food','wat','market','massage','medical']:
 h<15?['food','shopping','massage','wat','medical']:
 h<20?['food','market','massage','whats-on','medical']:
 ['food','medical','essentials','whats-on','hotel'];}
function wmin(){var n=new Date();return ((n.getDay()+6)%7)*1440+n.getHours()*60+n.getMinutes();}
function isOpen(hours,w){if(!hours||hours===0)return null;
 for(var i=0;i<hours.length;i++)if(hours[i][0]<=w&&w<hours[i][1])return true;
 return false;}
function far(d){return d<1?Math.round(d*100)*10+' m':d.toFixed(1)+' km';}
/* Straight-line metres, not the trip: a U-turn or the moat can make the ride
   longer (Nan, 2026-09-23). Said once in the list head, and on each figure. */
var CROW='<span class="crow">ระยะเส้นตรง · straight-line</span>';
function row(r,ic,w){
 var o=isOpen(r.hours,w),tel=r.tel?String(r.tel).split(/[,;\/]/)[0].replace(/[^\d+]/g,''):'';
 return '<li><a class="go" href="'+esc(r.p)+'/p/'+esc(r.slug)+'.html">'+mark(ic,20)+
  '<span class="lbl">'+esc(r.th||r.en)+
  (r.en&&r.th?'<span class="en" lang="en">'+esc(r.en)+'</span>':'')+'</span>'+
  (o===true?'<span class="open">เปิด · open</span>':'')+
  '<span class="d" title="ระยะเส้นตรง · straight-line distance">'+far(r.d)+'</span></a>'+
  (tel.length>=9?'<a class="tel" href="tel:'+esc(tel)+'" aria-label="โทร · call">'+
   mark('i-phone',18)+'</a>':'')+'</li>';}
/* Scroll to the list only after a tap. With location already granted the list also
   fills itself on load, and a page that moves on its own reads as broken (Nan,
   2026-09-27). */
var TAPPED=false;
function paint(head,html){var list=document.getElementById('nearlist');if(!list)return;
 list.innerHTML=head+html;list.hidden=false;
 if(TAPPED&&list.getBoundingClientRect().top>innerHeight*0.7)list.scrollIntoView({block:'center',behavior:'smooth'});}
function wait(){var list=document.getElementById('nearlist');if(!list)return;
 list.hidden=false;list.innerHTML='<li class="wait">กำลังดู · looking…</li>';}
function showNear(lat,lon){
 wait();
 around(lat,lon,1).then(function(rows){
  var w=wmin(),out=[],seen={};
  kinds(new Date().getHours()).forEach(function(k){
   var best=null;
   for(var i=0;i<rows.length;i++){var r=rows[i];
    if(r.cat!==k||seen[r.slug])continue;
    var o=isOpen(r.hours,w);if(o===false)continue;
    if(!best||(o===true&&isOpen(best.hours,w)!==true))best=r;
    if(o===true)break;}
   if(best){seen[best.slug]=1;out.push(row(best,D.kinds[k],w));}});
  if(!out.length){location.href='here.html';return;}
  paint('<li class="head">'+mark('i-here',18)+'แถวนี้ · around you'+CROW+'</li>',out.join(''));});}

/* ---- the need tiles: the nearest few of one kind, open ones marked, a phone to
   tap. A reader with no position, or far from both cities, gets the tile's own page. */
var NEED=null;
function showNeed(key){
 var N=D.needs[key],p=FIX;if(!N||!p)return;NEED=key;
 document.querySelectorAll('[data-need]').forEach(function(a){
  a.classList.toggle('on',a.dataset.need===key);});
 wait();
 function pick(rows){var w=wmin();return rows.filter(function(r){
  return N.m.some(function(m){return r.cat===m[0]&&(!m[1]||r.sub===m[1]);})&&
   isOpen(r.hours,w)!==false;}).slice(0,5);}
 around(p.lat,p.lon,1).then(function(rows){var got=pick(rows);
  return got.length>=3?got:around(p.lat,p.lon,2).then(pick);})
 .then(function(got){
  var all=N.href.replace('{c}',CITY);
  if(!got.length){location.href=all;return;}
  var w=wmin();
  paint('<li class="head">'+mark(N.ic,18)+esc(N.th)+' · '+esc(N.en)+CROW+'</li>',
   got.map(function(r){return row(r,N.ic,w);}).join('')+
   '<li class="all"><a href="'+esc(all)+'">ทั้งหมด · all '+mark('i-arrow',14)+'</a></li>');});}

function locate(done,fail){
 if(!navigator.geolocation){if(fail)fail();return;}
 var b=document.getElementById('asknear');if(b)b.disabled=true;
 navigator.geolocation.getCurrentPosition(function(p){
  if(b)b.disabled=false;
  FIX={lat:p.coords.latitude,lon:p.coords.longitude};
  var best=null,bd=1e9;D.cities.forEach(function(x){var d=km(FIX.lat,FIX.lon,x.lat,x.lon);
   if(d<bd){bd=d;best=x.k;}});
  FAR=bd>=150;if(!FAR&&best!==CITY)setCity(best,false);
  where();pictures();
  if(FAR){if(fail)fail();}else if(done)done();
 },function(){if(b)b.disabled=false;if(fail)fail();},{maximumAge:60000,timeout:8000});}

var ask=document.getElementById('asknear');
if(ask)ask.addEventListener('click',function(){TAPPED=true;
 if(FIX&&!FAR)showNear(FIX.lat,FIX.lon);
 else locate(function(){showNear(FIX.lat,FIX.lon);},function(){location.href='here.html';});});
document.querySelectorAll('[data-need]').forEach(function(a){
 a.addEventListener('click',function(e){
  if(!navigator.geolocation||!D.needs[a.dataset.need])return;
  e.preventDefault();TAPPED=true;
  if(FIX&&!FAR){showNeed(a.dataset.need);return;}
  locate(function(){showNeed(a.dataset.need);},function(){location.href=a.href;});});});
document.querySelectorAll('[data-city]').forEach(function(a){
 a.addEventListener('click',function(e){e.preventDefault();setCity(a.dataset.city,true);});});

setCity(guess(),false);pictures();
try{if(navigator.permissions)navigator.permissions.query({name:'geolocation'})
 .then(function(s){if(s.state==='granted')locate(function(){showNear(FIX.lat,FIX.lon);});});}catch(e){}
})();
</script>"""


# ---------------------------------------------------------------- the bar

# NaN, 2026-09-21: "menu bar and top bits should collapse/disappear on scroll,
# elegantly." Three states, not two: at the top the bar is whole; once the page has
# moved the nav and the language switch fold away and the bar keeps only the brand and
# the search; scrolling down takes the bar with it and any upward scroll brings it
# back. A keyboard focus inside it brings it back too, because a bar that hides a
# focused field is a trap. The kit already carried the away-state for phones
# (body.nav-away, max-width:52rem) — this drives it at every width.
# NaN, 2026-09-22: "big top menu persists too much on scroll". It used to come back
# on an 8 px twitch upward; now the bar leaves on the first real downward move past
# the fold and only returns on a deliberate 90 px of scrolling back up, or at the top
# of the page. UP and DOWN accumulate separately, so a wobble moves neither.
HEADER_JS = r"""<script>
(function(){
var b=document.body,y=window.pageYOffset,up=0,dn=0,ticking=false;
function frame(){
 ticking=false;
 var n=window.pageYOffset,d=n-y;y=n;
 if(n<60){up=dn=0;b.classList.remove('nav-away','nav-tight');return;}
 b.classList.add('nav-tight');
 if(d>0){dn+=d;up=0;if(dn>14)b.classList.add('nav-away');}
 else if(d<0){up-=d;dn=0;if(up>90)b.classList.remove('nav-away');}
}
addEventListener('scroll',function(){
 if(!ticking){ticking=true;requestAnimationFrame(frame);}},{passive:true});
addEventListener('focusin',function(e){
 var h=document.querySelector('header.top');
 if(h&&h.contains(e.target))b.classList.remove('nav-away');});
frame();
})();
</script>"""
