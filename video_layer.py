#!/usr/bin/env python3
"""A clip on a place page — the shop's own footage, or ours, under the photograph.

The capture pipeline writes data/place_videos.json; this module reads it and renders
one <figure class="placevideo"> per place that clears the consent gate. Files live
in assets/video/<place_id>/ and are copied to docs/v/ at the end of the build, the
same way the brief and the loop travel — an object put straight in the bucket would
be deleted by the next sync.

The gate, in one place, tested in tests/test_place_video.py:

  · no consent field at all              → held
  · tier2_editorial false                → held
  · tier2_face_visible false, not blurred → held  (the blurred render does not exist
                                            until the pipeline's export step makes it)
  · otherwise                             → rendered

Held rows are counted and printed by the build, never rendered.

Entry points: gate(row) → (ok, reason); block(r, helpers) → html; copy_assets(root, docs).
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "place_videos.json"
ASSETS = ROOT / "assets" / "video"

CSS = """
/* ---- a clip under the photograph ---------------------------------------- */
/* preload=none: nothing downloads until the reader presses play, which on a
   phone in Mae Hong Son is the difference between a page and a bill. */
.placevideo{margin:.9rem 0 .4rem}
.placevideo video{display:block;width:100%;max-height:70vh;border-radius:.8rem;
background:#000;border:1px solid var(--soft)}
.placevideo figcaption{font-size:.85rem;color:var(--muted);margin:.35rem .1rem 0}
"""


def load():
    if not DATA.exists():
        return {}
    d = json.loads(DATA.read_text(encoding="utf-8"))
    return d.get("videos", {}) if isinstance(d, dict) else {}


def gate(row):
    """(True, "") when this row may be rendered, else (False, why not)."""
    if not isinstance(row, dict):
        return False, "not a row"
    c = row.get("consent")
    if not isinstance(c, dict):
        return False, "no consent field"
    if c.get("tier2_editorial") is not True:
        return False, "no editorial consent"
    if c.get("tier2_face_visible") is not True and c.get("blurred") is not True:
        return False, "face not cleared and no blurred render"
    if not row.get("mp4"):
        return False, "no file"
    return True, ""


def block(r, att, esc, bi, videos=None):
    """The figure for one place, or "" — held rows and places with no clip alike."""
    rows = load() if videos is None else videos
    row = rows.get(r.get("id"))
    if not row:
        return ""
    ok, _why = gate(row)
    if not ok:
        return ""
    src = "../../" + row["mp4"].lstrip("/")
    poster = ('poster="../../%s" ' % att(row["poster"].lstrip("/"))) if row.get("poster") else ""
    who_th = row.get("credit_th") or "ร้านนี้ถ่ายเอง"
    who_en = row.get("credit_en") or "filmed by the shop"
    when = row.get("date") or ""
    cap = bi(who_th, who_en) + ((" · " + esc(when)) if when else "")
    return ('<figure class="placevideo"><video controls playsinline preload="none" %s'
            'aria-label="%s"><source src="%s" type="video/mp4"></video>'
            '<figcaption>%s</figcaption></figure>'
            % (poster, att(who_en), att(src), cap))


def counts(videos=None):
    rows = load() if videos is None else videos
    shown = held = 0
    reasons = {}
    for row in rows.values():
        ok, why = gate(row)
        if ok:
            shown += 1
        else:
            held += 1
            reasons[why] = reasons.get(why, 0) + 1
    return shown, held, reasons


def copy_assets(docs):
    """assets/video/ → docs/v/, only for rows the gate lets through."""
    rows = load()
    n = 0
    for pid, row in rows.items():
        ok, _ = gate(row)
        if not ok:
            continue
        for key in ("mp4", "poster"):
            rel = (row.get(key) or "").lstrip("/")
            if not rel.startswith("v/"):
                continue
            src = ASSETS / rel[2:]
            if src.exists():
                dest = docs / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                n += 1
    return n
