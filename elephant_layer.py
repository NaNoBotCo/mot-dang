#!/usr/bin/env python3
"""ช้าง — the register of what each camp states, the shelf, the city's elephant
names, and what to know before you go.

Three things a reader asks about elephants in this town, in the order they
ask them, on one page (/chang.html):

  1. WHICH CAMP, AND WHAT HAPPENS THERE — the register: for every camp the
     directory holds, what THE CAMP ITSELF states on its own site about
     riding, bathing, shows and a hands-off option, how many elephants it
     says it keeps, what it posts as the price. Read from
     data/curated/elephants.json, where every row names who stated it and
     when. "unstated" is a column value and it means the pages read did not
     say — it is not a no and it is not a yes. "sanctuary", "ethical" and
     "rescue" are a venue's own words and render as the venue's words. No
     row is a welfare verdict; no camp is ranked against another. A venue
     whose pages could not be read is listed by name with what happened.
  2. WHERE THE SHELF IS — the camps, the clinic and the of-the-elephant
     places the catalogue holds, one line each with their reach, linking to
     the shelf where the map is. The shelf is the list of record; this is
     its front porch.
  3. WHAT YOU ARE LOOKING AT — the two laws an elephant sits under and the
     bodies that certify camps, named as what they are; the national
     hospital and institute in Lampang; the names in this city that carry
     the elephant (the White Elephant Gate, Wat Lam Chang, Chang Khlan, Chang
     Moi, Doi Chang…) with the tradition each carries, marked as tradition;
     a first-timer's primer — the word ปาง, the mahout and the hook, the
     white elephant and its marks, money, a dozen words, the national day.

The joins to wichaa are stated from THIS side: what each wichaa page is to a
person who has just spent a morning beside an elephant.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
muay thai layer. Emits chang.html + chang.css, copies the register to
docs/data/elephants.json; prints the counts.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "data" / "curated" / "elephants.json"
sys.path.insert(0, str(ROOT / "importers"))
import audit_elephant  # noqa: E402  (zero network; the NAME_ELEMENTS fence)

CSS = """
.ch-intro{font-size:1.02rem;max-width:46rem}
.ch-rule{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07);font-size:.98rem}
.ch-rule b{display:block;margin-bottom:.15rem}
.ch-reg{width:100%;border-collapse:collapse;margin:.6rem 0 .4rem;font-size:.93rem}
.ch-reg th,.ch-reg td{padding:.4rem .35rem;border-bottom:1px solid rgba(0,0,0,.08);text-align:center;vertical-align:top}
.ch-reg th:first-child,.ch-reg td:first-child{text-align:left}
.ch-reg td.no{font-weight:600;color:var(--ant-dark)}
.ch-reg td.yes{font-weight:600}
.ch-reg td.un{color:var(--mute);font-style:italic}
.ch-reg .venue a{text-decoration:none;color:inherit}
.ch-reg .venue a:hover{text-decoration:underline}
.ch-reg .venue small{display:block;color:var(--mute);font-weight:400;font-size:.8rem}
.ch-legend{font-size:.82rem;color:var(--mute);margin:0 0 1rem}
.ch-venues{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));margin:.6rem 0 1.2rem}
.ch-venue{border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:.75rem .85rem;background:#fff}
.ch-venue h3{margin:0 0 .3rem;font-size:1.05rem}
.ch-venue h3 a{text-decoration:none;color:inherit}
.ch-venue h3 a:hover{text-decoration:underline}
.ch-venue p{margin:.25rem 0;font-size:.92rem}
.ch-venue .src{font-size:.8rem;color:var(--mute)}
.ch-venue .self{font-style:italic}
.ch-venue .draft{font-size:.8rem;color:var(--mute)}
.ch-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));margin:.6rem 0 1.2rem}
.ch-card{border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:.75rem .9rem;background:#fff}
.ch-card h3{margin:0 0 .35rem;font-size:1.05rem}
.ch-card p{margin:.3rem 0;font-size:.93rem;line-height:1.55}
.ch-card .say{font-size:.86rem;color:var(--mute)}
.ch-words{columns:2;column-gap:1.5rem;margin:.4rem 0 1rem;font-size:.95rem}
.ch-words li{break-inside:avoid;margin:.15rem 0}
@media (max-width:40rem){.ch-words{columns:1}}
.ch-camps{list-style:none;padding:0;margin:.4rem 0 1rem;columns:2;column-gap:1.5rem}
.ch-camps li{break-inside:avoid;margin:.2rem 0;font-size:.95rem}
@media (max-width:40rem){.ch-camps{columns:1}}
.ch-camps .reach{color:var(--mute);font-size:.85rem}
.ch-shelf{margin:.4rem 0 1rem}
.ch-joins{margin:.6rem 0 1.2rem;padding:.8rem .9rem;border-radius:.8rem;background:var(--soft)}
.ch-joins p{margin:.3rem 0;font-size:.93rem}
.ch-unc{font-size:.92rem}
.ch-unc li{margin:.25rem 0}
.ch-note{font-size:.86rem;color:var(--mute)}
.ch-names{font-size:.93rem;margin:.4rem 0 1rem}
.ch-names li{margin:.25rem 0}
.ch-names .cnt{color:var(--mute);font-size:.85rem}
.ch-land{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));margin:.6rem 0 1.2rem}
.ch-land .ch-card p{font-size:.9rem}
"""

STATED_TH = {"no": "ไม่มี", "yes": "มี", "unstated": "ไม่ระบุ", "program": "มีโปรแกรม", "all": "ทั้งหมด"}
STATED_EN = {"no": "no", "yes": "yes", "unstated": "unstated", "program": "a program", "all": "all of it"}


def load_reg():
    return json.loads(REG.read_text())


def _cell(val, bi_text, att):
    """A register cell. `no` is bold: the venue said it in words. `unstated`
    is italic: the pages read did not say, which is neither."""
    v = val or "unstated"
    cls = {"no": "no", "yes": "yes", "program": "yes", "all": "yes"}.get(v, "un")
    return (f'<td class="{cls}" title="{att(bi_text(STATED_TH.get(v, v), STATED_EN.get(v, v)))}">'
            f'{bi_text(STATED_TH.get(v, v), STATED_EN.get(v, v))}</td>')


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi, name_of = g["place_slug"], g["name_bi"], g["name_of"]
    BASE, DOCS, BUILD_DATE = g["BASE"], g["DOCS"], g["BUILD_DATE"]
    share_block, channels = g["share_block"], g["channels"]
    PROVINCES, CATS = g["PROVINCES"], g["CATS"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    reg = load_reg()
    (DOCS / "chang.css").write_text(CSS)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "elephants.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1))

    by_id, prov_of = {}, {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]

    def href(r):
        return f'{prov_of[r["id"]]}/p/{place_slug(r)}.html'

    def link(place_id, fallback_th="", fallback_en=""):
        r = by_id.get(place_id) if place_id else None
        if r:
            return f'<a href="{href(r)}">{name_bi(r)}</a>'
        return bi(fallback_th, fallback_en) if (fallback_th or fallback_en) else ""

    # ---- the register ---------------------------------------------------
    venues = reg.get("venues", [])
    head = "".join(f"<th>{bi(th, en)}</th>" for th, en in [
        ("ขี่ช้าง", "riding"), ("อาบน้ำกับช้าง", "bathing"), ("โชว์", "shows"),
        ("ดูอย่างเดียว", "hands-off"), ("ช้าง", "elephants"), ("ราคาที่ประกาศ", "posted")])
    rows = []
    n_no_ride = n_unstated_ride = 0
    for v in venues:
        r = by_id.get(v["place"])
        nm = name_bi(r) if r else esc(v.get("name_en", ""))
        lk = f'<a href="{href(r)}">{nm}</a>' if r else nm
        st = v.get("stated") or {}
        if st.get("riding") == "no":
            n_no_ride += 1
        if (st.get("riding") or "unstated") == "unstated":
            n_unstated_ride += 1
        dist = f'<small>{bi(v.get("district_th", ""), v.get("district_en", ""))}</small>'
        price = bi(v.get("prices_th") or "—", v.get("prices_en") or "—") if (v.get("prices_th") or v.get("prices_en")) else "—"
        rows.append(
            f'<tr><td class="venue">{lk}{dist}</td>'
            + _cell(st.get("riding"), bi_text, att) + _cell(st.get("bathing"), bi_text, att)
            + _cell(st.get("shows"), bi_text, att) + _cell(st.get("handsoff"), bi_text, att)
            + f'<td>{esc(v.get("elephants") or "—")}</td><td>{price}</td></tr>')
    reg_html = (f'<table class="ch-reg"><thead><tr><th>{bi("ปาง", "Camp")}</th>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table>'
                f'<p class="ch-legend">{bi("ตัวหนา = ปางบอกเองเป็นคำพูดบนเว็บของตัวเอง · ตัวเอียง “ไม่ระบุ” = หน้าที่อ่านไม่ได้พูดถึง — ไม่ใช่ “ไม่มี” และไม่ใช่ “มี” · โชว์ = การแสดง วาดรูป เล่นกล · ราคาคือที่ประกาศ ยังไม่มีใครอ่านป้ายหน้าปาง", "bold = the camp says so in words on its own site · italic “unstated” = the pages read did not say — neither a no nor a yes · shows = performances, painting, tricks · prices are as posted; nobody has yet read a board at a gate")}'
                f' · {bi("ทะเบียนตรวจล่าสุด", "register last read")} {esc(reg.get("verified_on", ""))}</p>')

    # ---- venue cards ----------------------------------------------------
    cards = []
    for v in venues:
        r = by_id.get(v["place"])
        nm = name_bi(r) if r else esc(v.get("name_en", ""))
        title = f'<h3><a href="{href(r)}">{nm}</a></h3>' if r else f"<h3>{nm}</h3>"
        dist = f'<p class="src">📍 {bi(v.get("district_th", ""), v.get("district_en", ""))}</p>'
        self_ = (f'<p class="self">{bi("ปางเรียกตัวเองว่า", "calls itself")}: “{bi(v.get("self_th", ""), v.get("self_en", ""))}”</p>'
                 if (v.get("self_th") or v.get("self_en")) else "")
        prog = f'<p>{bi(v.get("program_th", ""), v.get("program_en", ""))}</p>' if (v.get("program_th") or v.get("program_en")) else ""
        price = ""
        if v.get("prices_th") or v.get("prices_en"):
            draft = ("" if v.get("_pricesVerified") else
                     f' <span class="draft">({bi("ตามที่ประกาศ ยังไม่ได้เทียบที่หน้าปาง", "as posted — not yet checked at the gate")})</span>')
            price = f'<p><b>{bi("ราคา", "Prices")}:</b> {bi(v.get("prices_th", ""), v.get("prices_en", ""))}{draft}</p>'
        note = f'<p class="src">{bi(v.get("note_th", ""), v.get("note_en", ""))}</p>' if (v.get("note_th") or v.get("note_en")) else ""
        src = (f'<p class="src">{bi("ที่มา", "Source")}: <a href="{att(v["source"])}" rel="noopener nofollow">'
               f'{esc(v["source"].replace("https://", "").replace("http://", "").rstrip("/"))}</a> · '
               f'{bi("ดูเมื่อ", "read")} {esc(v.get("fetched", ""))} · {bi("ผู้บอก", "stated by")}: {esc(v.get("stated_by", ""))}</p>') if v.get("source") else ""
        cards.append(f'<div class="ch-venue">{title}{dist}{self_}{prog}{price}{note}{src}</div>')
    venues_html = f'<div class="ch-venues">{"".join(cards)}</div>'

    # unreachable + unconfirmed + chiang rai + lampang
    unr = reg.get("unreachable") or []
    unr_html = ""
    if unr:
        items = "".join(f'<li><b>{esc(u.get("name_en", ""))}</b> — {bi(u.get("note_th", ""), u.get("note_en", ""))} '
                        f'<span class="ch-note">({esc(u.get("what", ""))})</span></li>' for u in unr)
        unr_html = (f'<h3>{bi("ปางที่เว็บยังอ่านไม่ได้", "Camps whose pages could not be read")}</h3>'
                    f'<p class="ch-note">{bi("ลงชื่อไว้ตามตรงว่าเกิดอะไรขึ้น — ไม่ใช่ว่าไม่มี และไม่ใช่ว่าปิด ใครไปยืนหน้าประตูมาแล้ว บอกมดได้", "Named with what happened — not absent, not closed; if you have stood at the gate, tell the ants")}</p>'
                    f'<ul class="ch-unc">{items}</ul>')
    unc = reg.get("unconfirmed") or []
    unc_html = ""
    if unc:
        items = "".join(f'<li><b>{esc(u.get("name_en", ""))}</b> — {bi(u.get("note_th", ""), u.get("note_en", ""))}</li>' for u in unc)
        unc_html = (f'<h3>{bi("ยังไม่ยืนยัน", "Unconfirmed")}</h3><ul class="ch-unc">{items}</ul>')
    # Camps the shelf holds that the register has no row for — the OSM crawl
    # brings a camp in with a surveyed pin and no read of its own site, and
    # the gap between the two lists is a fact worth stating rather than
    # papering over: the shelf says it exists; the register says what it
    # states; a camp can honestly be on one and not yet the other.
    reg_ids = {v.get("place") for v in venues}
    no_row = [r for p in PROVINCES for r in data[p["key"]]
              if "chang" in (r.get("cat") or []) and "elephant-camp" in (r.get("sub") or [])
              and r["id"] not in reg_ids]
    norow_html = ""
    if no_row:
        links = " · ".join(f'<a href="{href(r)}">{name_bi(r)}</a>'
                           for r in sorted(no_row, key=lambda x: name_of(x).lower()))
        norow_html = (f'<p class="ch-note">🐜 {bi("บนชั้นแล้ว มดยังไม่ได้อ่านเว็บของปางเอง", "On the shelf; the ants have not yet read the venue’s own pages")} '
                      f'({len(no_row)}): {links}</p>')
    cr = reg.get("chiang_rai") or {}
    cr_html = f'<p class="ch-note">🌱 {bi(cr.get("note_th", ""), cr.get("note_en", ""))}</p>' if cr else ""
    lp = reg.get("lampang") or {}
    lp_html = ""
    if lp:
        t = lp.get("tecc") or {}
        f_ = lp.get("fae") or {}
        phones = " · ".join(f'<a href="tel:{att(re.sub(r"[^0-9+]", "", x))}">{esc(x)}</a>' for x in t.get("phones") or [])
        lp_html = (f'<div class="ch-card"><h3>🏥 {bi("ลำปาง — โรงพยาบาลช้างและสถาบันคชบาล", "Lampang — the elephant hospital and the institute")}</h3>'
                   f'<p class="ch-note">{bi(lp.get("note_th", ""), lp.get("note_en", ""))}</p>'
                   f'<p><b>{bi(t.get("name_th", ""), t.get("name_en", ""))}</b> — {esc(t.get("district_en", ""))}'
                   + (f' · ☎ {phones}' if phones else "")
                   + (f' · <a href="{att(t["website"])}" rel="noopener nofollow">{esc(t["website"].replace("https://", "").rstrip("/"))}</a>' if t.get("website") else "")
                   + f'</p><p class="ch-note">{bi(t.get("stated_th", ""), t.get("stated_en", ""))} ({bi("ดูเมื่อ", "read")} {esc(t.get("fetched", ""))})</p>'
                   f'<p><b>{bi(f_.get("name_th", ""), f_.get("name_en", ""))}</b> — {esc(f_.get("district_en", ""))} · {bi(f_.get("stated_th", ""), f_.get("stated_en", ""))}</p></div>')

    # ---- the shelf: camps, the clinic, the craft ----------------------------
    def on_shelf(r, sub=None):
        return "chang" in (r.get("cat") or []) and (sub is None or sub in (r.get("sub") or []))
    shelf_links, camp_rows, n_all = [], [], 0
    cdef = CATS.get("chang") or {}
    for p in PROVINCES:
        recs = [r for r in data[p["key"]] if on_shelf(r)]
        if not recs:
            continue
        n_all += len(recs)
        subs = []
        for ch in cdef.get("children", []):
            n = sum(1 for r in recs if on_shelf(r, (ch.get("match") or {}).get("sub")))
            if n:
                subs.append(f'<a href="{p["key"]}/chang/{ch["key"]}/index.html">{bi(ch["th"], ch["en"])}</a> '
                            f'<span class="count">({n})</span>')
        shelf_links.append(f'<li><b><a href="{p["key"]}/chang/index.html">{bi(p["th"], p["en"])}</a></b> '
                           f'<span class="count">({len(recs)})</span> — {" · ".join(subs)}</li>')
        for r in sorted((x for x in recs if on_shelf(x, "elephant-camp")), key=lambda x: name_of(x).lower()):
            live, _ = channels(r)
            kinds = [c.get("kind") for c in live] if live and isinstance(live[0], dict) else []
            marks = []
            if r.get("phone") or "phone" in kinds:
                marks.append("☎")
            if "line" in kinds or (r.get("attrs") or {}).get("lineId"):
                marks.append("LINE")
            if (r.get("attrs") or {}).get("whatsapp") or "whatsapp" in kinds:
                marks.append("WA")
            if r.get("website") or "website" in kinds:
                marks.append("🌐")
            pin = "" if (r.get("lat") and r.get("lng")) else f' <span class="reach">{bi("ยังไม่มีหมุด", "no pin yet")}</span>'
            reach = f' <span class="reach">{" ".join(marks)}</span>' if marks else \
                f' <span class="reach">{bi("ยังไม่มีเบอร์", "no contact yet")}</span>'
            camp_rows.append(f'<li><a href="{href(r)}">{name_bi(r)}</a>{reach}{pin}</li>')
    shelf_note = bi("แผนที่ของชั้นอยู่บนหน้าชั้นแต่ละจังหวัด · ปางที่ยังไม่อยู่ในสารบัญ — บอกมดได้ที่",
                    "The shelf map is on each province’s shelf page · a camp not here yet —")
    shelf_html = (f'<ul class="cats ch-shelf">{"".join(shelf_links)}</ul>'
                  f'<p class="ch-note">{shelf_note} <a href="add.html">{bi("เพิ่มข้อมูล", "add a place")}</a> · '
                  f'{bi("ปางที่ยังไม่มีหมุดอยู่ใน", "camps still without a pin are on")} <a href="pins.html">pins.html</a></p>')
    camps_html = (f'<ul class="ch-camps">{"".join(camp_rows)}</ul>' if camp_rows else
                  f'<p class="ch-note">{bi("ยังไม่มีปางในสารบัญ", "no camps in the directory yet")}</p>')

    # ---- the law and the bodies -----------------------------------------------
    LAW = []
    for x in reg.get("registers") or []:
        LAW.append(f'<div class="ch-card"><h3>{bi(x.get("th", ""), x.get("en", ""))}</h3><p>{bi(x.get("what_th", ""), x.get("what_en", ""))}</p></div>')
    for x in reg.get("standards_bodies") or []:
        LAW.append(f'<div class="ch-card"><h3>{esc(x.get("name", ""))}</h3><p>{bi(x.get("what_th", ""), x.get("what_en", ""))}</p></div>')
    law_html = (f'<p class="ch-note">{bi("ช้างเลี้ยงทุกเชือกมีกระดาษ และปางมีใบรับรองได้หลายใบ — หน้านี้บอกว่าแต่ละใบคืออะไร ไม่ได้มอบใบไหนให้ใคร ปางไหนถือใบไหน ถามปาง", "Every captive elephant has a paper, and a camp can hold several certificates — this page says what each one is, and awards none; which a camp holds is a question for the camp")}</p>'
                f'<div class="ch-grid">{"".join(LAW)}</div>')

    # ---- the city's elephant names ------------------------------------------
    LANDS = []
    for x in reg.get("landmarks") or []:
        r = by_id.get(x.get("place")) if x.get("place") else None
        title = f'<a href="{href(r)}">{bi(x.get("name_th", ""), x.get("name_en", ""))}</a>' if r else bi(x.get("name_th", ""), x.get("name_en", ""))
        norec = "" if r else f' <span class="ch-note">({bi("ยังไม่มีระเบียน", "no record yet")})</span>'
        LANDS.append(f'<div class="ch-card"><h3>{title}{norec}</h3><p>{bi(x.get("line_th", ""), x.get("line_en", ""))}</p></div>')
    land_html = (f'<p class="ch-note">{bi("ประโยคที่ขึ้นต้นว่า “ตามตำนาน” คือตำนาน — ไม่ใช่เอกสารที่มดถืออยู่ ใครมีฉบับที่ดีกว่า ส่งมาได้", "A line that begins “tradition holds” is tradition — not a document the ants hold; a better telling is welcome")}</p>'
                 f'<div class="ch-land">{"".join(LANDS)}</div>')
    # live: every record whose name holds the elephant, grouped by element
    allrecs = [r for p in PROVINCES for r in data[p["key"]]]
    named = [r for r in allrecs if audit_elephant.ELE_RE.search(audit_elephant.name_of(r))
             and not audit_elephant.is_camp(r) and not audit_elephant.is_care(r) and not audit_elephant.is_craft(r)
             and "chang" not in (r.get("cat") or [])]
    groups, rest = {}, []
    for r in named:
        n = audit_elephant.name_of(r)
        for label, pat in audit_elephant.NAME_ELEMENTS:
            if re.search(pat, n, re.I):
                groups.setdefault(label, []).append(r)
                break
        else:
            rest.append(r)
    name_items = []
    for label, _ in audit_elephant.NAME_ELEMENTS:
        rs = groups.get(label)
        if not rs:
            continue
        links = " · ".join(f'<a href="{href(r)}">{name_bi(r)}</a>' for r in rs[:6])
        more = f' <span class="cnt">+{len(rs) - 6}</span>' if len(rs) > 6 else ""
        name_items.append(f'<li><b>{esc(label)}</b> <span class="cnt">({len(rs)})</span> — {links}{more}</li>')
    if rest:
        links = " · ".join(f'<a href="{href(r)}">{name_bi(r)}</a>' for r in rest[:8])
        name_items.append(f'<li><b>{bi("อื่น ๆ", "other")}</b> <span class="cnt">({len(rest)})</span> — {links}</li>')
    names_html = (f'<p class="ch-note">{bi(f"ระเบียน {len(named)} แห่งในสารบัญมีคำว่าช้างอยู่ในชื่อโดยไม่ใช่ปางช้าง — เมืองนี้จำช้างไว้ในชื่อย่าน ประตู วัด ดอย และชื่อเล่น (ลุงช้างคือคน) นี่คือแผนที่ว่าช้างเคยอยู่ตรงไหน ไม่ใช่ความผิดพลาดที่ต้องเก็บกวาด", f"{len(named)} records carry the elephant in their name without being an elephant venue — the city remembers elephants in the names of quarters, a gate, temples, a mountain and a nickname (Uncle Chang is a man). A map of where elephants were, not a mess to clean up")}</p>'
                  f'<ul class="ch-names">{"".join(name_items)}</ul>')

    # ---- the primer -------------------------------------------------------------
    P = []

    def card(h_th, h_en, *paras):
        body = "".join(f"<p>{x}</p>" for x in paras)
        P.append(f'<div class="ch-card"><h3>{bi(h_th, h_en)}</h3>{body}</div>')

    def say(th, en):
        # Lifted out of the f-strings on purpose: an apostrophe inside a bi()
        # call nested in an f'…' string is a SyntaxError on Python 3.9.
        return '<span class="say">' + bi(th, en) + "</span>"

    # money from the register itself, computed not typed
    posted = [v for v in venues if v.get("prices_en")]
    card("ปาง — คำที่อยู่หน้าทุกชื่อ", "Pang — the word in front of every name",
         bi("ปางช้าง (paang cháang) — ปาง คือค่ายพักในป่าที่ตั้งชั่วคราวเพื่อทำงาน คำเดียวกับปางไม้ของคนทำไม้ซุง ปางช้างจึงแปลตรงตัวว่าค่ายช้าง และเกือบทุกปางในหุบเขาแม่แตง แม่วาง แม่แจ่ม เคยเป็นหรือสืบจากค่ายทำไม้ก่อนปิดป่าสัมปทานปี 2532 — หลังจากนั้นช้างกับควาญต้องหางานใหม่ และงานใหม่คือผู้มาเยือน",
            "ปางช้าง paang cháang — ปาง is a working camp pitched in the forest, the same word as the loggers' timber camps, so a pang chang is literally an elephant camp. Tradition holds that most of the camps in the Mae Taeng, Mae Wang and Mae Chaem valleys are, or descend from, the logging camps that lost their work when the forests were closed to logging in 1989 — after which the elephants and their mahouts needed a new trade, and the new trade was visitors."),
         say("ลักษณนามของช้างเลี้ยงคือ เชือก — ช้างหนึ่งเชือก สองเชือก — ส่วนช้างป่านับเป็น ตัว: ภาษาจำไว้ว่าช้างเลี้ยงคือช้างที่มีเชือกผูก", "The classifier for a captive elephant is เชือก chʉ̂ak, “rope” — one rope, two ropes of elephants — while a wild one is counted in ตัว: the language remembers that a kept elephant is an elephant with a rope on it."))
    card("ควาญ ตะขอ และคำถามที่ถามได้", "The mahout, the hook, and the questions you may ask",
         bi("ควาญช้าง (khwaan cháang) คือคนประจำช้างหนึ่งเชือก มักเป็นคนเดียวกันนานหลายปี หลายปางบอกเองว่าช้างแต่ละเชือกมีควาญประจำ — ตะขอ หรือ ขอช้าง (khɔ̌ɔ) คือเครื่องมือโลหะปลายงอที่ควาญถือ ปางที่ไม่ใช้จะประกาศเอง ปางที่ใช้มักไม่พูดถึง ถามได้ตรง ๆ ว่าใช้ไหม และกลางคืนช้างอยู่ที่ไหน ล่ามไหม — คำตอบเป็นของปาง มดแค่จด",
            "The ควาญ khwaan is the person assigned to one elephant, often the same person for years; several camps say on their own sites that each elephant has its own mahout. The ตะขอ / ขอช้าง khɔ̌ɔ is the curved metal hook a mahout carries; camps that do not use one say so, camps that do rarely mention it. Both are fair questions at the gate — do the mahouts carry a hook, and where are the elephants at night, and are they chained. The answer is the camp's; the ants only write it down."),
         say("ในภาคเหนือ ชุมชนกะเหรี่ยง (ปกาเกอะญอ) แม่วาง แม่แจ่ม อมก๋อย เลี้ยงช้างมาหลายชั่วคน หลายปางในทะเบียนบอกเองว่าเป็นของครอบครัวกะเหรี่ยง — คำว่าหมอช้าง (mɔ̌ɔ cháang) คือผู้รู้วิชาช้าง ผู้ทำพิธีให้ช้าง อ่านต่อที่ wichaa", "In the north the Karen (Pgakenyaw) communities of Mae Wang, Mae Chaem and Omkoi have kept elephants for generations, and several camps in the register describe themselves as Karen family camps. A หมอช้าง mɔ̌ɔ cháang is an elephant-master, the keeper of the elephant lore and the rites — which continues on wichaa, below."))
    card("ช้างเผือก — ไม่ใช่ช้างสีขาว", "The white elephant — not a white elephant",
         bi("ช้างเผือก (cháang phʉ̀ak; เผือก = เผือก/ด่าง สีจาง) ไม่ใช่ช้างตัวขาว แต่คือช้างที่มีลักษณะตามตำราคชลักษณ์ — ตามตำราเล่าว่าดูที่ตาขาว เพดานปากขาว เล็บขาว ขนขาว ผิวสีหม้อใหม่ ขนหางขาว และอีกหนึ่ง รวมเจ็ด — ช้างเผือกเป็นของหลวงตามประเพณี เป็นสัตว์ประจำชาติ และเคยอยู่บนธงชาติ (ธงช้างเผือก ก่อน 2460)",
            "A ช้างเผือก cháang phʉ̀ak (เผือก, pale, as in the taro root) is not a white-coloured elephant but one that carries the marks the elephant treatises describe — tradition holds they are read in the eyes, the palate, the nails, the hair, a skin the colour of new clay, the tail hair, and one more, seven in all. By custom a white elephant belongs to the king; it is the national animal, and it stood on the national flag until 1917."),
         say("ตามตำนาน — ช้างเผือกเชือกที่เลือกที่ตั้งพระธาตุดอยสุเทพ (พ.ศ. 1926) และอนุสาวรีย์ช้างเผือกคู่หน้าประตูเหนือ คือเหตุที่เมืองนี้มีประตู ย่าน ตลาด โรงพยาบาล และถนนชื่อช้างเผือก — ตำราดูลักษณะช้าง (ลักขณะช้าง) มีจริงในใบลานล้านนา อ่านที่ wichaa", "Tradition holds that the white elephant that chose the place for the Doi Suthep relic (1383), and the twin white elephants outside the north gate, are why this city has a gate, a quarter, a market, a hospital and a road called Chang Phueak — and a treatise on reading an elephant's marks (ลักขณะช้าง) survives on Lanna palm leaf; read it at wichaa."))
    card("เงิน — ราคาที่ประกาศ ไม่ใช่ราคาที่จ่าย", "Money — posted, not yet paid",
         bi(f"ในทะเบียนมี {len(posted)} ปางที่ประกาศราคาบนเว็บของตัวเอง: ค่าเข้าอย่างเดียวมีตั้งแต่ 300 บาท (แม่สา) ครึ่งวันราว 1,700 ขึ้นไป เต็มวันราว 2,400–3,500 และโปรแกรมหลายวันหรือรายสัปดาห์ 5,000 ถึง 15,000 บาท — ทุกตัวเลขคือ “ตามที่ประกาศ” มีที่มาและวันที่อ่านกำกับ และยังไม่มีใครเอาไปเทียบกับป้ายหน้าปาง",
            f"{len(posted)} camps in the register post prices on their own sites: admission alone from 300 baht (Mae Sa), half-days from about 1,700, full days about 2,400–3,500, and multi-day or weekly programs 5,000 to 15,000 baht — every figure is “as posted”, carries its source and the date it was read, and none has yet been checked against a board at a gate."),
         bi("ราคาปกติรวมรถรับจากในเมือง อาหารกลางวัน และเสื้อควาญ — “รถรับฟรี” คือค่าใช้จ่ายที่อยู่ในราคาแล้ว ไม่ผิดอะไร แค่รู้ไว้ จองตรงกับปางทาง LINE หรือ WhatsApp มักได้ราคาเดียวกับที่ประกาศ · ถ้าคุณจ่ายไปเท่าไหร่ บอกมดได้",
            "The price normally folds in the pickup from town, lunch and the mahout shirt — a “free pickup” is a cost already inside the number, nothing wrong with it, just know it; booking straight with the camp by LINE or WhatsApp usually gets the posted price. If you paid, tell the ants what."))
    card("ถามที่ประตู — ห้าคำถาม", "At the gate — five questions",
         bi("1 มีขี่ช้างไหม ถ้ามี หลังเปล่าหรือแหย่ง · 2 ควาญใช้ตะขอไหม · 3 กลางคืนช้างอยู่ไหน ล่ามไหม · 4 มีสัตวแพทย์ไหม · 5 ขอดูตั๋วรูปพรรณได้ไหม — ถามอย่างสุภาพ คำตอบคือข้อมูลของปาง ไม่ใช่ข้อสอบ และคนที่ตอบคือคนที่อยู่กับช้างทุกวัน",
            "1 Is there riding, and if so bareback or with a chair · 2 Do the mahouts carry a hook · 3 Where are the elephants at night, and are they chained · 4 Is there a vet · 5 May I see the registration papers — asked politely; the answers are the camp's own information, not an exam, and the person answering is the one who is with the elephants every day."),
         say("มดแดงจดคำตอบที่ปางประกาศไว้ (ตารางด้านบน) และเจ้าของปางติ๊กเองได้ที่หน้าของตัวเอง — ไม่มีใครติ๊กแทนปาง และหน้านี้ไม่ให้คะแนนสวัสดิภาพใคร", "The ants write down what a camp has stated (the register above) and a camp's owner can tick the facts on their own page — nobody ticks on a camp's behalf, and this page scores nobody's welfare."))
    card("คำที่จะได้ยิน", "Words you will hear",
         '<ul class="ch-words">'
         + "".join(f"<li>{bi(th, en)}</li>" for th, en in [
             ("ช้าง (cháang) — ช้าง", "chang (ช้าง, cháang) — elephant; คช khót and หัตถี hàt-thǐi in the old words"),
             ("ปางช้าง (paang cháang) — ค่ายช้าง", "pang chang (ปางช้าง, paang cháang) — elephant camp; ปาง, a forest work-camp"),
             ("ควาญ (khwaan) — คนประจำช้าง", "khwan (ควาญ, khwaan) — mahout"),
             ("ตะขอ / ขอ (khɔ̌ɔ) — ขอช้าง", "kho (ตะขอ, khɔ̌ɔ) — the hook"),
             ("โขลง (khlǒong) — ฝูงช้าง", "khlong (โขลง, khlǒong) — a herd"),
             ("พลาย (phlaai) — ช้างตัวผู้ · พัง (phang) — ตัวเมีย", "phlai (พลาย, phlaai) — a bull · phang (พัง, phang) — a cow"),
             ("สีดอ (sǐi-dɔɔ) — ตัวผู้ไม่มีงา", "sido (สีดอ, sǐi-dɔɔ) — a tuskless bull"),
             ("งา (ngaa) — งาช้าง · งวง (nguang) — งวง", "nga (งา, ngaa) — tusk · nguang (งวง, nguang) — trunk"),
             ("ตกมัน (tòk man) — ช้างตกมัน", "tok man (ตกมัน, tòk man) — musth; keep your distance"),
             ("เชือก (chʉ̂ak) — ลักษณนามช้างเลี้ยง", "chueak (เชือก, chʉ̂ak) — the classifier for a kept elephant, literally “rope”"),
             ("ช้างเผือก (cháang phʉ̀ak) — ช้างลักษณะดี", "chang phueak (ช้างเผือก, cháang phʉ̀ak) — the white elephant"),
             ("ช้างต้น (cháang tôn) — ช้างหลวง", "chang ton (ช้างต้น, cháang tôn) — a royal elephant"),
             ("หมอช้าง (mɔ̌ɔ cháang) — ผู้รู้วิชาช้าง", "mo chang (หมอช้าง, mɔ̌ɔ cháang) — the elephant-master, keeper of the lore"),
             ("สู่ขวัญช้าง (sùu khwǎn cháang) — พิธีเรียกขวัญช้าง", "su khwan chang (สู่ขวัญช้าง) — the khwan rite for an elephant"),
             ("ตั๋วรูปพรรณ (tǔa rûup-phá-phan) — ใบทะเบียนช้าง", "tua ruppaphan (ตั๋วรูปพรรณ) — the elephant's registration paper"),
         ]) + "</ul>",
         say("รากศัพท์: ช้าง เป็นคำไท (ลาว ຊ້າງ ไทใหญ่ ၸၢင်ႉ) · คช ← สันสกฤต gaja · หัตถี ← บาลี hatthī (hattha = มือ — สัตว์ที่มีมือ) · กุญชร ← kuñjara · ไอยรา/เอราวัณ ← Airāvata ช้างของพระอินทร์ — ตามรากไปต่อได้ที่ wichaa.net/thairoots", "Roots: ช้าง is a Tai word (Lao ຊ້າງ, Shan ၸၢင်ႉ) · คช ← Sanskrit gaja · หัตถี ← Pali hatthī (hattha, a hand — the animal with a hand) · กุญชร ← kuñjara · ไอยรา / เอราวัณ ← Airāvata, Indra's elephant — follow the roots at wichaa.net/thairoots"))
    card("วันในปฏิทิน และลำปาง", "A day in the calendar, and Lampang",
         bi("13 มีนาคม — วันช้างไทย มติคณะรัฐมนตรี 26 พ.ค. 2541 ระลึกวันที่ช้างเผือกได้เป็นสัตว์ประจำชาติ (13 มี.ค. 2506 ตามที่เล่ากัน) ปางทำบุญให้ช้าง เลี้ยงผลไม้ บางแห่งสู่ขวัญช้าง — งานหลักที่ศูนย์อนุรักษ์ช้างไทย ห้างฉัตร ลำปาง ซึ่งเป็นที่ตั้งสถาบันคชบาลแห่งชาติ โรงพยาบาลช้างลำปาง และโรงพยาบาลช้างแห่งแรกของโลก (มูลนิธิเพื่อนช้าง) ห่างเชียงใหม่ราวชั่วโมงครึ่ง",
            "13 March — Thai Elephant Day, by a 1998 Cabinet resolution, recalling (it is told) the day the white elephant became the national animal in 1963: camps make merit for their elephants and lay out fruit, some hold a su khwan — the main event is at the Thai Elephant Conservation Center at Hang Chat, Lampang, which is also the National Elephant Institute, the Lampang elephant hospital, and the first elephant hospital in the world (Friends of the Asian Elephant), about an hour and a half from Chiang Mai."),
         f'<a href="festivals.html">{bi("อยู่ในปฏิทินเทศกาล", "On the festivals page")} →</a>')
    primer_html = f'<div class="ch-grid">{"".join(P)}</div>'

    joins_html = (f'<div class="ch-joins"><b>{bi("ไปต่อที่ wichaa", "Onward, on wichaa")}</b>'
                  f'<p><a href="https://wichaa.net/a/entity_chang/" rel="noopener">wichaa.net/a/entity_chang/</a> — '
                  + bi("ช้างในใบลานล้านนา: ตำราลักขณะช้างของน่าน สู่ขวัญช้างสองฉบับ ชาดกช้างฉัททันต์หกงา ช้างเผือกในชาดกพื้นบ้าน และคาถา-ยันต์ที่ใช้ช้างเป็นรูป — ที่ซึ่งคำถาม “ช้างเชือกนี้มีลักษณะอะไร” เคยมีตำราตอบ",
                       "the elephant on Lanna palm leaf: a Nan treatise on reading an elephant's marks, two su khwan rites for elephants, the six-tusked Chaddanta jataka, white elephants in the local jatakas, and the kathas and yants that take the elephant as their figure — where the question “what are this elephant's marks” once had a treatise to answer it")
                  + f'</p><p><a href="https://wichaa.net/a/entity_su_khwan/" rel="noopener">wichaa.net/a/entity_su_khwan/</a> — '
                  + bi("พิธีสู่ขวัญที่ปางทำให้ช้างในวันช้างไทย คือพิธีเดียวกับที่ทำให้คน — สายและเหตุผลของมัน",
                       "the su khwan a camp holds for its elephants on 13 March is the same rite held for people — its lineage and its reasons")
                  + f'</p><p><a href="https://wichaa.net/a/entity_vessantara/" rel="noopener">wichaa.net/a/entity_vessantara/</a> — '
                  + bi("มหาชาติ: ช้างเผือกปัจจัยนาเคนทร์ที่พระเวสสันดรให้ทานจนถูกเนรเทศ — เรื่องที่ทุกวัดในล้านนาเทศน์ทุกปี และเหตุที่ช้างเผือกคือฝน",
                       "the Great Birth: the white elephant Paccaya whose giving-away sent Vessantara into exile — the story every Lanna temple preaches each year, and why a white elephant is rain")
                  + f'</p><p><a href="https://wichaa.net/thairoots" rel="noopener">wichaa.net/thairoots</a> — '
                  + bi("รากศัพท์ไทย สำหรับคนที่อยากรู้ว่า ช้าง คช หัตถี และควาญ มาจากไหน",
                       "Thai roots, for whoever wants to know where chang, khot, hatthi and khwan come from")
                  + "</p></div>")

    # ---- assemble ---------------------------------------------------------
    intro = bi("หน้านี้มีสามอย่าง: ทะเบียนว่าแต่ละปางบอกเองอย่างไรเรื่องขี่ช้าง อาบน้ำ โชว์ และการดูอย่างเดียว (ปางบอก มดจดพร้อมที่มา) ชั้นปางช้างและคลินิกที่สารบัญมี และเรื่องที่ควรรู้ก่อนไป — กฎหมายสองฉบับ องค์กรที่ออกใบรับรอง ชื่อในเมืองที่มีช้างอยู่ และคำศัพท์ — เขียนจากข้าง ๆ ช้าง ไม่ได้จัดอันดับว่าปางไหนดีกว่ากัน คำว่า sanctuary เป็นของปางที่พูด",
               "Three things on one page: a register of what each camp states for itself about riding, bathing, shows and hands-off (the camp states it; the ants write it down with the source), the shelf of camps and the clinic the directory holds, and what to know before you go — the two laws, the bodies that certify, the names in this city that carry the elephant, and the words — written from beside an elephant, with no ranking of camps against each other. The word sanctuary belongs to whoever says it.")
    rule_html = ('<div class="ch-rule"><b>🐘 ' + bi("กติกาของหน้านี้", "The rule of this page") + '</b>'
                 + bi("ปางบอกเองว่ามีอะไร — หรือหน้านี้บอกว่ายังไม่มีใครบอก · กฎหมายบอกว่าอะไรขึ้นทะเบียน · หน้านี้ไม่ตัดสินว่าปางไหนมีจริยธรรม ปางไหนไม่มี เพราะคำตัดสินผิดเพียงครั้งเดียวคือการใส่ร้ายครอบครัวหนึ่งหรือการส่งคนไปที่ใดที่หนึ่งด้วยความมั่นใจผิด ๆ — ทั้งสองอย่างเป็นคำพูดถึงธุรกิจที่มีชื่อ ในขนาดของเว็บนี้", "The camp states what happens — or this page says nobody has stated it · the law says what is registered · this page does not judge which camp is ethical and which is not, because one wrong verdict either slanders a family or sends a reader somewhere under false comfort — and both are statements about a named business, at this site's scale.") + '</div>')
    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "ปางช้างเชียงใหม่ — Elephant camps and sanctuaries, Chiang Mai: what each states",
        "url": BASE + "chang.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "TouristAttraction", "name": v.get("name_en"),
                      **({"url": BASE + href(by_id[v["place"]])} if v["place"] in by_id else {})}}
            for i, v in enumerate(venues)],
    }
    head = ('<link rel="stylesheet" href="chang.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "chang") if shelf_og else None
    body = (
        f'<h1>🐘 {bi("ช้าง — ปางไหนบอกว่าอะไร ชั้นปางช้าง และเรื่องที่ควรรู้ก่อนไป", "Elephants — what each camp states, the shelf, what to know before you go")}</h1>'
        f'<p class="ch-intro">{intro}</p>'
        f'{rule_html}'
        f'<h2>{bi("ทะเบียน — ปางบอกเองว่าอะไร", "The register — what each camp states")}</h2>'
        f'{reg_html}{venues_html}{unr_html}{unc_html}{norow_html}{cr_html}'
        f'<h2>{bi("ชั้นช้าง — ปาง คลินิก และของช้าง", "The elephant shelf — camps, the clinic, the craft")}</h2>'
        f'{shelf_html}'
        f'<h3>{bi("ปางช้างในสารบัญ", "Camps in the directory")} <span class="count">({len(camp_rows)})</span></h3>'
        f'<p class="ch-note">{bi("เรียงตามชื่อ ไม่จัดอันดับ — ☎ LINE WA 🌐 คือช่องทางที่สารบัญมี", "Alphabetical, unranked — ☎ LINE WA 🌐 mark the channels the directory holds")}</p>'
        f'{camps_html}'
        f'<h2>{bi("กฎหมายสองฉบับ และองค์กรที่ออกใบรับรอง", "Two laws, and the bodies that certify")}</h2>'
        f'{law_html}'
        f'<div class="ch-grid">{lp_html}</div>'
        '<h2>' + bi("ช้างในชื่อเมือง — ประตู วัด ย่าน ดอย", "The elephant in the city's names — a gate, temples, quarters, a mountain") + '</h2>'
        f'{land_html}'
        f'<h3>{bi("ทุกระเบียนที่มีช้างในชื่อ", "Every record with the elephant in its name")}</h3>'
        f'{names_html}'
        f'<h2>{bi("ก่อนไปปาง — เรื่องที่ควรรู้", "Before you go — what you are looking at")}</h2>'
        f'{primer_html}{joins_html}'
        f'<p class="ch-note">{bi("ที่มาของทะเบียน", "Register data")}: <a href="data/elephants.json">data/elephants.json</a> · '
        f'{bi("วันช้างไทยอยู่ในปฏิทินเทศกาล", "Thai Elephant Day is on the festivals page")} → <a href="festivals.html">festivals.html</a></p>'
        f'{share_block(BASE + "chang.html", "ช้าง ปางไหนบอกว่าอะไร · มดแดง", card=og)}')
    (DOCS / "chang.html").write_text(page(
        "ช้าง — ปางช้างเชียงใหม่ บอกเองว่าอะไร · Elephant camps, Chiang Mai — what each states",
        body, depth=0, path="chang.html",
        desc="ทะเบียนปางช้างเชียงใหม่: แต่ละปางบอกเองว่ามีขี่ช้างไหม อาบน้ำไหม โชว์ไหม ดูอย่างเดียวได้ไหม ราคาที่ประกาศ กฎหมาย องค์กรรับรอง ชื่อในเมืองที่มีช้าง และเรื่องที่ควรรู้ก่อนไป · Elephant camps in Chiang Mai: what each states about riding, bathing, shows and hands-off, posted prices, the law, the certifying bodies, the city's elephant names, and what to know before you go",
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("ช้าง", "Elephants")}'))
    return {"page": 1, "venues": len(venues), "no_riding_stated": n_no_ride,
            "riding_unstated": n_unstated_ride, "camps": len(camp_rows), "on_shelf": n_all,
            "named": len(named)}
