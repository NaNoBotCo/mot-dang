#!/usr/bin/env python3
"""The clip under the photograph renders only when consent says it may.

    python3 tests/test_place_video.py

No build needed: video_layer is imported on its own with stand-in helpers. Held:

  1. a row with no consent field never renders;
  2. editorial false never renders;
  3. editorial true, face false, no blurred render → held;
  4. editorial true, face false, blurred true → rendered, with the file the row names;
  5. editorial true, face true → rendered;
  6. a place with no row renders nothing, and counts() agrees with the gate.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import video_layer  # noqa: E402


def att(s):
    return str(s).replace('"', "&quot;")


def esc(s):
    return str(s).replace("<", "&lt;")


def bi(th, en):
    return "%s · %s" % (th, en)


R = {"id": "cm-test-1"}
FILE = {"mp4": "v/cm-test-1/clip.mp4", "poster": "v/cm-test-1/clip.jpg", "date": "2026-09-22"}


def render(consent):
    row = dict(FILE)
    if consent is not None:
        row["consent"] = consent
    return video_layer.block(R, att, esc, bi, videos={"cm-test-1": row})


fails = 0


def check(name, cond):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        fails += 1


check("no consent field → nothing", render(None) == "")
check("editorial false → nothing", render({"tier2_editorial": False, "tier2_face_visible": True}) == "")
check("face false, not blurred → held",
      render({"tier2_editorial": True, "tier2_face_visible": False}) == "")
html = render({"tier2_editorial": True, "tier2_face_visible": False, "blurred": True})
check("face false, blurred → rendered", 'class="placevideo"' in html and "v/cm-test-1/clip.mp4" in html)
check("preload none, no autoplay", 'preload="none"' in html and "autoplay" not in html)
html = render({"tier2_editorial": True, "tier2_face_visible": True})
check("face true → rendered with poster and date", 'poster="../../v/cm-test-1/clip.jpg"' in html and "2026-09-22" in html)
check("no row → nothing", video_layer.block({"id": "cm-none"}, att, esc, bi, videos={}) == "")
shown, held, reasons = video_layer.counts({
    "a": {**FILE, "consent": {"tier2_editorial": True, "tier2_face_visible": True}},
    "b": {**FILE},
    "c": {**FILE, "consent": {"tier2_editorial": True, "tier2_face_visible": False}},
})
check("counts: 1 shown, 2 held, reasons named",
      shown == 1 and held == 2 and reasons.get("no consent field") == 1)
print("%d failure(s)" % fails if fails else "all held")
sys.exit(1 if fails else 0)
