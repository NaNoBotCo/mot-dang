#!/usr/bin/env python3
"""THE LINE LANE — the three things that would silently poison the lead set.

A shop with no website still has a LINE Official Account, and that account's
public page carries a name, a phone, an address and a lat/lng. Three importers
work that seam: discover_line.py finds handles on the open web,
decode_line_qr.py decodes them off photographs of signs, probe_line_oa.py asks
LINE what each one is. None of them writes a record. What they can do is write
a WRONG lead, quietly, and three ways:

  A PERSON IS NOT A SHOP        line.me/ti/p/<token> is somebody's personal
      handle; page.line.me/@id is a business. They differ by one character
      class — the token carries capitals — and confusing them would put a
      private person into a directory. Tested in both directions.

  A HANDLE IS NOT A READING     A QR decodes or it does not. The vision model
      READS the letters off the sign and can read @ai1234 as @aI1234. The two
      never merge: a decoded handle is "qr", a read one is "sign reading —
      check it", and the distinction has to survive the sidecar round trip.

  noIndex MEANS NO              An account can ask not to be listed. It is
      honoured by leaving it out of `accounts`, and COUNTED, so a later pass
      cannot read the gap as a shop nobody found.

  AND THE SEED FILE IS SHARED   Two importers write cache/line_oa_seeds.json.
      Whichever runs second must not erase the first.

    python3 tests/test_line_discovery.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))

import decode_line_qr as qr                                  # noqa: E402
import probe_line_oa as probe                                # noqa: E402

fails = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        fails.append(name)


print("A PERSON IS NOT A SHOP")
check("basic id is an account", probe.classify("@gyk4392g") == ("oa", "@gyk4392g"))
check("vanity id is an account", probe.classify("ratchaphrueklab") == ("oa", "@ratchaphrueklab"))
check("~name is a person", probe.classify("~somebody")[0] == "personal")
check("a mixed-case token is a person", probe.classify("40hUhkHZKr")[0] == "personal")
check("a capitalised id is a person", probe.classify("@GYK4392G")[0] == "personal")
check("empty is neither", probe.classify("@") == (None, None))
got = probe.handles_in(
    "x https://lin.ee/Orxkq55 y https://line.me/R/ti/p/@288bwjse "
    "z http://line.me/ti/p/~someone w https://page.line.me/%40gyk4392g")
check("every url shape is read", sorted(got) == sorted([
    ("short", "Orxkq55"), ("oa", "@288bwjse"),
    ("personal", "~someone"), ("oa", "@gyk4392g")]), got)
check("a personal handle is never probed", probe.probe("personal", "~x")["outcome"] == "personal")
check("prose with no handle yields none", probe.handles_in("LINE is how they take orders") == [])

print("A HANDLE IS NOT A READING")
FIXTURE = {"props": {"pageProps": {"initialDataString": json.dumps({"account": {
    "accountInfo": {"basicSearchId": "@gyk4392g", "premiumSearchId": "@ratchaphrueklab",
                    "countryCode": "TH", "friendCount": 3906},
    "profile": {"name": "ราชพฤกษ์แล็บ", "badgeType": "certified",
                "btnList": [{"type": "call", "tel": "0857178242"}],
                "info": {"basicInfo": {"description": "เจาะเลือดถึงบ้าน"}, "statusMsg": "ยินดี"},
                "displayInformation": {"website": None, "workingTime": None,
                                       "newAddress": {"baseAddress": "5/1 moo.1",
                                                      "cityName": "Hangdong",
                                                      "provinceName": "Chiang Mai",
                                                      "postalCode": "50230",
                                                      "lat": 18.69, "lng": 98.92}}},
    "isNoIndex": False}})}}}
html = '<html><script id="__NEXT_DATA__" type="application/json">' + json.dumps(FIXTURE) + "</script></html>"
prof = probe.parse_profile(html)
check("the payload gives a pin", (prof["lat"], prof["lng"]) == (18.69, 98.92))
check("the payload gives a province", prof["province"] == "Chiang Mai")
check("the payload gives the phone off the call button", prof["tel"] == "0857178242")
check("the OA's own website field is carried through", prof["website"] is None)
check("a page with no payload is not a profile", probe.parse_profile("<html>nothing</html>") is None)
with tempfile.TemporaryDirectory() as d:
    photo = Path(d) / "sign.jpg"
    try:
        import cv2
        m = cv2.QRCodeEncoder.create().encode("https://lin.ee/Orxkq55")
        cv2.imwrite(str(photo), cv2.resize(m, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST))
        # The reading lives in the transcript, keyed by message id, which is
        # the image's own filename — not in the sidecar beside the picture.
        qr.CHAT = Path(d) / "chat"
        qr.CHAT.mkdir()
        (qr.CHAT / "2026-09-21.jsonl").write_text(json.dumps(
            {"message_id": photo.stem, "sign": {"line_id": "@readwrong"},
             "lat": 18.79, "lng": 98.98}, ensure_ascii=False) + "\n", encoding="utf-8")
        qr.SEEDS = Path(d) / "seeds.json"
        out = qr.run([photo])
        side = json.loads((Path(str(photo) + ".qr.json")).read_text(encoding="utf-8"))
        check("the QR decodes to the handle", side["handles"] == [{"kind": "short", "handle": "Orxkq55"}], side)
        check("the sign's letters are kept apart from it",
              side.get("typed") == [{"kind": "oa", "handle": "@readwrong"}], side)
        seeded = json.loads(qr.SEEDS.read_text(encoding="utf-8"))["handles"]
        hows = {h["how"] for h in seeded}
        check("and each seed says which it was", hows == {"qr", "sign reading — check it"}, hows)
        check("a frame with a pin hands it to every handle it produced",
              all(h.get("pin", {}).get("lat") == 18.79 for h in seeded), seeded)
    except AttributeError:
        print("  skip  QR round trip (no QR encoder in this OpenCV)")

print("noIndex MEANS NO")
with tempfile.TemporaryDirectory() as d:
    probe.CACHE = Path(d) / "line_oa"
    probe.CACHE.mkdir(parents=True)
    probe.OUT = Path(d) / "line_discovery.json"
    probe.SEARCH_SEEDS = Path(d) / "seeds.json"
    for row in ({"kind": "oa", "handle": "@aaa11111", "fetched": probe.TODAY, "outcome": "page",
                 "name": "listed", "province": "Chiang Mai", "lat": 1, "lng": 1,
                 "website": None, "noIndex": False},
                {"kind": "oa", "handle": "@bbb22222", "fetched": probe.TODAY, "outcome": "page",
                 "name": "asked not to be", "province": "Chiang Mai", "lat": 2, "lng": 2,
                 "website": None, "noIndex": True}):
        (probe.CACHE / f"oa_{row['handle'].lstrip('@')}.json").write_text(
            json.dumps(row, ensure_ascii=False), encoding="utf-8")
    doc = probe.report({})
    names = [a["name"] for a in doc["accounts"]]
    check("a noIndex account is not listed", names == ["listed"], names)
    check("and it is counted, not dropped", doc["counts"]["noIndexHonoured"] == 1)
    check("the report calls them leads",
          "LEADS, not records" in doc["_comment"])
    check("and does not claim a footprint is absent",
          "not a claim that no other footprint exists" in doc["_comment"])

print("THE SEED FILE IS SHARED")
with tempfile.TemporaryDirectory() as d:
    qr.SEEDS = Path(d) / "line_oa_seeds.json"
    qr.merge_seeds([{"kind": "oa", "handle": "@web11111", "how": "web search"}])
    qr.merge_seeds([{"kind": "oa", "handle": "@sign2222", "how": "qr"}])
    held = json.loads(qr.SEEDS.read_text(encoding="utf-8"))["handles"]
    check("the second writer keeps the first's handles", len(held) == 2, held)
    qr.merge_seeds([{"kind": "oa", "handle": "@web11111", "how": "qr", "found_on": "/a.jpg"}])
    held = json.loads(qr.SEEDS.read_text(encoding="utf-8"))["handles"]
    check("a handle seen twice stays one row", len(held) == 2, held)
    check("and gains what the second sighting knew",
          any(h.get("found_on") == "/a.jpg" for h in held), held)

print()
if fails:
    print(f"{len(fails)} FAILED: {', '.join(fails)}")
    sys.exit(1)
print("all green")
