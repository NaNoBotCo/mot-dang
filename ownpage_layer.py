#!/usr/bin/env python3
"""ownpage_layer.py - a place's own page, on the place's page.

Nan, 2026-10-13: "information posted on minisites should be used everywhere it
can be to make all of motdang better."

importers/own_pages.py ties a page made with the page maker (sites.motdang.net)
to the place record it describes, and importers/import_all.py writes what the
page states into the record's gaps. This layer draws the two things a reader
sees of that on the place page:

  pill_html   a button beside the reach buttons, "เว็บของร้าน · Their own page",
              that goes to the page
  menu_row    the menu items and prices the page lists, with the day they were
              read, as one row of the details list

Both read the record alone (attrs.ownPage, attrs.ownMenu), so a record the
importer never touched draws nothing and no page pays for this.

The tier a page was made on (free or gold) is not drawn. Ordering gold pages
ahead on a list is a decision about paid placement and is Nan's; build.py's
ground_truth() feeds the search index's level as well, so it is not a one-line
tie-break and is left alone.
"""
from __future__ import annotations

PAGES_HOST = "https://sites.motdang.net/"
MENU_SHOWN = 12


def own(r: dict):
    """The record's own page as {url, seen}, or None. The address must be on the
    pages host: the field is data and a link that points elsewhere is not drawn."""
    op = (r.get("attrs") or {}).get("ownPage")
    if isinstance(op, dict) and isinstance(op.get("url"), str) and op["url"].startswith(PAGES_HOST):
        return op
    return None


def pill_html(r: dict, bi, att, esc, icon) -> str:
    """The button, as reach_block's other pills are drawn; '' when no page."""
    op = own(r)
    if not op:
        return ""
    shown = op["url"].split("//", 1)[1].rstrip("/")
    return (f'<span class="chwrap"><a class="pill web ownpage" href="{att(op["url"])}" rel="noopener">'
            f'<span class="chico">{icon("i-shop", 16)}</span> <span class="chlabel">'
            f'{bi("เว็บของร้าน", "Their own page")}</span> <b>{esc(shown)}</b></a></span>')


def _price(p: str, currency: str) -> str:
    p = (p or "").strip()
    if not p:
        return ""
    if not any(c.isdigit() for c in p):
        return p
    return ("฿" + p) if currency == "THB" else f"{currency} {p}"


def menu_row(r: dict, bi, esc, att, mark) -> str:
    """'<dt>…</dt><dd>…</dd>' for the items the page lists, or ''."""
    m = (r.get("attrs") or {}).get("ownMenu")
    op = own(r)
    if not (isinstance(m, dict) and m.get("items") and op):
        return ""
    cur = str(m.get("currency") or "THB")
    lines = []
    for it in m["items"][:MENU_SHOWN]:
        if not isinstance(it, dict) or not it.get("n"):
            continue
        price = _price(str(it.get("p") or ""), cur)
        note = f' <span class="tinynote">{esc(it["note"])}</span>' if it.get("note") else ""
        lines.append(esc(it["n"]) + (f" - {esc(price)}" if price else "") + note)
    if not lines:
        return ""
    more = len(m["items"]) - MENU_SHOWN
    tail = (f' <a href="{att(op["url"])}" rel="noopener">'
            + bi(f"อีก {more} รายการ", f"{more} more") + "</a>") if more > 0 else ""
    seen = str(m.get("seen") or op.get("seen") or "")[:10]
    src = mark('<span class="tinynote">' + bi("ที่มา", "source") + "</span>",
               f"จากหน้าของร้านเอง อ่านเมื่อ {seen}" if seen else "จากหน้าของร้านเอง",
               f"from their own page, read {seen}" if seen else "from their own page")
    return (f"<dt>{bi('เมนูจากหน้าของร้าน', 'Menu from their page')}</dt><dd>"
            + "<br>".join(lines) + tail + " " + src + "</dd>")
