"""affiliate_layer.py — paid links on place pages and shelf pages.

data/curated/affiliate.json is written by ../affiliate-slots/sync.py from that
project's slots.json. A slot names where it goes by `records` (record ids) or
by `shelves` ("cat" or "cat/sub", limited to one province by `prov`). A shelf
slot goes on the shelf page and on the place pages in that shelf, unless `on`
is "shelf". A slot whose url is null renders nothing.
"""
import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent / "data" / "curated" / "affiliate.json"
try:
    _AFF = json.loads(_PATH.read_text(encoding="utf-8"))
except FileNotFoundError:
    _AFF = {"slots": {}, "label_en": "", "label_th": ""}

BY_RECORD = {}
BY_SHELF = {}
for _k, _s in _AFF["slots"].items():
    if _s.get("url"):
        for _rid in _s.get("records", []):
            BY_RECORD.setdefault(_rid, []).append(_s)
        for _sh in _s.get("shelves", []):
            BY_SHELF.setdefault(_sh, []).append(_s)


def _prov_ok(s, prov):
    return not s.get("prov") or s["prov"] == prov


def _line(got, bi, att):
    seen, uniq = set(), []
    for s in got:
        if s["url"] not in seen:
            seen.add(s["url"])
            uniq.append(s)
    if not uniq:
        return ""
    links = " · ".join(f'<a href="{att(s["url"])}" rel="sponsored nofollow noopener" target="_blank">'
                       f'{bi(s["th"], s["en"])}</a>' for s in uniq)
    th, en = _AFF["label_th"], _AFF["label_en"]
    if len(uniq) > 1:
        th, en = th.replace("ลิงก์นี้", "ลิงก์เหล่านี้"), en.replace("Paid link:", "Paid links:")
    return (f'<p class="looline paidline">{links}'
            f' <span class="paidnote">{bi(th, en)}</span></p>')


def place_line(r, bi, att, esc):
    """One line of paid links under a place's title: slots naming this record,
    then slots on a shelf it sits in."""
    got = list(BY_RECORD.get(r.get("id"), []))
    prov = (r.get("id") or "")[:2]
    subs = r.get("sub") or []
    for c in r.get("cat") or []:
        for k in [c] + [f"{c}/{s}" for s in subs]:
            got += [s for s in BY_SHELF.get(k, [])
                    if s.get("on") != "shelf" and _prov_ok(s, prov)]
    return _line(got, bi, att)


def shelf_line(cat, sub, prov, bi, att, esc):
    """Paid links for a shelf page; a sub-shelf page also takes its shelf's."""
    keys = [cat] + ([f"{cat}/{sub}"] if sub else [])
    got = [s for k in keys for s in BY_SHELF.get(k, []) if _prov_ok(s, prov)]
    return _line(got, bi, att)
