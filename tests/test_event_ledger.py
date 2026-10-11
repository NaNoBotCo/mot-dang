#!/usr/bin/env python3
"""Events stay on their place after their day: the ledger, the history, the nets.

Nan, 2026-10-04: "Prior events and future events should add to a place's
richness and placement in our internal search results." Four things carry
that, and each is checked here on made-up rows, not the live data:

  1. importers/event_ledger.fold keeps every date it is shown and a weekly
     series as one row, and a second sighting never drops a field;
  2. build.place_event_history puts a past event on its place, rides a live
     series' history on the live row (also when the title was worded
     differently), and folds one title on several days into one line;
  3. build.whats_on_here links each coming event to its card on events.html
     and lists what was held before;
  4. event_nets_layer sorts titles into kinds on whole words.

    python3 tests/test_event_ledger.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


def ev(uid, title, start, venue="", recurring=False, weekday=None, **kw):
    return dict(uid=uid, title=title, start=start, venue_name=venue, recurring=recurring,
                weekday=weekday, source="steve-newsletter", url=None, cost=None, end=None, **kw)


def test_fold():
    import event_ledger
    doc = {"events": {}}
    event_ledger.fold(doc, [ev("a1", "Jazz night", "2026-08-07 20:00:00", "Blue Bar", True, 4),
                            ev("a2", "Jazz night", "2026-08-14 20:00:00", "Blue Bar", True, 4),
                            ev("b", "Book launch", "2026-08-09 18:00:00", "")], "2026-08-05")
    event_ledger.fold(doc, [ev("a3", "Jazz night", "2026-08-21 20:00:00", "", True, 4),
                            ev("b", "Book launch", "2026-08-09 18:00:00", "Shop")], "2026-08-20")
    led = doc["events"]
    check("a weekly series is one row", len([k for k in led if k.startswith("w:")]) == 1, list(led))
    s = led["w:jazz night:4"]
    check("its dates gather across sightings", s["dates"] == ["2026-08-07", "2026-08-14", "2026-08-21"], s["dates"])
    check("a later sighting without a venue keeps the venue", s["venue_name"] == "Blue Bar")
    check("a later sighting fills a venue that was missing", led["b"]["venue_name"] == "Shop")
    check("first_seen and last_seen", (s["first_seen"], s["last_seen"]) == ("2026-08-05", "2026-08-20"))


def test_history():
    import build
    rec = {"id": "cm-x-blue", "name": "Blue Bar", "nameEn": "Blue Bar", "nameTh": None,
           "province": "cm", "cat": ["food"], "lat": 18.79, "lng": 98.99}
    data = {p["key"]: [] for p in build.PROVINCES}
    data["cm"] = [rec]
    live = dict(ev("l1", "Jazz night", build.BUILD_DATE + " 20:00:00", "Blue Bar", True, 4),
                place={"id": "cm-x-blue"}, dt=None)
    build.EVENT_LEDGER = {
        "w:jazz night at blue bar:4": {"title": "Jazz Night at Blue Bar", "venue_name": "Blue Bar",
                                        "recurring": True, "weekday": 4, "sources": [],
                                        "dates": ["2026-08-07", "2026-08-14"]},
        "d1": {"title": "Wine tasting", "venue_name": "Blue Bar", "recurring": False, "weekday": None,
               "sources": [], "dates": ["2026-08-02"], "url": None},
        "d2": {"title": "Wine tasting", "venue_name": "Blue Bar", "recurring": False, "weekday": None,
               "sources": [], "dates": ["2026-09-06"], "url": None},
        "d3": {"title": "Elsewhere", "venue_name": "Nowhere Known", "recurring": False,
               "weekday": None, "sources": [], "dates": ["2026-08-02"]},
    }
    h = build.place_event_history(data, [live]).get("cm-x-blue") or {}
    check("the live series carries its history (reworded title)", live.get("since") == "2026-08-07", live.get("since"))
    check("one title on two days is one past line",
          [(x["title"], x["gone"]) for x in h.get("past", [])] == [("Wine tasting", ["2026-08-02", "2026-09-06"])],
          h.get("past"))
    check("n counts distinct events", h.get("n") == 2, h.get("n"))
    check("an unknown venue joins nothing", set(build.place_event_history(data, [])) == {"cm-x-blue"})
    build.PLACE_EVENTS = {"cm-x-blue": h}
    html = build.whats_on_here("cm-x-blue", [live])
    check("the coming event links to its card", 'href="../../events.html#ev-jazz-night"' in html, html[:300])
    check("what was held before is listed", "Wine tasting" in html and "evpast" in html)


def test_kinds():
    import event_nets_layer as k
    check("jazz is music", "music" in k.kinds_of("Thursday Jazz Jam"))
    check("smart is not art", "art" not in k.kinds_of("Smart contracts"))
    check("marketing is not a market", "market" not in k.kinds_of("Marketing for founders"))
    check("a title can be two kinds", {"food", "music"} <= set(k.kinds_of("Wine dinner with live music")))


if __name__ == "__main__":
    test_fold()
    test_history()
    test_kinds()
    print(f"\n{'FAILED: ' + ', '.join(failures) if failures else 'all passed'}")
    sys.exit(1 if failures else 0)
