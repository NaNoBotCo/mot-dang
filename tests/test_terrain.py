#!/usr/bin/env python3
"""build_terrain's writer, proven against map_ground's reader.

The elevation archive is written by hand in stdlib (importers/build_terrain.py)
and read in production by pmtiles.js; the only PMTiles reader on this machine
is map_ground's, and the two must agree on every byte of the format or the doi
page ships an archive that quietly never draws. So this test is the whole
contract in miniature: a synthetic archive of known tiles, written by the
writer, read back by the reader, byte for byte — plus the misses that must
stay misses and the header fields the clients steer by.

Fixtures only, no network, no Pillow, no real cache: the tiles here are a few
bytes wearing a PNG magic. Run: python3 tests/test_terrain.py
"""
import importlib.util
import shutil
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bt = _load("build_terrain", ROOT / "importers" / "build_terrain.py")
map_ground = _load("map_ground_t", ROOT / "map_ground.py")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="terrain-test-"))
    try:
        # A spread of zooms, none of them z12/0/0 (bind's own negative probe).
        tiles = [(0, 0, 0), (1, 1, 0), (5, 3, 7), (11, 1620, 940),
                 (12, 3160, 1830), (12, 3161, 1830)]
        bt.CACHE = tmp / "cache"
        for i, (z, x, y) in enumerate(tiles):
            p = bt._path(z, x, y)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([i]) * (20 + i * 7))

        out = tmp / "t.pmtiles"
        r = bt.bind(tiles, out)
        assert r["tiles"] == len(tiles), r

        arc = map_ground._Archive(out)
        assert arc.min_zoom == 0 and arc.max_zoom == bt.MAX_Z, (arc.min_zoom, arc.max_zoom)
        assert arc.tile_type == 2 and arc.clustered == 1
        assert arc.internal_compression == 2 and arc.tile_compression == 1
        for z, x, y in tiles:
            want = bt._path(z, x, y).read_bytes()
            got = arc.tile(z, x, y)
            assert got == want, "tile %d/%d/%d came back different" % (z, x, y)
        # The misses that must stay misses: same zoom, absent tile; and a
        # zoom outside the archive entirely.
        assert arc.tile(5, 3, 8) is None
        assert arc.tile(12, 0, 0) is None
        arc.close()

        # The parity gate's own inverse must really invert.
        for zxy in tiles + [(12, 3200, 1800), (9, 400, 230)]:
            tid = bt.zxy_to_tileid(*zxy)
            assert bt._tileid_to_zxy(tid) == zxy, zxy

        # The header the browser steers by: bounds hold the rails.
        h = out.open("rb").read(127)
        w, s, e, n = struct.unpack_from("<4i", h, 102)
        assert w / 1e7 <= bt.RAILS[0] and e / 1e7 >= bt.RAILS[2]
        assert s / 1e7 <= bt.RAILS[1] and n / 1e7 >= bt.RAILS[3]

        print("test_terrain: OK (%d tiles round-tripped, misses stayed misses)"
              % len(tiles))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
