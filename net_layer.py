#!/usr/bin/env python3
"""Nets — places strung together by a story, each page showing all the others.

Indra's net: a jewel at every knot, and each jewel shows every other one. Here
a knot is a place record, and a net is a set of them that one history ties
together — the Yunnanese (Haw) kitchens, market and mosque by the Night Bazaar,
and the mountain villages the same people built. Every member's page carries
the whole net, itself included and marked, so a reader who lands on any one of
them can walk to all the rest.

data/curated/nets.json, hand-filled:

    nets.<key>          th, en, roman, lede_th, lede_en, sources[]
      .strands[]        key, th, en, roman, jewels[]
        .jewels[]       id, th, en        (why this place is in the net)

A jewel whose id is not in the built data is skipped and counted, so a record
that leaves the catalogue cannot write a dead link.

Entry points: bind(data, place_href); block(r, helpers) → html; counts().
"""
import json
import pathlib

import commons_layer
import sites_layer

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "curated" / "nets.json"
EXPLAINER = "https://nanobotco.github.io/indras-net/"
LINKHEALTH = ROOT / "data" / "linkhealth.json"
# The publish gate's own set (tests/test_publish_gate.py ALIVE): anything else the
# checker recorded is dead, and a dead source is named, not linked.
ALIVE = {"ok", "social", "redirect-offsite", "walled"}
_HEALTH = None


def _health(url):
    global _HEALTH
    if _HEALTH is None:
        try:
            _HEALTH = json.loads(LINKHEALTH.read_text(encoding="utf-8")).get("links", {})
        except (OSError, ValueError):
            _HEALTH = {}
    return _HEALTH.get(url) or {}

CSS = """
/* ---- nets: every page in a net shows every other page in it ----------- */
.net{margin:1rem 0;padding:.8rem .9rem;background:#fffaf0;
border:2px solid #c0392b;border-radius:.8rem;box-shadow:3px 3px 0 #f1c40f}
.net h2{margin:0 0 .2rem;font-size:1.05rem}
.net .netname{margin:0 0 .4rem;font-weight:600}
.net .lede{margin:.2rem 0 .6rem;line-height:1.55}
.net details{margin:.35rem 0;border-top:1px dashed var(--soft);padding-top:.35rem}
.net summary{cursor:pointer;font-weight:600;padding:.2rem 0}
.net ul{list-style:none;padding-left:0;margin:.3rem 0}
.net li{padding:.3rem 0;line-height:1.5}
.net li .why{display:block;font-size:.9rem;color:var(--muted)}
.net li.here{background:#fdebd0;border-radius:.5rem;padding:.3rem .45rem}
.net .roman{font-style:italic;color:var(--muted);font-size:.85rem}
.net .netsrc{font-size:.8rem;color:var(--muted);margin:.5rem 0 0}
"""

_NETS = None
_RECS = {}
_HREF = {}
_SKIPPED = []
_SHOWN = set()


def load():
    global _NETS
    if _NETS is None:
        _NETS = (json.loads(DATA.read_text(encoding="utf-8")).get("nets", {})
                 if DATA.exists() else {})
        # a net staged for Nan's word carries "hold": true and stays off every page
        _NETS = {k: n for k, n in _NETS.items() if not n.get("hold")}
    return _NETS


def add(generated):
    """Nets built during the build rather than written by hand — the event nets
    (event_nets_layer.py). A hand-written net of the same key wins."""
    nets = load()
    for k, n in (generated or {}).items():
        nets.setdefault(k, n)
    return len(generated or {})


def bind(data, place_href):
    """Called once per build, after PLACE_HREF, with the loaded provinces."""
    global _RECS, _HREF
    _RECS = {r["id"]: r for recs in data.values() for r in recs}
    _HREF = place_href
    _SKIPPED.clear()
    for key, net in load().items():
        for s in net.get("strands", []):
            for j in s.get("jewels", []):
                if j["id"] not in _HREF:
                    _SKIPPED.append((key, j["id"]))


def first_href(key):
    """The page of the net's first member the build wrote, or None (before bind)."""
    for s in load().get(key, {}).get("strands", []):
        for j in s.get("jewels", []):
            if j["id"] in _HREF:
                return _HREF[j["id"]]
    return None


def nets_of(pid):
    return [(k, n) for k, n in load().items()
            if any(j["id"] == pid for s in n.get("strands", []) for j in s.get("jewels", []))]


def _where(rec, h):
    a = rec.get("attrs") or {}
    amphoe = a.get("amphoe") or ""
    if not amphoe:
        return ""
    cr = rec["id"].startswith("cr-")
    return h["bi"]("อ.%s จ.%s" % (amphoe, "เชียงราย" if cr else "เชียงใหม่"),
                   "%s, %s" % (h["reading"](amphoe), "Chiang Rai" if cr else "Chiang Mai"))


def block(r, h):
    """h: dict of build helpers — bi, esc, att, name_bi, reading."""
    nets = nets_of(r["id"])
    if not nets:
        return ""
    bi, esc, att = h["bi"], h["esc"], h["att"]
    here_amphoe = ((_RECS.get(r["id"]) or r).get("attrs") or {}).get("amphoe")
    out = []
    for key, net in nets:
        _SHOWN.add(r["id"])
        parts = ['<section class="net" id="net-%s">' % att(key),
                 "<h2>%s</h2>" % bi("ร้อยไว้ในตาข่ายเดียวกัน", "Strung in the same net"),
                 '<p class="netname">%s%s</p>' % (
                     bi(net["th"], net["en"]),
                     (' <span class="roman">%s</span>' % esc(net["roman"])) if net.get("roman") else "")]
        # The minisite this net belongs to, when the register names one.
        parts.append(sites_layer.net_line(key, "../../"))
        if net.get("lede_th") or net.get("lede_en"):
            parts.append('<p class="lede">%s</p>' % bi(net.get("lede_th", ""), net.get("lede_en", "")))
        # The net as pictures: its jewels first, then its subject (commons_layer).
        try:
            parts.append(commons_layer.net_pics(key, net, r["id"], h))
        except Exception as e:                       # pictures are never worth a failed page
            print("  ! net pictures", key, e)
        for s in net.get("strands", []):
            jewels = [j for j in s.get("jewels", []) if j["id"] in _HREF]
            if not jewels:
                continue
            mine = any(j["id"] == r["id"] for j in jewels)
            rows = []
            for j in jewels:
                rec = _RECS.get(j["id"])
                if rec is None:
                    continue
                why = bi(j.get("th", ""), j.get("en", ""))
                # The district only where it differs from this page's own.
                where = ("" if (rec.get("attrs") or {}).get("amphoe") == here_amphoe
                         else _where(rec, h))
                if j["id"] == r["id"]:
                    rows.append('<li class="here"><b>%s</b> — %s<span class="why">%s</span></li>'
                                % (h["name_bi"](rec), bi("ที่นี่", "you are here"), why))
                else:
                    rows.append('<li>%s<a href="../../%s.html">%s</a>%s<span class="why">%s</span></li>'
                                % (commons_layer.jewel_thumb(j["id"], "../../", h),
                                   att(_HREF[j["id"]]), h["name_bi"](rec),
                                   (" · " + where) if where else "", why))
            parts.append('<details%s><summary>%s%s (%d)</summary><ul>%s</ul></details>' % (
                " open" if mine else "", bi(s["th"], s["en"]),
                (' <span class="roman">%s</span>' % esc(s["roman"])) if s.get("roman") else "",
                len(rows), "".join(rows)))
        src = net.get("sources") or []
        if src:
            def _src(x):
                h = _health(x["url"])
                if not h or h.get("status") in ALIVE:
                    return '<a href="%s" rel="noopener">%s</a>' % (att(x["url"]), esc(x["label"]))
                wb = (h.get("wayback") or {}).get("url")
                return esc(x["label"]) + (' (<a href="%s" rel="noopener">%s</a>)' % (
                    att(wb), bi("สำเนาเก่า", "archived copy")) if wb else "")
            links = " · ".join(_src(x) for x in src)
            parts.append('<p class="netsrc">%s %s</p>' % (bi("ที่มา:", "Sources:"), links))
        parts.append('<p class="netsrc"><a href="%s" rel="noopener">%s</a> · <a href="../../sites/#motdang-net">%s</a></p>' % (
            att(EXPLAINER), bi("ทำไมเป็นตาข่าย — Indra's Net, Drawn (ภาษาอังกฤษ)",
                               "Why a net — Indra's Net, Drawn"),
            bi("ตาข่ายมดแดง: เว็บทั้งหมด", "The Mot Dang net: all the sites")))
        parts.append("</section>")
        out.append("".join(parts))
    return "".join(out)


def counts():
    """(members rendered, jewels skipped for a missing record)."""
    return len(_SHOWN), list(_SKIPPED)
