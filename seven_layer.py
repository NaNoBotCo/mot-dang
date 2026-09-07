#!/usr/bin/env python3
"""เซเว่นทุกซอย — the branch layer (/seven.html). WO-38.

Two branches of the same chain are not the same shop — the facet row has said
so from the start. What was missing is the other half of the sentence: what
IS the same everywhere. This page holds both, in the two voices the toilets
work established and this site keeps apart on principle:

  the CLASS voice — what any branch can do (pay a bill, deposit cash, send a
      parcel, warm a box of rice), labeled general-knowledge, never a
      per-branch promise;
  the BRANCH voice — what THIS one has, which lives in the facet row on the
      branch's own page, with provenance on every pill.

Everything counted here is counted live from the records at build time:
the brand census (463 7-Elevens, 59 of them branded off their own signs —
see importers/import_overpass.py seven_from_name), the doubled sevens
(SEVEN_CTX, computed in build.py), the coverage strip (the whole catalogue
measured against the sevens, grid-bucketed so it costs seconds), the zone
table (zone_of, WO-36's curated boxes). Nothing here is a pasted number
that can drift.

The สาขา branch names themselves live with CP All and are WO-18's parked
door. Until that door opens, a branch's identity on this site is its
neighbours — "the 7-Eleven beside the wat", measured from our own pins —
which is the identity the band on each branch page renders.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
moat layer. Emits seven.html + seven.css + docs/data/seven.json; prints
counts.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CSS = """
.sv-lede{font-size:1.02rem;max-width:46rem}
.sv-strip{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0}
.sv-tile{flex:1 1 10rem;padding:.7rem .9rem;border:1px solid rgba(0,0,0,.08);
  border-radius:.8rem;background:var(--card,#fff)}
.sv-tile b{display:block;font-size:1.5rem;line-height:1.2}
.sv-tile small{color:var(--mute)}
.sv-note{color:var(--mute);font-size:.9rem}
.sv-reg{width:100%;border-collapse:collapse;margin:.6rem 0 .4rem;font-size:.93rem}
.sv-reg th,.sv-reg td{padding:.4rem .35rem;border-bottom:1px solid rgba(0,0,0,.08);
  text-align:left;vertical-align:top}
.sv-reg td.n,.sv-reg th.n{text-align:right}
.sv-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));margin:.6rem 0}
.sv-card{padding:.8rem .95rem;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;
  background:var(--card,#fff)}
.sv-card h3{margin:.1rem 0 .4rem}
.sv-words{margin:.2rem 0;padding-left:1.1rem}
.sv-words li{margin:.22rem 0}
.sv-asks{margin:.2rem 0;padding-left:1.1rem}
.sv-asks li{margin:.2rem 0}
.sv-rule{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07);font-size:.98rem}
"""

# The class primer. Chain-level knowledge, festivals-style confidence label —
# each card is what any branch normally does, phrased so it can never be
# mistaken for a statement about one branch. The per-branch truth is the
# facet row, and the lede under the heading says so before the first card.
# The alcohol card names the practice a reader meets (the till refusing) and
# points at the chiller's own sign as the current word — no statute is recited
# unfetched (the WO-27 rule).
PRIMER = [
    ("🧾", "จ่ายบิลที่เคาน์เตอร์",
     "Pay bills at the counter",
     "ค่าไฟ ค่าน้ำ ค่าเน็ต ค่าโทรศัพท์ — ใบแจ้งหนี้ที่มีบาร์โค้ดส่วนใหญ่ยื่นจ่ายที่แคชเชียร์ได้เลย",
     "Electricity, water, internet, phone — most barcoded bills can be paid "
     "straight at the till."),
    ("🏧", "ฝาก-ถอนเงินสด",
     "Deposit and withdraw cash",
     "เป็นตัวแทนธนาคาร (banking agent) ของหลายธนาคารไทย ใช้บัตรหรือแอปธนาคาร มีค่าธรรมเนียมเล็กน้อยต่อรายการ",
     "Branches act as banking agents for several Thai banks — card or bank "
     "app in hand, a small per-transaction fee."),
    ("📦", "ส่ง-รับพัสดุ",
     "Send and collect parcels",
     "ส่งกล่องผ่าน SPEED-D ที่สาขาที่มีเคาน์เตอร์ และรับของที่สั่งออนไลน์ได้ที่สาขา",
     "Drop a parcel at a branch with the SPEED-D counter, or collect an "
     "online order at the branch you named."),
    ("📱", "เติมเงินเกือบทุกอย่าง",
     "Top up nearly anything",
     "ค่าโทร เกม วอลเล็ต — บอกแคชเชียร์หรือกดผ่านตู้ในร้าน",
     "Phone credit, game cards, e-wallets — ask the cashier or use the "
     "in-store kiosk."),
    ("🍚", "ไมโครเวฟและน้ำร้อน ฟรี",
     "Free microwave and hot water",
     "ซื้อข้าวกล่องแล้วอุ่นได้เลย — “อุ่นไหมคะ/ครับ” คือคำถามที่จะได้ยินหน้าแคชเชียร์",
     "Buy the rice box and it can be warmed on the spot — “shall I heat "
     "it?” is the question you will hear at the till."),
    ("☕", "กาแฟสด-เบเกอรี่ บางสาขา",
     "Fresh coffee and bakery, some branches",
     "เคาน์เตอร์กาแฟ (All Café) และชั้นเบเกอรี่มีเป็นบางสาขา — สาขาที่มดรู้ว่ามี จะติดป้าย ☕ ในหน้าสาขานั้น",
     "A coffee counter (All Café) and a bake-off shelf exist at some "
     "branches — the ones the ants know of carry the ☕ pill on their page."),
    ("🍺", "เหล้า-เบียร์ขายเป็นช่วง",
     "Alcohol sells in two windows",
     "ปกติ 11:00–14:00 และ 17:00–24:00 — เครื่องคิดเงินจะไม่ขายนอกช่วงเอง กติกาปรับได้ ป้ายที่ตู้แช่คือคำตอบล่าสุด",
     "Usually 11:00–14:00 and 17:00–24:00 — the till itself refuses outside "
     "the windows. The rule shifts from time to time; the sign on the "
     "chiller is the current word."),
    ("🛵", "สั่งถึงบ้าน",
     "Delivery from the branch",
     "แอป 7-Delivery ของเครือส่งจากสาขาใกล้บ้าน — ในเมืองครอบคลุมเกือบทุกซอย",
     "The chain's own 7-Delivery app sends from the branch nearest you — "
     "in town, nearly every soi is inside somebody's ring."),
    ("💳", "“มีออลเมมเบอร์มั้ย”",
     "“Do you have All Member?”",
     "คำถามประจำหน้าแคชเชียร์ หมายถึงบัตรสะสมแต้มของเครือ — ตอบว่าไม่มีได้สบายใจ",
     "The standing question at the till — it means the chain's points card, "
     "and “no” is a perfectly fine answer."),
]

# The words a reader meets around a convenience counter, RTGS + tone + root
# on first use, per the house transliteration rule.
WORDS = [
    ("เซเว่น", "sewen (sē-wên, mid-falling)",
     "จากอังกฤษ seven — ชื่อที่คนพูดจริง ไม่มีใครเรียกอีเลฟเว่น",
     "from English “seven” — the name people actually say; nobody "
     "says the “eleven” half."),
    ("สาขา", "sakha (sǎa-khǎa, rising-rising)",
     "สันสกฤต śākhā กิ่งไม้ — กิ่งของต้นเดียวกัน คำเดียวกับสาขาธนาคาร",
     "Sanskrit śākhā, the bough of a tree — one trunk, many branches; the "
     "same word a bank branch uses."),
    ("โชห่วย", "chohuai (choo-hùai, mid-low)",
     "จากแต้จิ๋ว 雜貨 (จับห่วย ของชำคละอย่าง) — ร้านหัวมุมที่มาก่อนทุกเครือ",
     "from Teochew 雜貨, “mixed goods” — the corner grocer that was "
     "here before every chain."),
    ("ฝาก-ถอน", "fak-thon (fàak-thǒn, low-rising)",
     "สองคำบนป้ายตัวแทนธนาคาร — ฝากเข้า ถอนออก",
     "the two words on the banking-agent sign: put in, take out."),
    ("ตู้แช่", "tu chae (tûu-châe, falling-falling)",
     "ตู้เย็นแนวตั้งหลังกระจก — ที่อยู่ของป้ายช่วงเวลาขายเหล้า-เบียร์",
     "the glass-front chiller — where the alcohol-window sign lives."),
]


def _grid(points, cell):
    g = {}
    for la, ln in points:
        g.setdefault((int(la // cell), int(ln // cell)), []).append((la, ln))
    return g


def _hav_m(la1, ln1, la2, ln2):
    r1, r2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(ln2 - ln1)
    h = math.sin(dp / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def coverage(records, sevens):
    """The city measured in sevens — every named record's distance to the
    nearest 7-Eleven, grid-bucketed (0.05° cells, 3×3 neighbourhood ≈ a 5 km
    reach) so the whole catalogue costs seconds, not minutes. A record with
    no seven inside the reach is counted as beyond-5-km, not dropped: the
    deep-rural edge is part of the finding. The median is exact — every
    beyond-reach record is farther than every in-reach distance, so as long
    as more than half the catalogue is in reach (it is), the middle value
    is measured, not estimated."""
    cell = 0.05
    grid = _grid([(s["lat"], s["lng"]) for s in sevens], cell)
    dists, beyond = [], 0
    for r in records:
        la, ln = r["lat"], r["lng"]
        ci, cj = int(la // cell), int(ln // cell)
        best = None
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for sla, sln in grid.get((ci + di, cj + dj), ()):
                    d = _hav_m(la, ln, sla, sln)
                    if best is None or d < best:
                        best = d
        if best is None or best > 5000:
            beyond += 1
        else:
            dists.append(best)
    dists.sort()
    total = len(dists) + beyond
    mid = total // 2
    median = int(dists[mid]) if mid < len(dists) else None
    return {
        "total": total,
        "median_m": median,
        "within_200": sum(1 for d in dists if d <= 200),
        "within_500": sum(1 for d in dists if d <= 500),
        "beyond_5km": beyond,
    }


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi, name_of = g["place_slug"], g["name_bi"], g["name_of"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block, shelf_og = g["share_block"], g.get("shelf_og")
    PROVINCES = g["PROVINCES"]
    zone_of = g.get("zone_of")
    SEVEN_CTX = g.get("SEVEN_CTX") or {}
    FACET_SETS = g.get("FACET_SETS") or []

    conv, sevens, by_id, prov_of = [], [], {}, {}
    brands = {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]
            if "convenience" in (r.get("sub") or []):
                conv.append(r)
                b = (r.get("attrs") or {}).get("brand")
                brands[b or ""] = brands.get(b or "", 0) + 1
                if b == "7-Eleven" and r.get("lat") is not None:
                    sevens.append(r)
    named = [r for p in PROVINCES for r in data[p["key"]]
             if r.get("lat") is not None
             and (r.get("name") or r.get("nameTh") or r.get("nameEn"))]
    signed = sum(1 for r in conv
                 if (r.get("attrs") or {}).get("brandFrom") == "osm-name")

    cov = coverage(named, sevens) if sevens else None

    # ---- the doubled sevens: pairs out of SEVEN_CTX, deduped ------------
    pairs, seen = [], set()
    for cid, ctx in SEVEN_CTX.items():
        twin = ctx.get("twin")
        if not twin:
            continue
        o, d = twin
        key = tuple(sorted((cid, o["id"])))
        if key in seen:
            continue
        seen.add(key)
        a = by_id.get(cid)
        if a is None:
            continue
        pairs.append((int(d), a, o))
    pairs.sort(key=lambda x: x[0])

    def phref(r):
        return f'{prov_of[r["id"]]}/p/{place_slug(r)}.html'

    def plink(r):
        # Two branches of one chain share a name; the neighbour gives the
        # words that tell them apart — the same identity the band uses.
        anch = (SEVEN_CTX.get(r["id"]) or {}).get("anchors") or []
        tail = ""
        if anch:
            tail = (' <span class="tinynote">(' + bi("ใกล้", "near") + " "
                    + esc(name_of(anch[0][0])) + ")</span>")
        return f'<a href="{att(phref(r))}">{name_bi(r)}</a>{tail}'

    # ---- census strip ---------------------------------------------------
    n_cm = sum(1 for r in conv if r["province"] == "cm")
    n_cr = len(conv) - n_cm
    tiles = [
        (str(len(conv)), bi("ร้านสะดวกซื้อในสมุด", "convenience records"),
         f"cm {n_cm} · cr {n_cr}"),
        (str(brands.get("7-Eleven", 0)), bi("สาขาเซเว่น", "7-Eleven branches"),
         bi(f"{signed} สาขาได้ยี่ห้อจากป้ายชื่อตัวเอง",
            f"{signed} branded off their own signs")),
        (str(len(pairs)), bi("เซเว่นแฝด — สองสาขาใน 150 ม.",
                             "doubled sevens (two in 150 m)"), ""),
    ]
    if cov and cov["median_m"] is not None:
        tiles.append((f'{cov["median_m"]} ' + "ม.",
                      bi("ระยะกลางจากทุกที่ในสมุด ถึงเซเว่นที่ใกล้สุด",
                         "median distance, any place in the book to its nearest seven"),
                      bi(f'{cov["within_200"]:,} ที่อยู่ใน 200 ม. · {cov["beyond_5km"]:,} ที่ไกลเกิน 5 กม.',
                         f'{cov["within_200"]:,} places within 200 m · {cov["beyond_5km"]:,} beyond 5 km')))
    strip = "".join(
        f'<div class="sv-tile"><b>{t0}</b>{t1}'
        + (f'<br><small>{t2}</small>' if t2 else "")
        + "</div>"
        for t0, t1, t2 in tiles)

    # ---- brand table ----------------------------------------------------
    brand_rows = ""
    for b, n in sorted(brands.items(), key=lambda kv: -kv[1]):
        if not b:
            continue
        brand_rows += f'<tr><td>{esc(b)}</td><td class="n">{n:,}</td></tr>'
    nob = brands.get("", 0)
    brand_rows += ('<tr><td>' + bi("ไม่ระบุยี่ห้อ — ร้านใกล้บ้าน โชห่วย มินิมาร์ทอิสระ",
                                   "no brand stated — corner shops, independent minimarts")
                   + f'</td><td class="n">{nob:,}</td></tr>')

    # ---- zone table (cm boxes; cr is a separate sitting, WO-36) ---------
    zone_html = ""
    if zone_of:
        zc = {}
        for r in sevens:
            if r["province"] != "cm":
                continue
            z = zone_of(r, "cm")
            key = ((z.get("th") or z.get("key", "?"),
                    z.get("en") or z.get("key", "?"))
                   if z else ("รอบนอก", "the outer ring"))
            zc[key] = zc.get(key, 0) + 1
        rows = "".join(
            f'<tr><td>{bi(th, en)}</td><td class="n">{n:,}</td></tr>'
            for (th, en), n in sorted(zc.items(), key=lambda kv: -kv[1]))
        zone_html = (
            f'<h2>{bi("เซเว่นรายย่าน", "Sevens by part of town")}</h2>'
            f'<table class="sv-reg"><tr><th>' + bi("ย่าน", "Zone")
            + '</th><th class="n">' + bi("สาขา", "Branches") + "</th></tr>"
            + rows + "</table>"
            + '<p class="sv-note">'
            + bi("ย่านตามกล่องที่วาดไว้ใน WO-36 — เชียงรายยังไม่แบ่งย่าน นับรวมไว้ก่อน",
                 "Zones are WO-36's drawn boxes; Chiang Rai is not yet zoned and is counted whole.")
            + "</p>")

    # ---- doubled sevens table ------------------------------------------
    twin_rows = "".join(
        f'<tr><td>{plink(a)}</td><td>{plink(b)}</td><td class="n">{d}</td></tr>'
        for d, a, b in pairs[:12])
    twins_html = ""
    if pairs:
        twins_html = (
            f'<h2>{bi("เซเว่นแฝด — สาขาที่มองเห็นกันเอง", "The doubled sevens")}</h2>'
            f'<p class="sv-lede">'
            + bi("คู่สาขายี่ห้อเดียวกันที่ห่างกันไม่เกิน 150 เมตร — ใกล้พอที่จะยืนตรงกลางแล้วเห็นทั้งสองร้าน "
                 "วัดตรงจากหมุดของเราเอง คู่ที่ใกล้กว่า 25 เมตรถือว่าน่าจะเป็นร้านเดียวกันถูกปักซ้ำ และไม่นับ",
                 "Same-brand pairs no more than 150 m apart — close enough to stand between and see "
                 "both. Measured straight from our own pins; anything under 25 m is treated as one "
                 "shop mapped twice, and not counted.")
            + "</p>"
            + '<table class="sv-reg"><tr><th>' + bi("สาขา", "Branch")
            + "</th><th>" + bi("คู่ของมัน", "Its double")
            + '</th><th class="n">' + bi("ห่าง (ม.)", "Apart (m)") + "</th></tr>"
            + twin_rows + "</table>"
            + (f'<p class="sv-note">' + bi(f"แสดง 12 จาก {len(pairs)} คู่ — ครบทุกคู่ใน",
                                           f"12 of {len(pairs)} pairs shown — all of them in")
               + ' <a href="data/seven.json">data/seven.json</a></p>' if len(pairs) > 12 else ""))

    # ---- the class primer ----------------------------------------------
    cards = "".join(
        f'<div class="sv-card"><h3>{ico} {bi(th, en)}</h3>'
        f"<p>{bi(dth, den)}</p></div>"
        for ico, th, en, dth, den in PRIMER)
    primer_html = (
        f'<h2>{bi("สาขาไหนก็ทำได้", "What any branch can do")}</h2>'
        f'<p class="sv-note">'
        + bi("ความรู้ระดับเครือ (confidence: general-knowledge) ไม่ใช่คำยืนยันรายสาขา — "
             "สาขาไหนมีอะไรจริง ดูป้ายในหน้าสาขานั้น",
             "Chain-level knowledge (confidence: general-knowledge), not a per-branch "
             "promise — what a given branch actually has lives on that branch's own page.")
        + "</p>"
        + f'<div class="sv-grid">{cards}</div>')

    # ---- the toilet sentence, in the one wording the site stands behind -
    toilet_html = ""
    tj = ROOT / "data" / "toilets.json"
    if tj.exists():
        exc = [e for e in json.loads(tj.read_text()).get("excluded", [])
               if e.get("key") == "convenience"]
        if exc:
            toilet_html = (
                '<div class="sv-rule"><b>🚻 '
                + bi("ห้องน้ำ — เรื่องเดียวที่ต้องพูดตรง ๆ", "The toilet, said plainly")
                + "</b>"
                + bi(esc(exc[0]["why_th"]), esc(exc[0]["why_en"]))
                + f' <a href="toilets.html">{bi("หาห้องน้ำใกล้ตัว", "Find a toilet near you")}</a></div>')

    # ---- the door survey: the facet questions, ready to carry ----------
    conv_set = next((s for s in FACET_SETS if s.get("key") == "convenience"), None)
    asks_html = ""
    if conv_set:
        asks = "".join(
            f'<li>{f.get("icon", "")} ' + bi(f.get("ask_th", f["th"]), f.get("ask_en", f["en"])) + "</li>"
            for f in conv_set["facets"])
        asks_html = (
            f'<h2>{bi("คำถามหน้าร้าน", "The shopfront questions")}</h2>'
            f'<p class="sv-lede">'
            + bi("นี่คือคำถามที่แยกสาขาหนึ่งจากอีกสาขา — ผ่านร้านไหน กดปุ่ม 🐜 ในหน้าสาขานั้นแล้วตอบเท่าที่เห็น",
                 "These are the questions that tell one branch from the next. Pass a branch, open its "
                 "page, tap 🐜 and answer what you saw.")
            + "</p>"
            + f'<ul class="sv-asks">{asks}</ul>')

    # ---- words ----------------------------------------------------------
    words_html = (
        f'<h2>{bi("คำที่เจอหน้าเคาน์เตอร์", "The words at the counter")}</h2>'
        + '<ul class="sv-words">'
        + "".join(
            f"<li><b>{esc(w)}</b> — {esc(rt)} — {bi(dth, den)}</li>"
            for w, rt, dth, den in WORDS)
        + "</ul>")

    # ---- the held door, said plainly -----------------------------------
    held_html = (
        '<p class="sv-note">'
        + bi("ชื่อสาขาจริง (“สาขาศิริมังคลาจารย์”) อยู่กับ CP All และแหล่งนั้น (WO-18) ยังไม่เปิด — "
             "ระหว่างนี้ สาขาบนเว็บนี้เรียกตามเพื่อนบ้านของมัน วัดจากหมุดของเราเอง",
             "The real branch names live with CP All, and that source (WO-18) is not yet open — until "
             "it is, a branch here goes by its neighbours, measured from our own pins.")
        + "</p>")

    # ---- assemble -------------------------------------------------------
    shelf_links = " · ".join(
        f'<a href="{p["key"]}/essentials/convenience/index.html">'
        + bi(p["th"], p["en"]) + f' ({sum(1 for r in conv if r["province"] == p["key"]):,})</a>'
        for p in PROVINCES)
    body = (
        f'<h1>🏪 {bi("เซเว่นทุกซอย", "A seven in every soi")}</h1>'
        f'<p class="sv-lede">'
        + bi("ร้านสะดวกซื้อยี่ห้อเดียวกันก็ไม่เหมือนกัน — หน้านี้คือชั้นของทั้งเมือง: "
             "เครือไหนกี่สาขา ย่านไหนหนาแน่น สาขาไหนเป็นแฝด และอะไรที่สาขาไหนก็ทำได้เหมือนกัน",
             "Two branches of the same chain are not the same shop. This is the whole city's "
             "shelf: how many of which chain, which parts of town run thick with them, which "
             "branches are doubles — and what any branch can do all the same.")
        + "</p>"
        + f'<div class="sv-strip">{strip}</div>'
        + f'<p class="sv-note">{bi("ชั้นเต็ม", "The full shelves")}: {shelf_links}</p>'
        + f'<h2>{bi("เครือไหน กี่สาขา", "Which chain, how many")}</h2>'
        + '<table class="sv-reg"><tr><th>' + bi("เครือ / ยี่ห้อ", "Chain / brand")
        + '</th><th class="n">' + bi("สาขา", "Branches") + "</th></tr>"
        + brand_rows + "</table>"
        + '<p class="sv-note">'
        + bi("ร้านไม่ระบุยี่ห้อไม่ใช่ช่องว่างของข้อมูล — มันคือร้านใกล้บ้านที่มีชื่อของตัวเอง อยู่บนชั้นเดียวกัน",
             "The no-brand rows are not a data gap — they are the neighbourhood shops with names "
             "of their own, on the same shelf.")
        + "</p>"
        + twins_html
        + zone_html
        + primer_html
        + toilet_html
        + asks_html
        + words_html
        + held_html
        + f'<p class="sv-note">{bi("ข้อมูลหน้านี้", "This page as data")}: '
        + '<a href="data/seven.json">data/seven.json</a></p>'
        + share_block(BASE + "seven.html", "เซเว่นทุกซอย · มดแดง",
                      card=shelf_og("seven") if shelf_og else None))

    (DOCS / "seven.css").write_text(CSS)
    head = '<link rel="stylesheet" href="seven.css">'
    og = shelf_og("seven") if shelf_og else None
    (DOCS / "seven.html").write_text(page(
        "เซเว่นทุกซอย — ร้านสะดวกซื้อทั้งเมือง · A seven in every soi",
        body, depth=0, path="seven.html",
        desc="ชั้นร้านสะดวกซื้อทั้งเชียงใหม่-เชียงราย: เครือไหนกี่สาขา เซเว่นแฝด ย่านไหนหนาแน่น "
             "และอะไรที่สาขาไหนก็ทำได้ — จ่ายบิล ฝากถอน ส่งพัสดุ · Every convenience shelf in "
             "Chiang Mai and Chiang Rai: the brand census, the doubled sevens, and what any "
             "branch can do — bills, banking agent, parcels",
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › '
               + bi("เซเว่นทุกซอย", "A seven in every soi")))

    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "seven.json").write_text(json.dumps({
        "_license": "ODbL contributions via OpenStreetMap where sourced osm; "
                    "counts computed by motdang.net at build time",
        "census": {"convenience": len(conv), "seven_eleven": brands.get("7-Eleven", 0),
                   "branded_from_own_sign": signed,
                   "brands": {k or "(none)": v for k, v in brands.items()}},
        "coverage": cov,
        "doubled": [{"a": a["id"], "b": b["id"], "m": d,
                     "brand": (a.get("attrs") or {}).get("brand")}
                    for d, a, b in pairs],
    }, ensure_ascii=False, indent=1))

    return {"page": 1, "convenience": len(conv),
            "sevens": brands.get("7-Eleven", 0), "signed": signed,
            "doubled": len(pairs),
            "median_m": cov["median_m"] if cov else None}
