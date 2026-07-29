#!/usr/bin/env python3
"""Build the LINE rich menu — the image and the tap-area JSON that goes with it.

The rich menu is the grid pinned to the bottom of the LINE chat. It is the
closest thing this project has to a granny interface: six always-there buttons,
no typing, no account, inside the app she already has open. It costs nothing —
rich menus are on LINE's free plan.

Layout, deliberately:

    ดวงวันนี้      เซียมซี        งานในเมือง      <- why anyone opens it
    ร้านนี้ของฉัน   ส่งรูป         ตรงนี้ผิด        <- what we would like them to do

Pleasure on the top row. Somebody who came to shake the fortune sticks is
already here when they notice their own shop is missing a phone number.

    python3 importers/make_richmenu.py

Writes assets/richmenu.png and assets/richmenu.json. Upload both in LINE OA
Manager (Home -> Rich menus), or POST the JSON to the Messaging API if a
channel token exists. The image is drawn by make_richmenu.swift, because
Pillow here has no raqm and cannot shape Thai.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWIFT = os.path.join(ROOT, "importers", "make_richmenu.swift")
PNG = os.path.join(ROOT, "assets", "richmenu.png")
JSON_OUT = os.path.join(ROOT, "assets", "richmenu.json")
SITE = "https://motdang.net/"

W, H, COLS, ROWS = 2500, 1686, 3, 2
CW, CH = W // COLS, H // ROWS

# Order must match the cells in make_richmenu.swift — same grid, same reading
# order, left to right then down.
ACTIONS = [
    {"type": "uri", "label": "duang", "uri": SITE + "widgets.html"},
    {"type": "uri", "label": "siamsi", "uri": SITE + "widgets.html#w-siamsi"},
    {"type": "uri", "label": "events", "uri": SITE + "events.html"},
    {"type": "uri", "label": "claim", "uri": SITE + "claim.html"},
    # These two are message actions on purpose. A photo is sent by sending a
    # photo — pushing someone to a web form to upload one is the barrier this
    # whole exercise exists to remove. Tapping puts the words in the box; she
    # attaches the picture and presses send, which she already knows how to do.
    {"type": "message", "label": "photo", "text": "ส่งรูป"},
    {"type": "message", "label": "fix", "text": "ตรงนี้ผิด"},
]

AREAS = []
for i, action in enumerate(ACTIONS):
    col, row = i % COLS, i // COLS
    AREAS.append({
        "bounds": {"x": col * CW, "y": row * CH, "width": CW, "height": CH},
        "action": action,
    })

MENU = {
    "size": {"width": W, "height": H},
    "selected": True,
    "name": "Mot Dang - main",
    "chatBarText": "เมนูมดแดง",
    "areas": AREAS,
}


def main():
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    try:
        out = subprocess.run(["swift", SWIFT, PNG], capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        raise SystemExit("swift not on PATH — install the Xcode command line tools")
    if out.returncode != 0:
        raise SystemExit("swift failed:\n" + (out.stderr or out.stdout)[:2000])

    size = os.path.getsize(PNG)
    with open(JSON_OUT, "w") as fh:
        json.dump(MENU, fh, ensure_ascii=False, indent=1)

    print(f"🐜 {PNG} ({size:,} bytes, {W}x{H})")
    print(f"🐜 {JSON_OUT} — {len(AREAS)} tap areas")
    if size > 1_000_000:
        print("⚠  over LINE's 1 MB limit — reduce detail or save as JPEG")
    for a in AREAS:
        act = a["action"]
        where = act.get("uri") or f'sends "{act.get("text")}"'
        b = a["bounds"]
        print(f'   ({b["x"]:>4},{b["y"]:>4}) {b["width"]}x{b["height"]}  {act["label"]:<7} -> {where}')
    print("\nUpload both in LINE OA Manager -> Home -> Rich menus.")
    print("The two message buttons need a matching auto-reply; see the keywords")
    print("printed by --replies.")
    if "--replies" in sys.argv:
        print("\n--- suggested auto-replies (OA Manager -> Auto-response) ---")
        print('keyword "ส่งรูป":')
        print("  ส่งรูปมาได้เลยเจ้า ถ่ายจากมือถือก็ได้ ใส่ชื่อร้านมาด้วยนะ")
        print("  แล้วเราจะลงเครดิตชื่อคุณไว้ใต้รูป")
        print("  (Send the photo right here. Tell us which place it is, and your")
        print("   name goes under the picture.)")
        print('\nkeyword "ตรงนี้ผิด":')
        print("  บอกมาสั้นๆ ได้เลย ว่าตรงไหนผิด แล้วที่ถูกคืออะไร")
        print("  ถ้ามีลิงก์หน้าร้านด้วยยิ่งดี")
        print("  (Tell us briefly what is wrong and what it should be. A link to")
        print("   the page helps.)")


if __name__ == "__main__":
    main()
