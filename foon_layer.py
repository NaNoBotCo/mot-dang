#!/usr/bin/env python3
"""/foon.html — ฝุ่น, the smoke season. WO-57 item 4.

THE QUESTION February brings, every year, and the site could not answer:
the number is 180, so where do I go? It could say what the number MEANT —
the PCD bands have been on the air widget for months — and nothing at all
about where a person with asthma, a small child or a building site job
actually goes to breathe for two hours.

THE INSTINCT WAS TO GUESS, and this page exists because the guess was
refused. Malls have air handling; libraries are indoors; hospitals must
filter something. All plausible, none read off anything, and a room listed
as clean that is not is worse than no page. It turns out no guess was
needed: กรมอนามัย keeps a national register of assessed clean-air rooms with
a public API, and importers/fetch_cleanrooms.py reads our two provinces out
of it — 2,428 publicly accessible rooms with pins, every one with a phone.

THE GRADE RIDES ON EVERY ROW, the same discipline as care.html, ot.html and
the lens pages:
    ตรวจโดยเจ้าหน้าที่ · assessed by an officer  — 221 rooms, and only these
        carry an expiry date
    ประเมินตนเอง · self-assessed                — the rest
and the DATE rides with it, because some rows were last assessed in 2024 and
"assessed" with no "when" is not a fact anybody can act on. The register's
own verdict (ผ่าน) is printed in its own words and never translated into a
pass or a fail of ours.

WHAT THIS PAGE DOES NOT DO. It does not say whether to go out, does not
advise a mask, does not forecast, and does not rank a room. It says what the
number means, where the register says the rooms are, who assessed each one
and when. The air reading it prints is stamped with the hour it was modelled
for and named as a model, not a monitor.

Entry point: emit(globals_of_build, data).
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

GRADE = {
    "evaluator": ("ตรวจโดยเจ้าหน้าที่", "assessed by an officer"),
    "self": ("ประเมินตนเอง", "self-assessed"),
}
NEAR = 12          # rooms drawn for a reader who asks what is nearest
STALE_YEARS = 2    # an assessment older than this is called old, on the row


def _air(g):
    """Today's reading for both provinces, and the standing band table.

    Two different kinds of fact and they are drawn apart on purpose: the
    reading is a model's number for one hour and is stamped as such; the
    bands are the Pollution Control Department's standing scale and do not
    move. Conflating them is how a page ends up looking like a forecast."""
    src = ROOT / "data" / "air.json"
    if not src.exists():
        return "", []
    bi, esc = g["bi"], g["esc"]
    air = json.loads(src.read_text())
    want = {"chiang-mai", "chiang-rai"}
    cards = []
    for p in air["places"]:
        if p["id"] not in want:
            continue
        b = p.get("band") or {}
        spark = ""
        days = p.get("days") or []
        if days:
            hi = max((d.get("pm25") or 0) for d in days) or 1
            bars = "".join(
                f'<i style="height:{max(4, round(100 * (d.get("pm25") or 0) / hi))}%;'
                f'background:{esc((d.get("band") or {}).get("colour", "#999"))}"'
                f' title="{esc(d.get("date", ""))} · {esc(str(d.get("pm25")))}"></i>'
                for d in days)
            spark = (f'<span class="fo-spark" role="img" '
                     f'aria-label="{esc(bi_days_label(days))}">{bars}</span>')
        cards.append(
            f'<div class="fo-now" style="--band:{esc(b.get("colour", "#888"))}">'
            f'<span class="fo-city">{bi(p.get("th", ""), p.get("en", ""))}</span>'
            f'<span class="fo-num">{esc(str(p.get("pm25")))}'
            f'<small> µg/m³</small></span>'
            f'<span class="fo-band">{bi(b.get("th", ""), b.get("en", ""))}</span>'
            f'{spark}'
            f'<span class="fo-when">{esc(p.get("observed", ""))}</span></div>')
    note = (f'<p class="tinynote">{bi("ค่านี้เป็นค่าจากแบบจำลอง ไม่ใช่เครื่องวัดที่หัวถนน อบไว้ตอนสร้างหน้า — ดูค่าสดที่เครื่องวัดจริงได้ที่ cmuccdc.org", "A modelled figure, not a street-level monitor, and baked when the page was built — for live readings from real monitors see cmuccdc.org")} · {esc(air.get("source", ""))}</p>')
    return f'<div class="fo-nowrow">{"".join(cards)}</div>{note}', air


def bi_days_label(days):
    return "seven days: " + ", ".join(
        f'{d.get("date", "")} {d.get("pm25")}' for d in days)


def _bands(g):
    """The PCD bands, read from importers/make_air.py rather than typed.

    Same reason make_chuai_sheet.py imports them: the paper, the page and the
    colour on the air widget are one fact, and this repo's recurring failure
    is that fact existing in three places."""
    import sys
    sys.path.insert(0, str(ROOT / "importers"))
    from make_air import BANDS
    bi, esc = g["bi"], g["esc"]
    rows, low = [], 0.0
    for ceiling, _key, th, en, colour in BANDS:
        rng = f"{low:g}–{ceiling:g}" if ceiling != float("inf") else f"{low:g}+"
        rows.append(
            f'<tr><td class="sw"><span style="background:{esc(colour)}"></span></td>'
            f'<td class="rng">{esc(rng)}</td><td>{bi(th, en)}</td></tr>')
        low = ceiling
    return (f'<table class="fo-bands"><caption class="vh">'
            f'{esc(g["bi_text"]("เกณฑ์ PM2.5", "PM2.5 bands"))}</caption>'
            f'{"".join(rows)}</table>')


def _census(g, doc):
    """How many rooms, where, and how they were assessed — the whole register
    in two tables. Districts with the fewest are not hidden: a district with
    four rooms is the finding, not the embarrassment."""
    bi, esc = g["bi"], g["esc"]
    rooms = doc["rooms"]
    by_prov = {}
    for r in rooms:
        by_prov.setdefault(r["p"], []).append(r)

    out = []
    for key, th, en in (("cm", "เชียงใหม่", "Chiang Mai"),
                        ("cr", "เชียงราย", "Chiang Rai")):
        rs = by_prov.get(key) or []
        if not rs:
            continue
        by_d = {}
        for r in rs:
            by_d.setdefault(r["d"] or "—", []).append(r)
        cells = "".join(
            f'<tr><td>{esc(d)}</td><td class="n">{len(v):,}</td>'
            f'<td class="n">{sum(1 for x in v if x["g"] == "evaluator"):,}</td></tr>'
            for d, v in sorted(by_d.items(), key=lambda kv: -len(kv[1])))
        out.append(
            f'<div class="fo-cen"><h3>{bi(th, en)} '
            f'<span class="count">({len(rs):,})</span></h3>'
            f'<table class="fo-tab"><tr><th>{bi("อำเภอ", "District")}</th>'
            f'<th class="n">{bi("ห้อง", "rooms")}</th>'
            f'<th class="n">{bi("เจ้าหน้าที่ตรวจ", "officer-assessed")}</th></tr>'
            f'{cells}</table></div>')

    kinds = {}
    for r in rooms:
        kinds[doc["types"][r["k"]]] = kinds.get(doc["types"][r["k"]], 0) + 1
    kind_rows = "".join(
        f'<tr><td>{esc(k)}</td><td class="n">{v:,}</td></tr>'
        for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]))
    return (f'<div class="fo-cengrid">{"".join(out)}</div>'
            f'<h3>{bi("ห้องแบบไหนบ้าง", "What kind of room")}</h3>'
            f'<table class="fo-tab">{kind_rows}</table>')


def build_page(g, doc):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    page, share_block, BASE = g["page"], g["share_block"], g["BASE"]
    rooms = doc["rooms"]
    src, also = doc["source"], doc["also"]
    n_ev = sum(1 for r in rooms if r["g"] == "evaluator")
    cutoff = (datetime.date.today()
              - datetime.timedelta(days=365 * STALE_YEARS)).isoformat()
    n_old = sum(1 for r in rooms if r["w"] and r["w"] < cutoff)
    n_bad = sum(1 for r in rooms if r.get("doubt") in ("outside", "far"))

    air_html, _air_doc = _air(g)

    body = (
        f'<h1>🌫 {bi("ฝุ่น — ห้องปลอดฝุ่นใกล้ฉัน", "Smoke season — clean-air rooms near you")}</h1>'
        f'<p class="lede">{bi("ตัวเลข PM2.5 แปลว่าอะไร และทะเบียนห้องปลอดฝุ่นของกรมอนามัยบอกว่าห้องที่เข้าได้จริงอยู่ตรงไหน ใครตรวจ และตรวจเมื่อไร", "What the PM2.5 number means, and where the Department of Health register says the rooms a member of the public may walk into actually are — who assessed each one, and when.")}</p>'
        + air_html +
        f'<h2>{bi("ตัวเลขแปลว่าอะไร", "What the number means")}</h2>'
        + _bands(g) +
        f'<h2>{bi("ห้องปลอดฝุ่นใกล้ฉัน", "Clean-air rooms near me")} '
        f'<span class="count">({len(rooms):,})</span></h2>'
        f'<button type="button" id="fo-locate" class="ch-go">📍 '
        + bi("หาห้องใกล้ฉัน", "Find the rooms near me") + '</button>'
        f'<div id="fo-out" class="ch-out" aria-live="polite"></div>'
        f'<p class="tinynote">'
        + bi(f"ทะเบียนถือ {len(rooms):,} ห้องที่ประชาชนเข้าได้และมีพิกัด — {n_ev:,} ห้องมีเจ้าหน้าที่ไปตรวจ ที่เหลือเป็นการประเมินตนเอง และ {n_old:,} ห้องประเมินไว้เกินสองปีแล้ว ป้ายบนแต่ละแถวบอกไว้ทั้งหมด โทรถามก่อนไปเสมอ",
             f"The register holds {len(rooms):,} public rooms with a pin. {n_ev:,} were assessed by an officer; the rest assessed themselves, and {n_old:,} were last assessed more than two years ago. Every row says which and when. Ring before you go.")
        + '</p>'
        f'<h2>{bi("ทะเบียนทั้งหมด", "The whole register")}</h2>'
        + _census(g, doc) +
        f'<p class="tinynote">'
        + bi(f"ที่มา: {src['name']} — {src['credit']} · อ่านเมื่อ {doc['generated']} · "
             f"อีกประตูหนึ่งคือ {also['name']}",
             f"Source: {src['name']} — {src['credit']}, read {doc['generated']}. "
             f"A second door to the same rooms: {also['name']}.")
        + f' <a href="{att(src["url"])}" rel="noopener">podfoon.anamai.moph.go.th</a>'
        f' · <a href="{att(also["url"])}" rel="noopener">pakpod.cmuccdc.org</a>'
        f' · <a href="data/cleanrooms.json">cleanrooms.json</a></p>'
        f'<p class="tinynote">{bi("มดแดงไม่ได้ไปตรวจห้องเหล่านี้เอง หน้านี้บอกว่าทะเบียนราชการบันทึกอะไรไว้ ไม่ใช่คำแนะนำด้านสุขภาพ", "Mot Dang did not assess these rooms. This page says what a state register records — it is not health advice.")}</p>'
        f'<p class="tinynote">🆘 <a href="chuai.html">'
        + bi("เบอร์ฉุกเฉินและที่ใกล้ที่สุด", "Emergency numbers and what is nearest")
        + '</a></p>'
        + share_block(BASE + "foon.html",
                      "ฝุ่น · ห้องปลอดฝุ่นใกล้ฉัน — มดแดง"))

    # THE ROOMS ARE NOT BAKED INTO THIS PAGE, and /chuai.html's are. The
    # difference is what each page promises. The lifeline page has to be whole
    # in one request with no signal, so it pays 47 kB over the wire every
    # time. This page is a register somebody reads in February: the bands, the
    # census and today's reading arrive in 12 kB, and the 2,428 rooms are
    # fetched only when a reader actually presses the button. The service
    # worker keeps that fetch, so the second visit needs no network either.
    inline = (f'<script>{JS_TMPL % {"NEAR": NEAR, "SRC": NEAR_SRC}}</script>')

    return page(
        "ฝุ่น — ห้องปลอดฝุ่นใกล้ฉัน เชียงใหม่ เชียงราย ค่า PM2.5 แปลว่าอะไร",
        body + inline, depth=0, path="foon.html",
        desc=f"ห้องปลอดฝุ่นที่ประชาชนเข้าได้ {len(rooms):,} ห้องในเชียงใหม่และเชียงราย "
             "จากทะเบียนกรมอนามัย พร้อมเบอร์โทร ใครตรวจ ตรวจเมื่อไร และเกณฑ์ค่าฝุ่น "
             "PM2.5 · Every public clean-air room in Chiang Mai and Chiang Rai from "
             "the Thai Department of Health register, with phones, who assessed it "
             "and when.",
        extra_head='<link rel="stylesheet" href="foon.css">'
                   '<script src="near.js"></script>',
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("ฝุ่น", "Smoke season"))


NEAR_SRC = "data/cleanrooms-near.json"


def near_payload(doc):
    """[name, lat5, lng5, phone, district, typeIx, grade, when] + the types.

    The lean copy the page actually reads. data/cleanrooms.json beside it
    keeps every field the register gave us, for anybody who wants the whole
    thing — but a reader on a February connection should not pay for the
    email addresses and the room areas to find a door.


    A row whose pin the importer could not place — outside the provinces, or
    in an amphoe other than the one it names — is NOT here. It keeps its seat
    in data/cleanrooms.json and its count on the page; what it loses is the
    ability to be offered as somewhere 200 m away when it is 90 km away. The
    68 rows the check could not run on (no amphoe on the row) DO ride, wearing
    a mark, because dropping a real room is also a cost."""
    keep = [r for r in doc["rooms"] if r.get("doubt") not in ("outside", "far")]
    return {
        "generated": doc["generated"],
        "types": doc["types"],
        "rooms": [[r["n"], round(r["la"] * 1e5), round(r["ln"] * 1e5),
                   r["t"], r["d"], r["k"],
                   1 if r["g"] == "evaluator" else 0, r["w"],
                   1 if r.get("doubt") == "unchecked" else 0]
                  for r in keep],
    }


JS_TMPL = """
// foon.js — the nearest clean-air rooms, sorted on the device. Distance,
// bilingual spans and the locate button come from near.js; what is this
// page's own is the row: the grade and the date it was assessed ride on
// every one of them, because the register itself grades them and a page
// that flattened that would be inventing a standard.
(function(){
var N=window.MDNear;
var out=document.getElementById('fo-out'),NEAR=%(NEAR)d,SRC='%(SRC)s';
var rows=null,TYPES=null;
var CUT=new Date(Date.now()-2*365*864e5).toISOString().slice(0,10);
function row(km,r){
 var g=r[6]?N.bi('\\u0E15\\u0E23\\u0E27\\u0E08\\u0E42\\u0E14\\u0E22\\u0E40\\u0E08\\u0E49\\u0E32\\u0E2B\\u0E19\\u0E49\\u0E32\\u0E17\\u0E35\\u0E48','assessed by an officer')
                :N.bi('\\u0E1B\\u0E23\\u0E30\\u0E40\\u0E21\\u0E34\\u0E19\\u0E15\\u0E19\\u0E40\\u0E2D\\u0E07','self-assessed');
 var old=(r[7]&&r[7]<CUT)?'<span class="fo-old">'
  +N.bi('\\u0E40\\u0E01\\u0E34\\u0E19\\u0E2A\\u0E2D\\u0E07\\u0E1B\\u0E35','over two years old')+'</span>':'';
 // The 68 rows the amphoe cross-check could not run on say so on the row.
 var unk=r[8]?'<span class="fo-unk">'+N.bi(
  '\\u0E44\\u0E21\\u0E48\\u0E44\\u0E14\\u0E49\\u0E15\\u0E23\\u0E27\\u0E08\\u0E2A\\u0E2D\\u0E1A\\u0E1E\\u0E34\\u0E01\\u0E31\\u0E14',
  'pin not cross-checked')+'</span>':'';
 return '<div class="ch-row"><span class="ch-nm">'+N.esc(r[0])
  +'<span class="fo-meta">'+N.esc(TYPES[r[5]])+' \\u00B7 '+N.esc(r[4])
  +'</span></span>'
  +'<span class="ch-km">'+N.far(km)+'</span>'
  +'<span class="fo-grade'+(r[6]?' ev':'')+'">'+g+' '+N.esc(r[7])+old+unk+'</span>'
  +N.tel(r[3])+N.pin(r[1]/1e5,r[2]/1e5)+'</div>';}
function draw(here){
 var list=[];
 for(var i=0;i<rows.length;i++){var r=rows[i];
  list.push([N.km(here[0],here[1],r[1]/1e5,r[2]/1e5),r]);}
 list.sort(function(a,b){return a[0]-b[0];});
 var h='';
 for(var j=0;j<Math.min(list.length,NEAR);j++)h+=row(list[j][0],list[j][1]);
 out.innerHTML=h;}
// The register is fetched on the press, not on the load: a February reader
// on a bad connection pays for it only if they asked for it. Once fetched
// the service worker holds it, so a second visit needs no network.
document.getElementById('fo-locate').addEventListener('click',function(){
 N.locate(out,function(here){
  if(rows){draw(here);return;}
  N.say(out,'\u0E01\u0E33\u0E25\u0E31\u0E07\u0E42\u0E2B\u0E25\u0E14\u0E17\u0E30\u0E40\u0E1A\u0E35\u0E22\u0E19\u2026','loading the register\u2026');
  fetch(SRC).then(function(r){return r.json();}).then(function(d){
   rows=d.rooms;TYPES=d.types;draw(here);})
  .catch(function(){N.say(out,
   '\u0E15\u0E48\u0E2D\u0E40\u0E19\u0E47\u0E15\u0E44\u0E21\u0E48\u0E44\u0E14\u0E49 \u2014 \u0E25\u0E2D\u0E07\u0E43\u0E2B\u0E21\u0E48\u0E2D\u0E35\u0E01\u0E04\u0E23\u0E31\u0E49\u0E07',
   'could not reach the register \u2014 try again');});});});
})();
"""


CSS = """/* foon.css — generated by foon_layer.py */
.fo-nowrow{display:flex;flex-wrap:wrap;gap:.7rem;margin:1rem 0 .3rem}
.fo-now{flex:1 1 15rem;display:grid;grid-template-columns:auto 1fr;
gap:.1rem .7rem;align-items:baseline;background:var(--card);
border-left:6px solid var(--band);border-radius:.5rem;padding:.6rem .9rem}
.fo-city{grid-column:1/-1;font-weight:700}
.fo-num{font-size:2rem;font-weight:700;line-height:1}
.fo-num small{font-size:.8rem;font-weight:400;color:var(--ink-soft)}
.fo-band{font-weight:700}
.fo-spark{grid-column:1/-1;display:flex;align-items:flex-end;gap:2px;
height:2.2rem;margin-top:.3rem}
.fo-spark i{flex:1 1 0;min-width:3px;border-radius:1px 1px 0 0}
.fo-when{grid-column:1/-1;font-size:.78rem;color:var(--ink-soft)}
table.fo-bands{border-collapse:collapse;margin:.5rem 0 1rem}
table.fo-bands td{border-bottom:1px solid var(--card-alt);padding:.3rem .8rem .3rem 0}
table.fo-bands td.sw{width:3rem;padding-right:.6rem}
table.fo-bands td.sw span{display:block;height:1.1rem;border:1.5px solid var(--ink);
border-radius:.2rem}
table.fo-bands td.rng{font-variant-numeric:tabular-nums;font-weight:700;
white-space:nowrap}
.fo-meta{display:block;font-size:.8rem;font-weight:400;color:var(--ink-soft)}
.fo-grade{flex:0 0 auto;font-size:.78rem;color:var(--ink-soft);
border:1.5px dashed var(--gloss);border-radius:2rem;padding:.02rem .55rem}
.fo-grade.ev{border-style:solid;border-color:var(--ant-dark);color:var(--ink)}
.fo-old{margin-left:.35rem;font-weight:700}
.fo-unk{margin-left:.35rem;font-style:italic}
.fo-cengrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));
gap:1.2rem;margin:.6rem 0 1.2rem}
.fo-cen h3{margin:.2rem 0 .35rem}
table.fo-tab{border-collapse:collapse;width:100%;font-size:.92rem}
table.fo-tab th,table.fo-tab td{border-bottom:1px solid var(--card-alt);
padding:.28rem .5rem .28rem 0;text-align:left;vertical-align:baseline}
table.fo-tab th{border-bottom:2px solid var(--card-alt);white-space:nowrap}
table.fo-tab .n{text-align:right;font-variant-numeric:tabular-nums;
white-space:nowrap}
"""


def emit(g, data):
    DOCS, ROOT_ = g["DOCS"], g["ROOT"]
    src = ROOT_ / "data" / "cleanrooms.json"
    if not src.exists():
        return "SKIPPED — no data/cleanrooms.json (importers/fetch_cleanrooms.py)"
    import nearby
    nearby.emit(DOCS)
    doc = json.loads(src.read_text(encoding="utf-8"))
    (DOCS / "foon.css").write_text(CSS)
    html = build_page(g, doc)
    (DOCS / "foon.html").write_text(html)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "cleanrooms.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    (DOCS / "data" / "cleanrooms-near.json").write_text(
        json.dumps(near_payload(doc), ensure_ascii=False,
                   separators=(",", ":")), encoding="utf-8")
    n_ev = sum(1 for r in doc["rooms"] if r["g"] == "evaluator")
    n_near = len(near_payload(doc)["rooms"])
    return (f'{len(doc["rooms"]):,} public rooms ({n_ev:,} officer-assessed, '
            f'{n_near:,} placeable), '
            f'{len(doc["types"])} types, read {doc["generated"]}, '
            f'page {len(html.encode()) / 1024:.0f} kB')


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
