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

  make_html   a button on every place page, "ทำเว็บของคุณเอง · Make your own page",
              that opens the page maker with the record's name, pin, hours and
              phone in the address, so the maker starts from what is known

The first two read the record alone (attrs.ownPage, attrs.ownMenu), so a record the
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


# ---------------------------------------------------------------- the maker

# The maker's six kinds (motdang-pages public/s/make.js KINDS), by shelf.
_KIND_OF = {"food": "food", "shopping": "shop", "market": "shop", "essentials": "shop",
            "cannabis": "shop", "pets": "shop", "hotel": "shop", "realestate": "shop",
            "whats-on": "event"}
_GROUP = {"wat", "community", "school", "school-intl", "parks", "sights", "museums-galleries"}


def maker_kind(cats) -> str:
    for c in cats or []:
        if c in _KIND_OF:
            return _KIND_OF[c]
    for c in cats or []:
        if c in _GROUP:
            return "group"
    return "service"


_LAMPS = []


def _lamps():
    """importers/build_open_lamps.py, loaded once; None if it will not load."""
    if not _LAMPS:
        try:
            import importlib.util
            from pathlib import Path
            spec = importlib.util.spec_from_file_location(
                "_bol", Path(__file__).resolve().parent / "importers" / "build_open_lamps.py")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            _LAMPS.append(m)
        except Exception:
            _LAMPS.append(None)
    return _LAMPS[0]


def week_hash(raw: str) -> str:
    """OSM opening_hours text -> the maker's hrs= value: Monday..Sunday joined
    by '.', a day '0900-1800' (ranges joined by ','), 'x' closed, 'a' always.
    '' when the text is not one the lamp parser reads."""
    if not raw or not isinstance(raw, str):
        return ""
    m = _lamps()
    if m is None:
        return ""
    try:
        iv = m.parse_hours(raw)
    except Exception:
        return ""
    if not iv:
        return ""
    if iv == [[0, 7 * 1440]]:
        return "a"
    days = [[] for _ in range(7)]
    for a, b in iv:
        while a < b:
            d, edge = divmod(a, 1440)[0], (a // 1440 + 1) * 1440
            days[d % 7].append([a - d * 1440, min(b, edge) - d * 1440])
            a = min(b, edge)
    for d in range(7):                      # an overnight span reads as one range
        nxt = (d + 1) % 7
        if days[d] and days[nxt] and days[d][-1][1] == 1440 and days[nxt][0][0] == 0 \
                and days[nxt][0][1] < days[d][-1][0]:
            days[d][-1][1] = days[nxt][0][1]
            days[nxt].pop(0)

    def hhmm(x):
        x = min(x, 1439)
        return "%02d%02d" % (x // 60, x % 60)
    return ".".join(",".join(f"{hhmm(a)}-{hhmm(b)}" for a, b in rs[:2]) if rs else "x" for rs in days)


def make_html(r: dict, bi, att, name: str, phone: str = "", hours: str = "",
              address: str = "", cc: str = "TH") -> str:
    """The button. The hash carries what the record states; the maker reads it
    in the reader's browser."""
    import urllib.parse
    if not name:
        return ""
    q = [("title", name[:60]), ("kind", maker_kind(r.get("cat")))]
    if r.get("lat") is not None and r.get("lng") is not None:
        q.append(("pin", f"{r['lat']:.6f},{r['lng']:.6f}"))
    if address:
        q.append(("ad", address[:200]))
    if cc:
        q.append(("cc", cc))
    p = (phone or "").split("/")[0].split(",")[0].strip()
    if p:
        q.append(("tel", p[:30]))
    h = week_hash(hours)
    if h:
        q.append(("hrs", h))
    href = PAGES_HOST + "make#" + urllib.parse.urlencode(q, quote_via=urllib.parse.quote, safe=",.-")
    return (f'<p class="makeown"><a class="pill" href="{att(href)}" rel="noopener">'
            f'{bi("ทำเว็บของคุณเอง", "Make your own page")}</a></p>')
