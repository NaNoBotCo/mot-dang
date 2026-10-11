#!/usr/bin/env python3
"""Screenshots of the draft, for looking at it.

Two traps, both hit before: background-attachment:fixed sizes to the VIEWPORT, so a
tall headless window zooms into a patch of sky; and anything measured in vh grows with
the window. So the shot runs against a COPY with both pinned.

The copy sits NEXT TO the page, not in a temp directory: every picture on it is a
relative path, and a copy somewhere else is a page with no pictures.

    python3 shot.py 1440 2200 top.png            # a window
    python3 shot.py 1440 9000 full.png dark      # the lot, in the other theme
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path("/private/tmp/claude-501/-Users-annikapeacock-Desktop-catalog/"
                   "2bd32f5a-a3ca-4e72-b623-b6ff2969a9f1/scratchpad")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PIN = """<style>
.band{background-attachment:scroll!important;min-height:440px!important}
@media(min-width:61rem){.bigmap .plate{height:1044px!important}}
</style></head>"""

w, h, name = sys.argv[1], sys.argv[2], sys.argv[3]
theme = sys.argv[4] if len(sys.argv) > 4 else "light"
src = (HERE / "index.html").read_text().replace("</head>", PIN, 1)
# headless picks its own colour scheme; the page answers to data-theme, so say it.
src = src.replace('<html lang="th">', f'<html lang="th" data-theme="{theme}">', 1)
# <picture> answers to the OS, not to data-theme, so pick the plate's frame by hand.
if theme == "dark":
    src = src.replace("img/map-dots-light.png", "img/map-dots-dark.png")
src = re.sub(r"<source[^>]*map-dots-dark[^>]*>", "", src)
copy = HERE / "_shot.html"
copy.write_text(src)
# HEADLESS CHROME LAYS THE PAGE OUT AT DESKTOP WIDTH whatever --window-size says, so a
# phone shot taken that way is a desktop page cropped. An iframe is a real viewport:
# media queries inside it answer to ITS width.
frame = None
if len(sys.argv) > 5 and sys.argv[5] == "frame":
    frame = HERE / "_frame.html"
    frame.write_text(f'<body style="margin:0"><iframe src="_shot.html" width="{w}" '
                     f'height="{h}" style="border:0;display:block"></iframe>')
out = OUT / name
subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                f"--window-size={int(w) + (30 if frame else 0)},{h}", f"--screenshot={out}",
                "--virtual-time-budget=4000",
                (frame or copy).as_uri()], check=True,
               capture_output=True)
copy.unlink()
if frame:
    frame.unlink()
print(out, out.stat().st_size)
