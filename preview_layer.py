#!/usr/bin/env python3
"""preview_layer.py — a picture and a reading on every shelf row, and the peek.

Nan, 2026-10-04, over her phone's search for "Big bike rental": "Not enough
transliteration on search-responsive sub-page summaries. Not enough preview
anywhere. Not enough magic!"

A shelf, tag or list row (build.py entry_li) gets:

  thumb(r, rel)     a small square before the name: the place's own photograph
                    or a Commons one OF it (commons_layer.place_picture), else
                    its piece of the search's map (tiles/find/g/, the cell
                    fleetsearch/thumbs.py draws) with the pin; data-sc names the
                    scene the place page draws of itself, and findpeek.js paints
                    that drawing over the map once the row is on screen
  reading(r)        a Latin-only name read in Thai, for Thai readers (a
                    Thai-only name already carries its RTGS reading, name_bi)
  SCRIPT            assets/front/findpeek.js — long press, the pointer resting
                    on a name, opens a card with the place's facts, without
                    leaving the list

CSS is appended to style.css by build.py.
"""
import re

import commons_layer
import doodles_layer

THAI = re.compile(r"[฀-๿]")
CELL_Z = 16

CSS = """
/* ---- preview_layer: a picture and a reading on each shelf row ---- */
ul.dir li[data-n]:has(>a.mdth){display:flex;flex-wrap:wrap;align-items:center;gap:.15em .3em}
ul.dir li[data-n]:has(>a.mdth)>a:not(.mdth){flex:1 1 10em;min-width:0}
a.mdth{position:relative;display:inline-block;flex:none;width:44px;height:44px;border-radius:8px;overflow:hidden;
  background:#f2ebdc;border:1px solid #c9b895;box-shadow:2px 2px 0 rgba(90,60,20,.12);margin-right:.35em}
a.mdth img{display:block;width:100%;height:100%;object-fit:cover}
a.mdth i{position:absolute;width:7px;height:7px;margin:-4px 0 0 -4px;border-radius:50%;background:#b3261e;
  border:1.5px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.3)}
a.mdth canvas{position:absolute;inset:0;width:100%;height:100%;opacity:0;transition:opacity .6s}
a.mdth canvas.in{opacity:1}
.rdth{display:block;font-size:.84em;color:#7a4b12;font-style:italic;font-weight:normal}
html.lang-en .rdth{display:none}
@media (prefers-reduced-motion:reduce){a.mdth canvas{transition:none}}
"""

SCRIPT_NAME = "findpeek.js"

# Rides at the end of md.js and of locshare.js (the one script /find carries):
# a page with shelf rows or search rows fetches the peek script from the same
# root that script came from.
LOADER = r"""(function(){var d=document;function go(){if(window.MDPEEK||!d.querySelector('ul.dir li[data-n], .r[data-k], a[href*="/p/"]'))return;
var me=[].filter.call(d.scripts,function(s){return /(^|\/)(md|locshare)\.js(\?|$)/.test(s.getAttribute('src')||'')})[0];
var root=me?me.src.replace(/(md|locshare)\.js(\?.*)?$/,''):'/';var s=d.createElement('script');s.src=root+'front/findpeek.js?v=1012';s.async=true;d.head.appendChild(s)}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',go);else go()})();"""


def script(rel):
    """The peek script tag for a page `rel` deep (its path back to the root)."""
    return f'<script src="{rel}front/{SCRIPT_NAME}?v=1012" defer></script>'


_CELL_OF = None


def _cell_of(lat, lng):
    """The same arithmetic thumbs.py draws by, read from it when it imports."""
    global _CELL_OF
    if _CELL_OF is None:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parent / "fleetsearch"))
            from thumbs import cell_of
            _CELL_OF = cell_of
        except Exception:                       # noqa: BLE001
            _CELL_OF = False
    if not _CELL_OF:
        return None
    hx, hy, fx, fy = _CELL_OF(lat, lng)
    return hx, hy, fx * 100, fy * 100


_SCENE = {}


def thumb(r, href, rel, att):
    """The row's picture, a link to the same page as its name."""
    pp = None
    try:
        pp = commons_layer.place_picture(r["id"])
    except Exception:                           # noqa: BLE001
        pp = None
    if pp and pp.get("src"):
        return (f'<a class="mdth ph" href="{href}" tabindex="-1" aria-hidden="true">'
                f'<img src="{att(rel + pp["src"])}" alt="" loading="lazy" decoding="async" width="44" height="44"></a>')
    sc = _SCENE.get(r["id"])
    if sc is None:
        try:
            sc = doodles_layer.place_scene(r) or ""
        except Exception:                       # noqa: BLE001
            sc = ""
        _SCENE[r["id"]] = sc
    dsc = f' data-sc="{att(sc)}"' if sc else ""
    if r.get("lat") is None or (r.get("geoPrecision") or "exact") == "needs-pin":
        return (f'<a class="mdth" href="{href}" tabindex="-1" aria-hidden="true"{dsc}></a>' if sc else "")
    cell = _cell_of(r["lat"], r["lng"])
    if not cell:
        return (f'<a class="mdth" href="{href}" tabindex="-1" aria-hidden="true"{dsc}></a>' if sc else "")
    hx, hy, x, y = cell
    return (f'<a class="mdth" href="{href}" tabindex="-1" aria-hidden="true"{dsc}>'
            f'<img src="/tiles/find/g/{hx}_{hy}.webp" alt="" loading="lazy" decoding="async" width="44" height="44" '
            f'onerror="this.remove()"><i style="left:{x:.1f}%;top:{y:.1f}%"></i></a>')


_READ = {}


def reading(r, th, en, esc):
    """A Latin-only name read in Thai, shown to Thai readers; '' otherwise."""
    if th or not en or THAI.search(en):
        return ""
    if r["id"] not in _READ:
        try:
            from front_layer import _reading
            rd = _reading(en, "")
        except Exception:                       # noqa: BLE001
            rd = ""
        _READ[r["id"]] = rd if rd and THAI.search(rd) else ""
    rd = _READ[r["id"]]
    return f'<span class="rdth" lang="th">อ่านว่า {esc(rd)}</span>' if rd else ""
