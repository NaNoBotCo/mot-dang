#!/usr/bin/env python3
"""WO-44 — the quiet inks stay readable. Zero network.

The defect this file exists for: `--mute` sat at **3.0:1** against the paper
and `--gloss` at 4.0:1, both under the 4.5:1 floor for body text — and they
were not decorative. Between them they set 93 rules, every one of them a
`color:`, on exactly the smallest text the site prints: `.tinynote`, `.src`,
`.cat`, `.teaser`, `.photodesc`, `.adlabel`, and the homepage's own opening
paragraph. **The site's whole trust argument — provenance lines, source
credits, read-dates — was written in its least readable ink.**

What this pins:

  FLOOR    every ink the site sets text in clears 4.5:1 against each light
           surface it can sit on — the paper, the card, and the card-alt
           that the chips and bands use.
  LADDER   the four inks stay four distinguishable steps. Pushing the quiet
           pair up to the floor is only half the job; pushing them so far
           that `--gloss` collapses into `--ink-soft` would buy contrast by
           spending a level of the palette, which is a different kind of
           worse.
  GOLD     `--gold` was doing two jobs — the bead after a band label and the
           hero's hello line, the counts on the nine doors and the care shelf.
           At 2.8:1 it was never a text colour. `--gold-ink` is the same hue
           carried down to the floor; `--gold` keeps the decoration, and is
           allowed to stay under the floor ONLY where nothing is read.

  HONEST   `--soft` (#e3d5bc) is the one surface `--mute` still does not
           clear (3.5:1). It is 49 borders to 24 backgrounds, and the fix
           belongs to those few bands, not to the token. The exemption is
           written down here rather than left for someone to rediscover.

    python3 tests/test_contrast.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build            # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


def _lum(hexv):
    h = hexv.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in ch]
    return .2126 * ch[0] + .7152 * ch[1] + .0722 * ch[2]


def ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def _hue(hexv):
    import colorsys
    h = hexv.lstrip("#")
    r_, g_, b_ = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return colorsys.rgb_to_hls(r_, g_, b_)[0] * 360


def token(name):
    """Read a token straight out of the stylesheet, so the test reads what
    ships rather than a number copied into the test."""
    m = re.search(rf"--{name}:(#[0-9a-fA-F]{{6}})", build.CSS)
    return m.group(1) if m else None


AA = 4.5
INKS = ("ink", "ink-soft", "gloss", "mute")
LIGHT = ("paper", "card", "card-alt")

print("the tokens are readable off the stylesheet")
vals = {n: token(n) for n in INKS + ("soft",) + LIGHT}
missing = [n for n, v in vals.items() if not v]
check("every ink and surface token is found", not missing, missing)

print(f"the floor — {AA}:1 on every light surface the inks sit on")
for ink in INKS:
    for surf in LIGHT:
        r = ratio(vals[ink], vals[surf])
        check(f"--{ink} on --{surf}: {r:.1f}:1", r >= AA)

print("the ladder — four distinguishable steps, quietest last")
order = [ratio(vals[i], vals["paper"]) for i in INKS]
check("ink > ink-soft > gloss > mute",
      all(a > b for a, b in zip(order, order[1:])),
      [f"{i}={r:.1f}" for i, r in zip(INKS, order)])
check("no two neighbouring inks collapse into each other (>1.15x apart)",
      all(a / b > 1.15 for a, b in zip(order, order[1:])),
      [f"{i}={r:.1f}" for i, r in zip(INKS, order)])

print("the written-down exemption")
r_soft = ratio(vals["mute"], vals["soft"])
check(f"--mute on --soft is knowingly below the floor ({r_soft:.1f}:1) — "
      "the bands' problem, not the token's", r_soft < AA)
check("and --soft is still mostly a border colour, which is why",
      len(re.findall(r"border[a-z-]*:[^;{}]*var\(--soft\)", build.CSS))
      > len(re.findall(r"background:var\(--soft\)", build.CSS)))

print("gold speaks and gold decorates, and they are now two tokens")
gold, gold_ink = token("gold"), token("gold-ink")
check("--gold-ink exists", bool(gold_ink), gold_ink)
if gold_ink:
    for surf in LIGHT:
        r = ratio(gold_ink, vals[surf])
        check(f"--gold-ink on --{surf}: {r:.1f}:1", r >= AA)
    check("it is still gold — same hue as --gold, only carried darker",
          abs(_hue(gold_ink) - _hue(gold)) < 2,
          f"{_hue(gold_ink):.0f}deg vs {_hue(gold):.0f}deg")
    check("and distinct from the ant red it sits near",
          ratio(gold_ink, "#8f2a21") > 1.3)

# The decorative gold is ALLOWED to stay under the floor — that is the whole
# point of splitting it — but only where nothing is read. If a future rule
# points --gold at text again, this is the check that says so.
DECORATIVE_TEXT = {".svclbl::after",            # a " ‧ " bead between band labels
                   ".sidecard.dark .yantra"}    # a watermark at opacity .16, on dark
gold_text = set()
# (?<![-a-z]) so `text-decoration-color:var(--gold)` — the underline on a
# hovered header link — is not mistaken for a text colour. It decorates.
for m in re.finditer(
        r"([.#][a-zA-Z][a-zA-Z0-9_ .,>:()-]*)\{[^}]*(?<![-a-z])color:var\(--gold\)",
        build.CSS):
    for sel in m.group(1).split(","):
        gold_text.add(sel.strip())
stray = gold_text - DECORATIVE_TEXT
check("--gold is used as a text colour ONLY where nothing is read",
      not stray, sorted(stray))

print("the quiet inks are text-only, so darkening them moves no structure")
for ink in ("mute", "gloss"):
    uses = re.findall(rf"([a-z-]+):[^;{{}}]*var\(--{ink}\)", build.CSS)
    check(f"--{ink} is used for color: and nothing else ({len(uses)} uses)",
          set(uses) == {"color"}, sorted(set(uses)))

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all contrast checks passed")
