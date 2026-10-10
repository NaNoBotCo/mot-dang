"""importers/event_links.py — the ladder, offline: a stand-in replaces check_links.check.

    python3 tests/test_event_links.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
sys.path.insert(0, ROOT)
import event_links as L  # noqa: E402

fails = []


def ok(cond, what):
    print(("  ok    " if cond else "  FAIL  ") + what)
    if not cond:
        fails.append(what)


# series keys: the same weekly night under the words a source adds
k = L.series_key("Salsa for beginners", "Bailamos Dance Studio")
ok(k == L.series_key("Salsa for Beginners (every Tuesday)", "Bailamos Dance Studio"), "a series key ignores '(every Tuesday)'")
ok(k != L.series_key("Salsa for beginners", "Travelodge Nimman"), "the same title at another venue is another series")

# the page test
ok(L.names_it("weekly salsa for beginners at bailamos", "Salsa for beginners", "Bailamos Dance Studio") != "", "a page with the title's words names it")
ok(L.names_it("bailamos dance studio · classes", "Kizomba night", "Bailamos Dance Studio") == "names the venue", "a page with the venue's name names it")
ok(L.names_it("a hotel homepage about rooms", "Sunday family brunch", "Shangri-La Chiang Mai") == "", "a page naming neither is refused")

# the ladder, with every network call replaced
VERDICT = {"https://dead.example/": "gone", "https://live.example/": "ok", "https://series.example/": "ok",
           "https://venue.example/": "ok", "https://fb.example/": "social", "https://slow.example/": "timeout"}
L.check_links.check = lambda u: {"url": u, "status": VERDICT.get(u, "gone"), "checkedAt": "2026-10-10"}
tmp = tempfile.mkdtemp()
L.CHECKS, L.OUT, L.TODO = os.path.join(tmp, "c.json"), os.path.join(tmp, "o.json"), os.path.join(tmp, "todo.tsv")
L.SERIES = os.path.join(tmp, "s.json")
with open(L.SERIES, "w") as fh:
    json.dump({"series": {L.series_key("B", "V"): {"url": "https://series.example/"}}}, fh)
rows = [
    {"uid": "a", "title": "A", "venue_name": "V", "start": "2026-10-12 19:00:00", "url": "https://live.example/"},
    {"uid": "b", "title": "B", "venue_name": "V", "start": "2026-10-12 19:00:00", "url": "https://dead.example/"},
    {"uid": "c", "title": "C", "venue_name": "V", "start": "2026-10-12 19:00:00", "url": ""},
    {"uid": "d", "title": "D", "venue_name": "W", "start": "2026-10-12 19:00:00", "url": "https://dead.example/"},
    {"uid": "e", "title": "E", "venue_name": "W", "start": "2026-10-12 19:00:00", "url": "https://fb.example/"},
]
L.upcoming = lambda: rows
L.venue_sites = lambda rs: {"c": "https://venue.example/"}
tally, todo = L.resolve()
out = json.load(open(L.OUT))["links"]
ok(out["a"]["rung"] == "event", "a live source link is kept")
ok(out["b"]["rung"] == "series" and out["b"]["url"] == "https://series.example/", "a dead source link falls to the series' link")
ok(out["c"]["rung"] == "venue" and out["c"]["kind"] == "host", "no link and no series: the venue's site, as the host's")
ok("d" not in out, "dead link, no series, no venue site: none")
ok(out["e"]["status"] == "social", "a social page is shown")
ok(sorted(json.load(open(L.OUT))["judged"]) == ["a", "b", "c", "d", "e"], "every event the run saw is listed as judged")
ok(todo == 2, "the todo lists the venue-only and the linkless series")

# a link that only timed out keeps its last good verdict
json.dump({"https://slow.example/": {"status": "ok", "checkedAt": "2000-01-01"}}, open(L.CHECKS, "w"))
rows[:] = [{"uid": "f", "title": "F", "venue_name": "V", "start": "2026-10-12 19:00:00", "url": "https://slow.example/"}]
L.resolve()
ok(json.load(open(L.OUT))["links"].get("f", {}).get("rung") == "event", "a timeout does not unlink a link that answered before")

print("\nall passed" if not fails else "\n%d failed" % len(fails))
sys.exit(1 if fails else 0)
