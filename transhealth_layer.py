#!/usr/bin/env python3
"""สุขภาพคนข้ามเพศ — where gender-affirming care is, what each place states
itself, and where a credential can be checked (/trans-health.html). WO-26.

WHY THIS PAGE EXISTS. Measured 2026-08-21: across all 19,975 records in both
provinces, not one place named a trans or gender-affirming service — no
ข้ามเพศ, no แปลงเพศ, no hormone, no LGBT anywhere in a name. The care exists in
this city; the corpus simply could not say so, because clinics here are named
after their doctors (importers/specialty.py) and community organizations sit
in OSM as bare points. Meanwhile the community's own map of itself —
SISTERHOOD เพื่อนสาว, the Thai trans community directory — lists six places in
the north. So this layer is curated research with dated sources, the same bar
as additions-chiang-mai.json, plus the lgbtq welcome tags the crawl held all
along and import used to drop (importers/import_all.py:apply_lgbtq).

WHAT THIS PAGE IS. A directory of PLACES and a pointer to the registers. It is
not medical advice, it does not rank anybody, and it names no individual
doctor — the womens-health rules, unchanged. The grade is the point and goes
on every row:

  stated            the place itself names trans or gender-diverse people in
                    its services or its welcome, on its own site. Quoted in
                    its own terms.
  community-listed  listed by the trans community's own directory; the
                    place's own statement is general. Both provenances shown.
  route             a hospital where this care's departments (ต่อมไร้ท่อ,
                    จิตเวช) are standard for its class — NOT confirmed for
                    this building. Ring first.
  reference         outside both provinces, kept because readers travel.

Everyday venues carrying an lgbtq welcome tag are shown too, marked as what
they are: a MAPPER's statement in OpenStreetMap, not the venue's own sign.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
womens-health layer. Emits trans-health.html + trans-health.css.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The name-rule scan that measures the zero. One source of truth: the audit
# (importers/audit_transhealth.py) imports this, so the page's sentence and
# the audit's report cannot drift apart. เพศ alone is NOT a rule — it lives in
# สุขภาพเพศ, เพศสัมพันธ์ and a thousand ordinary compounds; only the specific
# phrases below state what this page is about.
TRANS_NAME_RX = re.compile(
    r"ข้ามเพศ|แปลงเพศ|หลากหลายทางเพศ|ยืนยันเพศ"
    r"|\btransgender\b|\btrans[- ]?health\b|\bgender[- ]?affirm|\blgbtq?\b",
    re.I)

GRADE_ORDER = ["stated", "community-listed", "route", "reference"]

CSS = """
.gx-intro{font-size:1.02rem;max-width:46rem}
.gx-note{font-size:.86rem;opacity:.78;max-width:46rem}
.gx-benefit{max-width:46rem;border:1px solid rgba(0,0,0,.14);border-radius:.8rem;
  padding:.7rem .9rem;margin:.8rem 0}
.gx-benefit .ask{font-weight:600}
.gx-grade{display:inline-block;font-size:.72rem;padding:.08rem .42rem;border-radius:.7rem;
  border:1px solid currentColor;opacity:.85;vertical-align:.08em;white-space:nowrap}
.gx-grade.stated{color:#1c6b3a}
.gx-grade.listed{color:#2a5a7a}
.gx-grade.route{color:#7a5a12}
.gx-grade.welcome{color:#6a4a7a}
.gx-grade.field{color:#8a4a2a}
.gx-list .gx-cred{opacity:.9}
.gx-rules{margin:.5rem 0 .2rem;padding-left:1.1rem;font-size:.9rem;line-height:1.55}
.gx-procs{margin:.2rem 0 0;padding-left:1.1rem;font-size:.82rem;opacity:.78;
  columns:2;column-gap:1.4rem}
@media (max-width:640px){.gx-procs{columns:1}}
.gx-list{list-style:none;padding-left:0;max-width:46rem}
.gx-list li{padding:.34rem 0;border-bottom:1px solid rgba(0,0,0,.07);line-height:1.5}
.gx-list .states{display:block;font-size:.84rem;opacity:.8}
.gx-list .reach{font-size:.8rem;opacity:.7}
.gx-list .srcs{font-size:.76rem;opacity:.65}
.gx-reg{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.gx-reg th,.gx-reg td{text-align:left;vertical-align:top;padding:.42rem .5rem;
  border-bottom:1px solid rgba(0,0,0,.09)}
.gx-reg th{font-weight:600;white-space:nowrap}
.gx-gloss{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.gx-gloss td{padding:.34rem .5rem;border-bottom:1px solid rgba(0,0,0,.07);vertical-align:top}
.gx-gloss .th{font-size:1.06rem;white-space:nowrap}
.gx-gloss .rtgs{opacity:.72;font-style:italic;white-space:nowrap}
@media (max-width:640px){.gx-reg,.gx-gloss{font-size:.86rem}
  .gx-reg th{white-space:normal}}
"""

# Competence is a credential. Every URL verified reachable 2026-08-21 from this
# machine. rcpt.org (the endocrinology board's college) is deliberately absent:
# its HTTPS is broken and a register link has to be one — the lead is filed in
# data/curated/transhealth.json unverified[].
REGISTERS = [
    ("ใบประกอบวิชาชีพเวชกรรม — เป็นแพทย์จริงไหม และมีวุฒิบัตรสาขาไหน",
     "Is this person a licensed physician, and which board certifications do they hold?",
     "แพทยสภา — ตรวจสอบแพทย์", "The Medical Council of Thailand — physician lookup",
     "https://checkmd.tmc.or.th",
     "ทะเบียนแพทย์ทั้งประเทศ พร้อมวุฒิบัตรเฉพาะทาง — ต่อมไร้ท่อ จิตเวช ศัลยกรรมตกแต่ง ดูได้จากที่เดียวกัน",
     "The national register of licensed doctors, including specialist "
     "qualifications (วุฒิบัตร) — endocrinology, psychiatry and plastic surgery "
     "all show in the same lookup."),
    ("จิตแพทย์ผู้ประเมิน — สังกัดราชวิทยาลัยไหน",
     "The assessing psychiatrist — which college stands behind that?",
     "ราชวิทยาลัยจิตแพทย์แห่งประเทศไทย",
     "Royal College of Psychiatrists of Thailand", "https://www.rcpsycht.org",
     "การประเมินก่อนการผ่าตัดยืนยันเพศเป็นงานของจิตแพทย์",
     "The assessment that gender-affirming surgery requires is a "
     "psychiatrist's own work."),
    ("ศัลยแพทย์ตกแต่ง — บอร์ดจริงไหม",
     "Is the surgeon board-certified in plastic surgery?",
     "สมาคมศัลยแพทย์ตกแต่งแห่งประเทศไทย",
     "Society of Plastic and Reconstructive Surgeons of Thailand",
     "https://thprs.org",
     "วุฒิบัตรศัลยศาสตร์ตกแต่ง คือใบที่ควรถามถึงก่อนการผ่าตัดยืนยันเพศทุกชนิด",
     "Board certification in plastic surgery (วุฒิบัตรศัลยศาสตร์ตกแต่ง) is the "
     "credential to ask about before any gender-affirming operation."),
    ("มาตรฐานการดูแลที่คลินิกอ้างถึง คืออะไร",
     "The standards of care a clinic cites — what are they?",
     "WPATH — Standards of Care (SOC-8)", "WPATH — Standards of Care (SOC-8)",
     "https://www.wpath.org",
     "มาตรฐานสากลของการดูแลสุขภาพคนข้ามเพศ ฉบับที่ 8 — คลินิกที่ดีมักบอกเองว่าทำตามนี้",
     "The international standards for transgender health care, 8th edition — "
     "a clinic working to them tends to say so itself."),
    ("สิทธิของฉันครอบคลุมไหม", "Does my coverage include this?",
     "สปสช. — สายด่วน 1330", "NHSO — hotline 1330", "https://www.nhso.go.th",
     "บริการฮอร์โมนยืนยันเพศสภาพเป็นสิทธิประโยชน์แล้ว (2568) — โทร 1330 ถามสิทธิของตัวเองได้เลย",
     "Gender-affirming hormone therapy entered the benefit package in 2025 — "
     "ring 1330 and ask about your own entitlement."),
    ("คลินิกมีใบอนุญาตไหม", "Is a private clinic licensed at all?",
     "กองสถานพยาบาลและการประกอบโรคศิลปะ กระทรวงสาธารณสุข",
     "MoPH, Dept. of Health Service Support", "",
     "คลินิกที่ถูกต้องจะติดใบอนุญาตสถานพยาบาลไว้ให้เห็นในร้าน",
     "A legitimate clinic displays its สถานพยาบาล licence on the premises."),
]

# The sign on the door, for a reader in either language. Script · RTGS · gloss.
GLOSSARY = [
    ("คนข้ามเพศ", "khon kham phet", "a transgender person — literally 'a person "
     "who crosses gender'. ผู้หญิงข้ามเพศ a trans woman; ผู้ชายข้ามเพศ a trans man."),
    ("ยืนยันเพศสภาพ", "yuenyan phetsaphap", "gender affirmation — the word in the "
     "NHSO benefit's own name, ฮอร์โมนยืนยันเพศสภาพ."),
    ("ความหลากหลายทางเพศ", "khwam lak lai thang phet", "gender diversity — the "
     "phrasing hospitals use, as in คลินิกเพื่อผู้ที่มีความหลากหลายทางเพศ."),
    ("กะเทย", "kathoei", "a longstanding Thai word; many trans women use it for "
     "themselves, and from a stranger it can land very differently. The word to "
     "recognize on a page or a stage bill, not necessarily the one to reach for."),
    ("ฮอร์โมน", "homon", "hormone. เทคฮอร์โมน is the everyday phrase for taking "
     "them; ตรวจวัดระดับฮอร์โมน is the blood test that checks levels."),
    ("ต่อมไร้ท่อ", "tom rai tho", "endocrine — อายุรศาสตร์ต่อมไร้ท่อ is the "
     "hospital department where hormone care lives."),
    ("จิตเวช", "chittawet", "psychiatry — สุขภาพจิต is mental health. The "
     "pre-surgery assessment is this department's work."),
    ("ศัลยกรรมแปลงเพศ", "sanlayakam plaeng phet", "gender-affirming surgery as "
     "most signs still write it; formal writing now says การผ่าตัดยืนยันเพศสภาพ."),
    ("เพร็พ · เป๊ป", "phrep · pep", "PrEP and PEP — HIV prevention before and "
     "after exposure. The community clinics on this page dispense both."),
    ("ตรวจเลือด", "truat lueat", "a blood test — the follow-up that careful "
     "hormone care runs on."),
    ("บัตรทอง", "bat thong", "the universal-coverage 'gold card' (สิทธิ 30 บาท) — "
     "the scheme the new hormone benefit sits in. สายด่วน 1330 answers questions."),
    ("คลินิกเทคนิคการแพทย์", "khlinik theknik kan phaet", "a medical-technology "
     "clinic — the licence class community testing clinics operate under; testing "
     "and counselling, not prescriptions."),
]


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block, channels = g["share_block"], g["channels"]
    name_of = g["name_of"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    (DOCS / "trans-health.css").write_text(CSS)

    reg = json.loads((ROOT / "data" / "curated" / "transhealth.json").read_text())

    # ---- resolve register rows against the catalogue -----------------------
    by_id = {}
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            by_id[r["id"]] = (prov, r)

    # ---- the measured zero, taken live so it heals itself ------------------
    n_records = sum(len(data.get(p, [])) for p in ("cm", "cr"))
    n_stating = 0
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            blob = " ".join(str(v) for v in
                            (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)
            if TRANS_NAME_RX.search(blob):
                n_stating += 1

    def reach_marks(r):
        live, _ = channels(r)
        kinds = [c.get("kind") for c in live] if live and isinstance(live[0], dict) else []
        marks = []
        if r.get("phone") or "phone" in kinds:
            marks.append("☎")
        if "line" in kinds or (r.get("attrs") or {}).get("lineId"):
            marks.append("LINE")
        if "web" in kinds:
            marks.append("🌐")
        return (' <span class="reach">' + " · ".join(marks) + "</span>") if marks else ""

    GRADE_TAG = {
        "stated": ('stated', "บอกเอง", "stated",
                   ("ที่นี่ระบุเองในช่องทางของตัวเองว่าดูแลหรือยินดีต้อนรับคนข้ามเพศ",
                    "this place names trans or gender-diverse people in its own words")),
        "community-listed": ('listed', "ชุมชนแนะนำ", "community-listed",
                   ("อยู่ในสารบัญของชุมชนคนข้ามเพศเอง (SISTERHOOD เพื่อนสาว) — ที่นี่บอกบริการทั่วไปของตัวเองไว้ตามที่แสดง",
                    "listed by the trans community's own directory (SISTERHOOD); the place's own statement is general")),
        "route": ('route', "เส้นทางโรงพยาบาล — ยังไม่ยืนยัน", "hospital route — not confirmed",
                   ("แผนกที่เกี่ยวข้องเป็นแผนกมาตรฐานของโรงพยาบาลระดับนี้ แต่ยังไม่มีใครยืนยันของที่นี่ — โทรถามก่อน",
                    "the relevant departments are standard for this class of hospital, but nobody has confirmed this one — ring first")),
        "reference": ('listed', "นอกสองจังหวัด", "outside these provinces", ("", "")),
    }

    def row_html(row):
        grade = row.get("grade")
        cls, tag_th, tag_en, title_pair = GRADE_TAG.get(grade, GRADE_TAG["stated"])
        tag = ('<span class="gx-grade ' + cls + '" title="'
               + att(bi_text(*title_pair)) + '">' + bi(tag_th, tag_en) + "</span>")
        pid = row.get("place")
        srcs = "".join(
            ' <a href="' + att(s["ref"]) + '" rel="noopener">[' + str(i + 1) + "]</a>"
            for i, s in enumerate(row.get("sources") or []))
        # A credential is a REGISTER ENTRY and never a rating. This site names
        # no doctor as good or bad — womens_health_layer settled that twice —
        # and the one thing it will publish about a named clinician is the row
        # a reader can look up for themselves, which is exactly what the
        # register table below tells them to do. No adjectives,
        # and the link goes to the register rather than to our word for it.
        cred = ""
        if row.get("credential_th") or row.get("credential_en"):
            body = bi(esc(row.get("credential_th") or ""),
                      esc(row.get("credential_en") or ""))
            url = row.get("credential_url")
            cred = ('<span class="states gx-cred">✓ '
                    + (('<a href="' + att(url) + '" rel="noopener">' + body + "</a>")
                       if url else body) + "</span>")
        states = ('<span class="states">' + bi(esc(row.get("states_th") or ""),
                                               esc(row.get("states_en") or ""))
                  + ('<span class="srcs">' + srcs + "</span>" if srcs else "")
                  + "</span>" + cred)
        if pid and pid in by_id:
            prov, r = by_id[pid]
            link = ('<a href="' + prov + "/p/" + place_slug(r) + '.html">'
                    + name_bi(r) + "</a>")
            return "<li>" + link + " " + tag + reach_marks(r) + states + "</li>"
        if pid:
            print(f"  trans-health: register row {row.get('key')} names unknown id {pid} — row skipped")
            return ""
        nm = bi(esc(row.get("name_th") or ""), esc(row.get("name_en") or ""))
        return "<li>" + nm + " " + tag + states + "</li>"

    # Surgery is banded on its own, not because it matters more but because
    # the rules for an operation are different rules — an age, a consent, a
    # psychiatric assessment and a surgeon's branch, all set out in the
    # regulation printed beside it. A row filed under its grade alone would
    # put an operation next to a walk-in test with nothing saying so.
    rows = reg.get("rows") or []
    sections = {k: [] for k in GRADE_ORDER}
    surgery_rows = []
    for row in rows:
        h = row_html(row)
        if not h:
            continue
        if row.get("surgery"):
            surgery_rows.append((row, h))
        elif row.get("grade") in sections:
            sections[row["grade"]].append((row, h))

    # ---- everyday venues: curated provenance ∪ live attrs scan -------------
    venue_rows = []
    curated_venues = {v["place"]: v for v in (reg.get("venues") or [])}
    seen = set()
    for pid, v in curated_venues.items():
        if pid not in by_id:
            print(f"  trans-health: venue id {pid} not in catalogue — skipped")
            continue
        prov, r = by_id[pid]
        seen.add(pid)
        tag = ('<span class="gx-grade welcome" title="'
               + att(bi_text(v.get("evidence_th") or "", v.get("evidence_en") or ""))
               + '">' + bi("ป้ายแผนที่ว่ายินดีต้อนรับ", "welcome — per the map") + "</span>")
        ev = ('<span class="states">'
              + bi(esc(v.get("evidence_th") or ""), esc(v.get("evidence_en") or ""))
              + "</span>")
        venue_rows.append('<li><a href="' + prov + "/p/" + place_slug(r)
                          + '.html">' + name_bi(r) + "</a> " + tag
                          + reach_marks(r) + ev + "</li>")
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            a = r.get("attrs") or {}
            if r["id"] in seen or not (a.get("lgbtq") or a.get("lgbtqTrans")):
                continue
            vals = " ".join(f"{k}={a[k]}" for k in ("lgbtq", "lgbtqTrans") if a.get(k))
            tag = ('<span class="gx-grade welcome" title="'
                   + att(bi_text("ป้ายข้อมูลใน OpenStreetMap: " + vals,
                                 "OpenStreetMap tags: " + vals))
                   + '">' + bi("ป้ายแผนที่ว่ายินดีต้อนรับ", "welcome — per the map") + "</span>")
            venue_rows.append('<li><a href="' + prov + "/p/" + place_slug(r)
                              + '.html">' + name_bi(r) + "</a> " + tag
                              + reach_marks(r) + "</li>")

    community_rows = []
    for c in reg.get("community") or []:
        srcs = "".join(
            ' <a href="' + att(s["ref"]) + '" rel="noopener">[' + str(i + 1) + "]</a>"
            for i, s in enumerate(c.get("sources") or []))
        community_rows.append(
            "<li>" + bi(esc(c.get("name_th") or ""), esc(c.get("name_en") or ""))
            + '<span class="states">' + bi(esc(c.get("states_th") or ""),
                                           esc(c.get("states_en") or ""))
            + ('<span class="srcs">' + srcs + "</span>" if srcs else "")
            + "</span></li>")

    # ---- the benefit box ---------------------------------------------------
    ben = reg.get("benefit") or {}
    ben_srcs = "".join(
        ' <a href="' + att(s["ref"]) + '" rel="noopener">[' + str(i + 1) + "]</a>"
        for i, s in enumerate(ben.get("sources") or []))
    benefit_html = ""
    if ben:
        benefit_html = (
            '<div class="gx-benefit"><b>' + bi(esc(ben.get("name_th") or ""),
                                               esc(ben.get("name_en") or "")) + "</b><br>"
            + bi(esc(ben.get("summary_th") or ""), esc(ben.get("summary_en") or ""))
            + '<span class="srcs">' + ben_srcs + "</span><br>"
            + '<span class="ask">' + bi(esc(ben.get("ask_th") or ""),
                                        esc(ben.get("ask_en") or "")) + "</span></div>")

    # ---- the regulation ----------------------------------------------------
    # Read out of the Royal Gazette PDF itself, because the secondary
    # reporting disagreed with itself about the surgery age — one outlet ran
    # "18 and over" as its headline while the clause says 20, or 18 with a
    # guardian's consent. A reader planning their own year needs the number
    # that is actually in the book, so the citation travels with it.
    rules = reg.get("rules") or {}
    rules_html = ""
    if rules:
        pts = "".join("<li>" + bi(esc(th), esc(en)) + "</li>"
                      for th, en in rules.get("points", []))
        procs = "".join("<li>" + esc(p) + "</li>"
                        for p in rules.get("procedures", []))
        rsrc = "".join(
            ' <a href="' + att(s["ref"]) + '" rel="noopener">[' + str(i + 1) + "]</a>"
            for i, s in enumerate(rules.get("sources") or []))
        rules_html = (
            '<div class="gx-benefit"><b>'
            + bi(esc(rules.get("name_th") or ""), esc(rules.get("name_en") or ""))
            + "</b><br>" + '<span class="srcs">'
            + bi(esc(rules.get("cite_th") or ""), esc(rules.get("cite_en") or ""))
            + rsrc + "</span>"
            + '<ul class="gx-rules">' + pts + "</ul>"
            + '<p class="gx-note">'
            + bi(esc(rules.get("procedures_note_th") or ""),
                 esc(rules.get("procedures_note_en") or "")) + "</p>"
            + '<ul class="gx-procs">' + procs + "</ul></div>")

    # ---- the pharmacy question --------------------------------------------
    # Field testimony, and marked as that. It stays on the page because it is
    # a fact about SHOPS and stock — which is what a directory is for — and it
    # is the question a reader actually arrives with. It carries no dose, no
    # brand and no view about what anybody should take; that line is written
    # into the block itself rather than left to be inferred.
    ph = reg.get("pharmacy") or {}
    pharm_html = ""
    if ph:
        n_pharm = 0
        for prov in ("cm", "cr"):
            for r in data.get(prov, []):
                a = r.get("attrs") or {}
                if "pharmacy" in (r.get("sub") or []) or a.get("facilityType") == "pharmacy":
                    n_pharm += 1
        tag = ('<span class="gx-grade field" title="'
               + att(bi_text("รายงานจากการเดินจริงในเชียงใหม่",
                             "a field report from walking Chiang Mai"))
               + '">' + bi("จากการเดินจริง", "field report") + "</span>")
        pharm_html = (
            "<h2>" + bi("แล้วร้านขายยาล่ะ", "And the pharmacy question") + " "
            + tag + "</h2>"
            + '<p class="gx-note">'
            + bi(esc(ph.get("note_th") or "").replace("1,133", f"{n_pharm:,}"),
                 esc(ph.get("note_en") or "").replace("1,133", f"{n_pharm:,}"))
            + "</p>"
            + '<p class="gx-note"><b>'
            + bi(esc(ph.get("stance_th") or ""), esc(ph.get("stance_en") or ""))
            + "</b> "
            + '<a href="cm/medical/pharmacy/index.html">'
            + bi("ดูชั้นร้านขายยา เชียงใหม่", "the Chiang Mai pharmacy shelf") + "</a> · "
            + '<a href="cr/medical/pharmacy/index.html">'
            + bi("เชียงราย", "Chiang Rai") + "</a></p>")

    # ---- registers and glossary -------------------------------------------
    reg_rows = []
    for q_th, q_en, n_th, n_en, url, note_th, note_en in REGISTERS:
        who = ('<a href="' + att(url) + '" rel="noopener">' + bi(n_th, n_en) + "</a>") \
            if url else bi(n_th, n_en)
        reg_rows.append("<tr><th>" + bi(q_th, q_en) + "</th><td>" + who
                        + "</td><td>" + bi(note_th, note_en) + "</td></tr>")
    reg_html = ('<table class="gx-reg"><thead><tr>'
                "<th>" + bi("อยากยืนยันอะไร", "What you want to confirm") + "</th>"
                "<th>" + bi("ที่ไหน", "Where") + "</th>"
                "<th>" + bi("หมายเหตุ", "Notes") + "</th></tr></thead>"
                "<tbody>" + "".join(reg_rows) + "</tbody></table>")

    gl_rows = "".join(
        '<tr><td class="th">' + esc(th) + '</td><td class="rtgs">' + esc(rtgs)
        + "</td><td>" + esc(en) + "</td></tr>" for th, rtgs, en in GLOSSARY)
    gloss_html = '<table class="gx-gloss"><tbody>' + gl_rows + "</tbody></table>"

    # ---- copy --------------------------------------------------------------
    intro = bi(
        "หน้านี้รวบรวมที่ที่เกี่ยวกับสุขภาพคนข้ามเพศในสารบัญ พร้อมบอกตรง ๆ ว่ารู้มาจากไหน — "
        "บางแห่งบอกเองในช่องทางของตัวเอง บางแห่งชุมชนคนข้ามเพศแนะนำไว้ในสารบัญของชุมชนเอง "
        "และบางแห่งเป็นโรงพยาบาลที่แผนกที่เกี่ยวข้องน่าจะมีแต่ยังไม่ยืนยัน "
        "ตารางข้างล่างบอกว่าไปตรวจได้ที่ไหน",
        "This page collects the places in the directory that concern trans health, "
        "and says plainly where each fact comes from — some places state it in "
        "their own words, some are listed by the trans community's own directory, "
        "and some are hospitals where the relevant department is likely but "
        "unconfirmed. Below: where to check a board certification.")

    zero_note = bi(
        f"วัดจริงเมื่อสร้างหน้า: จาก {n_records:,} รายการในสารบัญ มี {n_stating} แห่งที่ชื่อของตัวเอง"
        "ระบุบริการด้านนี้ — ทุกแถวในหน้านี้จึงมาจากการค้นคว้าที่มีแหล่งอ้างอิงกำกับวันที่ "
        "ไม่ใช่จากป้ายชื่อร้าน",
        f"Measured at build time: of {n_records:,} records in the directory, "
        f"{n_stating} state this care in their own name — so every row on this "
        "page comes from dated, sourced research rather than from a shopfront sign.")

    # ---- JSON-LD -----------------------------------------------------------
    ld_items = []
    for grade in ("stated", "community-listed"):
        for row, _ in sections[grade]:
            pid = row.get("place")
            if pid and pid in by_id:
                prov, r = by_id[pid]
                ld_items.append({
                    "@type": "ListItem", "position": len(ld_items) + 1,
                    "item": {"@type": "MedicalClinic", "name": name_of(r),
                             "url": BASE + prov + "/p/" + place_slug(r) + ".html"}})
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "สุขภาพคนข้ามเพศ เชียงใหม่-เชียงราย — Trans health, Chiang Mai and Chiang Rai",
          "url": BASE + "trans-health.html",
          "itemListElement": ld_items}
    head = ('<link rel="stylesheet" href="trans-health.css">'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + "</script>")

    def sec(title_th, title_en, note_th, note_en, items):
        if not items:
            return ""
        return ("<h2>" + bi(title_th, title_en)
                + ' <span class="count">(' + str(len(items)) + ")</span></h2>"
                + '<p class="gx-note">' + bi(note_th, note_en) + "</p>"
                + '<ul class="gx-list">' + "".join(h for _, h in items) + "</ul>")

    og = shelf_og("cm", "medical") if shelf_og else None
    body = (
        "<h1>" + bi("สุขภาพคนข้ามเพศ — ไปที่ไหน",
                    "Trans health — where to go") + "</h1>"
        + '<p class="gx-intro">' + intro + "</p>"
        + benefit_html
        + sec("ที่ที่บอกเองว่าดูแลคนข้ามเพศ", "Places that state it themselves",
              "แต่ละแห่งระบุไว้ในเว็บไซต์หรือช่องทางของตัวเอง — ตัวเลข [1] คือแหล่งที่อ่าน พร้อมวันที่ในไฟล์ข้อมูล",
              "Each one states it on its own site or channel — the [1] marks are the sources read, dated in the data file",
              sections["stated"])
        + sec("ชุมชนแนะนำ", "Listed by the community",
              "SISTERHOOD เพื่อนสาว คือสารบัญทรัพยากรของชุมชนคนข้ามเพศไทยเอง — ที่ในรายการนี้อยู่ในสารบัญนั้น และคำบรรยายคือสิ่งที่แต่ละที่บอกเองเท่านั้น",
              "SISTERHOOD is the Thai trans community's own resource directory — these places appear there, and the description shown is only what each states itself",
              sections["community-listed"])
        + sec("การผ่าตัด — ที่ที่บอกเองในสองจังหวัดนี้", "Surgery — what states it in these two provinces",
              "ค้นทั้งสารบัญแล้วพบที่เดียวที่ระบุการผ่าตัดยืนยันเพศสภาพไว้เอง ที่อื่นที่ทำอยู่ในกรุงเทพฯ และภูเก็ต ซึ่งอยู่นอกสารบัญนี้ · เครื่องหมาย ✓ คือรายการทะเบียนที่เปิดดูเองได้ ไม่ใช่คะแนนหรือคำรับรองของมดแดง · ข้อบังคับที่ใช้กับการผ่าตัดนี้อยู่ถัดลงไป",
              "A scan of the whole directory found one place stating operative gender-affirming care itself; the others doing this work are in Bangkok and Phuket, outside these two provinces · a ✓ is a register entry anyone can open, not a score and not our endorsement · the regulation governing this surgery is printed below",
              surgery_rows)
        + rules_html
        + sec("เส้นทางโรงพยาบาล — น่าจะมี แต่ยังไม่ยืนยัน", "The hospital route — likely, not yet confirmed",
              "โรงพยาบาลมหาวิทยาลัยและโรงพยาบาลจิตเวชคือที่ที่แผนกเหล่านี้อยู่เป็นปกติ แต่ยังไม่มีใครโทรยืนยันของที่นี่ — โทรถามแผนกก่อนไป ตู้สายโรงพยาบาลตอบเรื่องนี้เป็นประจำ",
              "University and psychiatric hospitals are where these departments normally live, but nobody has rung to confirm these — call the department first; Thai hospital switchboards answer this routinely",
              sections["route"])
        + sec("อ้างอิงกรุงเทพฯ", "A Bangkok reference",
              "อยู่นอกสองจังหวัดของสารบัญนี้ — เก็บไว้เพราะคนเดินทาง และเพราะเป็นต้นแบบของบริการทั้งประเทศ",
              "Outside this directory's two provinces — kept because readers travel, and because it is the model the country's services grew from",
              sections["reference"])
        + ("<h2>" + bi("ชุมชน", "Community") + "</h2><ul class=\"gx-list\">"
           + "".join(community_rows) + "</ul>" if community_rows else "")
        + ("<h2>" + bi("ที่ที่ป้ายแผนที่ว่ายินดีต้อนรับ", "Everyday places the map marks as welcoming")
           + ' <span class="count">(' + str(len(venue_rows)) + ")</span></h2>"
           + '<p class="gx-note">'
           + bi("ป้ายเหล่านี้เป็นบันทึกของผู้ทำแผนที่ใน OpenStreetMap ไม่ใช่ป้ายของร้านเอง — บอกไว้ตรง ๆ แบบเดียวกับทุกหน้าของมดแดง",
                "These marks are OpenStreetMap mappers' statements, not the venues' own signs — said plainly, the way every Mot Dang page does")
           + "</p><ul class=\"gx-list\">" + "".join(venue_rows) + "</ul>" if venue_rows else "")
        + pharm_html
        + "<h2>" + bi("ตรวจใบวุฒิบัตรได้ที่นี่",
                      "Where to check a credential") + "</h2>"
        + '<p class="gx-note">'
        + bi("ทุกแห่งเป็นทะเบียนหรือหน่วยงานทางการ ตรวจแล้วว่าเข้าถึงได้เมื่อ 21 ส.ค. 2569",
             "Every one is an official register or body, verified reachable 2026-08-21")
        + "</p>" + reg_html
        + "<h2>" + bi("อ่านป้ายหน้าคลินิก",
                      "Reading the clinic sign") + "</h2>"
        + '<p class="gx-note">'
        + bi("อักษรไทย · คำอ่านแบบ RTGS · ความหมาย — เทียบรูปคำกับป้ายได้เลยแม้อ่านไทยไม่ออก",
             "Thai script · RTGS spelling · what it means — enough to match a word against a sign by its shape, without reading Thai")
        + "</p>" + gloss_html
        + '<p class="gx-note">' + zero_note + "</p>"
        + '<p class="gx-note">'
        + bi("มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ และไม่ใช่การรับรองคุณภาพ "
             "ข้อมูลสถานพยาบาลบางส่วนมาจาก OpenStreetMap (ODbL 1.0) และจากหน้าเว็บของแต่ละที่ตามวันที่ที่ระบุ "
             "เห็นอะไรที่เปลี่ยนไปหรือควรเพิ่ม — บอกมดได้ที่หน้าเสนอแนะ",
             "Mot Dang is a directory of places. It is not medical advice, not a referral, and not a quality "
             "guarantee. Some facility data is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap "
             "contributors, and from each place's own pages on the dates shown. If something here has "
             "changed or is missing, tell the ants via the suggestion page.")
        + "</p>"
        + share_block(BASE + "trans-health.html", "สุขภาพคนข้ามเพศ เชียงใหม่ · มดแดง", card=og))

    (DOCS / "trans-health.html").write_text(page(
        "สุขภาพคนข้ามเพศ เชียงใหม่ · Trans health, Chiang Mai",
        body, depth=0, path="trans-health.html",
        desc=bi_text(
            "สุขภาพคนข้ามเพศในเชียงใหม่และเชียงราย — ที่ไหนบอกเองว่าดูแลคนข้ามเพศ "
            "ที่ไหนชุมชนแนะนำ สิทธิฮอร์โมนยืนยันเพศสภาพของ สปสช. ตรวจใบวุฒิบัตรแพทย์ได้ที่ไหน "
            "และคำไทยบนป้ายหน้าคลินิกแปลว่าอะไร",
            "Trans health and gender-affirming care in Chiang Mai and Chiang Rai: which "
            "places state trans services themselves, which the community lists, the NHSO "
            "gender-affirming hormone benefit, where to verify a doctor's board "
            "certification, and what the Thai words on the clinic sign mean"),
        extra_head=head, og=og,
        crumbs='<a href="index.html">' + bi("หน้าแรก", "Home") + "</a> › "
               + bi("สุขภาพคนข้ามเพศ", "Trans health")))
    n_stated = len(sections["stated"])
    n_listed = len(sections["community-listed"])
    return (f"{n_stated} stated · {n_listed} community-listed · "
            f"{len(sections['route'])} route · {len(surgery_rows)} stating surgery · "
            f"{len(venue_rows)} welcome venue(s) · {n_stating} of {n_records:,} "
            f"records name this care themselves")
