#!/usr/bin/env python3
"""เรียนทำอาหารไทย — the class board, the shelf, and what to know before the pestle.

Three things a reader asks about Thai cooking classes in this town, in the
order they ask them, on one page (/cooking.html):

  1. WHICH CLASS TODAY — the weekly board: which school runs which sessions,
     on which days, from what time, for what posted price. Read from
     data/curated/cooking_classes.json, where every row names WHO stated the
     sessions (the school, on its own site, dated). A school that states
     sessions but not weekdays is shown with its times in every column, grey,
     because "weekdays not stated" is not "closed" — and the legend says so.
     A school on the shelf that states nothing still appears, below, under
     "ask first". Nothing here becomes an event: a class that runs every
     morning is a booking, not a happening, and ten daily "events" would bury
     the real ones on /events.html. The board lives here and on each
     school's own record (known_facts rows, via enrich.json).
  2. WHERE TO LEARN — the shelf: every school the catalogue holds, by kind
     (farm, home kitchen, vegan, Northern and Akha, dessert, carving, hotel,
     vocational), one line each with its reach (phone · LINE · site). The
     shelf is the list of record; this is its front porch.
  3. WHAT YOU ARE LOOKING AT — a primer for the first-timer: the market walk
     and the five tastes, galangal against ginger and the three basils, the
     mortar and why you pound, the wok and the fire, the Northern menu and
     sticky rice, เจ against มังสวิรัติ against วีแกน, what a class costs and who
     takes the commission, twenty words, and what the paper on the wall
     says. Written in the house voice: what a person sees from the chopping
     board, *Tradition holds—* where a claim is the tradition's and not a
     document's, and no sorting of schools into tourist and real — a kitchen
     is a kitchen, the menu is the menu.

The joins outward are stated from THIS side: what wichaa's roots page is to
a person who has just learned that กินข้าว means to eat anything at all, and
what /taste.html is to somebody who wants to eat tonight what they cooked
this morning.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
muay thai layer. Emits cooking.html + cooking.css, copies the board to
docs/data/cooking_classes.json; prints the counts.
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOARD = ROOT / "data" / "curated" / "cooking_classes.json"

DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
DAY_TH = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
DAY_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_TH_LONG = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
DAY_EN_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

CSS = """
.ck-intro{font-size:1.02rem;max-width:46rem}
.ck-today{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07);font-size:1.02rem}
.ck-today b{display:block;margin-bottom:.15rem}
.ck-wrap{overflow-x:auto}
.ck-board{width:100%;border-collapse:collapse;margin:.6rem 0 .4rem;font-size:.9rem;min-width:40rem}
.ck-board th,.ck-board td{padding:.4rem .3rem;border-bottom:1px solid rgba(0,0,0,.08);
  text-align:center;vertical-align:top}
.ck-board th:first-child,.ck-board td:first-child{text-align:left}
.ck-board td.on{font-weight:600;color:var(--ant-dark)}
.ck-board td.unk{color:var(--mute)}
.ck-board td.off{color:var(--mute)}
.ck-board td.today,.ck-board th.today{background:var(--soft)}
.ck-board th.today{border-bottom:2px solid var(--ant)}
.ck-board .venue a{text-decoration:none;color:inherit}
.ck-board .venue a:hover{text-decoration:underline}
.ck-board .venue small{display:block;color:var(--mute);font-weight:400;font-size:.78rem}
.ck-board td small{display:block;font-size:.74rem;font-weight:400;color:var(--mute)}
.ck-legend{font-size:.82rem;color:var(--mute);margin:0 0 1rem}
.ck-venues{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));
  margin:.6rem 0 1.2rem}
.ck-venue{border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:.75rem .85rem;background:#fff}
.ck-venue h3{margin:0 0 .3rem;font-size:1.05rem}
.ck-venue h3 a{text-decoration:none;color:inherit}
.ck-venue h3 a:hover{text-decoration:underline}
.ck-venue p{margin:.25rem 0;font-size:.92rem}
.ck-venue .src{font-size:.8rem;color:var(--mute)}
.ck-venue .draft{font-size:.8rem;color:var(--mute)}
.ck-venue .addr{color:var(--mute)}
.ck-venue .kind{display:inline-block;font-size:.74rem;padding:.05rem .45rem;border-radius:.6rem;
  background:var(--soft);color:var(--mute);margin-left:.3rem;vertical-align:middle}
.ck-venue ul.sess{margin:.2rem 0 .3rem 1rem;padding:0;font-size:.9rem}
.ck-venue ul.sess li{margin:.1rem 0}
.ck-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));margin:.6rem 0 1.2rem}
.ck-card{border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:.75rem .9rem;background:#fff}
.ck-card h3{margin:0 0 .35rem;font-size:1.05rem}
.ck-card p{margin:.3rem 0;font-size:.93rem;line-height:1.55}
.ck-card .say{font-size:.86rem;color:var(--mute)}
.ck-words{columns:2;column-gap:1.5rem;margin:.4rem 0 1rem;font-size:.95rem}
.ck-words li{break-inside:avoid;margin:.15rem 0}
@media (max-width:40rem){.ck-words{columns:1}}
.ck-schools{list-style:none;padding:0;margin:.4rem 0 1rem;columns:2;column-gap:1.5rem}
.ck-schools li{break-inside:avoid;margin:.2rem 0;font-size:.95rem}
@media (max-width:40rem){.ck-schools{columns:1}}
.ck-schools .reach{color:var(--mute);font-size:.85rem}
.ck-schools .onboard{font-size:.8rem;color:var(--ant-dark)}
.ck-shelf{margin:.4rem 0 1rem}
.ck-joins{margin:.6rem 0 1.2rem;padding:.8rem .9rem;border-radius:.8rem;background:var(--soft)}
.ck-joins p{margin:.3rem 0;font-size:.93rem}
.ck-unc{font-size:.92rem}
.ck-unc li{margin:.25rem 0}
.ck-note{font-size:.86rem;color:var(--mute)}
"""


def load_board():
    return json.loads(BOARD.read_text())


def _cell_text(sessions, bi_text):
    """What fits in a board cell: the start times the school states, sorted
    and de-duplicated ("09:00 · 15:30"), or — when no session carries a time —
    a short word that says a class exists and the time does not. The card
    under the board carries the labels; the cell carries only the clock."""
    starts = sorted({s["start"] for s in sessions if s.get("start")})
    if starts:
        return " · ".join(starts)
    return bi_text("มีคลาส เวลาไม่ระบุ", "class, time not stated")


def _prices_line(v, bi):
    tk = v.get("prices_thb")
    if not tk:
        return ""
    lab = {"half": ("ครึ่งเมนู", "half"), "full": ("เต็มวัน", "full day"),
           "morning": ("เช้า", "morning"), "afternoon": ("บ่าย", "afternoon"),
           "evening": ("เย็น", "evening"), "oldcity": ("เมืองเก่า", "old city"),
           "farm": ("ฟาร์ม", "farm"), "carving": ("แกะสลัก", "carving"),
           "standard": ("ปกติ", "standard"), "aircon": ("ห้องแอร์", "air-con room"),
           "group": ("กลุ่ม", "group"), "private": ("ส่วนตัว", "private"),
           "kids": ("เด็ก", "kids"), "from": ("เริ่ม", "from")}
    parts = []
    for k, n in tk.items():
        th, en = lab.get(k, (k, k))
        parts.append(f"{bi(th, en)} {n:,}")
    s = " · ".join(parts) + " " + bi("บาท/คน", "baht per person")
    via = v.get("price_via") or ""
    draft = ("" if v.get("_pricesVerified") else
             f' <span class="draft">({bi("ราคาที่ประกาศ — ยังไม่ได้เทียบกับป้ายหน้าโรงเรียน", "as posted — not yet checked against the board at the school")}'
             + (f" · {via}" if via else "") + ")</span>")
    return f'<p><b>{bi("ค่าเรียน", "Price")}:</b> {s}{draft}</p>'


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS, BUILD_DATE = g["BASE"], g["DOCS"], g["BUILD_DATE"]
    share_block, channels = g["share_block"], g["channels"]
    PROVINCES, CATS = g["PROVINCES"], g["CATS"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    board = load_board()
    (DOCS / "cooking.css").write_text(CSS)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "cooking_classes.json").write_text(json.dumps(board, ensure_ascii=False, indent=1))

    by_id, prov_of = {}, {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]

    def href(r):
        return f'{prov_of[r["id"]]}/p/{place_slug(r)}.html'

    # ---- the board --------------------------------------------------------
    schools = board.get("schools", [])
    head = "".join(f'<th data-day="{i}">{bi(DAY_TH[i], DAY_EN[i])}</th>' for i in range(7))
    rows, today = [], {i: [] for i in range(7)}
    n_unk = 0
    for v in schools:
        r = by_id.get(v["place"]) if v.get("place") else None
        nm = name_bi(r) if r else bi(v.get("name_th", ""), v.get("name_en", ""))
        link = f'<a href="{href(r)}">{nm}</a>' if r else nm
        sess = [s for s in (v.get("sessions") or []) if s.get("key") != "open"]
        cell_txt = _cell_text(sess, bi_text) if sess else bi_text("เปิด", "open") + " " + (v.get("sessions") or [{}])[0].get("start", "")
        stated = v.get("days")
        cells = []
        if stated:
            for i, code in enumerate(DAYS):
                if code in stated:
                    cells.append(f'<td data-day="{i}" class="on">{esc(cell_txt)}</td>')
                    today[i].append((v, r))
                else:
                    cells.append(f'<td data-day="{i}" class="off" title="{att(bi_text("โรงเรียนบอกว่าไม่มีคลาสวันนี้", "the school states no class this day"))}">—</td>')
        else:
            n_unk += 1
            for i in range(7):
                cells.append(f'<td data-day="{i}" class="unk" title="{att(bi_text("โรงเรียนไม่ได้ระบุวัน — ถามก่อน", "weekday not stated — ask first"))}">{esc(cell_txt)}</td>')
        sub = ""
        if not stated:
            sub = "<small>" + bi("ไม่ระบุวัน — ถามก่อนไป", "weekdays not stated — ask first") + "</small>"
        elif v.get("stated_by", "").startswith("venue (") and "times" in v.get("stated_by", ""):
            sub = "<small>" + bi("วันบอกเอง เวลาไม่ระบุ", "days stated, times not") + "</small>"
        rows.append(f'<tr><td class="venue">{link}{sub}</td>{"".join(cells)}</tr>')
    board_html = (f'<div class="ck-wrap"><table class="ck-board"><thead><tr><th>{bi("โรงเรียน", "School")}</th>{head}</tr></thead>'
                  f'<tbody>{"".join(rows)}</tbody></table></div>'
                  f'<p class="ck-legend">{bi("ตัวหนา = โรงเรียนบอกเองว่าวันนี้มีคลาส · ตัวเทา = โรงเรียนบอกรอบเรียนแต่ไม่ระบุวัน (ไม่ได้แปลว่าปิด — ถามก่อน) · — = โรงเรียนบอกว่าวันนี้ไม่มี · เวลาคือเวลาเริ่มที่โรงเรียนบอก", "bold = the school states a class this day · grey = the school states sessions but not weekdays (not closed — ask first) · — = the school states no class this day · times are the start the school states")}'
                  f' · {bi("กระดานตรวจล่าสุด", "board last checked")} {esc(board.get("verified_on", ""))}</p>')

    # Today line: one sentence per weekday, swapped in by the browser for the
    # reader's own day (Asia/Bangkok); the page as built names the build day.
    def today_sentence(i):
        hits = today[i]
        tail_th = f" · อีก {n_unk} โรงเรียนบอกรอบเรียนแต่ไม่ระบุวัน — โทรหรือไลน์ถาม" if n_unk else ""
        tail_en = f" · {n_unk} more state sessions but not weekdays — call or LINE" if n_unk else ""
        if not hits:
            return bi_text(f"วัน{DAY_TH_LONG[i]} — ไม่มีโรงเรียนที่ระบุว่าวันนี้มีคลาส{tail_th}",
                           f"{DAY_EN_LONG[i]} — no school states a class for this day{tail_en}")
        def starts(v):
            ss = sorted({s["start"] for s in (v.get("sessions") or []) if s.get("start") and s.get("key") != "open"})
            return " · ".join(ss)
        names_th = " · ".join(f'{(v.get("name_en") or v.get("name_th"))} {starts(v)}'.strip() for v, _ in hits)
        names_en = " · ".join(f'{v.get("name_en")} {starts(v)}'.strip() for v, _ in hits)
        return bi_text(f"วัน{DAY_TH_LONG[i]}: {names_th}{tail_th}", f"{DAY_EN_LONG[i]}: {names_en}{tail_en}")
    built_i = datetime.date.fromisoformat(BUILD_DATE).weekday()
    data_attrs = " ".join(f'data-{i}="{att(today_sentence(i))}"' for i in range(7))
    today_html = (f'<div class="ck-today"><b>🍳 {bi("วันนี้เรียนที่ไหนได้", "Which class today")}</b>'
                  f'<span id="ck-today" {data_attrs}>{esc(today_sentence(built_i))}</span>'
                  f'<div class="ck-note">{bi("โรงเรียนบอกรอบเรียนของตัวเอง มดแดงแค่จดไว้ — จองล่วงหน้าสักวัน ส่วนใหญ่มารับถึงที่พัก", "Each school states its own sessions; the ants only write them down — book a day ahead, most will pick you up at your accommodation")}</div></div>')
    today_js = ("<script>(function(){try{var d=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Bangkok'})).getDay();"
                "var i=(d+6)%7;document.querySelectorAll('[data-day=\"'+i+'\"]').forEach(function(c){c.classList.add('today')});"
                "var t=document.getElementById('ck-today');if(t&&t.getAttribute('data-'+i)){t.textContent=t.getAttribute('data-'+i)}}catch(e){}})();</script>")

    # ---- school cards -----------------------------------------------------
    kind_lab = {}
    for ch in (CATS.get("cooking") or {}).get("children", []):
        kind_lab[ch["key"]] = (ch["th"], ch["en"])
    cards = []
    for v in schools:
        r = by_id.get(v["place"]) if v.get("place") else None
        nm = name_bi(r) if r else bi(v.get("name_th", ""), v.get("name_en", ""))
        kind = v.get("kind")
        chip = (f'<span class="kind">{bi(*kind_lab[kind])}</span>' if kind in kind_lab else "")
        title = (f'<h3><a href="{href(r)}">{nm}</a>{chip}</h3>' if r else f"<h3>{nm}{chip}</h3>")
        addr = f'<p class="addr">📮 {esc(r.get("address"))}</p>' if r and r.get("address") else ""
        stated = f'<p>{bi(v.get("stated_th") or "", v.get("stated_en") or "")}</p>'
        sess_items = []
        for s in v.get("sessions") or []:
            t = ""
            if s.get("start") and s.get("end"):
                t = f' {s["start"]}–{s["end"]}'
            elif s.get("start"):
                t = f' {s["start"]}'
            note = ""
            if s.get("note_th") or s.get("note_en"):
                note = f' <span class="src">({bi(s.get("note_th") or "", s.get("note_en") or "")})</span>'
            sess_items.append(f'<li>{bi(s.get("th") or s.get("key"), s.get("en") or s.get("key"))}{esc(t)}{note}</li>')
        sess_html = f'<ul class="sess">{"".join(sess_items)}</ul>' if sess_items else ""
        pick = (f'<p>🚐 {bi(v.get("pickup_th") or "", v.get("pickup_en") or "")}</p>'
                if (v.get("pickup_th") or v.get("pickup_en")) else "")
        menu = (f'<p>🧺 {bi(v.get("menu_th") or "", v.get("menu_en") or "")}</p>'
                if (v.get("menu_th") or v.get("menu_en")) else "")
        book = (f'<p>{bi("จอง-ถาม", "Book / ask")}: {bi(v.get("book_th") or "", v.get("book_en") or "")}</p>'
                if (v.get("book_th") or v.get("book_en")) else "")
        maybe = ""
        if not r and v.get("maybe_place"):
            cand = by_id.get(v["maybe_place"])
            cand_link = (f'<a href="{href(cand)}">{name_bi(cand)}</a>' if cand else esc(v["maybe_place"]))
            maybe = (f'<p class="src">{bi("ยังไม่ผูกกับระเบียนในสารบัญ — ตัวเลือก", "Not yet tied to a directory record — candidate")}: {cand_link}. '
                     f'{esc(v.get("maybe_note") or "")}</p>')
        src = (f'<p class="src">{bi("ที่มา", "Source")}: <a href="{att(v["source"])}" rel="noopener nofollow">'
               f'{esc(v["source"].replace("https://", "").replace("http://", "").rstrip("/"))}</a> · '
               f'{bi("ดูเมื่อ", "seen")} {esc(v.get("fetched", ""))}</p>') if v.get("source") else ""
        cards.append(f'<div class="ck-venue">{title}{addr}{stated}{sess_html}{_prices_line(v, bi)}{pick}{menu}{book}{maybe}{src}</div>')
    venues_html = f'<div class="ck-venues">{"".join(cards)}</div>'

    # Dead or unreadable sites, named and dated, never linked.
    links = board.get("link_notes") or []
    link_html = ""
    if links:
        items = []
        for L in links:
            r = by_id.get(L.get("place"))
            nm = (f'<a href="{href(r)}">{name_bi(r)}</a>' if r else esc(L.get("school", "")))
            items.append(f'<li>{nm} — {bi(L.get("verdict_th", ""), L.get("verdict_en", ""))}</li>')
        link_html = (f'<h3>{bi("เว็บที่อ่านไม่ได้วันนี้", "Sites that could not be read")}</h3>'
                     f'<p class="ck-note">{bi("โรงเรียนจริง เว็บของตัวเองตอบไม่ได้ในวันที่ตรวจ — อยู่บนชั้น ไม่อยู่บนกระดาน จนกว่าจะอ่านคำของโรงเรียนได้", "Real schools whose own sites would not answer on the day checked — on the shelf, not on the board, until the school’s own word can be read")}</p>'
                     f'<ul class="ck-unc">{"".join(items)}</ul>')
    unc = board.get("unconfirmed") or []
    unc_html = ""
    if unc:
        items = "".join(
            f'<li><b>{bi(u.get("name_th", ""), u.get("name_en", ""))}</b> — {bi(u.get("note_th", ""), u.get("note_en", ""))}</li>'
            for u in unc)
        unc_html = (f'<h3>{bi("ชื่อที่ยังไม่แน่ใจ", "Names not yet confirmed")}</h3>'
                    f'<p class="ck-note">{bi("ชื่อที่คนเรียนรู้จัก แต่ไม่มีเว็บของตัวเองที่อ่านได้ หรือป้ายบอกไม่พอ — ไม่เข้าสารบัญจนกว่าจะมีคนไปยืนหน้าประตู", "Names learners know, with no readable site of their own or a sign that says too little — not in the directory until someone stands at the door")}</p>'
                    f'<ul class="ck-unc">{items}</ul>')
    cr = board.get("chiang_rai") or {}
    cr_html = f'<p class="ck-note">🌱 {bi(cr.get("note_th", ""), cr.get("note_en", ""))}</p>' if cr else ""

    # ---- the shelf: every school, by kind, with reach ----------------------
    on_board = {v["place"] for v in schools if v.get("place")}

    def on_shelf(r, sub=None):
        return "cooking" in (r.get("cat") or []) and (sub is None or sub in (r.get("sub") or []))
    shelf_links, school_rows, n_all = [], [], 0
    cdef = CATS.get("cooking") or {}
    for p in PROVINCES:
        recs = [r for r in data[p["key"]] if on_shelf(r)]
        if not recs:
            continue
        n_all += len(recs)
        subs = []
        for ch in cdef.get("children", []):
            n = sum(1 for r in recs if on_shelf(r, (ch.get("match") or {}).get("sub")))
            if n:
                subs.append(f'<a href="{p["key"]}/cooking/{ch["key"]}/index.html">{bi(ch["th"], ch["en"])}</a> '
                            f'<span class="count">({n})</span>')
        shelf_links.append(f'<li><b><a href="{p["key"]}/cooking/index.html">{bi(p["th"], p["en"])}</a></b> '
                           f'<span class="count">({len(recs)})</span> — {" · ".join(subs)}</li>')
        for r in sorted(recs, key=lambda x: g["name_of"](x).lower()):
            live, _ = channels(r)
            kinds = [c.get("kind") for c in live] if live and isinstance(live[0], dict) else []
            marks = []
            if r.get("phone") or "phone" in kinds:
                marks.append("☎")
            if "line" in kinds or (r.get("attrs") or {}).get("lineId"):
                marks.append("LINE")
            if r.get("website") or "website" in kinds:
                marks.append("🌐")
            reach = f' <span class="reach">{" ".join(marks)}</span>' if marks else \
                f' <span class="reach">{bi("ยังไม่มีเบอร์", "no contact yet")}</span>'
            ob = f' <span class="onboard">📋</span>' if r["id"] in on_board else ""
            school_rows.append(f'<li><a href="{href(r)}">{name_bi(r)}</a>{reach}{ob}</li>')
    shelf_note = bi("แผนที่ของชั้นอยู่บนหน้าชั้นแต่ละจังหวัด · โรงเรียนที่ยังไม่อยู่ในสารบัญ — บอกมดได้ที่",
                    "The shelf map is on each province’s shelf page · a school not here yet —")
    shelf_html = (f'<ul class="cats ck-shelf">{"".join(shelf_links)}</ul>'
                  f'<p class="ck-note">{shelf_note} '
                  f'<a href="add.html">{bi("เพิ่มข้อมูล", "add a place")}</a></p>')
    schools_html = (f'<ul class="ck-schools">{"".join(school_rows)}</ul>' if school_rows else
                    f'<p class="ck-note">{bi("ยังไม่มีโรงเรียนในสารบัญ", "no schools in the directory yet")}</p>')

    # ---- the primer --------------------------------------------------------
    P = []

    def card(h_th, h_en, *paras):
        body = "".join(f"<p>{x}</p>" for x in paras)
        P.append(f'<div class="ck-card"><h3>{bi(h_th, h_en)}</h3>{body}</div>')

    card("กาด — เดินตลาดก่อน แล้วค่อยเข้าครัว", "The market first — then the kitchen",
         bi("เกือบทุกคลาสเริ่มที่ตลาดสด (คนเมืองเรียก กาด, kàat) ครูจะหยิบของให้ดูทีละอย่าง: ข่า ตะไคร้ ใบมะกรูด พริก กะปิ น้ำปลา น้ำตาลปี๊บ มะนาว — นั่นคือรสทั้งห้าของครัวไทย เค็ม (น้ำปลา กะปิ) หวาน (น้ำตาลปี๊บ) เปรี้ยว (มะนาว มะขาม) เผ็ด (พริก) ขม (สมุนไพร ผักพื้นบ้าน) จานไทยคือการจูนห้ารสนี้ให้พอดี ไม่ใช่สูตรตายตัว",
            "Almost every class begins at a fresh market (in the north, a kàat, กาด). The teacher picks things up one at a time: galangal, lemongrass, kaffir lime leaf, chillies, shrimp paste, fish sauce, palm sugar, lime — the five tastes of a Thai kitchen. Salty (fish sauce, shrimp paste), sweet (palm sugar), sour (lime, tamarind), hot (chilli), bitter (herbs and the wild greens). A Thai dish is those five tuned against each other, not a fixed recipe."),
         bi("ถ้าครูชิมแล้วเติมน้ำปลาอีกช้อน นั่นคือบทเรียน — จดไว้ว่าทำไม ไม่ใช่จดกี่ช้อน",
            "When the teacher tastes and adds one more spoon of fish sauce, that is the lesson — write down why, not how many spoons."))
    card("ข่าไม่ใช่ขิง — ของที่หน้าตาคล้ายแต่ไม่เหมือน", "Galangal is not ginger — the look-alikes",
         bi("ข่า (khàa) เผ็ดซ่าเหมือนสน ใช้ในต้มข่า ต้มยำ และพริกแกง · ขิง (khǐng) หวานร้อน ใช้ผัดและของหวาน — สองอย่างนี้แทนกันไม่ได้ · มะกรูด (má-krùut) ใช้ใบฉีกและผิวขูด ไม่ใช้น้ำ ส่วน มะนาว (má-naao) คือมะนาวที่บีบ · โหระพาสามชนิด: กะเพรา (kà-phrao) ใบขนเผ็ดร้อน สำหรับผัดกะเพรา · โหระพา (hǒo-rá-phaa) หอมชะเอม ใส่แกงเขียวหวาน · แมงลัก (maeng-lák) กลิ่นมะนาว ใส่ขนมจีนน้ำยา",
            "Galangal (ข่า, khàa) is piny and sharp — tom kha, tom yam, every curry paste; ginger (ขิง, khǐng) is sweet-hot — stir-fries and sweets; they do not swap. Kaffir lime (มะกรูด, má-krùut) gives its torn leaf and grated zest, not its juice; the lime you squeeze is มะนาว (má-naao). Three basils: holy basil (กะเพรา, kà-phrao) — furred, peppery, for phat kaphrao; Thai sweet basil (โหระพา, hǒo-rá-phaa) — anise-scented, into green curry; lemon basil (แมงลัก, maeng-lák) — into khanom chin nam ya."),
         bi("ตะไคร้ (tà-khrái) ใช้แต่โคนขาว · ขมิ้น (khà-mîn) ทำให้แกงเหนือเหลือง · รากผักชี (râak phàk-chii) คือกลิ่นลับในพริกแกงและน้ำจิ้ม — ของสามอย่างที่คนเรียนมักไม่เคยเห็นทั้งต้น",
            "Lemongrass (ตะไคร้, tà-khrái): only the pale base. Turmeric (ขมิ้น, khà-mîn) is what makes a Northern curry yellow. Coriander root (รากผักชี, râak phàk-chii) is the hidden scent in pastes and dipping sauces — three things a learner has usually not seen whole."))
    card("ครกกับสาก", "The mortar and pestle",
         bi("พริกแกง (phrík kaeng) ทุกชนิดเริ่มจากครกหิน (khrók hǐn) กับสาก (sàak): พริกแห้งแช่น้ำ ข่า ตะไคร้ ผิวมะกรูด รากผักชี หอม กระเทียม กะปิ ตำจากของแข็งไปหาของนิ่ม ใส่เกลือเม็ดช่วยบด ตำจนเนียนเป็นเนื้อเดียว — สิบถึงสิบห้านาทีต่อครก คลาสดี ๆ ให้ทุกคนมีครกของตัวเอง และเสียงตำพร้อมกันทั้งห้องคือเสียงของครัวไทยจริง ๆ",
            "Every curry paste (พริกแกง, phrík kaeng) starts in a stone mortar (ครกหิน, khrók hǐn) with a pestle (สาก, sàak): soaked dried chillies, galangal, lemongrass, kaffir zest, coriander root, shallot, garlic, shrimp paste — hardest things first, a pinch of coarse salt to help the grind, pounded until it is one smooth paste. Ten to fifteen minutes a mortar. A good class gives everyone their own, and a room pounding together is the real sound of a Thai kitchen."),
         bi("ครกดิน (khrók din, ครกดินเผากับสากไม้) ใช้ตำส้มตำ — ตำเบา ๆ แค่ให้ช้ำ ไม่ใช่บด · เครื่องปั่นทำได้ แต่ได้เนื้อและกลิ่นคนละอย่าง — ครูจะบอกเองว่าทำไม",
            "The clay mortar (ครกดิน, khrók din, with a wooden pestle) is for som tam — a light bruising, not a grind. A blender works, but the texture and the smell are different things; the teacher will say why."))
    card("กระทะกับไฟ — ผัด", "The wok and the fire — stir-frying",
         bi("ผัด (phàt) คือไฟแรง กระทะร้อนจัด น้ำมันนิดหน่อย กระเทียมลงก่อน แล้วทุกอย่างตามติด ๆ ภายในสองนาที — ครูจะบอก “ใส่ ๆ ๆ” เพราะกระทะรอไม่ได้ ของทั้งหมดต้องหั่นเสร็จก่อนจุดไฟ (mise en place แบบไทย) · ข้าวผัดที่ดีมีกลิ่นไหม้นิด ๆ จากกระทะ · ผัดไทยเป็นการจูนรสเปรี้ยวหวานเค็มในน้ำซอสก่อนผัด ไม่ใช่ตอนผัด",
            "Stir-frying (ผัด, phàt) is high heat, a smoking wok, a little oil, garlic first, then everything in fast — done inside two minutes. The teacher will say “sài sài sài” (in, in, in) because the wok does not wait; everything is cut before the flame goes on. Good fried rice carries a faint scorch from the wok. Pad thai is tuned sour-sweet-salty in the sauce before it ever meets the pan, not during."),
         bi("คลาสส่วนใหญ่ใช้เตาแก๊สแรงแบบบ้านหรือร้าน ไม่ใช่เตาเหล็กร้านข้างทาง — ที่บ้านของคุณก็ทำได้ ขอแค่กระทะร้อนพอและอย่าใส่ของเยอะเกินไปในครั้งเดียว",
            "Most classes cook on ordinary strong gas rings, not a street stall's jet burner — which is the point: you can do this at home, if the pan is hot enough and you do not crowd it."))
    card("เมนูเหนือ และข้าวเหนียว", "The Northern menu, and sticky rice",
         bi("อาหารเหนือ (อาหารล้านนา, อาหารเมือง) ไม่ใช่แกงเขียวหวานกับต้มยำ: ข้าวซอย (khâao sɔɔi) เส้นในน้ำแกงกะหรี่ใส่กะทิ โรยเส้นทอด · น้ำพริกอ่อง (nám phrík òng) หมูสับมะเขือเทศ · น้ำพริกหนุ่ม (nám phrík nùm) พริกหนุ่มย่างตำ กินกับแคบหมู · ไส้อั่ว (sâi ùa) ไส้กรอกสมุนไพร · แกงฮังเล (kaeng hang-lee) แกงหมูขิงมะขาม ไม่ใส่กะทิ · ลาบคั่ว (lâap khûa) ลาบแบบเหนือใส่พริกลาบ — โรงเรียนส่วนใหญ่สอนเมนูกลาง ถามว่ามี “เมนูเหนือ” ไหม บางแห่งระบุไว้บนกระดาน",
            "Northern food (อาหารเหนือ, Lanna, khon mueang food) is not green curry and tom yam: khao soi (ข้าวซอย, khâao sɔɔi) — noodles in a coconut curry broth under a crisp nest; nam phrik ong (น้ำพริกอ่อง) — minced pork and tomato; nam phrik num (น้ำพริกหนุ่ม) — pounded roast green chilli with pork crackling; sai ua (ไส้อั่ว) — the herb sausage; kaeng hang le (แกงฮังเล) — pork, ginger and tamarind, no coconut; laap khua (ลาบคั่ว) — the Northern laap with its own spice mix. Most schools teach a central-Thai menu; ask for a “Northern menu” — some state one on the board above."),
         f'<span class="say">{bi("ตามประเพณีเล่าว่า ข้าวซอยมากับพ่อค้าจีนฮ่อมุสลิมจากยูนนาน และชื่อ ฮังเล มาจากพม่า (hin lay) — เป็นเรื่องเล่าสืบกัน ไม่ใช่เอกสาร · ภาคเหนือกินข้าวเหนียว (khâao nǐao) นึ่งในหวด ใส่กระติ๊บ (krà-típ) ปั้นด้วยมือขวาจิ้มน้ำพริก — คลาสที่สอนอาหารเหนือมักให้หัดนึ่งข้าวเหนียวด้วย", "Tradition holds that khao soi came with the Chin Haw, the Yunnanese Muslim traders, and that hang le is the Burmese hin lay — stories carried, not documents. The north eats sticky rice (ข้าวเหนียว, khâao nǐao), steamed in a cone and served in a woven kratip (กระติ๊บ), pinched with the right hand and pressed into the relish — a Northern class usually teaches the steaming too.")}</span>')
    card("เจ · มังสวิรัติ · วีแกน — สามคำที่ไม่เหมือนกัน", "เจ, มังสวิรัติ, วีแกน — three words that differ",
         bi("เจ (jee) คือแบบจีน-พุทธ: ไม่มีเนื้อ ไข่ นม และไม่มีผักฉุนห้าอย่าง (กระเทียม หอม กุยช่าย หลักเกียว ใบยาสูบ) ร้านเจติดธงเหลืองตัว 齋 · มังสวิรัติ (mang-sà-wí-rát) คือมังสวิรัติทั่วไป บางคนกินไข่-นม · วีแกน (wii-kaen) คือไม่มีของจากสัตว์เลย — น้ำปลาและกะปิคือจุดที่เมนูไทยเลี่ยงยาก โรงเรียนที่ทำได้จะบอกเองว่าใช้ซีอิ๊วหรือเกลือแทน",
            "เจ (jee) is the Chinese-Buddhist rule: no meat, egg or dairy, and none of the five pungent plants (garlic, onion, chives, Chinese leek, tobacco-leaf); a jee shop flies a yellow flag with the character 齋. มังสวิรัติ (mang-sà-wí-rát) is ordinary vegetarian, egg and dairy for some. วีแกน (wii-kaen) is nothing from an animal — fish sauce and shrimp paste are where a Thai menu has to be rewritten, and a school that can do it will say whether soy sauce or salt stands in."),
         f'<a href="festivals/kin-je.html">{bi("เทศกาลกินเจ — เก้าวันเดือนเก้าจีน (ราวกันยายน–ตุลาคม) ธงเหลืองทั้งเมือง", "The Vegetarian Festival — nine days of the ninth Chinese month, about September–October, yellow flags across town")} →</a>')
    card("เงิน — ค่าเรียน รถรับ ค่านายหน้า", "Money — fee, van, commission",
         bi("ราคาที่โรงเรียนในเมืองประกาศเอง (ดูกระดาน) อยู่ราว 1,000–1,500 บาทต่อคนสำหรับครึ่งวันหรือเต็มวัน รวมรถรับ ตลาด วัตถุดิบ สูตรกลับบ้าน และอาหารที่ทำ · คลาสในโรงแรมคิดเป็นพันหลายพันบวกค่าบริการ · ทุกตัวเลขบนกระดานมีที่มาและวันที่ และยังไม่มีตัวไหนเทียบกับป้ายหน้าประตู",
            "What the town's schools post themselves (see the board) runs about 1,000–1,500 baht a person for a half or full day, with the van, the market, the ingredients, the recipes and the meal you made; hotel studios charge several thousand plus service. Every number on the board carries its source and date, and none has yet been checked against the sign at the school's entrance."),
         bi("จองผ่านที่พัก เอเจนซี่ หรือแอปจอง มักมีค่านายหน้าอยู่ในราคา — ไม่ผิดอะไร แค่รู้ไว้ ราคาที่เว็บหรือ LINE ของโรงเรียนคือราคาของโรงเรียน เทียบได้ · ถามสามอย่างก่อนโอน: รวมรถรับไหม รัศมีกี่กิโล และยกเลิกได้ถึงเมื่อไหร่",
            "A booking through a guesthouse, an agency or a booking app usually carries a commission inside the price — nothing wrong with it, just know it; the price on the school's own site or LINE is the school's price, and it can be compared. Three questions before you transfer: is the pickup included, within what radius, and until when can I cancel?"))
    card("คำที่จะได้ยิน", "Words you will hear",
         '<ul class="ck-words">'
         + "".join(f"<li>{bi(th, en)}</li>" for th, en in [
             ("ผัด (phàt) — ผัดในกระทะ", "phat (ผัด, phàt) — stir-fry"),
             ("ต้ม (tôm) — ต้ม", "tom (ต้ม, tôm) — boil; a soup"),
             ("แกง (kaeng) — แกง/ซุปข้น", "kaeng (แกง) — curry, or a soupy dish"),
             ("ยำ (yam) — คลุกรสเปรี้ยวเผ็ด", "yam (ยำ) — the sour-hot salad"),
             ("ตำ (tam) — ตำในครก", "tam (ตำ) — pound in the mortar"),
             ("นึ่ง (nʉ̂ng) — นึ่ง", "nueng (นึ่ง, nʉ̂ng) — steam"),
             ("ทอด (thɔ̂ɔt) — ทอด", "thot (ทอด, thɔ̂ɔt) — deep-fry"),
             ("ย่าง (yâang) — ย่าง", "yang (ย่าง, yâang) — grill"),
             ("เผ็ด (phèt) · ไม่เผ็ด · เผ็ดน้อย", "phet (เผ็ด, phèt) — hot · mâi phèt — not hot · phèt nɔ́ɔi — a little"),
             ("หวาน (wǎan) · เปรี้ยว (prîao) · เค็ม (khem) · ขม (khǒm)", "waan — sweet · priao — sour · khem — salty · khom — bitter"),
             ("อร่อย (à-rɔ̀i) — อร่อย", "aroi (อร่อย, à-rɔ̀i) — delicious"),
             ("พริกแกง (phrík kaeng) — เครื่องแกง", "phrik kaeng (พริกแกง) — curry paste"),
             ("กะทิ (kà-thí) — น้ำกะทิ", "kathi (กะทิ, kà-thí) — coconut cream"),
             ("น้ำปลา (nám plaa) · กะปิ (kà-pì)", "nam pla (น้ำปลา) — fish sauce · kapi (กะปิ) — shrimp paste"),
             ("ครก (khrók) · สาก (sàak) · กระทะ (krà-thá) · ตะหลิว (tà-lǐu)", "khrok — mortar · saak — pestle · kratha — wok · taliu — spatula"),
             ("ข้าวสวย (khâao sǔai) · ข้าวเหนียว (khâao nǐao)", "khao suai — steamed rice · khao niao — sticky rice"),
             ("กินข้าว (kin khâao) — กินอาหาร", "kin khao (กินข้าว) — to eat, whatever is eaten"),
         ]) + "</ul>",
         f'<span class="say">{bi("คำว่า ครัว (khrua) แปลว่าห้องครัว และในภาษาเมืองยังแปลว่าของ/ข้าวของ (ครัวตาน — ของที่นำไปทำบุญ) · แกง ใช้ได้ทั้งของใส่กะทิและไม่ใส่ ความหมายกว้างกว่า curry", "ครัว (khrua) is the kitchen — and in the Northern tongue also means goods, things (khrua taan, the things carried to a temple offering). แกง (kaeng) covers dishes with coconut and without; it is wider than the English curry.")}</span>')
    card("กระดาษบนผนัง", "The paper on the wall — school or tour",
         bi("โรงเรียนสอนทำอาหารที่จดทะเบียนเป็น โรงเรียนนอกระบบ กับสำนักงานคณะกรรมการส่งเสริมการศึกษาเอกชน (สช.) ตาม พ.ร.บ.โรงเรียนเอกชน พ.ศ. 2550 จะมีใบอนุญาตจัดตั้งโรงเรียนมีเลขที่ติดผนัง ออกใบประกาศที่กระทรวงรับรองได้ และคอร์สยาวของโรงเรียนแบบนี้คือทางที่วีซ่านักเรียน (ED) เดิน · คลาสที่มารับถึงที่พักและพาเดินตลาด บางแห่งจดทะเบียนเป็นธุรกิจนำเที่ยว มีเลขใบอนุญาตของ ททท. (สุวรรณีที่เชียงรายพิมพ์เลขไว้บนเว็บ) · สองกระดาษนี้ต่างกัน และไม่มีอันไหนบอกว่าครัวไหนดีกว่า — ถ้าอยากเห็น ขอดู",
            "A cooking school registered as a โรงเรียนนอกระบบ, a private non-formal school, with the Office of the Private Education Commission (สช.) under the Private School Act B.E. 2550 hangs a numbered licence on the wall, can issue a Ministry-recognised certificate, and a long course at such a school is the road an ED visa travels. A class that fetches you and walks a market is sometimes registered instead as a tour business, with a TAT licence number (Suwannee in Chiang Rai prints hers on her site). The two papers are different things, and neither says whose kitchen is better — if you want to see it, ask."),
         bi("ฝั่งอาชีพ: กรมพัฒนาฝีมือแรงงานมีมาตรฐานฝีมือแรงงานแห่งชาติ สาขาผู้ประกอบอาหารไทย ให้คนทำครัวสอบเอาใบรับรอง — สถาบันที่เชียงใหม่ (335 หมู่ 3 ถ.โชตนา แม่ริม โทร 053 121002-3) และที่เชียงรายมีสอบตามรอบ รอบนี้มีสาขาไหนบ้าง โทรถาม · ชั้น “หลักสูตรอาชีพ” บนชั้นนี้ยังว่างอยู่จริง ๆ จนกว่าสถาบันเหล่านี้จะบอกเองบนหน้าเว็บว่าสอนอาหาร",
            "On the trade side: the Department of Skill Development runs a national skill standard for ผู้ประกอบอาหารไทย, the Thai cook, that a working cook can test for; the Chiang Mai institute (335 Moo 3 Chotana Rd, Mae Rim, 053 121002-3) and the Chiang Rai one hold rounds — which trades this round, is a phone call. The “vocational” shelf here is truthfully empty until those institutions say on their own pages that they teach food."))
    primer_html = f'<div class="ck-grid">{"".join(P)}</div>'

    joins_html = (f'<div class="ck-joins"><b>{bi("ไปต่อ", "Onward")}</b>'
                  f'<p><a href="https://wichaa.net/thairoots" rel="noopener">wichaa.net/thairoots</a> — '
                  + bi("รากศัพท์ไทย: ข้าว ที่แปลว่าอาหารทั้งหมด (กินข้าว) และ กิน ที่แปลได้ถึงการกินตำแหน่ง — สำหรับคนที่เพิ่งรู้ว่าครูพูดว่า “กินข้าวกัน” ไม่ได้แปลว่ามีแต่ข้าว",
                       "Thai roots: ข้าว, rice that means all food (กินข้าว, to eat), and กิน, to eat, which also eats a bribe — for whoever just learned that “kin khao” from the teacher did not mean only rice")
                  + f'</p><p><a href="taste.html">taste.html — รสเมือง</a> — '
                  + bi("แผนที่ร้านอาหารทั้งเมืองแยกตามแนวอาหาร — กินคืนนี้ในสิ่งที่ทำเมื่อเช้า",
                       "every eating place in town on one map by cuisine — eat tonight what you cooked this morning")
                  + f'</p><p><a href="festivals/kin-je.html">festivals/kin-je.html</a> — '
                  + bi("เทศกาลกินเจ ในปฏิทินเทศกาล", "the Vegetarian Festival on the festivals calendar")
                  + f'</p><p><a href="cm/market/index.html">{bi("ชั้นตลาด", "the markets shelf")}</a> — '
                  + bi("กาดที่คลาสพาไป และกาดที่ไปเองได้ก่อนเจ็ดโมง", "the markets the classes walk, and the ones you can walk yourself before seven")
                  + "</p></div>")

    # ---- assemble ---------------------------------------------------------
    intro = bi("หน้านี้มีสามอย่าง: กระดานรอบเรียนของโรงเรียนสอนทำอาหารในเมือง (โรงเรียนบอกเอง มดจดไว้พร้อมที่มา) ชั้นโรงเรียนทุกแบบ — ในสวน ที่บ้านครู เจ-วีแกน อาหารเหนือ-อาข่า ขนมไทย แกะสลัก โรงแรม — และเรื่องที่ควรรู้ก่อนจับครก เขียนจากหน้าเขียง ไม่ได้จัดอันดับว่าครัวไหนแท้กว่ากัน ครัวก็คือครัว",
               "Three things on one page: the weekly class board for the town's cooking schools (each school states its own sessions; the ants write them down with the source), the shelf of every kind of school — farm, home kitchen, vegetarian and vegan, Northern and Akha, Thai dessert, carving, hotel — and what to know before you lift the pestle, written from the chopping board, with no ranking of kitchens into real and otherwise. A kitchen is a kitchen.")
    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "โรงเรียนสอนทำอาหารไทย เชียงใหม่-เชียงราย — Thai cooking classes, Chiang Mai and Chiang Rai",
        "url": BASE + "cooking.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "School", "name": v.get("name_en") or v.get("name_th"),
                      "alternateName": v.get("name_th"),
                      **({"url": BASE + href(by_id[v["place"]])} if v.get("place") in by_id else {}),
                      **({"url": v["source"]} if (v.get("place") not in by_id and v.get("source")) else {})}}
            for i, v in enumerate(schools)],
    }
    head = ('<link rel="stylesheet" href="cooking.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "cooking") if shelf_og else None
    body = (
        f'<h1>🍳 {bi("เรียนทำอาหารไทย — คลาสวันนี้ ทุกโรงเรียน", "Thai cooking classes — today, every school")}</h1>'
        f'<p class="ck-intro">{intro}</p>'
        f'{today_html}'
        f'<h2>{bi("กระดานรอบเรียนประจำสัปดาห์", "The weekly class board")}</h2>'
        f'{board_html}{venues_html}{link_html}{unc_html}{cr_html}'
        f'<h2>{bi("ชั้นเรียนทำอาหาร", "The cooking shelf")}</h2>'
        f'{shelf_html}'
        f'<h3>{bi("โรงเรียนทั้งหมดในสารบัญ", "Every school in the directory")} <span class="count">({len(school_rows)})</span></h3>'
        f'<p class="ck-note">{bi("เรียงตามชื่อ — ☎ LINE 🌐 คือช่องทางที่สารบัญมี · 📋 = อยู่บนกระดานด้านบน ที่เหลือยังไม่มีคำของตัวเองให้จด ถามก่อนไป · โรงเรียนไหนยังไม่มีเบอร์ ช่วยกันเติมได้", "Alphabetical — ☎ LINE 🌐 mark the channels the directory holds · 📋 = on the board above; the rest have stated nothing yet to write down, so ask first · a school with no contact can be filled in by anyone")}</p>'
        f'{schools_html}'
        f'<h2>{bi("ก่อนจับครก", "Before the mortar")}</h2>'
        f'{primer_html}{joins_html}'
        f'<p class="ck-note">{bi("ที่มาของกระดาน", "Board data")}: <a href="data/cooking_classes.json">data/cooking_classes.json</a> · '
        f'{bi("รอบเรียนและราคาอยู่บนหน้าของแต่ละโรงเรียนด้วย", "sessions and prices also sit on each school’s own page")}</p>'
        f'{share_block(BASE + "cooking.html", "เรียนทำอาหารไทย เชียงใหม่ · มดแดง", card=og)}'
        f'{today_js}')
    (DOCS / "cooking.html").write_text(page(
        "เรียนทำอาหารไทย — คลาสวันนี้ เชียงใหม่ · Thai cooking classes, Chiang Mai",
        body, depth=0, path="cooking.html",
        desc="กระดานรอบเรียนของโรงเรียนสอนทำอาหารไทยในเชียงใหม่และเชียงราย ราคาที่ประกาศ รถรับ โรงเรียนทุกแบบ — ฟาร์ม บ้านครู เจ-วีแกน อาหารเหนือ ขนมไทย แกะสลัก โรงแรม — และเรื่องที่ควรรู้ก่อนจับครก · Thai cooking classes in Chiang Mai and Chiang Rai: today's class board, posted prices, pickup, every kind of school, and what to know before the mortar",
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("เรียนทำอาหารไทย", "Thai cooking classes")}'))
    stated_days = sum(1 for v in schools if v.get("days"))
    return {"page": 1, "schools": len(schools), "days_stated": stated_days,
            "on_shelf": n_all, "listed": len(school_rows)}
