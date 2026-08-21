#!/usr/bin/env python3
"""ตามหาหมุด — the pin hunt: curated places still waiting for coordinates.

A curated record can be true and complete in every field and still carry
geoPrecision "needs-pin": the place is real, the address is stated, but nobody
has stood in front of it with a map yet. Those records deserve better than a
quiet badge on a shelf row — collected on one page they become an errand list,
the kind a person on a bicycle clears three at a time.

Grouped by shelf since WO-16: the temple-register fold took this page from
~265 rows to ~1,500, and one flat list at that size is a wall, not an errand
list. Each province+shelf is a <details> fold with its count — the same
disclosure the brand shelves use, no script — with the temples (the biggest
group by far) sorted after the small, clear-three-on-one-ride groups.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
answers layer. Emits pins.html; prints the count.
"""


def emit(g, data):
    page, bi, esc = g["page"], g["bi"], g["esc"]
    place_slug = g["place_slug"]
    DOCS, BASE = g["DOCS"], g["BASE"]
    share_block = g["share_block"]
    CATS = g["CATS"]

    groups = {}
    n = 0
    for prov in ("cm", "cr"):
        for r in data[prov]:
            if r.get("geoPrecision") != "needs-pin":
                continue
            n += 1
            cat = next((c for c in (r.get("cat") or []) if c in CATS),
                       (r.get("cat") or ["?"])[0])
            groups.setdefault((prov, cat), []).append(r)

    def li(prov, r):
        href = f'{prov}/p/{place_slug(r)}.html'
        addr = esc(r.get("address") or "")
        return (f'<li><a href="{href}"><b>{esc(r.get("name") or "")}</b></a>'
                + (f'<br><span class="shelf">📮 {addr}</span>' if addr else "")
                + "</li>")

    # Small groups first: a hunt page should open on the errands a person can
    # actually finish. The temple register is the long tail and knows it.
    ordered = sorted(groups.items(), key=lambda kv: (len(kv[1]), kv[0]))
    blocks = []
    for (prov, cat), rs in ordered:
        prov_th, prov_en = ("เชียงใหม่", "Chiang Mai") if prov == "cm" else ("เชียงราย", "Chiang Rai")
        cdef = CATS.get(cat, {"th": cat, "en": cat})
        rs.sort(key=lambda r: r.get("name") or "")
        opened = " open" if len(rs) <= 15 else ""
        blocks.append(
            f'<li class="brandshelf"><details{opened}><summary>'
            + bi(f"{cdef['th']} · {prov_th}", f"{cdef['en']} · {prov_en}")
            + f' <span class="count">({len(rs):,})</span></summary>'
            f'<ul class="dir sub">{"".join(li(prov, r) for r in rs)}</ul></details></li>')

    hint_th = (f"อีก {n:,} แห่งในสารบัญที่รู้จักจริง มีที่อยู่จริง แต่ยังไม่มีพิกัดบนแผนที่ — "
               "ใครผ่านไปแถวนั้น ช่วยปักหมุดได้เลยเจ้า กดชื่อร้านแล้วบอกมดตรงหน้านั้นได้ทันที "
               "กลุ่มเล็กอยู่บนสุด — เก็บหมดได้ในเที่ยวเดียว")
    hint_en = (f"{n:,} places in the directory are real and addressed but not yet pinned "
               "on the map. If your errands pass one, open its page and tell the ants "
               "where it stands. Small groups sit on top — clearable in one ride.")
    body = (
        f'<h1>📍 {bi("ตามหาหมุด", "The pin hunt")}</h1>'
        f'<p class="myhint">{bi(hint_th, hint_en)}</p>'
        f'<ul class="dir">{"".join(blocks)}</ul>'
        f'<p class="tinynote">{bi("หมุดหนึ่งอัน = ที่หนึ่งแห่งที่คนหาเจอ ขอบคุณเจ้า", "One pin is one more place someone can find. Thank you.")}</p>'
        + share_block(BASE + "pins.html", "ตามหาหมุด · มดแดง"))

    (DOCS / "pins.html").write_text(page(
        "ตามหาหมุด", body, depth=0, path="pins.html",
        desc=f"ตามหาหมุด — {n} แห่งที่มีที่อยู่แต่ยังรอพิกัด ช่วยมดปักหมุดได้เลย",
        crumbs=f'<a href="index.html">มดแดง</a> › {bi("ตามหาหมุด", "Pin hunt")}'))
    return f"{n} places awaiting pins in {len(groups)} groups"


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
