#!/usr/bin/env python3
"""The graded-register page, made a layer — one renderer, many lenses. WO-56+.

care.html, trans-health.html, adhd.html, longcare.html and ot.html are the
same page five times: a question the corpus cannot answer by name, a
register read from each institution's own site, a GRADE on every row
naming who is speaking, a glossary of the words on the doors, and a table
of what was not read. Each was written as its own module; the sixth would
have been a copy of the fifth. So the shape is data now: one JSON per lens
in data/curated/lens/, this file draws it, build.py loops over them, and
the index takes its keywords from the same file (the one-source rule).

THE RULE does not change by being generic. `stated` is the place's own
words on its own site or poster, with the sentence, the url and the date.
`listed` is a dated third-party directory row and says so. `route` is the
door this care ordinarily runs through, whose own page was read and does
NOT say the word. No rankings, no named clinicians, no outcome claims, no
medical advice, no price the page did not read. A licence is a register
row, never a rating. Absent is silence, never a 'no'. And a page is a
record, not a pamphlet (WO-52): the prose is the census, the rows, the
registers and the words on the doors.

Lens JSON (see data/curated/lens/README.md):
  key · glyph · nav [th, en] · title [th, en] · h1 [th, en] · desc [th, en]
  intro [th, en] · sections [[key, th, en]…] · for {key: [th, en]}
  census [[label_th, label_en, regex]…]  counted LIVE over names
  rows [ {key, section, for[], grade, name_th, name_en, placeIds[], site,
          phone, hours, note_th, note_en, evidence, src, fetched} ]
  registers [ {key, th, en, url, note_th, note_en, fetched} ]
  glossary [[th, rtgs, en]…] · unread [ {name, ref, reason} ]
  links [[href, th, en]…] · index {"base": words, "for": {key: words}}
  panel {…a search_panels.json panel…} · thesaurus [[…]…]
"""
import json
import re

CSS = """
:root{--ln-ink:#3a2f28;--ln-line:#e4d9cd;--ln-tint:#fbf6f0;
--ln-state:#2f6b46;--ln-list:#7a5c1e;--ln-route:#4a5a8a;--ln-quiet:#8a7a62}
.ln-intro{font-size:1.05rem;line-height:1.65;max-width:62ch}
.ln-h{margin:1.9rem 0 .35rem}
.ln-note{color:var(--ln-quiet);font-size:.92rem;line-height:1.6;max-width:64ch}
.ln-card{border:1px solid var(--ln-line);border-radius:.85rem;padding:.85rem 1rem 1rem;
margin:.9rem 0;background:var(--ln-tint)}
.ln-card h3{margin:.1rem 0 .15rem;font-size:1.12rem}
.ln-where{color:var(--ln-quiet);font-size:.9rem;margin:0 0 .35rem}
.ln-where a{color:inherit}
.ln-tag{display:inline-block;font-size:.76rem;letter-spacing:.03em;text-transform:uppercase;
border:1px solid var(--ln-line);border-radius:.6rem;padding:.05rem .45rem;
background:#fff;margin-left:.35rem;vertical-align:.12em;color:var(--ln-state)}
.ln-tag.listed{color:var(--ln-list)}
.ln-tag.route{color:var(--ln-route)}
.ln-for{display:inline-block;font-size:.78rem;border-radius:.6rem;padding:.05rem .5rem;
background:#fff;border:1px solid var(--ln-line);margin:0 .25rem .25rem 0;color:var(--ln-ink)}
.ln-hours{display:block;font-size:.95rem;margin:.25rem 0}
.ln-said{display:block;color:var(--ln-quiet);font-size:.86rem;line-height:1.5;
margin-top:.3rem;border-left:2px solid var(--ln-line);padding-left:.55rem}
.ln-dead{text-decoration:underline dotted;text-underline-offset:.18em;opacity:.72;cursor:help}
.ln-tablewrap{overflow-x:auto}
table.ln-tab{border-collapse:collapse;width:100%;font-size:.94rem;min-width:30rem}
table.ln-tab th,table.ln-tab td{border-bottom:1px solid var(--ln-line);
padding:.45rem .6rem;text-align:left;vertical-align:top}
table.ln-tab thead th{border-bottom:2px solid var(--ln-line);white-space:nowrap}
table.ln-gloss td.th{font-size:1.05rem;white-space:nowrap}
table.ln-gloss td.rtgs{color:var(--ln-quiet);font-style:italic;white-space:nowrap}
"""

GRADE_LABEL = {
    "stated": ("บอกเอง", "stated"),
    "listed": ("ตามสารบัญ", "listed"),
    "route": ("ทางที่ใช้ประจำ", "the usual route"),
}
GRADE_ORDER = {"stated": 0, "listed": 1, "route": 2}


def load_all(ROOT):
    """Every lens, by key, in file order — the one list build.py loops over."""
    d = ROOT / "data" / "curated" / "lens"
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        lens = json.loads(p.read_text(encoding="utf-8"))
        if lens.get("draft"):
            continue
        out.append(lens)
    return out


def rows_by_place(lenses):
    """placeId -> [(lens, row), …], for the index keywords.

    A LIST, not one pair. WO-63: Maharaj (Suan Dok) sits in the vaccines
    register and the skin register, and with one slot per place the last
    lens in file order silently won — the hospital whose own page states a
    dermatology clinic could not be found by "rosacea" because it was the
    yellow-fever centre first. Every register a place is in gets its words in.
    """
    out = {}
    for lens in lenses:
        for row in lens.get("rows", []):
            for pid in row.get("placeIds") or []:
                out.setdefault(pid, []).append((lens, row))
    return out


def index_words(lens, row):
    """The words a place answers because of this register — only grades
    stated and listed; a route hospital nobody has confirmed must not
    answer the question as if it had said yes."""
    if row.get("grade") not in ("stated", "listed"):
        return ""
    idx = lens.get("index") or {}
    words = [idx.get("base", "")]
    for f in row.get("for") or []:
        words.append((idx.get("for") or {}).get(f, ""))
    return " ".join(w for w in words if w)


def emit(g, data, lens):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug = g["place_slug"]
    BASE, DOCS, ROOT = g["BASE"], g["DOCS"], g["ROOT"]
    share_block = g["share_block"]
    PROVINCES = g["PROVINCES"]
    name_of = g["name_of"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")
    verdict, BROKEN = g["verdict"], g["BROKEN"]
    BROKEN_WHY = g["BROKEN_WHY"]
    LINK_HEALTH_DATE = g.get("LINK_HEALTH_DATE") or ""

    key = lens["key"]
    FOR = {k: tuple(v) for k, v in (lens.get("for") or {}).items()}

    def site_a(url, label=None):
        url = (url or "").strip()
        if not url:
            return ""
        v = verdict(url)
        st = v.get("status")
        text = esc(label or url[:48])
        if st not in BROKEN:
            return f'<a href="{att(url)}" rel="noopener nofollow">{text}</a>'
        why_th, why_en = BROKEN_WHY.get(
            st, ("เปิดไม่ได้", "the link could not be opened"))
        when = v.get("checkedAt") or LINK_HEALTH_DATE
        tip = url + " — " + bi_text(
            why_th + " ตรวจเมื่อ " + when, why_en + ", checked " + when)
        return f'<span class="ln-dead" title="{att(tip)}">{text}</span>'

    (DOCS / "lens.css").write_text(CSS)

    byid = {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            byid[r["id"]] = (p["key"], r)

    def names(r):
        return " ".join(str(r.get(k) or "") for k in ("name", "nameTh", "nameEn"))

    # The census, counted live over every name so the sentence and the
    # catalogue cannot disagree. Crawled names only: a curated addition
    # that says the word was put there by this register.
    census_bits = []
    for lab_th, lab_en, rx in lens.get("census") or []:
        cre = re.compile(rx, re.I)
        n = sum(1 for _, r in byid.values()
                if cre.search(names(r)) and "-curated-" not in r["id"])
        census_bits.append((lab_th, lab_en, n))
    n_all = len(byid)
    census = ""
    if census_bits:
        th = " · ".join(f"{a} {n}" for a, _, n in census_bits)
        en = " · ".join(f"{b} {n}" for _, b, n in census_bits)
        census = bi(
            f"นับตรง ๆ ในระเบียน {n_all:,} แห่งของสองจังหวัด ชื่อจากการสำรวจแผนที่ที่เขียนคำเหล่านี้: {th}",
            f"Counted plainly across {n_all:,} records in both provinces, crawled names carrying these words: {en}")

    def place_link(ids):
        for pid in ids or []:
            hit = byid.get(pid)
            if hit:
                k, r = hit
                return f'<a href="{att(k)}/p/{att(place_slug(r))}.html">{esc(name_of(r))}</a>'
        return ""

    def card(row):
        th_g, en_g = GRADE_LABEL.get(row["grade"], (row["grade"], row["grade"]))
        tag = f'<span class="ln-tag {att(row["grade"])}">{bi(th_g, en_g)}</span>'
        pills = "".join(
            f'<span class="ln-for">{bi(*FOR[f])}</span>'
            for f in row.get("for", []) if f in FOR)
        link = place_link(row.get("placeIds"))
        site = site_a(row.get("site"))
        phone = ""
        if row.get("phone"):
            tel = re.sub(r"[^\d+]", "", row["phone"].split("ต่อ")[0])
            phone = f'<a href="tel:{att(tel)}">☎ {esc(row["phone"])}</a>'
        where = " · ".join(x for x in (link, phone, site) if x)
        hours = (f'<span class="ln-hours">🕐 {esc(row["hours"])}</span>'
                 if row.get("hours") else "")
        ev = row.get("evidence", "")
        said = (f'<span class="ln-said">{bi(row.get("note_th", ""), row.get("note_en", ""))}'
                + (f'<br>“{esc(ev)}”' if ev else "")
                + f' — {esc(row.get("src", ""))} · {esc(row.get("fetched", ""))}</span>')
        return (f'<section class="ln-card"><h3>{bi(row["name_th"], row["name_en"])}{tag}</h3>'
                + (f'<p class="ln-where">{pills}</p>' if pills else "")
                + f'<p class="ln-where">{where}</p>{hours}{said}</section>')

    rows = lens.get("rows", [])
    section_html = []
    for skey, sth, sen in lens.get("sections") or []:
        srows = sorted([r for r in rows if r.get("section") == skey],
                       key=lambda r: (GRADE_ORDER.get(r["grade"], 9), r["name_th"]))
        if not srows:
            continue
        n_st = sum(1 for r in srows if r["grade"] == "stated")
        head = (f'<h2 class="ln-h">{bi(sth, sen)} '
                f'<span class="count">({len(srows)})</span></h2>'
                f'<p class="ln-note">{bi(f"บอกเอง {n_st} แห่ง — ที่เหลือคือคำของสารบัญหรือประตูที่ใช้ประจำ ไม่ใช่คำของสถานที่", f"{n_st} stated in their own words; the rest are a directory’s word or the usual door, not the place’s own.")}</p>')
        section_html.append(head + "".join(card(r) for r in srows))

    registers = lens.get("registers") or []
    reg_html = ""
    if registers:
        reg_rows = "".join(
            f'<tr><td>{bi(x["th"], x["en"])}</td>'
            f'<td>{site_a(x.get("url"), x.get("url", "")[:40])}</td>'
            f'<td>{bi(x.get("note_th", ""), x.get("note_en", ""))} '
            f'<span class="ln-note">· {esc(x.get("fetched", ""))}</span></td></tr>'
            for x in registers)
        reg_html = (
            f'<h2 class="ln-h">{bi("ทะเบียนและประตูของรัฐ", "Registers and official doors")}</h2>'
            f'<p class="ln-note">{bi("ใบอนุญาตคือแถวในทะเบียน ไม่ใช่คะแนน — ตรวจชื่อได้", "A licence is a register row, not a rating — a name can be checked.")}</p>'
            f'<div class="ln-tablewrap"><table class="ln-tab"><thead><tr>'
            f'<th>{bi("อะไร", "What")}</th><th>{bi("ที่ไหน", "Where")}</th><th>{bi("บอกว่า", "What it states")}</th>'
            f'</tr></thead><tbody>{reg_rows}</tbody></table></div>')

    unread = lens.get("unread") or []
    unread_html = ""
    if unread:
        un_rows = "".join(
            f'<tr><td>{esc(u["name"])}</td><td>{esc(u.get("ref", ""))}</td>'
            f'<td>{esc(u["reason"])}</td></tr>' for u in unread)
        unread_html = (
            f'<h2 class="ln-h">{bi("ยังไม่ได้อ่าน — บอกไว้ตรง ๆ", "Not read yet — said plainly")} '
            f'<span class="count">({len(unread)})</span></h2>'
            f'<p class="ln-note">{bi("ชื่อที่รู้ว่ามีแต่ยังไม่มีใครอ่านหน้าของมันเอง และชื่อที่อ่านแล้วต้องตัดออก พร้อมเหตุผล", "Names known to exist whose own page nobody has read, and names read and refused, each with the reason.")}</p>'
            f'<div class="ln-tablewrap"><table class="ln-tab"><thead><tr>'
            f'<th>{bi("ชื่อ", "Name")}</th><th>{bi("อ้างอิง", "Ref")}</th>'
            f'<th>{bi("ทำไม", "Why")}</th>'
            f'</tr></thead><tbody>{un_rows}</tbody></table></div>')

    glossary = lens.get("glossary") or []
    gloss_html = ""
    if glossary:
        gl_rows = "".join(
            f'<tr><td class="th">{esc(th)}</td><td class="rtgs">{esc(rtgs)}</td>'
            f'<td>{esc(en)}</td></tr>' for th, rtgs, en in glossary)
        gloss_html = (
            f'<h2 class="ln-h">{bi("คำบนป้ายพวกนี้", "The words on these signs")}</h2>'
            f'<p class="ln-note">{bi("อักษรไทย · คำอ่านแบบ RTGS · ความหมายและรากศัพท์", "Thai script · RTGS · the meaning and the root.")}</p>'
            f'<div class="ln-tablewrap">'
            f'<table class="ln-tab ln-gloss"><tbody>{gl_rows}</tbody></table></div>')

    links = " · ".join(
        f'<a href="{att(h)}">{bi(th, en)}</a>' for h, th, en in (lens.get("links") or []))

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": f'{lens["title"][0]} — {lens["title"][1]}',
        "url": BASE + f"{key}.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "MedicalOrganization", "name": r["name_en"],
                      **({"url": r["site"]}
                         if r.get("site")
                         and verdict(r["site"]).get("status") not in BROKEN
                         else {})}}
            for i, r in enumerate(rows)],
    }
    head = ('<link rel="stylesheet" href="lens.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", lens.get("og_shelf", "medical")) if shelf_og else None

    body = (
        f'<h1>{bi(*lens["h1"])}</h1>'
        f'<p class="ln-intro">{bi(*lens["intro"])}</p>'
        + (f'<p class="ln-note">{census}</p>' if census else "")
        + "".join(section_html)
        + reg_html + gloss_html + unread_html
        + f'<p class="ln-note">{bi("มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ และไม่ใช่การรับรองคุณภาพ ข้อมูลบางส่วนมาจาก OpenStreetMap (ODbL 1.0)", "Mot Dang is a directory of places. It is not medical advice, not a referral, and not a quality guarantee. Some facility data is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap contributors.")}</p>'
        + (f'<p class="ln-note">{links}</p>' if links else "")
        + share_block(BASE + f"{key}.html", f'{lens["title"][0]} · มดแดง', card=og))

    (DOCS / f"{key}.html").write_text(page(
        f'{lens["title"][0]} · {lens["title"][1]}',
        body, depth=0, path=f"{key}.html",
        desc=bi_text(*lens["desc"]), extra_head=head, og=og))
    n_by = {}
    for r in rows:
        n_by[r["grade"]] = n_by.get(r["grade"], 0) + 1
    return (f"{key}: {len(rows)} rows ({' · '.join(f'{k} {v}' for k, v in sorted(n_by.items()))}), "
            f"{len(registers)} registers, {len(unread)} not read")
