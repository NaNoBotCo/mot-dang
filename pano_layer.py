#!/usr/bin/env python3
"""A 360-degree look around on a place page, from NaN's GoPro Max 2 spheres.

importers/make_panos.py writes the spheres to assets/pano/<slug>.jpg, a flat cut at
the initial view to assets/pano/prev/<slug>.jpg, and one row per sphere to
data/curated/panos.json. This module renders, for a record with a row, a preview
button; a tap loads Pannellum 2.5.6 (MIT, assets/vendor/pannellum/, served from our
own tree) and opens the viewer in the page. A row renders once its "reviewed" field
carries the date someone looked at every crop of it.

Entry points: block(r, att, esc, bi, svg_icon) -> html; copy_assets(docs) -> files copied.
"""
import datetime
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "curated" / "panos.json"
ASSETS = ROOT / "assets" / "pano"
VENDOR = ROOT / "assets" / "vendor" / "pannellum"
VENDOR_FILES = ("pannellum.js", "pannellum.css", "COPYING")

TH_MON = ("ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.")

CSS = """
/* ---- 360-degree look around (pano_layer.py) ------------------------------ */
.pano{margin:.9rem 0 .4rem}
.pano [hidden]{display:none!important}
.pano-open{display:block;position:relative;width:100%;padding:0;margin:0;border:1px solid var(--soft);
border-radius:.8rem;overflow:hidden;background:#111;cursor:pointer;font:inherit;color:inherit}
.pano-open img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.pano-label{position:absolute;left:.6rem;bottom:.6rem;display:inline-flex;align-items:center;gap:.35rem;
background:rgba(0,0,0,.66);color:#fff;border-radius:999px;padding:.4rem .85rem;font-weight:600}
.pano-label .rowicon{color:#fff}
.pano-view{position:relative}
.pano-box{width:100%;height:60vh;min-height:280px;border-radius:.8rem;overflow:hidden;background:#111}
.pano-close{position:absolute;top:.5rem;right:.5rem;z-index:5;display:inline-flex;align-items:center;gap:.3rem;
background:rgba(0,0,0,.66);color:#fff;border:0;border-radius:999px;padding:.4rem .8rem;font:inherit;cursor:pointer}
.pano-close .rowicon{color:#fff}
.pano figcaption{font-size:.85rem;color:var(--muted);margin:.35rem .1rem 0}
"""

# One small script a figure: load Pannellum on the first tap, open, close.
JS = ("(function(){var f=document.currentScript.previousElementSibling,b=f.querySelector('.pano-open'),"
      "v=f.querySelector('.pano-view'),box=f.querySelector('.pano-box'),x=f.querySelector('.pano-close'),"
      "cfg=JSON.parse(b.getAttribute('data-pano')),base=b.getAttribute('data-base'),w=null;"
      "function need(cb){if(window.pannellum)return cb();"
      "if(!document.querySelector('link[data-pnlm]')){var l=document.createElement('link');l.rel='stylesheet';"
      "l.href=base+'pannellum.css';l.setAttribute('data-pnlm','');document.head.appendChild(l)}"
      "var s=document.createElement('script');s.src=base+'pannellum.js';s.onload=cb;"
      "s.onerror=function(){v.hidden=true;b.hidden=false};document.head.appendChild(s)}"
      "b.addEventListener('click',function(){b.hidden=true;v.hidden=false;"
      "need(function(){if(!w)w=pannellum.viewer(box,cfg)});x.focus()});"
      "x.addEventListener('click',function(){if(w){w.destroy();w=null}box.innerHTML='';"
      "v.hidden=true;b.hidden=false;b.focus()})})();")


def load():
    """{placeId: row} for reviewed rows, the first row a place has."""
    if not DATA.exists():
        return {}
    out = {}
    for row in json.loads(DATA.read_text(encoding="utf-8")):
        if row.get("reviewed") and row.get("placeId") and row["placeId"] not in out:
            out[row["placeId"]] = row
    return out


_ROWS = None


def rows():
    global _ROWS
    if _ROWS is None:
        _ROWS = load()
    return _ROWS


def _when(iso):
    try:
        d = datetime.datetime.fromisoformat(iso).date()
    except (TypeError, ValueError):
        return "", ""
    return (f"{d.day} {TH_MON[d.month - 1]} {d.year + 543}", d.strftime("%-d %b %Y"))


def block(r, att, esc, bi, svg_icon, panos=None):
    """The look-around figure for one place, or "" when it has no reviewed sphere."""
    row = (rows() if panos is None else panos).get(r.get("id"))
    if not row:
        return ""
    slug = row["slug"]
    cfg = {"type": "equirectangular", "panorama": f"../../pano/{slug}.jpg", "autoLoad": True,
           "yaw": row.get("yaw", 0), "pitch": row.get("pitch", 0), "hfov": row.get("hfov", 100),
           "compass": row.get("northOffset") is not None, "showZoomCtrl": True, "showFullscreenCtrl": True}
    if row.get("northOffset") is not None:
        cfg["northOffset"] = row["northOffset"]
    th_d, en_d = _when(row.get("taken"))
    name = r.get("name") or ""
    cap = (bi(f"ถ่ายเมื่อ {th_d}", f"taken {en_d}") + " · " if th_d else "") + \
        'NaN Peacock · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
    return (f'<figure class="pano">'
            f'<button type="button" class="pano-open" data-base="../../vendor/pannellum/" '
            f"data-pano='{att(json.dumps(cfg, separators=(',', ':')))}'>"
            f'<img src="../../pano/prev/{att(slug)}.jpg" width="960" height="540" loading="lazy" '
            f'alt="{att("360° · " + name)}">'
            f'<span class="pano-label">{svg_icon("i-compass", 18)} {bi("ภาพ 360°", "Look around")}</span>'
            f'</button>'
            f'<div class="pano-view" hidden><div class="pano-box"></div>'
            f'<button type="button" class="pano-close">{svg_icon("i-x", 16)} {bi("ปิด", "Close")}</button></div>'
            f'<figcaption>{cap}</figcaption></figure>'
            f'<script>{JS}</script>')


def copy_assets(docs):
    """assets/pano/ -> docs/pano/ (reviewed rows only) and the viewer -> docs/vendor/pannellum/."""
    n = 0
    got = rows()
    if not got:
        return 0
    for row in got.values():
        for src, dest in ((ASSETS / f"{row['slug']}.jpg", docs / "pano" / f"{row['slug']}.jpg"),
                          (ASSETS / "prev" / f"{row['slug']}.jpg", docs / "pano" / "prev" / f"{row['slug']}.jpg")):
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest); n += 1
    (docs / "vendor" / "pannellum").mkdir(parents=True, exist_ok=True)
    for f in VENDOR_FILES:
        if (VENDOR / f).exists():
            shutil.copy2(VENDOR / f, docs / "vendor" / "pannellum" / f); n += 1
    return n
