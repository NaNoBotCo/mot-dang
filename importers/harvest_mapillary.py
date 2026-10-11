#!/usr/bin/env python3
"""harvest_mapillary.py — street-level photographs, baked at build time. WO-79.

    export MAPILLARY_TOKEN=MLY|...            # Nan makes this. See below.
    python3 importers/harvest_mapillary.py --bbox 98.96,18.77,99.02,18.81
    python3 importers/harvest_mapillary.py --bbox <...> --dry-run   # no token
    python3 importers/harvest_mapillary.py --self-test              # no network

THE PRIVACY PROPERTY IS THE WHOLE DESIGN
----------------------------------------
No reader ever fetches anything from Meta. This importer runs on Nan's own
machine, deliberately, outside the build; it downloads the chosen JPEG bytes
into `assets/streetphotos/` and writes the credit into
`data/street_photos.json`. build.py then copies those bytes into `docs/`,
which is the R2 bucket the site is served from. So a reader loading a place
page makes exactly one request, to our own origin, exactly as they already do
for every other picture on this site.

That is not a nicety. The Commons photographs on place pages today are
HOT-LINKED to upload.wikimedia.org (build.py ~line 10505), which means every
reader of those pages tells Wikimedia they are reading them. Doing the same
with Mapillary would tell META instead, and Meta is the company that disabled
the founder's account overnight on 29 July with one appeal. Baking is the
difference between using their data and introducing them to our readers.

Corollary, and it constrains the code below: HOT-LINKING A THUMBNAIL IS NOT
ALLOWED HERE, not even as a fallback when a download fails. A missing photo
is a missing photo.

WHAT NAN HAS TO DO HERSELF — I did not do it and did not try
-------------------------------------------------------------
The Graph API needs an access token, and a token belongs to a person with an
account. Verbatim steps, so this is not a "go and ask" note:

  1. Make an account at mapillary.com (a Meta login is one of the options;
     an email address is another, and the email one is the one that does not
     give Meta a second handle on you).
  2. Open mapillary.com/dashboard/developers and press "Register application".
     Name it anything. It asks which scopes; the only one this needs is
     `read` on images. It does NOT need write, upload, or private data.
  3. The page then shows a "Client token" beginning `MLY|`. That is the
     token. Copy it.
  4. With it on the clipboard: `~/.claude/bin/token save MAPILLARY_TOKEN`.
     That writes ~/.tokens/MAPILLARY_TOKEN (mode 600) on the Mac and on
     motdang-server (her word 2026-10-11: save tokens, they get reused).
     Not in data/ and not in the repo. MAPILLARY_TOKEN in the environment
     still wins over the saved file.

MEASURED WITHOUT A TOKEN, 2026-09-08 — what the failure actually looks like:
a tokenless request to graph.mapillary.com returns **HTTP 500**, not 401, with
a JSON body {"error":{"message":"Invalid OAuth 2.0 Access Token","code":190}}.
A naive `if status == 401` check would report that as a server outage and
retry it forever. `_explain()` below reads code 190 out of the body.

LICENCE
-------
Mapillary imagery is CC BY-SA 4.0. Three things follow, all enforced by
`credit_of()` and asserted by tests/test_streetphoto.py:

  · the photographer is named, per image, not "Mapillary";
  · the licence is named and linked;
  · the image links back to its page on mapillary.com.

Share-alike applies to the picture, not to this catalogue's own data — the
photograph is displayed alongside, never merged into, the record. Nan has
said share-alike is fine to use aggressively; that is the licence being used
as intended, not a risk being run.

CHIANG MAI COVERAGE IS OLD AND PATCHY, AND THE DATE IS A FIELD
--------------------------------------------------------------
`captured_at` is stored on every pick and the display side prints it. A photo
from 2016 shown without its year is a claim about what a street looks like
today, and that claim would be false often enough to matter. STALE_YEARS
below is where "old" is defined; the page says the year either way.

Stdlib only. Nothing here is imported by build.py.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "streetphotos"
INDEX = ROOT / "data" / "street_photos.json"

API = "https://graph.mapillary.com/images"
UA = ("mot-dang-directory/1.0 (+https://motdang.net; "
      "one-time street-level photo bake, CC BY-SA)")
LICENCE = "CC BY-SA 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"

# The fields worth asking for. `thumb_1024_url` because a place page shows a
# picture about 640 px wide on a phone and 1024 is the first size above that;
# `thumb_2048_url` would double the bake for nothing anybody can see.
FIELDS = ("id", "captured_at", "compass_angle", "computed_compass_angle",
          "geometry", "thumb_1024_url", "creator", "is_pano", "camera_type")

# How near a photograph has to have been taken to be about a place at all.
# 35 m is roughly "the far side of a two-lane soi": beyond that the camera is
# looking at somebody else's shopfront. Deliberately tighter than the 60 m
# neighbour test the Foursquare work landed on, because that test was asking
# "is this the same business" and this one is asking "is this building in
# frame", which is a stricter question.
NEAR_M = 35.0

# Past this, the display side says the photograph is old rather than merely
# dating it. Five years is not a rule about photographs; it is roughly how
# long a Chiang Mai shopfront lasts, which is the thing a reader is trying to
# find out when they look.
STALE_YEARS = 5

PAUSE = 0.35          # between requests. Their published search limit is
                      # 10,000/min; this is politeness, not compliance.
TIMEOUT = 30


# ── distance ─────────────────────────────────────────────────────────────────

def metres(lat1, lng1, lat2, lng2):
    """Haversine, the same formula explore.js counts the ring with. Kept here
    rather than imported because importers/ must run without the site."""
    import math
    r = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


# ── the token, and what its absence looks like ───────────────────────────────

class NoToken(RuntimeError):
    pass


def token(env=None):
    """MAPILLARY_TOKEN from the environment, else ~/.tokens/MAPILLARY_TOKEN
    (saved by `~/.claude/bin/token save`, her word 2026-10-11), or a clear
    refusal. The file is read only for the real environment; a caller passing
    its own env gets that env and nothing else. No prompt and no anonymous
    call: an anonymous call does not fail cleanly (see _explain), so it would
    turn a missing credential into a mysterious server error."""
    real = env is None
    env = os.environ if env is None else env
    t = (env.get("MAPILLARY_TOKEN") or "").strip()
    saved = Path.home() / ".tokens" / "MAPILLARY_TOKEN"
    if not t and real and saved.exists():
        t = saved.read_text().strip()
    if not t:
        raise NoToken(
            "MAPILLARY_TOKEN is not set, so nothing was fetched and nothing "
            "was changed.\n"
            "The token is Nan's to make — the steps are in the docstring at "
            "the top of this file (mapillary.com/dashboard/developers → "
            "Register application → read scope → copy the MLY| client "
            "token), copy it, then:\n"
            "    ~/.claude/bin/token save MAPILLARY_TOKEN\n"
            "To see what this would do without one:\n"
            "    python3 importers/harvest_mapillary.py --bbox <w,s,e,n> --dry-run")
    if not t.startswith("MLY|"):
        raise NoToken(
            "MAPILLARY_TOKEN is set but does not look like a Mapillary client "
            "token (they begin 'MLY|'). Refusing to send it: a token sent to "
            "the wrong place is worse than a missing one.")
    return t


def _explain(err_body, status):
    """Turn Mapillary's answer into a sentence. MEASURED 2026-09-08: a
    tokenless request returns 500, not 401, carrying error.code 190."""
    try:
        body = json.loads(err_body)
    except Exception:
        return "HTTP %s from Mapillary, and the body was not JSON." % status
    e = (body or {}).get("error") or {}
    code, msg = e.get("code"), e.get("message") or ""
    if code == 190:
        return ("Mapillary rejected the token (code 190: %s). Note the status "
                "is %s, not 401 — do not read this as an outage." % (msg, status))
    if code == 4 or code == 17 or status == 429:
        return "Mapillary is rate-limiting (code %s). Wait and run it again." % code
    return "HTTP %s from Mapillary: %s (code %s)" % (status, msg, code)


# ── the fetch ────────────────────────────────────────────────────────────────

def build_url(bbox, limit=500, fields=FIELDS):
    """The Graph API v4 search URL. Separated from the fetch so it can be
    checked without a token — which is most of what can be checked."""
    w, s, e, n = bbox
    q = urllib.parse.urlencode({
        "fields": ",".join(fields),
        "bbox": "%s,%s,%s,%s" % (w, s, e, n),
        "limit": str(int(limit)),
    })
    return API + "?" + q


def fetch(bbox, tok, limit=500, opener=None):
    """Image metadata inside a bbox. The token goes in the Authorization
    HEADER, never the query string: a URL ends up in shell history, in proxy
    logs and in this repo's own notes, and a credential in a URL is a
    credential that has been published."""
    url = build_url(bbox, limit)
    req = urllib.request.Request(url, headers={
        "Authorization": "OAuth " + tok,
        "User-Agent": UA,
    })
    op = opener or urllib.request.urlopen
    try:
        with op(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        raise RuntimeError(_explain(ex.read(), ex.code)) from None


# ── choosing one photograph per place ────────────────────────────────────────

def _when(captured_at):
    """Mapillary gives captured_at as epoch MILLISECONDS. Returns an ISO date
    string, or None. Never guesses: a photo with no date is displayed with no
    date, and the display side says so."""
    try:
        ms = int(captured_at)
    except (TypeError, ValueError):
        return None
    if ms <= 0:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date().isoformat()


def is_stale(iso_date, today=None, years=STALE_YEARS):
    """Older than STALE_YEARS. An unknown date counts as stale — we cannot
    say a photograph is current, so we do not."""
    if not iso_date:
        return True
    today = today or datetime.now(tz=timezone.utc).date()
    try:
        d = datetime.fromisoformat(iso_date).date()
    except ValueError:
        return True
    return (today - d).days > years * 365.25


def score(img, lat, lng):
    """How good a picture of THIS place. Lower is better.

    Distance first, because a photograph of the shop next door is the wrong
    photograph however pretty. Panoramas are pushed back: a 360 frame cropped
    to a card is usually a picture of the road. Age breaks ties, newest first
    — but age never overrides distance, because a fresh photo of the wrong
    building is still the wrong building.
    """
    g = (img.get("geometry") or {}).get("coordinates") or [None, None]
    if g[0] is None:
        return None
    d = metres(lat, lng, g[1], g[0])
    if d > NEAR_M:
        return None
    when = _when(img.get("captured_at"))
    age_days = 9999
    if when:
        age_days = (datetime.now(tz=timezone.utc).date()
                    - datetime.fromisoformat(when).date()).days
    return (round(d, 1) + (200.0 if img.get("is_pano") else 0.0)
            + age_days / 3650.0)


def pick(images, lat, lng):
    """The one photograph for a place, or None. None is a normal answer."""
    scored = []
    for im in images or []:
        s = score(im, lat, lng)
        if s is not None and im.get("thumb_1024_url"):
            scored.append((s, im))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0])
    return scored[0][1]


def credit_of(img):
    """The attribution block. CC BY-SA 4.0 requires the photographer by name
    and a route back to the original, so both are mandatory here: an image
    whose creator cannot be named is DROPPED rather than credited to
    'Mapillary', which would be a false attribution and a licence breach at
    the same time."""
    creator = (img.get("creator") or {})
    who = (creator.get("username") or "").strip()
    if not who:
        return None
    mid = str(img.get("id") or "").strip()
    if not mid:
        return None
    return {
        "by": who,
        "byUrl": "https://www.mapillary.com/app/user/" + urllib.parse.quote(who),
        "licence": LICENCE,
        "licenceUrl": LICENCE_URL,
        "source": "https://www.mapillary.com/app/?pKey=" + urllib.parse.quote(mid),
        "sourceName": "Mapillary",
        "imageId": mid,
        # THE DATE IS NOT OPTIONAL. See the module docstring.
        "captured": _when(img.get("captured_at")),
        "bearing": img.get("computed_compass_angle") or img.get("compass_angle"),
        "pano": bool(img.get("is_pano")),
    }


def download(url, dest, opener=None):
    """The bytes, onto our disk. This is the step that keeps readers off
    Meta's servers, so a failure here means no photo — never a hot link."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    op = opener or urllib.request.urlopen
    with op(req, timeout=TIMEOUT) as r:
        data = r.read()
    if len(data) < 1024:
        raise RuntimeError("suspiciously small image (%d bytes)" % len(data))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)


# ── the index build.py reads ─────────────────────────────────────────────────

def load_index(path=None):
    p = Path(path or INDEX)
    if not p.exists():
        return {"generated": None, "source": "mapillary", "licence": LICENCE,
                "photos": {}}
    d = json.loads(p.read_text())
    d.setdefault("photos", {})
    return d


def save_index(d, path=None):
    p = Path(path or INDEX)
    d["generated"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True))
    return p


def records_in_bbox(bbox, canonical_dir=None):
    """Pinned records inside a bbox, from data/canonical/. Read-only."""
    w, s, e, n = bbox
    d = Path(canonical_dir or (ROOT / "data" / "canonical"))
    out = []
    for f in sorted(d.glob("*.json")):
        if f.stem not in ("cm", "cr"):
            continue
        try:
            rows = json.loads(f.read_text())
        except Exception:
            continue
        for r in rows:
            lat, lng = r.get("lat"), r.get("lng")
            if lat is None or lng is None:
                continue
            if (r.get("geoPrecision") or "exact") == "needs-pin":
                continue
            if s <= lat <= n and w <= lng <= e:
                out.append(r)
    return out


def harvest(bbox, tok, limit=500, dry_run=False, opener=None, say=print):
    """One bbox, end to end. Returns a summary dict; writes nothing on a
    dry run."""
    recs = records_in_bbox(bbox)
    say("records pinned inside the bbox: %d" % len(recs))
    if dry_run:
        say("DRY RUN — the request that would be sent (token in the header, "
            "not shown):\n    %s" % build_url(bbox, limit))
        return {"records": len(recs), "fetched": 0, "picked": 0,
                "downloaded": 0, "dry_run": True}
    payload = fetch(bbox, tok, limit, opener=opener)
    images = payload.get("data") or []
    say("images returned by Mapillary: %d" % len(images))

    idx = load_index()
    picked = kept = dropped_nocredit = failed = 0
    for r in recs:
        if r["id"] in idx["photos"]:
            continue                    # snapshot-first, like the other importers
        best = pick(images, r["lat"], r["lng"])
        if not best:
            continue
        picked += 1
        cred = credit_of(best)
        if not cred:
            dropped_nocredit += 1
            continue
        dest = PHOTOS / ("%s.jpg" % r["id"])
        try:
            n = download(best["thumb_1024_url"], dest, opener=opener)
        except Exception as ex:
            failed += 1
            say("  could not download for %s: %s" % (r["id"], ex))
            continue
        cred["file"] = dest.name
        cred["bytes"] = n
        cred["placeId"] = r["id"]
        cred["distanceM"] = round(metres(
            r["lat"], r["lng"],
            best["geometry"]["coordinates"][1],
            best["geometry"]["coordinates"][0]), 1)
        idx["photos"][r["id"]] = cred
        kept += 1
        time.sleep(PAUSE)
    save_index(idx)
    say("picked %d · kept %d · dropped for no photographer name %d · failed %d"
        % (picked, kept, dropped_nocredit, failed))
    return {"records": len(recs), "fetched": len(images), "picked": picked,
            "kept": kept, "dropped_nocredit": dropped_nocredit, "failed": failed}


# ── self-test: everything that can be checked without a token ────────────────

def self_test(say=print):
    ok = True

    def check(name, cond):
        nonlocal ok
        say("  %-52s %s" % (name, "ok" if cond else "FAILED"))
        ok = ok and bool(cond)

    u = build_url((98.96, 18.77, 99.02, 18.81), 5)
    check("URL is the Graph v4 images endpoint", u.startswith(API + "?"))
    check("bbox goes over as w,s,e,n", "bbox=98.96%2C18.77%2C99.02%2C18.81" in u)
    check("the token is NEVER in the URL", "access_token" not in u and "MLY" not in u)
    check("every field asked for is in FIELDS", "thumb_1024_url" in u)

    check("no token -> NoToken, not a request",
          _raises(lambda: token({}), NoToken))
    check("a token of the wrong shape is refused",
          _raises(lambda: token({"MAPILLARY_TOKEN": "abc123"}), NoToken))
    check("a well-formed token is accepted",
          token({"MAPILLARY_TOKEN": "MLY|1|2"}) == "MLY|1|2")

    body = b'{"error":{"message":"Invalid OAuth 2.0 Access Token","code":190}}'
    check("HTTP 500 + code 190 reads as a token problem",
          "token" in _explain(body, 500).lower() and "not 401" in _explain(body, 500))

    check("captured_at ms -> ISO date",
          _when(1470009600000) == "2016-08-01")
    check("captured_at absent -> None, never a guess", _when(None) is None)
    check("no date counts as stale", is_stale(None) is True)
    check("a 2016 photo is stale", is_stale("2016-08-01") is True)
    check("a photo from today is not stale",
          is_stale(datetime.now(tz=timezone.utc).date().isoformat()) is False)

    near = {"id": "1", "captured_at": 1700000000000,
            "geometry": {"type": "Point", "coordinates": [98.98700, 18.78800]},
            "thumb_1024_url": "https://x/1.jpg",
            "creator": {"username": "somebody"}}
    far = dict(near, id="2",
               geometry={"type": "Point", "coordinates": [98.99900, 18.79900]})
    pano = dict(near, id="3", is_pano=True)
    check("a photo beyond NEAR_M is not a picture of the place",
          score(far, 18.788, 98.987) is None)
    check("the nearest non-pano wins",
          (pick([pano, near], 18.788, 98.987) or {}).get("id") == "1")
    check("nothing near enough -> None, not a bad photo",
          pick([far], 18.788, 98.987) is None)

    c = credit_of(near)
    check("credit names the photographer", c and c["by"] == "somebody")
    check("credit carries the licence", c and c["licence"] == LICENCE)
    check("credit links back to the image", c and "pKey=1" in c["source"])
    check("credit carries the capture date", c and c["captured"] == "2023-11-14")
    check("an image with no photographer is DROPPED, not credited to Mapillary",
          credit_of(dict(near, creator={})) is None)

    say("\nself-test: %s" % ("all checks passed" if ok else "FAILURES above"))
    return ok


def _raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bbox", help="w,s,e,n in degrees")
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--dry-run", action="store_true",
                    help="say what would be fetched; needs no token")
    ap.add_argument("--self-test", action="store_true",
                    help="everything checkable without a token or a network")
    a = ap.parse_args(argv)

    if a.self_test:
        return 0 if self_test() else 1
    if not a.bbox:
        ap.error("--bbox is required (or --self-test)")
    try:
        bbox = tuple(float(x) for x in a.bbox.split(","))
        assert len(bbox) == 4
    except Exception:
        ap.error("--bbox wants four numbers: w,s,e,n")
    if not a.dry_run:
        try:
            tok = token()
        except NoToken as ex:
            print(str(ex), file=sys.stderr)
            return 2
    else:
        tok = None
    harvest(bbox, tok, a.limit, dry_run=a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
