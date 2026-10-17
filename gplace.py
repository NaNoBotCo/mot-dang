#!/usr/bin/env python3
"""gplace.py — Google place IDs: read one out of a Google Maps link, and say it back.

Nan, 2026-10-10: "Google Place IDs should be stored in records."

A Google place ID for a business or landmark ("ChIJ…") is the base64url of a
small protobuf holding the two halves of Google's feature ID, the
"0x30da3a…:0x8c5…" pair every long Google Maps link carries after `!1s`:

    0x0a 0x12 0x09 <high half, 8 bytes little-endian> 0x11 <low half, 8 bytes LE>

so a place ID can be written from a link alone, with no request to Google, and
read back into the feature ID and the CID (the low half as a decimal, the
`?cid=` of the oldest Google Maps links). Checked against Google's own example,
the Sydney Opera House: ChIJ3S-JXmauEmsRUcIaWtf4MzE ⇄
0x6b12ae665e892fdd:0x3133f8d75a1ac251, CID 3545450935484072529
(tests/test_gplace.py).

A short link (maps.app.goo.gl, goo.gl/maps, g.page) holds none of this until
it is opened; importers/google_ids.py --resolve opens those.

Place IDs of other shapes (an address or an area: "Ei…", "GhIJ…") are kept as
given when a link names them outright (query_place_id=, place_id:), and simply
have no feature ID to read back.
"""
import base64
import re
import struct
from urllib.parse import quote, unquote

_FTID = re.compile(r"(?:!1s|ftid=|[?&]q=)?(0x[0-9a-fA-F]{1,16}):(0x[0-9a-fA-F]{1,16})")
_PID_TAGGED = re.compile(r"(?:query_place_id=|place_id[:=]|placeid=)([0-9A-Za-z_\-]{16,})")
_PID_BARE = re.compile(r"(?<![0-9A-Za-z_\-])(ChIJ[0-9A-Za-z_\-]{20,})")
_CID = re.compile(r"[?&]cid=(\d{5,20})")
_SHORT = re.compile(r"https?://(?:maps\.app\.goo\.gl|goo\.gl/maps|g\.page|g\.co/kgs)/[^\s\"'<>]+", re.I)
_GOOGLE = re.compile(r"https?://(?:www\.)?(?:google\.[a-z.]+/maps|maps\.google\.[a-z.]+|maps\.app\.goo\.gl|goo\.gl/maps|g\.page|g\.co/kgs)[^\s\"'<>]*", re.I)


def from_ftid(hi, lo):
    """Feature-ID halves (ints or '0x…' strings) → 'ChIJ…'."""
    hi = int(hi, 16) if isinstance(hi, str) else int(hi)
    lo = int(lo, 16) if isinstance(lo, str) else int(lo)
    raw = b"\x0a\x12\x09" + struct.pack("<Q", hi) + b"\x11" + struct.pack("<Q", lo)
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def to_ftid(pid):
    """'ChIJ…' → (hi, lo) ints, or None for a place ID of another shape."""
    try:
        raw = base64.urlsafe_b64decode(pid + "=" * (-len(pid) % 4))
    except (ValueError, TypeError):
        return None
    if len(raw) < 20 or raw[:3] != b"\x0a\x12\x09" or raw[11] != 0x11:
        return None
    return struct.unpack("<Q", raw[3:11])[0], struct.unpack("<Q", raw[12:20])[0]


def cid_of(pid):
    f = to_ftid(pid or "")
    return str(f[1]) if f else None


def ftid_text(pid):
    f = to_ftid(pid or "")
    return "0x%x:0x%x" % f if f else None


def parse(text):
    """Any text — a long or short Google Maps link, a bare place ID — →
    {"placeId", "ftid", "cid", "short"} with what could be read, or None."""
    s = unquote(str(text or ""))
    out = {}
    m = _PID_TAGGED.search(s) or _PID_BARE.search(s)
    if m:
        out["placeId"] = m.group(1)
    if "placeId" not in out:
        f = _FTID.search(s)
        if f and int(f.group(1), 16) and int(f.group(2), 16):
            out["placeId"] = from_ftid(f.group(1), f.group(2))
    if out.get("placeId"):
        if to_ftid(out["placeId"]):
            out["ftid"] = ftid_text(out["placeId"])
            out["cid"] = cid_of(out["placeId"])
        return out
    c = _CID.search(s)
    if c:
        return {"cid": c.group(1)}
    sh = _SHORT.search(str(text or ""))
    if sh:
        return {"short": sh.group(0)}
    return None


def links_in(text):
    """Every Google Maps link in a blob of text."""
    return list(dict.fromkeys(_GOOGLE.findall(str(text or ""))))


def maps_url(pid, name=None):
    """The link that opens this exact Google listing."""
    q = quote(name or pid, safe="")
    return f"https://www.google.com/maps/search/?api=1&query={q}&query_place_id={quote(pid, safe='')}"


def valid(pid):
    return bool(pid) and bool(re.fullmatch(r"[0-9A-Za-z_\-]{16,}", pid))
