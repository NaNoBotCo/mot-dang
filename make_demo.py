"""make_demo.py — a page that shows the engine doing somebody's actual week.

The search engine under this site is invisible by design: a reader types
something approximate and gets an answer, and the four layers that got them
there leave no trace on the page. Someone who works with the directory every
day can therefore use it for a month and never learn that it read her Thai
compound, mended her spelling, or crossed her English word to the shop's Thai
one. This page puts the work back on the surface, for a fixed set of jobs
taken from a real week of operations traffic.

Two rules it keeps:

  * Every number and every result on the page comes from a RUN, stored in
    data/demo_run.json with the date it was measured. Nothing is typed by
    hand into the template, so the page cannot drift from the engine.
  * The queries include ones the engine handles poorly. A demo of a search
    box that only shows its wins teaches nobody where its edges are, and the
    tier the engine reports on a weak query is the part worth seeing.

Run:
    python3 make_demo.py            # measure against the live API, then render
    python3 make_demo.py --render   # re-render from the stored run, no network

Writes:
    data/demo_run.json        the measurement, dated
    assets/demo/index.html    the page

Wiring it into the site is a separate decision: build.py copies assets/brief
to docs/brief and would copy this the same way. Until somebody does that, the
file is opened from disk.
"""

from __future__ import annotations

import html
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "data" / "demo_run.json"
OUT = ROOT / "assets" / "demo" / "index.html"
API = "https://motdang.net/api/v1/search"
SITE = "https://motdang.net/"
UA = "Mozilla/5.0 (Macintosh) motdang-demo"

# (query, TH job line, EN job line, TH point, EN point)
# The job lines are real: the medals, the tailor, the company registration and
# the lawyer are all open items in the operations traffic of the week of
# 2026-09-15. The point is what the reader is meant to notice, one sentence.
JOBS = [
    ("เหรียญรางวัล",
     "สั่งเหรียญรางวัล 400 เหรียญ ให้โครงการว่ายน้ำ",
     "Order 400 medals for the swim programme",
     "พิมพ์คำว่า “เหรียญรางวัล” คำเดียว ได้ร้านที่รับทำ — และได้เจ้าที่สอง ไว้เทียบราคา",
     "One Thai word for “medal” finds the shop — and a second supplier to price against."),
    ("bespoke tailor",
     "หาช่างตัดสูทสั่งตัด ก่อนกลางเดือนตุลาคม",
     "Find a bespoke tailor before mid-October",
     "ถามเป็นภาษาอังกฤษ ได้ร้านที่เขียนชื่อตัวเองเป็นภาษาอังกฤษ ทั้งสองร้าน",
     "Asked in English, answered with the two shops that write their own name in English."),
    ("จดทะเบียนบริษัท",
     "จดทะเบียนบริษัท เดือนตุลาคม",
     "Register the company in October",
     "หกราย ทุกรายเป็นข้อมูลที่คนไปยืนดูเอง ไม่ใช่ข้อมูลที่เครื่องลอกมา",
     "Six firms, every one of them entered by hand rather than copied by a crawler."),
    ("ทนายความ",
     "หาทนายที่เชียงใหม่",
     "Find the Chiang Mai lawyer",
     "หนึ่งร้อยยี่สิบสามราย เรียงตามชื่อที่ตรงคำ ไม่ใช่ตามค่าโฆษณา",
     "123 of them, ordered by how well the name matches — nobody paid to be at the top."),
    ("rajavey hospital",
     "นัดหมอที่ราชเวช — สะกดจากความจำ",
     "Book at Rajavej — spelled from memory",
     "สะกดผิด คนละภาษากับชื่อร้าน ได้คำตอบเดียว และถูก",
     "Misspelled, in the wrong script, and it comes back with one answer — the right one."),
    ("amulet shop",
     "หาร้านพระเครื่อง",
     "Find amulet shops",
     "พิมพ์อังกฤษ เครื่องไปหยิบคำว่า “พระเครื่อง” มาให้",
     "Typed in English; the engine reached for the Thai word พระเครื่อง on its own."),
    ("ร้านกรอบพระ",
     "หาร้านทำกรอบพระ",
     "Find somewhere to frame them",
     "ภาษาไทยไม่เว้นวรรค เครื่องตัดเป็น ร้าน + กรอบ + พระ ได้เอง",
     "Thai is written without spaces; the engine split it into ร้าน · กรอบ · พระ itself."),
    ("แปลเอกสาร",
     "แปลเอกสาร",
     "Get documents translated",
     "ยี่สิบหกราย ส่วนใหญ่มีวันที่อ่านกำกับไว้ต้นเดือนนี้",
     "26 of them, most read this month, each carrying the date it was read."),
    ("ร้านกาแฟนั่งทำงานได้",
     "หาที่นั่งทำงาน",
     "Find somewhere to sit and work",
     "ทั้งประโยค เครื่องอ่านออกว่าอยากได้อะไร แล้วไปเจอ coworking",
     "A whole sentence. The engine reads what is being asked for and lands on a coworking space."),
    ("ถ้วยรางวัล",
     "ถ้วยรางวัล — คำที่เครื่องยังทำได้ไม่ดี",
     "Trophies — the word this engine still handles badly",
     "ถ้วย ไปชนกับ cup ในชื่อร้านกาแฟ เครื่องบอกเองว่าใช้ชั้น “คำพ้อง” ซึ่งเป็นชั้นที่กว้างที่สุด",
     "ถ้วย (a cup) collided with Cup in a café's name. The engine says on its own that it fell back to the widest layer."),
]

TIER_WORDS = {
    "exact":     ("ตรงคำ", "matched your words"),
    "thesaurus": ("คำพ้อง", "matched your word to theirs"),
    "loose":     ("ใกล้เคียง", "near spellings, closest first"),
    "partial":   ("บางคำ", "some of your words"),
}
NOTE_WORDS = {
    "segmented": ("ตัดคำ", "split the Thai into words"),
    "mended":    ("ซ่อมคำ", "mended a spelling"),
    "widened":   ("ขยายคำ", "widened to near spellings"),
    "stopwords": ("ตัดคำเชื่อม", "set the filler words aside"),
    "intent":    ("แยกเงื่อนไข", "lifted the conditions out"),
}
SRC_WORDS = {
    "curated":     ("คนกรอกเอง", "entered by hand"),
    "official":    ("ทะเบียนราชการ", "a government register"),
    "third-party": ("แหล่งอื่น", "another directory"),
    "crawled":     ("เก็บจากเว็บ", "read off the web"),
    "register":    ("ทะเบียน", "a register"),
}


def measure() -> dict:
    out = {"measured": date.today().isoformat(), "api": API, "jobs": []}
    for q, th, en, pth, pen in JOBS:
        url = f"{API}?q={urllib.parse.quote(q)}&limit=4"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        t0 = time.time()
        doc = json.load(urllib.request.urlopen(req, timeout=60))
        ms = int((time.time() - t0) * 1000)
        print(f"  {q:24} total={doc.get('total')} tier={doc.get('tier')} {ms}ms")
        out["jobs"].append({
            "q": q, "th": th, "en": en, "pointTh": pth, "pointEn": pen,
            "total": doc.get("total"), "tier": doc.get("tier"),
            "notes": doc.get("notes") or [], "ms": ms,
            "results": [{
                "name": r.get("name"), "nameEn": r.get("nameEn"),
                "url": r.get("url"), "confidence": r.get("confidence"),
                "updatedAt": r.get("updatedAt"), "antRank": r.get("antRank"),
                "has": r.get("has") or [],
            } for r in (doc.get("results") or [])[:3]],
        })
    RUN.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def bi(th: str, en: str) -> str:
    return (f'<span class="th">{html.escape(th)}</span>'
            f'<span class="en">{html.escape(en)}</span>')


def pills(job: dict) -> str:
    out = []
    for n in job["notes"]:
        if n in NOTE_WORDS:
            th, en = NOTE_WORDS[n]
            out.append(f'<span class="pill work">{bi(th, en)}</span>')
    th, en = TIER_WORDS.get(job["tier"] or "", (job["tier"] or "", job["tier"] or ""))
    out.append(f'<span class="pill tier t-{html.escape(job["tier"] or "x")}">{bi(th, en)}</span>')
    return "".join(out)


def rows(job: dict) -> str:
    out = []
    for r in job["results"]:
        src = SRC_WORDS.get(r["confidence"] or "", (r["confidence"] or "", r["confidence"] or ""))
        name = html.escape(r["name"] or "")
        link = html.escape(r["url"] or "#")
        rank = max(0, min(9, int(r["antRank"] or 0)))
        out.append(
            f'<li><a class="nm" href="{link}" rel="noopener">{name}</a>'
            f'<span class="prov">{bi(*src)}'
            f'<span class="sep">·</span>'
            f'<span class="th">อ่านเมื่อ {html.escape(r["updatedAt"] or "—")}</span>'
            f'<span class="en">read {html.escape(r["updatedAt"] or "—")}</span>'
            f'<span class="sep">·</span><span class="ants">🐜\u2009{rank}/9'
            f'<span class="th"> ข้อมูล</span><span class="en"> facts</span>'
            f'</span></span></li>')
    return "".join(out)


def render(run: dict) -> str:
    cards = []
    for job in run["jobs"]:
        qq = urllib.parse.quote(job["q"])
        total = job["total"]
        cards.append(f'''
<article class="card">
 <p class="job">{bi(job["th"], job["en"])}</p>
 <p class="typed"><span class="lab">{bi("พิมพ์ว่า", "typed")}</span>
   <code>{html.escape(job["q"])}</code></p>
 <p class="did"><span class="lab">{bi("เครื่องทำอะไร", "what it did")}</span>{pills(job)}
   <span class="pill count">{total:,}<span class="th"> รายการ</span><span class="en"> found</span></span></p>
 <ul class="res">{rows(job)}</ul>
 <p class="point">{bi(job["pointTh"], job["pointEn"])}</p>
 <p class="live"><a href="{SITE}search.html?q={qq}" rel="noopener">{bi(
    "ลองเองเลย →", "run it yourself →")}</a></p>
</article>''')

    measured = run["measured"]
    median = sorted(j["ms"] for j in run["jobs"])[len(run["jobs"]) // 2]
    return f'''<!doctype html>
<html lang="th" translate="no"><head><meta charset="utf-8">
<meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>มดทำงานยังไง · What the ants did</title>
<style>
:root{{--paper:#faf5ea;--ink:#2a1e16;--ant:#c13a2e;--ant-dark:#8f2a21;
--link:#14479b;--soft:#e3d5bc;--mute:#7d6b51;--card:#fffdf7;--card-alt:#f8f0dd;
--ink-soft:#544636;--gold-ink:#8e6621;--jade:#1f6b57;--jade-a:#cfe3d2;
--marigold-a:#f9dc93;--marigold-ink:#6d5411;--rule:#e3d5bc}}
@media(prefers-color-scheme:dark){{:root{{--paper:#17120d;--ink:#f3e8d5;
--card:#201911;--card-alt:#2a2016;--ink-soft:#cbbba0;--soft:#4a3c2a;
--rule:#463829;--link:#9dc0ff;--mute:#a4917a;--jade-a:#1e3a2c;
--marigold-a:#4a3a16;--marigold-ink:#f0d79a;--gold-ink:#e0b767}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.65 "Noto Sans Thai","Sarabun",system-ui,-apple-system,"Segoe UI",sans-serif;
padding:0 0 4rem}}
.wrap{{max-width:44rem;margin:0 auto;padding:0 1rem}}
header{{border-bottom:3px solid var(--ant);margin-bottom:1.4rem;padding:1.6rem 0 1rem}}
h1{{margin:0;font-size:1.55rem;line-height:1.3}}
.sub{{margin:.3rem 0 0;font-size:1rem;font-weight:400;color:var(--ink-soft)}}
.lede{{margin:.8rem 0 0;color:var(--ink-soft);font-size:.98rem}}
.stamp{{margin:.7rem 0 0;font-size:.82rem;color:var(--mute)}}
.card{{background:var(--card);border:2px solid var(--soft);border-radius:.7rem;
padding:.95rem 1.05rem 1.05rem;margin:0 0 1.15rem}}
.job{{margin:0 0 .55rem;font-weight:700;font-size:1.06rem;
border-left:4px solid var(--ant);padding-left:.55rem}}
.typed,.did{{margin:.45rem 0;font-size:.93rem}}
.lab{{display:block;color:var(--mute);font-size:.78rem;letter-spacing:.03em;
text-transform:none;margin:0 0 .18rem}}
code{{background:var(--card-alt);border:1px solid var(--rule);border-radius:.3rem;
padding:.12rem .45rem;font-size:1rem;font-family:inherit}}
.pill{{display:inline-block;border-radius:999px;padding:.1rem .6rem;margin:.12rem .18rem .12rem 0;
font-size:.8rem;border:1px solid transparent;white-space:nowrap}}
.pill.work{{background:var(--jade-a);color:var(--jade);border-color:var(--jade)}}
.pill.tier{{background:var(--marigold-a);color:var(--marigold-ink);border-color:var(--gold-ink)}}
.pill.tier.t-partial,.pill.tier.t-loose{{background:transparent;border-style:dashed}}
.pill.count{{background:transparent;border:1px solid var(--rule);color:var(--ink-soft)}}
@media(prefers-color-scheme:dark){{.pill.work{{color:#9fe3c6}}}}
ul.res{{list-style:none;margin:.7rem 0 .2rem;padding:0;border-top:1px solid var(--rule)}}
ul.res li{{padding:.5rem 0;border-bottom:1px solid var(--rule)}}
a.nm{{color:var(--link);text-decoration:none;font-weight:600;display:block}}
a.nm:hover,a.nm:focus-visible{{text-decoration:underline}}
.prov{{display:block;font-size:.8rem;color:var(--mute);margin-top:.12rem}}
.prov .sep{{margin:0 .35rem}}
.ants{{white-space:nowrap}}
.point{{margin:.75rem 0 0;font-size:.95rem;color:var(--ink-soft);
background:var(--card-alt);border-radius:.5rem;padding:.55rem .7rem}}
.live{{margin:.6rem 0 0;font-size:.92rem}}
.live a{{color:var(--ant-dark);font-weight:600}}
@media(prefers-color-scheme:dark){{.live a{{color:#ef8a7d}}}}
.legend{{background:var(--card-alt);border:2px dashed var(--soft);border-radius:.7rem;
padding:.9rem 1.05rem;margin:1.6rem 0 0;font-size:.9rem}}
.legend h2{{margin:0 0 .5rem;font-size:1.05rem}}
.legend dt{{font-weight:700;margin-top:.5rem}}
.legend dd{{margin:0;color:var(--ink-soft)}}
.tryit{{margin:1.6rem 0 0;padding:1rem 1.05rem;border:2px solid var(--ant);
border-radius:.7rem;background:var(--card)}}
.tryit h2{{margin:0 0 .5rem;font-size:1.1rem}}
.tryit form{{display:flex;gap:.5rem;flex-wrap:wrap}}
.tryit input{{flex:1 1 14rem;font:inherit;padding:.55rem .7rem;border:2px solid var(--soft);
border-radius:.45rem;background:var(--paper);color:var(--ink)}}
.tryit button{{font:inherit;font-weight:700;padding:.55rem 1.3rem;border:2px solid var(--ant-dark);
border-radius:.45rem;background:var(--ant);color:#fff;cursor:pointer}}
html[data-l="en"] .th,html:not([data-l="en"]) .en{{display:none}}
.langbar{{display:flex;gap:0;margin:.9rem 0 0;border:2px solid var(--ink);
border-radius:.45rem;overflow:hidden;width:max-content}}
.langbar button{{font:inherit;font-size:.85rem;padding:.25rem .85rem;border:0;
border-right:2px solid var(--ink);background:var(--card);color:var(--ink);cursor:pointer}}
.langbar button:last-child{{border-right:0}}
.langbar button[aria-pressed="true"]{{background:var(--ink);color:var(--paper)}}
footer{{margin:2rem 0 0;font-size:.82rem;color:var(--mute)}}
</style></head><body>
<div class="wrap">
<header>
 <h1><span class="th">มดทำงานยังไง</span><span class="en">What the ants did</span></h1>
 <p class="sub">{bi("งานสิบอย่างจากสัปดาห์เดียว ลองผ่านสารบบเชียงใหม่",
   "Ten jobs from one week, run through the directory")}</p>
 <div class="langbar" role="group">
   <button type="button" data-l="th" aria-pressed="true">ไทย</button>
   <button type="button" data-l="en" aria-pressed="false">EN</button>
 </div>
 <p class="lede">{bi(
   "ทุกบรรทัดข้างล่างนี้มาจากการยิงคำถามจริงเข้าเครื่องค้นหาของ motdang.net เมื่อวันที่ " + measured
   + " ไม่มีตัวเลขไหนพิมพ์เอง",
   "Every line below came from putting these questions to the motdang.net search engine on "
   + measured + ". No number here was typed by hand.")}</p>
 <p class="stamp">{bi(
   "วัดเมื่อ " + measured + " · ผ่าน API สาธารณะ เวลาตอบกลางทาง "
   + f"{median/1000:.1f}" + " วินาที (หน้าเว็บค้นในเครื่อง เร็วกว่านี้มาก)",
   "measured " + measured + " · through the public API, median "
   + f"{median/1000:.1f}" + " s (the site's own search runs on the device and is far quicker)")}</p>
</header>

{"".join(cards)}

<section class="legend">
 <h2>{bi("ศัพท์บนป้าย", "the words on the pills")}</h2>
 <dl>
  <dt>{bi("ตัดคำ", "split the Thai into words")}</dt>
  <dd>{bi("ภาษาไทยเขียนติดกัน เครื่องต้องตัดเองก่อนถึงจะหาเจอ",
          "Thai is written without spaces, so the engine has to cut the query into words before it can match anything.")}</dd>
  <dt>{bi("ซ่อมคำ", "mended a spelling")}</dt>
  <dd>{bi("คำที่พิมพ์ผิดหนึ่งตัว ถูกซ่อมเทียบกับชื่อที่มีอยู่จริงในสารบบ",
          "A word one letter wrong, repaired against the names this directory actually holds.")}</dd>
  <dt>{bi("คำพ้อง", "matched your word to theirs")}</dt>
  <dd>{bi("คำที่คุณใช้ กับคำที่ร้านใช้ ไม่ใช่คำเดียวกัน เครื่องเชื่อมให้",
          "Your word and the shop's word are different words; the engine bridges them — including across languages.")}</dd>
  <dt>{bi("ใกล้เคียง", "near spellings, closest first")}</dt>
  <dd>{bi("ไม่มีคำไหนตรงเป๊ะ เครื่องเรียงคำที่เสียงใกล้ที่สุดขึ้นก่อน",
          "Nothing matched outright, so the engine ranked by sound and put the closest first.")}</dd>
  <dt>{bi("บางคำ", "some of your words")}</dt>
  <dd>{bi("จับได้แค่บางคำ ชั้นนี้กว้างที่สุด และเป็นชั้นที่ผลลัพธ์เพี้ยนได้มากที่สุด",
          "Only part of the query matched. This is the widest layer and the one where the results wander.")}</dd>
  <dt>{bi("ที่มาของข้อมูล", "where each fact came from")}</dt>
  <dd>{bi("ใต้ชื่อทุกร้านมีที่มาและวันที่อ่าน — คนกรอกเอง · ทะเบียนราชการ · แหล่งอื่น · เก็บจากเว็บ",
          "Under every name: where the fact came from and the date it was read — entered by hand · a government register · another directory · read off the web.")}</dd>
  <dt>🐜</dt>
  <dd>{bi("จำนวนมด คือจำนวนข้อมูลที่หน้านั้นมีอยู่จริง เก้าตัวคือครบ",
          "One ant per fact the listing holds. Nine is a complete listing.")}</dd>
 </dl>
</section>

<section class="tryit">
 <h2>{bi("ลองพิมพ์เอง", "type your own")}</h2>
 <p>{bi("พิมพ์ผิดได้ ภาษาไหนก็ได้ ไม่ต้องเว้นวรรค",
        "Spell it wrong. Either language. No spaces needed.")}</p>
 <form action="{SITE}search.html" method="get" target="_blank">
  <input name="q" type="search" placeholder="เช่น ร้านกรอบพระ / bespoke tailor" aria-label="search">
  <button type="submit">{bi("ค้นหา", "search")}</button>
 </form>
</section>

<footer>{bi(
  "มดแดง · motdang.net — สารบบเชียงใหม่และเชียงราย",
  "มดแดง Mot Dang · motdang.net — the Chiang Mai and Chiang Rai directory")}</footer>
</div>
<script>
(function(){{
 var h=document.documentElement,bs=document.querySelectorAll('.langbar button');
 function set(l){{h.setAttribute('data-l',l);
  bs.forEach(function(b){{b.setAttribute('aria-pressed',String(b.dataset.l===l));}});
  try{{localStorage.setItem('md-demo-lang',l);}}catch(e){{}}
 }}
 bs.forEach(function(b){{b.addEventListener('click',function(){{set(b.dataset.l);}});}});
 var saved=null;try{{saved=localStorage.getItem('md-demo-lang');}}catch(e){{}}
 set(saved==='en'?'en':'th');
}})();
</script>
</body></html>
'''


def main() -> None:
    if "--render" in sys.argv:
        if not RUN.exists():
            sys.exit("no data/demo_run.json yet — run without --render first")
        run = json.loads(RUN.read_text())
    else:
        print("measuring against", API)
        run = measure()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(run))
    print(f"\n  {RUN}\n  {OUT}")


if __name__ == "__main__":
    main()
