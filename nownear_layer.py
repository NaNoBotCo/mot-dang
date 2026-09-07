"""WO-65 — ตอนนี้ · ใกล้ๆ  NOW · NEAR. Every page leads with what is happening
now and what is near; everything else is drawered.

Beer's rule (via Nan, 2026-09-06): the most important thing on motdang.net is
what is happening right now and what is nearby — weather, air, today's
events, the reader's own plan. Nan, same afternoon: "as minimal and effective
as possible; easy to wander, not a giant card catalog." So:

  header  = masthead · search · ONE LINE of text (the strip) · ☰
            The ☰ is a closed <details> holding the eight chips and the 27
            svcbar links that used to stand above every page's content.
  home    = the line · three event cards · one map postcard · eight paths ·
            closed folds for everything else (the shelves, the readings, the
            sky and prices, the instruments, the feeds).

Nothing here composes new content. The strip is baked from the same
data/weather.json, data/air.json and events rows the tiles already read; the
home is a re-sort of pieces build.py already made. The strip has no boxes and
no cells: it is a <p> of links separated by " · ", one line, scrolling
sideways on a phone if it must.

📍 here landed 2026-09-07 with here_layer's hook. It stays hidden until the
browser itself reports geolocation as already granted, so the cell advertises
a page only to a reader who has already said yes to the one question it asks.
Nan's call the same day: the chip and this cell, and no homepage hop.

🎪 today is no longer counted at build time. BUILD_DATE is a hand-typed string
and it was two days behind on 2026-09-07, so every page on the site was
reporting Friday's events as today's. The count now comes from a 21-day window
baked into data/today.json and picked by the reader's own clock — the same
mdPick(doc).days[MD_TODAY] pattern the sky and fortune tiles already use, and
the same reasoning as the freshness strip: a baked "today" rots, a computed one
cannot.

What is deliberately NOT in the strip:
  📝 to-do — localStorage 'md-notes' is my.html's sticky-notes textarea,
     free text, not a list. Nothing to count. Fork F2 stays hers.

Called from build.py: strip() in page(), where the ☰ <details> is written
inline around the chips and the svcbar; home() where the spare
front page was composed; CSS and JS appended where style.css and md.js are
written. tests/test_page_weight.py gates the result.
"""

import datetime
import re

# The eight paths — the questions people actually bring, ranked by go/gptmine
# on 2026-09-05 (shopping 96 · clinics 50 · food 49 · activities 35 ·
# services 24 · transport 19 · pharmacy 17 · massage 5). Chiang Mai shelves,
# because that is where the demand was measured; Chiang Rai's shelves sit one
# fold down. Re-cut whenever ask.motdang.net's search_log says otherwise.
PATHS = (
    ("cm/shopping/", "🛍", "ช้อปปิ้ง", "shopping"),
    ("cm/medical/clinic/", "🩺", "คลินิก", "clinics"),
    ("cm/food/", "🍜", "ของกิน", "food"),
    ("cm/sport/", "🏃", "กีฬา-ฟิตเนส", "sport"),
    ("cm/repair/", "🔧", "ช่าง", "trades"),
    ("cm/transport/", "🚌", "เดินทาง", "getting around"),
    ("cm/medical/pharmacy/", "💊", "ร้านยา", "pharmacies"),
    ("cm/massage/", "💆", "นวด", "massage"),
)

_BYDAY = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def today_count(events, build_date):
    """How many events are on today: one-offs dated today, plus weekly
    regulars whose day is today. Same reading of a row as build.event_when:
    `weekday` (one day a week), `byday` (several), else the row's own dt.
    De-duplicated the way the carousel is, on (title, place)."""
    try:
        today = datetime.date.fromisoformat(build_date)
    except (TypeError, ValueError):
        return 0
    wd = today.weekday()
    seen, n = set(), 0
    for e in events:
        key = (e.get("title"), (e.get("place") or {}).get("id"))
        if key in seen:
            continue
        if e.get("recurring"):
            if e.get("weekday") is not None:
                hit = e["weekday"] == wd
            elif e.get("byday"):
                hit = _BYDAY[wd] in e["byday"]
            else:
                dt = e.get("dt")
                hit = bool(dt) and dt.weekday() == wd
        else:
            hit = (e.get("start") or "")[:10] == build_date
        if hit:
            seen.add(key)
            n += 1
    return n


def _pick(rows, path):
    """The Chiang Rai reading on a Chiang Rai page, Chiang Mai everywhere
    else. The site has no third city."""
    want_cr = path.startswith("cr/")
    for c in rows:
        if ("chiang-rai" in c.get("id", "")) == want_cr:
            return c
    return rows[0] if rows else None


def strip(r, path=""):
    """One line: 🌤 24° ฝนปรอย · PM2.5 17 ดี · 🎪 24 งานวันนี้ · 🗺 (plan, JS).
    A cell with nothing true to say drops; a stale file drops its cell rather
    than printing yesterday as today (the same guard widget_weather uses)."""
    import build as B
    cells = []
    wx = _pick(B.WEATHER_CITIES, path)
    if wx and B.WEATHER_DATE >= B.BUILD_DATE and isinstance(wx.get("temp"), (int, float)):
        icon, th, en = B.wmo(wx.get("code"))
        cells.append(f'<a class="nn nnwx" href="{r}widgets.html#w-weather" '
                     f'aria-label="{B.att(B.bi_text(th, en))}">{icon} {wx["temp"]:.0f}°</a>')
    air = _pick(B.AIR_PLACES, path)
    if air and B.AIR_DATE >= B.BUILD_DATE and isinstance(air.get("pm25"), (int, float)):
        band = air.get("band") or {}
        cells.append(f'<a class="nn nnair" href="{r}widgets.html#w-air">'
                     f'PM2.5 {air["pm25"]:.0f} {B.bi(band.get("th", ""), band.get("en", ""))}</a>')
    # What is happening comes first: on a 375 px phone the line wraps, and
    # whatever is written last is read last. Every cell is deliberately terse —
    # the weather's own words live on its tile, and a cloud glyph beside 24°
    # already says drizzle to anyone standing in it.
    #
    # The count itself is the reader's, not the build's: JS reads today's
    # number out of data/today.json. The wrapper carries the separator so that
    # a strip whose only cell is this one never trails a stray " · ".
    ev = ""
    if B.TODAY_DAYS:
        ev = (f'<span class="nnevwrap" hidden>'
              f'<a class="nn nnev" href="{r}events.html"></a>'
              f'<span class="nnsep nnevsep"> · </span></span>')
    # Filled by JS from localStorage md-plan, separator and all; stays hidden
    # with an empty plan, so no stray " · " ever trails the line. 📍 ตรงนี้ is
    # the same shape, revealed only where the browser already reports
    # geolocation as granted — it never asks, and never hops.
    plan = f'<a class="nn nnplan" href="{r}plan.html" hidden></a>'
    here = f'<a class="nn nnhere" href="{r}here.html" hidden></a>'
    # THE READER'S OWN CHIPS DO NOT DEPEND ON THE WEATHER (2026-09-07).
    # This used to `return ""` when there was no weather, no air reading and no
    # event count — and plan and here were built AFTER that guard, so they went
    # with it. On 09-07 that is exactly what happened live: weather.json and
    # air.json were 09-06, BUILD_DATE was 09-07, the freshness guard correctly
    # dropped both cells, and the whole line vanished — taking 📍 ตรงนี้ with
    # it. here.html shipped in that build and nothing on the front page linked
    # to it, because its only link lived inside a line about the weather.
    #
    # Dropping a stale reading is right; a reader's plan and their own location
    # are not readings and have nothing to do with how fresh an air sensor is.
    # They are hidden by default and revealed by JS, so a line holding only
    # them costs no height until the browser has something to put there.
    if not cells and not ev:
        return (f'<p class="nownear" aria-label="{B.att(B.bi_text("ตอนนี้ · ใกล้ๆ", "now · near"))}">'
                + plan + here + "</p>")
    return (f'<p class="nownear" aria-label="{B.att(B.bi_text("ตอนนี้ · ใกล้ๆ", "now · near"))}">'
            + ev + '<span class="nnsep"> · </span>'.join(cells) + plan + here + "</p>")



def _fold(fid, glyph, th, en, inner):
    import build as B
    if not inner:
        return ""
    return (f'<details class="homefold" id="{fid}"><summary>{glyph} {B.bi(th, en)}</summary>'
            f'<div class="homefoldbody">{inner}</div></details>')


def home(parts):
    """The front page. parts: ev_strip · map · finder · today · sky · toys ·
    feeds · ad · share — all composed by build.py exactly as before; this only
    decides what stands open and what folds."""
    import build as B
    p = parts
    paths = '<span class="nnsep"> · </span>'.join(
        f'<a href="{href}">{g} {B.bi(th, en)}</a>' for href, g, th, en in PATHS)
    # The finder carries its own <h2>🔎; the fold's summary says it once.
    finder = re.sub(r"(?s)<h2>.*?</h2>", "", p.get("finder", ""), count=1)
    return (
        '<section class="hero herolite"><div class="herocopy">'
        f'<h1 class="herotitle"><span class="accent">{B.bi("มดแดงรู้ทุกซอย", "the red ants know every lane")}</span></h1>'
        '</div></section>'
        f'{p.get("ev_strip", "")}'
        f'{p.get("map", "")}'
        f'<p class="homepaths">{paths}</p>'
        + _fold("shelves", "🔎", "ทุกชั้น ทุกหมวด", "every shelf", finder)
        + _fold("today", "✨", "วันนี้", "today", p.get("today", ""))
        + _fold("sky", "🌙", "ฟ้า ลม น้ำ ราคา", "sky, air and prices", p.get("sky", ""))
        + _fold("toys", "🧭", "เครื่องมือของมด", "the ants’ instruments", p.get("toys", ""))
        + _fold("feeds", "📡", "ข่าวสด", "live", "<!--MD:COMINGUP-->" + p.get("feeds", ""))
        + p.get("ad", "") + p.get("share", ""))


CSS = """
/* ---- WO-65 NOW · NEAR: one line, then ☰ ---- */
/* Wraps, never scrolls sideways. In both-language mode the line runs 423 px
   on a 375 px phone, and a sideways scroll nobody discovers is how the air
   reading — the one number that matters in burning season — went missing off
   the right edge. Two short lines beat one hidden one. */
.nownear{margin:.5rem 0 0;font-size:.92rem;line-height:1.7}
.nownear a{white-space:nowrap}
.nownear a{color:var(--ant-dark);text-decoration:none;white-space:nowrap}
.nownear a:hover{color:var(--ant);text-decoration:underline}
.nnsep{color:var(--mute)}
details.morenav{margin:.15rem 0 0}
details.morenav>summary{cursor:pointer;list-style:none;display:inline-block;
font-size:1.3rem;line-height:1;padding:.3rem .4rem .3rem 0;color:var(--ant-dark)}
details.morenav>summary::-webkit-details-marker{display:none}
details.morenav>summary:hover{color:var(--ant)}
details.morenav[open]>summary{color:var(--ant)}
.homepaths{margin:.9rem 0 .4rem;font-size:1rem;line-height:2}
.homepaths a{white-space:nowrap;color:var(--ant-dark);text-decoration:none}
.homepaths a:hover{color:var(--ant);text-decoration:underline}
details.homefold{border-top:1px solid var(--soft);margin:0}
details.homefold>summary{cursor:pointer;font-weight:600;font-size:1.02rem;padding:.65rem 0;
list-style:none}
details.homefold>summary::-webkit-details-marker{display:none}
details.homefold>summary::after{content:"›";float:right;color:var(--mute);
transition:transform .12s ease}
details.homefold[open]>summary::after{transform:rotate(90deg)}
.homefoldbody{padding:0 0 .8rem}
.homefoldbody .wgrid{margin-top:.2rem}
.homefoldbody .finder{margin:.2rem 0 .4rem}
"""

JS = r"""
// ---- WO-65 NOW · NEAR: the plan cell, and a ☰ that never opens on nothing --
(function(){
function nnPlan(){var el=document.querySelector('.nnplan');if(!el)return;
var n=0;try{var v=JSON.parse(localStorage.getItem('md-plan'));n=Array.isArray(v)?v.length:0;}catch(e){}
el.hidden=!n;el.innerHTML=n?'<span class="nnsep"> · </span>🗺 '+mdBi('แผนของคุณ '+n+' จุด','your plan, '+n+(n>1?' stops':' stop')):'';}
nnPlan();
document.addEventListener('click',function(e){if(e.target.closest&&e.target.closest('.planbtn'))setTimeout(nnPlan,0);});
window.addEventListener('storage',function(e){if(!e.key||e.key==='md-plan')nnPlan();});
// The count of what is on TODAY, where today is the reader's own date. It was
// baked from BUILD_DATE, a hand-typed string, and on 2026-09-07 that string
// said the 5th on every page of the site. data/today.json carries three weeks
// forward; mdPick hands back today's entry or nothing at all.
function nnSep(el){var n=el.nextElementSibling;
while(n){if(!n.hidden&&!n.classList.contains('nnsep'))return true;n=n.nextElementSibling;}
return false;}
(async function(){var wrap=document.querySelector('.nnevwrap');if(!wrap)return;
var a=wrap.querySelector('.nnev'),sep=wrap.querySelector('.nnevsep');
var day=mdPick(await mdJSON('data/today.json'));
var n=day&&day.events;
// Nothing on today is a true answer and not an error: the cell goes rather
// than printing a nought, exactly as an empty plan does.
if(!n){nnEmpty();return;}
a.innerHTML='🎪 '+mdBi(n+' งานวันนี้',n+' on today');
wrap.hidden=false;sep.hidden=!nnSep(wrap);nnEmpty();})();
// 📍 ตรงนี้ — shown only where the browser already says granted. It is a link,
// never a redirect and never a prompt: Nan's call, 2026-09-07. Where
// navigator.permissions is missing the cell simply stays down and the reader
// still has the chip in ☰.
(function(){var el=document.querySelector('.nnhere');if(!el)return;
if(!navigator.permissions||!navigator.permissions.query)return;
navigator.permissions.query({name:'geolocation'}).then(function(st){
function paint(){var on=st.state==='granted';
el.innerHTML=on?'<span class="nnsep"> · </span>📍 '+mdBi('ตรงนี้','where I am'):'';
el.hidden=!on;nnEmpty();}
paint();st.onchange=paint;}).catch(function(){});})();
// A line with nothing true left to say is not a line. Same cleanup nnDrawer
// does for the ☰ over an empty drawer.
function nnEmpty(){document.querySelectorAll('p.nownear').forEach(function(p){
var live=Array.prototype.some.call(p.children,function(c){
return !c.hidden&&!c.classList.contains('nnsep')&&(c.textContent||'').trim();});
p.hidden=!live;});}
nnEmpty();
// search.html files the chip rows under its results; the drawer they left is
// then a glyph over nothing, so it goes too.
function nnDrawer(){document.querySelectorAll('details.morenav').forEach(function(d){
d.hidden=!d.querySelector('a');});}
window.addEventListener('load',function(){setTimeout(nnDrawer,0);});
})();
"""
