#!/usr/bin/env python3
"""ในเวียงหรือนอกเวียง — reading the moat (/moat.html). WO-37.

WHY THIS PAGE EXISTS. The first sorting question this city asks about any
address is one word wide: ในเวียงก่อ — inside the walls? Every resident
answers it without thinking and almost nobody can say how they know. The
answer is written all over town in nine different scripts — water, brick,
traffic, street names, postcodes, the slope of the ground — and a directory
that already holds the moat's own geometry can teach every one of them.

WHAT THIS PAGE IS. Nine ways to read which side you are on, ordered by the
distance they work from: the mountain (10 km) down to the paper in your hand
(0 m), ending with the reader's own machine. Nine ways for the nine named
crossings — five gates and four แจ่ง — which is not a coincidence anybody
planned, just a coincidence worth keeping.

WHERE THE FACTS COME FROM. Geometry is build.MOAT_POLY and _moat_crossings()
— the catalogue's own pins, never typed here (ride_rules learned why: a
hand-typed square once sat 372 m out of place). The census is taken live from
the records at build time, so the numbers heal themselves. The one-way ring
directions were measured 2026-08-27 from the roads snapshot in cache/roads/
(oneway=yes segments within 110 m of the corner-to-corner ring, all eight
roads agreeing); the street-name split and the ground levels carry their own
read dates. A dated measurement that goes stale reads as history; an undated
one reads as a lie.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
geography (doi) layer: the earth page, then the water page. Emits moat.html
+ moat.css.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CSS = """
.mo-intro{font-size:1.02rem;max-width:46rem}
.mo-note{font-size:.86rem;opacity:.78;max-width:46rem}
.mo-lead{max-width:46rem;border-left:3px solid rgba(0,0,0,.22);padding:.1rem 0 .1rem .9rem;
  margin:.9rem 0;font-size:1.02rem;line-height:1.6}
.mo-way{max-width:52rem;margin:1.6rem 0 1.9rem}
.mo-way h2{margin-bottom:.2rem}
.mo-way h2 .bead{display:inline-block;min-width:1.7em;text-align:center;
  border:1px solid var(--gold);border-radius:50%;margin-right:.35rem;
  font-size:.82em;padding:.08em 0;color:var(--gold);background:var(--card)}
.mo-range{font-size:.8rem;color:var(--mute);letter-spacing:.04em;margin:0 0 .5rem}
.mo-fig{max-width:52rem;margin:.7rem 0;border:1px solid var(--warm-border);
  border-radius:.6rem;background:var(--card);padding:.6rem}
.mo-fig svg{display:block;width:100%;height:auto}
.mo-cap{font-size:.84rem;opacity:.78;margin:.45rem .2rem 0;line-height:1.5}
.mo-catch{max-width:46rem;border-top:1px dashed var(--dashed);margin-top:.7rem;
  padding-top:.45rem;font-size:.9rem;line-height:1.55}
.mo-catch .lbl{font-weight:600;color:var(--ant-dark)}
.mo-census{display:flex;flex-wrap:wrap;gap:.6rem;max-width:52rem;margin:.8rem 0}
.mo-census .tile{border:1px solid var(--warm-border);border-radius:.6rem;
  background:var(--card);padding:.5rem .8rem;line-height:1.4}
.mo-census .n{font-size:1.3rem;font-weight:700;display:block}
.mo-check{max-width:46rem;border:2px solid var(--day);border-radius:.8rem;
  padding:1rem 1.1rem;margin:1rem 0;background:var(--card)}
.mo-btn{font-size:1.12rem;padding:.7rem 1.3rem;border-radius:.7rem;
  border:2px solid var(--ink);background:var(--gold-pale);cursor:pointer;
  font-family:inherit;line-height:1.4}
.mo-btn:active{transform:translateY(1px)}
.mo-verdict{font-size:1.35rem;font-weight:700;margin:.6rem 0 .2rem;min-height:1.2em}
.mo-verdict.in{color:var(--jade)}
.mo-verdict.out{color:var(--ant-dark)}
.mo-verdict.rim{color:var(--gold)}
.mo-detail{font-size:.95rem;line-height:1.6}
.mo-quiet{font-size:.8rem;opacity:.7;margin-top:.5rem}
.mo-tally{margin:.6rem 0 .2rem}
.mo-tally button{font-size:.98rem;padding:.4rem .9rem;border-radius:.6rem;
  border:1px solid var(--ink);background:var(--card-alt);cursor:pointer;
  font-family:inherit;margin-right:.5rem}
.mo-tally .par{font-weight:700}
.mo-gloss{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.mo-gloss td{padding:.34rem .5rem;border-bottom:1px solid rgba(0,0,0,.07);vertical-align:top}
.mo-gloss .th{font-size:1.06rem;white-space:nowrap}
.mo-gloss .rtgs{opacity:.72;font-style:italic;white-space:nowrap}
.mo-code{max-width:46rem;font-size:.8rem}
.mo-code pre{overflow-x:auto;background:var(--card-alt);border:1px solid var(--warm-border);
  border-radius:.5rem;padding:.6rem .8rem;line-height:1.5}
.mo-svgtxt{font-family:inherit}
@media (max-width:640px){.mo-gloss{font-size:.86rem}.mo-verdict{font-size:1.2rem}}
"""

# Measured 2026-08-27 from the roads snapshot (cache/roads/): every oneway=yes
# segment within 110 m of the corner-to-corner ring, summed for winding sense.
# Inner four counterclockwise, outer four clockwise, no dissenting segment.
RING_ROADS = {
    "inner": [("ถนนศรีภูมิ", "Si Phum", "N"), ("ถนนมูลเมือง", "Moon Mueang", "E"),
              ("ถนนบำรุงบุรี", "Bamrung Buri", "S"), ("ถนนอารักษ์", "Arak", "W")],
    "outer": [("ถนนมณีนพรัตน์", "Mani Nopparat", "N"), ("ถนนคชสาร", "Kotchasan", "E"),
              ("ถนนช่างหล่อ", "Chang Lo", "S"), ("ถนนบุญเรืองฤทธิ์", "Bunrueangrit", "W")],
}

# Thai script · RTGS · what it means. Same shape as the souvenir glossary:
# enough to match a word on a sign or in an address by its roots.
GLOSSARY = [
    ("เวียง", "wiang",
     "คำล้านนา — เมืองมีกำแพงมีคู ในเวียง/นอกเวียง คือคำถามแรกของทุกที่อยู่",
     "Lanna word for a walled, moated town (as in Wiang Kum Kam). "
     "ในเวียง nai wiang, inside; นอกเวียง nok wiang, outside — the first "
     "question any Chiang Mai address answers."),
    ("คูเมือง", "khu mueang",
     "คู = ร่องน้ำที่ขุด + เมือง — คนเมืองมักเรียกสั้น ๆ ว่า คู",
     "The moat — คู khu, a dug channel + เมือง mueang, town. Locals often "
     "just say khu."),
    ("แจ่ง", "chaeng",
     "คำเมือง แปลว่า มุม — ภาษากลางว่า มุม ได้ยิน 'แจ่ง' คือกำลังวนรอบเวียง",
     "Corner, in the northern tongue (standard Thai uses มุม mum). The four "
     "moat corners keep their Lanna name — hearing chaeng in directions "
     "means the old city is near."),
    ("แจ่งศรีภูมิ", "chaeng si phum",
     "มุมตะวันออกเฉียงเหนือ — ศรี (สิริมงคล) + ภูมิ (แผ่นดิน) ตำนานว่าการสร้างเมืองเริ่มที่มุมนี้",
     "The NE corner — si, auspicious glory (Skt. sri) + phum, ground (Skt. "
     "bhumi). Tradition holds the city's founding began at this corner."),
    ("แจ่งก๊ะต๊ำ", "chaeng katam",
     "มุมตะวันออกเฉียงใต้ — ก๊ะต๊ำ คือเครื่องมือดักปลาไม้ไผ่ มุมน้ำออกที่ปลาไปรวมกัน",
     "The SE corner — a katam is a bamboo fish trap; the low corner where "
     "the water (and the fish) head out."),
    ("แจ่งกู่เฮือง", "chaeng ku hueang",
     "มุมตะวันตกเฉียงใต้ — กู่ คือสถูปบรรจุอัฐิ ตำนานผูกมุมนี้ไว้กับกู่ของหมื่นเฮือง",
     "The SW corner — a ku is a reliquary stupa; tradition ties the name to "
     "the ku of a noble called Hueang."),
    ("แจ่งหัวลิน", "chaeng hua lin",
     "มุมตะวันตกเฉียงเหนือ — ลิน คือรางน้ำ (คำเมือง) หัวลิน = ปากทางน้ำเข้าเมือง มุมที่พื้นสูงสุด",
     "The NW corner — lin is a water conduit in the northern tongue, so hua "
     "lin is the head of the channel: where water entered the moat, at its "
     "highest corner. The name is a map of the plumbing."),
    ("ประตูท่าแพ", "pratu tha phae",
     "ประตูตะวันออก — ท่า (ท่าน้ำ) + แพ ทางไปท่าแพริมปิง",
     "The east gate — tha, a landing + phae, raft: the road to the river "
     "rafts. The gate faces the Ping, and the name says so."),
    ("ถนนมณีนพรัตน์", "thanon mani nopparat",
     "ถนนวงนอกด้านเหนือ — มณี + นพรัตน์ = แก้วเก้าประการ",
     "The outer north road — mani, jewel + nopparat, the NINE gems. Even "
     "the ring road counts to nine."),
    ("ถนนช่างหล่อ", "thanon chang lo",
     "ถนนวงนอกด้านใต้ — ช่าง + หล่อ ย่านช่างหล่อพระเก่า",
     "The outer south road — chang, craftsman + lo, to cast: the old "
     "Buddha-casters' quarter, nothing to do with elephants (ช้าง)."),
]


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")
    MOAT_POLY = g.get("MOAT_POLY")
    crossings = g["_moat_crossings"]()

    if not MOAT_POLY or len(crossings) < 9:
        return "SKIPPED — moat geometry missing from the catalogue"

    (DOCS / "moat.css").write_text(CSS)

    # ---- geometry, all from the catalogue's own pins ----------------------
    clat = sum(p[0] for p in MOAT_POLY) / 4
    clng = sum(p[1] for p in MOAT_POLY) / 4
    KX = math.cos(math.radians(clat))

    def metres(a, b):
        return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * KX)

    sides = [metres(MOAT_POLY[i], MOAT_POLY[(i + 1) % 4]) for i in range(4)]
    perimeter = sum(sides)
    walk_min = perimeter / 1000 / 4.5 * 60          # stroll, 4.5 km/h
    # shoelace area in km²
    mp = [((p[1] - clng) * 111320 * KX, (p[0] - clat) * 111320) for p in MOAT_POLY]
    area = abs(sum(mp[i][0] * mp[(i + 1) % 4][1] - mp[(i + 1) % 4][0] * mp[i][1]
                   for i in range(4))) / 2 / 1e6
    # bearing of the north side (nw -> ne): ~90° would be due east, so
    # tilt - 90 is how far the whole square leans off true cardinal
    nw, ne = MOAT_POLY[0], MOAT_POLY[1]
    tilt = math.degrees(math.atan2((ne[1] - nw[1]) * 111320 * KX,
                                   (ne[0] - nw[0]) * 111320))

    # Doi Suthep, from the catalogue if it holds the pin
    doi = next((r for r in data.get("cm", [])
                if (r.get("nameTh") or r.get("name")) == "ดอยสุเทพ"
                and r.get("lat") is not None), None)
    doi_bear = doi_km = None
    if doi:
        dx = (doi["lng"] - clng) * 111320 * KX
        dy = (doi["lat"] - clat) * 111320
        doi_bear = (math.degrees(math.atan2(dx, dy)) + 360) % 360
        doi_km = math.hypot(dx, dy) / 1000

    # ---- the census, taken live so the sentence heals itself --------------
    def in_poly(lat, lng):
        inside = False
        j = 3
        for i in range(4):
            yi, xi = MOAT_POLY[i]
            yj, xj = MOAT_POLY[j]
            if (xi > lng) != (xj > lng) and \
               lat < (yj - yi) * (lng - xi) / ((xj - xi) or 1e-12) + yi:
                inside = not inside
            j = i
        return inside

    cm = data.get("cm", [])
    inside_recs = [r for r in cm if r.get("lat") is not None
                   and in_poly(r["lat"], r["lng"])]
    n_in = len(inside_recs)

    def cat_of(r):
        c = r.get("cat")
        return c[0] if isinstance(c, list) and c else (c or "")

    n_wat = sum(1 for r in inside_recs if cat_of(r) == "wat")
    n_food = sum(1 for r in inside_recs if cat_of(r) == "food")
    n_hotel = sum(1 for r in inside_recs if cat_of(r) == "hotel")
    wat_gap = math.sqrt(area / n_wat) * 1000 if n_wat else 0

    # postcode forensics from the records that carry one
    import re as _re
    pc_in = pc_in_50200 = pc_out_50200 = 0
    for r in cm:
        if r.get("lat") is None:
            continue
        m = _re.search(r"\b(50\d{3})\b", r.get("address") or "")
        if not m:
            continue
        if in_poly(r["lat"], r["lng"]):
            pc_in += 1
            if m.group(1) == "50200":
                pc_in_50200 += 1
        elif m.group(1) == "50200":
            pc_out_50200 += 1
    pc_pct = round(pc_in_50200 * 100 / pc_in) if pc_in else 0

    # ground level across the old city, from the doi page's own transect
    ele_note = ""
    tp_path = ROOT / "data" / "terrain_profile.json"
    if tp_path.exists():
        tp = json.loads(tp_path.read_text())

        def ele_at(lng):
            i = round((lng - tp["lon_a"]) / tp["step"])
            return tp["ele"][i] if 0 <= i < len(tp["ele"]) else None

        w_ele = ele_at(min(p[1] for p in MOAT_POLY))
        e_ele = ele_at(max(p[1] for p in MOAT_POLY))
        if w_ele and e_ele and w_ele > e_ele:
            ele_note = bi(
                f"มดวัดเองจากเส้นระดับของหน้าดอย (อ่าน {esc(tp.get('read', ''))}): "
                f"กำแพงฝั่งตะวันตกอยู่สูง {w_ele:.0f} ม. ฝั่งตะวันออก {e_ele:.0f} ม. "
                "— พื้นทั้งเวียงเอียงออกจากดอยลงไปหาแม่น้ำ "
                "น้ำในคูจึงเข้าที่แจ่งหัวลินแล้วไหลไปทางก๊ะต๊ำ ตามที่ชื่อสองแจ่งบอกไว้ก่อนแล้ว",
                f"Measured from the doi page's own elevation transect (read "
                f"{esc(tp.get('read', ''))}): the west wall stands at "
                f"{w_ele:.0f} m, the east at {e_ele:.0f} m — the whole town "
                "leans away from the mountain, down toward the river. Moat "
                "water enters at Chaeng Hua Lin and drains toward Katam, "
                "exactly as the two corner names said all along.")

    # ---- SVG helpers ------------------------------------------------------
    gates = [c for c in crossings if c[4] == "gate"]
    corners = [c for c in crossings if c[4] == "corner"]

    def hero_map():
        """The moat to scale, from the catalogue pins: nine crossings named,
        the mountain off the west edge, the river off the east."""
        pad = 0.0038
        n = max(p[0] for p in MOAT_POLY) + pad
        s = min(p[0] for p in MOAT_POLY) - pad
        w = min(p[1] for p in MOAT_POLY) - pad / KX
        e = max(p[1] for p in MOAT_POLY) + pad / KX
        W = 720.0
        H = W * ((n - s) / ((e - w) * KX))

        def X(lng):
            return (lng - w) / (e - w) * W

        def Y(lat):
            return (n - lat) / (n - s) * H

        ring = " ".join("%.1f,%.1f" % (X(p[1]), Y(p[0])) for p in MOAT_POLY)
        # the water band: the corner ring, widened outward a touch to draw as
        # a band of water (the corners bound the water — build.py's rule)
        fat = 1.055
        ring_out = " ".join(
            "%.1f,%.1f" % (X(clng + (p[1] - clng) * fat), Y(clat + (p[0] - clat) * fat))
            for p in MOAT_POLY)
        parts = [
            '<polygon points="%s" fill="var(--jade-a)" stroke="var(--jade)" '
            'stroke-width="1.5"/>' % ring_out,
            '<polygon points="%s" fill="var(--paper)" stroke="var(--ant-dark)" '
            'stroke-width="2.5" stroke-dasharray="7 4"/>' % ring,
        ]
        for glat, glng, gth, gen, kind in crossings:
            x, y = X(glng), Y(glat)
            if kind == "gate":
                parts.append('<rect x="%.1f" y="%.1f" width="12" height="12" '
                             'fill="var(--paper)" stroke="var(--ink)" '
                             'stroke-width="2"/>' % (x - 6, y - 6))
            else:
                parts.append('<circle cx="%.1f" cy="%.1f" r="7" '
                             'fill="var(--gold-light)" stroke="var(--ink)" '
                             'stroke-width="2"/>' % (x, y))
            dx, dy = x - W / 2, y - H / 2
            if abs(dx) > abs(dy):
                anch = "start" if dx > 0 else "end"
                lx, ly = x + (14 if dx > 0 else -14), y + 4
            else:
                anch = "middle"
                lx, ly = x, y + (26 if dy > 0 else -14)
            # keep labels on the canvas: near the right edge a start-anchored
            # name runs off the drawing, so flip its anchor (and mirror left)
            if anch == "start" and lx > W - 150:
                anch, lx = "end", x - 14
            elif anch == "end" and lx < 150:
                anch, lx = "start", x + 14
            elif anch == "middle":
                lx = min(max(lx, 76), W - 76)
            parts.append('<text class="mo-svgtxt" x="%.1f" y="%.1f" '
                         'text-anchor="%s" font-size="13" fill="var(--ink)">'
                         '%s</text>' % (lx, ly, anch, esc(gth)))
        # centre label
        parts.append('<text class="mo-svgtxt" x="%.1f" y="%.1f" text-anchor="middle" '
                     'font-size="17" fill="var(--ink-soft)">ในเวียง</text>'
                     % (W / 2, H / 2 - 6))
        parts.append('<text class="mo-svgtxt" x="%.1f" y="%.1f" text-anchor="middle" '
                     'font-size="11" fill="var(--mute)">nai wiang — inside</text>'
                     % (W / 2, H / 2 + 12))
        # mountain west, river east
        parts.append('<text class="mo-svgtxt" x="8" y="%.1f" font-size="12" '
                     'fill="var(--jade-ink)">◀ ดอยสุเทพ%s</text>'
                     % (H / 2 + 40, " ~%.0f กม." % doi_km if doi_km else ""))
        parts.append('<text class="mo-svgtxt" x="%.1f" y="%.1f" font-size="12" '
                     'text-anchor="end" fill="var(--link)">แม่น้ำปิง ▶</text>'
                     % (W - 8, H / 2 + 40))
        # north arrow + scale bar (500 m)
        parts.append('<g stroke="var(--ink)" stroke-width="2" fill="none">'
                     '<line x1="%.1f" y1="34" x2="%.1f" y2="14"/>'
                     '<path d="M %.1f 20 L %.1f 14 L %.1f 20" fill="var(--ink)"/></g>'
                     '<text class="mo-svgtxt" x="%.1f" y="46" text-anchor="middle" '
                     'font-size="11" fill="var(--ink)">เหนือ</text>'
                     % (W - 40, W - 40, W - 45, W - 40, W - 35, W - 40))
        sx = 500.0 / (111320 * KX) / (e - w) * W
        parts.append('<line x1="16" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="var(--ink)" stroke-width="2"/>'
                     '<text class="mo-svgtxt" x="16" y="%.1f" font-size="11" '
                     'fill="var(--ink)">500 ม.</text>'
                     % (H - 16, 16 + sx, H - 16, H - 24))
        lbl = bi_text(
            "แผนที่คูเมืองตามหมุดจริงในสารบัญ — สี่แจ่ง ห้าประตู รวมเก้าทางข้าม "
            "ดอยสุเทพอยู่ทางตะวันตก แม่น้ำปิงทางตะวันออก",
            "The moat drawn to scale from the catalogue's own pins: four "
            "chaeng corners, five gates — nine named crossings. Doi Suthep "
            "lies west, the Ping river east.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, round(H), "".join(parts)))

    def rings_svg():
        """The two counter-rotating one-way rings, schematic."""
        W, H = 680, 520
        x0, y0, x1, y1 = 150, 110, 530, 410      # the water rectangle
        g_ = 26                                   # half-gap between rings
        parts = [
            '<rect x="%d" y="%d" width="%d" height="%d" fill="none" '
            'stroke="var(--jade-a)" stroke-width="34"/>' % (x0, y0, x1 - x0, y1 - y0),
            '<rect x="%d" y="%d" width="%d" height="%d" fill="none" '
            'stroke="var(--jade)" stroke-width="2" stroke-dasharray="2 6"/>'
            % (x0, y0, x1 - x0, y1 - y0),
        ]

        def arrow_line(ax, ay, bx, by, colour):
            mx, my = (ax + bx) / 2, (ay + by) / 2
            ang = math.degrees(math.atan2(by - ay, bx - ax))
            return ('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
                    'stroke="%s" stroke-width="3.5"/>'
                    '<path d="M -9 -6 L 3 0 L -9 6 Z" fill="%s" '
                    'transform="translate(%.0f %.0f) rotate(%.0f)"/>'
                    % (ax, ay, bx, by, colour, colour, mx, my, ang))

        # inner ring, counterclockwise (jade): E side heads N, N side W …
        i0x, i0y, i1x, i1y = x0 + g_, y0 + g_, x1 - g_, y1 - g_
        for (ax, ay, bx, by) in [(i1x, i1y, i1x, i0y), (i1x, i0y, i0x, i0y),
                                 (i0x, i0y, i0x, i1y), (i0x, i1y, i1x, i1y)]:
            parts.append(arrow_line(ax, ay, bx, by, "var(--jade)"))
        # outer ring, clockwise (ant red): N side heads E …
        o0x, o0y, o1x, o1y = x0 - g_, y0 - g_, x1 + g_, y1 + g_
        for (ax, ay, bx, by) in [(o0x, o0y, o1x, o0y), (o1x, o0y, o1x, o1y),
                                 (o1x, o1y, o0x, o1y), (o0x, o1y, o0x, o0y)]:
            parts.append(arrow_line(ax, ay, bx, by, "var(--ant)"))
        # road names, inner inside / outer outside
        inn = {r[2]: r for r in RING_ROADS["inner"]}
        out = {r[2]: r for r in RING_ROADS["outer"]}
        lab = [
            (inn["N"], (x0 + x1) / 2, y0 + g_ + 40, "middle", "var(--jade-ink)"),
            (inn["S"], (x0 + x1) / 2, y1 - g_ - 28, "middle", "var(--jade-ink)"),
            (inn["E"], x1 - g_ - 14, (y0 + y1) / 2, "end", "var(--jade-ink)"),
            (inn["W"], x0 + g_ + 14, (y0 + y1) / 2, "start", "var(--jade-ink)"),
            (out["N"], (x0 + x1) / 2, y0 - g_ - 14, "middle", "var(--ant-dark)"),
            (out["S"], (x0 + x1) / 2, y1 + g_ + 26, "middle", "var(--ant-dark)"),
            (out["E"], x1 + g_ + 10, (y0 + y1) / 2 - 40, "start", "var(--ant-dark)"),
            (out["W"], x0 - g_ - 10, (y0 + y1) / 2 - 40, "end", "var(--ant-dark)"),
        ]
        for (th, en, _), lx, ly, anch, col in lab:
            parts.append('<text class="mo-svgtxt" x="%.0f" y="%.0f" text-anchor="%s" '
                         'font-size="13" fill="%s">%s</text>'
                         % (lx, ly, anch, col, esc(th)))
        parts.append(
            '<text class="mo-svgtxt" x="%.0f" y="%.0f" text-anchor="middle" '
            'font-size="15" fill="var(--ink)">วงใน ทวนเข็ม</text>'
            '<text class="mo-svgtxt" x="%.0f" y="%.0f" text-anchor="middle" '
            'font-size="12" fill="var(--ink-soft)">inner ring — counterclockwise</text>'
            '<text class="mo-svgtxt" x="%.0f" y="%.0f" text-anchor="middle" '
            'font-size="15" fill="var(--ink)">วงนอก ตามเข็ม</text>'
            '<text class="mo-svgtxt" x="%.0f" y="%.0f" text-anchor="middle" '
            'font-size="12" fill="var(--ink-soft)">outer ring — clockwise</text>'
            % ((x0 + x1) / 2, (y0 + y1) / 2 - 26, (x0 + x1) / 2, (y0 + y1) / 2 - 8,
               (x0 + x1) / 2, (y0 + y1) / 2 + 22, (x0 + x1) / 2, (y0 + y1) / 2 + 40))
        parts.append(
            '<text class="mo-svgtxt" x="%.0f" y="%.0f" text-anchor="middle" '
            'font-size="13" fill="var(--gloss)">น้ำอยู่ขวามือของรถเสมอ ทั้งสองวง</text>'
            % ((x0 + x1) / 2, H - 14))
        lbl = bi_text(
            "ผังการเดินรถรอบคู: ถนนวงในสี่สายวิ่งทวนเข็มนาฬิกา ถนนวงนอกสี่สายวิ่งตามเข็ม "
            "น้ำจึงอยู่ขวามือของรถเสมอ",
            "Traffic schematic: the four inner ring roads run counterclockwise, "
            "the four outer ones clockwise — so the water always sits on the "
            "traffic's right.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def skyline_svg():
        W, H = 720, 210
        gy = H - 40
        parts = [
            # ground line + water gap
            '<line x1="0" y1="%d" x2="%d" y2="%d" stroke="var(--ink-soft)" '
            'stroke-width="2"/>' % (gy, W, gy),
            '<rect x="330" y="%d" width="60" height="12" fill="var(--jade-a)" '
            'stroke="var(--jade)" stroke-width="1"/>' % (gy - 6),
            # inside (left): chedi, temple roof, shophouses, palm
            '<path d="M 60 %d L 60 %d L 90 %d L 90 %d Z" fill="var(--card-alt)" '
            'stroke="var(--ink)" stroke-width="1.5"/>' % (gy, gy - 44, gy - 44, gy),
            '<path d="M 120 %d L 145 %d L 170 %d Z" fill="var(--gold-pale)" '
            'stroke="var(--gold)" stroke-width="1.5"/>' % (gy - 30, gy - 86, gy - 30),
            '<rect x="118" y="%d" width="54" height="30" fill="var(--card-alt)" '
            'stroke="var(--ink)" stroke-width="1.5"/>' % (gy - 30),
            '<circle cx="145" cy="%d" r="4" fill="var(--gold)"/>' % (gy - 92),
            '<rect x="200" y="%d" width="80" height="38" fill="var(--card)" '
            'stroke="var(--ink)" stroke-width="1.5"/>' % (gy - 38),
            '<path d="M 300 %d C 292 %d 288 %d 292 %d M 300 %d C 308 %d 312 %d 308 %d '
            'M 300 %d L 300 %d" stroke="var(--jade)" stroke-width="2.5" fill="none"/>'
            % (gy - 52, gy - 62, gy - 66, gy - 70, gy - 52, gy - 62, gy - 66, gy - 70,
               gy - 52, gy),
            # outside (right): towers
            '<rect x="430" y="%d" width="46" height="118" fill="var(--card-alt)" '
            'stroke="var(--ink)" stroke-width="1.5"/>' % (gy - 118),
            '<rect x="500" y="%d" width="52" height="150" fill="var(--card)" '
            'stroke="var(--ink)" stroke-width="1.5"/>' % (gy - 150),
            '<rect x="580" y="%d" width="44" height="96" fill="var(--card-alt)" '
            'stroke="var(--ink)" stroke-width="1.5"/>' % (gy - 96),
        ]
        for bx, bw, bh in [(430, 46, 118), (500, 52, 150), (580, 44, 96)]:
            for fy in range(gy - bh + 12, gy - 8, 16):
                parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" '
                             'stroke="var(--mute)" stroke-width="1"/>'
                             % (bx + 5, fy, bx + bw - 5, fy))
        parts.append('<text class="mo-svgtxt" x="180" y="%d" text-anchor="middle" '
                     'font-size="13" fill="var(--ink)">ในเวียง — ยอดเจดีย์ หลังคาวัด ยอดตาล</text>'
                     % (H - 12))
        parts.append('<text class="mo-svgtxt" x="530" y="%d" text-anchor="middle" '
                     'font-size="13" fill="var(--ink)">นอกเวียง — ตึกยืนได้สูง</text>'
                     % (H - 12))
        lbl = bi_text(
            "เส้นขอบฟ้าสองแบบ: ฝั่งในเวียงของสูงสุดคือยอดเจดีย์กับยอดตาล ฝั่งนอกตึกสูงตั้งได้",
            "Two skylines: inside the walls the tallest things are chedi "
            "spires and palm crowns; towers stand only outside.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def waters_svg():
        W, H = 720, 200
        panels = [
            (10, "คูเมือง — นิ่ง ตรง หักมุมฉาก ขอบอิฐ", "khu mueang"),
            (250, "แม่น้ำปิง — ไหล กว้าง โค้งตามใจ", "mae nam ping"),
            (490, "คลองแม่ข่า — แคบ คดในซอย", "khlong mae kha"),
        ]
        parts = []
        for x, cap, rtgs in panels:
            parts.append('<rect x="%d" y="14" width="220" height="130" rx="8" '
                         'fill="var(--card)" stroke="var(--warm-border)"/>' % x)
            parts.append('<text class="mo-svgtxt" x="%d" y="168" font-size="12.5" '
                         'fill="var(--ink)">%s</text>' % (x + 4, esc(cap)))
            parts.append('<text class="mo-svgtxt" x="%d" y="186" font-size="10.5" '
                         'font-style="italic" fill="var(--mute)">%s</text>'
                         % (x + 4, rtgs))
        # moat: straight band with a right angle + brick ticks
        parts.append('<path d="M 30 120 L 150 120 L 150 40" stroke="var(--jade)" '
                     'stroke-width="16" fill="none"/>')
        for tx in range(40, 140, 20):
            parts.append('<rect x="%d" y="104" width="10" height="5" '
                         'fill="var(--ant-dark)"/>' % tx)
        # river: wide wavy band
        parts.append('<path d="M 270 40 C 320 70 300 110 350 130 C 385 143 420 120 450 132" '
                     'stroke="var(--link)" stroke-width="26" fill="none" '
                     'stroke-linecap="round" opacity=".55"/>')
        # khlong: thin wiggle
        parts.append('<path d="M 510 40 C 530 70 560 80 555 105 C 550 125 585 130 600 140" '
                     'stroke="var(--jade-ink)" stroke-width="6" fill="none"/>')
        lbl = bi_text(
            "น้ำสามสาย: คูเมืองนิ่งเป็นเส้นตรงหักมุมฉากมีขอบอิฐ แม่น้ำปิงกว้างและไหล "
            "คลองแม่ข่าแคบและคดไปตามซอย",
            "Three waters: the moat stands still in straight lines with right "
            "angles and brick edges; the Ping is wide and moving; Khlong Mae "
            "Kha is a narrow wiggle between sois.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def parity_svg():
        W, H = 720, 250
        # the square, and a walk of three straight legs whose crossings are
        # unmistakable: out -> in (left edge), in -> out (right edge),
        # out -> in (right edge again). Odd count, so the walk ends inside.
        parts = ['<rect x="270" y="40" width="180" height="170" '
                 'fill="var(--gold-pale)" fill-opacity=".35" stroke="var(--jade)" '
                 'stroke-width="10" stroke-opacity=".5"/>']
        parts.append('<path d="M 40 120 L 330 120 L 560 90 L 390 180" '
                     'stroke="var(--ant)" stroke-width="3" fill="none" '
                     'stroke-dasharray="1 7" stroke-linecap="round" '
                     'stroke-linejoin="round"/>')
        parts.append('<circle cx="40" cy="120" r="6" fill="var(--ink)"/>')
        parts.append('<text class="mo-svgtxt" x="34" y="146" font-size="12" '
                     'fill="var(--ink)">เริ่ม — นอก</text>')
        for (bx, by, n) in [(270, 120, "๑"), (450, 104, "๒"), (450, 148, "๓")]:
            parts.append('<circle cx="%d" cy="%d" r="12" fill="var(--paper)" '
                         'stroke="var(--ant-dark)" stroke-width="2"/>'
                         '<text class="mo-svgtxt" x="%d" y="%d" text-anchor="middle" '
                         'font-size="13" fill="var(--ant-dark)">%s</text>'
                         % (bx, by, bx, by + 5, n))
        parts.append('<circle cx="390" cy="180" r="7" fill="none" '
                     'stroke="var(--ink)" stroke-width="2.5"/>')
        parts.append('<text class="mo-svgtxt" x="300" y="203" font-size="12" '
                     'fill="var(--ink)">จบ — ข้ามคี่ (๓) ครั้ง = สลับเป็นใน</text>')
        parts.append('<text class="mo-svgtxt" x="40" y="30" font-size="13" '
                     'fill="var(--ink-soft)">ข้ามน้ำเลขคี่ = สลับข้าง · เลขคู่ = ข้างเดิม</text>')
        lbl = bi_text(
            "เส้นทางเดินข้ามคูสามครั้ง — เริ่มนอกเวียง ข้ามเข้าหนึ่ง ออกสอง เข้าสาม "
            "เลขคี่จึงจบข้างใน",
            "A walk crossing the moat three times: starting outside, the count "
            "runs in, out, in — an odd total, so the walk ends inside. Odd "
            "crossings flip your side; even keep it.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def loop_svg():
        W, H = 720, 190
        parts = [
            # left: closed loop with return arrow
            '<rect x="60" y="30" width="150" height="110" rx="6" fill="none" '
            'stroke="var(--jade)" stroke-width="9" stroke-opacity=".6"/>',
            '<path d="M -8 -6 L 6 0 L -8 6 Z" fill="var(--jade-ink)" '
            'transform="translate(135 30) rotate(180)"/>',
            '<circle cx="210" cy="85" r="6" fill="var(--ink)"/>',
            '<text class="mo-svgtxt" x="62" y="170" font-size="12.5" fill="var(--ink)">'
            'เดินเลียบคู %s ม. — ชั่วโมงเศษกลับถึงที่เดิม</text>' % f"{perimeter:,.0f}",
            # right: the river runs off the page
            '<path d="M 430 40 C 480 70 470 110 530 130 C 580 146 640 130 700 150" '
            'stroke="var(--link)" stroke-width="9" fill="none" stroke-opacity=".55"/>',
            '<path d="M -8 -6 L 6 0 L -8 6 Z" fill="var(--link)" '
            'transform="translate(697 149) rotate(16)"/>',
            '<circle cx="430" cy="40" r="6" fill="var(--ink)"/>',
            '<text class="mo-svgtxt" x="432" y="170" font-size="12.5" fill="var(--ink)">'
            'เดินเลียบปิง — แม่น้ำไม่พากลับบ้าน</text>',
        ]
        lbl = bi_text(
            "เส้นปิดกับเส้นเปิด: เดินเลียบคูเมืองราวหกกิโลเมตรจะวนกลับถึงที่เดิม "
            "เดินเลียบแม่น้ำจะไปเรื่อย ๆ ไม่กลับมา",
            "Closed curve versus open: walk the moat's six kilometres and you "
            "return to your own footprints; walk the river and it simply "
            "carries on without you ever coming back.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def mountain_svg():
        W, H = 720, 200
        hy = 130
        parts = [
            '<line x1="0" y1="%d" x2="%d" y2="%d" stroke="var(--ink-soft)" '
            'stroke-width="2"/>' % (hy, W, hy),
            # the ridge filling the west
            '<path d="M 0 %d L 60 70 L 130 46 L 200 78 L 260 100 L 320 %d Z" '
            'fill="var(--jade-b)" stroke="var(--jade-ink)" stroke-width="1.5"/>' % (hy, hy),
            '<circle cx="130" cy="40" r="3.5" fill="var(--gold)"/>',
            '<text class="mo-svgtxt" x="130" y="28" text-anchor="middle" font-size="11.5" '
            'fill="var(--ink)">วัดพระธาตุ</text>',
            # setting sun
            '<circle cx="96" cy="58" r="13" fill="var(--gold-light)" '
            'stroke="var(--gold)" stroke-width="2"/>',
            '<text class="mo-svgtxt" x="40" y="%d" font-size="13" fill="var(--ink)">'
            'ตะวันตก — ดอยสุเทพ</text>' % (hy + 24),
            '<text class="mo-svgtxt" x="%d" y="%d" text-anchor="end" font-size="13" '
            'fill="var(--ink)">ตะวันออก — แม่น้ำปิง</text>' % (W - 20, hy + 24),
            '<text class="mo-svgtxt" x="%d" y="%d" text-anchor="end" font-size="12" '
            'fill="var(--mute)">พื้นเอียงลงทางนี้ ▶</text>' % (W - 20, hy - 12),
        ]
        if doi_bear:
            parts.append('<text class="mo-svgtxt" x="40" y="%d" font-size="11.5" '
                         'fill="var(--gloss)">จากใจกลางเวียง ยอดดอยอยู่ทาง ~%.0f° '
                         '(ตะวันตกค่อนเหนือ) ห่าง ~%.0f กม.</text>'
                         % (hy + 44, doi_bear, doi_km))
        lbl = bi_text(
            "เส้นขอบฟ้าด้านตะวันตก: แนวดอยสุเทพเต็มขอบฟ้า พระอาทิตย์ตกหลังดอย "
            "พื้นเมืองเอียงลงไปทางแม่น้ำทางตะวันออก",
            "The western horizon: the Doi Suthep ridge fills it and the sun "
            "sets behind the ridge; the ground tilts gently down toward the "
            "river in the east.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def names_svg():
        W, H = 700, 330
        parts = ['<rect x="170" y="60" width="360" height="220" fill="var(--gold-pale)" '
                 'fill-opacity=".3" stroke="var(--jade)" stroke-width="8" '
                 'stroke-opacity=".45"/>']
        inside_names = ["ถนนราชดำเนิน", "ถนนราชวิถี", "ถนนราชภาคินัย",
                        "ถนนราชมรรคา", "ถนนพระปกเกล้า", "ถนนสิงหราช",
                        "ถนนจ่าบ้าน", "ถนนอินทวโรรส"]
        for i, nm in enumerate(inside_names):
            parts.append('<text class="mo-svgtxt" x="350" y="%d" text-anchor="middle" '
                         'font-size="13.5" fill="var(--jade-ink)">%s</text>'
                         % (92 + i * 24, esc(nm)))
        outside_names = [("ถนนราชวงศ์", 348, 40), ("ถนนราชเชียงแสน", 360, 306),
                         ("ถนนนิมมานเหมินท์", 84, 130), ("ถนนช้างคลาน", 616, 250),
                         ("ถนนท่าแพ", 600, 130), ("ถนนห้วยแก้ว", 84, 240)]
        for nm, x, y in outside_names:
            parts.append('<text class="mo-svgtxt" x="%d" y="%d" text-anchor="middle" '
                         'font-size="12.5" fill="var(--ant-dark)">%s</text>'
                         % (x, y, esc(nm)))
        lbl = bi_text(
            "ป้ายถนนสองฝั่ง: ชื่อชุด ราช- และพระนามกษัตริย์กระจุกอยู่ในเวียง "
            "ส่วนราชวงศ์กับราชเชียงแสนยืนนอกเวียงไว้หลอกคนอ่านป้าย",
            "Street names, both sides: the royal Ratcha- cluster stands "
            "inside the walls — while Ratchawong and Ratcha Chiang Saen "
            "stand outside precisely to fool sign-readers.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    def postcode_svg():
        W, H = 660, 120
        w1 = int(430 * pc_in_50200 / max(pc_in, 1))
        parts = [
            '<text class="mo-svgtxt" x="8" y="30" font-size="13" fill="var(--ink)">'
            'ที่อยู่ฝั่งในที่มีรหัสไปรษณีย์ (%d รายการในสารบัญ)</text>' % pc_in,
            '<rect x="8" y="42" width="430" height="26" fill="var(--card-alt)" '
            'stroke="var(--warm-border)"/>',
            '<rect x="8" y="42" width="%d" height="26" fill="var(--jade-b)"/>' % w1,
            '<text class="mo-svgtxt" x="16" y="60" font-size="13" fill="var(--jade-ink)">'
            '50200 — %d%%</text>' % pc_pct,
            '<text class="mo-svgtxt" x="8" y="98" font-size="12" fill="var(--ink-soft)">'
            'แต่ 50200 ยังพบนอกเวียงอีก %d รายการ — รหัสล้นข้ามน้ำ</text>' % pc_out_50200,
        ]
        lbl = bi_text(
            "แผนภูมิรหัสไปรษณีย์: ที่อยู่ฝั่งในส่วนใหญ่เขียน 50200 "
            "แต่รหัสเดียวกันพบนอกเวียงด้วย — ใช้ตัดออกได้ ใช้ยืนยันไม่ได้",
            "Postcode bar: most inside addresses read 50200, but the same "
            "code spills outside the water — it can rule out, never rule in.")
        return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
                'xmlns="http://www.w3.org/2000/svg">%s</svg>'
                % (att(lbl), W, H, "".join(parts)))

    # ---- the checker payload ----------------------------------------------
    payload = {
        "poly": [[round(p[0], 6), round(p[1], 6)] for p in MOAT_POLY],
        "cross": [[round(c[0], 6), round(c[1], 6), c[2], c[3], c[4]]
                  for c in crossings],
        "kx": round(KX, 6),
    }
    checker_js = """
(function(){
var M=JSON.parse(document.getElementById('mo-data').textContent);
var KX=M.kx,P=M.poly;
function mx(la,ln){return [(ln-P[0][1])*111320*KX,(la-P[0][0])*111320];}
function inPoly(la,ln){var i,j,c=false;
 for(i=0,j=P.length-1;i<P.length;j=i++){
  if(((P[i][1]>ln)!==(P[j][1]>ln))&&
   (la<(P[j][0]-P[i][0])*(ln-P[i][1])/((P[j][1]-P[i][1])||1e-12)+P[i][0]))c=!c;}
 return c;}
function chordDist(la,ln){var p=mx(la,ln),best=1e9,i;
 for(i=0;i<4;i++){var a=mx(P[i][0],P[i][1]),b=mx(P[(i+1)%4][0],P[(i+1)%4][1]);
  var vx=b[0]-a[0],vy=b[1]-a[1],L=vx*vx+vy*vy;
  var t=Math.max(0,Math.min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vy)/L));
  var dx=p[0]-(a[0]+t*vx),dy=p[1]-(a[1]+t*vy);
  best=Math.min(best,Math.hypot(dx,dy));}
 return best;}
var WINDS=[['เหนือ','N'],['ตะวันออกเฉียงเหนือ','NE'],['ตะวันออก','E'],
 ['ตะวันออกเฉียงใต้','SE'],['ใต้','S'],['ตะวันตกเฉียงใต้','SW'],
 ['ตะวันตก','W'],['ตะวันตกเฉียงเหนือ','NW']];
function biSpan(th,en){return '<span class="bi"><span class="th" lang="th">'+th+
 '</span><span class="en" lang="en"><span class="th" lang="th"> \\u00b7 </span>'+
 en+'</span></span>';}
function tell(pos){
 var la=pos.coords.latitude,ln=pos.coords.longitude,acc=pos.coords.accuracy||0;
 var isin=inPoly(la,ln),d=chordDist(la,ln);
 var v=document.getElementById('mo-verdict'),
     det=document.getElementById('mo-detail');
 var best=null,i;
 for(i=0;i<M.cross.length;i++){var c=M.cross[i];
  var dx=(c[1]-ln)*111320*KX,dy=(c[0]-la)*111320,dd=Math.hypot(dx,dy);
  if(!best||dd<best.d)best={d:dd,th:c[2],en:c[3],
   w:WINDS[Math.round((((Math.atan2(dx,dy)*180/Math.PI)+360)%360)/45)%8]};}
 if(d<=60){v.className='mo-verdict rim';
  v.innerHTML=biSpan('ริมคูพอดี — บนสะพาน ริมตลิ่ง หรือถนนเลียบคู',
   'right on the rim: a bridge, a bank, a ring road');}
 else if(isin){v.className='mo-verdict in';
  v.innerHTML=biSpan('ในเวียง','inside the walls');}
 else{v.className='mo-verdict out';
  v.innerHTML=biSpan('นอกเวียง','outside the walls');}
 var lines=[];
 lines.push(biSpan('ห่างจากน้ำราว '+Math.round(d)+' ม.',
  'about '+Math.round(d)+' m from the water'));
 if(best&&best.d<25)lines.push(biSpan('อยู่ตรง'+best.th+'พอดี',
  'right at '+best.en));
 else if(best)lines.push(biSpan('ทางข้ามใกล้สุด: '+best.th+' ~'+
  Math.round(best.d)+' ม. ทางทิศ'+best.w[0],
  'nearest crossing: '+best.en+', ~'+Math.round(best.d)+' m '+best.w[1]));
 if(acc>150)lines.push(biSpan('สัญญาณหลวม \\u00b1'+Math.round(acc)+
  ' ม. — คำตอบริมคูอาจคลาดฝั่ง','loose fix \\u00b1'+Math.round(acc)+
  ' m — near the rim the verdict can wobble'));
 det.innerHTML=lines.join('<br>');}
function oops(){var v=document.getElementById('mo-verdict');
 v.className='mo-verdict';
 v.innerHTML=biSpan('เครื่องไม่บอกก็ไม่เป็นไร — เก้าทางข้างบนยังอยู่ครบ',
  'no fix from the machine — the nine ways above still work');}
var b=document.getElementById('mo-btn');
if(b)b.addEventListener('click',function(){
 if(!navigator.geolocation){oops();return;}
 b.disabled=true;setTimeout(function(){b.disabled=false;},4000);
 navigator.geolocation.getCurrentPosition(tell,oops,
  {enableHighAccuracy:true,timeout:12000,maximumAge:30000});});
var n=0,par=document.getElementById('mo-par');
var b1=document.getElementById('mo-cross'),b0=document.getElementById('mo-reset');
function showPar(){if(!par)return;
 par.innerHTML=biSpan('ข้ามแล้ว '+n+' ครั้ง — ตอนนี้อยู่'+
  (n%2? 'อีกข้างจากตอนเริ่ม':'ข้างเดิมกับตอนเริ่ม'),
  n+' crossing'+(n===1?'':'s')+' — you are on '+
  (n%2? 'the other side from where you started':'the same side you started'));}
if(b1)b1.addEventListener('click',function(){n++;showPar();});
if(b0)b0.addEventListener('click',function(){n=0;showPar();});
})();
"""

    # ---- assemble the page -------------------------------------------------
    def way(num, th_title, en_title, range_th, range_en, inner_html):
        return ('<section class="mo-way"><h2><span class="bead">' + num + "</span>"
                + bi(th_title, en_title) + "</h2>"
                + '<p class="mo-range">' + bi_text(range_th, range_en) + "</p>"
                + inner_html + "</section>")

    def fig(svg, cap_th, cap_en):
        return ('<figure class="mo-fig">' + svg
                + '<figcaption class="mo-cap">' + bi(cap_th, cap_en)
                + "</figcaption></figure>")

    def catch(th, en):
        return ('<p class="mo-catch"><span class="lbl">'
                + bi("ข้อควรระวัง", "the catch") + "</span> — "
                + bi(th, en) + "</p>")

    gloss_html = ('<table class="mo-gloss"><tbody>' + "".join(
        '<tr><td class="th">' + esc(th) + '</td><td class="rtgs">' + esc(rtgs)
        + "</td><td>" + bi(d_th, d_en) + "</td></tr>"
        for th, rtgs, d_th, d_en in GLOSSARY) + "</tbody></table>")

    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "name": "ในเวียงหรือนอกเวียง — Inside or outside the moat",
          "url": BASE + "moat.html",
          "inLanguage": ["th", "en"],
          "about": ["คูเมืองเชียงใหม่", "Chiang Mai moat", "เมืองเก่าเชียงใหม่",
                    "Chiang Mai old city"]}
    head = ('<link rel="stylesheet" href="moat.css">'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + "</script>")

    # The page's own card (make_moat_card.py) — the square over the night
    # ground with its nine crossings lit. Missing file falls back to the
    # brand card, the shelf_og discipline: the build never waits on Chrome.
    og = "og/moat.png" if (ROOT / "assets" / "og" / "moat.png").exists() else None

    body = (
        "<h1>" + bi("ในเวียง หรือ นอกเวียง?", "Inside the walls, or out?") + "</h1>"

        + '<p class="mo-intro">' + bi(
            "อยู่เชียงใหม่ไม่กี่วันก็จะเจอคำถามที่คนเมืองใช้แบ่งทุกที่อยู่: ในเวียงก่อ — "
            "เวียง เป็นคำล้านนา แปลว่าเมืองที่มีกำแพงมีคู "
            "คูเมืองรูปสี่เหลี่ยมขุดไว้แต่แรกสร้างเมื่อ พ.ศ. ๑๘๓๙ "
            f"ด้านละราวกิโลเมตรครึ่ง เดินรอบ {perimeter:,.0f} เมตร "
            "ทุกอย่างในเมืองนี้เรียงตัวรอบคำตอบของคำถามเดียวนี้ "
            "แต่พอยืนอยู่กลางซอย ใครจะรู้ว่าตัวเองอยู่ข้างไหน — หน้านี้รวมเก้าทางรู้ "
            "เรียงจากทางที่มองเห็นแต่ไกล ไปจนถึงทางที่ต้องก้มอ่านกระดาษ",
            "A few days in Chiang Mai and the sorting question arrives: nai "
            "wiang ko? — are you inside? เวียง wiang is the Lanna word for a "
            "walled, moated town. The square moat (คูเมือง khu mueang — khu, "
            "dug channel + mueang, town) has ringed this one since its "
            f"founding in 1296: about a kilometre and a half per side, "
            f"{perimeter:,.0f} m around. The whole city sorts itself by which "
            "side of that water you stand on — and yet, standing in the "
            "middle of a soi, who can tell? Here are nine ways to know, "
            "ordered from the clue you can read at ten kilometres down to "
            "the one printed on an envelope.")
        + "</p>"

        + '<p class="mo-lead">' + bi(
            "เก้าทางรู้ สำหรับเก้าทางข้าม — คูเมืองมีประตูห้า แจ่งสี่ "
            "รวมเก้าจุดข้ามที่คนเมืองเรียกชื่อได้ เลขเก้าไม่ได้ตั้งใจ แต่ตั้งใจเก็บไว้",
            "Nine ways to know, for the nine named crossings — five gates and "
            "four chaeng corners. Nobody planned that the counts would match; "
            "it is the kind of coincidence one keeps.")
        + "</p>"

        + fig(hero_map(),
              f"สี่แจ่ง ห้าประตู วาดตามหมุดจริงในสารบัญ — ด้านเหนือ {sides[0]:,.0f} ม. "
              f"ตะวันออก {sides[1]:,.0f} ม. ใต้ {sides[2]:,.0f} ม. ตะวันตก {sides[3]:,.0f} ม. "
              f"พื้นที่ข้างใน {area:.2f} ตร.กม. และจัตุรัสนี้เบนจากทิศจริงราว {tilt - 90:+.1f}°",
              f"Four chaeng, five gates, drawn from the catalogue's own pins — "
              f"north side {sides[0]:,.0f} m, east {sides[1]:,.0f} m, south "
              f"{sides[2]:,.0f} m, west {sides[3]:,.0f} m; {area:.2f} km² "
              f"inside, and the whole square leans {tilt - 90:+.1f}° off true "
              "cardinal.")

        # ---- ๑ the mountain ------------------------------------------------
        + way("๑", "ดอยคือกำแพงทิศตะวันตก", "The mountain is the west wall",
              "ใช้ได้จากทุกที่ในเมือง — ระยะ ๑๐ กิโลเมตร",
              "works from anywhere in town — the 10 km clue",
              "<p>" + bi(
                  "เชียงใหม่มีเข็มทิศที่มองเห็นด้วยตา: แนวดอยสุเทพยืนเต็มขอบฟ้าตะวันตกเสมอ "
                  "หันหน้าเข้าดอยคือหันไปตะวันตกโดยประมาณ แล้วทุกทางในหน้านี้ก็เริ่มใช้ได้ "
                  + (f"จากใจกลางเวียง ยอดดอยอยู่ทางราว ๆ {doi_bear:.0f}° "
                     f"ห่าง {doi_km:.0f} กิโลเมตร (คำนวณจากหมุดในสารบัญ) " if doi_bear else "")
                  + "ตอนเย็นพระอาทิตย์ตกหลังแนวดอยพอดี",
                  "Chiang Mai carries a compass you can see: the Doi Suthep "
                  "ridge fills the western horizon, always. Face the mountain "
                  "and you face roughly west — and every other way on this "
                  "page starts working. "
                  + (f"From the moat's centre the summit bears about "
                     f"{doi_bear:.0f}°, {doi_km:.0f} km out (computed from "
                     "the catalogue's own pin). " if doi_bear else "")
                  + "In the evening the sun goes down behind the ridge.")
              + "</p>"
              + fig(mountain_svg(),
                    "ขอบฟ้าตะวันตก — และพื้นเมืองเอียงหนีดอยลงไปหาแม่น้ำ",
                    "The western horizon — and the ground leans away from the "
                    "mountain, down toward the river.")
              + ("<p class='mo-note'>" + ele_note + "</p>" if ele_note else "")
              + catch("ในซอยแคบ ตึกบังดอยได้ และหน้าฝนเมฆก็บังทั้งแนว — "
                      "วันไหนมองไม่เห็น ใช้ทางถัดไป",
                      "Deep in a narrow soi the buildings hide the ridge, and "
                      "in the rainy season the clouds do — on those days, "
                      "read on."))

        # ---- ๒ the skyline -------------------------------------------------
        + way("๒", "อ่านเส้นขอบฟ้า", "Read the skyline",
              "ใช้ได้ในระยะไม่กี่ร้อยเมตร", "the few-hundred-metre clue",
              "<p>" + bi(
                  "ในเวียง ของที่สูงที่สุดคือยอดเจดีย์ หลังคาวัด กับยอดตาล — "
                  "ตึกสูงเป็นแถบ ๆ ยืนอยู่นอกเวียงทั้งนั้น "
                  "ถ้าคอนโดตั้งอยู่ใกล้ ๆ ตัวจนต้องแหงนคอ แทบแน่ว่ากำลังยืนอยู่นอก "
                  "ถ้ารอบตัวไม่มีอะไรเกินยอดตาลเลย น่าจะอยู่ใน",
                  "Inside the walls the tallest things are chedi spires, "
                  "temple roofs and palm crowns — the tower blocks all stand "
                  "outside. If a condo looms close enough to crane your neck "
                  "at, you are almost certainly outside; if nothing near you "
                  "outgrows a palm tree, you are probably in.")
              + "</p>"
              + fig(skyline_svg(),
                    "สังเกตของใกล้ตัว ไม่ใช่ของไกล — ตึกไกล ๆ โผล่หลังหลังคาได้",
                    "Judge what stands NEAR you, not the distance — far "
                    "towers can still peek over old-city roofs.")
              + catch("ทางนี้บอกเป็นแนวโน้ม ไม่ใช่เส้นแบ่งคม ๆ — ยืนริมคูฝั่งในก็เห็นตึกฝั่งตรงข้ามได้",
                      "A tendency, not a knife edge — from the inner bank you "
                      "can see towers across the water plainly."))

        # ---- ๓ the waters ---------------------------------------------------
        + way("๓", "น้ำจริงกับน้ำหลอก", "The water, and its impostors",
              "ใช้ได้เมื่อเห็นน้ำ — ระยะร้อยเมตร", "the hundred-metre clue: seeing water",
              "<p>" + bi(
                  "เจอน้ำไม่ได้แปลว่าเจอคูเมืองเสมอไป เมืองนี้มีน้ำหลายสาย "
                  "คูเมืองคือน้ำนิ่ง เดินเป็นเส้นตรง หักมุมฉาก ขอบเป็นอิฐ "
                  "แม่น้ำปิงกว้างกว่ามาก ไหลจริง และโค้งตามใจตัวเอง "
                  "คลองแม่ข่าแคบ คดไปตามหลังบ้าน ส่วนคลองชลประทานอยู่ไกลออกไปทางตะวันตก "
                  "ถ้าน้ำตรงหน้านิ่ง ตรง และเลี้ยวเป็นมุมฉากได้ นั่นแหละคู",
                  "Meeting water does not yet mean meeting the moat — this "
                  "town keeps several. The moat stands still, runs dead "
                  "straight, turns right angles, and wears brick edges. The "
                  "Ping is far wider, actually flows, and bends as it "
                  "pleases. Khlong Mae Kha is a narrow wiggle behind houses, "
                  "and the irrigation canal lies further west. If the water "
                  "in front of you is still, straight and cornered — that is "
                  "the one.")
              + "</p>"
              + fig(waters_svg(),
                    "น้ำสามสาย สามนิสัย", "Three waters, three temperaments")
              + catch("เห็นคูแล้วรู้แค่ว่าอยู่ขอบ — ยังไม่รู้ฝั่ง ไปต่อทาง ๕",
                      "Seeing the moat only says you are at the edge — which "
                      "bank is way 5's job."))

        # ---- ๔ bricks and chaeng -------------------------------------------
        + way("๔", "อิฐ กับ แจ่ง", "Bricks, and the chaeng",
              "ใช้ได้ริมคู — และในชื่อสถานที่", "at the rim — and inside place names",
              "<p>" + bi(
                  "กำแพงอิฐเหลือให้เห็นชัดที่มุมทั้งสี่ ซึ่งคนเมืองไม่เรียกว่า มุม "
                  "แต่เรียกว่า แจ่ง — คำเมืองแท้ ๆ ที่อยู่รอดมากับตัวกำแพงเอง "
                  "ได้ยินชื่อ แจ่งศรีภูมิ แจ่งก๊ะต๊ำ แจ่งกู่เฮือง แจ่งหัวลิน เมื่อไร "
                  "แปลว่ากำลังวนอยู่ขอบเวียงพอดี และชื่อแจ่งยังเป็นแผนที่ในตัว: "
                  "หัวลิน คือหัวรางน้ำเข้าที่มุมสูงสุด ก๊ะต๊ำ คือลอบดักปลาที่มุมน้ำออก",
                  "The brick wall survives most visibly at the four corners — "
                  "which this city does not call มุม mum like standard Thai, "
                  "but แจ่ง chaeng, a Lanna word that outlived the kingdom "
                  "alongside the bricks themselves. Hear Chaeng Si Phum, "
                  "Chaeng Katam, Chaeng Ku Hueang or Chaeng Hua Lin and you "
                  "are orbiting the rim. The names are a map of their own: "
                  "hua lin, head of the water conduit, at the high corner "
                  "where water enters; katam, the bamboo fish trap, at the "
                  "low corner where it leaves.")
              + "</p>"
              + catch("กำแพงดินแนวโค้งด้านตะวันออกเฉียงใต้ (แถวหายยา) เป็นแนวเก่าอีกชั้นหนึ่ง "
                      "— อิฐเก่าไม่ได้แปลว่าคูเมืองเสมอไป",
                      "The curved earthen rampart southeast of the square "
                      "(round Haiya) is an older, separate line — old brick "
                      "does not always mean THE moat."))

        # ---- ๕ the rings ----------------------------------------------------
        + way("๕", "รถวนสองวง สวนทางกัน", "Two rings of traffic, counter-rotating",
              "ใช้ได้ริมถนนเลียบคู — กลางคืนก็ใช้ได้ ไม่ต้องอ่านป้าย",
              "at any ring road — works at night, no reading required",
              "<p>" + bi(
                  "ถนนเลียบคูเป็นวันเวย์ทั้งแปดสาย และแปดสายนั้นเรียงเป็นระบบเดียว: "
                  "วงในวิ่งทวนเข็มนาฬิกา วงนอกวิ่งตามเข็ม "
                  "พูดอีกแบบ — น้ำอยู่ขวามือของรถเสมอ ไม่ว่าวงไหน "
                  "วิธีใช้ง่ายสุด: เดินตามน้ำไปจนถึงแจ่ง ถ้าแนวน้ำโค้งขวา คุณอยู่ฝั่งนอก "
                  "ถ้าโค้งซ้าย คุณอยู่ฝั่งใน "
                  "หรือถ้าขับรถอยู่: น้ำต้องอยู่ขวามือ — ถ้าน้ำอยู่ซ้าย นั่นไม่ใช่ถนนเลียบคู "
                  "หรือไม่ก็ถึงเวลากลับรถแล้ว",
                  "All eight moat-side roads are one-way, and the eight make "
                  "one system: the inner ring runs counterclockwise, the "
                  "outer ring clockwise. Said another way — the water always "
                  "sits on the traffic's right, both banks. Simplest use: "
                  "follow the water to a chaeng and watch which way it bends. "
                  "Bends right: you are on the outer bank. Bends left: the "
                  "inner. And if you are driving: the water belongs on your "
                  "right hand — water on the left means this is not a ring "
                  "road, or it is time to turn around.")
              + "</p>"
              + fig(rings_svg(),
                    "วัดจากทิศวันเวย์ของทั้งแปดสายในสแนปช็อตถนนของมดเอง (๒๗ ส.ค. ๒๕๖๙) "
                    "— ไม่มีสายไหนแย้ง",
                    "Measured from the one-way bearings of all eight roads in "
                    "the ants' own road snapshot (2026-08-27) — not one "
                    "dissents.")
              + catch("จักรยานกับคนเดินไม่ผูกกับวันเวย์ — ดูรถยนต์เป็นหลัก "
                      "และตีสี่ถนนว่างก็ต้องรอคันแรกผ่านก่อน",
                      "Bicycles and walkers ignore the one-way — judge by the "
                      "cars, and at 4 a.m. you may wait a while for the "
                      "first witness."))

        # ---- ๖ street names -------------------------------------------------
        + way("๖", "อ่านป้ายถนน", "Read the street signs",
              "ใช้ได้ทุกหัวมุม — ระยะห้าเมตร", "at every corner — the five-metre clue",
              "<p>" + bi(
                  "ในเวียงชื่อถนนเป็นชุดราชสำนัก: ราชดำเนิน ราชวิถี ราชภาคินัย ราชมรรคา "
                  "พระปกเกล้า สิงหราช — ถนนสั้น ซอยถี่ "
                  "(ในสี่เหลี่ยมสองตารางกิโลเมตรเศษนี้มีถนนมีชื่อนับได้ ๑๐๓ สาย "
                  "— นับจากสแนปช็อตถนน ๒๗ ส.ค. ๒๕๖๙) "
                  "ส่วนชื่อถนนวงในทั้งสี่ — ศรีภูมิ มูลเมือง บำรุงบุรี อารักษ์ — "
                  "ขึ้นป้ายเมื่อไรก็คือขอบในพอดี",
                  "Inside, the street names run to the royal register: "
                  "Ratchadamnoen (the royal procession way), Ratchawithi, "
                  "Ratchaphakhinai, Ratchamankha, Phra Pokklao, Singharat — "
                  "short streets, dense sois (103 named streets in these two "
                  "and a bit square kilometres, counted from the road "
                  "snapshot, 2026-08-27). And the four inner ring names — "
                  "Si Phum, Moon Mueang, Bamrung Buri, Arak — on a sign mean "
                  "you stand exactly on the inner rim.")
              + "</p>"
              + fig(names_svg(),
                    "ชุดชื่อในเวียง (เขียว) กับชื่อลวงนอกเวียง (แดง)",
                    "The inside cluster (jade) and the outside decoys (red)")
              + catch("ราชวงศ์ ราชเชียงแสน ราชพฤกษ์ ยืนนอกเวียงทั้งสาม — "
                      "คำว่า ราช เดี่ยว ๆ ยังไม่ตัดสิน และราชดำเนินเองก็ยาวพ้นประตูไปนิดหน่อย",
                      "Ratchawong, Ratcha Chiang Saen and Ratchaphruek all "
                      "stand outside — the word Ratcha alone settles "
                      "nothing, and Ratchadamnoen itself runs a little past "
                      "its gate."))

        # ---- ๗ the address --------------------------------------------------
        + way("๗", "อ่านซองจดหมาย", "Read the envelope",
              "ใช้ได้บนกระดาษ — ระยะศูนย์เมตร", "on paper — the zero-metre clue",
              "<p>" + bi(
                  f"ในสารบัญมด ที่อยู่ฝั่งในที่มีรหัสไปรษณีย์ {pc_in} รายการ "
                  f"เขียน 50200 เสีย {pc_pct}% "
                  f"แต่ 50200 ยังโผล่นอกเวียงอีก {pc_out_50200:,} รายการ "
                  "ทางนี้จึงใช้ได้ทางเดียว: รหัสไม่ใช่ 50200 → แทบแน่ว่านอกเวียง "
                  "รหัสเป็น 50200 → ยังสรุปไม่ได้ "
                  "ส่วนชื่อตำบล: ที่อยู่ฝั่งในที่ระบุตำบลไว้ มีแต่ ศรีภูมิ กับ พระสิงห์ "
                  "(นับจากสารบัญเองตอนสร้างหน้านี้)",
                  f"In the ants' own records, of the {pc_in} inside addresses "
                  f"that carry a postcode, {pc_pct}% read 50200 — but 50200 "
                  f"also turns up {pc_out_50200:,} times outside the water. "
                  "So the clue works one direction only: not-50200 → almost "
                  "certainly outside; 50200 → still undecided. As for tambon "
                  "names: every inside address in the catalogue that names "
                  "one says either Si Phum or Phra Sing (counted live from "
                  "the records as this page was built).")
              + "</p>"
              + fig(postcode_svg(),
                    "เครื่องมือตัดออก ไม่ใช่เครื่องมือยืนยัน",
                    "A ruling-out tool, never a ruling-in one")
              + catch("ป้ายร้านชอบเขียนที่อยู่สาขาแรกไว้ — กระดาษบอกที่อยู่ของกระดาษ "
                      "ไม่ใช่ที่อยู่ของเท้าคุณ",
                      "Shop signs love printing the FIRST branch's address — "
                      "paper states where the paper lives, not where your "
                      "feet do."))

        # ---- ๘ topology ------------------------------------------------------
        + way("๘", "วิชาโทโพโลยีข้างถนน", "Roadside topology",
              "ใช้ได้ย้อนหลัง — แค่ความจำกับเลขคู่คี่",
              "works retroactively — memory and parity are enough",
              "<p>" + bi(
                  "คูเมืองเป็น เส้นปิด — วนกลับมาชนตัวเอง คณิตศาสตร์จึงแถมเครื่องมือให้สองชิ้น "
                  "ชิ้นแรก: นับครั้งที่ข้ามน้ำวันนี้ ข้ามเลขคี่ครั้ง = ตอนนี้อยู่คนละข้างกับตอนเช้า "
                  "เลขคู่ = ข้างเดิม (นับเฉพาะคูเมือง — สะพานข้ามปิงไม่นับ "
                  "เพราะแม่น้ำไม่ใช่เส้นปิด) "
                  "ชิ้นที่สอง: ถ้าไม่แน่ใจว่าน้ำตรงหน้าคือคูหรือแม่น้ำ ให้เดินเลียบน้ำไปเรื่อย ๆ "
                  f"— คูพากลับถึงที่เดิมใน {perimeter / 1000:.0f} กิโลเมตร ราว "
                  f"{walk_min:.0f} นาทีเดินเล่น แม่น้ำไม่พากลับบ้าน",
                  "The moat is a CLOSED curve — it meets itself. Mathematics "
                  "hands over two tools for free. First: count today's water "
                  "crossings. An odd count means you now stand on the other "
                  "side from where you woke; even, the same side. (Count "
                  "only the moat — Ping bridges do not count, because a "
                  "river is not a closed curve.) Second: unsure whether the "
                  "water in front of you is moat or river? Walk along it. "
                  f"The moat returns you to your own footprints in "
                  f"{perimeter / 1000:.0f} km, about {walk_min:.0f} strolling "
                  "minutes. A river never brings you home.")
              + "</p>"
              + fig(parity_svg(),
                    "กติกาเลขคู่คี่ของเส้นปิด — ทฤษฎีบทเส้นโค้งของฌอร์ด็อง ฉบับใช้จริงข้างถนน",
                    "The parity rule of a closed curve — the Jordan curve "
                    "theorem, roadside edition")
              + '<div class="mo-tally"><button type="button" id="mo-cross">'
              + bi("ข้ามน้ำ +๑", "crossed the water +1") + "</button>"
              + '<button type="button" id="mo-reset">' + bi("เริ่มนับใหม่", "reset")
              + '</button><p class="par" id="mo-par" aria-live="polite"></p></div>'
              + fig(loop_svg(),
                    "เส้นปิดพากลับบ้าน เส้นเปิดพาไปเรื่อย ๆ",
                    "Closed curves take you home; open ones just take you")
              + "<p class='mo-note'>" + bi(
                  "คำตอบที่สามมีจริง: บนสะพาน บนตลิ่ง กลางถนนเลียบคู — "
                  "เขตแดนไม่ใช่เส้นบาง ๆ แต่หนาพอให้ยืนได้ทั้งตัว ยืนตรงนั้นคือไม่ใช่ทั้งในทั้งนอก "
                  "ถือเป็นสิทธิพิเศษเล็ก ๆ ของคนข้ามสะพาน",
                  "There is a third answer: on a bridge, on the bank, on a "
                  "ring road — the boundary is not a thin line but thick "
                  "enough to stand in. Standing there you are neither in nor "
                  "out, which is the bridge-crosser's small privilege.")
              + "</p>"
              + catch("ลืมนับครั้งเดียว คำตอบกลับด้านทันที — จับคู่กับทางอื่นสักทางไว้เป็นเลขตรวจ",
                      "Forget one crossing and the answer flips — pair it "
                      "with any other way as your check digit."))

        # ---- ๙ ask ----------------------------------------------------------
        + way("๙", "ถามคน แล้วก็ถามเครื่อง", "Ask a person, then the machine",
              "ระยะศูนย์เมตร — คำตอบเด็ดขาด", "zero metres — the decisive clue",
              "<p>" + bi(
                  "ทางที่เก่าแก่ที่สุดยังไวที่สุด: ถามใครก็ได้ว่า ในเวียงก่อ "
                  "จะได้คำตอบคำเดียวพร้อมมือชี้ "
                  "ส่วนทางที่ใหม่ที่สุดอยู่ข้างล่างนี้ — เครื่องของคุณรู้พิกัด "
                  "หน้านี้รู้รูปสี่เหลี่ยม เทียบกันจบในเครื่อง ไม่มีอะไรถูกส่งออกไปไหน",
                  "The oldest way is still the fastest: ask anyone — nai "
                  "wiang ko? — and get one word and a pointing hand. The "
                  "newest way sits just below: your device knows its point, "
                  "this page knows the square, and the comparison happens "
                  "entirely on your machine. Nothing leaves it.")
              + "</p>"
              + '<div class="mo-check"><button type="button" class="mo-btn" id="mo-btn">'
              + bi("ตอนนี้ฉันอยู่ในเวียงไหม?", "Am I inside the walls right now?")
              + "</button>"
              + '<p class="mo-verdict" id="mo-verdict"></p>'
              + '<p class="mo-detail" id="mo-detail"></p>'
              + '<p class="mo-quiet">' + bi(
                  "คิดในหน้านี้จบ — พิกัดไม่ออกจากเครื่องของคุณ และมดไม่เก็บอะไรทั้งนั้น",
                  "Computed on this page — your position never leaves your "
                  "device, and the ants keep nothing.")
              + "</p><noscript><p>" + bi(
                  "ไม่มีสคริปต์ก็รู้ได้ — เก้าทางข้างบนทำงานด้วยตาเปล่าทั้งหมด "
                  "พิกัดสี่แจ่งพิมพ์ไว้ในกล่องถัดไปสำหรับเทียบมือ",
                  "No script, no problem — the nine ways above run on the "
                  "naked eye, and the four corner coordinates are printed in "
                  "the next box for checking by hand.")
              + "</p></noscript></div>"
              + '<details class="mo-code"><summary>' + bi(
                  "กลเม็ดทั้งหมดยาวแปดบรรทัด — เอาไปใช้ได้เลย",
                  "The whole trick is eight lines — take it")
              + "</summary><pre>"
              + esc("// จุดอยู่ในรูปสี่เหลี่ยมไหม — point in polygon (ray casting)\n"
                    "// สี่แจ่ง (lat, lng) จากสารบัญมดแดง:\n"
                    + "".join("//   %s  %.6f, %.6f\n"
                              % (c[2], c[0], c[1]) for c in corners)
                    + "function inWiang(la, ln, P) {\n"
                    "  let c = false;\n"
                    "  for (let i = 0, j = P.length - 1; i < P.length; j = i++)\n"
                    "    if (((P[i][1] > ln) !== (P[j][1] > ln)) &&\n"
                    "        (la < (P[j][0]-P[i][0]) * (ln-P[i][1]) /\n"
                    "              (P[j][1]-P[i][1]) + P[i][0]))\n"
                    "      c = !c;\n"
                    "  return c;\n"
                    "}")
              + "</pre></details>")

        # ---- census ---------------------------------------------------------
        + "<h2>" + bi("ตอนนี้ในเวียงมีอะไรยืนอยู่บ้าง",
                      "What stands inside right now") + "</h2>"
        + '<div class="mo-census">'
        + '<span class="tile"><span class="n">' + f"{n_in:,}" + "</span>"
        + bi("ที่ในสารบัญ อยู่ในสี่เหลี่ยมนี้", "places in the catalogue stand in the square")
        + "</span>"
        + '<span class="tile"><span class="n">' + str(n_wat) + "</span>"
        + bi(f"วัด — เฉลี่ยหนึ่งวัดทุก ~{wat_gap:.0f} ม.",
             f"wats — one every ~{wat_gap:.0f} m of walking") + "</span>"
        + '<span class="tile"><span class="n">' + str(n_food) + "</span>"
        + bi("ร้านอาหาร", "places to eat") + "</span>"
        + '<span class="tile"><span class="n">' + str(n_hotel) + "</span>"
        + bi("ที่พัก", "places to sleep") + "</span></div>"
        + '<p class="mo-note">' + bi(
            "นับสดจากสารบัญตอนสร้างหน้า — ดูรายชื่อทั้งหมดได้ที่ป้าย "
            "🏯 ในเวียง-ในคูเมือง",
            "Counted live from the records as this page was built — the full "
            "roll lives under the 🏯 inside-the-moat tag.")
        + ' <a href="cm/tag/old-city.html">' + bi("เปิดป้ายในเวียง →", "open the tag →")
        + "</a></p>"

        # ---- glossary -------------------------------------------------------
        + "<h2>" + bi("คำที่ได้ยินรอบคู", "The words heard around the water") + "</h2>"
        + '<p class="mo-note">' + bi(
            "อักษรไทย · คำอ่านแบบ RTGS · รากและความหมาย — ชื่อรอบคูเกือบทุกชื่อเป็นแผนที่ย่อ ๆ ในตัวเอง",
            "Thai script · RTGS spelling · roots and meaning — nearly every "
            "name around the moat is a small map of its own.")
        + "</p>" + gloss_html

        + '<p class="mo-note">' + bi(
            "เรื่องแผ่นดินเอียงต่อได้ที่หน้าดอย เรื่องเส้นทางรถต่อที่หน้ารถ-เดินทาง "
            "เห็นอะไรคลาดเคลื่อนหรือมีทางรู้ทางที่สิบ บอกมดได้ที่หน้าเสนอแนะ",
            "The tilt of the land continues on the doi page; buses and rides "
            "on the transport page. If something here has drifted — or you "
            "keep a tenth way in your pocket — tell the ants via the "
            "suggestion page.")
        + ' <a href="doi.html">' + bi("หน้าดอย →", "the doi page →") + "</a>"
        + ' <a href="transport.html">' + bi("หน้ารถ-เดินทาง →", "getting around →") + "</a>"
        + "</p>"

        + share_block(BASE + "moat.html", "ในเวียงหรือนอกเวียง · มดแดง", card=og)

        + '<script type="application/json" id="mo-data">'
        + json.dumps(payload, ensure_ascii=False) + "</script>"
        + "<script>" + checker_js + "</script>")

    (DOCS / "moat.html").write_text(page(
        "ในเวียงหรือนอกเวียง · Inside or outside the moat",
        body, depth=0, path="moat.html",
        desc=bi_text(
            "เก้าทางรู้ว่ากำลังยืนอยู่ในเวียงหรือนอกเวียงเชียงใหม่ — ดูดอย ดูเส้นขอบฟ้า "
            "ดูน้ำ ดูทิศรถวิ่งรอบคู อ่านป้ายถนน อ่านรหัสไปรษณีย์ นับสะพานแบบนักคณิตศาสตร์ "
            "หรือให้เครื่องเทียบพิกัดกับสี่แจ่งในเครื่องเอง",
            "Nine ways to tell whether you stand inside or outside Chiang "
            "Mai's old-city moat: the mountain, the skyline, the water, the "
            "counter-rotating one-way rings, street names, postcodes, a "
            "mathematician's bridge-count, and a point-in-square check that "
            "runs entirely on your own device."),
        extra_head=head, og=og,
        crumbs='<a href="index.html">' + bi("หน้าแรก", "Home") + "</a> › "
               + bi("ในเวียงหรือนอกเวียง", "The moat")))

    return (f"9 ways · {len(crossings)} crossings named · census {n_in:,} in "
            f"({n_wat} wat, {n_food} food, {n_hotel} hotel) · "
            f"postcode {pc_in_50200}/{pc_in} = {pc_pct}% 50200 · "
            f"ring {perimeter:,.0f} m, {area:.2f} km², tilt {tilt - 90:+.1f}°")
