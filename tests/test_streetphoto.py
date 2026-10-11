#!/usr/bin/env python3
"""WO-79 — street-level photographs. The licence and the date, asserted.

    python3 tests/test_streetphoto.py
    python3 -m unittest tests.test_streetphoto -v

Nothing here touches the network and nothing here needs MAPILLARY_TOKEN. The
JPEGs it needs, it builds — the same trick tests/test_exif_gps.py uses, and
for the same reason: a parser that returns a plausible answer for the wrong
reason is worse than one that returns nothing.

WHAT IS ASSERTED, AND WHY

  · NO READER EVER FETCHES FROM META. The display side must reference our own
    origin and nothing else; the importer must never hot-link a thumbnail,
    not even when a download fails. That privacy property is the whole reason
    this path exists rather than an <iframe> of Mapillary's viewer, and it is
    the kind of thing that gets quietly undone by a later "fallback".
  · ATTRIBUTION IS PRESENT. CC BY-SA 4.0 requires the photographer by name
    and a route back to the original. An image whose creator cannot be named
    is dropped, never credited to "Mapillary" — that would be a false
    attribution and a licence breach in the same line.
  · THE CAPTURE DATE IS ALWAYS SAID. Chiang Mai's coverage is old. A photo
    with no date must SAY it has no date; silence reads as recent.
  · GRACEFUL WITHOUT A TOKEN, AND WITHOUT A PHOTO. No token means a clear
    refusal and no request. No photo means no figure, and the page keeps
    whatever it draws today.
  · NO EMOJI in anything a reader sees.
"""

import os
import re
import struct
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import harvest_mapillary as H  # noqa: E402
import streetphoto_layer as S  # noqa: E402

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF\U0000FE0F\U0001F000-\U0001F02F]")


class _G(dict):
    def __init__(self):
        import html
        super().__init__(
            bi=lambda th, en: "%s · %s" % (th, en),
            bi_text=lambda th, en: "%s · %s" % (th, en),
            att=lambda s: html.escape(str(s), quote=True),
            esc=lambda s: html.escape(str(s)),
            name_th=lambda r: r.get("name", ""),
            name_en=lambda r: r.get("nameEn", ""),
        )


REC = {"id": "cm-test-1", "name": "ร้านทดสอบ", "nameEn": "Test Shop",
       "lat": 18.78800, "lng": 98.98700}

MLY = {"placeId": REC["id"], "file": "cm-test-1.jpg", "dir": "streetphotos",
       "own": False, "by": "somebody", "byUrl": "https://www.mapillary.com/app/user/somebody",
       "licence": "CC BY-SA 4.0",
       "licenceUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
       "source": "https://www.mapillary.com/app/?pKey=1", "sourceName": "Mapillary",
       "captured": "2024-03-02", "distanceM": 12.0}

OWN = {"placeId": REC["id"], "file": "own-1.jpg", "dir": "streetphotos/own",
       "own": True, "captured": "2026-08-01", "distanceM": 4.0,
       "by": None, "licence": None, "source": None}


# ── a JPEG with the EXIF we want to read, built by hand ──────────────────────

def jpeg_with(lat_dms=None, lat_ref="N", lng_dms=None, lng_ref="E",
              taken_str=None, denom=10000):
    """A minimal big-endian JPEG carrying an optional GPS IFD and an optional
    Exif sub-IFD with DateTimeOriginal. Laid out offset-first so the entries
    can point at real data."""
    want_gps = lat_dms is not None and lng_dms is not None
    want_date = taken_str is not None

    def rationals(dms):
        out = b""
        for v in dms:
            out += struct.pack(">II", int(round(v * denom)), denom)
        return out

    n0 = (1 if want_gps else 0) + (1 if want_date else 0)
    ifd0 = b"" + struct.pack(">H", n0)
    # IFD0 is 2 + 12n + 4 bytes, starting at offset 8.
    after_ifd0 = 8 + 2 + 12 * n0 + 4
    gps_at = after_ifd0
    gps_len = 2 + 12 * 4 + 4 if want_gps else 0
    lat_at = gps_at + gps_len
    lng_at = lat_at + 24
    exif_at = (lng_at + 24) if want_gps else after_ifd0
    date_at = exif_at + (2 + 12 * 1 + 4) if want_date else 0

    if want_gps:
        ifd0 += struct.pack(">HHI", 0x8825, 4, 1) + struct.pack(">I", gps_at)
    if want_date:
        ifd0 += struct.pack(">HHI", 0x8769, 4, 1) + struct.pack(">I", exif_at)
    ifd0 += struct.pack(">I", 0)

    body = b""
    if want_gps:
        g = struct.pack(">H", 4)
        g += struct.pack(">HHI", 1, 2, 2) + lat_ref.encode() + b"\x00\x00\x00"
        g += struct.pack(">HHI", 2, 5, 3) + struct.pack(">I", lat_at)
        g += struct.pack(">HHI", 3, 2, 2) + lng_ref.encode() + b"\x00\x00\x00"
        g += struct.pack(">HHI", 4, 5, 3) + struct.pack(">I", lng_at)
        g += struct.pack(">I", 0)
        body += g + rationals(lat_dms) + rationals(lng_dms)
    if want_date:
        s = (taken_str + "\x00").encode()
        e = struct.pack(">H", 1)
        e += struct.pack(">HHI", 0x9003, 2, len(s)) + struct.pack(">I", date_at)
        e += struct.pack(">I", 0)
        body += e + s

    tiff = b"MM\x00*" + struct.pack(">I", 8) + ifd0 + body
    payload = b"Exif\x00\x00" + tiff
    return (b"\xff\xd8\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
            + b"\xff\xd9")


class NoReaderEverTalksToMeta(unittest.TestCase):
    """The privacy property, asserted in both halves."""

    def test_the_figure_points_at_our_own_origin(self):
        g = _G()
        html = S.figure_html(REC, MLY, g, depth=2)
        m = re.search(r'<img[^>]+src="([^"]+)"', html)
        self.assertIsNotNone(m)
        src = m.group(1)
        self.assertTrue(src.startswith("../../streetphotos/"),
                        "the picture must come from our bucket, got %r" % src)
        for host in ("mapillary.com", "graph.mapillary", "fbcdn", "facebook",
                     "scontent", "http://", "https://"):
            self.assertNotIn(host, src,
                             "the img src reaches a third party: %r" % src)

    def test_the_only_outbound_links_are_the_licence_and_the_credit(self):
        """Links a reader must CHOOSE to follow are fine and are required by
        the licence. What is forbidden is a request the browser makes on its
        own — an img, a script, a stylesheet, a fetch."""
        html = S.figure_html(REC, MLY, _G(), depth=2)
        for href in re.findall(r'href="([^"]+)"', html):
            self.assertTrue(href.startswith("https://"), href)
        self.assertIn('rel="noopener nofollow', html)
        # nothing else may reach out
        self.assertEqual(re.findall(r'src="(https?://[^"]+)"', html), [])

    def test_the_sheet_script_fetches_only_our_own_json(self):
        js = S.JS
        urls = re.findall(r"fetch\((.*?)\)\.then", js)
        self.assertTrue(urls, "the sheet script fetches nothing at all")
        for u in urls:
            self.assertTrue(u.startswith("root()+"),
                            "the sheet must fetch relative to our own root, "
                            "got %r" % u)
            self.assertNotIn("//", u)
        self.assertNotIn("mapillary", js.lower())

    def test_the_importer_never_hot_links_as_a_fallback(self):
        """A download failure must mean NO photo. A fallback that pointed the
        page at thumb_1024_url would quietly undo the whole design."""
        src = (ROOT / "importers" / "harvest_mapillary.py").read_text()
        body = src.split("def harvest(")[1].split("\n# \u2500\u2500 self-test")[0]
        # the thumbnail URL may only ever be handed to download()
        for line in body.splitlines():
            if "thumb_1024_url" in line:
                self.assertIn("download(", line,
                              "thumb_1024_url used somewhere other than the "
                              "download: %r" % line.strip())

    def test_the_docstring_states_the_property(self):
        d = H.__doc__.lower()
        self.assertIn("no reader ever fetches anything from meta", d)
        self.assertIn("baked", d)


class Attribution(unittest.TestCase):
    """CC BY-SA 4.0 is a condition of use, not a courtesy."""

    def test_credit_names_photographer_licence_and_source(self):
        line = S.credit_line(MLY, _G())
        self.assertIn("somebody", line)
        self.assertIn("CC BY-SA 4.0", line)
        self.assertIn("Mapillary", line)
        self.assertIn("creativecommons.org/licenses/by-sa/4.0", line)

    def test_the_licence_link_is_marked_as_one(self):
        self.assertIn('rel="noopener nofollow license"', S.credit_line(MLY, _G()))

    def test_an_image_with_no_photographer_is_dropped_not_relabelled(self):
        img = {"id": "9", "creator": {}, "captured_at": 1700000000000,
               "thumb_1024_url": "https://x/9.jpg"}
        self.assertIsNone(H.credit_of(img),
                          "an unattributable image must be dropped, never "
                          "credited to the company")

    def test_an_image_with_no_id_is_dropped(self):
        img = {"creator": {"username": "a"}, "captured_at": 1700000000000}
        self.assertIsNone(H.credit_of(img))

    def test_the_figure_carries_the_credit(self):
        html = S.figure_html(REC, MLY, _G(), depth=2)
        self.assertIn("somebody", html)
        self.assertIn("CC BY-SA 4.0", html)

    def test_her_own_photo_carries_no_third_party_licence(self):
        line = S.credit_line(OWN, _G())
        self.assertIn("Our own photograph", line)
        for w in ("CC BY", "Mapillary", "mapillary.com"):
            self.assertNotIn(w, line)

    def test_the_importer_names_the_licence_it_is_using(self):
        self.assertEqual(H.LICENCE, "CC BY-SA 4.0")
        self.assertIn("creativecommons.org/licenses/by-sa/4.0", H.LICENCE_URL)


class TheDate(unittest.TestCase):
    """A stale photo presented as current is a false fact about a real place."""

    def test_a_known_date_is_printed(self):
        line = S.when_line({"captured": "2026-08-01"}, _G())
        self.assertIn("2569", line)      # BE
        self.assertIn("2026", line)      # and the Gregorian beside it

    def test_an_old_photo_says_the_street_may_have_changed(self):
        line = S.when_line({"captured": "2016-08-01"}, _G())
        self.assertIn("may have changed", line)
        self.assertIn("2559", line)

    def test_an_unknown_date_says_it_is_unknown(self):
        """Silence would read as recent."""
        line = S.when_line({"captured": None}, _G())
        self.assertIn("unknown", line.lower())
        self.assertIn("ไม่รู้ว่าถ่ายเมื่อไหร่", line)

    def test_the_figure_always_carries_a_date_line(self):
        for photo in (MLY, OWN, dict(MLY, captured=None)):
            html = S.figure_html(REC, photo, _G(), depth=2)
            self.assertIn("stcap", html)
            low = html.lower()
            self.assertTrue("taken in" in low or "unknown" in low,
                            "no date line: %r" % html)

    def test_unknown_counts_as_stale_on_both_sides(self):
        self.assertTrue(S.is_stale(None))
        self.assertTrue(H.is_stale(None))

    def test_epoch_milliseconds_not_seconds(self):
        """Mapillary gives captured_at in ms. Reading it as seconds would
        date every photograph to 1970."""
        self.assertEqual(H._when(1470009600000), "2016-08-01")
        self.assertEqual(H._when(0), None)
        self.assertEqual(H._when(None), None)
        self.assertEqual(H._when("not a number"), None)

    def test_the_sheet_caption_carries_the_year_and_the_warning(self):
        th, en = S._cap_pair(dict(MLY, captured="2016-05-05"))
        self.assertIn("2559", th)
        self.assertIn("may have changed", en)
        th2, en2 = S._cap_pair(dict(MLY, captured=None))
        self.assertIn("date unknown", en2)


class WithoutAToken(unittest.TestCase):
    def test_no_token_raises_and_says_whose_job_it_is(self):
        with self.assertRaises(H.NoToken) as cm:
            H.token({})
        msg = str(cm.exception)
        self.assertIn("MAPILLARY_TOKEN", msg)
        self.assertIn("Nan's to make", msg)
        self.assertIn("nothing was fetched", msg)

    def test_a_token_of_the_wrong_shape_is_not_sent(self):
        with self.assertRaises(H.NoToken):
            H.token({"MAPILLARY_TOKEN": "hunter2"})

    def test_the_token_never_goes_in_the_url(self):
        u = H.build_url((98.9, 18.7, 99.0, 18.8), 10)
        self.assertNotIn("access_token", u)
        self.assertNotIn("MLY", u)

    def test_the_token_goes_in_the_header(self):
        seen = {}

        class R:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b'{"data":[]}'

        def opener(req, timeout=None):
            seen["auth"] = req.get_header("Authorization")
            seen["url"] = req.full_url
            return R()

        H.fetch((98.9, 18.7, 99.0, 18.8), "MLY|x", opener=opener)
        self.assertEqual(seen["auth"], "OAuth MLY|x")
        self.assertNotIn("MLY", seen["url"])

    def test_the_tokenless_failure_is_read_correctly(self):
        """MEASURED 2026-09-08: it is a 500 carrying code 190, not a 401."""
        body = b'{"error":{"message":"Invalid OAuth 2.0 Access Token","code":190}}'
        msg = H._explain(body, 500)
        self.assertIn("token", msg.lower())
        self.assertIn("not 401", msg)

    def test_a_dry_run_needs_no_token_and_writes_nothing(self):
        before = H.INDEX.exists()
        out = H.harvest((98.9899, 18.7899, 98.9901, 18.7901), None,
                        dry_run=True, say=lambda *a: None)
        self.assertTrue(out["dry_run"])
        self.assertEqual(out["downloaded"], 0)
        self.assertEqual(H.INDEX.exists(), before,
                         "a dry run wrote the index")

    def test_the_self_test_passes_with_no_network(self):
        self.assertTrue(H.self_test(say=lambda *a: None))


class WithoutAPhoto(unittest.TestCase):
    def test_no_photo_means_no_figure(self):
        self.assertEqual(S.figure_html(REC, None, _G()), "")
        self.assertEqual(S.figure_html(REC, {}, _G()), "")
        self.assertEqual(S.figure_html(REC, {"by": "x"}, _G()), "",
                         "a record with a credit but no file must draw nothing")

    def test_no_index_files_means_an_empty_table_not_an_error(self):
        t = S.load(own_index=ROOT / "nope-own.json",
                   mly_index=ROOT / "nope-mly.json")
        self.assertEqual(t, {})

    def test_a_corrupt_index_does_not_stop_the_build(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text("{ this is not json")
            self.assertEqual(S.load(mly_index=p, own_index=p), {})

    def test_nothing_near_enough_returns_none(self):
        far = {"id": "1", "captured_at": 1700000000000,
               "geometry": {"type": "Point", "coordinates": [99.5, 19.5]},
               "thumb_1024_url": "https://x/1.jpg",
               "creator": {"username": "a"}}
        self.assertIsNone(H.pick([far], REC["lat"], REC["lng"]))
        self.assertIsNone(H.pick([], REC["lat"], REC["lng"]))


class HerOwnPhotos(unittest.TestCase):
    """The path that needs no token and no Meta."""

    def _folder(self, files):
        import tempfile
        d = Path(tempfile.mkdtemp())
        for name, blob in files.items():
            (d / name).write_bytes(blob)
        return d

    def test_a_geotagged_photo_matches_its_place(self):
        # Tha Phae Gate-ish, right on REC
        blob = jpeg_with((18, 47, 16.8), "N", (98, 59, 13.2), "E",
                         "2026:08:01 10:15:00")
        d = self._folder({"a.jpg": blob})
        idx, un = S.scan_own(d, [REC])
        self.assertIn(REC["id"], idx, "unmatched: %r" % un)
        self.assertTrue(idx[REC["id"]]["own"])
        self.assertEqual(idx[REC["id"]]["captured"], "2026-08-01")
        self.assertLess(idx[REC["id"]]["distanceM"], S.NEAR_M)

    def test_a_photo_with_no_gps_is_unmatched_never_guessed(self):
        d = self._folder({"a.jpg": jpeg_with(taken_str="2026:08:01 10:15:00")})
        idx, un = S.scan_own(d, [REC])
        self.assertEqual(idx, {})
        self.assertEqual(len(un), 1)
        self.assertIn("no GPS tag", un[0]["why"])
        self.assertIn("LINE", S.scan_own.__doc__)

    def test_a_photo_far_from_everything_is_unmatched(self):
        blob = jpeg_with((19, 30, 0), "N", (99, 30, 0), "E",
                         "2026:08:01 10:15:00")
        d = self._folder({"a.jpg": blob})
        idx, un = S.scan_own(d, [REC])
        self.assertEqual(idx, {})
        self.assertIn("within", un[0]["why"])

    def test_a_missing_folder_is_empty_not_an_error(self):
        idx, un = S.scan_own(ROOT / "no-such-folder", [REC])
        self.assertEqual((idx, un), ({}, []))

    def test_the_date_reader_never_guesses(self):
        self.assertIsNone(S.taken(b"not a jpeg"))
        self.assertIsNone(S.taken(jpeg_with((18, 0, 0), "N", (98, 0, 0), "E")))
        self.assertEqual(S._exif_date("2023:11:14 09:31:02"), "2023-11-14")
        self.assertIsNone(S._exif_date("0000:00:00 00:00:00"))
        self.assertIsNone(S._exif_date(""))
        self.assertIsNone(S._exif_date(None))

    def test_her_photo_beats_mapillary(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "m.json"
            o = Path(d) / "o.json"
            m.write_text(json.dumps({"photos": {REC["id"]: MLY}}))
            o.write_text(json.dumps({"photos": {REC["id"]: OWN}}))
            t = S.load(own_index=o, mly_index=m)
            self.assertTrue(t[REC["id"]]["own"],
                            "her own photograph must win: it owes nobody")
            self.assertEqual(t[REC["id"]]["file"], OWN["file"])


class WhatTheCaptionClaims(unittest.TestCase):
    def test_it_says_the_street_not_this_place(self):
        html = S.figure_html(REC, MLY, _G(), depth=2)
        self.assertIn("The street where this stands", html)
        self.assertNotIn("Photograph of Test Shop", html)

    def test_it_says_how_far_away_the_camera_was(self):
        html = S.figure_html(REC, dict(MLY, distanceM=22.0), _G(), depth=2)
        self.assertIn("22 m away", html)

    def test_the_alt_text_never_describes_the_frame(self):
        alt = S.alt_text(MLY, REC, _G())
        self.assertIn("street-level view", alt)
        self.assertIn("somebody", alt)
        self.assertIn("2024", alt)
        for invented in ("shopfront", "building", "sign", "road with"):
            self.assertNotIn(invented, alt.lower())


class TheTapSheet(unittest.TestCase):
    """Two things about MDCARD that a first draft got wrong silently."""

    def test_it_injects_the_image_rather_than_passing_an_ignored_key(self):
        """MDCARD.show() has no photo slot — an unknown key on its item is
        dropped without an error, so passing `opts.photo` would have done
        nothing at all, forever."""
        build = (ROOT / "build.py").read_text()
        card = build.split("const MDCARD=(()=>{")[1].split("window.MDCARD=MDCARD")[0]
        self.assertNotIn("item.photo", card,
                         "build.py grew a photo slot — this hook can be "
                         "simplified back to passing opts.photo")
        self.assertIn("createElement('img')", S.JS)
        self.assertIn("insertBefore", S.JS)

    def test_it_wraps_after_the_deferred_scripts(self):
        """tap.js REPLACES window.MDCARD after md.js defines it. Wrapping at
        parse time would wrap the card that gets thrown away."""
        self.assertIn("DOMContentLoaded", S.JS)
        self.assertIn("__stwrapped", S.JS)

    def test_a_reused_card_never_keeps_the_last_pins_photo(self):
        self.assertIn("if(old)old.remove()", S.JS.replace(" ", ""))
        self.assertIn("if(!id){draw(null);", S.JS.replace(" ", ""))

    def test_a_photographers_username_is_never_written_as_html(self):
        """A username is somebody else's text."""
        self.assertIn("cap.textContent=p.capLine", S.JS.replace(" ", ""))
        # The comments explain why innerHTML is not used, so check the code.
        code = re.sub(r"/\*.*?\*/", "", S.JS, flags=re.S)
        self.assertNotIn("innerHTML", code)


class NoEmoji(unittest.TestCase):
    def test_nothing_a_reader_sees_carries_emoji(self):
        g = _G()
        blobs = {
            "figure (mapillary)": S.figure_html(REC, MLY, g, depth=2),
            "figure (hers)": S.figure_html(REC, OWN, g, depth=2),
            "figure (no date)": S.figure_html(REC, dict(MLY, captured=None), g, 2),
            "credit": S.credit_line(MLY, g),
            "when": S.when_line(MLY, g),
            "alt": S.alt_text(MLY, REC, g),
            "sheet caption th": S._cap_pair(MLY)[0],
            "sheet caption en": S._cap_pair(MLY)[1],
            "css": S.CSS,
            "js": S.JS,
        }
        for name, blob in blobs.items():
            self.assertEqual(EMOJI.findall(blob), [],
                             "%s carries emoji: %r" % (name, EMOJI.findall(blob)))


class Picking(unittest.TestCase):
    def base(self, **kw):
        d = {"id": "1", "captured_at": 1700000000000,
             "geometry": {"type": "Point", "coordinates": [98.98700, 18.78800]},
             "thumb_1024_url": "https://x/1.jpg",
             "creator": {"username": "a"}}
        d.update(kw)
        return d

    def test_the_nearer_photo_wins(self):
        near = self.base(id="near")
        mid = self.base(id="mid",
                        geometry={"type": "Point",
                                  "coordinates": [98.98720, 18.78800]})
        self.assertEqual(H.pick([mid, near], 18.788, 98.987)["id"], "near")

    def test_a_panorama_loses_to_a_flat_frame(self):
        pano = self.base(id="pano", is_pano=True)
        flat = self.base(id="flat",
                         geometry={"type": "Point",
                                   "coordinates": [98.98715, 18.78800]})
        self.assertEqual(H.pick([pano, flat], 18.788, 98.987)["id"], "flat")

    def test_an_image_with_no_thumbnail_is_not_picked(self):
        no = self.base(id="no")
        no.pop("thumb_1024_url")
        self.assertIsNone(H.pick([no], 18.788, 98.987))

    def test_freshness_never_overrides_distance(self):
        """A fresh photo of the wrong building is still the wrong building."""
        old_near = self.base(id="old-near", captured_at=1300000000000)
        new_far = self.base(id="new-far",
                            captured_at=int(datetime.now(tz=timezone.utc)
                                            .timestamp() * 1000),
                            geometry={"type": "Point",
                                      "coordinates": [98.98725, 18.78800]})
        self.assertEqual(H.pick([new_far, old_near], 18.788, 98.987)["id"],
                         "old-near")


if __name__ == "__main__":
    print("token in environment: %s\n"
          % ("yes" if os.environ.get("MAPILLARY_TOKEN") else
             "no — and every test below runs without one"))
    unittest.main(verbosity=2)
