#!/usr/bin/env python3
"""A Facebook link is built from a free-text OSM field, so it is tested.

`contact:facebook` is whatever a mapper typed. On 2026-09-06 the catalogue held
232 of them: 134 clean URLs, 57 valid bare handles, 26 carrying share/tracking
junk, and 15 that the old one-liner turned into a BROKEN link — including
https://www.facebook.com/www.facebook.com/ThaiDress, a 404 shipped on a live
page, and nine values that were the page's NAME ("Audition music & art room",
"เต้ยดนตรี", "炭と鮨 Sumi to Sushi") rather than a handle.

The rule the third block tests is the one that matters: a name is NOT searched
for and NOT slugified into a URL. Guessing which page "Audition music & art
room" is would point a reader at the wrong shop, and a wrong link is worse than
no link on a directory whose whole claim is that facts carry their source.

    python3 tests/test_facebook_links.py
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fburl import fb_url_of  # the shipped normaliser, shared with build.py

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def main():
    print("a bare handle becomes a URL")
    check("plain handle", fb_url_of("akhaamacoffee") == "https://www.facebook.com/akhaamacoffee")
    check("leading slash", fb_url_of("/akhaamacoffee") == "https://www.facebook.com/akhaamacoffee")
    check("percent-encoded page slug kept whole",
          fb_url_of("Valentan-caf%C3%A9-111466000639513")
          == "https://www.facebook.com/Valentan-caf%C3%A9-111466000639513")

    print("\na URL is cleaned, never doubled")
    check("scheme-less URL gets its scheme, not the prefix",
          fb_url_of("www.facebook.com/ThaiDress") == "https://www.facebook.com/ThaiDress",
          fb_url_of("www.facebook.com/ThaiDress") or "None")
    check("profile.php?id= survives — it IS the address",
          fb_url_of("www.facebook.com/profile.php?id=100065433522102")
          == "https://www.facebook.com/profile.php?id=100065433522102")
    check("share tracking stripped",
          fb_url_of("https://www.facebook.com/klab.ma.rak?rdid=X&share_url=Y#")
          == "https://www.facebook.com/klab.ma.rak")
    check("fbclid stripped",
          fb_url_of("https://www.facebook.com/x/?fbclid=abc") == "https://www.facebook.com/x")

    print("\na page NAME is refused, never guessed into a link")
    for name in ("Audition music & art room", "Maximum Sound Chiangmai",
                 "เต้ยดนตรี", "炭と鮨 Sumi to Sushi", "Patr Music-ภัทร มิวสิค"):
        check(f"refuses {name[:28]!r}", fb_url_of(name) is None, str(fb_url_of(name)))
    check("empty is None", fb_url_of("") is None)
    check("None is None", fb_url_of(None) is None)

    print("\nevery value in the catalogue either resolves or is refused")
    bad = []
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if not f.exists():
            continue
        for r in json.loads(f.read_text(encoding="utf-8")):
            v = (r.get("attrs") or {}).get("facebook")
            if not v:
                continue
            u = fb_url_of(v)
            if u is None:
                continue
            if not u.startswith("https://") or "facebook.com/www." in u or " " in u:
                bad.append((r.get("id"), v, u))
    check("no built link is malformed", not bad,
          "; ".join(f"{i}: {v!r} -> {u}" for i, v, u in bad[:4]))

    print()
    if failures:
        print(f"{len(failures)} failure(s): {failures}")
        return 1
    print("facebook links hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
