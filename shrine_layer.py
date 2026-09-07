#!/usr/bin/env python3
"""ศาล-ศาลเจ้า-หลักเมือง — the shrine register of both provinces, the map,
and what you are looking at, on one page (/san.html). WO-39.

Three things a reader asks, in the order they ask them:

  1. WHERE — the two provinces on one drawn map: every register row whose
     record carries a pin. No tiles needed at this scale; drawn ink, the
     namphuron trade.
  2. WHAT EACH ONE IS — the register grouped by kind: the city pillars and
     navels, the ศาลเจ้า and their keepers, the founder-king shrines, the
     guardian อารักษ์, the devalayas, the Guanyin. Every row carries its
     confidence and its source with the date it was read; told-of names
     stay in their own block and never enter the register.
  3. WHAT YOU ARE LOOKING AT — the primer: ศาลพระภูมิ vs ศาลเจ้าที่, who
     keeps a ศาลเจ้า, what a หลักเมือง is, where a spirit house retires.
     Class knowledge in the tradition's voice.

The keeper names the shrine; the calendar carries its source. Public shrines
only.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
hotspring layer. Emits san.html + san.css, copies the register to
docs/data/shrines.json; prints the counts.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "data" / "shrines.json"

CSS = """
.sn-intro{font-size:1.02rem;max-width:46rem}
.sn-map{margin:.6rem 0 .2rem;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;
  background:var(--card,#fff);overflow:hidden}
.sn-map svg{display:block;width:100%;height:auto}
.sn-credit{color:var(--mute);font-size:.78rem;margin:.15rem 0 1rem}
.sn-kind{margin:1rem 0 .2rem}
.sn-kind h3{margin:.9rem 0 .25rem}
.sn-kind h3 .count{color:var(--mute);font-weight:400}
.sn-row{margin:.35rem 0 .65rem}
.sn-row .venue a{text-decoration:none;color:inherit;font-weight:600}
.sn-row .venue a:hover{text-decoration:underline}
.sn-row small{color:var(--mute)}
.sn-note{color:var(--mute);font-size:.9rem}
.sn-say{display:block;margin:.15rem 0 0;font-size:.93rem}
.sn-chip{display:inline-block;padding:.05rem .5rem;border-radius:.7rem;font-size:.78rem;
  background:var(--soft);border:1px solid rgba(0,0,0,.08);color:var(--mute);margin-left:.35rem;vertical-align:middle}
.sn-chip.rec{color:#2f6b36}
.sn-chip.gk{color:#7d6a52}
.sn-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));margin:.6rem 0}
.sn-card{padding:.8rem .95rem;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;background:var(--card,#fff)}
.sn-card h3{margin:.1rem 0 .4rem}
.sn-card .say{display:block;margin-top:.5rem;color:var(--mute);font-size:.9rem}
.sn-words{margin:.2rem 0 .2rem;padding-left:1.1rem}
.sn-words li{margin:.22rem 0}
.sn-pin{fill:var(--ant,#b3402a);stroke:#fff;stroke-width:1}
.sn-maplabel{font-size:11px;fill:#5a4f42}
.sn-provlabel{font-size:12.5px;font-weight:600;fill:#3d3428}
@media (prefers-color-scheme: dark){
  .sn-maplabel{fill:#c8bfae}.sn-provlabel{fill:#e0d8c8}
}
"""


def load_reg():
    if REG.exists():
        return json.loads(REG.read_text())
    return {"provinces": {}, "kinds": {}, "shrines": [], "unverified": []}


def _pin_of(s, by_id):
    """A register row's pin comes from its RECORD (single source of truth) —
    a row with no record, or whose record has no pin, draws nothing."""
    for rid in [s.get("recordId")] + (s.get("companionIds") or []):
        r = by_id.get(rid or "")
        if r and r.get("lat") is not None and r.get("lng") is not None:
            return float(r["lat"]), float(r["lng"])
    return None


def _map_svg(rows, provinces, by_id, bi_text, esc):
    """Both provinces drawn, one pin per pinned register row, labelled by
    Thai name. Equirectangular with cos(lat) correction — the namphuron
    projection at two-province scale."""
    pts = []
    for s in rows:
        pin = _pin_of(s, by_id)
        if pin:
            pts.append((s, pin))
    if len(pts) < 3:
        return ""
    lats = [p[0] for _, p in pts]
    lngs = [p[1] for _, p in pts]
    lat0 = (min(lats) + max(lats)) / 2
    kx = 111.320 * math.cos(math.radians(lat0))
    ky = 110.574
    span_x = max((max(lngs) - min(lngs)) * kx, 1e-6)
    span_y = max((max(lats) - min(lats)) * ky, 1e-6)
    W = 760
    PAD = 50
    scale = (W - 2 * PAD) / span_x
    H = int(span_y * scale) + 2 * PAD
    if H > 900:
        scale *= 900 / H
        H = 900

    def xy(lat, lng):
        x = PAD + (lng - min(lngs)) * kx * scale
        y = PAD + (max(lats) - lat) * ky * scale
        return x, y

    pins, labels = [], []
    for s, (lat, lng) in pts:
        x, y = xy(lat, lng)
        pins.append(f'<circle class="sn-pin" cx="{x:.1f}" cy="{y:.1f}" r="4.6"/>')
        nm = s.get("nameTh") or s.get("nameEn") or ""
        nm = nm.split(" (")[0][:28]
        tx = min(max(x + 7, PAD), W - PAD - 8)
        anchor = "start" if tx < W - 180 else "end"
        labels.append(f'<text class="sn-maplabel" x="{tx:.1f}" y="{y + 4:.1f}" '
                      f'text-anchor="{anchor}">{esc(nm)}</text>')
    prov_labels = []
    for key, meta in provinces.items():
        mine = [(lat, lng) for s, (lat, lng) in pts if s["province"] == key]
        if not mine:
            continue
        cx = sum(xy(*m)[0] for m in mine) / len(mine)
        cy = sum(xy(*m)[1] for m in mine) / len(mine)
        cx = min(max(cx, PAD + 30), W - PAD - 30)
        prov_labels.append(f'<text class="sn-provlabel" x="{cx:.1f}" '
                           f'y="{cy - 16:.1f}" text-anchor="middle" opacity=".82">'
                           f'{esc(meta["th"])}</text>')
    km50 = 50 * scale
    bar = (f'<g><line x1="{PAD}" y1="{H - 18}" x2="{PAD + km50:.1f}" y2="{H - 18}" '
           f'stroke="#7d6a52" stroke-width="2"/>'
           f'<text class="sn-maplabel" x="{PAD}" y="{H - 24}">50 km</text></g>')
    label = bi_text("แผนที่ศาลและหลักเมืองสองจังหวัด — หมุดหนึ่งจุดต่อหนึ่งศาล",
                    "Map of the shrines and city pillars of both provinces, one pin each")
    return (f'<div class="sn-map"><svg role="img" aria-label="{esc(label)}" '
            f'viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
            + "".join(prov_labels) + "".join(pins) + "".join(labels) + bar
            + "</svg></div>")


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    PROVINCES = g["PROVINCES"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    reg = load_reg()
    rows = reg.get("shrines", [])
    kinds = reg.get("kinds", {})
    provinces = reg.get("provinces", {})
    (DOCS / "san.css").write_text(CSS)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "shrines.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1))

    by_id, prov_of = {}, {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]

    def href(r):
        return f'{prov_of[r["id"]]}/p/{place_slug(r)}.html'

    def link_of(s):
        r = by_id.get(s.get("recordId") or "")
        if r:
            return f'<a href="{href(r)}">{name_bi(r)}</a>'
        th, en = s.get("nameTh"), s.get("nameEn")
        if th and en:
            return f"<b>{bi(th, en)}</b>"
        return f"<b>{esc(th or en or '')}</b>"

    def conf_chip(s):
        c = s.get("confidence")
        if c == "record":
            return f'<span class="sn-chip rec">{bi("อยู่ในสารบัญ", "in the directory")}</span>'
        if c == "stated":
            f_on = ""
            for src in s.get("sources") or []:
                if src.get("fetched"):
                    f_on = src["fetched"]
                    break
            return ('<span class="sn-chip rec">'
                    + bi("ที่มาอ่านแล้ว " + f_on, "source read " + f_on) + "</span>")
        if c == "general-knowledge":
            return f'<span class="sn-chip gk">{bi("ความรู้ทั่วไป — ยังไม่ลงพื้นที่", "general knowledge, unfielded")}</span>'
        return f'<span class="sn-chip gk">{bi("รอยืนยัน", "needs verification")}</span>'

    def src_link(s):
        for src in s.get("sources") or []:
            ref = src.get("ref") or ""
            if ref.startswith("http"):
                host = ref.split("//", 1)[-1].split("/")[0].replace("www.", "")
                return (f' · <a class="sn-note" href="{att(ref)}" '
                        f'rel="noopener nofollow">{esc(host)}</a>')
        return ""

    # ---- the register, grouped by kind ------------------------------------
    KIND_ORDER = ["lak-mueang", "san-chao", "royal", "arak", "thewalai", "kuan-im"]
    kind_html = []
    for k in KIND_ORDER:
        mine = [s for s in rows if s.get("kind") == k]
        if not mine:
            continue
        meta = kinds.get(k, {"th": k, "en": k, "emoji": ""})
        items = []
        for s in mine:
            bits = [f'<span class="venue">{link_of(s)}</span>']
            where = []
            pv = provinces.get(s.get("province"), {})
            if s.get("amphoe_th"):
                a = s["amphoe_th"]
                where.append(a if a.startswith(("อ.", "เมือง", "แม่", "เชียง")) else "อ." + a)
            if pv:
                where.append(pv.get("th", ""))
            if where:
                bits.append(f'<small>{esc(" · ".join(where))}</small>')
            bits.append(conf_chip(s))
            if s.get("awaiting_pin"):
                bits.append(f'<span class="sn-chip gk">{bi("รอหมุด", "awaiting a pin")}</span>')
            if s.get("approx"):
                bits.append(f'<span class="sn-chip gk">{bi("ตำแหน่งโดยประมาณ", "position approximate")}</span>')
            line = " ".join(bits)
            note = ""
            if s.get("note_th") or s.get("note_en"):
                note = ('<span class="sn-say">'
                        + bi(s.get("note_th") or "", s.get("note_en") or ""))
                fid = s.get("festival")
                if fid:
                    note += (' <a href="festivals.html">🎉 '
                             + bi("ดูช่วงงานในหน้าเทศกาล", "festival window on the festivals page")
                             + "</a>")
                note += src_link(s) + "</span>"
            items.append(f'<li class="sn-row">{line}{note}</li>')
        kind_html.append(
            f'<h3>{esc(meta.get("emoji", ""))} {bi(meta["th"], meta["en"])} '
            f'<span class="count">({len(mine)})</span></h3>'
            f'<ul class="dir">{"".join(items)}</ul>')
    kind_html = f'<div class="sn-kind">{"".join(kind_html)}</div>'

    # ---- told of, not yet read -------------------------------------------
    unv = reg.get("unverified") or []
    unv_html = ""
    if unv:
        items = "".join(
            f'<li><b>{esc(u.get("name", ""))}</b> — {bi(u.get("note_th", ""), u.get("note_en", ""))}</li>'
            for u in unv)
        unv_html = (f'<h3>{bi("ที่เล่ากันแต่ยังอ่านที่มาไม่ได้", "Told of, not yet read")}</h3>'
                    f'<p class="sn-note">'
                    + bi("ชื่อที่มีคนเล่าหรือชื่อร้านพาดพิงถึง แต่มดยังไม่เจอหน้าที่อ่านได้หรือหมุดที่ยืนยันได้ — จดไว้ตรงนี้ตามตรง ไม่ลงทะเบียน ใครมีที่มา บอกมดได้",
                         "Names people tell of, or that a shop name points at, with no readable source or confirmable pin yet — held here plainly, off the register; if you hold a source, tell the ants")
                    + f'</p><ul class="sn-note">{items}</ul>')

    # ---- primer ----------------------------------------------------------
    P = []

    def card(h_th, h_en, *paras):
        body = "".join(f"<p>{p}</p>" if not str(p).startswith("<") else str(p)
                       for p in paras)
        P.append(f'<div class="sn-card"><h3>{bi(h_th, h_en)}</h3>{body}</div>')

    def say(th, en):
        return '<span class="say">' + bi(th, en) + "</span>"

    card("ศาลพระภูมิ กับ ศาลเจ้าที่ — สองศาลหน้าบ้าน", "The two house shrines",
         bi("ศาลพระภูมิ (เสาเดียว) เป็นที่ของพระภูมิเจ้าที่ผู้ดูแลผืนดิน ส่วนศาลเจ้าที่หรือศาลตายาย (เตี้ยกว่า มักหลายเสา) เป็นที่ของผีเจ้าที่เจ้าทางที่อยู่มาก่อน บ้านร้านค้าจีนมักมีตี่จู้เอี๊ยะตั้งกับพื้นในร้านอีกแบบหนึ่ง — ทั้งหมดนี้เป็นเรื่องของบ้านใครบ้านมัน สารบัญนี้จึงลงเฉพาะศาลสาธารณะที่ยืนในที่เปิด",
            "A san phra phum on its single post houses the lord of the land; the lower san chao thi (often many-posted, the grandparents' shrine) belongs to the spirits who were here first. Chinese shopfronts keep the ti chu ia on the floor inside — a third form of the same courtesy. All of it is household practice, which is why this register lists only the public shrines standing in open ground."),
         say("คำเมืองเรียกหอผีประจำหมู่บ้านว่า หอเสื้อบ้าน — เสื้อ ในที่นี้คือผีอารักษ์ ไม่ใช่เสื้อผ้า",
             "the northern word for a village guardian hall is ho suea ban — the suea here is a guardian spirit, nothing to do with shirts"))
    card("ศาลเจ้า — ศาลจีน", "San chao — the Chinese shrines",
         bi("ศาลเจ้าจีนดูแลโดยคณะกรรมการชุมชน มูลนิธิ หรือสมาคมตระกูล มีผู้ดูแลประจำ จุดธูปได้ทั้งปี และคึกคักที่สุดช่วงตรุษจีนกับงานประจำปีของศาล — ปุงเถ่ากงที่ช้างม่อยเป็นแบบฉบับของศาล «เจ้าที่ใหญ่ของชุมชน» ที่ชาวจีนโพ้นทะเลตั้งเมื่อมาถึงแล้วเลี้ยงดูแลสืบกันมา",
            "A Chinese shrine is kept — by a community committee, a foundation, a clan association — with a keeper on the ground, incense the year round, and its big days at Chinese New Year and the shrine's own annual festival. Pung Thao Kong by Warorot is the type specimen: the community's founding guardian, set up on arrival and kept ever since."),
         say("ศาลเจ้าจีนหลายแห่งอยู่ใต้มูลนิธิการกุศล — ชื่อบนป้ายจึงอาจเป็นชื่อมูลนิธิ ไม่ใช่ชื่อเทพ",
             "many Chinese shrines sit under benevolent foundations — the name on the gate may be the foundation's, not the deity's"))
    card("หลักเมือง อินทขีล สะดือเมือง", "The pillar, the Inthakhin, the navel",
         bi("เมืองในธรรมเนียมไท-ล้านนามีใจ: เชียงใหม่ฝากใจไว้กับเสาอินทขีลในวัดเจดีย์หลวง (งานใส่ขันดอกราวพฤษภาคม–มิถุนายน) เชียงรายมีเสาสะดือเมืองบนดอยจอมทอง แม่สายมีศาลหลักเมืองของตัวเอง — ส่วนแจ่งและประตูเมืองมีผู้เฝ้าของแต่ละมุม อย่างศาลเจ้าพ่อหลักเมืองที่แจ่งกระต๊ำ",
            "A mueang in the Tai-Lanna way keeps a heart: Chiang Mai's is the Inthakhin pillar inside Wat Chedi Luang (the flower-tray festival falls around May–June), Chiang Rai's the navel pillar on Doi Chom Thong, Mae Sai keeps a pillar shrine of its own — and the corners and gates keep their own guardians, like the Chao Pho Lak Mueang shrine at Katam Corner."),
         say("เสื้อเมือง คือผีอารักษ์ของทั้งเวียง — พิธีสืบชะตาเมืองทุกปีคือการเลี้ยงดูแลความผูกพันนี้",
             "the suea mueang is the guardian spirit of the whole city — the annual fate-extension rite keeps that bond fed"))
    card("ศาลเกษียณที่ไหน — ต้นโพธิ์ กำแพงวัด", "Where a spirit house retires",
         bi("ศาลที่ปลดแล้วไม่ทิ้งลงถัง — ธรรมเนียมที่เห็นได้ทั่วเมืองคือเชิญไปไว้โคนต้นโพธิ์ต้นไทรใหญ่ กำแพงวัด หรือทางสามแพร่ง จึงเห็นศาลเก่ารวมกันเป็นหย่อม ๆ ตามที่เหล่านั้น — ในคัมภีร์ล้านนายังมีสูตถอนสำหรับถอนบ้านถอนเรือนโดยเฉพาะ เป็นวิชาของปู่อาจารย์",
            "A retired spirit house is not binned — the custom seen all over both towns is to carry it to the foot of a great bodhi or banyan, a temple wall, or a three-way junction, which is why old shrines gather in small companies at such places. The Lanna manuscripts even keep withdrawal liturgies (sut thon) for un-consecrating a house — a ritual specialist's craft."),
         say("เห็นหย่อมศาลเก่าใต้ต้นไม้ใหญ่ = ที่เกษียณ ไม่ใช่ที่ถูกทิ้ง — เดินผ่านด้วยความเคารพตามธรรมเนียม",
             "a company of old shrines under a great tree is a retirement, not a dump — custom is to pass with respect"))
    card("คำที่จะได้เจอ", "Words you will meet",
         '<ul class="sn-words">'
         + "".join(f"<li>{bi(th, en)}</li>" for th, en in [
             ("ศาล (sǎan) — ที่สถิตของสิ่งศักดิ์สิทธิ์ · ศาลา (sǎa-laa) — ที่พักคน คนละคำ", "san (ศาล) — a shrine · sala (ศาลา) — a pavilion for people; different word"),
             ("ศาลเจ้า (sǎan-jâo) — ศาลจีน · เทวาลัย (thee-wáa-lai) — เทวสถานแบบพราหมณ์-ฮินดู", "san chao (ศาลเจ้า) — a Chinese shrine · thewalai (เทวาลัย) — a Brahmanic-Hindu devalaya"),
             ("หลักเมือง (làk-mʉʉang) — เสาใจเมือง · สะดือเมือง — «สะดือ» ของเวียง", "lak mueang (หลักเมือง) — the city pillar · sadue mueang (สะดือเมือง) — the city's navel"),
             ("อารักษ์ (aa-rák) — ผีผู้พิทักษ์ · เสื้อบ้าน-เสื้อเมือง — อารักษ์ของบ้านและเวียง", "arak (อารักษ์) — a guardian spirit · suea ban / suea mueang — the guardians of village and city"),
             ("บนบาน (bon-baan) — ขอไว้ · แก้บน (kɛ̂ɛ-bon) — มาคืนตามคำ เมื่อสมหวัง", "bon ban (บนบาน) — to make a vow at a shrine · kae bon (แก้บน) — returning to keep it"),
             ("หอ (hɔ̌ɔ) — เรือนบูชาขนาดย่อม เช่น หอผี หอเสื้อบ้าน หอพญามังราย", "ho (หอ) — a small votive hall: ho phi, ho suea ban, the Mangrai memorial ho"),
         ]) + "</ul>",
         say("รากศัพท์ต่อได้ที่ wichaa.net/thairoots — ศาล เป็นคำยืมสายวัด-ราชสำนัก ส่วน หอ, เสื้อ, ผี เป็นคำไทแท้",
             "follow the roots at wichaa.net/thairoots — san rides the temple-and-court loan stream, while ho, suea and phi are Tai-stock words"))
    primer_html = f'<div class="sn-grid">{"".join(P)}</div>'

    # ---- assemble --------------------------------------------------------
    n_rec = sum(1 for s in rows if s.get("recordId"))
    n_wait = sum(1 for s in rows if s.get("awaiting_pin"))
    intro = bi(
        f"ทะเบียนศาล ศาลเจ้า และหลักเมืองของเชียงใหม่-เชียงราย — {len(rows)} แห่งในทะเบียน "
        f"({n_rec} แห่งกดเข้าหน้าของแต่ละที่ได้ อีก {n_wait} แห่งรอหมุด-รอสำรวจ) "
        "จัดตามชนิดที่ผู้ดูแลเรียกเอง",
        f"The register of shrines and city pillars of Chiang Mai and Chiang Rai — {len(rows)} entries "
        f"({n_rec} open their own directory pages; {n_wait} await a pin or a survey), "
        "grouped by the kinds their keepers use.")

    map_html = _map_svg(rows, provinces, by_id, bi_text, esc)
    credit = ('<p class="sn-credit">'
              + bi("หมุดจากสารบัญ (OpenStreetMap © ผู้ร่วมแก้ไข, ODbL · ทะเบียนวัดและบัญชีเปิดราชการ) — แถวที่ยังไม่มีหมุดบอกไว้ตรง ๆ ว่ารอสำรวจ",
                   "Pins come from the directory's own records (OpenStreetMap © contributors, ODbL; temple and open-government registers) — rows without a pin say so plainly")
              + "</p>")

    ld_items = []
    for i, s in enumerate(rows):
        pin = _pin_of(s, by_id)
        item = {"@type": "PlaceOfWorship" if s.get("kind") in ("san-chao", "thewalai", "kuan-im")
                else "LandmarksOrHistoricalBuildings",
                "name": s.get("nameTh") or s.get("nameEn")}
        if pin:
            item["geo"] = {"@type": "GeoCoordinates", "latitude": pin[0], "longitude": pin[1]}
        r = by_id.get(s.get("recordId") or "")
        if r:
            item["url"] = BASE + href(r)
        ld_items.append({"@type": "ListItem", "position": i + 1, "item": item})
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "ศาล ศาลเจ้า และหลักเมืองของเชียงใหม่-เชียงราย — the shrine register",
          "url": BASE + "san.html", "itemListElement": ld_items}
    head = ('<link rel="stylesheet" href="san.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "wat", "shrine") if shelf_og else None

    body = (
        f'<h1>🏮 {bi("ศาล-ศาลเจ้า-หลักเมือง", "Shrines & city pillars")}</h1>'
        f'<p class="sn-intro">{intro}</p>'
        f'<h2>{bi("แผนที่", "The map")}</h2>'
        f"{map_html}{credit}"
        f'<h2>{bi("ทะเบียน — ตามชนิดของผู้ดูแล", "The register — by keeper kind")}</h2>'
        f"{kind_html}"
        f"{unv_html}"
        f'<h2>{bi("ก่อนไหว้", "Before you wai")}</h2>'
        f"{primer_html}"
        f'<p class="sn-note">{bi("ที่มาของทะเบียน", "Register data")}: <a href="data/shrines.json">data/shrines.json</a> · '
        + bi("ศาลที่มดยังไม่เจอ หรือป้ายที่ไม่ตรงทะเบียน — ", "A shrine the ants have not found, or a sign the register gets wrong — ")
        + f'<a href="suggest.html">{bi("บอกมด", "tell the ants")}</a></p>'
        + share_block(BASE + "san.html", "ศาล-ศาลเจ้า-หลักเมือง เชียงใหม่-เชียงราย · มดแดง", card=og))
    (DOCS / "san.html").write_text(page(
        "ศาล ศาลเจ้า หลักเมือง เชียงใหม่-เชียงราย — ทะเบียนพร้อมที่มา · Shrines & city pillars of Chiang Mai & Chiang Rai",
        body, depth=0, path="san.html",
        desc="ทะเบียนศาล ศาลเจ้า และหลักเมืองของเชียงใหม่-เชียงราย: เสาอินทขีล สะดือเมือง ปุงเถ่ากง ปู่แสะย่าแสะ ศาลบูรพกษัตริย์ เทวาลัย — แผนที่ ชนิดตามผู้ดูแล งานประจำปี พร้อมที่มาทุกแถว · The shrine register of Chiang Mai and Chiang Rai: city pillars, Chinese shrines, founder-king shrines, guardian spirits and devalayas — mapped and sourced",
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("ศาลเจ้า-หลักเมือง", "Shrines")}'))
    return {"page": 1, "register": len(rows), "with_records": n_rec,
            "awaiting": n_wait, "told_of": len(unv)}
