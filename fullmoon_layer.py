#!/usr/bin/env python3
"""/full-moon — วันเพ็ญที่วัด, the full moon at the wats, through the year.

NaN, 2026-09-27: "check if there's a full moon festival tonight (and each month)
and which wats are celebrating. Fully relate/integrate/link, indra's net fashion.
Also create a minisite about the full moon at wats, throughout the year. Post all
of this to motdang, everywhere it goes."

    /full-moon/                 tonight, the next full moon, the year drawn as a ring
    /full-moon/<date>/          one full moon: its names, what happens, which wats
    /full-moon/wats/            every wat on the list, and what it keeps
    /full-moon/how/             what a person does at a wat on the day

THE DATES are the published Thai lunar calendar (data/curated/full_moon.json says
which), not the astronomical moment: the two differ by a day in either direction,
and the wat keeps the published one.

WHAT A PAGE SAYS ABOUT A WAT comes from a dated source named beside it. A line
from a past year says the year; nothing here promises that a wat will hold a
thing again.

THE NET. Every page that belongs to it points at the others: each member wat's
place page (and its /wats/w/ page) carries the whole list, the wat shelves and
the festival pages carry a door, the front page and the calendar link the day.
stamp() writes those into an already-built docs/, between marker comments, so
running it twice changes nothing.

    python3 fullmoon_layer.py          # write docs/full-moon/ and stamp docs/
    fullmoon_layer.emit(DOCS)          # what build.py calls
"""
import datetime
import html
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import homebits  # noqa: E402
from homebits import icon  # noqa: E402

DATA = ROOT / "data" / "curated" / "full_moon.json"
FEST = ROOT / "data" / "festivals.json"
PATHS = ROOT / "cache" / "place_paths.json"
CSSDIR = ROOT / "assets" / "minisite"
BASE = "https://motdang.net/"
HERE = BASE + "full-moon/"
EXPLAINER = "https://nanobotco.github.io/indras-net/"
DOCS = ROOT / "docs"

TH_MONTH = homebits.TH_MONTH
EN_MONTH = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TH_WEEKDAY = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
TH_MON_SHORT = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.",
                "ต.ค.", "พ.ย.", "ธ.ค."]
FEST_MOON = {  # festival pages that belong to a full moon, and which observance
    "makha-bucha": "makha", "visakha-bucha": "visakha", "visakha-doi-suthep-walk": "visakha",
    "asalha-bucha": "asanha", "khao-phansa": "asanha", "ok-phansa": "ok_phansa",
    "yi-peng-loi-krathong": "yi_peng", "tan-kuay-salak": "salak",
}


def E(x):
    return html.escape(str(x), quote=True)


def bi(th, en):
    return (f'<span class="bi"><span class="th" lang="th">{E(th)}</span>'
            f'<span class="en" lang="en">{E(en)}</span></span>')


def load():
    d = json.loads(DATA.read_text())
    fest = {f["id"]: f for f in json.loads(FEST.read_text())["festivals"]}
    paths = json.loads(PATHS.read_text()) if PATHS.exists() else {}
    return d, fest, paths


def thai_date(iso, weekday=True):
    d = datetime.date.fromisoformat(iso)
    wd = TH_WEEKDAY[d.weekday()] if weekday else ""
    return f'{("วัน" + wd + "ที่ ") if wd else ""}{d.day} {TH_MONTH[d.month]} {d.year + 543}'


def en_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%a %-d %b %Y")


def moon_svg(illum=1.0, waxing=True, r=60, cls="bigmoon"):
    return homebits.moon(illum, waxing, r).replace('class="moon"', f'class="moon {cls}"', 1)


# ---------------------------------------------------------------- the wats

def wat_links(w, paths, docs):
    """(place page, /wats/w page or None) as site paths, or (None, None)."""
    p = paths.get(w.get("id") or "")
    if not p:
        return None, None
    place = p + ".html" if not p.endswith(".html") else p
    wpage = "wats/w/" + place.rsplit("/", 1)[-1]
    return place, (wpage if (docs / wpage).exists() else None)


def hold_when(h, lang):
    """How a hold is dated, plainly: a date, a past year, or monthly."""
    w = h.get("when") or ""
    if w == "monthly":
        return "ทุกเดือน" if lang == "th" else "every month"
    if not w:
        return ""
    y = int(w[:4])
    if h["conf"] == "announced":
        return thai_date(w, False) if lang == "th" else en_date(w)
    return f"เมื่อปี {y + 543}" if lang == "th" else f"in {y}"


CONF = {
    "announced": ("ประกาศแล้ว", "announced"),
    "past-year": ("เคยจัด", "held before"),
    "recurring": ("ทุกเดือน", "every month"),
    "disputed": ("ที่มาไม่ตรงกัน", "sources disagree"),
}


def hold_li(h, obs, prefix=BASE, with_obs=True):
    o = obs[h["obs"]]
    th = [h["th"]]
    en = [h["en"]]
    tw, ew = hold_when(h, "th"), hold_when(h, "en")
    if tw:
        th.append(tw)
        en.append(ew)
    if h.get("time"):
        th.append(h["time"])
        en.append(h["time"])
    c = CONF[h["conf"]]
    tag = f'<span class="conf c-{E(h["conf"])}">{bi(c[0], c[1])}</span>'
    head = f'<b>{bi(o["th"], o["en"])}</b> ' if with_obs else ""
    src = h["src"]
    return (f'<li>{head}{tag}<span class="hl">{bi(" · ".join(th), " · ".join(en))}</span>'
            f'<a class="src" href="{E(src["url"])}" rel="noopener">{E(src["label"])}</a></li>')


def wats_for(obs_keys, wats):
    """Wats that keep one of these observances, plus the ones that keep every full moon."""
    out = []
    for w in wats:
        hs = [h for h in w["holds"] if h["obs"] in obs_keys or h.get("when") == "monthly"]
        if hs:
            out.append((w, hs))
    return out


# ---------------------------------------------------------------- the ring

def ring_svg(moons, today):
    """The year as a ring: one bright disc per full moon, placed by its date, the
    Lanna month beside it, and a hand where today is. Drawn from the table."""
    W, cx, cy, R = 360, 180, 180, 128
    years = sorted({m["date"][:4] for m in moons})
    y = str(today.year) if str(today.year) in years else years[0]
    start = datetime.date(int(y), 1, 1)
    days = (datetime.date(int(y) + 1, 1, 1) - start).days

    def ang(iso):
        t = (datetime.date.fromisoformat(iso) - start).days / days
        return 2 * math.pi * t - math.pi / 2

    parts = [f'<svg class="ring" viewBox="0 0 {W} {W}" role="img" '
             f'aria-label="วันเพ็ญทั้งปี {int(y) + 543} · the full moons of {y}">',
             f'<circle cx="{cx}" cy="{cy}" r="{R}" class="track"/>']
    for k in range(12):  # month ticks
        a = ang(f"{y}-{k + 1:02d}-01")
        x1, y1 = cx + (R - 8) * math.cos(a), cy + (R - 8) * math.sin(a)
        x2, y2 = cx + (R + 8) * math.cos(a), cy + (R + 8) * math.sin(a)
        tx, ty = cx + (R - 26) * math.cos(a + .26), cy + (R - 26) * math.sin(a + .26)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="tick"/>'
                     f'<text x="{tx:.1f}" y="{ty:.1f}" class="mon">{TH_MON_SHORT[k + 1]}</text>')
    for m in moons:
        if m["date"][:4] != y:
            continue
        a = ang(m["date"])
        x, yy = cx + R * math.cos(a), cy + R * math.sin(a)
        big = m["obs"][0] != "plain"
        past = m["date"] < today.isoformat()
        lx, ly = cx + (R + 30) * math.cos(a), cy + (R + 30) * math.sin(a)
        parts.append(
            f'<a href="{HERE}{m["date"]}/"><title>{E(m["peng_th"])} · {E(en_date(m["date"]))}</title>'
            f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{13 if big else 9}" '
            f'class="fm{" big" if big else ""}{" past" if past else ""}"/>'
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" class="lm">{E(m["lanna_month"].replace("b", "²"))}</text></a>')
    a = ang(today.isoformat()) if today.year == int(y) else None
    if a is not None:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + (R - 18) * math.cos(a):.1f}" '
                     f'y2="{cy + (R - 18) * math.sin(a):.1f}" class="hand" id="hand"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" class="hub"/>'
                 f'<text x="{cx}" y="{cy + 34}" class="yr">{int(y) + 543}</text>'
                 f'<text x="{cx}" y="{cy + 52}" class="yr2">{y}</text></svg>')
    return "".join(parts)


# ---------------------------------------------------------------- pages

EXTRA_CSS = """
/* a pair inside running text reads as two lines, the English in plain weight */
p>.bi,.hl>.bi,.steps .bi,.notice>.bi,.obs p>.bi{display:flex;gap:.15rem}
p>.bi .en,.hl .bi .en,.steps .bi .en,.notice .bi .en,.why .bi .en,.obs p .bi .en{
 text-transform:none;letter-spacing:0;font-weight:400;font-size:.92em;color:var(--mute)}
.notice .bi .en{color:#fff}
h1 .bi .en{font-size:.5em}
.tonight .bi .en{font-size:.62em;text-transform:none;letter-spacing:.02em}
.fmhead{display:grid;grid-template-columns:auto 1fr;gap:1.2rem;align-items:center;margin:1.4rem 0}
@media(max-width:34rem){.fmhead{grid-template-columns:1fr;justify-items:center;text-align:center}}
.moon .dark{fill:color-mix(in srgb,var(--road) 82%,var(--panel))}
.moon .lit{fill:#f6e6b4}
.moon .rim{fill:none;stroke:color-mix(in srgb,var(--ink) 35%,transparent);stroke-width:1}
.bigmoon{width:9rem;height:9rem;filter:drop-shadow(0 0 22px rgba(246,230,180,.55))}
.tonight{font-family:var(--display);font-size:clamp(1.3rem,4.4vw,2rem);font-weight:800;
 line-height:1.15;margin:0 0 .3rem}
.tonight .en{display:block;font-size:.62em;color:var(--mute);letter-spacing:.03em}
.count{font-family:var(--mono);font-size:.9rem;color:var(--mute);margin:.2rem 0}
.fmcards{display:grid;gap:.7rem;grid-template-columns:repeat(auto-fill,minmax(min(17rem,100%),1fr));
 margin:1rem 0 1.6rem}
.fmcard{display:grid;grid-template-columns:auto 1fr;gap:.2rem .7rem;align-items:start;
 border:2px solid var(--ink);background:var(--panel);padding:.7rem .8rem;text-decoration:none;
 color:var(--ink);box-shadow:4px 4px 0 var(--ink)}
.fmcard:hover{transform:translate(2px,2px);box-shadow:2px 2px 0 var(--ink)}
.fmcard.past{opacity:.62;box-shadow:none;border-color:var(--line)}
.fmcard.big{background:color-mix(in srgb,#f6e6b4 28%,var(--panel))}
.fmcard .d{font-family:var(--display);font-weight:800;font-size:1.5rem;line-height:1;text-align:center}
.fmcard .d small{display:block;font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mute)}
.fmcard .w{font-size:.94rem;line-height:1.35}
.fmcard .w b{display:block}
.fmcard .pg{font-size:.78rem;color:var(--mute)}
.fmcard .dry{display:inline-block;margin-top:.2rem;font-size:.72rem;font-weight:800;
 background:var(--hot);color:#fff;padding:0 .35rem}
.ring{width:min(100%,26rem);display:block;margin:1rem auto 1.6rem}
.ring .track{fill:none;stroke:var(--line);stroke-width:3}
.ring .tick{stroke:var(--mute);stroke-width:1.5}
.ring .mon{font-family:var(--thai);font-size:10px;fill:var(--mute);text-anchor:middle}
.ring .fm{fill:#f6e6b4;stroke:var(--ink);stroke-width:1.5}
.ring .fm.big{fill:#ffd54a}
.ring .fm.past{opacity:.45}
.ring a:hover .fm,.ring a:focus .fm{stroke:var(--hot);stroke-width:3}
.ring .lm{font-family:var(--display);font-size:11px;font-weight:800;fill:var(--ink);text-anchor:middle}
.ring .hand{stroke:var(--hot);stroke-width:3;stroke-linecap:round}
.ring .hub{fill:var(--hot)}
.ring .yr{font-family:var(--display);font-size:22px;font-weight:800;fill:var(--ink);text-anchor:middle}
.ring .yr2{font-family:var(--mono);font-size:12px;fill:var(--mute);text-anchor:middle}
ul.holds{list-style:none;padding:0;margin:.4rem 0 1rem}
ul.holds li{border-top:1px solid var(--line);padding:.45rem 0;line-height:1.45}
ul.holds li .hl{display:block}
ul.holds .src{display:inline-block;font-size:.74rem;color:var(--mute);margin-top:.15rem}
.conf{display:inline-block;font-size:.66rem;font-weight:800;padding:0 .3rem;margin-right:.3rem;
 border:1px solid var(--line);vertical-align:.1em}
.conf .bi{display:inline}.conf .en{display:inline;margin-left:.25rem}
.conf.c-announced{background:#ffd54a;color:#17110c;border-color:#17110c}
.conf.c-disputed{background:var(--chip)}
.watbox{border:2px solid var(--ink);background:var(--panel);padding:.7rem .9rem;margin:.8rem 0}
.watbox h3{margin:0 0 .1rem}
.watbox .where{font-size:.82rem;color:var(--mute);margin:0 0 .3rem}
.watbox .go{display:flex;gap:.4rem;flex-wrap:wrap;margin:.3rem 0 0}
.watbox .go a{font-size:.8rem;font-weight:700}
.obs{border-left:6px solid #ffd54a;padding:.2rem 0 .2rem .8rem;margin:1rem 0}
.obs h3{margin:.1rem 0}
.notice{border:2px solid var(--ink);background:var(--hot);color:#fff;padding:.6rem .8rem;
 font-weight:700;margin:1rem 0}
.notice a{color:#fff}
.steps{counter-reset:s;list-style:none;padding:0}
.steps li{counter-increment:s;position:relative;padding:.6rem 0 .6rem 2.6rem;border-top:1px solid var(--line)}
.steps li::before{content:counter(s);position:absolute;left:0;top:.55rem;width:1.9rem;height:1.9rem;
 border-radius:50%;background:#ffd54a;color:#17110c;font-family:var(--display);font-weight:800;
 display:grid;place-items:center;border:2px solid var(--ink)}
.pn{display:flex;justify-content:space-between;gap:.6rem;flex-wrap:wrap;margin:1.6rem 0}
.srcs{font-size:.78rem;color:var(--mute)}
.srcs a{color:var(--mute)}
.fmnav{display:flex;gap:.4rem;flex-wrap:wrap;margin:1rem 0}
"""

TONIGHT_JS = r"""<script>
(function(){
var el=document.getElementById('fm-data');if(!el)return;var M=JSON.parse(el.textContent);
var now=new Date(Date.now()+7*36e5),iso=now.toISOString().slice(0,10);
function days(a,b){return Math.round((Date.parse(b)-Date.parse(a))/864e5);}
var next=null,last=null;M.moons.forEach(function(m){if(m.d>=iso&&!next)next=m;if(m.d<iso)last=m;});
var t=document.getElementById('tonight'),c=document.getElementById('count');
if(t&&next){var n=days(iso,next.d),s;
 if(n===0)s=['คืนนี้วันเพ็ญ '+next.pth,'Full moon tonight — '+next.pen];
 else if(n===1)s=['พรุ่งนี้วันเพ็ญ '+next.pth,'Full moon tomorrow — '+next.pen];
 else if(last&&days(last.d,iso)===1)s=['เมื่อคืนวันเพ็ญ '+last.pth,'The full moon was last night — '+last.pen];
 else s=['อีก '+n+' วันถึงวันเพ็ญ','Full moon in '+n+' days'];
 t.innerHTML='<span class="th" lang="th">'+s[0]+'</span><span class="en">'+s[1]+'</span>';
 if(c)c.textContent=next.th+' · '+next.en;}
/* the moon as it is tonight: age from a known new moon, 29.530589-day month */
var age=((Date.now()/864e5-10962.759)%29.530589+29.530589)%29.530589;
var f=(1-Math.cos(2*Math.PI*age/29.530589))/2,wax=age<14.765;
var mv=document.querySelector('.bigmoon.live');
if(mv){var p=mv.querySelector('.lit'),r=60,rx=r*Math.abs(1-2*f),sw=f>.5?1:0;
 p.setAttribute('d','M0 '+(-r)+'A'+r+' '+r+' 0 0 1 0 '+r+'A'+rx.toFixed(2)+' '+r+' 0 0 '+sw+' 0 '+(-r));
 if(wax)p.removeAttribute('transform');else p.setAttribute('transform','scale(-1,1)');}
})();
</script>"""


def shell(title, desc, body, canon, data_json=""):
    import home_next  # the front page's own additions, so the bar, the icons and the
    #                   Thai-over-English pairs look the same here as there
    css = ((CSSDIR / "kit.css").read_text() + (CSSDIR / "bands.css").read_text()
           + home_next.EXTRA + EXTRA_CSS)
    nav = (f'<a href="{HERE}">{icon("i-fullmoon", 18)}<span class="th" lang="th">วันเพ็ญ</span>'
           f'<span class="en">Full moon</span></a>'
           f'<a href="{HERE}wats/">{icon("i-wat", 18)}<span class="th" lang="th">วัด</span>'
           f'<span class="en">Wats</span></a>'
           f'<a href="{HERE}how/">{icon("i-lotus", 18)}<span class="th" lang="th">ทำอย่างไร</span>'
           f'<span class="en">How</span></a>'
           f'<a href="{BASE}calendar.html">{icon("i-cal", 18)}<span class="th" lang="th">ปฏิทิน</span>'
           f'<span class="en">Calendar</span></a>')
    js = (f'<script type="application/json" id="fm-data">{data_json}</script>{TONIGHT_JS}'
          if data_json else "")
    sprite = homebits.sprite_defs()
    return homebits.pair_bare(f"""<!DOCTYPE html>
<html lang="th" translate="no" class="notranslate lang-both"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="google" content="notranslate">
{homebits.LANG_HEAD}
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(canon)}">
<link rel="icon" href="{BASE}logo/motdang-favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="มดแดง Mot Dang">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{E(canon)}">
<meta property="og:image" content="{BASE}site/hero/golden-chedi-flags.jpg">
<meta name="twitter:card" content="summary_large_image">
<style>{css}{homebits.LANG_CSS}</style>
</head><body>
{sprite}
<a class="skip" href="#main">ข้ามไปเนื้อหา · Skip to content</a>
<header class="top"><div class="in">
 <a class="brand" href="{BASE}">MOT <b>DANG</b></a>
 <nav>{nav}</nav>
 {homebits.LANG_SWITCH}
</div></header>
<main id="main">{body}</main>
{js}{homebits.LANG_JS}
<footer class="bot"><div class="in">
 <p><b>วันเพ็ญที่วัด · Full moon at the wat</b> — part of <a href="{BASE}">มดแดง Mot Dang</a>,
 เชียงใหม่ · เชียงราย. Built by NaN. Text and data
 <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</p>
 <p class="small"><a href="{BASE}festivals.html">เทศกาล · festivals</a> ·
 <a href="{BASE}wats/">ไหว้พระ ๙ วัด · nine wats</a> ·
 <a href="{BASE}calendar.html">ปฏิทิน · calendar</a> ·
 <a href="{BASE}cm/wat/">วัดเชียงใหม่ · Chiang Mai wats</a> ·
 <a href="{BASE}cr/wat/">วัดเชียงราย · Chiang Rai wats</a> ·
 <a href="{EXPLAINER}" rel="noopener">Indra's Net, Drawn</a></p>
</div></footer>
</body></html>""")


def moon_card(m, obs, today, fest):
    o = [obs[k] for k in m["obs"]]
    past = m["date"] < today.isoformat()
    big = m["obs"][0] != "plain"
    dry = any(x.get("dry") for x in o) or any(x.get("dry") for x in m["extra"])
    d = datetime.date.fromisoformat(m["date"])
    what = "".join(f'<b>{bi(x["th"], x["en"])}</b>' for x in o)
    return (f'<a class="fmcard{" past" if past else ""}{" big" if big else ""}" href="{HERE}{m["date"]}/">'
            f'<span class="d">{d.day}<small>{homebits.tx(TH_MON_SHORT[d.month], EN_MONTH[d.month])}</small></span>'
            f'<span class="w">{what}<span class="pg">'
            f'{homebits.tx(E(m["peng_th"]) + " · " + E(m["weekday_th"]), E(m["weekday"]))}</span>'
            f'{"<span class=dry>ห้ามขายเหล้าเบียร์ · no alcohol sales</span>" if dry else ""}'
            f'</span></a>')


def src_line(keys, d):
    links = " · ".join(f'<a href="{E(d["sources"][k]["url"])}" rel="noopener">{E(d["sources"][k]["label"])}</a>'
                       for k in keys if k in d["sources"])
    return f'<p class="srcs">{bi("ที่มา", "Sources")}: {links}</p>' if links else ""


def watbox(w, hs, obs, paths, docs, with_obs=True):
    place, wpage = wat_links(w, paths, docs)
    name = (f'<a href="{BASE}{E(place)}">{bi(w["th"], w["en"])}</a>' if place
            else bi(w["th"], w["en"]))
    go = []
    if place:
        go.append(f'<a href="{BASE}{E(place)}">{icon("i-pin", 14)}หน้าวัด · the page for this wat</a>')
    if wpage:
        go.append(f'<a href="{BASE}{E(wpage)}">{icon("i-wat", 14)}ไหว้พระ · on the wat rounds</a>')
    prov = (homebits.tx("เชียงใหม่", "Chiang Mai") if w["prov"] == "cm"
            else homebits.tx("เชียงราย", "Chiang Rai"))
    return (f'<div class="watbox"><h3>{name}</h3>'
            f'<p class="where">{homebits.tx("อ." + E(w["amphoe_th"]), E(w["amphoe_en"]))} · {prov}</p>'
            f'<ul class="holds">{"".join(hold_li(h, obs, with_obs=with_obs) for h in hs)}</ul>'
            f'{"<p class=go>" + " ".join(go) + "</p>" if go else ""}</div>')


def page_index(d, fest, paths, docs, today):
    obs, moons = d["observances"], d["moons"]
    nxt = next((m for m in moons if m["date"] >= today.isoformat()), moons[-1])
    o = [obs[k] for k in nxt["obs"]]
    cards = "".join(moon_card(m, obs, today, fest) for m in moons)
    wnext = wats_for(set(nxt["obs"]), d["wats"])
    body = f"""
<section class="fmhead">
 {moon_svg(1.0, True, 60, "bigmoon live")}
 <div>
  <p class="kicker">วันเพ็ญที่วัด · Full moon at the wat</p>
  <h1>{bi("วันเพ็ญที่วัด", "The full moon at the wat")}</h1>
  <p class="tonight" id="tonight">{bi("วันเพ็ญครั้งหน้า " + thai_date(nxt["date"]), "Next full moon " + en_date(nxt["date"]))}</p>
  <p class="count" id="count"></p>
 </div>
</section>
<p>{bi("วันขึ้น 15 ค่ำ ทุกเดือนเป็นวันพระ คนไปทำบุญที่วัด บางเดือนมีงานใหญ่ ข้างล่างคือวันเพ็ญทุกครั้ง ว่าวันไหน เดือนอะไรตามแบบล้านนา มีงานอะไร และวัดไหนจัด",
        "Every full moon is a wan phra, a Buddhist holy day, and people go to the wat. Some months carry a big festival. Below is every full moon: the date, its northern (Lanna) month name, what happens, and which wats hold it.")}</p>

<h2 id="next">{bi("วันเพ็ญครั้งหน้า", "The next full moon")}</h2>
<div class="fmcards">{moon_card(nxt, obs, today, fest)}</div>
{_moon_band(nxt["obs"], [(k, obs[k]) for k in nxt["obs"]])}
{"".join(f'<div class="obs"><h3>{bi(x["th"], x["en"])}</h3><p>{bi(x["what_th"], x["what_en"])}</p></div>' for x in o)}
{"".join(watbox(w, hs, obs, paths, docs) for w, hs in wnext[:6])}
<p class="fmnav"><a class="btn" href="{HERE}{nxt["date"]}/">{icon("i-fullmoon", 20)} {E(thai_date(nxt["date"], False))} · {E(en_date(nxt["date"]))}</a>
<a class="btn alt" href="{HERE}wats/">{icon("i-wat", 20)} วัดทั้งหมด · All the wats</a></p>

<h2 id="year">{bi("ทั้งปี", "The year")}</h2>
{ring_svg(moons, today)}
<div class="fmcards">{cards}</div>
<p>{bi("ตัวเลขข้างดวงจันทร์คือเดือนล้านนา ทางเหนือนับเดือนเร็วกว่าภาคกลางสองเดือน ปี 2569 มีเดือนแปดสองหน (อธิกมาส) วันมาฆบูชาจึงเลื่อนไปเดือนสี่ วิสาขบูชาไปเดือนเจ็ด",
        "The number by each moon is its northern (Lanna) month, which runs two ahead of central Thailand's. 2026 has a second eighth month, so Makha Bucha moved to the fourth month's full moon and Visakha Bucha to the seventh's.")}</p>

<h2 id="more">{bi("อ่านต่อ", "More")}</h2>
<p class="fmnav"><a class="btn alt" href="{HERE}how/">{icon("i-lotus", 20)} ไปวัดวันพระ · At the wat on the day</a>
<a class="btn alt" href="{BASE}festivals.html">{icon("i-party", 20)} เทศกาล · Festivals</a>
<a class="btn alt" href="{BASE}calendar.html">{icon("i-cal", 20)} ปฏิทิน · Calendar</a>
<a class="btn alt" href="{BASE}wats/">{icon("i-route", 20)} ไหว้พระ ๙ วัด · Nine wats</a></p>
{src_line(["tpbs", "myhora69", "myhora70", "mondee", "rmutl"], d)}
"""
    return shell("วันเพ็ญที่วัด · The full moon at the wat — Mot Dang",
                 "Every full moon of the year in Chiang Mai and Chiang Rai: the date on the Thai lunar calendar, the northern month name, what happens at the wat, and which wats hold it.",
                 body, HERE, fm_json(d))


def fm_json(d):
    rows = [{"d": m["date"], "pth": m["peng_th"], "pen": m["peng_en"],
             "th": thai_date(m["date"]), "en": en_date(m["date"])} for m in d["moons"]]
    return json.dumps({"moons": rows}, ensure_ascii=False, separators=(",", ":"))


def _moon_band(keys, o):
    """A Commons photograph of what this full moon is kept with (commons_layer)."""
    try:
        import commons_layer
        for k in keys:
            ps = commons_layer.observance_picks(k, 1)
            if ps:
                x = dict(o).get(k) or {}
                return commons_layer.band(ps[0], bi(x.get("th", ""), x.get("en", "")), BASE, E, E,
                                          E(commons_layer._short(ps[0].get("description"), 90)))
    except Exception as e:                       # noqa: BLE001 — a picture never costs a page
        print("  ! full-moon band:", e)
    return ""


def page_moon(i, d, fest, paths, docs, today):
    obs, moons = d["observances"], d["moons"]
    m = moons[i]
    prv = moons[i - 1] if i else None
    nxt = moons[i + 1] if i + 1 < len(moons) else None
    o = [(k, obs[k]) for k in m["obs"]]
    dry = any(x.get("dry") for _, x in o)
    parts = []
    for k, x in o:
        f = fest.get(x.get("festival") or "")
        link = (f'<p><a href="{BASE}festivals/{E(f["id"])}.html">{icon("i-party", 16)} '
                f'{bi("หน้าเทศกาล " + f["name_th"], "The festival page: " + f["name_en"].split(" — ")[0])}</a></p>'
                if f else "")
        parts.append(f'<div class="obs"><h3>{bi(x["th"], x["en"])}</h3>'
                     f'<p>{bi(x["what_th"], x["what_en"])}</p>{link}</div>')
    extra = "".join(
        f'<div class="obs"><h3>{bi(x["th"], x["en"])}</h3><p>{E(thai_date(x["d"]))} · {E(en_date(x["d"]))}</p>'
        + (f'<p><a href="{BASE}festivals/{E(x["festival"])}.html">{bi("หน้าเทศกาล", "The festival page")}</a></p>'
           if x.get("festival") in fest else "") + "</div>"
        for x in m["extra"])
    notice = (f'<p class="notice">{bi(d["dry"]["th"], d["dry"]["en"])}</p>'
              if dry or any(x.get("dry") for x in m["extra"]) else "")
    wl = wats_for(set(m["obs"]), d["wats"])
    none_yet = bi("ยังไม่มีวัดไหนประกาศงานเฉพาะสำหรับวันนี้ในรายการของเรา วัดทั่วไปทำบุญตักบาตรตอนเช้าตามปกติ",
                  "No wat on our list has announced anything special for this day. Wats hold the usual morning alms.")
    wats_html = ("".join(watbox(w, hs, obs, paths, docs) for w, hs in wl) if wl else
                 "<p>" + none_yet + "</p>")
    past = m["date"] < today.isoformat()
    body = f"""
<section class="fmhead">
 {moon_svg(1.0, True, 60)}
 <div>
  <p class="kicker">วันเพ็ญที่วัด · Full moon at the wat</p>
  <h1>{bi(m["peng_th"], m["peng_en"])}</h1>
  <p class="tonight">{bi(thai_date(m["date"]), en_date(m["date"]))}</p>
  <p class="count">{E(m["central_th"])} · {"ผ่านไปแล้ว · past" if past else ""}</p>
 </div>
</section>
{notice}
{_moon_band(m["obs"], o)}
<h2>{bi("มีอะไร", "What happens")}</h2>
{"".join(parts)}{extra}
<h2>{bi("วัดไหนจัด", "Which wats")}</h2>
{wats_html}
<p class="fmnav"><a class="btn alt" href="{BASE}calendar.html">{icon("i-cal", 20)} ปฏิทิน · Calendar</a>
<a class="btn alt" href="{HERE}how/">{icon("i-lotus", 20)} ไปวัดวันพระ · At the wat</a></p>
<nav class="pn">
 {f'<a class="btn alt" href="{HERE}{prv["date"]}/">← {E(prv["peng_th"])} · {E(en_date(prv["date"]))}</a>' if prv else "<span></span>"}
 <a class="btn alt" href="{HERE}#year">{icon("i-fullmoon", 18)} ทั้งปี · The year</a>
 {f'<a class="btn alt" href="{HERE}{nxt["date"]}/">{E(nxt["peng_th"])} · {E(en_date(nxt["date"]))} →</a>' if nxt else "<span></span>"}
</nav>
{src_line(sorted({s for _, x in o for s in x.get("src", [])}) + ["tpbs", "myhora69"], d)}
"""
    names = " · ".join(x["en"] for _, x in o)
    return shell(f'{m["peng_th"]} {thai_date(m["date"], False)} · {names} — Mot Dang',
                 f'The full moon of {en_date(m["date"])} ({m["peng_en"]}, {m["central_th"]}): {names}. What happens at the wat in Chiang Mai and Chiang Rai, and which wats hold it.',
                 body, f'{HERE}{m["date"]}/')


def page_wats(d, fest, paths, docs, today):
    obs = d["observances"]
    out = []
    for prov, th, en in (("cm", "เชียงใหม่", "Chiang Mai"), ("cr", "เชียงราย", "Chiang Rai")):
        ws = [w for w in d["wats"] if w["prov"] == prov]
        out.append(f'<h2>{bi(th, en)} <b class="n">{len(ws)}</b></h2>')
        out.extend(watbox(w, w["holds"], obs, paths, docs) for w in ws)
    body = f"""
<h1>{bi("วัดที่จัดงานวันเพ็ญ", "Wats that keep the full moon")}</h1>
<p>{bi("แต่ละบรรทัดบอกว่าเอามาจากไหน และปีไหน ป้ายเหลือง ประกาศแล้ว คือมีประกาศสำหรับวันนั้น ป้าย เคยจัด คือจัดในปีที่เขียนไว้ ก่อนไปถามวัดหรือดูประกาศปีนี้",
        "Each line names its source and its year. A yellow 'announced' tag means a notice for that date; 'held before' means held in the year shown. Before you go, ask the wat or look for this year's notice.")}</p>
{"".join(out)}
<p class="fmnav"><a class="btn alt" href="{HERE}">{icon("i-fullmoon", 20)} วันเพ็ญทั้งปี · Every full moon</a>
<a class="btn alt" href="{BASE}wats/">{icon("i-route", 20)} ไหว้พระ ๙ วัด · Nine wats</a></p>
"""
    return shell("วัดที่จัดงานวันเพ็ญ · Wats that keep the full moon — Mot Dang",
                 "Wats in Chiang Mai and Chiang Rai that hold full-moon events — candle walks, salak baskets, Tak Bat Thewo, Yi Peng — each with its dated source.",
                 body, HERE + "wats/")


def page_how(d):
    steps = "".join(f'<li>{bi(s["th"], s["en"])}</li>' for s in d["how"])
    keys = sorted({k for s in d["how"] for k in s["src"]})
    body = f"""
<h1>{bi("ไปวัดวันพระ", "At the wat on a full-moon day")}</h1>
<ol class="steps">{steps}</ol>
<h2>{bi("เหล้าเบียร์", "Alcohol")}</h2>
<p class="notice">{bi(d["dry"]["th"], d["dry"]["en"])}</p>
{src_line(keys + d["dry"]["src"], d)}
<p class="fmnav"><a class="btn alt" href="{HERE}">{icon("i-fullmoon", 20)} วันเพ็ญทั้งปี · Every full moon</a>
<a class="btn alt" href="{HERE}wats/">{icon("i-wat", 20)} วัดไหนจัด · Which wats</a></p>
"""
    return shell("ไปวัดวันพระ · At the wat on a full-moon day — Mot Dang",
                 "What people do at a wat on a full-moon day in northern Thailand: morning alms, the precepts, the candle walk on the big nights, what to wear, and the no-alcohol days.",
                 body, HERE + "how/")


# ---------------------------------------------------------------- the net, stamped

MARK = ("<!-- fm:net -->", "<!-- /fm:net -->")
WHY_NET = bi("ทำไมเป็นตาข่าย", "Why a net — Indra's Net, Drawn")

STAMP_CSS = """<style>
.fmnet{margin:1rem 0;padding:.8rem .9rem;border:2px solid var(--ink,#2a1e16);border-radius:.8rem;
 background:var(--card,#fffdf7);box-shadow:3px 3px 0 #ffd54a}
.fmnet h2{margin:0 0 .3rem;font-size:1.05rem}
.fmnet ul{list-style:none;padding:0;margin:.3rem 0}
.fmnet li{padding:.25rem 0;line-height:1.45}
.fmnet li .why{display:block;font-size:.88rem;opacity:.8}
.fmnet li.here{background:#fff3c4;color:#2a1e16;border-radius:.4rem;padding:.3rem .45rem}
.fmnet .fmsrc{font-size:.78rem;opacity:.8;margin:.4rem 0 0}
.fmnet details{margin:.4rem 0 0}.fmnet summary{cursor:pointer;font-weight:700}
</style>"""


def _strip(html_text):
    return re.sub(re.escape(MARK[0]) + r".*?" + re.escape(MARK[1]), "", html_text, flags=re.S)


def _put(path, block, before=None, after=None):
    """Insert block (marked) before the first `before` or after the first `after`;
    an earlier stamp is removed first, so this is safe to run again."""
    if not path.exists():
        return False
    t = _strip(path.read_text())
    b = MARK[0] + block + MARK[1]
    if before and before in t:
        t = t.replace(before, b + before, 1)
    elif after and after in t:
        t = t.replace(after, after + b, 1)
    else:
        return False
    path.write_text(t)
    return True


def net_block(w, d, paths, docs, rel):
    """The whole list on a member wat's page: what this wat keeps, then every other
    wat in the net — each page shows all the others."""
    obs = d["observances"]
    mine = "".join(
        f'<li class="here"><b>{bi(obs[h["obs"]]["th"], obs[h["obs"]]["en"])}</b>'
        f'<span class="why">{bi(h["th"], h["en"])} · {E(hold_when(h, "th"))} · {E(hold_when(h, "en"))} · '
        f'<a href="{E(h["src"]["url"])}" rel="noopener">{E(h["src"]["label"])}</a></span></li>'
        for h in w["holds"])
    others = []
    for o in d["wats"]:
        if o is w:
            continue
        place, _ = wat_links(o, paths, docs)
        kinds = " · ".join(dict.fromkeys(obs[h["obs"]]["th"] for h in o["holds"]))
        kinds_en = " · ".join(dict.fromkeys(obs[h["obs"]]["en"] for h in o["holds"]))
        name = (f'<a href="{rel}{E(place)}">{bi(o["th"], o["en"])}</a>' if place
                else bi(o["th"], o["en"]))
        others.append(f'<li>{name}<span class="why">{bi(kinds, kinds_en)}</span></li>')
    return (f'{STAMP_CSS}<section class="fmnet" id="full-moon">'
            f'<h2>{bi("วันเพ็ญที่วัดนี้", "Full moon at this wat")}</h2>'
            f'<ul>{mine}</ul>'
            f'<details><summary>{bi("ร้อยไว้ในตาข่ายเดียวกัน — วัดอื่นที่จัดงานวันเพ็ญ", "Strung in the same net — the other wats that keep the full moon")} ({len(others)})</summary>'
            f'<ul>{"".join(others)}</ul></details>'
            f'<p class="fmsrc"><a href="{HERE}">{bi("วันเพ็ญทั้งปี", "Every full moon of the year")}</a> · '
            f'<a href="{HERE}wats/">{bi("วัดทั้งหมด", "All the wats")}</a> · '
            f'<a href="{EXPLAINER}" rel="noopener">{WHY_NET}</a></p>'
            f'</section>')


def door(th, en, href):
    return (f'{STAMP_CSS}<p class="fmnet" style="padding:.5rem .8rem"><a href="{E(href)}">'
            f'{bi(th, en)}</a></p>')


def stamp(docs=DOCS, d=None, fest=None, paths=None):
    if d is None:
        d, fest, paths = load()
    today = datetime.date.today()
    n = 0
    # member wats: the place page and the wat-rounds page
    for w in d["wats"]:
        place, wpage = wat_links(w, paths, docs)
        for p in (place, wpage):
            if p and _put(docs / p, net_block(w, d, paths, docs, "../../"), before='<footer class="bare">'):
                n += 1
    # the festival pages that belong to a full moon
    for fid, ok in FEST_MOON.items():
        dates = [m for m in d["moons"] if ok in m["obs"] and m["date"] >= today.isoformat()][:2]
        if not dates:
            continue
        ws = [w for w in d["wats"] if any(h["obs"] == ok for h in w["holds"])]
        lis = "".join(f'<li><a href="{HERE}{m["date"]}/">{E(thai_date(m["date"]))} · {E(en_date(m["date"]))}</a></li>'
                      for m in dates)
        wl = []
        for w in ws:
            place, _ = wat_links(w, paths, docs)
            nm = bi(w["th"], w["en"])
            wl.append("<li>" + ('<a href="../' + E(place) + '">' + nm + "</a>" if place else nm) + "</li>")
        block = (f'{STAMP_CSS}<section class="fmnet" id="full-moon"><h2>{bi("วันเพ็ญที่วัด", "Full moon at the wat")}</h2>'
                 f'<ul>{lis}</ul>'
                 + (f'<details open><summary>{bi("วัดที่เคยจัด", "Wats that have held it")} ({len(wl)})</summary><ul>{"".join(wl)}</ul></details>' if wl else "")
                 + f'<p class="fmsrc"><a href="{HERE}">{bi("วันเพ็ญทั้งปี", "Every full moon of the year")}</a></p></section>')
        if _put(docs / "festivals" / f"{fid}.html", block, before='<footer class="bare">'):
            n += 1
    # doors: the wat shelves, the festivals hub, the wat rounds
    for p, rel in (("cm/wat/index.html", "../../"), ("cr/wat/index.html", "../../"),
                   ("festivals.html", ""), ("wats/index.html", "../")):
        if _put(docs / p, door("วันเพ็ญที่วัด — วันไหน วัดไหนจัดงาน", "Full moon at the wat — which day, which wats", HERE),
                after="</h1>"):
            n += 1
    return n


LLMS = """

## วันเพ็ญที่วัด · Full moon at the wat (/full-moon/)
Every full moon of 2026–2027 on the published Thai lunar calendar, with its northern (Lanna) month name,
what happens at the wat, and which wats in Chiang Mai and Chiang Rai hold it — each line with its dated source.
- https://motdang.net/full-moon/ — the next full moon, and the year
- https://motdang.net/full-moon/wats/ — the wats
- https://motdang.net/full-moon/how/ — what people do at a wat on the day
- https://motdang.net/full-moon/<YYYY-MM-DD>/ — one full moon
Data: data/curated/full_moon.json in the source archive.
"""


def llms(docs=DOCS):
    p = docs / "llms.txt"
    if p.exists() and "/full-moon/" not in p.read_text():
        with p.open("a", encoding="utf-8") as f:
            f.write(LLMS)


def emit(docs=DOCS):
    d, fest, paths = load()
    today = datetime.date.today()
    out = docs / "full-moon"
    (out / "wats").mkdir(parents=True, exist_ok=True)
    (out / "how").mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page_index(d, fest, paths, docs, today))
    (out / "wats" / "index.html").write_text(page_wats(d, fest, paths, docs, today))
    (out / "how" / "index.html").write_text(page_how(d))
    for i, m in enumerate(d["moons"]):
        (out / m["date"]).mkdir(exist_ok=True)
        (out / m["date"] / "index.html").write_text(page_moon(i, d, fest, paths, docs, today))
    pages = 3 + len(d["moons"])
    stamped = stamp(docs, d, fest, paths)
    return pages, stamped


def full_moon_dates():
    """For the calendar and the front page: {date: (peng_th, peng_en)}."""
    try:
        return {m["date"]: (m["peng_th"], m["peng_en"]) for m in json.loads(DATA.read_text())["moons"]}
    except (OSError, ValueError, KeyError):
        return {}


if __name__ == "__main__":
    pages, stamped = emit()
    llms()
    print(f"full-moon: {pages} pages, {stamped} pages stamped")
