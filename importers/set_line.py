#!/usr/bin/env python3
"""Point Mot Dang's contribute doors at the LINE Official Account.

    python3 importers/set_line.py @motdang
    python3 importers/set_line.py https://lin.ee/AbCdEf

Give it the Basic ID or the share link from LINE OA Manager — both are on the
account's own page ("Gain friends" / เพิ่มเพื่อน, or Settings → Account
settings). Either is checked, written into data/config.json, and every
contribute door across the site switches from email to LINE on the next build.

Deliberately NOT accepting the numeric id out of the manager URL
(page.line.biz/account-page/<digits>/profile): that address is the admin
console, and line.me/R/ti/p/<digits> answers 200 with byte-identical HTML for
an id that does not exist, so a wrong one cannot be told from a right one until
somebody taps it and lands nowhere.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "data", "config.json")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def reachable(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.geturl(), r.read(4000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except (urllib.error.URLError, OSError) as e:
        return None, url, str(e)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    arg = sys.argv[1].strip()

    if re.fullmatch(r"@[A-Za-z0-9_.-]{2,30}", arg):
        basic = arg
        add_url = "https://line.me/R/ti/p/" + urllib_quote(basic)
        check = "https://page.line.me/" + basic.lstrip("@")
    elif re.match(r"^https?://lin\.ee/[A-Za-z0-9]+$", arg):
        basic = ""
        add_url = arg
        check = arg
    elif re.fullmatch(r"\d{6,}", arg) or "page.line.biz" in arg:
        raise SystemExit(
            "That is the OA Manager (admin) id or URL, which nobody but you can open.\n"
            "Take the Basic ID (@something) or the lin.ee share link from that page instead —\n"
            "the numeric form cannot be verified: line.me answers 200 for ids that do not exist.")
    else:
        raise SystemExit(f"Not a Basic ID or a lin.ee link: {arg!r}")

    code, final, body = reachable(check)
    if code != 200:
        raise SystemExit(f"{check} did not answer 200 (got {code}). Not writing a link "
                         "that may dead-end someone.")
    print(f"✓ {check} answers 200")
    if basic and basic.lstrip("@").lower() not in (body + final).lower():
        print(f"⚠  the page did not visibly mention {basic} — check it is the right account "
              "before you push")

    cfg = json.load(open(CFG)) if os.path.exists(CFG) else {}
    cfg["lineOaId"] = basic
    cfg["lineAddUrl"] = add_url
    json.dump(cfg, open(CFG, "w"), ensure_ascii=False, indent=1)
    print(f"🐜 wrote lineAddUrl = {add_url}")
    print("   now: python3 build.py   (every contribute door switches to LINE)")


def urllib_quote(s):
    import urllib.parse
    return urllib.parse.quote(s, safe="")


if __name__ == "__main__":
    main()
