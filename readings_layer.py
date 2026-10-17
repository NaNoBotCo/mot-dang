"""Readings of Thai-only names, for the maps: docs/data/readings/<cell>.json.

Nan, 2026-10-11: "All names should be transliterated on the english speaking map
pages if no english version exists." The place pages already print the RTGS
reading after a Thai-only name (build.name_roman, translit.py); the maps draw
their names from /api/v1/places and the shelves' geojson, which carry none, and
the API's keys are frozen at v1. So the readings travel beside it, cut into cells
of 0.02° (about 2 km) so a map fetches only the ground it shows:

    /data/readings/<floor(lat/0.02)>_<floor(lng/0.02)>.json   {record id: reading}

/readings.js (window.MDREAD, written here too) fetches the cells and answers by id. A reading is
never a name: it stays out of nameEn, slugs and the API.

    python3 readings_layer.py        writes docs/data/readings/ from data/canonical/
"""
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CELL = 0.02


def cell(lat, lng):
    return "%d_%d" % (math.floor(lat / CELL), math.floor(lng / CELL))


JS = r"""/* MDREAD: readings of Thai-only names, for maps in English (readings_layer.py, Nan 2026-10-11).
   MDREAD.want(list) fetches the cells under [{id, lat, lng}] and resolves when they are in;
   MDREAD.of(id) is the reading, or ''. A reading is how the Thai sounds (RTGS), not a name. */
(function () {
  if (window.MDREAD) return;
  var C = 0.02, BASE = (function () { try { return new URL('.', document.currentScript.src).href; } catch (e) { return '/'; } })();
  var by = {}, got = {}, wait = {};
  function key(la, ln) { return Math.floor(la / C) + '_' + Math.floor(ln / C); }
  function load(k) {
    if (got[k]) return Promise.resolve();
    if (wait[k]) return wait[k];
    return wait[k] = fetch(BASE + 'data/readings/' + k + '.json').then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; }).then(function (d) { for (var i in d) by[i] = d[i]; got[k] = 1; delete wait[k]; });
  }
  window.MDREAD = {
    want: function (list) {
      var ks = {}, n = 0;
      (list || []).forEach(function (o) { if (o && o.lat != null && o.lng != null && !isNaN(+o.lat)) ks[key(+o.lat, +o.lng)] = 1; });
      return Promise.all(Object.keys(ks).filter(function () { return ++n <= 40; }).map(load));
    },
    of: function (id) { return by[id] || ''; }
  };
})();
"""


def write(docs, records, roman):
    out = Path(docs) / "data" / "readings"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    by = defaultdict(dict)
    for r in records:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        rom = roman(r)
        if rom:
            by[cell(float(r["lat"]), float(r["lng"]))][r["id"]] = rom
    n = 0
    for k, v in by.items():
        (out / (k + ".json")).write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")))
        n += len(v)
    (Path(docs) / "readings.js").write_text(JS)
    return "%d readings in %d cells" % (n, len(by))


def emit(g, data):
    recs = [r for p in g["PROVINCES"] for r in data[p["key"]]]
    return write(g["DOCS"], recs, g["name_roman"])


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    import build
    recs = []
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / (prov + ".json")
        if p.exists():
            recs += json.loads(p.read_text())
    print(write(ROOT / "docs", recs, build.name_roman))
