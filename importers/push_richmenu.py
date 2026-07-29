#!/usr/bin/env python3
"""Install the rich menu on the LINE account in one command.

Doing it by hand means uploading the image, picking a template, then placing
six tap areas one at a time and getting every bound right. This does the same
three things the Messaging API exposes — create, upload, set as default — and
gets the bounds from assets/richmenu.json, which was generated from the same
grid that drew the picture, so they cannot drift apart.

    python3 importers/push_richmenu.py            # install and set as default
    python3 importers/push_richmenu.py --list     # what is installed now
    python3 importers/push_richmenu.py --replace  # remove the old ones first

THE TOKEN. This needs a channel access token, which can send messages as the
account, so it is never typed on the command line and never written into the
repo. Put it in ~/.mot-dang-line-token (chmod 600) or export LINE_CHANNEL_TOKEN.
Get one at developers.line.biz -> your provider -> the channel linked to the OA
-> Messaging API -> Channel access token (long-lived). If the OA has no linked
channel yet: OA Manager -> Settings -> Messaging API -> Enable.
"""
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MENU_JSON = os.path.join(ROOT, "assets", "richmenu.json")
MENU_PNG = os.path.join(ROOT, "assets", "richmenu.png")
TOKEN_FILE = os.path.expanduser("~/.mot-dang-line-token")
API = "https://api.line.me/v2/bot"
DATA_API = "https://api-data.line.me/v2/bot"


def token():
    t = os.environ.get("LINE_CHANNEL_TOKEN", "").strip()
    if not t and os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE).read().strip()
    if not t:
        raise SystemExit(
            "No channel access token.\n\n"
            "  1. developers.line.biz -> your provider -> the channel linked to the\n"
            "     Official Account -> Messaging API -> issue a long-lived token.\n"
            "     (No channel yet? OA Manager -> Settings -> Messaging API -> Enable.)\n"
            f"  2. Save it:  printf %s 'THE_TOKEN' > {TOKEN_FILE} && chmod 600 {TOKEN_FILE}\n\n"
            "It is kept outside the repo on purpose — that token can send messages\n"
            "as the account, and this repo is public.")
    return t


def call(url, method="GET", body=None, content_type="application/json", raw=False):
    headers = {"Authorization": "Bearer " + token()}
    if body is not None:
        headers["Content-Type"] = content_type
    data = body if raw else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(text) if text.strip().startswith("{") else text)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"LINE API {e.code} on {method} {url}\n{detail[:900]}")


def listing():
    _, doc = call(API + "/richmenu/list")
    menus = doc.get("richmenus", []) if isinstance(doc, dict) else []
    if not menus:
        print("no rich menus installed")
        return []
    for m in menus:
        print(f"  {m['richMenuId']}  {m.get('name','')}  "
              f"{m['size']['width']}x{m['size']['height']}  areas={len(m.get('areas', []))}")
    return menus


def main():
    if "--list" in sys.argv:
        listing()
        return
    for p in (MENU_JSON, MENU_PNG):
        if not os.path.exists(p):
            raise SystemExit(f"{p} missing — run importers/make_richmenu.py first")

    menu = json.load(open(MENU_JSON))
    png = open(MENU_PNG, "rb").read()
    if len(png) > 1_000_000:
        raise SystemExit(f"{MENU_PNG} is {len(png):,} bytes; LINE's limit is 1 MB")

    if "--replace" in sys.argv:
        for m in listing():
            call(API + "/richmenu/" + m["richMenuId"], method="DELETE")
            print(f"   deleted {m['richMenuId']}")

    _, made = call(API + "/richmenu", method="POST", body=menu)
    rid = made["richMenuId"]
    print(f"🐜 created {rid}")

    call(f"{DATA_API}/richmenu/{rid}/content", method="POST", body=png,
         content_type="image/png", raw=True)
    print(f"🐜 uploaded {len(png):,} bytes of image")

    call(f"{API}/user/all/richmenu/{rid}", method="POST")
    print(f"🐜 set as the default menu for everyone who messages the account")
    print("\nOpen the LINE chat and it should be pinned at the bottom.")
    print("The two message buttons put ส่งรูป / ตรงนี้ผิด in the box — replies land in")
    print("OA Manager's chat inbox, so either answer them yourself or add a keyword")
    print("auto-response (make_richmenu.py --replies prints wording to paste).")


if __name__ == "__main__":
    main()
