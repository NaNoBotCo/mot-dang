#!/usr/bin/env python3
"""Event nets — the places that hold the same kind of evening, strung together.

A net (net_layer.py) is a set of places each of whose pages shows all the
others. These are drawn from the events a place has held or will hold
(build.py place_event_history, which reads the event ledger), sorted into
kinds by the words in the event titles: the jazz bar's page shows the city's
other music stages, the gallery the other galleries. Nan, 2026-10-04: every
event address "should be geocoded, linked, related, netted, and enriched".

Each kind is its own net, keyed `ev-<kind>`, with two strands — places with
something coming up, and places where it has been held before. A kind needs
NET_MIN places to become a net. A place joins on what its events are called,
so a title that names no kind joins nothing.

Entry point: nets(place_events, records, base) -> {key: net}, in nets.json's
shape, for net_layer.add().
"""
import re

NET_MIN = 3

# (kind, th, en, roman, words) — matched on whole words in the event title,
# lower-cased. A title can land in more than one kind.
KINDS = [
    ("music", "ตาข่ายดนตรีสด", "The live-music net", "ta-khai don-tri sot",
     r"jazz|live music|band|bands|concert|acoustic|orchestra|symphony|piano|guitar|singer|"
     r"open mic|open-mic|choir|ukulele|string|strings|recital|gig|blues|dj|music|musical"),
    ("stage", "ตาข่ายเวทีการแสดง", "The comedy-and-theatre net", "ta-khai we-thi kan sa-daeng",
     r"comedy|stand-up|standup|stand up|theatre|theater|drag|cabaret|improv|magic show|puppet"),
    ("film", "ตาข่ายฉายหนัง", "The film-night net", "ta-khai chai nang",
     r"film|films|movie|movies|cinema|screening"),
    ("art", "ตาข่ายศิลปะ", "The art-and-exhibition net", "ta-khai sin-la-pa",
     r"exhibition|exhibit|gallery|art|arts|painting|sketching|drawing|photography|ceramics|craft|crafts"),
    ("talk", "ตาข่ายวงคุย", "The talks-and-meetups net", "ta-khai wong khui",
     r"meetup|meet-up|talk|talks|discussion|networking|language exchange|book club|philosophy|"
     r"stoicism|lecture|seminar|conference|geeks|drinks|social|nomads|longtermers|questions"),
    ("move", "ตาข่ายโยคะและการเต้น", "The yoga-and-dance net", "ta-khai yo-kha lae kan ten",
     r"yoga|pilates|meditation|meditate|breathwork|dance|dancing|salsa|bachata|tango|zumba|"
     r"sound bath|qi gong|qigong|tai chi|kizomba|ecstatic|mindful"),
    ("sport", "ตาข่ายกีฬาและการวิ่ง", "The sport-and-running net", "ta-khai ki-la lae kan wing",
     r"run|running|runners|marathon|race|rugby|football|soccer|golf|disc golf|padel|hockey|"
     r"boxing|muay|cycling|bike|hike|hiking|trek|frisbee|volleyball|tennis|badminton|swim"),
    ("food", "ตาข่ายกินดื่ม", "The food-and-drink net", "ta-khai kin duem",
     r"brunch|buffet|dinner|wine|wines|tasting|beer|cocktail|cocktails|bbq|barbecue|"
     r"afternoon tea|happy hour|pizza|lunch|feast"),
    ("market", "ตาข่ายตลาดนัด", "The market net", "ta-khai ta-lat nat",
     r"market|markets|fair|bazaar|flea|kad|night market|weekend market"),
    ("learn", "ตาข่ายห้องเรียน", "The classes-and-courses net", "ta-khai hong rian",
     r"class|classes|course|courses|workshop|workshops|lesson|lessons|training|learn|learning"),
    ("games", "ตาข่ายเกม", "The games net", "ta-khai kem",
     r"board game|board games|boardgame|catan|dnd|d&d|gaming|gamers|games|scrabble|chess|"
     r"trivia|quiz|poker|mahjong|strategy"),
    ("kids", "ตาข่ายเด็กและครอบครัว", "The children-and-families net", "ta-khai dek lae khrop-khrua",
     r"kids|kid|children|child|family|families|toddler|toddlers"),
]
_RX = [(k, th, en, ro, re.compile(r"(?<![\w])(?:%s)(?![\w])" % w)) for k, th, en, ro, w in KINDS]

LEDE = {
    "th": "ที่ที่มี{what}ลงไว้ในมดแดง ทั้งงานที่กำลังจะมาและงานที่ผ่านมาแล้ว "
          "เปิดหน้าไหน ก็เห็นที่อื่นทั้งหมด",
    "en": "Places with {what} listed on Mot Dang, coming up and gone by. "
          "Open any one and you see all the others.",
}
WHAT = {
    "music": ("งานดนตรีสด", "live music"), "stage": ("ตลกและละคร", "comedy and theatre"),
    "film": ("ฉายหนัง", "film nights"), "art": ("นิทรรศการและศิลปะ", "art and exhibitions"),
    "talk": ("วงคุยและงานพบปะ", "talks and meetups"), "move": ("โยคะและการเต้น", "yoga and dance"),
    "sport": ("กีฬาและการวิ่ง", "sport and running"), "food": ("งานกินดื่ม", "food and drink evenings"),
    "market": ("ตลาดนัด", "markets"), "learn": ("ห้องเรียนและคอร์ส", "classes and courses"),
    "games": ("วงเกม", "game nights"), "kids": ("งานสำหรับเด็กและครอบครัว", "children's and family events"),
}
MONTH_TH = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.",
            "ต.ค.", "พ.ย.", "ธ.ค."]
MONTH_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def kinds_of(title):
    t = (title or "").lower()
    return [k for k, _th, _en, _ro, rx in _RX if rx.search(t)]


def _day(iso):
    try:
        y, m, d = (int(x) for x in iso[:10].split("-"))
    except ValueError:
        return "", ""
    return f"{d} {MONTH_TH[m]} {y + 543}", f"{d} {MONTH_EN[m]} {y}"


def nets(place_events, records, base):
    """{"ev-<kind>": net} for every kind NET_MIN or more places have held."""
    by_kind = {}
    for pid, h in place_events.items():
        if pid not in records:
            continue
        for e in h.get("next") or []:
            for k in kinds_of(e.get("title")):
                slot = by_kind.setdefault(k, {}).setdefault(pid, {"next": None, "past": None})
                if slot["next"] is None:
                    slot["next"] = e
        for x in h.get("past") or []:
            for k in kinds_of(x.get("title")):
                slot = by_kind.setdefault(k, {}).setdefault(pid, {"next": None, "past": None})
                if slot["past"] is None:
                    slot["past"] = x
    out = {}
    for k, th, en, roman, _rx in _RX:
        members = by_kind.get(k) or {}
        if len(members) < NET_MIN:
            continue
        coming, before = [], []
        for pid, s in members.items():
            if s["next"]:
                e = s["next"]
                dth, den = _day((e.get("start") or "")[:10])
                wd = e.get("weekday")
                if e.get("recurring") and wd is not None:
                    dth, den = "ทุกสัปดาห์", "weekly"
                coming.append({"id": pid, "th": f"{e.get('title', '')} · {dth}",
                               "en": f"{e.get('title', '')} · {den}",
                               "_s": (e.get("start") or "")})
            else:
                x = s["past"]
                dth, den = _day(x["gone"][-1])
                before.append({"id": pid, "th": f"{x.get('title', '')} · ครั้งล่าสุด {dth}",
                               "en": f"{x.get('title', '')} · last listed {den}",
                               "_s": x["gone"][-1]})
        coming.sort(key=lambda j: j.pop("_s"))
        before.sort(key=lambda j: j.pop("_s"), reverse=True)
        strands = []
        if coming:
            strands.append({"key": "coming", "th": "มีงานที่กำลังจะมา", "en": "Something coming up",
                            "roman": "", "jewels": coming})
        if before:
            strands.append({"key": "before", "th": "เคยมีงานที่นี่", "en": "Held here before",
                            "roman": "", "jewels": before})
        wth, wen = WHAT[k]
        out["ev-" + k] = {
            "th": th, "en": en, "roman": roman,
            "lede_th": LEDE["th"].format(what=wth), "lede_en": LEDE["en"].format(what=wen),
            "sources": [{"label": "มดแดง · งานในเมือง · Mot Dang events", "url": base + "events.html"}],
            "strands": strands, "generated": "event ledger",
        }
    return out
