#!/usr/bin/env python3
"""/lottery.html — สลากกินแบ่งรัฐบาล, the Thai government lottery draw.

The front-page tile (assets/front/tiles.js, drawLotto) shows the drum and the
first prize and links here. This page carries the rest of the office's sheet:
every tier, every number, each tier's amount in baht, the office's own PDF of
the announcement, a ticket check that runs in the reader's browser, and the
past draws held in data/lottery_history.json.

The ticket check matches as the office's sheet does:
  first, near_first, second, third, fourth, fifth  all six digits
  front3                                           the first three digits
  back3                                            the last three digits
  last2                                            the last two digits
A ticket can win more than one tier; the check lists each and adds them up.

The page prints the announced record and the reader's own check. No
prediction, no tip, no frequency of any number.

Data: importers/make_lottery.py -> data/lottery.json, data/lottery_history.json.

Entry point: emit(globals_of_build, data). Standalone, over a built docs/:
    python3 lottery_layer.py
"""
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Display order for the full sheet: by amount, the big ones first.
FULL = ("first", "near_first", "second", "third", "fourth", "fifth",
        "front3", "back3", "last2")
# The three short-number tiers drawn big beside the first prize.
SHORT = ("front3", "back3", "last2")

EN_MO_S = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TH_MO_S = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
           "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def baht(n):
    if n is None:
        return ""
    return "฿{:,}".format(int(n)) if float(n) == int(n) else "฿{:,.2f}".format(n)


def short_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return ("%d %s %d" % (d, TH_MO_S[m], y + 543), "%d %s %d" % (d, EN_MO_S[m], y))


def compact(draw):
    """One draw as the checker reads it."""
    p = {x["id"]: x for x in draw.get("prizes") or []}
    th, en = short_date(draw["date"])
    return {
        "d": draw["date"],
        "th": th,
        "en": en,
        "pdf": draw.get("record_pdf") or "",
        "t": {k: {"n": v["numbers"], "a": v.get("amount_baht")} for k, v in p.items()},
    }


def head_block(g, draw):
    bi, esc = g["bi"], g["esc"]
    p = {x["id"]: x for x in draw["prizes"]}
    first = p.get("first") or {}
    out = (f'<div class="lt-first">'
           f'<span class="lt-flab">{bi(first.get("th", ""), first.get("en", ""))}</span>'
           + "".join(f'<b class="lt-fnum ln" data-t="first" data-n="{esc(n)}">{esc(n)}</b>'
                     for n in first.get("numbers") or [])
           + f'<span class="lt-amt">{bi(baht(first.get("amount_baht")), baht(first.get("amount_baht")))}'
           f' <small>{bi("ต่อใบ", "per ticket")}</small></span></div>')
    cards = []
    for pid in SHORT:
        t = p.get(pid)
        if not t:
            continue
        nums = "".join(f'<b class="ln" data-t="{pid}" data-n="{esc(n)}">{esc(n)}</b>'
                       for n in t["numbers"])
        cards.append(f'<div class="lt-short"><span class="lt-slab">{bi(t["th"], t["en"])}</span>'
                     f'<span class="lt-snums">{nums}</span>'
                     f'<span class="lt-amt">{bi(baht(t.get("amount_baht")), baht(t.get("amount_baht")))}'
                     f' <small>{bi("ต่อใบ", "per ticket")}</small></span></div>')
    return out + f'<div class="lt-shorts">{"".join(cards)}</div>'


def full_sheet(g, draw):
    bi, esc = g["bi"], g["esc"]
    p = {x["id"]: x for x in draw["prizes"]}
    rows = []
    for pid in FULL:
        t = p.get(pid)
        if not t:
            continue
        n = len(t["numbers"])
        nums = sorted(t["numbers"])
        cnt = (bi("%d รางวัล" % n, "%d prizes" % n) if n > 1
               else bi("1 รางวัล", "1 prize"))
        rows.append(
            f'<section class="lt-tier" id="t-{pid}">'
            f'<h3><span>{bi(t["th"], t["en"])}</span>'
            f'<span class="lt-tamt">{bi(baht(t.get("amount_baht")), baht(t.get("amount_baht")))}'
            f' <small>{bi("ต่อใบ", "per ticket")} · {cnt}</small></span></h3>'
            f'<div class="lt-nums w{len(nums[0])}">'
            + "".join(f'<b class="ln" data-t="{pid}" data-n="{esc(x)}">{esc(x)}</b>' for x in nums)
            + '</div></section>')
    return "".join(rows)


def past_block(g, past):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    if not past:
        return ""
    items = []
    for d in past:
        p = {x["id"]: x for x in d["prizes"]}
        th, en = short_date(d["date"])
        first = " ".join(p.get("first", {}).get("numbers") or [])

        def grp(pid, th_l, en_l):
            t = p.get(pid)
            if not t:
                return ""
            return (f'<span class="lt-pg">{bi(th_l, en_l)} '
                    f'<b>{esc(" ".join(t["numbers"]))}</b></span>')

        last2 = " ".join(p.get("last2", {}).get("numbers") or [])
        pdf = (f'<a href="{att(d["record_pdf"])}" rel="noopener">'
               f'{bi("ใบประกาศผล (PDF)", "Announcement (PDF)")}</a>'
               if d.get("record_pdf") else "")
        items.append(
            f'<li class="lt-past">'
            f'<span class="lt-pdate">{bi(d.get("date_th") or th, d.get("date_en") or en)}</span>'
            f'<span class="lt-pmain">'
            f'<span class="lt-pbig"><small>{bi("รางวัลที่ 1", "First prize")}</small>'
            f'<b>{esc(first)}</b></span>'
            f'<span class="lt-pbig"><small>{bi("ท้าย 2 ตัว", "Last two")}</small>'
            f'<b>{esc(last2)}</b></span></span>'
            f'<span class="lt-prow">{grp("front3", "หน้า 3 ตัว", "Front three")}'
            f'{grp("back3", "ท้าย 3 ตัว", "Last three")}</span>'
            f'<span class="lt-plinks">{pdf}'
            f'<button type="button" class="lt-use" data-d="{att(d["date"])}">'
            f'{bi("ตรวจกับงวดนี้", "Check this draw")}</button></span>'  # stylecheck: allow — a button label
            f'</li>')
    return (f'<h2 id="past">{bi("งวดก่อน", "Past draws")}</h2>'
            f'<ol class="lt-pasts">{"".join(items)}</ol>')


def checker(g, draws):
    bi, bi_text, att = g["bi"], g["bi_text"], g["att"]
    opts = "".join(
        f'<option value="{att(d["date"])}">'
        f'{att(bi_text(short_date(d["date"])[0], short_date(d["date"])[1]))}</option>'
        for d in draws)
    sel = ""
    if len(draws) > 1:
        sel = (f'<label class="lt-lab" for="lt-draw">{bi("งวด", "Draw")}</label>'
               f'<select id="lt-draw">{opts}</select>')
    return (
        f'<section class="lt-check" id="check">'
        f'<h2>{bi("ตรวจสลาก", "Ticket check")}</h2>'
        f'<label class="lt-lab" for="lt-in">{bi("เลขสลาก 6 หลัก", "Six-digit ticket number")}</label>'
        f'<input id="lt-in" type="text" inputmode="numeric" autocomplete="off" '
        f'maxlength="12" spellcheck="false" placeholder="000000" '
        f'aria-describedby="lt-out">'
        f'{sel}'
        f'<div id="lt-out" class="lt-out" aria-live="polite"></div>'
        f'<noscript><p>{bi("ช่องตรวจนี้ใช้ JavaScript", "This check needs JavaScript.")}</p></noscript>'
        f'</section>')


def build_page(g, doc, hist):
    bi, bi_text, esc, att = g["bi"], g["bi_text"], g["esc"], g["att"]
    draw = doc["draw"]
    draws = [draw] + [d for d in (hist or []) if d.get("date") != draw["date"]]
    draws = sorted(draws, key=lambda d: d["date"], reverse=True)
    past = [d for d in draws if d["date"] != draw["date"]]

    labels = {}
    for d in draws:
        for x in d["prizes"]:
            labels.setdefault(x["id"], [x["th"], x["en"]])
    pay = json.dumps({"latest": draw["date"], "L": labels,
                      "draws": [compact(d) for d in draws]},
                     ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    pdf = ""
    if draw.get("record_pdf"):
        pdf = (f'<p class="lt-pdf"><a href="{att(draw["record_pdf"])}" rel="noopener">'
               f'{bi("ใบประกาศผลของสำนักงานสลากกินแบ่งรัฐบาล (PDF)", "The Lottery Office’s announcement sheet (PDF)")}'
               f'</a></p>')

    read = (doc.get("fetched_at") or doc.get("generated") or "")[:16].replace("T", " ")
    files = ' · <a href="data/lottery.json">lottery.json</a>'
    if past:
        files += ' · <a href="data/lottery_history.json">lottery_history.json</a>'

    body = (
        f'<h1>{bi("สลากกินแบ่งรัฐบาล", "Thai government lottery")}</h1>'
        f'<p class="lt-when">{bi("งวด" + draw["date_th"], "Draw of " + draw["date_en"])}</p>'
        + head_block(g, draw)
        + checker(g, draws)
        + pdf
        + f'<h2 id="all">{bi("รางวัลทั้งหมด", "All prizes")}</h2>'
        f'<p class="lt-note">{bi("ในแต่ละรางวัล เลขเรียงจากน้อยไปมาก", "Numbers in each tier run smallest to largest.")}</p>'
        + full_sheet(g, draw)
        + past_block(g, past)
        + f'<h2 id="source">{bi("ที่มา", "Source")}</h2>'
        f'<p class="lt-src">'
        + bi(f"สำนักงานสลากกินแบ่งรัฐบาล · อ่านเมื่อ {read}",
             f"Government Lottery Office, read {read}")
        + f' · <a href="https://www.glo.or.th/" rel="noopener">glo.or.th</a>{files}</p>'
        f'<script type="application/json" id="lt-data">{pay}</script>'
        + g["share_block"](g["BASE"] + "lottery.html",
                           "สลากกินแบ่งรัฐบาล · Thai government lottery — มดแดง"))

    th_short, en_short = short_date(draw["date"])
    return g["page"](
        f"สลากกินแบ่งรัฐบาล งวด {th_short} · Thai government lottery, {en_short}",
        body, depth=0, path="lottery.html", body_class="lt-dark",
        desc=bi_text(
            f"ผลสลากกินแบ่งรัฐบาลงวด{draw['date_th']} ทุกรางวัล ทุกเลข "
            f"พร้อมช่องตรวจสลากและงวดก่อน",
            f"Thai government lottery results for {draw['date_en']}: every prize "
            f"tier and number, a ticket check, and past draws."),
        extra_head=f'<link rel="stylesheet" href="lottery.css?v={version()}">'
                   f'<script src="lottery.js?v={version()}" defer></script>',
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("สลากกินแบ่ง", "Lottery"),
        updated=(doc.get("generated") or None))


def version():
    return "%08x" % (zlib.crc32((JS + CSS).encode()) & 0xFFFFFFFF)


def emit(g, data=None):
    DOCS, ROOT_ = g["DOCS"], g["ROOT"]
    src = ROOT_ / "data" / "lottery.json"
    if not src.exists():
        return "SKIPPED — no data/lottery.json (importers/make_lottery.py)"
    doc = json.loads(src.read_text(encoding="utf-8"))
    if not (doc.get("draw") or {}).get("prizes"):
        return "SKIPPED — data/lottery.json carries no prizes"
    hsrc = ROOT_ / "data" / "lottery_history.json"
    hist = []
    if hsrc.exists():
        try:
            hist = json.loads(hsrc.read_text(encoding="utf-8")).get("draws") or []
        except ValueError:
            hist = []
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "lottery.json").write_text(src.read_text(encoding="utf-8"),
                                                encoding="utf-8")
    if hist:
        (DOCS / "data" / "lottery_history.json").write_text(
            hsrc.read_text(encoding="utf-8"), encoding="utf-8")
    (DOCS / "lottery.css").write_text(CSS)
    (DOCS / "lottery.js").write_text(JS)
    html = build_page(g, doc, hist)
    (DOCS / "lottery.html").write_text(html)
    n_past = len([d for d in hist if d.get("date") != doc["draw"]["date"]])
    return "งวด %s, %d past draws, page %.0f kB" % (
        doc["draw"]["date"], n_past, len(html.encode()) / 1024)


CSS = """/* lottery.css — generated by lottery_layer.py */
body.lt-dark{--paper:#14110e;--ink:#f7f2e8;--ink-soft:#e6dccb;--mute:#d9cdb8;
 --card:#211c17;--card-alt:#2c251e;--link:#ffd48a;--visited:#ffd48a;--rule:#5a4a38;
 --soft:#5a4a38;--warm-border:#5a4a38;--gloss:#e6dccb;
 background:#14110e;color:#f7f2e8}
body.lt-dark main a,body.lt-dark main a:visited{color:#ffd48a}
body.lt-dark main{font-size:1.06rem}
.lt-when{font-size:1.25rem;font-weight:700;margin:.2rem 0 1rem}
.lt-first{display:flex;flex-direction:column;align-items:flex-start;gap:.2rem;
 background:#211c17;border:3px solid #ffd48a;border-radius:14px;padding:.9rem 1rem;margin:0 0 1rem}
.lt-flab{font-size:1.2rem;font-weight:700}
.lt-fnum{font-size:clamp(3rem,17vw,6rem);line-height:1.05;letter-spacing:.06em;
 font-variant-numeric:tabular-nums;color:#ffd48a;font-weight:800}
.lt-amt{font-size:1.25rem;font-weight:700}
.lt-amt small,.lt-tamt small{font-size:1rem;font-weight:400;color:#e6dccb}
.lt-shorts{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:.7rem;margin:0 0 1.2rem}
.lt-short{background:#211c17;border:2px solid #6b5a45;border-radius:12px;padding:.7rem .9rem;
 display:flex;flex-direction:column;gap:.25rem}
.lt-slab{font-weight:700;font-size:1.05rem}
.lt-snums{display:flex;flex-wrap:wrap;gap:.2rem .9rem}
.lt-snums b{font-size:2.6rem;line-height:1.1;letter-spacing:.06em;font-variant-numeric:tabular-nums;
 color:#fff;border-radius:6px;padding:0 .1em}
.lt-check{background:#211c17;border:3px solid #f7f2e8;border-radius:14px;padding:.9rem 1rem 1rem;margin:0 0 1.2rem}
.lt-check h2{margin-top:0}
.lt-lab{display:block;font-weight:700;margin:.5rem 0 .3rem}
#lt-in{font:inherit;font-size:2.4rem;font-weight:800;letter-spacing:.14em;width:100%;max-width:12em;
 box-sizing:border-box;padding:.3rem .5rem;background:#0b0907;color:#fff;border:3px solid #ffd48a;
 border-radius:10px;font-variant-numeric:tabular-nums}
#lt-in::placeholder{color:#8d806c}
#lt-in:focus,#lt-draw:focus,.lt-use:focus{outline:3px solid #fff;outline-offset:2px}
#lt-draw{font:inherit;font-size:1.1rem;padding:.4rem .5rem;background:#0b0907;color:#fff;
 border:2px solid #e6dccb;border-radius:8px;max-width:100%}
.lt-out{margin-top:.8rem;font-size:1.15rem}
.lt-out:empty{display:none}
.lt-out .lt-miss{font-weight:700}
.lt-out p{margin:.1rem 0}
.lt-out ul{list-style:none;padding:0;margin:.3rem 0}
.lt-out li{display:flex;flex-wrap:wrap;justify-content:space-between;gap:.2rem 1rem;
 border-bottom:1px solid #5a4a38;padding:.4rem 0}
.lt-out li b{font-variant-numeric:tabular-nums}
.lt-total{display:block;margin-top:.5rem;font-size:2rem;font-weight:800;color:#ffd48a}
.lt-pdf{font-size:1.15rem;font-weight:700;margin:0 0 1.2rem}
.lt-note{color:#e6dccb}
.lt-tier{margin:0 0 1.2rem}
.lt-tier h3{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;
 gap:.2rem 1rem;font-size:1.25rem;border-bottom:2px solid #6b5a45;padding-bottom:.3rem;margin:0 0 .5rem}
.lt-tamt{font-size:1.15rem;color:#ffd48a}
.lt-nums{display:grid;gap:.35rem;grid-template-columns:repeat(auto-fill,minmax(5.8rem,1fr))}
.lt-nums.w3{grid-template-columns:repeat(auto-fill,minmax(4rem,1fr))}
.lt-nums.w2{grid-template-columns:repeat(auto-fill,minmax(3.2rem,1fr))}
.lt-nums b{font-size:1.35rem;font-weight:700;letter-spacing:.04em;font-variant-numeric:tabular-nums;
 text-align:center;background:#211c17;border:1px solid #4a3e31;border-radius:6px;padding:.25rem 0;color:#fff}
.ln.hit,.lt-nums b.hit,.lt-snums b.hit{background:#ffd48a;color:#14110e;outline:3px solid #fff}
.lt-fnum.hit{color:#14110e;background:#ffd48a;border-radius:8px;padding:0 .15em}
.lt-pasts{list-style:none;padding:0;margin:.5rem 0 1.2rem;display:grid;gap:.7rem;
 grid-template-columns:repeat(auto-fill,minmax(17rem,1fr))}
.lt-past{background:#211c17;border:2px solid #4a3e31;border-radius:12px;padding:.7rem .9rem;
 display:flex;flex-direction:column;gap:.3rem}
.lt-pdate{font-weight:700}
.lt-pmain{display:flex;flex-wrap:wrap;gap:.2rem 1.4rem;align-items:flex-end}
.lt-pbig small{display:block;font-size:1rem;color:#e6dccb}
.lt-pbig b{font-size:2rem;line-height:1.1;letter-spacing:.06em;font-variant-numeric:tabular-nums;color:#ffd48a}
.lt-prow{display:flex;flex-direction:column;gap:.1rem;color:#e6dccb}
.lt-pg b{white-space:nowrap;font-size:1.2rem;color:#fff;font-variant-numeric:tabular-nums;letter-spacing:.04em}
.lt-plinks{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:center;margin-top:.2rem}
.lt-use{font:inherit;font-size:1rem;font-weight:700;background:#ffd48a;color:#14110e;border:0;
 border-radius:2rem;padding:.35rem .9rem;cursor:pointer}
.lt-src{color:#e6dccb}
"""


JS = r"""/* lottery.js — generated by lottery_layer.py. The ticket check. */
(function(){
var el=document.getElementById('lt-data');if(!el)return;
var D;try{D=JSON.parse(el.textContent);}catch(e){return;}
var input=document.getElementById('lt-in'),sel=document.getElementById('lt-draw'),
    out=document.getElementById('lt-out');
if(!input||!out)return;
var BY={};D.draws.forEach(function(d){BY[d.d]=d;});
/* six digits: first, near_first, second..fifth; front3 the first three;
   back3 the last three; last2 the last two */
var MATCH={first:6,near_first:6,second:6,third:6,fourth:6,fifth:6,front3:'f3',back3:'b3',last2:'b2'};
var ORDER=['first','near_first','second','third','fourth','fifth','front3','back3','last2'];
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function bi(th,en){if(th===en)return '<span class="th solo" lang="th">'+esc(th)+'</span>';
 return '<span class="bi"><span class="th" lang="th">'+esc(th)+'</span><span class="en" lang="en">'+
 '<span class="th" lang="th"> · </span>'+esc(en)+'</span></span>';}
function baht(n){return '฿'+Number(n).toLocaleString('en-US');}
function digits(s){
 /* Thai digits ๐-๙ count as 0-9; anything else that is not a digit drops */
 return s.replace(/[๐-๙]/g,function(c){return String(c.charCodeAt(0)-0x0E50);}).replace(/\D/g,'');}
function wins(t,d){
 var hits=[];
 ORDER.forEach(function(id){var tier=d.t[id];if(!tier)return;var m=MATCH[id];
  tier.n.forEach(function(n){
   var ok=m===6?t===n:m==='f3'?t.slice(0,3)===n:m==='b3'?t.slice(3)===n:t.slice(4)===n;
   if(ok)hits.push({id:id,n:n,a:tier.a||0,th:(D.L[id]||[id])[0],en:(D.L[id]||[id,id])[1]});});});
 return hits;}
function mark(hits,d){
 document.querySelectorAll('.ln.hit').forEach(function(b){b.classList.remove('hit');});
 if(d.d!==D.latest)return;
 hits.forEach(function(h){
  document.querySelectorAll('.ln[data-t="'+h.id+'"][data-n="'+h.n+'"]').forEach(function(b){b.classList.add('hit');});});}
function run(){
 var t=digits(input.value);
 if(input.value!==t)input.value=t.slice(0,6);
 t=t.slice(0,6);
 var d=BY[sel?sel.value:D.latest]||D.draws[0];
 if(!t.length){out.innerHTML='';mark([],d);return;}
 if(t.length<6){var k=6-t.length;
  out.innerHTML='<p>'+bi('อีก '+k+' หลัก','Type '+k+' more digit'+(k>1?'s':''))+'</p>';mark([],d);return;}
 var hits=wins(t,d),when=bi('งวด '+d.th,'draw of '+d.en);
 mark(hits,d);
 if(!hits.length){
  out.innerHTML='<p class="lt-miss"><b>'+t+'</b> '+bi('ไม่ถูกรางวัล','wins nothing')+'</p><p>'+when+'</p>';return;}
 var total=0,li=hits.map(function(h){total+=h.a;
  return '<li><span>'+bi(h.th,h.en)+' <b>'+esc(h.n)+'</b></span><b>'+baht(h.a)+'</b></li>';}).join('');
 out.innerHTML='<p><b>'+t+'</b> '+bi('ถูกรางวัล','wins')+'</p><p>'+when+'</p><ul>'+li+'</ul>'+
  '<span class="lt-total">'+bi('รวม '+baht(total),'Total '+baht(total))+'</span>';}
input.addEventListener('input',run);
if(sel)sel.addEventListener('change',run);
document.querySelectorAll('.lt-use').forEach(function(b){b.addEventListener('click',function(){
 if(sel){sel.value=b.dataset.d;}run();
 document.getElementById('check').scrollIntoView({behavior:'smooth',block:'start'});
 input.focus({preventScroll:true});});});
run();
})();
"""


def main():
    import build  # importing does not build: build() runs under __main__ only
    if not (build.DOCS / "index.html").exists():
        raise SystemExit("docs/ is not built yet — run python3 build.py first")
    print(emit(vars(build)))


if __name__ == "__main__":
    main()
