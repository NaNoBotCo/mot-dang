"""The two marks the satellite control needs, drawn.

A NEW FILE RATHER THAN TWO LINES IN glyphs.py, on purpose: another session is
holding that file open, and a sprite is exactly the kind of thing where two
people editing one dict produces a merge that silently drops a glyph. The
contract is glyphs.py's, unchanged, so a mark from here sits beside one from
there and nobody can tell which file it came from:

  · 24-grid, stroke only — no `fill=`, no `stroke=`; colour is the row's,
    always, through the `.rowicon` rule in build.py's CSS;
  · margin 2.5, nothing at 0 or 24, because a 1.6 stroke on the grid edge
    is clipped;
  · ids `i-*`, and they must collide with NEITHER glyphs.IDS NOR
    build.ICON_SPRITE — a `<use>` resolves the first id it finds, so a
    duplicate draws the wrong picture and never errors.
    tests/test_satellite.py asserts both.

When glyphs.py is free, these two can move into `_G` there and this file can
go; nothing else has to change, because `icon()` below has the same signature
and `SPRITE` the same shape.
"""

_G = {
    # The [layers] door: three sheets seen edge-on, the top one being lifted.
    # Not a stack of squares — a stack of squares is i-grid, which is already
    # taken and means something else.
    "i-layers": '<path d="m12 3.2 8.6 4.6L12 12.4 3.4 7.8Z"/>'
                '<path d="m3.4 12 8.6 4.6 8.6-4.6"/>'
                '<path d="m3.4 16.2 8.6 4.6 8.6-4.6"/>',
    # The photograph of the ground: a satellite, body and two panels, with the
    # downlink it is sending. Read at 20 px it is unmistakably an instrument
    # looking down, which is the claim the layer is making — not a globe
    # (i-globe, taken, means the web) and not a camera (i-camera, taken,
    # means send a picture).
    "i-satellite": '<rect x="9.6" y="6.4" width="4.8" height="4.8" rx="1" '
                   'transform="rotate(45 12 8.8)"/>'
                   '<path d="M6.6 3.4 3.2 6.8l2.6 2.6 3.4-3.4ZM18.2 6.6l-3.4 3.4 '
                   '2.6 2.6 3.4-3.4Z"/>'
                   '<path d="M12 11.6v3"/>'
                   '<path d="M8.6 21c0-2 1.5-3.6 3.4-3.6s3.4 1.6 3.4 3.6"/>'
                   '<path d="M5.6 21c0-3.7 2.9-6.6 6.4-6.6s6.4 2.9 6.4 6.6"/>',
}

IDS = tuple(_G)


def sprite(ids=None):
    """The <svg><defs> block, same shape as glyphs.sprite()."""
    keys = list(_G) if ids is None else [k for k in _G if k in set(ids)]
    body = "\n".join('<g id="%s">%s</g>' % (k, _G[k]) for k in keys)
    return ('<svg aria-hidden="true" focusable="false" width="0" height="0" '
            'style="position:absolute" xmlns="http://www.w3.org/2000/svg"><defs>\n'
            + body + "\n</defs></svg>")


SPRITE = sprite()


def icon(name, size=22, cls="rowicon", label=None):
    """One <use>. Decorative unless `label` is given — same contract as
    glyphs.icon(), so a caller need not know which file a mark lives in."""
    if name not in _G:
        return ""
    a11y = ('role="img" aria-label="%s"' % label if label
            else 'aria-hidden="true" focusable="false"')
    return ('<svg class="%s" %s width="%d" height="%d" viewBox="0 0 24 24">'
            '<use href="#%s"></use></svg>' % (cls, a11y, size, size, name))
