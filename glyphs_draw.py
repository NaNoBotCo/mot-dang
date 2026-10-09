"""glyphs_draw.py — the five marks the reader's own GIS needed and nobody had.

WHY A SECOND FILE
-----------------
`glyphs.py` holds 66 bespoke marks and `build.ICON_SPRITE` holds 42 more, and
between them they cover the site's furniture. Drawing on the map wants six
controls; five of them had no mark. Those five could have gone into glyphs.py
— and this file exists instead only because another session is editing
glyphs.py right now, so a second file is the way to add marks without two
writers in one dict. If that ever stops being true, fold these five in and
delete this module: nothing here is a different KIND of glyph.

THE CONTRACT IS glyphs.py's, UNCHANGED
--------------------------------------
24 grid, margin ~2.5, stroke only, no `fill=` and no `stroke=` inside the
sprite — colour is the row's, through the `.rowicon` rule in build.py. Round
caps come from that rule too. A mark from this file has to sit beside one from
either of the other two and be indistinguishable.

Ids are checked against BOTH existing sprites in tests/test_draw.py, because a
`<use href="#id">` resolves the FIRST id it finds in the document and a
collision draws the wrong picture silently — the same reason glyphs.py pins
build.BUILD_IDS.

WHAT WAS REUSED RATHER THAN DRAWN, and why each fits
----------------------------------------------------
    point mode   i-pin       (build.ICON_SPRITE) — a pin IS a dropped point
    line mode    i-route     (build.ICON_SPRITE) — a drawn path
    clear all    i-x         (glyphs.py) — the same mark ล้าง/Clear already
                             carries on /map.html's rail; two marks for one
                             verb would read as two verbs
    export       i-download  (glyphs.py)
    the link     i-link      (glyphs.py)
    measurement  i-ruler     — NEW; there was no measuring mark at all

Five drawn here: i-poly, i-cursor, i-erase, i-upload, i-ruler.
"""

import glyphs

# ── the drawings ─────────────────────────────────────────────────────────────
_G = {
    # A closed ring with its vertices showing. Not a plain pentagon: the dots
    # are what says "you place these corners", which is the whole gesture.
    "i-poly": '<path d="M12 3.2 20.3 9.3 17.1 19.2H6.9L3.7 9.3Z"/>'
              '<circle cx="12" cy="3.2" r="1.5"/><circle cx="20.3" cy="9.3" r="1.5"/>'
              '<circle cx="17.1" cy="19.2" r="1.5"/><circle cx="6.9" cy="19.2" r="1.5"/>'
              '<circle cx="3.7" cy="9.3" r="1.5"/>',
    # Select and move: the arrow, and the dashed box it works inside. The box
    # is what separates this from a plain cursor — it says "the shapes".
    "i-cursor": '<rect x="2.8" y="2.8" width="18.4" height="18.4" rx="2" stroke-dasharray="2.6 2.4"/>'
                '<path d="M8.5 7.2 16.8 12.6l-4 .9-1.6 3.9Z"/>',
    # Rub one shape out: an eraser on its baseline, tilted the way a hand
    # holds it. The line under it is the paper, so it reads as removing FROM
    # something rather than as a block.
    "i-erase": '<path d="M9.4 18.5 3.9 13a1.8 1.8 0 0 1 0-2.6l7-7a1.8 1.8 0 0 1 2.6 0l5.4 5.4a1.8 1.8 0 0 1 0 2.6l-6.6 6.6"/>'
               '<path d="M7.6 8.7 14.9 16"/><path d="M3 21h18"/>',
    # The mirror of i-download, and deliberately the same tray: a reader who
    # has learnt one has learnt the other. Arrow out of the tray, not into it.
    "i-upload": '<path d="M12 14.5V3.5M7.5 8 12 3.5 16.5 8"/><path d="M4 16v3.5h16V16"/>',
    # How long, how big: a rule with its ticks. The ticks are uneven on
    # purpose — an even comb reads as a barcode at 20 px.
    "i-ruler": '<rect x="2.6" y="7.5" width="18.8" height="9" rx="1.4" transform="rotate(-20 12 12)"/>'
               '<path d="M6.6 9.9v3M10.3 8.6v2M14 7.3v3M17.7 6v2"/>',
}

SPRITE_IDS = tuple(_G)
IDS = SPRITE_IDS

# Every id this module's callers may ask for: its own, plus everything the
# other two sprites already draw. icon() below refuses anything else rather
# than emitting a <use> pointing at nothing — an empty box on a 44 px control
# is a button with no label.
KNOWN = glyphs.KNOWN | frozenset(IDS)

# The ids draw_layer actually puts on a page, so the page carries five marks
# rather than seventy-three. Kept here because this module knows what it drew.
USED = ("i-pin", "i-route", "i-poly", "i-cursor", "i-erase",
        "i-ruler", "i-download", "i-upload", "i-link", "i-x")


def sprite(ids=None):
    """The <defs> block for THIS file's marks. The other two sprites are
    already on the page — build.ICON_SPRITE and glyphs.SPRITE are written by
    page() — so this adds five <g> and nothing else."""
    keys = list(_G) if ids is None else [k for k in _G if k in set(ids)]
    body = "\n".join(f'<g id="{k}">{_G[k]}</g>' for k in keys)
    return ('<svg aria-hidden="true" focusable="false" width="0" height="0" '
            'style="position:absolute" xmlns="http://www.w3.org/2000/svg"><defs>\n'
            + body + "\n</defs></svg>")


SPRITE = sprite()


def icon(name, size=22, cls="rowicon", label=None):
    """One <use>, over the union of all three sprites. Same signature and
    same a11y bargain as glyphs.icon(): decorative beside a label, named when
    the control has no words of its own."""
    if name not in KNOWN:
        return ""
    a11y = (f'role="img" aria-label="{label}"' if label
            else 'aria-hidden="true" focusable="false"')
    return (f'<svg class="{cls}" {a11y} width="{size}" height="{size}" '
            f'viewBox="0 0 24 24"><use href="#{name}"></use></svg>')


if __name__ == "__main__":
    import sys
    print(f"{len(_G)} new glyphs · {len(KNOWN)} known ids", file=sys.stderr)
    print(SPRITE)
