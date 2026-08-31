#!/usr/bin/env python3
"""Check every outbound official-site link and record whether it actually works.

The point is not to shame anyone's webmaster. It is that a Mot Dang page should
never send someone into a browser security warning or a parked-domain ad farm.
When a place's own site is broken we say so plainly, link the Wayback snapshot
instead, and put the channels that DO work (phone, LINE, Facebook) first.

Snapshot-first and resumable, like crawl_overpass.py: every URL's verdict is
cached under cache/linkhealth/, so a rerun only touches what is missing or stale.

    python3 importers/check_links.py            # check what isn't cached yet
    python3 importers/check_links.py --recheck  # ignore cache, check everything
    python3 importers/check_links.py --max 50   # stop after 50 live checks
"""

import concurrent.futures
import hashlib
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "linkhealth")
OUT = os.path.join(ROOT, "data", "linkhealth.json")
UA = "MotDangLinkCheck/1.0 (+https://motdang.net/reach.html; link health for a local directory)"
TIMEOUT = 15
WORKERS = 6
STALE_DAYS = 30

# Hosts that are walled gardens, not websites. A bot cannot tell a live page from
# a dead one behind a login wall, so we never guess — we classify and move on.
SOCIAL = {
    "facebook.com": "facebook", "m.facebook.com": "facebook", "web.facebook.com": "facebook",
    "fb.com": "facebook", "fb.me": "facebook", "instagram.com": "instagram",
    "line.me": "line", "lin.ee": "line", "tiktok.com": "tiktok",
    "twitter.com": "x", "x.com": "x", "youtube.com": "youtube", "youtu.be": "youtube",
    "wa.me": "whatsapp",
}

# Two-level public suffixes we actually meet in Thailand.
TWO_LEVEL = {"co", "ac", "go", "or", "in", "net", "mi", "com", "org"}

PARKED_MARKERS = [
    "this domain is for sale", "buy this domain", "domain for sale", "domain is parked",
    "parked free, courtesy", "godaddy.com/domainsearch", "sedoparking", "bodis.com",
    "afternic", "hugedomains", "this site is temporarily unavailable",
    "account suspended", "suspended page", "บัญชีถูกระงับ", "โดเมนนี้",
    "future home of something quite cool", "default web page", "it works!",
    "welcome to nginx", "apache2 ubuntu default page", "index of /",
]


def registrable(host):
    """Best-effort registrable domain without pulling in a public-suffix library."""
    host = (host or "").lower().split(":")[0].strip(".")
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    if len(parts[-1]) == 2 and parts[-2] in TWO_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def normalize(url):
    url = (url or "").strip()
    if not url:
        return None
    if "://" not in url:
        url = "http://" + url
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if p.scheme not in ("http", "https") or not p.netloc:
        return None
    return urllib.parse.urlunsplit(p)


def social_kind(url):
    p = urllib.parse.urlsplit(url)
    return SOCIAL.get(registrable(p.netloc)) or SOCIAL.get(p.netloc.lower().replace("www.", ""))


def _open(url, verify=True):
    ctx = ssl.create_default_context()
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "th,en;q=0.8",
    })
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx), NoRedirect())
    return opener.open(req, timeout=TIMEOUT)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects by hand so we can see where a link really lands."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_chain(url, verify=True, max_hops=6):
    """Walk the redirect chain manually. Returns (final_url, code, body, hops)."""
    hops = []
    current = url
    for _ in range(max_hops):
        try:
            resp = _open(current, verify=verify)
        except urllib.error.HTTPError as e:
            code = e.code
            loc = e.headers.get("Location") if e.headers else None
            if code in (301, 302, 303, 307, 308) and loc:
                nxt = urllib.parse.urljoin(current, loc)
                hops.append(nxt)
                current = nxt
                continue
            body = b""
            try:
                body = e.read(120_000)
            except Exception:
                pass
            return current, code, body, hops
        with resp:
            body = resp.read(120_000)
        return resp.geturl(), resp.status, body, hops
    return current, 310, b"", hops


def sniff(body):
    try:
        text = body.decode("utf-8", "ignore").lower()
    except Exception:
        return None
    head = text[:20_000]
    for m in PARKED_MARKERS:
        if m in head:
            return m
    return None


def check(url):
    """Classify one URL. Returns a verdict dict — never raises."""
    v = {"url": url, "checkedAt": date.today().isoformat()}
    kind = social_kind(url)
    if kind:
        v.update(status="social", channel=kind,
                 note="walled garden — reachable for people, not verifiable by a crawler")
        return v
    try:
        final, code, body, hops = fetch_chain(url)
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLCertVerificationError) or isinstance(reason, ssl.SSLError):
            detail = str(getattr(reason, "verify_message", "") or reason)
            # Is anything alive behind the bad certificate?
            alive = False
            try:
                final, code, body, hops = fetch_chain(url, verify=False)
                alive = 200 <= code < 400
            except Exception:
                pass
            v.update(status="tls", detail=detail[:200], aliveBehindCert=alive)
            return v
        if isinstance(reason, socket.gaierror):
            v.update(status="dns", detail=str(reason)[:200])
            return v
        if isinstance(reason, socket.timeout):
            v.update(status="timeout", detail="no response in %ds" % TIMEOUT)
            return v
        v.update(status="down", detail=str(reason)[:200])
        return v
    except socket.timeout:
        v.update(status="timeout", detail="no response in %ds" % TIMEOUT)
        return v
    except Exception as e:  # malformed URL, weird encoding, http.client oddities
        v.update(status="error", detail=f"{type(e).__name__}: {e}"[:200])
        return v

    v["final"] = final
    v["code"] = code
    start_dom = registrable(urllib.parse.urlsplit(url).netloc)
    end_dom = registrable(urllib.parse.urlsplit(final).netloc)
    if hops:
        v["hops"] = len(hops)
    if code >= 500:
        v.update(status="server-error")
        return v
    if code >= 400:
        v.update(status="gone" if code in (404, 410) else "http-error")
        return v
    moved = social_kind(final)
    if moved and end_dom != start_dom:
        v.update(status="moved-social", channel=moved,
                 note="the site now just forwards to a social page")
        return v
    if end_dom != start_dom:
        v.update(status="redirect-offsite", to=end_dom)
    marker = sniff(body)
    if marker:
        v.update(status="parked", detail=marker)
        return v
    if len(body.strip()) < 200:
        v.update(status="empty")
        return v
    v.setdefault("status", "ok")
    return v


def wayback(url):
    """Closest archived snapshot, so a dead link still leads somewhere real."""
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    try:
        req = urllib.request.Request(api, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None
    snap = (data.get("archived_snapshots") or {}).get("closest") or {}
    if snap.get("available") and snap.get("url"):
        return {"url": snap["url"].replace("http://web.archive.org", "https://web.archive.org"),
                "timestamp": snap.get("timestamp", "")}
    return None


def cache_path(url):
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".json")


def cached(url, recheck):
    if recheck:
        return None
    p = cache_path(url)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as fh:
            v = json.load(fh)
    except Exception:
        return None
    try:
        age = (date.today() - date.fromisoformat(v.get("checkedAt", "1970-01-01"))).days
    except ValueError:
        return None
    return v if age < STALE_DAYS else None


def save(v):
    os.makedirs(CACHE, exist_ok=True)
    with open(cache_path(v["url"]), "w") as fh:
        json.dump(v, fh, ensure_ascii=False)


def collect_urls():
    """Every outbound link we publish, with the places that point at it."""
    by_url = {}
    for prov in ("cm", "cr"):
        path = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
        with open(path) as fh:
            for r in json.load(fh):
                a = r.get("attrs") or {}
                for field, raw in (("website", r.get("website")),
                                   ("brandWebsite", a.get("brandWebsite")),
                                   ("attrs.website", a.get("website"))):
                    u = normalize(raw)
                    if u:
                        by_url.setdefault(u, []).append({"id": r["id"], "field": field})
    return by_url


def main():
    args = sys.argv[1:]
    recheck = "--recheck" in args
    limit = None
    if "--max" in args:
        limit = int(args[args.index("--max") + 1])

    by_url = collect_urls()
    urls = sorted(by_url)
    print(f"🐜 {len(urls)} distinct outbound links from {sum(len(v) for v in by_url.values())} places")

    verdicts = {}
    todo = []
    for u in urls:
        hit = cached(u, recheck)
        if hit:
            verdicts[u] = hit
        else:
            todo.append(u)
    if limit:
        todo = todo[:limit]
    print(f"   {len(verdicts)} cached · {len(todo)} to check")

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(check, u): u for u in todo}
        for fut in concurrent.futures.as_completed(futures):
            u = futures[fut]
            try:
                v = fut.result()
            except Exception as e:
                v = {"url": u, "status": "error", "detail": str(e)[:200],
                     "checkedAt": date.today().isoformat()}
            verdicts[u] = v
            save(v)
            done += 1
            if done % 25 == 0:
                print(f"   …{done}/{len(todo)}")

    # Archived fallbacks, only for the links we would otherwise send people into.
    broken = [u for u, v in verdicts.items()
              if v.get("status") in ("tls", "dns", "down", "timeout", "gone", "http-error",
                                     "server-error", "parked", "empty")
              and "wayback" not in v]
    print(f"🕰  looking up {len(broken)} Wayback snapshots (gently)")
    for i, u in enumerate(broken, 1):
        verdicts[u]["wayback"] = wayback(u) or {}
        save(verdicts[u])
        time.sleep(0.6)
        if i % 25 == 0:
            print(f"   …{i}/{len(broken)}")

    payload = {
        "generated": date.today().isoformat(),
        "checker": UA,
        "links": verdicts,
        "places": {u: by_url[u] for u in verdicts if u in by_url},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=True)

    tally = {}
    for v in verdicts.values():
        tally[v.get("status", "?")] = tally.get(v.get("status", "?"), 0) + 1
    print("\n— verdicts —")
    for k in sorted(tally, key=lambda k: -tally[k]):
        print(f"{tally[k]:5}  {k}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
