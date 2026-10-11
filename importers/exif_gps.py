#!/usr/bin/env python3
"""Where a photo was taken, read out of its own bytes. Stdlib only.

    from exif_gps import gps
    gps(open("photo.jpg","rb").read())   -> (18.788, 98.985) or None

    python3 importers/exif_gps.py <file>...     # report each file

MEASURED 2026-09-07, and the reason this exists: LINE re-encodes anything sent
as a *photo* and throws the metadata away. The first picture through the ops
channel arrived with exactly one EXIF entry on it and no GPS tag at all. The
same picture sent through the paperclip, as a *file*, keeps its EXIF. So this
returns None for most of what arrives, and that is the honest answer rather
than a failure — a photo with no coordinates must never be given one.

No Pillow: this repo is stdlib, and a coordinate is worth reading correctly
rather than conveniently. Every branch below is exercised by test_exif_gps.py,
which builds a JPEG with known coordinates and reads them back.
"""
import struct
import sys

# TIFF field type -> (struct code, byte width)
TYPES = {1: ("B", 1), 2: ("s", 1), 3: ("H", 2), 4: ("I", 4), 5: ("II", 8),
         7: ("B", 1), 9: ("i", 4), 10: ("ii", 8)}


def _app1(jpeg):
    """The Exif APP1 segment's payload, walking the marker segments properly."""
    if jpeg[:2] != b"\xff\xd8":
        return None
    i = 2
    while i < len(jpeg) - 3:
        if jpeg[i] != 0xFF:
            return None
        marker = jpeg[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xDA:  # start of scan: no metadata past here
            return None
        length = struct.unpack(">H", jpeg[i + 2:i + 4])[0]
        seg = jpeg[i + 4:i + 2 + length]
        if marker == 0xE1 and seg[:6] == b"Exif\x00\x00":
            return seg[6:]
        i += 2 + length
    return None


def _entries(tiff, offset, bo):
    """The (tag, type, count, value-or-offset) rows of one IFD."""
    if offset + 2 > len(tiff):
        return []
    n = struct.unpack(bo + "H", tiff[offset:offset + 2])[0]
    out = []
    for k in range(n):
        e = offset + 2 + k * 12
        if e + 12 > len(tiff):
            break
        tag, typ, cnt = struct.unpack(bo + "HHI", tiff[e:e + 8])
        out.append((tag, typ, cnt, tiff[e + 8:e + 12]))
    return out


def _read(tiff, typ, cnt, raw, bo):
    if typ not in TYPES:
        return None
    code, width = TYPES[typ]
    size = width * cnt
    if size > 4:
        (off,) = struct.unpack(bo + "I", raw)
        data = tiff[off:off + size]
    else:
        data = raw[:size]
    if len(data) < size:
        return None
    if typ in (5, 10):  # rationals: numerator/denominator pairs
        vals = []
        for k in range(cnt):
            num, den = struct.unpack(bo + ("II" if typ == 5 else "ii"), data[k * 8:k * 8 + 8])
            vals.append(num / den if den else 0.0)
        return vals
    if typ == 2:
        return data.split(b"\x00")[0].decode("ascii", "replace")
    return list(struct.unpack(bo + code * cnt, data))


def _dms(vals):
    """Degrees, minutes, seconds -> decimal degrees."""
    if not vals:
        return None
    d = vals[0] if len(vals) > 0 else 0
    m = vals[1] if len(vals) > 1 else 0
    s = vals[2] if len(vals) > 2 else 0
    return d + m / 60 + s / 3600


def gps(jpeg_bytes):
    """(lat, lng) if the file carries coordinates, else None. Never guesses."""  # stylecheck: allow — code docstring
    tiff = _app1(jpeg_bytes)
    if not tiff or len(tiff) < 8:
        return None
    bo = ">" if tiff[:2] == b"MM" else "<" if tiff[:2] == b"II" else None
    if not bo:
        return None
    (ifd0,) = struct.unpack(bo + "I", tiff[4:8])

    gps_off = None
    for tag, typ, cnt, raw in _entries(tiff, ifd0, bo):
        if tag == 0x8825:
            v = _read(tiff, typ, cnt, raw, bo)
            gps_off = v[0] if v else None
    if not gps_off:
        return None

    lat = lng = None
    lat_ref = lng_ref = None
    for tag, typ, cnt, raw in _entries(tiff, gps_off, bo):
        v = _read(tiff, typ, cnt, raw, bo)
        if tag == 1:
            lat_ref = v
        elif tag == 2:
            lat = _dms(v)
        elif tag == 3:
            lng_ref = v
        elif tag == 4:
            lng = _dms(v)
    if lat is None or lng is None:
        return None
    if str(lat_ref).upper().startswith("S"):
        lat = -lat
    if str(lng_ref).upper().startswith("W"):
        lng = -lng
    # 0,0 is the Gulf of Guinea and, far more often, a camera that wrote the
    # tag without a fix. Nothing in Chiang Mai is there.
    if abs(lat) < 0.0001 and abs(lng) < 0.0001:
        return None
    return (round(lat, 6), round(lng, 6))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        try:
            print(f"{gps(open(path, 'rb').read()) or 'no coordinates'}  {path}")
        except OSError as e:
            print(f"unreadable: {path} ({e})")
