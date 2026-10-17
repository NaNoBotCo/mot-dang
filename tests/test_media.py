"""Pictures in their own bucket (media_layer.py, publish/media_sync.py, worker-media/).

    python3 tests/test_media.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "publish"))
sys.path.insert(0, str(ROOT / "tools"))
import media_layer  # noqa: E402
import media_sync  # noqa: E402
import safety  # noqa: E402
import deploy  # noqa: E402


class Bucket:
    """MD_MEDIA_BUCKET set for one test."""
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self.old = os.environ.get("MD_MEDIA_BUCKET")
        os.environ["MD_MEDIA_BUCKET"] = self.value
        media_layer._listed.clear()

    def __exit__(self, *a):
        if self.old is None:
            os.environ.pop("MD_MEDIA_BUCKET", None)
        else:
            os.environ["MD_MEDIA_BUCKET"] = self.old
        media_layer._listed.clear()


class TheBuild(unittest.TestCase):
    def test_off_it_copies_into_docs_as_before(self):
        with Bucket("0"), tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "a").mkdir()
            (d / "a" / "x.jpg").write_bytes(b"x")
            (d / "tree" / "n").mkdir(parents=True)
            (d / "tree" / "n" / "y.jpg").write_bytes(b"y")
            media_layer.put(d / "a" / "x.jpg", d / "docs", "photos/x.jpg")
            media_layer.put_tree(d / "tree", d / "docs", "photos/landmarks")
            self.assertEqual((d / "docs" / "photos" / "x.jpg").read_bytes(), b"x")
            self.assertEqual((d / "docs" / "photos" / "landmarks" / "n" / "y.jpg").read_bytes(), b"y")
            self.assertEqual(media_layer.flush(d / "m.txt"), 0)
            self.assertFalse((d / "m.txt").exists())

    def test_on_it_copies_nothing_and_lists(self):
        with Bucket("1"), tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "a").mkdir()
            (d / "a" / "x.jpg").write_bytes(b"x")
            (d / "tree" / "n").mkdir(parents=True)
            (d / "tree" / "n" / "y.jpg").write_bytes(b"y")
            media_layer.put(d / "a" / "x.jpg", d / "docs", "photos/x.jpg")
            media_layer.put_tree(d / "tree", d / "docs", "photos/landmarks")
            self.assertFalse((d / "docs").exists())
            self.assertEqual(media_layer.flush(d / "m.txt"), 2)
            self.assertEqual(media_layer.listed(d / "m.txt"),
                             {"photos/x.jpg", "photos/landmarks/n/y.jpg"})

    def test_a_gate_asking_for_a_card_finds_it_in_either_place(self):
        with Bucket("1"), tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "docs" / "og").mkdir(parents=True)
            (d / "docs" / "og" / "here.png").write_bytes(b"x")
            self.assertTrue(media_layer.in_build(d / "docs", "og/here.png"))
            self.assertFalse(media_layer.in_build(d / "docs", "og/gone.png"))
        with Bucket("0"), tempfile.TemporaryDirectory() as d:
            self.assertFalse(media_layer.in_build(Path(d), "og/listed.png"))


class ThePublish(unittest.TestCase):
    def test_the_site_sync_and_the_preview_leave_the_same_prefixes_alone(self):
        with Bucket("1"):
            ex = deploy.media_excludes()
            self.assertEqual(ex, [a for p in ("streetphotos/", "photos/", "inat/", "og/")
                                  for a in ("--exclude", "/" + p + "**")])
            self.assertEqual(safety.preview_excludes(),
                             ("tiles/", "streetphotos/", "photos/", "inat/", "og/"))
        with Bucket("0"):
            self.assertEqual(deploy.media_excludes(), [])
            self.assertEqual(safety.preview_excludes(), ("tiles/",))

    def test_the_preview_does_not_count_the_media_folders_as_missing(self):
        listed = ["index.html", "photos/a.jpg", "og/c.png", "inat/1.jpg", "streetphotos/s.jpg",
                  "listings/photos/p1/1.jpg", "old.html"]
        fake = lambda *a, **k: "\n".join(listed) + "\n"   # noqa: E731
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text("x")
            (Path(d) / "listings" / "photos" / "p1").mkdir(parents=True)
            (Path(d) / "listings" / "photos" / "p1" / "1.jpg").write_text("x")
            with Bucket("1"):
                gone, _ = safety.diff_preview("R2:b", {}, fake, root=d)
            self.assertEqual(gone, ["old.html"])
            with Bucket("0"):
                gone, _ = safety.diff_preview("R2:b", {}, fake, root=d)
            self.assertEqual(len(gone), 5)


class TheSync(unittest.TestCase):
    def test_what_the_bucket_needs(self):
        with tempfile.TemporaryDirectory() as d:
            old = media_sync.ASSETS
            media_sync.ASSETS = Path(d)
            try:
                (Path(d) / "photos").mkdir()
                for n, body in (("same", b"aaa"), ("bigger", b"bbbb"), ("new", b"c"),
                                ("redrawn", b"dd"), ("touched", b"ee")):
                    (Path(d) / "photos" / (n + ".jpg")).write_bytes(body)
                now = Path(d, "photos", "same.jpg").stat().st_mtime
                import hashlib
                md5 = lambda b: hashlib.md5(b).hexdigest()   # noqa: E731
                table = {
                    "photos/same.jpg": (3, now + 100, md5(b"aaa")),       # object newer than the file
                    "photos/bigger.jpg": (3, now + 100, md5(b"bbb")),     # another size
                    "photos/redrawn.jpg": (2, now - 100, md5(b"xx")),     # file newer, other content
                    "photos/touched.jpg": (2, now - 100, md5(b"ee")),     # file newer, same content
                }
                got = media_sync.wanted(["photos/same.jpg", "photos/bigger.jpg", "photos/new.jpg",
                                         "photos/redrawn.jpg", "photos/touched.jpg"], table)
                self.assertEqual(sorted(got), ["photos/bigger.jpg", "photos/new.jpg", "photos/redrawn.jpg"])
            finally:
                media_sync.ASSETS = old

    def test_the_list_keeps_to_the_four_prefixes_and_files_that_exist(self):
        with tempfile.TemporaryDirectory() as d:
            old = (media_sync.ASSETS, media_sync.MANIFEST)
            media_sync.ASSETS = Path(d)
            media_sync.MANIFEST = Path(d) / "m.txt"
            try:
                (Path(d) / "photos").mkdir()
                (Path(d) / "photos" / "a.jpg").write_bytes(b"x")
                (Path(d) / "sites").mkdir()
                (Path(d) / "sites" / "b.jpg").write_bytes(b"x")
                media_sync.MANIFEST.write_text("photos/a.jpg\nphotos/gone.jpg\nsites/b.jpg\nphotos/../sites/b.jpg\n")
                rels, gone = media_sync.listed()
                self.assertEqual((rels, gone), (["photos/a.jpg"], 1))
            finally:
                media_sync.ASSETS, media_sync.MANIFEST = old


if __name__ == "__main__":
    unittest.main(verbosity=1)
