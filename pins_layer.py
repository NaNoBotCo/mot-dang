#!/usr/bin/env python3
"""ตามหาหมุด — the pin hunt: curated places still waiting for coordinates.

A curated record can be true and complete in every field and still carry
geoPrecision "needs-pin": the place is real, the address is stated, but nobody
has stood in front of it with a map yet. Those records deserve better than a
quiet badge on a shelf row — collected on one page they become an errand list,
the kind a person on a bicycle clears three at a time.

The page lists every needs-pin record in both provinces with its address and a
link to its place page (whose "tell the ants" paths already exist). One ride,
one pin, one more place findable — ช่วยกันคนละหมุด.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
answers layer. Emits pins.html; prints the count.
"""


def emit(g, data):
    page, bi, esc = g["page"], g["bi"], g["esc"]
    place_slug = g["place_slug"]
    DOCS, BASE = g["DOCS"], g["BASE"]
    share_block = g["share_block"]

    rows = []
    n = 0
    for prov in ("cm", "cr"):
        for r in data[prov]:
            if r.get("geoPrecision") != "needs-pin":
                continue
            n += 1
            href = f'{prov}/p/{place_slug(r)}.html'
            addr = esc(r.get("address") or "")
            prov_th = "เชียงใหม่" if prov == "cm" else "เชียงราย"
            rows.append(
                f'<li><a href="{href}"><b>{esc(r.get("name") or "")}</b></a> '
                f'<span class="count">· {prov_th}</span>'
                + (f'<br><span class="shelf">📮 {addr}</span>' if addr else "")
                + "</li>")

    hint_th = (f"อีก {n} แห่งในสารบัญที่รู้จักจริง มีที่อยู่จริง แต่ยังไม่มีพิกัดบนแผนที่ — "
               "ใครผ่านไปแถวนั้น ช่วยปักหมุดได้เลยเจ้า กดชื่อร้านแล้วบอกมดตรงหน้านั้นได้ทันที")
    hint_en = (f"{n} places in the directory are real and addressed but not yet pinned "
               "on the map. If your errands pass one, open its page and tell the ants "
               "where it stands.")
    body = (
        f'<h1>📍 {bi("ตามหาหมุด", "The pin hunt")}</h1>'
        f'<p class="myhint">{bi(hint_th, hint_en)}</p>'
        f'<ul class="dir">{"".join(rows)}</ul>'
        f'<p class="tinynote">{bi("หมุดหนึ่งอัน = ที่หนึ่งแห่งที่คนหาเจอ ขอบคุณเจ้า", "One pin is one more place someone can find. Thank you.")}</p>'
        + share_block(BASE + "pins.html", "ตามหาหมุด · มดแดง"))

    (DOCS / "pins.html").write_text(page(
        "ตามหาหมุด", body, depth=0, path="pins.html",
        desc=f"ตามหาหมุด — {n} แห่งที่มีที่อยู่แต่ยังรอพิกัด ช่วยมดปักหมุดได้เลย",
        crumbs=f'<a href="index.html">มดแดง</a> › {bi("ตามหาหมุด", "Pin hunt")}'))
    return f"{n} places awaiting pins"


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
