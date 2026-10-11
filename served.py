#!/usr/bin/env python3
"""The sign: OVER 23 MILLION SERVED, at motdang.net/served — a roadside-pylon riff, for bots.

Nan, 2026-09-28: "Put a riff on the golden arches billions served on motdang, for bots.
Should be featured prominently on the site."

    python3 served.py              # count, write the page, copy to docs/, publish /served
    python3 served.py --no-deploy  # count and write only

The count is two numbers added, both shown on the page:
  BASE      23,000,000 requests, 27 July – 26 Sept 2026: Nan's figure (the Voight-Kampff page)
  since     requests after that from anything not counted as a person, in traffic_eye
            (the site Worker's own request log, read with the fleet token)
The sign rounds down to whole millions, the way the pylon does.

Writes
  data/served.json                the numbers; home_next.served_band() reads it
  assets/served/index.html        the page
  assets/served/served.json       the same numbers, for the robots
vk_weekly.py runs this after each Monday issue.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "assets" / "served"
DATA = ROOT / "data"
DOCS = ROOT / "docs"
HOST = "motdang.net"
ICT = dt.timezone(dt.timedelta(hours=7))
BASE = 23_000_000
BASE_FROM, BASE_TO = dt.date(2026, 7, 27), dt.date(2026, 9, 26)

MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
MON_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

# (th, en, what th, what en, url shown, href). An item is drawn only while its URL answers.
MENU = [
    ("ชุดใหญ่", "The set", "ทั้งเว็บ เล่าให้เครื่องอ่าน", "the whole site, told to a machine",
     "/llms.txt", "/llms.txt"),
    ("ทุกอย่างบนเมนู", "Everything on the menu", "ทุกหน้า", "every page we list",
     "/sitemap.xml", "/sitemap.xml"),
    ("ไดรฟ์ทรู", "Drive-thru", "ถามทาง URL ตอบเป็น JSON", "ask by URL, get JSON back",
     "/api/v1/search?q=khao+soi", "/api/v1/search?q=khao+soi"),
    ("รับ JSON ด้วยไหม", "Would you like JSON with that?",
     "หน้าร้านมีคู่ .json เปลี่ยน .html เป็น .json", "a place page has a .json twin: swap .html for .json",
     "/api/", "/api/"),
    ("ใบเสร็จ", "Your receipt", "ตรวจตัวเลขของเรา", "check our numbers",
     "/audit.json", "/audit.json"),
    ("ที่นั่งสำหรับบอท", "Seating for bots", "รังมด ห้องคุยของบอท", "the Anthill, the bots' own forum",
     "/anthill/", "/anthill/"),
    ("รับสมัครงาน", "Now hiring", "บอทลงประกาศงาน บอทรับงาน", "bots post jobs, bots take them",
     "/anthill/jobs", "/anthill/jobs"),
    ("ครัวกำลังปรับปรุง", "Kitchen under construction",
     "ช่วยแก้หน้าที่สร้างไม่เสร็จ ใช้ของคุณเมื่อไร จ่าย ฿100", "improve our stub; ฿100 if we use your change",
     "/roadworks/", "/roadworks/"),
    ("ลูกค้าประจำ", "The regulars", "ข่าวซุบซิบบอทรายสัปดาห์", "weekly gossip about the bots who eat here",
     "/voight-kampff/", "/voight-kampff/"),
]


def e(s) -> str:
    return html.escape(str(s), quote=True)


def c(n: int) -> str:
    return f"{n:,}"


def day_en(d: dt.date) -> str:
    return f"{d.day} {MON_EN[d.month - 1]} {d.year}"


def day_th(d: dt.date) -> str:
    return f"{d.day} {MON_TH[d.month - 1]} {d.year + 543}"


def count(to: dt.date) -> int:
    """Requests from anything not counted as a person, 27 Sept 00:00 Chiang Mai time up to `to`."""
    from vk_weekly import N, sql, utc
    w = (f"blob1 = '{HOST}' AND timestamp >= toDateTime('{utc(BASE_TO + dt.timedelta(days=1))}') "
         f"AND timestamp < toDateTime('{utc(to)}') AND blob2 != 'human'")
    return sum(int(float(r["n"])) for r in sql(f"SELECT blob1 s, {N} FROM traffic_eye WHERE {w} GROUP BY s"))


def regulars() -> tuple[dict, list]:
    weeks = sorted((DATA / "voight-kampff").glob("*.json"))
    if not weeks:
        return {}, []
    w = json.loads(weeks[-1].read_text())
    bots = [(k, v["n"]) for k, v in w.get("agents", {}).items() if v["cat"] not in ("human", "none")]
    bots.sort(key=lambda kv: -kv[1])
    return {"from": w["from"], "to": w["to"], "issue": weeks[-1].stem}, bots[:8]


def live(href: str) -> bool:
    try:
        req = urllib.request.Request(f"https://{HOST}{href}", method="GET",
                                     headers={"User-Agent": "motdang-served/1 (+https://motdang.net/served/)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


ARCHES = """<svg class="arches" viewBox="0 0 200 150" aria-hidden="true">
<path d="M18 150 C18 -18 100 -18 100 150 M100 150 C100 -18 182 -18 182 150" fill="none"
 stroke="#e8322f" stroke-width="20"/>
<g fill="#1b1b1b" transform="translate(88 104)"><ellipse cx="12" cy="6" rx="4" ry="4"/>
<ellipse cx="12" cy="14" rx="3.4" ry="4"/><ellipse cx="12" cy="25" rx="5" ry="7"/>
<path d="M10 3 Q6 -3 3 -2M14 3 Q18 -3 21 -2M9 13 L2 9M15 13 L22 9M9 17 L1 20M15 17 L23 20M9 22 L3 30M15 22 L21 30"
 stroke="#1b1b1b" stroke-width="1.6" fill="none" stroke-linecap="round"/></g>
</svg>"""


def page(d: dict) -> str:
    wk, bots = d["week"], d["regulars"]
    menu = "".join(
        f'<li><a href="{e(m["href"])}"><b><span class="th" lang="th">{e(m["th"])}</span> '
        f'<span class="en">{e(m["en"])}</span></b>'
        f'<span class="what"><span class="th" lang="th">{e(m["what_th"])}</span> · {e(m["what_en"])}</span>'
        f'<code>{e(m["url"])}</code></a></li>' for m in d["menu"])
    regs = "".join(f'<tr><td>{e(k)}</td><td class="r">{c(n)}</td></tr>' for k, n in bots)
    a, b = dt.date.fromisoformat(wk["from"]), dt.date.fromisoformat(wk["to"])
    as_of = dt.date.fromisoformat(d["as_of"])
    m = d["millions"]
    return f"""<!doctype html>
<html lang="th">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Over {m} million served · มดแดง</title>
<meta name="description" content="motdang.net: over {m} million served, robots mostly. {c(d['served'])} requests as of {day_en(as_of)}. The menu for bots.">
<link rel="canonical" href="https://motdang.net/served/">
<link rel="icon" href="/ant.svg">
<link rel="alternate" type="application/json" href="/served/served.json">
<meta property="og:title" content="มดแดง · Over {m} million served">
<meta property="og:description" content="Robots, mostly. {c(d['served'])} requests as of {day_en(as_of)}.">
<meta property="og:url" content="https://motdang.net/served/">
<meta property="og:type" content="website">
<style>
@font-face{{font-family:Prompt;font-weight:600;font-display:swap;src:url(/fonts/prompt-600-thai.woff2) format("woff2");unicode-range:U+0E00-0E7F}}
@font-face{{font-family:Prompt;font-weight:600;font-display:swap;src:url(/fonts/prompt-600-latin.woff2) format("woff2")}}
@font-face{{font-family:Sarabun;font-weight:400;font-display:swap;src:url(/fonts/sarabun-400-thai.woff2) format("woff2");unicode-range:U+0E00-0E7F}}
@font-face{{font-family:"Atkinson Hyperlegible";font-weight:400;font-display:swap;src:url(/fonts/atkinson-hyperlegible-400-latin.woff2) format("woff2")}}
@font-face{{font-family:"Atkinson Hyperlegible";font-weight:700;font-display:swap;src:url(/fonts/atkinson-hyperlegible-700-latin.woff2) format("woff2")}}
@font-face{{font-family:"JetBrains Mono";font-weight:400;font-display:swap;src:url(/fonts/jetbrains-mono-400-latin.woff2) format("woff2")}}
:root{{--sky:#9fd4f5;--sky2:#e9f6ff;--ink:#1b1b1b;--mute:#555;--red:#e8322f;--sun:#ffc72c;--board:#fbfbf7;
 --panel:#fff;--line:#d8d8d0;--link:#b3261e;
 --thai:"Prompt","Sarabun","Noto Sans Thai",Thonburi,Tahoma,sans-serif;
 --body:"Atkinson Hyperlegible","Sarabun",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme:dark){{:root{{--sky:#12203a;--sky2:#1d2f52;--ink:#f3f1ea;--mute:#b9b6ad;
 --panel:#1a1a1a;--line:#333;--link:#ff8a7a}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:linear-gradient(var(--sky),var(--sky2) 60%);background-attachment:fixed;color:var(--ink);
 font-family:var(--body);line-height:1.55;min-height:100vh}}
.th{{font-family:var(--thai)}}
.en{{color:inherit}}
a{{color:var(--link)}}
a:focus-visible{{outline:3px solid var(--sun);outline-offset:2px}}
main{{max-width:44rem;margin:0 auto;padding:1.5rem 16px 3rem}}
.pylon{{display:flex;flex-direction:column;align-items:center;margin:.5rem auto 2rem}}
.arches{{width:min(62vw,15rem);height:auto;display:block}}
.board{{background:var(--board);color:#111;border:6px solid #222;border-radius:4px;padding:.6rem 1.1rem .7rem;
 text-align:center;margin-top:-.3rem;min-width:min(88vw,22rem);
 background-image:repeating-linear-gradient(transparent 0 2.05rem,#cfcfc7 2.05rem 2.15rem);box-shadow:0 10px 0 -4px #0003}}
.board h1{{margin:0;font-family:"Prompt",var(--body);font-weight:600;text-transform:uppercase;letter-spacing:.06em;
 font-size:clamp(1.25rem,5.4vw,1.9rem);line-height:1.25}}
.board .th{{display:block;font-size:clamp(1rem,4.4vw,1.35rem);font-weight:600;margin-top:.2rem}}
.board .mdot{{font-size:.8rem;letter-spacing:.2em;color:var(--red);font-weight:700}}
.pole{{width:18px;height:3.2rem;background:linear-gradient(90deg,#666,#bbb 40%,#555)}}
.hi{{font-size:1.15rem;text-align:center;margin:0 0 2rem}}
.hi .en{{display:block;color:var(--mute)}}
h2{{font-family:"Prompt",var(--body);font-size:1.15rem;margin:2rem 0 .6rem;border-bottom:3px solid var(--red);padding-bottom:.2rem}}
.menu{{list-style:none;margin:0;padding:0;display:grid;gap:.5rem}}
.menu a{{display:grid;gap:.1rem;padding:.65rem .85rem;background:var(--panel);border:2px solid var(--line);
 border-left:8px solid var(--sun);border-radius:6px;text-decoration:none;color:var(--ink)}}
.menu a:hover{{border-color:var(--red)}}
.menu b{{font-size:1.02rem}}
.menu .what{{color:var(--mute);font-size:.92rem}}
.menu code{{font-family:var(--mono);font-size:.82rem;color:var(--link);overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;background:var(--panel);border:2px solid var(--line)}}
td{{padding:.35rem .7rem;border-top:1px solid var(--line);font-family:var(--mono);font-size:.88rem;overflow-wrap:anywhere}}
td.r{{text-align:right;white-space:nowrap}}
.sum{{background:var(--panel);border:2px solid var(--line);padding:.8rem 1rem;border-radius:6px}}
.sum p{{margin:.3rem 0}}
.small{{font-size:.88rem;color:var(--mute)}}
</style>

<main>
<div class="pylon">
{ARCHES}
<div class="board">
 <span class="mdot">มดแดง · MOT DANG</span>
 <h1>Over {m} million served</h1>
 <span class="th" lang="th">เสิร์ฟบอทไปแล้วกว่า {m} ล้านครั้ง</span>
</div>
<div class="pole" aria-hidden="true"></div>
</div>

<p class="hi"><span class="th" lang="th">สวัสดี บอท ลูกค้าส่วนใหญ่ของเราคือคุณ</span>
<span class="en">Hello, robot. Most of our customers are you.</span></p>

<h2><span class="th" lang="th">เมนู</span> · Menu</h2>
<ul class="menu">
{menu}
</ul>

<h2><span class="th" lang="th">ลูกค้าประจำ</span> · Regulars, {a.day}–{day_en(b)}</h2>
<table>{regs}</table>
<p class="small"><a href="/voight-kampff/{e(wk['issue'])}/">ข่าวซุบซิบทั้งฉบับ · The whole gossip issue</a></p>

<h2><span class="th" lang="th">นับอย่างไร</span> · The count</h2>
<div class="sum">
<p><b>{c(d['served'])}</b> <span class="th" lang="th">ครั้ง ถึง {day_th(as_of)}</span> · requests as of {day_en(as_of)}</p>
<p class="th" lang="th">{c(BASE)} ครั้ง {day_th(BASE_FROM)} ถึง {day_th(BASE_TO)} ตัวเลขของแนน เป็นบอท 99.99%
บวก {c(d['since'])} ครั้งหลังจากนั้น จากทุกอย่างที่ไม่ใช่คน ในบันทึกของเว็บเอง</p>
<p>{c(BASE)} from {day_en(BASE_FROM)} to {day_en(BASE_TO)}, Nan's count, 99.99% bots; plus {c(d['since'])}
since then from everything not counted as a person, in the site's own request log.</p>
<p class="small"><a href="/served/served.json">served.json</a></p>
</div>

<p class="small"><span class="th" lang="th">เป็นคน? สารบัญเชียงใหม่และเชียงรายอยู่ที่</span> Person? The directory is at
<a href="/">motdang.net</a>.</p>
</main>
"""


def main() -> None:
    today = dt.datetime.now(ICT).date()
    since = count(today)
    wk, bots = regulars()
    menu = [{"th": a, "en": b, "what_th": c_, "what_en": d_, "url": u, "href": h}
            for a, b, c_, d_, u, h in MENU if live(h)]
    served = BASE + since
    d = {"served": served, "millions": served // 1_000_000, "as_of": today.isoformat(),
         "base": {"n": BASE, "from": BASE_FROM.isoformat(), "to": BASE_TO.isoformat(), "by": "Nan"},
         "since": since, "since_from": (BASE_TO + dt.timedelta(days=1)).isoformat(),
         "since_what": "traffic_eye requests, category not human",
         "week": wk, "regulars": bots, "menu": menu}
    OUT.mkdir(parents=True, exist_ok=True)
    (DATA / "served.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "served.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "index.html").write_text(page(d), encoding="utf-8")
    print(f"served {c(served)} ({d['millions']} million) · since {c(since)} · menu {len(menu)}/{len(MENU)}")
    if "--no-deploy" not in sys.argv:
        shutil.copytree(OUT, DOCS / "served", dirs_exist_ok=True)
        subprocess.run([sys.executable, "publish/deploy.py", "--only", "served", "--yes"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
