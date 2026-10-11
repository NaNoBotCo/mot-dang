"""feedback_layer.py — the thumbs and the optional paragraph (Nan, 2026-10-11).

"You should be able to give feedback on any item on motdang (thumbs up, thumbs
down, pgph input optional field)." assets/feedback.js draws the control and
posts to /feedback on the claims Worker; this file puts a slot for it on a page
and loads the script.

    slot("place:cm-osm-node-1")   an empty <div data-fb="…"> the script fills
    SCRIPT_TAG(r)                 the <script> tag; page() adds it whenever a body
                                  carries a slot
    stamp_sites(docs)             one slot at the foot of each minisite's index.html

An item is a short id, 1 to 120 characters of A-Z a-z 0-9 : _ - . / (the Worker
refuses anything else): place:<id>, shelf:<prov>/<cat>[/<sub>], site:<slug>,
event:<key>, festival:<key>.  Answers are read on the Mac with
importers/sync_feedback.py.
"""
import re
from pathlib import Path

ITEM_RE = re.compile(r"^[A-Za-z0-9:_\-./]{1,120}$")
MARK = 'data-fb="'
# the doodle apps carry their own vote (doodle-vote); a full-screen canvas has no foot to stamp
SKIP_SITES = {"doodles", "doodle-map", "doodle-north", "doodle-chiang-rai"}


def slot(item):
    return f'<div data-fb="{item}"></div>' if ITEM_RE.match(item or "") else ""


def script_tag(r):
    return f'<script src="{r}feedback.js" defer></script>'


def stamp_sites(docs):
    """Add a slot and the script to docs/sites/<slug>/index.html. Returns the slugs stamped."""
    done = []
    root = Path(docs) / "sites"
    if not root.is_dir():
        return done
    for d in sorted(root.iterdir()):
        f = d / "index.html"
        if d.name in SKIP_SITES or not f.is_file():
            continue
        item = f"site:{d.name}"
        if not ITEM_RE.match(item):
            continue
        html = f.read_text(encoding="utf-8")
        if MARK in html or "</body>" not in html:
            continue
        add = (f'<div data-fb="{item}" style="max-width:42rem;margin:0 auto;padding:0 16px 1.5rem;'
               f'box-sizing:border-box"></div><script src="/feedback.js" defer></script>')
        i = html.rindex("</body>")
        f.write_text(html[:i] + add + html[i:], encoding="utf-8")
        done.append(d.name)
    return done
