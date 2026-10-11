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
 </svg>
</div>
<figcaption>{icon('i-pin', 16)} Every place in the catalogue, one dot each.
 Tap a district to open it in the live map.
 <span class="src">{E(MAP_CREDIT)}</span></figcaption>
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


def calendar(today, months=2, k_events=2):
    """Two months, drawn. Every day carries its Thai colour, its moon and its lunar
    day; the dated things sit in the square they fall in."""
    F = json.loads((MD / "data/fortune.json").read_text())["days"]
    S = json.loads((MD / "data/sky.json").read_text())["days"]
    EV = json.loads((MD / "data/events.json").read_text())["events"]

    byday: dict[str, list] = {}
    for e in EV:
        d = (e.get("start") or "")[:10]
        if not d:
            continue
        byday.setdefault(d, []).append(e)

    out = []
    y, m = today.year, today.month
    for _ in range(months):
        first = datetime.date(y, m, 1)
        nxt = datetime.date(y + (m == 12), m % 12 + 1, 1)
        start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)
        cells = []
        d = start
        while d < nxt or d.weekday() != 6:
            cells.append(day_cell(d, d.month == m, today, F, S, byday, k_events))
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


TH_MONTH = {1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน", 5: "พฤษภาคม",
            6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม", 9: "กันยายน", 10: "ตุลาคม",
            11: "พฤศจิกายน", 12: "ธันวาคม"}


def day_cell(d, in_month, today, F, S, byday, k):
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
    evs = byday.get(iso, [])
    if evs:
        li = []
        for e in evs[:k]:
            tt = (e.get("title") or "").strip()
            tt = tt if len(tt) < 46 else tt[:43] + "…"
            if e.get("url"):
                li.append(f'<li><a href="{E(e["url"])}" rel="noopener">{E(tt)}</a></li>')
            else:
                li.append(f"<li>{E(tt)}</li>")
        more = (f'<li class="more">+{len(evs) - k} more</li>' if len(evs) > k else "")
        bits.append(f'<ul class="ev">{"".join(li)}{more}</ul>')
    if d == today:
        bits.append('<p class="tag">วันนี้ · today</p>')
    return f'<div class="{" ".join(cls)}">{"".join(bits)}</div>'
