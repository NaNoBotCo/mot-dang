#!/usr/bin/env python3
"""fburl.py — one place that turns a Facebook value into a usable URL, or refuses.

OSM's contact:facebook is a free-text field and it shows. Of the 232 values in
the catalogue on 2026-09-06, 134 were clean URLs, 57 were valid bare handles,
26 carried share/tracking junk, and 15 built a BROKEN link when pasted onto
"https://www.facebook.com/": four had a scheme-less URL in them (that produced
.../www.facebook.com/ThaiDress, a 404 shipped on a live page), two were
percent-encoded page slugs the old charset rejected, and nine were the page's
NAME with spaces or Thai or Japanese in it — not a handle at all.

A name is not a URL and must not be guessed into one: searching Facebook for
"Audition music & art room" and linking the first hit is how this directory
would point a reader at the wrong shop. Those return None and the caller shows
no Facebook link, which is the honest outcome — the value stays in the record
as the lead it is.

Shared by build.py (rendering) and importers/discover_facebook.py (matching),
so the two can never disagree about which page a value names.
"""
import re
import urllib.parse

_FB_HANDLE = re.compile(r"^[A-Za-z0-9.\-_%]{3,}$")
_FB_JUNK = ("rdid", "share_url", "mibextid", "fbclid", "__cft__", "__tn__",
            "locale", "ref", "_rdr", "mibextid")
_FB_HOST = re.compile(r"^(?:www\.|m\.|web\.|mbasic\.|th-th\.|en-gb\.)?(?:facebook|fb)\.(?:com|me)/", re.I)


def fb_url_of(fb):
    """A usable https URL for a Facebook value, or None if it is a name.

    Never invents: a value that is not already a URL and not a legal handle is
    not searched for, not slugified and not linked.
    """
    if not fb:
        return None
    fb = str(fb).strip().strip("/")
    if not fb:
        return None
    if fb.startswith("//"):
        fb = "https:" + fb
    # A URL with no scheme has no netloc — the enrich_sites.py lesson, which
    # never reached the render path. "www.facebook.com/x" pasted onto the
    # prefix is a 404, so give it its scheme instead.
    if not fb.startswith("http") and _FB_HOST.match(fb):
        fb = "https://" + fb
    if fb.startswith("http"):
        u = urllib.parse.urlsplit(fb)
        host = u.netloc.lower()
        if not re.search(r"(?:^|\.)(?:facebook\.com|fb\.com|fb\.me)$", host):
            return None
        q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query)
             if k.lower() not in _FB_JUNK]
        # profile.php?id= is the whole address for a page with no vanity name;
        # everything else in the query is somebody's share tracking. http is
        # upgraded because Facebook redirects it anyway and a mixed-content
        # link on an https page is a link some browsers will not follow.
        return urllib.parse.urlunsplit(
            ("https", "www.facebook.com" if host.endswith("facebook.com") else host,
             u.path.rstrip("/"), urllib.parse.urlencode(q), ""))
    return "https://www.facebook.com/" + fb if _FB_HANDLE.match(fb) else None


def fb_key(url):
    """The identity of a page for matching: 'profile:<id>' or the lower-cased
    vanity path, with /p/Name-<id>/ and /people/Name/<id>/ forms reduced to the
    numeric id they carry. Two URLs with the same key are the same page."""
    u = fb_url_of(url)
    if not u:
        return None
    s = urllib.parse.urlsplit(u)
    path = s.path.strip("/")
    q = dict(urllib.parse.parse_qsl(s.query))
    if path == "profile.php" and q.get("id"):
        return "profile:" + q["id"]
    parts = path.split("/")
    if parts and parts[0] in ("p", "people", "pages") and parts[-1].isdigit():
        return "profile:" + parts[-1]
    m = re.search(r"-(\d{6,})$", parts[-1] if parts else "")
    if parts and parts[0] in ("p", "pages") and m:
        return "profile:" + m.group(1)
    return parts[0].lower() if parts else None
