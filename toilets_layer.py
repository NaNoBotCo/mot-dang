#!/usr/bin/env python3
"""Where to go, when there is no time to choose.

Every other surface on this site answers "what is around here". This one
answers a narrower question under a clock, and that changes the shape of it:
the ranking is not by quality, the map is not the point, and a wrong answer
costs more than no answer.

Two kinds of knowledge, never printed in the same voice:

  verified — a toilet somebody mapped at a spot (amenity=toilets). 344 points
             in Chiang Mai, 87 in Chiang Rai. Certain, and outside the old
             city, close to nothing.
  tier     — a habit of a CLASS of venue. Fuel stations keep a free toilet;
             temples open theirs in daylight. True about the class, never a
             claim about the building in front of you, and always worded that
             way: "stations like this normally have one".

The tiers are what make the page usable — they turn 431 points into 1,310
places anyone may walk into, plus 5,313 more that will oblige a customer —
without asserting a single thing nobody told us. A verified point or a field
report at the same spot always outranks the tier it sits in, including the
report that says there is none, which is the only way a wrong guess comes off
the map.

What is deliberately NOT here is written down in data/toilets.json under
`excluded`, with reasons. The one worth repeating: Thai convenience stores do
not normally keep a customer toilet, so the 515 7-Elevens are not a tier. The
`toilet` facet those shops already carry on this site means "there is one
around here", which is a different sentence.

Entry point: emit(globals_of_build, data). Runnable alone against a built
docs/ while iterating:

    python3 toilets_layer.py
"""
import json
import math
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / "data" / "toilets.json").read_text())

TIERS = MODEL["tiers"]
COSTS = MODEL["costs"]
ACCESS = MODEL["access"]
WINDOWS = MODEL["windows"]
REPORTS = MODEL["reports"]

# Tiers whose door a stranger may walk through. The rest (a restaurant, a
# hotel lobby) are real answers but ask something of the reader first, so they
# are a second, larger file the page fetches only when it needs them — 215 KB
# gzipped has no business loading before the first result appears.
WALK_IN = {t["key"] for t in TIERS if t["access"] in ("public", "visitor")}

WALK_M_PER_MIN = 80          # 4.8 km/h, an unhurried pace on a flat soi

# Pin colours for the "which way" panel. Presentation, so it lives in the
# module beside the drawing rather than in the data file — same split
# festivals_layer.py uses for its family palette. The pin carries the tier's
# emoji as well, which is what actually identifies it; the colour is a second
# cue for a glance, and the two never disagree because both come from the tier.
TIER_COLOR = {
    "fuel": "#B4341A", "hospital": "#1F7A8C", "mall": "#6E4A9E",
    "wat": "#B8912E", "terminal": "#3F5AA6", "market": "#C0641B",
    "museum": "#8C6D3F", "university": "#2F6B4F", "park": "#3F7F4F",
    "sitdown": "#7D5A3C", "hotel": "#5B6770",
}
MAPPED_COLOR = "#2A1E16"     # a verified point: the darkest thing on the panel

# Landmarks for the reader who will not, or cannot, share a location. Resolved
# against the catalog by name so the coordinates carry a source rather than
# being typed in from memory; anything that does not resolve is dropped.
LANDMARK_SEEDS = [
    ("cm", "ประตูท่าแพ", "Tha Phae Gate", ["ท่าแพ", "tha phae"], ("sights", "historic")),
    ("cm", "ประตูเชียงใหม่", "Chiang Mai Gate", ["ประตูเชียงใหม่", "chiang mai gate"], ("sights", "historic")),
    ("cm", "ตลาดวโรรส", "Warorot Market", ["วโรรส", "warorot"], ("market",)),
    # The Arcade coach terminal, not the railway station: the station itself
    # is absent from the catalog (only "Railway Park" carries the word), and a
    # seed that resolves to nothing is silently dropped rather than pinned by
    # hand. Worth a crawl request of its own — a terminal is exactly the kind
    # of place someone asks this page about.
    ("cm", "สถานีขนส่งอาเขต", "Arcade Bus Terminal", ["อาเขต", "arcade bus"], ("transport",)),
    ("cm", "สนามบินเชียงใหม่", "Airport", ["สนามบิน", "airport"], ("transport", "sights")),
    ("cm", "นิมมานเหมินท์", "Nimmanhaemin", ["maya", "มายา", "นิมมาน"], ("shopping",)),
    ("cr", "หอนาฬิกาเชียงราย", "Clock Tower", ["หอนาฬิกา", "clock tower"], ("sights", "historic")),
    ("cr", "ขนส่งเชียงราย", "Bus Terminal", ["ขนส่ง", "bus terminal"], ("transport",)),
]


# ------------------------------------------------------------------ matching

def cat_of(r):
    c = r.get("cat")
    return c[0] if isinstance(c, list) else c


def tier_index(r):
    """First matching tier, or None. Order in the file is the rule — a temple
    that also sells coffee is a temple."""
    subs = set(r.get("sub") or [])
    cat = cat_of(r)
    name = " ".join(str(r.get(k) or "") for k in ("nameTh", "nameEn", "name")).lower()
    for i, t in enumerate(TIERS):
        m = t["match"]
        if "sub" in m and not (subs & set(m["sub"])):
            continue
        if "cat" in m and cat not in m["cat"]:
            continue
        if "name_any" in m and not any(w.lower() in name for w in m["name_any"]):
            continue
        return i
    return None


# --------------------------------------------------------- verified points

_FEE_BAHT = re.compile(r"(\d+)")


def verified_points(province):
    """The mapped toilets, with the tags that answer a reader's actual
    questions. The fixtures harvest has carried these all along; until now only
    their coordinates were read, and the fee sitting right beside them was
    thrown away on the way past."""
    p = ROOT / "cache" / "overpass" / province / "fixtures.json"
    if not p.exists():
        return []
    out = []
    for el in json.loads(p.read_text()).get("elements", []):
        t = el.get("tags") or {}
        if t.get("amenity") != "toilets":
            continue
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lng = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lng is None:
            continue

        # Cost. `fee=yes` without a `charge` is the common case (17 of the 18
        # that admit a fee at all), so the class figure stands in and says so.
        fee, baht = "", 0
        if t.get("fee") == "no":
            fee = "free"
        elif t.get("fee") == "yes":
            fee = "fee-small"
            m = _FEE_BAHT.search(t.get("charge") or "")
            if m:
                baht = int(m.group(1))

        flags = ""
        if t.get("wheelchair") in ("yes", "limited"):
            flags += "w"
        if t.get("changing_table") == "yes":
            flags += "b"
        acc = t.get("access") or ""
        if acc in ("private", "customers"):
            flags += "r"          # restricted — shown, but ranked below open ones

        out.append({
            "lat": round(lat, 5), "lng": round(lng, 5),
            "th": t.get("name:th") or t.get("name") or "",
            "en": t.get("name:en") or "",
            "fee": fee, "baht": baht,
            "hours": t.get("opening_hours") or "",
            "flags": flags,
        })
    return out


# --------------------------------------------------------------- the baking

# Most decisive first. Ticks are additive, so a contributor can hand us a
# contradiction ("free" and "10 baht"); this is the order that resolves one.
# The higher fee wins over the lower on purpose — somebody who arrives with a
# 5 baht coin at a 10 baht door is stuck, and the reverse is a pleasant
# surprise.
_REPORT_PRIORITY = ["toiletnone", "toiletfee10", "toiletfee5", "toiletfree",
                    "toilethere"]


def load_reports():
    """Passer-by reports, snapshotted by importers/sync_toilets.py. Absent
    file is the normal state until the LINE channel is live."""
    p = ROOT / "data" / "toilet_reports.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text()).get("reports", {}) or {}
    except (ValueError, OSError):
        return {}


def _report_of(rec_id, claims, reports):
    """A field report outranks every inference. Returns a report key or "" —
    the report vocabulary is closed (data/toilets.json `reports`), so nothing a
    submitter typed can arrive here.

    An owner's own claim beats a passer-by's report about the same place, on
    the same reasoning the rest of this site uses: a business is the authority
    on its own facts. A report fills in everywhere nobody has claimed, which
    is very nearly everywhere.
    """
    got = set((claims.get(rec_id) or {}).get("facets") or [])
    for k in _REPORT_PRIORITY:
        if k in got:
            return k
    r = (reports.get(rec_id) or {}).get("report")
    return r if r in _REPORT_PRIORITY else ""


def bake(g, data):
    """Two files: the doors anyone may walk through, and the ones that ask you
    to buy a coffee first. Split by size, not by worth — the second is four
    times the first and the reader in a hurry should not wait for it."""
    docs = g["DOCS"]
    claims = g.get("CLAIMS") or {}
    reports = load_reports()
    place_slug = g["place_slug"]
    provinces = [p["key"] for p in g["PROVINCES"]]

    walk, cust = [], []
    per_tier = {}
    n_reported = 0
    for prov in provinces:
        for r in data[prov]:
            if r.get("lat") is None:
                continue
            i = tier_index(r)
            if i is None:
                continue
            t = TIERS[i]
            rep = _report_of(r["id"], claims, reports)
            if rep:
                n_reported += 1
            if rep == "toiletnone":      # somebody stood there and told us
                continue
            per_tier[t["key"]] = per_tier.get(t["key"], 0) + 1
            th = r.get("nameTh") or r.get("name") or ""
            en = r.get("nameEn") or ""
            # The record id rides along because two of the three report doors
            # need it: the LINE deep link embeds [id:...] for the webhook to
            # resolve, and the web POST keys on it. It gzips to almost nothing
            # — every id shares the same "cm-osm-node-" head.
            row = [i, round(r["lat"], 5), round(r["lng"], 5), th, ("" if en == th else en),
                   f'{prov}/{place_slug(r)}', r.get("hours") or "", rep, r["id"]]
            (walk if t["key"] in WALK_IN else cust).append(row)

    ver = []
    per_prov = {}
    for prov in provinces:
        pts = verified_points(prov)
        per_prov[prov] = len(pts)
        for v in pts:
            ver.append([v["lat"], v["lng"], v["th"], v["en"], v["fee"],
                        v["baht"], v["hours"], v["flags"]])

    tiers_out = []
    for t in TIERS:
        rec = {k: t[k] for k in
               ("key", "rank", "emoji", "th", "en", "access", "cost",
                "window", "strength", "basis_th", "basis_en", "source")}
        rec["color"] = TIER_COLOR.get(t["key"], MAPPED_COLOR)
        tiers_out.append(rec)

    head = {
        "generated": g["BUILD_DATE"],
        "note_en": ("Two kinds of row. `verified` is a toilet mapped at that "
                    "spot. `places` is a venue whose CLASS normally keeps one "
                    "— a habit, never a claim about that building. A field "
                    "report (last column) outranks the tier."),
        "note_th": ("ข้อมูลสองแบบ — verified คือห้องน้ำที่มีคนปักหมุดไว้จริง "
                    "ส่วน places คือสถานที่ที่ประเภทของมันมักจะมีห้องน้ำ "
                    "เป็นธรรมเนียมของประเภทนั้น ไม่ใช่การยืนยันรายแห่ง"),
        "tiers": tiers_out,
        "costs": COSTS, "access": ACCESS, "windows": WINDOWS,
        "reports": REPORTS,
        "walkMetresPerMinute": WALK_M_PER_MIN,
        "verified_columns": ["lat", "lng", "th", "en", "fee", "baht", "hours", "flags"],
        "columns": ["tier", "lat", "lng", "th", "en", "href", "hours", "report", "id"],
        "verified": ver,
        "places": walk,
        "customersFile": "data/toilets-customers.json",
        "customersCount": len(cust),
        # Empty until she provisions the LINE Official Account; the page shows
        # no LINE door at all rather than a broken one.
        "lineOa": g.get("LINE_OA_ID") or "",
        "reportEndpoint": g.get("CLAIMS_WORKER_URL", "") + "/toilet",
        # For the "which way" panel. The ring and its nine gates come from
        # build.py's own helpers — the same geometry the plan and walking maps
        # draw — so a gate can never be in one place on one map and somewhere
        # else on another. Names are read out of the catalogue records, never
        # typed here.
        "mappedColor": MAPPED_COLOR,
        # tests/test_alt_text.py fails an unlabelled role="img", and a label
        # that is only the medium ("map") counts as unlabelled. Says what the
        # picture is FOR.
        "mapAlt": g["bi_text"](
            "แผนที่เล็ก ๆ บอกทิศ: จุดสีส้มตรงกลางคือคุณ หมุดคือห้องน้ำสิบแห่งที่ใกล้ที่สุด "
            "เส้นประคือคูเมือง วงกลมบอกระยะ",
            "A small panel showing which way to go: the orange dot in the "
            "middle is you, the pins are the ten nearest toilets, the dashed "
            "square is the moat, and the rings mark distance."),
        "moat": [[round(la, 5), round(ln, 5)] for la, ln in (g.get("MOAT_POLY") or [])],
        "gates": [[round(x[0], 5), round(x[1], 5), x[2], x[3], x[4]]
                  for x in (g["_moat_crossings"]() if g.get("_moat_crossings") else [])],
    }
    (docs / "data" / "toilets.json").write_text(
        json.dumps(head, ensure_ascii=False, separators=(",", ":")))
    (docs / "data" / "toilets-customers.json").write_text(
        json.dumps({"generated": g["BUILD_DATE"],
                    "columns": head["columns"], "places": cust},
                   ensure_ascii=False, separators=(",", ":")))
    return {"walk": len(walk), "cust": len(cust), "verified": len(ver),
            "per_tier": per_tier, "per_prov": per_prov, "reported": n_reported}


# ---------------------------------------------------------------- landmarks

def landmarks(g, data):
    """Resolve the fallback list against the catalog, so a coordinate printed
    here came from the same place every other coordinate on the site did."""
    out = []
    for prov, th, en, terms, cats in LANDMARK_SEEDS:
        best = None
        for r in data.get(prov) or []:
            if r.get("lat") is None or cat_of(r) not in cats:
                continue
            name = " ".join(str(r.get(k) or "") for k in ("nameTh", "nameEn", "name")).lower()
            if any(w.lower() in name for w in terms):
                best = r
                break
        if best:
            out.append({"th": th, "en": en, "lat": round(best["lat"], 5),
                        "lng": round(best["lng"], 5), "prov": prov})
    return out


# --------------------------------------------------------------------- CSS

CSS = """/* ห้องน้ำใกล้ฉัน — read at arm's length, in a hurry, one-handed.
   Type is deliberately larger than the rest of the site and the tap targets
   are deliberately bigger than they need to be on a desktop. */
.loogo{display:block;width:100%;border:0;border-radius:1.1rem;cursor:pointer;
  padding:1.15rem 1rem;font:700 1.35rem/1.25 var(--face-th),system-ui,sans-serif;
  color:#fff;background:linear-gradient(160deg,#D4552C,#A8371A);
  box-shadow:0 .55rem 1.3rem rgba(168,55,26,.28);letter-spacing:.01em}
.loogo:hover{filter:brightness(1.06)}
.loogo:active{transform:translateY(1px)}
.loogo:focus-visible{outline:3px solid #2A1E16;outline-offset:3px}
.loogo[disabled]{opacity:.6;cursor:progress}
.loostate{margin:.6rem 0 0;font-size:1rem;min-height:1.4em}
.loostate.err{color:#8C2A12;font-weight:600}

/* The which-way panel. Capped so it never eats the results it is there to
   help you reach — direction is a glance, the list is the answer. */
.loomap{margin:.9rem 0 .2rem}
.loomap:empty{display:none}
.loomapsvg{display:block;width:100%;max-width:20rem;height:auto;margin:0 auto}
.loopin{cursor:pointer}
.loopin:hover circle{filter:brightness(1.12)}
.loopin:focus-visible{outline:2px solid #2A1E16;outline-offset:2px}
.loorow.loohit{background:#FBEBD0;border-radius:.6rem}
@media (prefers-reduced-motion:no-preference){
  .loorow{transition:background .35s ease}
}
.loofilters{display:flex;flex-wrap:wrap;gap:.45rem;margin:1rem 0 .2rem}
.loofilters button{cursor:pointer;border:1.5px solid #C9B79B;background:#FFFDF8;
  border-radius:2rem;padding:.5rem .95rem;font:600 .98rem/1 var(--face-th),system-ui,sans-serif;
  color:#2A1E16}
.loofilters button[aria-pressed=true]{background:#2A1E16;border-color:#2A1E16;color:#FAF3E7}

.loolist{list-style:none;margin:.9rem 0 0;padding:0}
.loorow{display:flex;gap:.8rem;align-items:flex-start;padding:.95rem .2rem;
  border-bottom:1px solid #E4D8C4}
.loorow:first-child{border-top:1px solid #E4D8C4}
.lootier{flex:0 0 auto;font-size:1.9rem;line-height:1.1;width:2.2rem;text-align:center}
.loobody{flex:1 1 auto;min-width:0}
.looname{font-size:1.18rem;line-height:1.3;display:block}
.looname a{text-decoration:none;color:inherit;border-bottom:2px solid #E0CDAE}
.looname a:hover{border-bottom-color:#A8371A}
.loometa{display:flex;flex-wrap:wrap;gap:.3rem;align-items:center;margin:.3rem 0 0}
.lookline{flex-basis:100%;padding:.3rem .2rem 0}
.loodist{font-weight:700;font-size:1.12rem}
.loowalk{font-size:.9rem;color:#4A3B30}
.loochip{font-size:.86rem;border-radius:2rem;padding:.18rem .6rem;
  border:1.5px solid #C9B79B;background:#FFFDF8;white-space:nowrap}
.loochip.free{background:#DCEFD2;border-color:#8FBF77;font-weight:700}
.loochip.fee{background:#FBEBD0;border-color:#D9A441;font-weight:700}
.loochip.cust{background:#EDE7F5;border-color:#A99BC6}
.loochip.open{background:#DCEFD2;border-color:#8FBF77}
.loochip.shut{background:#F0E7E2;border-color:#C4A79A}
.loochip.sure{background:#2A1E16;border-color:#2A1E16;color:#FAF3E7;font-weight:700}
.loochip.wc{background:#DEE6F4;border-color:#8FA5CC}
.loobasis{margin:.4rem 0 0;font-size:.94rem;line-height:1.5;color:#4A3B30}
.looacts{margin:.45rem 0 0;font-size:.95rem}
.looacts a{margin-right:.75rem;white-space:nowrap}
/* The ticks. Same closed vocabulary as LINE and the worker, five buttons, no
   typing — the whole report is one tap and it says thank you on the spot. */
.looticks{display:flex;flex-wrap:wrap;gap:.4rem;margin:.55rem 0 .1rem;
  padding:.55rem;border:1.5px dashed #C9B79B;border-radius:.7rem;background:#FFFDF8}
.looticks button{cursor:pointer;border:1.5px solid #C9B79B;background:#FFF;
  border-radius:2rem;padding:.45rem .8rem;font:600 .92rem/1 var(--face-th),system-ui,sans-serif;
  color:#2A1E16}
.looticks button:hover{background:#DCEFD2;border-color:#8FBF77}
.looticks button[disabled]{opacity:.5;cursor:progress}
.lookthx{font-weight:700;color:#3F6B2B;padding:.45rem .2rem}
.lookerr{font-weight:600;color:#8C2A12;padding:.45rem .2rem;flex-basis:100%}
.loomore{margin:1.1rem 0 0}
.loomore button{cursor:pointer;width:100%;border:1.5px dashed #C9B79B;background:#FFFDF8;
  border-radius:.9rem;padding:.85rem 1rem;font:600 1.05rem/1.3 var(--face-th),system-ui,sans-serif;
  color:#2A1E16}
.loonear{margin:1.2rem 0 0;padding:.9rem 1rem;border:1px solid #E4D8C4;
  border-radius:.9rem;background:#FFFDF8}
.loonear ul{margin:.5rem 0 0;padding:0;list-style:none;display:flex;
  flex-wrap:wrap;gap:.45rem}
.loonear a{display:inline-block;border:1.5px solid #C9B79B;border-radius:2rem;
  padding:.45rem .9rem;background:#FFF;text-decoration:none}
.tiertable{width:100%;border-collapse:collapse;margin:.8rem 0}
.tiertable th,.tiertable td{text-align:left;vertical-align:top;padding:.55rem .5rem;
  border-bottom:1px solid #E4D8C4;font-size:.96rem}
.tiertable th{font-size:.86rem;text-transform:uppercase;letter-spacing:.04em;color:#6B584A}
.tiertable td.tk{white-space:nowrap;font-weight:700}
@media (max-width:34rem){
  .tiertable thead{display:none}
  .tiertable tr{display:block;border-bottom:1px solid #E4D8C4;padding:.4rem 0}
  .tiertable td{display:block;border:0;padding:.2rem .1rem}
}
@media (prefers-reduced-motion:reduce){.loogo:active{transform:none}}
"""


# ---------------------------------------------------------------------- JS

JS = r"""/* ห้องน้ำใกล้ฉัน. Everything is baked; the only thing this asks the
   network for is the second, larger file, and only if the reader taps for it.
   The location never leaves the browser — there is nowhere on this site to
   send it. */
(function(){
var D=null,MORE=null,here=null,filter='all',showCust=false;
var elBtn=document.getElementById('loogo'),elState=document.getElementById('loostate'),
    elList=document.getElementById('loolist'),elFilters=document.getElementById('loofilters'),
    elMore=document.getElementById('loomore'),elNear=document.getElementById('loonear'),
    elMap=document.getElementById('loomap');
if(!elBtn)return;
var LANG=document.documentElement;

function bi(th,en){return '<span class="bi"><span class="th">'+esc(th)+'</span>'+
  '<span class="en"><span class="th"> · </span>'+esc(en)+'</span></span>';}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}

function hav(a,b,c,d){var R=6371000,p1=a*Math.PI/180,p2=c*Math.PI/180,
  dp=(c-a)*Math.PI/180,dl=(d-b)*Math.PI/180,
  h=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);
  return 2*R*Math.asin(Math.sqrt(h));}

/* Opening hours. Only the two shapes that actually appear often enough to be
   worth reading are parsed; anything else falls back to the class window and
   is labelled as a habit, not as a fact. We never print a flat "closed" from a
   habit — being wrong about that sends somebody walking the wrong way. */
function stated(h){
  if(!h)return null;
  var s=h.replace(/\s+/g,'');
  if(s==='24/7'||s==='Mo-Su00:00-24:00'||s==='Mo-Su,PH00:00-00:00'||s==='Mo-Su00:00-00:00')return[0,24];
  var m=s.match(/^(?:Mo-Su|Mo-Sa|Daily)?,?(?:PH)?(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$/);
  if(m)return[+m[1]+ +m[2]/60,+m[3]+ +m[4]/60];
  return null;
}
function openness(row,tier){
  var now=new Date(),h=now.getHours()+now.getMinutes()/60;
  var w=stated(row.hours),sure=!!w;
  if(!w&&tier&&tier.window&&D.windows[tier.window])w=D.windows[tier.window];
  if(!w)return null;
  var lo=w[0],hi=w[1]===24?24:w[1],on=(hi<=lo)?(h>=lo||h<hi):(h>=lo&&h<hi);
  return {on:on,sure:sure};
}

function costChip(cost,baht){
  if(cost==='free')return '<span class="loochip free">'+bi('ฟรี','free')+'</span>';
  if(cost==='fee-small')return '<span class="loochip fee">'+
    (baht?bi(baht+' บาท',baht+' baht'):bi('5–10 ฿','5-10 ฿'))+'</span>';
  if(cost==='free-or-small')return '<span class="loochip">'+bi('ฟรี/5–10 ฿','free / 5-10 ฿')+'</span>';
  if(cost==='with-order')return '<span class="loochip cust">'+bi('ซื้อของก่อน','buy something')+'</span>';
  return '';
}

/* Three doors, and which one a row shows depends on what exists. LINE is the
   Thai-facing one and only appears once the Official Account is provisioned;
   the numbered ticks post straight to the worker; GitHub is the developers'
   side entrance and always works. Nobody is sent to the wrong one. */
function reportUrl(name,href,id){
  var body='ห้องน้ำ / Toilet: '+name+'\n'+(href?location.origin+'/'+href+'.html\n':'')+
    (id?'[id:'+id+']\n':'')+
    '\nที่นี่ใช้ได้ไหม เสียเงินเท่าไร / Can it be used, and what does it cost?\n\n'+
    D.reports.map(function(r,i){return (i+1)+'. '+r.emoji+' '+r.th+' / '+r.en;}).join('\n')+
    '\n\nลบข้อที่ไม่ใช่ออก แล้วส่งได้เลย / Delete the lines that do not apply, then send.\n';
  return 'https://github.com/NaNoBotCo/mot-dang/issues/new?title='+
    encodeURIComponent('ห้องน้ำ / Toilet: '+name)+'&body='+encodeURIComponent(body);
}
function lineUrl(name,id){
  if(!D.lineOa||!id)return '';
  return 'https://line.me/R/oaMessage/'+encodeURIComponent(D.lineOa)+'/?'+
    encodeURIComponent('ห้องน้ำ '+name+' [id:'+id+']');
}
/* The quickest door of all: the ticks, right on the row. Posts one closed
   word to the worker and says so on the spot. Falls back to nothing if the
   worker is unreachable — the GitHub link beside it still works. */
function tickRow(id,name){
  if(!id||!D.reportEndpoint)return '';
  /* LINE lives in here rather than on the row: it is the same intent as the
     ticks, and as a fourth link up top it cost a line of every result. */
  var lu=lineUrl(name,id);
  return '<div class="looticks" data-for="'+esc(id)+'" hidden>'+
    D.reports.map(function(r){return '<button type="button" data-rep="'+esc(r.key)+'">'+
      r.emoji+' '+bi(r.th,r.en)+'</button>';}).join('')+
    (lu?'<a class="lookline" href="'+esc(lu)+'" rel="noopener">'+
      bi('หรือบอกทางไลน์','or tell us on LINE')+'</a>':'')+
    '<span class="lookthx" hidden>'+bi('ขอบคุณเจ้า 🐜','thank you 🐜')+'</span>'+
    '<span class="lookerr" hidden>'+bi('ส่งไม่สำเร็จ ลองอีกครั้ง หรือใช้ทางอื่นด้านล่าง',
      'That did not send — try again, or use another door below')+'</span></div>';
}
function wireTicks(){
  elList.querySelectorAll('.looticks').forEach(function(box){
    box.querySelectorAll('button[data-rep]').forEach(function(b){
      b.addEventListener('click',function(){
        box.querySelector('.lookerr').hidden=true;
        box.querySelectorAll('button').forEach(function(x){x.disabled=true;});
        fetch(D.reportEndpoint,{method:'POST',headers:{'content-type':'application/json'},
          body:JSON.stringify({placeId:box.dataset.for,report:b.dataset.rep})})
          .then(function(r){if(!r.ok)throw 0;
            box.querySelector('.lookthx').hidden=false;
            box.querySelectorAll('button').forEach(function(x){x.hidden=true;});})
          /* Say so. A tap that silently does nothing reads as a broken page,
             and the other two doors are right there. */
          .catch(function(){box.querySelector('.lookerr').hidden=false;
            box.querySelectorAll('button').forEach(function(x){x.disabled=false;});});
      });});
    });
  elList.querySelectorAll('[data-tickopen]').forEach(function(a){
    a.addEventListener('click',function(e){e.preventDefault();
      var box=elList.querySelector('.looticks[data-for="'+a.dataset.tickopen+'"]');
      if(box)box.hidden=!box.hidden;});});
}

/* One shape for both kinds of row, so the renderer never has to ask which
   file a result came from — only how sure it is. */
function normalise(){
  var out=[];
  D.verified.forEach(function(v){
    out.push({kind:'v',lat:v[0],lng:v[1],th:v[2]||'ห้องน้ำสาธารณะ',en:v[3]||(v[2]?'':'Public toilet'),
      cost:v[4],baht:v[5],hours:v[6],flags:v[7]||'',href:'',tier:null});
  });
  var add=function(p){
    var t=D.tiers[p[0]];
    var cost=t.cost,baht=0,acc=t.access;
    var rep=p[7];
    if(rep){var R=D.reports.filter(function(x){return x.key===rep;})[0];
      if(R&&R.sets){if(R.sets.cost)cost=R.sets.cost;if(R.sets.access)acc=R.sets.access;
        if(R.sets.baht)baht=R.sets.baht;}}
    out.push({kind:rep?'f':'t',lat:p[1],lng:p[2],th:p[3],en:p[4],cost:cost,baht:baht,
      hours:p[6],flags:'',href:p[5],tier:t,access:acc,id:p[8]||''});
  };
  D.places.forEach(add);
  if(showCust&&MORE)MORE.places.forEach(add);
  return out;
}

function passes(x){
  if(filter==='free')return x.cost==='free'||x.cost==='free-or-small';
  if(filter==='open'){var o=openness(x,x.tier);return !o||o.on;}
  if(filter==='wc')return x.flags.indexOf('w')>=0;
  return true;
}

function render(){
  if(!here||!D)return;
  var rows=normalise().filter(passes);
  rows.forEach(function(x){x.d=hav(here.lat,here.lng,x.lat,x.lng);});
  /* Distance, and nothing else. An earlier version nudged mapped points and
     field reports up by 90 m so confirmed things outranked habits, and it
     produced a list reading 80 m, 120 m, 270 m, 180 m — which on a page whose
     one promise is "nearest first" looks broken, and looking broken costs
     more than the nudge was worth. Confidence is already on every row, in the
     "mapped" and "checked by a person" chips; the reader can weigh it. */
  rows.sort(function(a,b){return a.d-b.d;});
  rows=rows.slice(0,40);
  if(!rows.length){elList.innerHTML='<li class="loorow"><div class="loobody">'+
    bi('ไม่พบในตัวกรองนี้ ลองเอาตัวกรองออก','Nothing matches that filter — try clearing it')+
    '</div></li>';return;}
  /* The tier sentence belongs to the CLASS, not the row: printing it under
     all 591 temples restated one paragraph 591 times and pushed the results
     themselves off a phone screen. Shown once, the first time its tier
     appears in this list. */
  var toldTier={};
  elList.innerHTML=rows.map(function(x){
    var t=x.tier,o=openness(x,t),chips=[];
    /* The number once, not once per language — "80 ม. · เดิน ~1 นาที · 80 ม.
       · ~1 min walk" spent two lines saying 80 twice. */
    chips.push('<span class="loodist">'+esc(fmtD(x.d))+'</span>'+
      '<span class="loowalk">'+bi('เดิน ~'+Math.max(1,Math.round(x.d/D.walkMetresPerMinute))+' นาที',
        '~'+Math.max(1,Math.round(x.d/D.walkMetresPerMinute))+' min walk')+'</span>');
    if(x.kind==='v')chips.push('<span class="loochip sure">'+bi('ปักหมุดไว้แล้ว','mapped')+'</span>');
    if(x.kind==='f')chips.push('<span class="loochip sure">'+bi('มีคนไปดูมา','checked by a person')+'</span>');
    chips.push(costChip(x.cost,x.baht));
    if(o)chips.push('<span class="loochip '+(o.on?'open':'shut')+'">'+
      (o.sure?bi(o.on?'เปิดอยู่':'ปิดแล้ว',o.on?'open now':'closed now')
             :bi(o.on?'น่าจะเปิด':'น่าจะปิดแล้ว',o.on?'likely open':'probably closed'))+'</span>');
    if(x.flags.indexOf('w')>=0)chips.push('<span class="loochip wc">♿ '+bi('รถเข็นเข้าได้','step-free')+'</span>');
    if(x.flags.indexOf('r')>=0)chips.push('<span class="loochip cust">'+bi('เจ้าของจำกัดสิทธิ์','restricted')+'</span>');
    /* The name IS the link to the place page. It was a fourth action before,
       and four bilingual links wrapped to a hundred pixels on a phone — which
       on this page costs a whole result you could otherwise have seen. */
    var nm=x.en&&x.en!==x.th?bi(x.th,x.en):'<span class="th">'+esc(x.th)+'</span>';
    if(x.href)nm='<a href="'+esc(x.href)+'.html">'+nm+'</a>';
    var acts=[],nom=x.th||x.en;
    if(x.href)acts.push('<a href="plan.html?stops='+encodeURIComponent(x.href.split('/')[0]+':'+
      x.href.split('/').slice(1).join('/'))+'">'+bi('เดินไปยังไง','walk me there')+'</a>');
    if(x.id&&D.reportEndpoint)acts.push('<a href="#" data-tickopen="'+esc(x.id)+'">'+
      bi('บอกมดแดง','tell the ants')+'</a>');
    if(!x.id||!D.reportEndpoint)acts.push('<a href="'+esc(reportUrl(nom,x.href,x.id))+
      '" rel="noopener">'+bi('บอกมดแดง','tell the ants')+'</a>');
    var tk=t?t.key:'_mapped',basis='';
    if(!toldTier[tk]){toldTier[tk]=1;
      basis='<p class="loobasis">'+(t?bi(t.basis_th,t.basis_en):
        bi('ห้องน้ำสาธารณะที่มีคนปักหมุดไว้ในแผนที่เปิด',
           'A public toilet somebody mapped in OpenStreetMap.'))+'</p>';}
    return '<li class="loorow">'+
      '<span class="lootier" aria-hidden="true">'+(t?t.emoji:'🚻')+'</span>'+
      '<div class="loobody"><b class="looname">'+nm+'</b>'+
      '<div class="loometa">'+chips.join('')+'</div>'+basis+
      '<div class="looacts">'+acts.join(' ')+'</div>'+tickRow(x.id,nom)+'</div></li>';
  }).join('');
  wireTicks();
  if(elMap)drawMap(rows,elMap);
}

function fmtD(m){return m<1000?Math.round(m/10)*10+' ม.':(m/1000).toFixed(1)+' กม.';}

/* ---- the "which way" panel -------------------------------------------
   A list tells you how far; it cannot tell you which way to turn. This is
   drawn here rather than at build time because it has to be centred on
   wherever the reader actually is. No tiles and no map library: the site
   refuses both, and every shape below comes from coordinates already in the
   baked file. Equirectangular with a cos(lat) correction is ample over the
   half-kilometre or so this ever covers. */
function drawMap(rows,el){
  if(!rows.length){el.innerHTML='';return;}
  var S=300,PAD=26,shown=rows.slice(0,10);
  /* Frame on the tenth result so the pins fill the box, with a floor so a
     cluster of very near ones does not zoom to absurdity. */
  var far=Math.max(160,shown[shown.length-1].d)*1.18;
  var cosla=Math.cos(here.lat*Math.PI/180);
  var mPerDegLat=110574,mPerDegLng=111320*cosla;
  var half=S/2-PAD, scale=half/far;                 // px per metre
  function px(la,ln){
    return [S/2+((ln-here.lng)*mPerDegLng)*scale,
            S/2-((la-here.lat)*mPerDegLat)*scale];
  }
  function inBox(p){return p[0]>-40&&p[0]<S+40&&p[1]>-40&&p[1]<S+40;}
  var p=[];
  p.push('<svg viewBox="0 0 '+S+' '+S+'" class="loomapsvg" role="img" aria-label="'+
    esc(D.mapAlt||'')+'">');
  p.push('<rect width="'+S+'" height="'+S+'" rx="14" fill="#FFFDF8" stroke="#E4D8C4"/>');
  /* Range rings, labelled — the cheapest way to read distance off a picture. */
  [0.25,0.5,1].forEach(function(f){
    var r=half*f; if(r<18)return;
    p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="'+r.toFixed(1)+'" fill="none" '+
      'stroke="#EADFCB" stroke-dasharray="3 4"/>');
    p.push('<text x="'+(S/2+3)+'" y="'+(S/2-r+11).toFixed(1)+'" font-size="9" '+
      'fill="#9C8874">'+esc(fmtD(far*f))+'</text>');
  });
  /* The moat, when any of it is actually in frame. Everyone here navigates by
     it, and it is the difference between a picture of dots and a place. */
  if(D.moat&&D.moat.length){
    var ring=D.moat.map(function(c){return px(c[0],c[1]);});
    /* Overlap of BOUNDING BOXES, not "is a corner in frame". The ring is four
       points with very long sides: standing at Tha Phae Gate, on the moat,
       every corner is off-frame and the vertex test drew nothing — while the
       side you are standing on ran straight through the middle. */
    var xs=ring.map(function(q){return q[0];}),ys=ring.map(function(q){return q[1];});
    var overlaps=Math.min.apply(null,xs)<S+40&&Math.max.apply(null,xs)>-40&&
                 Math.min.apply(null,ys)<S+40&&Math.max.apply(null,ys)>-40;
    if(overlaps){
      p.push('<polygon points="'+ring.map(function(q){
        return q[0].toFixed(1)+','+q[1].toFixed(1);}).join(' ')+
        '" fill="none" stroke="#8FA5CC" stroke-width="2.5" stroke-dasharray="7 4"/>');
    }
    (D.gates||[]).forEach(function(gt){
      var q=px(gt[0],gt[1]); if(!inBox(q))return;
      p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+q[1].toFixed(1)+
        '" r="3" fill="#8FA5CC"/>');
      p.push('<text x="'+(q[0]+5).toFixed(1)+'" y="'+(q[1]+3.5).toFixed(1)+
        '" font-size="9" fill="#5E6C8A">'+esc(gt[2])+'</text>');
    });
  }
  /* North, so a rotated phone still reads. */
  p.push('<g opacity=".75"><path d="M'+(S-20)+' '+(PAD-6)+' l5 13 -5-3 -5 3Z" fill="#6B584A"/>'+
    '<text x="'+(S-20)+'" y="'+(PAD+22)+'" font-size="9" fill="#6B584A" text-anchor="middle">N</text></g>');
  /* Pins furthest-first, so the nearest ones land on top of the pile. */
  shown.slice().reverse().forEach(function(x){
    var i=shown.indexOf(x),q=px(x.lat,x.lng);
    var col=x.tier?(x.tier.color||D.mappedColor):D.mappedColor;
    p.push('<g class="loopin" data-pin="'+i+'" tabindex="0" role="button" aria-label="'+
      esc((x.th||x.en)+' — '+fmtD(x.d))+'">');
    p.push('<line x1="'+q[0].toFixed(1)+'" y1="'+q[1].toFixed(1)+'" x2="'+q[0].toFixed(1)+
      '" y2="'+(q[1]-9).toFixed(1)+'" stroke="'+col+'" stroke-width="1.5"/>');
    p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+(q[1]-15).toFixed(1)+'" r="11" fill="'+col+
      '" stroke="#FFFDF8" stroke-width="2"/>');
    p.push('<text x="'+q[0].toFixed(1)+'" y="'+(q[1]-11).toFixed(1)+
      '" font-size="11" text-anchor="middle">'+(x.tier?x.tier.emoji:'🚻')+'</text>');
    p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+q[1].toFixed(1)+'" r="2" fill="'+col+'"/>');
    p.push('</g>');
  });
  /* You, last, so nothing hides you. */
  p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="9" fill="#D4552C" opacity=".18"/>');
  p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="4.5" fill="#D4552C" stroke="#fff" stroke-width="2"/>');
  p.push('</svg>');
  el.innerHTML=p.join('');
  el.querySelectorAll('.loopin').forEach(function(g){
    var go=function(){
      var li=elList.children[+g.dataset.pin]; if(!li)return;
      li.scrollIntoView({block:'center'});
      li.classList.add('loohit');
      setTimeout(function(){li.classList.remove('loohit');},1400);
    };
    g.addEventListener('click',go);
    g.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});
  });
}

function locate(){
  if(!navigator.geolocation){fail('เครื่องนี้บอกตำแหน่งไม่ได้ · This device cannot share a location');return;}
  elBtn.disabled=true;
  elState.className='loostate';
  elState.innerHTML=bi('กำลังหาตำแหน่ง…','Finding you…');
  navigator.geolocation.getCurrentPosition(function(p){
    here={lat:p.coords.latitude,lng:p.coords.longitude};
    elBtn.disabled=false;
    elState.innerHTML=bi('เรียงจากใกล้ที่สุด · ระยะเป็นเส้นตรง เดินจริงไกลกว่านี้',
      'Nearest first. Distances are straight-line — the walk is longer, especially across the moat.');
    elFilters.hidden=false;elMore.hidden=false;
    render();
  },function(){
    elBtn.disabled=false;
    fail('ยังไม่ได้ตำแหน่ง — เลือกจุดใกล้ตัวข้างล่างได้เลย · No location yet — pick a spot below instead');
    elNear.hidden=false;
  },{enableHighAccuracy:true,timeout:10000,maximumAge:60000});
}
function fail(msg){elState.className='loostate err';
  var p=msg.split(' · ');elState.innerHTML=bi(p[0],p[1]||'');}

function boot(){
  fetch('data/toilets.json').then(function(r){return r.json();}).then(function(j){
    D=j;elBtn.disabled=false;
    elBtn.addEventListener('click',locate);
    elFilters.querySelectorAll('button').forEach(function(b){
      b.addEventListener('click',function(){
        filter=b.dataset.f;
        elFilters.querySelectorAll('button').forEach(function(x){
          x.setAttribute('aria-pressed',x===b?'true':'false');});
        render();});});
    elMore.querySelector('button').addEventListener('click',function(){
      var btn=this;btn.disabled=true;
      fetch(D.customersFile).then(function(r){return r.json();}).then(function(m){
        MORE=m;showCust=true;elMore.hidden=true;render();})
        .catch(function(){btn.disabled=false;});});
    elNear.querySelectorAll('a[data-lat]').forEach(function(a){
      a.addEventListener('click',function(e){e.preventDefault();
        here={lat:+a.dataset.lat,lng:+a.dataset.lng};
        elFilters.hidden=false;elMore.hidden=false;
        elState.className='loostate';
        elState.innerHTML=bi('เรียงจากจุดที่เลือก · ระยะเป็นเส้นตรง',
          'Nearest to the spot you picked. Distances are straight-line.');
        render();});});
  }).catch(function(){fail('โหลดข้อมูลไม่สำเร็จ ลองรีเฟรช · Could not load the data — try reloading');});
}
boot();
})();
"""


# -------------------------------------------------------------------- page

def _tier_table(g):
    bi, esc = g["bi"], g["esc"]
    rows = []
    for t in TIERS:
        cost = COSTS[t["cost"]]
        acc = ACCESS[t["access"]]
        field = ""
        if t.get("source") == "field":
            field = (' <span class="facet field">'
                     + bi("จากการอยู่จริง", "field knowledge") + "</span>")
        rows.append(
            f'<tr><td class="tk">{t["emoji"]} ' + bi(t["th"], t["en"]) + field + "</td>"
            + "<td>" + bi(cost["th"], cost["en"]) + "</td>"
            + "<td>" + bi(acc["th"], acc["en"]) + "</td>"
            + "<td>" + bi(t["basis_th"], t["basis_en"]) + "</td></tr>")
    return ('<table class="tiertable"><thead><tr>'
            + f'<th>{bi("ประเภท", "Class")}</th><th>{bi("ค่าใช้จ่าย", "Cost")}</th>'
            + f'<th>{bi("ใครใช้ได้", "Who may use it")}</th>'
            + f'<th>{bi("ทำไมถึงเชื่อแบบนี้", "Why we think so")}</th>'
            + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


def build_page(g, stats, marks):
    bi, att, esc = g["bi"], g["att"], g["esc"]
    page, share_block = g["page"], g["share_block"]

    walkin_total = sum(v for k, v in stats["per_tier"].items() if k in WALK_IN)

    lede_th = ("บางครั้งคำถามมีข้อเดียว — ห้องน้ำที่ใกล้ที่สุดอยู่ไหน ใช้ได้เลยไหม เสียเงินเท่าไร "
               "หน้านี้ตอบแค่นั้น กดปุ่มเดียว เรียงจากใกล้ที่สุด ตำแหน่งของคุณอยู่ในเครื่องคุณเท่านั้น "
               "เว็บนี้ไม่มีที่ให้ส่งไปไหนอยู่แล้ว")
    lede_en = ("Sometimes there is only one question — where is the nearest one, "
               "may I use it, what does it cost. This page answers that and "
               "nothing else. One button, nearest first. Your location stays in "
               "your browser; this site has nowhere to send it.")

    near_items = "".join(
        f'<li><a href="#" data-lat="{m["lat"]}" data-lng="{m["lng"]}">'
        + bi(m["th"], m["en"]) + "</a></li>" for m in marks)

    filters = "".join(
        f'<button type="button" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
        + bi(th, en) + "</button>"
        # "hide the probably-closed" and not "open now": the filter keeps rows
        # whose hours nobody recorded, which is most of the mapped points, and
        # calling that "open" would be a promise the data cannot keep.
        for k, th, en in (("all", "ทั้งหมด", "everything"),
                          ("free", "ฟรีเท่านั้น", "free only"),
                          ("open", "ซ่อนที่น่าจะปิด", "hide the probably-closed"),
                          ("wc", "รถเข็นเข้าได้", "step-free")))

    # The method section. The single most useful number on it is that one
    # toilet in 344 recorded its price — that is the gap this page's report
    # button exists to close, and saying so is more persuasive than asking.
    method_th = (
        f'ห้องน้ำที่ปักหมุดไว้จริงในแผนที่เปิด: เชียงใหม่ {stats["per_prov"].get("cm", 0)} แห่ง '
        f'เชียงราย {stats["per_prov"].get("cr", 0)} แห่ง — แน่นอนที่สุด แต่ในเชียงใหม่มีเพียง '
        f'แห่งเดียวเท่านั้นที่บอกราคาไว้ว่าเก็บเท่าไร ราคา ๕–๑๐ บาทจึงเป็นความรู้ตามประเภท '
        f'ที่รอให้คนที่ไปจริงมาแก้ · ชั้นของที่พึ่งอีก {walkin_total:,} แห่งที่ใครก็เดินเข้าได้ '
        f'และอีก {stats["cust"]:,} แห่งที่ให้ลูกค้าใช้ มาจากธรรมเนียมของประเภทสถานที่ '
        f'ไม่ใช่การยืนยันรายแห่ง — เขียนไว้แบบนั้นทุกบรรทัด · '
        f'ระยะทางเป็นเส้นตรง ไม่ใช่ระยะเดินจริง ข้ามคูเมืองต้องอ้อมไปประตู '
        f'ดู<a href="walk.html">แผนที่ระยะเดิน</a>ประกอบ · '
        f'คำบอกจากคนที่ไปจริงชนะการเดาจากประเภทเสมอ รวมถึงคำว่า "ที่นี่ไม่มี" '
        f'ซึ่งเป็นทางเดียวที่จะเอาการเดาที่ผิดออกจากรายการได้')
    method_en = (
        f'Toilets actually mapped in OpenStreetMap: {stats["per_prov"].get("cm", 0)} in '
        f'Chiang Mai, {stats["per_prov"].get("cr", 0)} in Chiang Rai — the surest rows here, '
        f'and yet exactly one of the Chiang Mai points records what it charges. '
        f'The 5-10 baht figure is therefore class knowledge waiting on somebody '
        f'who went. The {walkin_total:,} walk-in places and {stats["cust"]:,} '
        f'customer ones come from the habit of a class of venue, never from a '
        f'check on that building — and every line says so. Distances are '
        f'straight-line, not walking distance; the moat is crossable only at the '
        f'bridges and gates, so see <a href="walk.html">the walking-pace maps</a>. '
        f'A report from someone who stood there outranks the class every time, '
        f'including the one that says there is none — which is the only way a '
        f'wrong guess comes off this page.')

    excl = "".join(
        f'<div class="module"><h3>{bi(x["th"], x["en"])}'
        + (f' <span class="tinynote">({x["count_cm"]:,})</span>' if x.get("count_cm") else "")
        + f'</h3><p>{bi(x["why_th"], x["why_en"])}</p></div>'
        for x in MODEL["excluded"])

    # The three doors, and only the ones that actually exist today. The LINE
    # block stays hidden until data/line.json carries a real Official Account,
    # the same gate every other LINE block on this site uses — a door that
    # opens onto nothing is worse than no door.
    door_bits = [
        ('<div class="module"><h3>' + bi("แตะที่รายการเลย", "Tap it on the list")
         + "</h3><p>" + bi(
             "ทุกบรรทัดมีปุ่ม “บอกมดแดง” — เลือกหนึ่งข้อจากห้าข้อ ฟรี ๕ บาท ๑๐ บาท เฉพาะลูกค้า "
             "หรือ “ที่นี่ไม่มี” จบในแตะเดียว ไม่ต้องพิมพ์ ไม่ต้องสมัครอะไร",
             "Every row carries a “tell the ants” button — one of five answers: "
             "free, 5 baht, 10 baht, customers only, or none here. One tap, no "
             "typing, no account.") + "</p></div>"),
        ('<div class="module"><h3>' + bi("เจ้าของร้านยืนยันเองได้", "Owners can say so themselves")
         + "</h3><p>" + bi(
             "ถ้าเป็นร้านของคุณ ยืนยันร้านแล้วติ๊กเรื่องห้องน้ำไปพร้อมกันได้เลย "
             "คำของเจ้าของชนะการเดาจากประเภทเสมอ",
             "If it is your place, claim it and tick the toilet answer at the "
             "same time. The owner's word beats our guess about the class every "
             "time.") + f'</p><p><a class="pill" href="claim.html">'
         + bi("ยืนยันร้านของคุณ", "Claim your place") + "</a></p></div>"),
    ]
    if g.get("LINE_OA_ID"):
        door_bits.insert(0,
            '<div class="module"><h3>' + bi("บอกทางไลน์", "Tell us on LINE")
            + "</h3><p>" + bi(
                "แตะ “บอกทางไลน์” ที่รายการไหนก็ได้ แชทจะเปิดขึ้นมาพร้อมข้อความ "
                "แล้วตอบกลับเป็นตัวเลข ๑–๕ ข้อเดียว จบ",
                "Tap “tell us on LINE” on any row — the chat opens with the "
                "message ready, and you answer with one number from 1 to 5.")
            + "</p></div>")
    else:
        door_bits.append(
            '<div class="module"><h3>' + bi("ไลน์ — ยังไม่เปิด", "LINE — not open yet")
            + "</h3><p>" + bi(
                "ประตูทางไลน์สร้างเสร็จแล้วทั้งฝั่งเว็บและฝั่งบอท รอเพียงเปิดบัญชี "
                "LINE Official Account จริงแล้วใส่ไอดีลงใน data/line.json ปุ่มจะขึ้นเองทุกหน้า",
                "The LINE door is built on both sides, web and bot. It waits only "
                "on a real Official Account: put its id in data/line.json and the "
                "buttons appear by themselves.") + "</p></div>")
    doors = "".join(door_bits)

    # Hoisted, not inlined: build.py and this layer run on Python 3.9, where a
    # multi-line expression inside an f-string is a SyntaxError.
    order_note = bi(
        "เรียงตามความแน่นอนของประเภท แล้วจึงตามเวลาที่เปิด ไม่ได้เรียงตามความสวยงามของห้อง",
        "Ordered by how dependable the class is, then by how long its doors "
        "stay open — not by how nice the room is.")

    body = (
        f'<h1>🚻 {bi("ห้องน้ำใกล้ฉัน", "Toilets near you")}</h1>'
        f'<p class="lede">{bi(lede_th, lede_en)}</p>'
        '<button type="button" id="loogo" class="loogo" disabled>'
        + bi("📍 หาห้องน้ำที่ใกล้ที่สุด", "Find the nearest one") + "</button>"
        f'<p id="loostate" class="loostate"></p>'
        f'<div id="loomap" class="loomap"></div>'
        f'<div id="loofilters" class="loofilters" hidden role="group" '
        f'aria-label="{att(g["bi_text"]("ตัวกรอง", "Filters"))}">{filters}</div>'
        f'<ol id="loolist" class="loolist"></ol>'
        f'<div id="loomore" class="loomore" hidden><button type="button">'
        + bi(f"ดูร้านที่ให้ลูกค้าใช้ด้วย ({stats['cust']:,} แห่ง)",
             f"Also show places that oblige a customer ({stats['cust']:,})")
        + "</button></div>"
        f'<div id="loonear" class="loonear" hidden>'
        f'<b>{bi("หรือเลือกจุดที่คุณอยู่", "Or pick where you are")}</b>'
        f'<ul>{near_items}</ul></div>'

        f'<h2>{bi("ลองที่ไหนก่อน", "What to try first")}</h2>'
        f'<p>{order_note}</p>'
        + _tier_table(g)
        + f'<h2>{bi("ที่ไม่ได้ใส่ไว้ และเพราะอะไร", "What we left out, and why")}</h2>'
        + excl
        + f'<h2>{bi("ช่วยบอกหน่อย", "Help us get this right")}</h2>'
        + doors
        + f'<h2>{bi("รู้ได้ยังไง", "How we know")}</h2>'
        f'<p class="tinynote">{bi(method_th, method_en)}</p>'
        f'<p><a href="data/toilets.json">data/toilets.json</a> · '
        f'<a href="walk.html">🚶 {bi("แผนที่ระยะเดิน", "The city at walking pace")}</a></p>'
        + share_block(g["BASE"] + "toilets.html",
                      "ห้องน้ำใกล้ฉัน · Toilets near you · มดแดง"))

    return page("ห้องน้ำใกล้ฉัน", body, depth=0, path="toilets.html",
                desc=lede_th,
                extra_head='<link rel="stylesheet" href="toilets.css">'
                           '<script src="toilets.js" defer></script>')


# -------------------------------------------------------------------- emit

def emit(g, data):
    docs = g["DOCS"]
    stats = bake(g, data)
    marks = landmarks(g, data)
    (docs / "toilets.css").write_text(CSS)
    (docs / "toilets.js").write_text(JS)
    (docs / "toilets.html").write_text(build_page(g, stats, marks))
    walkin = sum(v for k, v in stats["per_tier"].items() if k in WALK_IN)
    return (f'{stats["verified"]} mapped + {walkin} walk-in + '
            f'{stats["cust"]} customer-only, {len(marks)} landmarks')


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
