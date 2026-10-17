#!/usr/bin/env python3
"""inat_layer.py — iNaturalist sightings near a place (Nan, 2026-10-02).

importers/harvest_inat.py picks, per place record, up to four species seen
within a kilometre and bakes their photos into assets/inat/. This module
draws them on the place page in the Commons strip's tiles (commons_layer.CSS,
class .cpics), each a link to the sighting on iNaturalist, with the
photographer and licence in the credit line.

    block(r, h)        -> html, or "" when the record has no pick
    copy_assets(docs)  -> photos copied into docs/inat/, or listed for mot-dang-media (media_layer)
    counts()           -> (pages, photos)
"""
import json
from pathlib import Path

import media_layer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "inat.json"
PICS = ROOT / "assets" / "inat"

_D = None


def _data():
    global _D
    if _D is None:
        try:
            _D = json.loads(DATA.read_text())
        except (OSError, ValueError):
            _D = {"obs": {}, "near": {}}
    return _D


def _dist(m, bi):
    if m < 1000:
        m = max(50, int(round(m / 50.0) * 50))
        return bi("%d ม." % m, "%d m" % m)
    return bi("%.1f กม." % (m / 1000.0), "%.1f km" % (m / 1000.0))


def _name(o, h):
    esc = h["esc"]
    sci = "<i>%s</i>" % esc(o.get("sci") or "")
    en = esc(o.get("en") or "")
    th = esc(o.get("th") or "")
    if th and en:
        return h["bi"](th, en)
    return th or en or sci


def block(r, h, base="../../"):
    try:
        return _block(r, h, base)
    except Exception as e:                       # a picture strip never costs a page
        print("  ! nature strip", r.get("id"), e)
        return ""


def _block(r, h, base):
    picks = _data()["near"].get(r.get("id"))
    if not picks:
        return ""
    obs = _data()["obs"]
    bi, att, esc = h["bi"], h["att"], h["esc"]
    tiles, credits, seen = [], [], set()
    for oid, m in picks:
        o = obs.get(oid)
        if not o:
            continue
        alt = att(" · ".join(x for x in (o.get("th"), o.get("en"), o.get("sci")) if x))
        tiles.append(
            '<a class="shot" href="https://www.inaturalist.org/observations/%s" rel="noopener">'
            '<span class="bg"><img src="%sinat/%s.jpg" alt="%s" loading="lazy" decoding="async"></span>'
            '<span class="scrim"></span><span class="sp"></span>'
            '<span class="tx">%s<span class="d">%s</span></span></a>'
            % (att(oid), base, att(oid), alt, _name(o, h), _dist(m, bi)))
        key = (o.get("user"), o.get("licence"))
        if key not in seen:
            seen.add(key)
            credits.append("%s (%s)" % (esc(o.get("user") or "iNaturalist"),
                                        esc((o.get("licence") or "").upper().replace("CC-", "CC "))))
    if len(tiles) < 2:
        return ""
    return ('<section class="cpics" id="nature"><h2>%s</h2><div class="row">%s</div>'
            '<p class="cred">%s %s · %s</p></section>'
            % (bi("ธรรมชาติแถวนี้", "Nature nearby"), "".join(tiles),
               bi("ภาพ:", "Photos:"), " · ".join(credits),
               bi("ผ่าน iNaturalist", "via iNaturalist")))


def copy_assets(docs):
    used = {oid for v in _data()["near"].values() for oid, _ in v}
    if not used:
        return 0
    n = 0
    for oid in used:
        f = PICS / ("%s.jpg" % oid)
        if f.exists():
            media_layer.put(f, docs, "inat/%s" % f.name)   # mot-dang-media when it is on
            n += 1
    return n


def counts():
    d = _data()
    return len(d["near"]), len(d["obs"])
