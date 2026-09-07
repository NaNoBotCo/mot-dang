#!/usr/bin/env python3
"""/ot.html — กิจกรรมบำบัด, the occupational-therapy page. WO-55.

THE QUESTION people bring: a child whose development is slow, an adult
relearning a hand or a kitchen after a stroke, an elder whose memory is
going and who needs the house made safe. The answer in Thai is
กิจกรรมบำบัด — a licensed profession (ผู้ประกอบโรคศิลปะ สาขากิจกรรมบำบัด)
whose only school in the north is at Chiang Mai University, and whose
professional association is seated in this city.

WHAT THE CATALOGUE HELD when somebody counted (2026-09-04, both provinces,
21,047 records): ZERO names carry กิจกรรมบำบัด or 'occupational'. Three
names say physio. The physio child of the medical tree matches nothing,
because OSM holds no healthcare=physiotherapist in either province, so a
page this site had linked for a fortnight (cm/medical/physio/) had never
been built. The register in data/curated/ot.json was therefore read from
each institution's own site or own poster, with the sentence and the date.

THE RULE, same as care.html, adhd.html and longcare.html: the grade rides
every row. `stated` is the place's own words; `listed` is a dated
third-party directory row and says so; `route` is the door this care
ordinarily runs through, whose own page was read and does NOT say the
word. No rankings, no named clinicians, no outcome claims, no medical
advice, no price the page did not read. A licence is a register row,
never a rating. Absent is silence, never a 'no'.

A PAGE IS A RECORD, NOT A PAMPHLET (WO-52): the prose here is the census,
the rows, the registers and the words on the doors. Nothing that would be
true on twenty thousand pages.
"""
import json
import re

CSS = """
:root{--ot-ink:#3a2f28;--ot-line:#e4d9cd;--ot-tint:#fbf6f0;
--ot-state:#2f6b46;--ot-list:#7a5c1e;--ot-route:#4a5a8a;--ot-quiet:#8a7a62}
.ot-intro{font-size:1.05rem;line-height:1.65;max-width:62ch}
.ot-h{margin:1.9rem 0 .35rem}
.ot-note{color:var(--ot-quiet);font-size:.92rem;line-height:1.6;max-width:64ch}
.ot-card{border:1px solid var(--ot-line);border-radius:.85rem;padding:.85rem 1rem 1rem;
margin:.9rem 0;background:var(--ot-tint)}
.ot-card h3{margin:.1rem 0 .15rem;font-size:1.12rem}
.ot-where{color:var(--ot-quiet);font-size:.9rem;margin:0 0 .35rem}
.ot-where a{color:inherit}
.ot-tag{display:inline-block;font-size:.76rem;letter-spacing:.03em;text-transform:uppercase;
border:1px solid var(--ot-line);border-radius:.6rem;padding:.05rem .45rem;
background:#fff;margin-left:.35rem;vertical-align:.12em;color:var(--ot-state)}
.ot-tag.listed{color:var(--ot-list)}
.ot-tag.route{color:var(--ot-route)}
.ot-for{display:inline-block;font-size:.78rem;border-radius:.6rem;padding:.05rem .5rem;
background:#fff;border:1px solid var(--ot-line);margin:0 .25rem .25rem 0;color:var(--ot-ink)}
.ot-hours{display:block;font-size:.95rem;margin:.25rem 0}
.ot-said{display:block;color:var(--ot-quiet);font-size:.86rem;line-height:1.5;
margin-top:.3rem;border-left:2px solid var(--ot-line);padding-left:.55rem}
.ot-dead{text-decoration:underline dotted;text-underline-offset:.18em;opacity:.72;cursor:help}
.ot-tablewrap{overflow-x:auto}
table.ot-tab{border-collapse:collapse;width:100%;font-size:.94rem;min-width:30rem}
table.ot-tab th,table.ot-tab td{border-bottom:1px solid var(--ot-line);
padding:.45rem .6rem;text-align:left;vertical-align:top}
table.ot-tab thead th{border-bottom:2px solid var(--ot-line);white-space:nowrap}
table.ot-gloss td.th{font-size:1.05rem;white-space:nowrap}
table.ot-gloss td.rtgs{color:var(--ot-quiet);font-style:italic;white-space:nowrap}
"""

# Script · RTGS · what it means — the words on these doors, for a reader who
# cannot read the doors. Same instrument as care.html and longcare.html.
GLOSSARY = [
    ("กิจกรรมบำบัด", "kitchakam bambat", "occupational therapy — กิจกรรม activity "
     "· บำบัด to treat. Therapy THROUGH the activities of daily life, which "
     "is why the English word 'occupational' misleads: it is not about jobs."),
    ("นักกิจกรรมบำบัด", "nak kitchakam bambat", "an occupational therapist — "
     "นัก the person who does. A licensed ผู้ประกอบโรคศิลปะ; the register "
     "below is where a name is checked."),
    ("อาชีวบำบัด", "achiwa bambat", "the older word for the same profession "
     "(อาชีวะ occupation); still in the association's name."),
    ("เวชกรรมฟื้นฟู · เวชศาสตร์ฟื้นฟู", "wetchakam fuenfu · wetchasat fuenfu",
     "rehabilitation medicine — the hospital GROUP that OT, physio and "
     "prosthetics all sit inside. The corridor to ask for first."),
    ("กายภาพบำบัด", "kayaphap bambat", "physiotherapy — the neighbour "
     "profession, on the same corridor, often the same room. Movement and "
     "pain; OT is doing and living."),
    ("กายอุปกรณ์", "kaya upakon", "prosthetics and orthotics — braces, "
     "splints, artificial limbs; the third door in the rehab group."),
    ("กระตุ้นพัฒนาการ", "kratun phatthanakan", "developmental stimulation — "
     "the phrase on children's clinics' signs. พัฒนาการล่าช้า is delayed "
     "development."),
    ("บูรณาการประสาทความรู้สึก", "buranakan prasat khwam rusuek",
     "sensory integration (SI) — the paediatric OT approach parents arrive "
     "asking for by its English initials."),
    ("กิจวัตรประจำวัน", "kitchawat pracham wan", "activities of daily living "
     "(ADL) — dressing, eating, washing; the unit OT measures progress in."),
    ("ฝึกกลืน", "fuek kluen", "swallowing training — after a stroke; OT and "
     "speech therapy both do it here."),
    ("ฟื้นฟูหลอดเลือดสมอง", "fuenfu lot lueat samong", "stroke rehabilitation "
     "— literally 'brain blood-vessel recovery'; อัมพฤกษ์ hemiparesis, "
     "อัมพาต paralysis are the words beside it on the signs."),
    ("คลินิกพิเศษนอกเวลา · SMC", "khlinik phiset nok wela",
     "the after-hours special clinic — the same state therapists after "
     "16:00 for a posted fee. Chiang Rai's rehab group runs one for OT."),
    ("ผู้ประกอบโรคศิลปะ", "phu prakop rok sinla", "a Healing Arts practitioner — "
     "the licence class OT belongs to (with physio, psychology, Thai and "
     "Chinese medicine), under กรมสนับสนุนบริการสุขภาพ."),
]

GRADE_LABEL = {
    "stated": ("บอกเอง", "stated"),
    "listed": ("ตามสารบัญ", "listed"),
    "route": ("ทางที่ใช้ประจำ", "the usual route"),
}
GRADE_ORDER = {"stated": 0, "listed": 1, "route": 2}
FOR_LABEL = {
    "child": ("เด็ก-พัฒนาการ", "children & development"),
    "adult": ("ผู้ใหญ่-ผู้สูงอายุ-ฟื้นฟู", "adults, elders & rehab"),
}
SECTIONS = [
    ("cm", "เชียงใหม่", "Chiang Mai"),
    ("cr", "เชียงราย", "Chiang Rai"),
]

OT_NAME_RX = re.compile(r"กิจกรรมบำบัด|\boccupational\s+therap|\bOT\s+clinic\b", re.I)


def emit(g, data):
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

    def site_a(url, label=None):
        """A row's own site — or the address of one that has stopped
        answering (the WO-31 dead-ref rule: keeps its place, carries the
        verdict and the date, stops being a door)."""
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
        return f'<span class="ot-dead" title="{att(tip)}">{text}</span>'

    src = ROOT / "data" / "curated" / "ot.json"
    if not src.exists():
        return "ot.json missing — page not built"
    reg = json.loads(src.read_text(encoding="utf-8"))
    rows = reg.get("rows", [])
    registers = reg.get("registers", [])
    unread = reg.get("unread", [])

    (DOCS / "ot.css").write_text(CSS)

    byid = {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            byid[r["id"]] = (p["key"], r)

    # The census, counted LIVE so the sentence and the catalogue cannot
    # disagree: names that say the word, records carrying the specialty,
    # and the physio shelf that matches nothing.
    n_all = len(byid)
    n_name = sum(1 for _, r in byid.values()
                 if OT_NAME_RX.search(" ".join(str(r.get(k) or "") for k in
                                              ("name", "nameTh", "nameEn"))))
    n_spec = sum(1 for _, r in byid.values()
                 if "ot" in ((r.get("attrs") or {}).get("specialty") or []))
    n_physio_shelf = sum(1 for _, r in byid.values()
                         if (r.get("attrs") or {}).get("facilityType") == "physio")
    n_curated_names = sum(1 for _, r in byid.values()
                          if r["id"].startswith(("cm-curated", "cr-curated"))
                          and OT_NAME_RX.search(" ".join(str(r.get(k) or "") for k in
                                                        ("name", "nameTh", "nameEn"))))
    n_crawled_names = n_name - n_curated_names

    def place_link(ids):
        for pid in ids or []:
            hit = byid.get(pid)
            if hit:
                k, r = hit
                return f'<a href="{att(k)}/p/{att(place_slug(r))}.html">{esc(name_of(r))}</a>'
        return ""

    def card(row):
        th_g, en_g = GRADE_LABEL.get(row["grade"], (row["grade"], row["grade"]))
        tag = f'<span class="ot-tag {att(row["grade"])}">{bi(th_g, en_g)}</span>'
        pills = "".join(
            f'<span class="ot-for">{bi(*FOR_LABEL[f])}</span>'
            for f in row.get("for", []) if f in FOR_LABEL)
        link = place_link(row.get("placeIds"))
        site = site_a(row.get("site"))
        phone = ""
        if row.get("phone"):
            tel = re.sub(r"[^\d+]", "", row["phone"].split("ต่อ")[0])
            phone = f'<a href="tel:{att(tel)}">☎ {esc(row["phone"])}</a>'
        where = " · ".join(x for x in (link, phone, site) if x)
        hours = (f'<span class="ot-hours">🕐 {esc(row["hours"])}</span>'
                 if row.get("hours") else "")
        said = (f'<span class="ot-said">{bi(row.get("note_th", ""), row.get("note_en", ""))}'
                f'<br>“{esc(row.get("evidence", ""))}” — {esc(row.get("src", ""))} · '
                f'{esc(row.get("fetched", ""))}</span>')
        return (f'<section class="ot-card"><h3>{bi(row["name_th"], row["name_en"])}{tag}</h3>'
                f'<p class="ot-where">{pills}</p>'
                f'<p class="ot-where">{where}</p>{hours}{said}</section>')

    section_html = []
    for skey, sth, sen in SECTIONS:
        srows = sorted([r for r in rows if r.get("section") == skey],
                       key=lambda r: (GRADE_ORDER.get(r["grade"], 9), r["name_th"]))
        n_st = sum(1 for r in srows if r["grade"] == "stated")
        head = (f'<h2 class="ot-h">{bi(sth, sen)} '
                f'<span class="count">({len(srows)})</span></h2>'
                f'<p class="ot-note">{bi(f"บอกเอง {n_st} แห่ง — ที่เหลือคือคำของสารบัญหรือประตูที่ใช้ประจำ ไม่ใช่คำของสถานที่", f"{n_st} stated in their own words; the rest are a directory’s word or the usual door, not the place’s own.")}</p>')
        section_html.append(head + "".join(card(r) for r in srows))

    reg_rows = "".join(
        f'<tr><td>{bi(x["th"], x["en"])}</td>'
        f'<td>{site_a(x.get("url"), x.get("url", "")[:40])}</td>'
        f'<td>{bi(x.get("note_th", ""), x.get("note_en", ""))} '
        f'<span class="ot-note">· {esc(x.get("fetched", ""))}</span></td></tr>'
        for x in registers)
    reg_html = (
        f'<h2 class="ot-h">{bi("ทะเบียน โรงเรียน สมาคม", "The register, the school, the association")}</h2>'
        f'<p class="ot-note">{bi("ใบอนุญาตคือแถวในทะเบียน ไม่ใช่คะแนน — ตรวจชื่อได้", "A licence is a register row, not a rating — a name can be checked.")}</p>'
        f'<div class="ot-tablewrap"><table class="ot-tab"><thead><tr>'
        f'<th>{bi("อะไร", "What")}</th><th>{bi("ที่ไหน", "Where")}</th><th>{bi("บอกว่า", "What it states")}</th>'
        f'</tr></thead><tbody>{reg_rows}</tbody></table></div>')

    un_rows = "".join(
        f'<tr><td>{esc(u["name"])}</td><td>{esc(u.get("ref", ""))}</td>'
        f'<td>{esc(u["reason"])}</td></tr>' for u in unread)
    unread_html = (
        f'<h2 class="ot-h">{bi("ยังไม่ได้อ่าน — บอกไว้ตรง ๆ", "Not read yet — said plainly")} '
        f'<span class="count">({len(unread)})</span></h2>'
        f'<p class="ot-note">{bi("ชื่อที่รู้ว่ามีแต่ยังไม่มีใครอ่านหน้าของมันเอง และชื่อที่อ่านแล้วต้องตัดออก พร้อมเหตุผล", "Names known to exist whose own page nobody has read, and names read and refused, each with the reason.")}</p>'
        f'<div class="ot-tablewrap"><table class="ot-tab"><thead><tr>'
        f'<th>{bi("ชื่อ", "Name")}</th><th>{bi("อ้างอิง", "Ref")}</th>'
        f'<th>{bi("ทำไม", "Why")}</th>'
        f'</tr></thead><tbody>{un_rows}</tbody></table></div>')

    gl_rows = "".join(
        f'<tr><td class="th">{esc(th)}</td><td class="rtgs">{esc(rtgs)}</td>'
        f'<td>{esc(en)}</td></tr>' for th, rtgs, en in GLOSSARY)
    gloss_html = (
        f'<h2 class="ot-h">{bi("คำบนป้ายพวกนี้", "The words on these signs")}</h2>'
        f'<p class="ot-note">{bi("อักษรไทย · คำอ่านแบบ RTGS · ความหมายและรากศัพท์ — คำที่ใช้ถามเคาน์เตอร์คือ งานกิจกรรมบำบัด อยู่ใต้ กลุ่มงานเวชกรรมฟื้นฟู", "Thai script · RTGS · the meaning and the root. The counter word is งานกิจกรรมบำบัด, and in a state hospital it sits under the rehabilitation-medicine group.")}</p>'
        f'<div class="ot-tablewrap">'
        f'<table class="ot-tab ot-gloss"><tbody>{gl_rows}</tbody></table></div>')

    intro = bi(
        "กิจกรรมบำบัดคือการฝึกให้กลับไปทำสิ่งที่ต้องทำในชีวิตประจำวันได้ — เด็กที่พัฒนาการช้า "
        "ผู้ใหญ่หลังโรคหลอดเลือดสมองหรือมือบาดเจ็บ ผู้สูงอายุที่ความจำถดถอย — โดยนักกิจกรรมบำบัด "
        "ซึ่งเป็นผู้ประกอบโรคศิลปะที่มีใบอนุญาต หน้านี้อ่านจากหน้าของแต่ละที่เอง ทุกแถวมีเกรดกำกับว่า"
        "ใครเป็นคนพูด: สถานที่เอง สารบัญ หรือประตูที่ใช้ประจำ "
        "ไม่ใช่คำแนะนำทางการแพทย์ ที่ไหนไม่ได้พูด = เงียบ ไม่ใช่ 'ไม่มี'",
        "Occupational therapy is training to do the everyday things again — a child "
        "whose development is slow, an adult after a stroke or a hand injury, an elder "
        "whose memory is going — by an occupational therapist, who here holds a Healing "
        "Arts licence. This page was read from each place's own site. Every row carries "
        "a grade naming who is speaking: the place itself, a directory, or the usual "
        "door. This is not medical advice. Where a place says "
        "nothing, that is silence — never a 'no'.")

    census = bi(
        f"นับตรง ๆ: ในระเบียน {n_all:,} แห่งของสองจังหวัด ชื่อที่มาจากการสำรวจแผนที่เขียนคำว่า "
        f"กิจกรรมบำบัด {n_crawled_names} แห่ง ชั้นกายภาพบำบัดบนต้นไม้หมอมี {n_physio_shelf} แถว "
        f"(OSM ไม่มี healthcare=physiotherapist ในสองจังหวัดนี้เลย) — แถวที่ถือคำนี้ตอนนี้ "
        f"{n_spec} แถว ทุกแถวมาจากการอ่านหน้าของสถานที่เอง",
        f"Counted plainly: of {n_all:,} records in both provinces, {n_crawled_names} "
        f"crawled names carry the word occupational therapy, and the physiotherapy shelf "
        f"on the medical tree holds {n_physio_shelf} rows (OSM has no "
        f"healthcare=physiotherapist in either province). The {n_spec} records that carry "
        f"it now were each read from the place's own page.")

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "กิจกรรมบำบัด เชียงใหม่-เชียงราย — Occupational therapy, Chiang Mai and Chiang Rai",
        "url": BASE + "ot.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "MedicalOrganization", "name": r["name_en"],
                      **({"url": r["site"]}
                         if r.get("site")
                         and verdict(r["site"]).get("status") not in BROKEN
                         else {})}}
            for i, r in enumerate(rows)],
    }
    head = ('<link rel="stylesheet" href="ot.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "medical") if shelf_og else None

    body = (
        f'<h1>{bi("กิจกรรมบำบัด — เด็ก ผู้ใหญ่ ผู้สูงอายุ ในเชียงใหม่และเชียงราย", "Occupational therapy — children, adults and elders in Chiang Mai and Chiang Rai")}</h1>'
        f'<p class="ot-intro">{intro}</p>'
        f'<p class="ot-note">{census}</p>'
        f'{"".join(section_html)}'
        f'{reg_html}'
        f'{gloss_html}'
        f'{unread_html}'
        f'<p class="ot-note">{bi("มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ และไม่ใช่การรับรองคุณภาพ ข้อมูลบางส่วนมาจาก OpenStreetMap (ODbL 1.0)", "Mot Dang is a directory of places. It is not medical advice, not a referral, and not a quality guarantee. Some facility data is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap contributors.")}</p>'
        f'<p class="ot-note"><a href="care.html">{bi("ดูแลต่อเนื่อง — แผนกที่โรงพยาบาลบอกเอง", "ongoing care — the departments hospitals state")}</a> · '
        f'<a href="adhd.html">{bi("สมาธิสั้น — ทะเบียนจิตเวช", "ADHD — the psychiatric register")}</a> · '
        f'<a href="longcare.html">{bi("ดูแลระยะยาว — พักฟื้น บ้านพักคนชรา", "long-term care — convalescence, nursing homes")}</a> · '
        f'<a href="cm/medical/index.html">{bi("ชั้นหมอ-สถานพยาบาล", "the medical shelf")}</a></p>'
        f'{share_block(BASE + "ot.html", "กิจกรรมบำบัด เชียงใหม่ · มดแดง", card=og)}')

    (DOCS / "ot.html").write_text(page(
        "กิจกรรมบำบัด เชียงใหม่ · Occupational therapy, Chiang Mai",
        body, depth=0, path="ot.html",
        desc=bi_text(
            "นักกิจกรรมบำบัดในเชียงใหม่-เชียงราย — คลินิกเด็ก แผนกเวชกรรมฟื้นฟู คลินิกนอกเวลา "
            "ทะเบียนใบอนุญาต และคำไทยบนป้าย ทุกแถวบอกว่าใครเป็นคนพูด",
            "Occupational therapists in Chiang Mai and Chiang Rai — children's clinics, "
            "rehabilitation-medicine departments, after-hours clinics, the licence "
            "register and the Thai words from the signs, every row naming who is speaking."),
        extra_head=head, og=og))
    n_by = {}
    for r in rows:
        n_by[r["grade"]] = n_by.get(r["grade"], 0) + 1
    return (f"{len(rows)} rows ({' · '.join(f'{k} {v}' for k, v in sorted(n_by.items()))}), "
            f"{len(registers)} registers, {len(unread)} not read; "
            f"corpus names {n_name} (crawled {n_crawled_names}), specialty ot {n_spec}, "
            f"physio shelf {n_physio_shelf}")
