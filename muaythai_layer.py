#!/usr/bin/env python3
"""มวยไทย — the fight board, the shelf, and what to know before the pipes start.

Three things a reader asks about muay thai in this town, in the order they
ask them, on one page (/muaythai.html):

  1. WHERE TONIGHT — the weekly board: which stadium fights on which night,
     from what time, for how much. Read from data/curated/fight_nights.json,
     where every row names WHO stated the nights (the venue, or a named
     listing, dated). Nights the venue itself states become weekly events
     (`raw_events()`, merged into the harvest by build.py) so /events.html,
     the carousel, the stadium's own page band, events.ics and the JSON all
     carry them through the one path everything else takes. Nights only a
     listing reports stay on this page, labelled as reported. A venue whose
     nights nobody states still appears — under "ask before you go" — because
     silence about the weekday is not the same as no fights.
  2. WHERE TO TRAIN — the camps and gyms the catalogue holds, one line each
     with their reach (phone · LINE · site), linking to the shelf where the
     map is. The shelf is the list of record; this is its front porch.
  3. WHAT YOU ARE LOOKING AT — a primer for the first-timer: the wai khru and
     why the fight has not started yet, the mongkhon and prajiad, the four
     musicians, the five rounds, the bettors, the ticket classes, a dozen
     words, the two national days, and where the north comes in. Written in
     the house voice: what a person sees from the seat, *Tradition holds—*
     where a claim is the tradition's and not a document's, and no ranking of
     stadiums into real and touristic — a ring is a ring, the card is the card.

The joins to wichaa are stated from THIS side: what each wichaa page is to a
person who just watched a mongkhon come off a fighter's head.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
answers layer. Emits muaythai.html + muaythai.css, copies the board to
docs/data/fight_nights.json; prints the counts. raw_events(build_date) is
called by build.py at import time, before any data is loaded, and reads only
the board file.
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOARD = ROOT / "data" / "curated" / "fight_nights.json"

DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
DAY_TH = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
DAY_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_TH_LONG = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
DAY_EN_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

CSS = """
.mt-intro{font-size:1.02rem;max-width:46rem}
.mt-today{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07);font-size:1.02rem}
.mt-today b{display:block;margin-bottom:.15rem}
.mt-board{width:100%;border-collapse:collapse;margin:.6rem 0 .4rem;font-size:.95rem}
.mt-board th,.mt-board td{padding:.4rem .35rem;border-bottom:1px solid rgba(0,0,0,.08);
  text-align:center;vertical-align:top}
.mt-board th:first-child,.mt-board td:first-child{text-align:left}
.mt-board td.on{font-weight:600;color:var(--ant-dark)}
.mt-board td.rep{color:var(--mute);font-style:italic}
.mt-board td.today,.mt-board th.today{background:var(--soft)}
.mt-board th.today{border-bottom:2px solid var(--ant)}
.mt-board .venue a{text-decoration:none;color:inherit}
.mt-board .venue a:hover{text-decoration:underline}
.mt-board .venue small{display:block;color:var(--mute);font-weight:400;font-size:.8rem}
.mt-legend{font-size:.82rem;color:var(--mute);margin:0 0 1rem}
.mt-venues{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));
  margin:.6rem 0 1.2rem}
.mt-venue{border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:.75rem .85rem;background:#fff}
.mt-venue h3{margin:0 0 .3rem;font-size:1.05rem}
.mt-venue h3 a{text-decoration:none;color:inherit}
.mt-venue h3 a:hover{text-decoration:underline}
.mt-venue p{margin:.25rem 0;font-size:.92rem}
.mt-venue .src{font-size:.8rem;color:var(--mute)}
.mt-venue .draft{font-size:.8rem;color:var(--mute)}
.mt-venue .addr{color:var(--mute)}
.mt-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));margin:.6rem 0 1.2rem}
.mt-card{border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:.75rem .9rem;background:#fff}
.mt-card h3{margin:0 0 .35rem;font-size:1.05rem}
.mt-card p{margin:.3rem 0;font-size:.93rem;line-height:1.55}
.mt-card .say{font-size:.86rem;color:var(--mute)}
.mt-words{columns:2;column-gap:1.5rem;margin:.4rem 0 1rem;font-size:.95rem}
.mt-words li{break-inside:avoid;margin:.15rem 0}
@media (max-width:40rem){.mt-words{columns:1}}
.mt-camps{list-style:none;padding:0;margin:.4rem 0 1rem;columns:2;column-gap:1.5rem}
.mt-camps li{break-inside:avoid;margin:.2rem 0;font-size:.95rem}
@media (max-width:40rem){.mt-camps{columns:1}}
.mt-camps .reach{color:var(--mute);font-size:.85rem}
.mt-shelf{margin:.4rem 0 1rem}
.mt-joins{margin:.6rem 0 1.2rem;padding:.8rem .9rem;border-radius:.8rem;background:var(--soft)}
.mt-joins p{margin:.3rem 0;font-size:.93rem}
.mt-unc{font-size:.92rem}
.mt-unc li{margin:.25rem 0}
.mt-note{font-size:.86rem;color:var(--mute)}
"""


def load_board():
    return json.loads(BOARD.read_text())


def _next_on(build_date, days, start):
    """The first date on or after build_date that falls on one of `days`."""
    d0 = datetime.date.fromisoformat(build_date)
    want = {DAYS.index(x) for x in days}
    for k in range(8):
        d = d0 + datetime.timedelta(days=k)
        if d.weekday() in want:
            return d
    return d0


def raw_events(build_date):
    """Weekly fight nights as raw harvest events — only for venues whose
    nights THE VENUE ITSELF states. One event per stadium carrying a BYDAY
    list (a stadium that fights six nights a week is one event, not six);
    `weekday` stays None so build.dedupe_events leaves it whole, and
    event_vevent writes the multi-day RRULE. `venue_name` is the catalogue's
    canonical name so match_venue pins it exactly, never loosely."""
    out = []
    try:
        board = load_board()
    except (OSError, ValueError):
        return out
    for v in board.get("venues", []):
        days = v.get("days")
        if not days or v.get("stated_by", "").split()[0] != "venue":
            continue
        d = _next_on(build_date, days, v.get("start") or "21:00")
        start = f"{d.isoformat()} {v.get('start') or '21:00'}:00"
        end_t = v.get("end") or "23:30"
        end_d = d + datetime.timedelta(days=1) if end_t == "00:00" else d
        end = f"{end_d.isoformat()} {end_t}:00"
        tk = v.get("tickets_thb") or {}
        vals = [x for x in tk.values() if isinstance(x, (int, float))]
        if "from" in tk:
            cost = f"จาก {tk['from']:,} บาท · from {tk['from']:,} baht"
        elif len(vals) > 1:
            cost = f"{min(vals):,}–{max(vals):,} บาท"
        elif vals:
            cost = f"{vals[0]:,} บาท"
        else:
            cost = ""
        idx = [DAYS.index(x) for x in days]
        run = len(idx) >= 3 and idx == list(range(idx[0], idx[-1] + 1))
        day_th = f"{DAY_TH[idx[0]]}–{DAY_TH[idx[-1]]}" if run else " · ".join(DAY_TH[i] for i in idx)
        day_en = f"{DAY_EN[idx[0]]}–{DAY_EN[idx[-1]]}" if run else " · ".join(DAY_EN[i] for i in idx)
        desc = " ".join(x for x in (
            f"{v.get('stated_en') or ''} — {day_en} from {v.get('start') or '21:00'}.",
            v.get("tickets_note_en") or "",
            f"Board: {BOARD.name} (verified {board.get('verified_on', '')}).") if x)
        out.append({
            "source": "fight-nights",
            "uid": v["place"],
            "title": f"คืนชกมวย {day_th} · Fight night — {v.get('name_en') or v['place']}",
            "start": start, "end": end, "tz": "Asia/Bangkok", "all_day": False,
            "url": v.get("source") or "",
            "cost": cost,
            "venue_name": v.get("venue_name") or v.get("name_en") or "",
            "venue_from": "feed",
            "description": desc,
            "recurring": True, "weekday": None, "byday": list(days),
        })
    return out


# ------------------------------------------------------------------ page
def _tickets_line(v, bi):
    tk = v.get("tickets_thb")
    if not tk:
        return ""
    parts = []
    lab = {"stadium": ("ที่นั่งสนาม", "stadium seat"), "standard": ("ธรรมดา", "standard"),
           "ringside": ("ริงไซด์", "ringside"), "vip": ("VIP", "VIP"), "from": ("เริ่ม", "from")}
    for k, n in tk.items():
        th, en = lab.get(k, (k, k))
        parts.append(f"{bi(th, en)} {n:,}")
    s = " · ".join(parts) + " " + bi("บาท", "baht")
    note = ""
    if v.get("tickets_note_th") or v.get("tickets_note_en"):
        note = " — " + bi(v.get("tickets_note_th") or "", v.get("tickets_note_en") or "")
    via = v.get("price_via") or ""
    draft = ("" if v.get("_pricesVerified") else
             f' <span class="draft">({bi("ยังไม่ได้เทียบกับป้ายหน้าสนาม", "not yet checked against the board at the stadium")}'
             + (f" · {via}" if via else "") + ")</span>")
    return f'<p><b>{bi("ตั๋ว", "Tickets")}:</b> {s}{note}{draft}</p>'


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS, BUILD_DATE = g["BASE"], g["DOCS"], g["BUILD_DATE"]
    share_block, channels = g["share_block"], g["channels"]
    PROVINCES, CATS = g["PROVINCES"], g["CATS"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    board = load_board()
    (DOCS / "muaythai.css").write_text(CSS)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "fight_nights.json").write_text(json.dumps(board, ensure_ascii=False, indent=1))

    by_id, prov_of = {}, {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]

    def href(r):
        return f'{prov_of[r["id"]]}/p/{place_slug(r)}.html'

    # ---- the board --------------------------------------------------------
    venues = board.get("venues", [])
    head = "".join(f'<th data-day="{i}">{bi(DAY_TH[i], DAY_EN[i])}</th>' for i in range(7))
    rows, tonight = [], {i: [] for i in range(7)}
    for v in venues:
        r = by_id.get(v["place"])
        nm = name_bi(r) if r else bi(v.get("name_th", ""), v.get("name_en", ""))
        link = f'<a href="{href(r)}">{nm}</a>' if r else nm
        stated = v.get("days") or []
        reported = {}
        for rep in v.get("days_reported") or []:
            for d in rep.get("days") or []:
                reported.setdefault(d, []).append(rep.get("by", ""))
        cells = []
        for i, code in enumerate(DAYS):
            if code in stated:
                cells.append(f'<td data-day="{i}" class="on">{esc(v.get("start") or "")}</td>')
                tonight[i].append((v, r))
            elif code in reported:
                cells.append(f'<td data-day="{i}" class="rep" title="{att(", ".join(reported[code]))}">'
                             f'{esc(v.get("start") or "")}?</td>')
            else:
                cells.append(f'<td data-day="{i}">·</td>')
        sub = ""
        if not stated:
            sub = "<small>" + bi("วันตามรายชื่ออื่น — โทรถามก่อน", "nights as others report them — call first") + "</small>"
        rows.append(f'<tr><td class="venue">{link}{sub}</td>{"".join(cells)}</tr>')
    board_html = (f'<table class="mt-board"><thead><tr><th>{bi("สนาม", "Stadium")}</th>{head}</tr></thead>'
                  f'<tbody>{"".join(rows)}</tbody></table>'
                  f'<p class="mt-legend">{bi("ตัวหนา = สนามบอกเอง · ตัวเอียงมี ? = รายชื่ออื่นบอก ยังไม่ยืนยันกับสนาม · เวลาคือเวลาเริ่มโชว์", "bold = the stadium states it · italic with ? = a listing reports it, unconfirmed with the stadium · times are show start")}'
                  f' · {bi("กระดานตรวจล่าสุด", "board last checked")} {esc(board.get("verified_on", ""))}</p>')

    # Tonight line: one sentence per weekday, swapped in by the browser for the
    # reader's own day (Asia/Bangkok); the page as built names the build day.
    def tonight_sentence(i):
        hits = tonight[i]
        if not hits:
            return bi_text(f"คืน{DAY_TH_LONG[i]} — ไม่มีสนามที่ประกาศคืนชกไว้ · ถามสนามที่ขึ้น ? ดู",
                           f"{DAY_EN_LONG[i]} night — no stadium states a card; ask the ones marked ?")
        names_th = " · ".join(f'{(v.get("name_th") or v.get("name_en"))} {v.get("start") or ""}' for v, _ in hits)
        names_en = " · ".join(f'{v.get("name_en")} {v.get("start") or ""}' for v, _ in hits)
        return bi_text(f"คืน{DAY_TH_LONG[i]}: {names_th}", f"{DAY_EN_LONG[i]} night: {names_en}")
    built_i = datetime.date.fromisoformat(BUILD_DATE).weekday()
    data_attrs = " ".join(f'data-{i}="{att(tonight_sentence(i))}"' for i in range(7))
    tonight_html = (f'<div class="mt-today"><b>🥊 {bi("คืนนี้ชกที่ไหน", "Who fights tonight")}</b>'
                    f'<span id="mt-today" {data_attrs}>{esc(tonight_sentence(built_i))}</span>'
                    f'<div class="mt-note">{bi("สนามบอกคืนชกของตัวเอง มดแดงแค่จดไว้ — ก่อนออกจากบ้านโทรหรือ LINE ถามสักครั้ง", "Each stadium states its own nights; the ants only write them down — one call or LINE before you set out is worth it")}</div></div>')
    today_js = ("<script>(function(){try{var d=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Bangkok'})).getDay();"
                "var i=(d+6)%7;document.querySelectorAll('[data-day=\"'+i+'\"]').forEach(function(c){c.classList.add('today')});"
                "var t=document.getElementById('mt-today');if(t&&t.getAttribute('data-'+i)){t.textContent=t.getAttribute('data-'+i)}}catch(e){}})();</script>")

    # ---- venue cards ------------------------------------------------------
    cards = []
    for v in venues:
        r = by_id.get(v["place"])
        nm = name_bi(r) if r else bi(v.get("name_th", ""), v.get("name_en", ""))
        title = f'<h3><a href="{href(r)}">{nm}</a></h3>' if r else f"<h3>{nm}</h3>"
        addr = f'<p class="addr">📮 {esc(r.get("address"))}</p>' if r and r.get("address") else ""
        stated = f'<p>{bi(v.get("stated_th") or "", v.get("stated_en") or "")}</p>'
        rep_lines = []
        for rep in v.get("days_reported") or []:
            ds = " · ".join(bi_text(DAY_TH[DAYS.index(x)], DAY_EN[DAYS.index(x)]) for x in rep.get("days") or [])
            line = f'{esc(rep.get("by", ""))} ({esc(rep.get("on", ""))}): {esc(ds)}'
            if rep.get("note_th") or rep.get("note_en"):
                line += " — " + bi(rep.get("note_th") or "", rep.get("note_en") or "")
            if rep.get("source"):
                line += f' <a href="{att(rep["source"])}" rel="noopener nofollow">↗</a>'
            rep_lines.append(line)
        rep_html = (f'<p class="src">{bi("รายชื่ออื่นบอกว่า", "Others report")}: {" · ".join(rep_lines)}</p>'
                    if rep_lines else "")
        book = f'<p>{bi("จอง-ถาม", "Book / ask")}: {bi(v.get("book_th") or "", v.get("book_en") or "")}</p>' \
            if (v.get("book_th") or v.get("book_en")) else ""
        src = (f'<p class="src">{bi("ที่มา", "Source")}: <a href="{att(v["source"])}" rel="noopener nofollow">'
               f'{esc(v["source"].replace("https://", "").replace("http://", "").rstrip("/"))}</a> · '
               f'{bi("ดูเมื่อ", "seen")} {esc(v.get("fetched", ""))}</p>') if v.get("source") else ""
        cards.append(f'<div class="mt-venue">{title}{addr}{stated}{_tickets_line(v, bi)}{book}{rep_html}{src}</div>')
    venues_html = f'<div class="mt-venues">{"".join(cards)}</div>'

    unc = board.get("unconfirmed") or []
    unc_html = ""
    if unc:
        items = "".join(
            f'<li><b>{bi(u.get("name_th", ""), u.get("name_en", ""))}</b> — {bi(u.get("note_th", ""), u.get("note_en", ""))}'
            + (f' <a href="{att(u["source"])}" rel="noopener nofollow">↗</a>' if u.get("source") else "")
            + "</li>" for u in unc)
        unc_html = (f'<h3>{bi("สนามที่ยังไม่แน่ใจ", "Unconfirmed rings")}</h3>'
                    f'<p class="mt-note">{bi("ชื่อที่ยังขายตั๋วอยู่บนเว็บแต่ไม่มีใครยืนยันว่ายังชก — ไม่เข้าสารบัญจนกว่าจะมีคนไปยืนหน้าประตู", "Names still selling tickets online that nobody has confirmed still fight — not in the directory until someone stands at the gate")}</p>'
                    f'<ul class="mt-unc">{items}</ul>')
    cr = board.get("chiang_rai") or {}
    cr_html = f'<p class="mt-note">🌱 {bi(cr.get("note_th", ""), cr.get("note_en", ""))}</p>' if cr else ""

    # ---- the shelf: camps, gyms, stadiums, gear -----------------------------
    def on_shelf(r, sub=None):
        return "muaythai" in (r.get("cat") or []) and (sub is None or sub in (r.get("sub") or []))
    shelf_links, camp_rows, n_all = [], [], 0
    cdef = CATS.get("muaythai") or {}
    for p in PROVINCES:
        recs = [r for r in data[p["key"]] if on_shelf(r)]
        if not recs:
            continue
        n_all += len(recs)
        subs = []
        for ch in cdef.get("children", []):
            n = sum(1 for r in recs if on_shelf(r, (ch.get("match") or {}).get("sub")))
            if n:
                subs.append(f'<a href="{p["key"]}/muaythai/{ch["key"]}/index.html">{bi(ch["th"], ch["en"])}</a> '
                            f'<span class="count">({n})</span>')
        shelf_links.append(f'<li><b><a href="{p["key"]}/muaythai/index.html">{bi(p["th"], p["en"])}</a></b> '
                           f'<span class="count">({len(recs)})</span> — {" · ".join(subs)}</li>')
        for r in sorted((x for x in recs if on_shelf(x, "camp")), key=lambda x: g["name_of"](x).lower()):
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
            camp_rows.append(f'<li><a href="{href(r)}">{name_bi(r)}</a>{reach}</li>')
    shelf_note = bi("แผนที่ของชั้นอยู่บนหน้าชั้นแต่ละจังหวัด · สนามมวยและค่ายที่ยังไม่อยู่ในสารบัญ — บอกมดได้ที่",
                    "The shelf map is on each province\u2019s shelf page · a stadium or camp not here yet —")
    shelf_html = (f'<ul class="cats mt-shelf">{"".join(shelf_links)}</ul>'
                  f'<p class="mt-note">{shelf_note} '
                  f'<a href="add.html">{bi("เพิ่มข้อมูล", "add a place")}</a></p>')
    camps_html = (f'<ul class="mt-camps">{"".join(camp_rows)}</ul>' if camp_rows else
                  f'<p class="mt-note">{bi("ยังไม่มีค่ายในสารบัญ", "no camps in the directory yet")}</p>')

    # ---- the primer --------------------------------------------------------
    P = []

    def card(h_th, h_en, *paras):
        body = "".join(f"<p>{x}</p>" for x in paras)
        P.append(f'<div class="mt-card"><h3>{bi(h_th, h_en)}</h3>{body}</div>')

    card("ไหว้ครูรำมวย — ทำไมยังไม่เริ่มชก", "Wai khru ram muay — why the fight has not started",
         bi("ก่อนชกทุกคู่ นักมวยจะไหว้ครู (wâi khruu): เดินวนเวที แตะเชือกมุมทั้งสี่ แล้วรำท่าประจำค่ายของตัวเองช้า ๆ มีเสียงปี่กลองคลอ ใช้เวลาสองสามนาที เป็นการไหว้ครูผู้สอน ไหว้พ่อแม่ และประกาศว่าเวทีนี้เป็นของเรา คนดูท้องถิ่นอ่านออกจากท่ารำว่านักมวยมาจากค่ายไหน",
            "Before every bout each fighter performs the wai khru (ไหว้ครู, wâi khruu): a slow walk round the ring, a touch on the top rope at each corner, then the ram muay (รำมวย), the dance of their own camp, with the pipe and drums under it. Two or three minutes. It salutes the teacher and the parents and declares the ring theirs; a local crowd reads which camp a fighter comes from by the dance alone."),
         bi("การชกยังไม่เริ่มจนกว่าท่านี้จะจบ — อย่าเพิ่งลุกไปซื้อเบียร์ตอนนี้",
            "The fight has not begun until the dance ends — this is not the moment to go for a beer."))
    card("มงคล · ประเจียด — ของสองชิ้นบนตัวนักมวย", "Mongkhon and prajiad — two things on the fighter",
         bi("มงคล (mong-khon) คือเชือกถักวงกลมที่สวมหัวเข้ามาในเวที เป็นของค่าย ไม่ใช่ของนักมวยคนใดคนหนึ่ง ครูเป็นคนสวมและถอดให้ก่อนยกแรก ประเจียด (prà-jìat) คือผ้ารัดต้นแขน มักมีคาถาหรือยันต์พับอยู่ข้างใน สวมไว้ตลอดการชก",
            "The mongkhon (มงคล, mong-khon) is the braided circlet worn into the ring: it belongs to the camp, not to any one fighter, and the trainer puts it on and takes it off before round one. The prajiad (ประเจียด, prà-jìat) are the armbands, often with a katha or a folded yant inside, worn through the fight."),
         f'<span class="say">{bi("ตามประเพณี — มงคลไม่วางถึงพื้น และบางค่ายมีข้อกำหนดว่าใครจับต้องได้ ของสองชิ้นนี้คือจุดที่มวยไทยพบกับสายยันต์-คาถา ซึ่งไปต่อได้ที่ wichaa ด้านล่าง", "Tradition holds — a mongkhon is never set on the floor, and some camps keep rules about who may handle it. These two objects are where muay thai meets the yant-and-katha tradition — which continues on wichaa, below.")}</span>')
    card("เสียงปี่กลอง — สี่คนที่คุมจังหวะทั้งคืน", "The music — four people who set the pace all night",
         bi("วงปี่กลอง: ปี่ชวา (pìi chá-waa, ปี่ลิ้นคู่เสียงแหลม) กลองแขกคู่ และฉิ่ง เล่นตั้งแต่ไหว้ครูจนระฆังยกสุดท้าย เพลงตอนไหว้ครูเรียกว่าสะระหม่า (sà-rá-màa) พอถึงยกท้าย ๆ จังหวะจะเร่งขึ้นตามการชก",
            "The pii klong ensemble: the pii chawaa (ปี่ชวา, pìi chá-waa — a shrill double-reed pipe), a pair of klong khaek drums (กลองแขก) and the ching cymbals (ฉิ่ง), playing from the wai khru to the last bell. The wai khru tune is the sarama (สะระหม่า, sà-rá-màa); in the late rounds the tempo climbs with the fight."),
         bi("ถ้ารู้สึกว่าใจเต้นเร็วขึ้นโดยไม่รู้ตัว นั่นคือฉิ่ง", "If your pulse rises without your leave, that is the ching."))
    card("ยก — ห้ายก สามนาที และยกที่ห้าที่เดินกัน", "The rounds — five of three minutes, and the fifth that is walked",
         bi("มวยอาชีพชก 5 ยก ยกละ 3 นาที พัก 2 นาที ยกแรก ๆ มักชกกันเงียบ ๆ เพื่ออ่านคู่ต่อสู้ ยก 3–4 คือของจริง และถ้าใครนำชัดแล้ว ยก 5 มักจะเดินรำกันจนหมดเวลา — ไม่ใช่ล้มมวย เป็นธรรมเนียม",
            "A professional bout is five rounds of three minutes with two minutes between. The first round or two is often quiet while the two read each other; rounds three and four are the fight; and once one is clearly ahead, round five is often walked out to the bell — not thrown, a custom."),
         bi("กรรมการให้คะแนนจากความสมดุล อาวุธที่เข้าเป้า และใครคุมจังหวะ ไม่ใช่ใครต่อยเยอะกว่า คืนหนึ่งมี 6–8 คู่ มีคู่หญิงและคู่เด็ก-เยาวชนปนอยู่ คู่เอก (khûu èek) คือคู่ท้าย ๆ",
            "Judges score balance, clean strikes that land, and who sets the pace — not who throws more. A card runs six to eight bouts, women's and youth bouts among them; the khu ek (คู่เอก, khûu èek), the main event, comes late."))
    card("เซียนมวย — มุมที่ส่งสัญญาณมือกัน", "The bettors — the corner trading hand signals",
         bi("ฝั่งหนึ่งของอัฒจันทร์จะมีกลุ่มคนยืนขยับนิ้วและตะโกนราคากัน นั่นคือเซียนมวย (sian muay) การพนันมวยเป็นเรื่องธรรมดาในสนามมวยไทย ไม่มีใครคาดหวังให้คุณเข้าร่วม และไม่มีใครว่าถ้าไม่สนใจ ดูมือเซียนก็พอรู้ว่าห้องนี้คิดว่าใครกำลังนำ",
            "On one side of the stands a knot of people flick fingers and shout odds — the sian muay (เซียนมวย), the bettors. Betting is ordinary in a Thai boxing stadium; nobody expects you to join and nobody minds if you don't. Watching their hands tells you who the room thinks is winning."))
    card("ตั๋วและเงิน — ชั้นที่นั่ง เครื่องดื่ม และรถรับฟรี", "Tickets and money — seat classes, the drink, the free pickup",
         bi("สนามขายตั๋วสองถึงสามชั้น: ที่นั่งสนาม / ริงไซด์ / VIP (VIP มักแถมเครื่องดื่ม) ราคาที่สนามในเมืองประกาศเองคืนนี้อยู่ราว 600 ถึง 1,500 บาท — ตัวเลขในกระดานด้านบนมีที่มาและวันที่ดูกำกับทุกตัว",
            "Stadiums sell two or three classes: stadium seat / ringside / VIP (VIP usually includes a drink). The prices the town's stadiums post themselves run from about 600 to 1,500 baht — every number on the board above carries its source and the date it was read."),
         bi("\"รถรับส่งฟรี\" จากบาร์หรือตุ๊กตุ๊กคือค่านายหน้าที่รวมอยู่ในตั๋วแล้ว ไม่ผิดอะไร แค่รู้ไว้ จองตรงกับสนามทาง LINE ก็ได้เท่ากัน · ค่าเรียนที่ค่ายคิดเป็นครั้ง เป็นสัปดาห์ เป็นเดือน — ป้ายหน้าค่ายคือของจริง และถ้าคุณจ่ายไปเท่าไหร่ บอกมดได้",
            "A \"free transfer\" from a bar or a tuk-tuk is a commission folded into the ticket — nothing wrong with it, just know it; booking with the stadium by LINE costs the same. Camps price by the session, the week and the month — the board on the camp wall is the truth, and if you paid, tell the ants what."))
    card("คำที่จะได้ยิน", "Words you will hear",
         '<ul class="mt-words">'
         + "".join(f"<li>{bi(th, en)}</li>" for th, en in [
             ("เตะ (tè) — เตะ", "te (เตะ, tè) — kick"),
             ("ต่อย (tòi) — ชกด้วยหมัด", "toi (ต่อย, tòi) — punch"),
             ("ศอก (sòk) — ศอก", "sok (ศอก, sòk) — elbow"),
             ("เข่า (khào) — เข่า", "khao (เข่า, khào) — knee"),
             ("ถีบ (thìip) — เตะถีบ", "thip (ถีบ, thìip) — the push kick, the teep"),
             ("ยก (yók) — ยก", "yok (ยก, yók) — round"),
             ("น็อก (nók) — ชนะน็อก", "nok (น็อก, nók) — knockout"),
             ("เสมอ (sà-mə̌ə) — เสมอกัน", "samoe (เสมอ, sà-mə̌ə) — a draw"),
             ("นักมวย (nák muay) — นักชก", "nak muay (นักมวย, nák muay) — fighter"),
             ("ครูมวย (khruu muay) — ผู้ฝึกสอน", "khru muay (ครูมวย, khruu muay) — trainer"),
             ("ค่าย (khâai) — ค่ายมวย", "khai (ค่าย, khâai) — camp"),
             ("คาดเชือก (khâat chʉ̂ak) — มวยโบราณพันมือด้วยเชือก", "khat chueak (คาดเชือก, khâat chʉ̂ak) — the old rope-bound style"),
             ("แม่ไม้ (mâe máai) — ท่าหลัก 15 ท่า", "mae mai (แม่ไม้, mâe máai) — the master techniques"),
             ("ไหว้ครู (wâi khruu) — การไหว้ครูก่อนชก", "wai khru (ไหว้ครู, wâi khruu) — the salute before the bout"),
         ]) + "</ul>",
         f'<span class="say">{bi("คำว่า มวย (muay) ในพจนานุกรมมีทั้งความหมายชกด้วยหมัด และมุ่นผมเป็นก้อน (มวยผม) — ที่เล่ากันว่ามาจากการพันหมัดด้วยเชือกเป็นเรื่องเล่าสืบต่อ ไม่ใช่รากศัพท์ที่ชี้ขาด", "The word muay (มวย) carries two dictionary senses — fighting with the fists, and a hair bun (มวยผม). Tradition holds the fighting sense came from binding the fists with rope; an inference, not a settled etymology.")}</span>')
    card("สองวันในปฏิทิน", "Two days in the calendar",
         bi("6 กุมภาพันธ์ — วันมวยไทย มติคณะรัฐมนตรี 3 พ.ค. 2554 เทิดพระเกียรติสมเด็จพระเจ้าเสือ พระบิดาแห่งมวยไทย · 17 มีนาคม — วันนายขนมต้ม / วันไหว้ครูมวยไทยโลก จัดที่อยุธยา ระลึกถึงนักมวยเชลยที่ชนะมวยพม่าต่อหน้าพระเจ้ามังระ",
            "6 February — วันมวยไทย, Muay Thai Day, set by a 2011 Cabinet resolution in honour of King Sanphet VIII, the Tiger King, held to be the father of the art · 17 March — Nai Khanom Tom Day, the World Wai Khru Muay Thai ceremony at Ayutthaya, for the captive fighter who beat the Burmese champions before King Hsinbyushin."),
         f'<a href="festivals.html">{bi("ทั้งสองวันอยู่ในปฏิทินเทศกาล", "Both are on the festivals page")} →</a>')
    card("ภาคเหนือ — เจิง ตบมะผาบ และมวยงานวัด", "The north — choeng, top ma phap, and temple-fair cards",
         bi("เชียงใหม่ไม่ได้เป็นเมืองหลวงของมวยไทย แต่ภาคเหนือมีของตัวเอง: เจิง (cəəng) ศิลปะการต่อสู้ล้านนาที่ฟ้อนได้ — ฟ้อนเจิง ฟ้อนดาบ และตบมะผาบ (tòp má-phàap) การตบตัวให้ดังเป็นจังหวะก่อนเข้าท่า ยังเห็นในขบวนแห่และงานปอยของวัด ส่วนมวยท่าเสาของอุตรดิตถ์ถูกนับเป็นสายเหนือในห้ามวยภูมิภาคตามที่เล่าสืบกันมา",
            "Chiang Mai is not the capital of muay thai, but the north has its own: choeng (เจิง, cəəng), the Lanna fighting art that is also danced — fon choeng, the sword dance, and top ma phap (ตบมะผาบ, tòp má-phàap), the loud rhythmic body-slap before a form — still seen in processions and at temple fairs. Tradition holds that Muay Tha Sao of Uttaradit is the northern line among the regional styles."),
         bi("มวยงานวัด: เวทีชั่วคราวในงานปอย คู่เด็กและคู่ท้องถิ่น ค่าเข้าไม่มีหรือน้อย — ถ้าได้ยินเสียงปี่กลองจากวัดตอนค่ำ นั่นอาจเป็นมวย",
            "Temple-fair cards: a ring raised for the fair, youth and village bouts, little or no entry — if you hear the pipe and drums from a wat after dark, it may be boxing."))
    primer_html = f'<div class="mt-grid">{"".join(P)}</div>'

    joins_html = (f'<div class="mt-joins"><b>{bi("ไปต่อที่ wichaa", "Onward, on wichaa")}</b>'
                  f'<p><a href="https://wichaa.net/yant" rel="noopener">wichaa.net/yant</a> — '
                  + bi("ลายยันต์ที่พับอยู่ในประเจียด: สารบัญลายยันต์ของล้านนา ระบุชื่อ สรรพคุณ และหน้าคัมภีร์ที่อ่านมา",
                       "the designs folded inside a prajiad: the Lanna yant index by name, by what each is for, and by the manuscript page it was read from")
                  + f'</p><p><a href="https://wichaa.net/waikhru" rel="noopener">wichaa.net/waikhru</a> — '
                  + bi("การไหว้ครูแบบเดียวกัน ทำไว้ให้มือที่อยู่หน้าเครื่องจักร: ไหว้ · รับ · รับปาก — นักมวยทำสามจังหวะนี้ทุกคืนบนเวที",
                       "the same salute, made for the hand at a machine: salute · receive · undertake — a fighter does those three beats every night in the ring")
                  + f'</p><p><a href="https://wichaa.net/thairoots" rel="noopener">wichaa.net/thairoots</a> — '
                  + bi("รากศัพท์ไทย สำหรับคนที่อยากรู้ว่า มวย ไหว้ และครู มาจากไหน",
                       "Thai roots, for whoever wants to know where muay, wai and khru come from")
                  + "</p></div>")

    # ---- assemble ---------------------------------------------------------
    intro = bi("หน้านี้มีสามอย่าง: กระดานคืนชกของทุกสนามในเมือง (สนามบอกเอง มดจดไว้พร้อมที่มา) ชั้นค่ายมวยและยิมที่ฝึกได้ และเรื่องที่ควรรู้ก่อนเสียงปี่ดัง — เขียนจากที่นั่งคนดู ไม่ได้จัดอันดับว่าสนามไหนแท้กว่ากัน เวทีก็คือเวที",
               "Three things on one page: the weekly fight board for every stadium in town (each stadium states its own nights; the ants write them down with the source), the shelf of camps and gyms where you can train, and what to know before the pipes start — written from the seat, with no ranking of stadiums into real and otherwise. A ring is a ring.")
    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "สนามมวยเชียงใหม่ — Muay Thai stadiums and fight nights, Chiang Mai",
        "url": BASE + "muaythai.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "StadiumOrArena", "name": v.get("name_en") or v.get("name_th"),
                      "alternateName": v.get("name_th"),
                      **({"url": BASE + href(by_id[v["place"]])} if v["place"] in by_id else {}),
                      **({"openingHours": " ".join(f"{d[0]}{d[1].lower()}" for d in v["days"]) + f" {v.get('start')}-{v.get('end') or ''}"}
                         if v.get("days") else {})}}
            for i, v in enumerate(venues)],
    }
    head = ('<link rel="stylesheet" href="muaythai.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "muaythai") if shelf_og else None
    body = (
        f'<h1>🥊 {bi("มวยไทย — ดูมวยคืนนี้ ฝึกที่ไหน รู้อะไรก่อนเข้าสนาม", "Muay Thai — tonight, where to train, what to know")}</h1>'
        f'<p class="mt-intro">{intro}</p>'
        f'{tonight_html}'
        f'<h2>{bi("กระดานคืนชกประจำสัปดาห์", "The weekly fight board")}</h2>'
        f'{board_html}{venues_html}{unc_html}{cr_html}'
        f'<h2>{bi("ชั้นมวยไทย — สนาม ค่าย ยิม ร้านอุปกรณ์", "The Muay Thai shelf — stadiums, camps, gyms, gear")}</h2>'
        f'{shelf_html}'
        f'<h3>{bi("ค่ายมวยและยิมที่ฝึกได้", "Camps and gyms where you can train")} <span class="count">({len(camp_rows)})</span></h3>'
        f'<p class="mt-note">{bi("เรียงตามชื่อ ไม่จัดอันดับ — ☎ LINE 🌐 คือช่องทางที่สารบัญมี ค่ายไหนยังไม่มีเบอร์ ช่วยกันเติมได้", "Alphabetical, unranked — ☎ LINE 🌐 mark the channels the directory holds; a camp with none yet can be filled in by anyone")}</p>'
        f'{camps_html}'
        f'<h2>{bi("ก่อนเสียงปี่ดัง — เรื่องที่ควรรู้", "Before the pipes start — what you are looking at")}</h2>'
        f'{primer_html}{joins_html}'
        f'<p class="mt-note">{bi("ที่มาของกระดาน", "Board data")}: <a href="data/fight_nights.json">data/fight_nights.json</a> · '
        f'{bi("คืนที่สนามบอกเองอยู่ในปฏิทินงานเมืองด้วย", "Nights the stadiums state are also on the events page")} → <a href="events.html">events.html</a> · <a href="events.ics">events.ics</a></p>'
        f'{share_block(BASE + "muaythai.html", "มวยไทย ดูมวยคืนนี้ · มดแดง", card=og)}'
        f'{today_js}')
    (DOCS / "muaythai.html").write_text(page(
        "มวยไทย — ดูมวยคืนนี้ เชียงใหม่ · Muay Thai in Chiang Mai — tonight's fights",
        body, depth=0, path="muaythai.html",
        desc="กระดานคืนชกมวยไทยทุกสนามในเชียงใหม่ ราคาตั๋ว ค่ายมวย-ยิมที่ฝึกได้ และเรื่องที่ควรรู้ก่อนเข้าสนาม · Muay Thai in Chiang Mai: tonight's fight board, ticket prices, camps and gyms, and what to know before the pipes start",
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("มวยไทย", "Muay Thai")}'))
    stated = sum(1 for v in venues if v.get("days"))
    return {"page": 1, "venues": len(venues), "stated": stated, "camps": len(camp_rows), "on_shelf": n_all}
