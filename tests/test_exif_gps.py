#!/usr/bin/env python3
"""The coordinate reader, checked against bytes whose answer we already know.

A parser that returns a plausible-looking number for the wrong reason is worse
than one that returns nothing: a wrong pin puts a real shop on the wrong soi
and nobody notices. So this builds JPEGs with coordinates chosen by hand and
reads them back, both hemispheres, and checks that everything without
coordinates comes back None rather than something.
"""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "importers"))
from exif_gps import gps  # noqa: E402


def build(lat_dms, lat_ref, lng_dms, lng_ref, denom=10000):
    """A minimal big-endian JPEG carrying exactly one GPS IFD."""
    def rationals(dms):
        out = b""
        for v in dms:
            out += struct.pack(">II", int(round(v * denom)), denom)
        return out

    # Offsets are laid out first so the entries can point at them.
    gps_ifd = 26
    lat_at, lng_at = 80, 104

    tiff = b"MM\x00*" + struct.pack(">I", 8)
    tiff += struct.pack(">H", 1)                                    # IFD0: one entry
    tiff += struct.pack(">HHI", 0x8825, 4, 1) + struct.pack(">I", gps_ifd)
    tiff += struct.pack(">I", 0)                                    # no IFD1
    tiff += struct.pack(">H", 4)                                    # GPS IFD: four entries
    tiff += struct.pack(">HHI", 1, 2, 2) + lat_ref.encode() + b"\x00\x00\x00"
    tiff += struct.pack(">HHI", 2, 5, 3) + struct.pack(">I", lat_at)
    tiff += struct.pack(">HHI", 3, 2, 2) + lng_ref.encode() + b"\x00\x00\x00"
    tiff += struct.pack(">HHI", 4, 5, 3) + struct.pack(">I", lng_at)
    tiff += struct.pack(">I", 0)
    assert len(tiff) == lat_at, f"layout drifted: {len(tiff)} != {lat_at}"
    tiff += rationals(lat_dms) + rationals(lng_dms)

    payload = b"Exif\x00\x00" + tiff
    return (b"\xff\xd8" + b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
            + b"\xff\xd9")


class ReadsCoordinates(unittest.TestCase):
    def test_reads_a_chiang_mai_pin(self):
        # Tha Phae Gate, near enough: 18°47'15.56"N 98°59'35.26"E
        got = gps(build((18, 47, 15.5604), "N", (98, 59, 35.2608), "E"))
        self.assertIsNotNone(got)
        lat, lng = got
        self.assertAlmostEqual(lat, 18 + 47 / 60 + 15.5604 / 3600, places=5)
        self.assertAlmostEqual(lng, 98 + 59 / 60 + 35.2608 / 3600, places=5)

    def test_southern_and_western_hemispheres_go_negative(self):
        lat, lng = gps(build((33, 51, 54.0), "S", (151, 12, 36.0), "W"))
        self.assertLess(lat, 0)
        self.assertLess(lng, 0)
        self.assertAlmostEqual(lat, -(33 + 51 / 60 + 54 / 3600), places=5)


class RefusesToGuess(unittest.TestCase):
    def test_no_exif_at_all(self):
        self.assertIsNone(gps(b"\xff\xd8\xff\xd9"))

    def test_not_a_jpeg(self):
        self.assertIsNone(gps(b"this is not an image"))
        self.assertIsNone(gps(b""))

    def test_null_island_is_a_camera_with_no_fix(self):
        self.assertIsNone(gps(build((0, 0, 0), "N", (0, 0, 0), "E")))

    def test_truncated_file_never_raises(self):
        # Half a photo is a thing that happens. It may not take the process down.
        whole = build((18, 47, 15.5604), "N", (98, 59, 35.2608), "E")
        for cut in range(1, len(whole)):
            gps(whole[:cut])

    def test_the_shape_line_leaves_behind(self):
        # What a picture sent as a *photo* actually looks like coming out of
        # LINE, measured 2026-09-07: an Exif block survives, but IFD0 holds a
        # single entry — a pointer to the Exif sub-IFD — and there is no GPS
        # tag anywhere. Built here rather than shipping the original photo.
        tiff = (b"MM\x00*" + struct.pack(">I", 8) + struct.pack(">H", 1)
                + struct.pack(">HHI", 0x8769, 4, 1) + struct.pack(">I", 26)
                + struct.pack(">I", 0) + struct.pack(">H", 0) + struct.pack(">I", 0))
        payload = b"Exif\x00\x00" + tiff
        jpeg = b"\xff\xd8\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload + b"\xff\xd9"
        self.assertIsNone(gps(jpeg))


if __name__ == "__main__":
    unittest.main(verbosity=2)
