#!/usr/bin/env python3
"""สนามกีฬา — which game a sports place is for, read off its own words.

Nan, 2026-10-17, from the Pantip read (pantip-coverage/shelf-plan-2026-10-16.txt,
shelf 4 option a): "sport children for badminton, football, tennis, basketball,
snooker, bowling. Karaoke stays on bars." Pantip asks where the badminton courts,
futsal pitches and bowling alleys are; motdang held 180 CM and 54 CR of them on
sport/sport, a sub no shelf child reads, so they showed on no list.

This pass reads what a sport record already says — its name, the category its
directory gave it, OpenStreetMap's sport tag — and writes:

  sub              `sport` (or no sub) becomes one or more of badminton,
                   football, tennis, basketball, snooker, bowling. A complex
                   with pitches for two games lands on both.
  attrs.sportKinds ["badminton", ...] — the games read.
  attrs.sportVia   {game: "field: word"} — the word read.

A gym keeps its gym shelf and joins a game's shelf only when its own NAME names
the game ("Fitness & Badminton"); a directory category does not move a gym.
Muay Thai and golf are their own shelves and this pass leaves them alone.

Deterministic and idempotent; called from derive.PASSES, so it runs at the tail
of importers/import_all.py and with `python3 derive.py`.
"""
from __future__ import annotations

import re

SRC = "derived:sport-words"
KINDS = ("badminton", "football", "tennis", "basketball", "snooker", "bowling")

_L, _R = r"(?<![a-z])", r"(?![a-z])"
_NAME = {
    "badminton": re.compile(rf"แบดมินตัน|แบดมินตั้น|แบตมินตัน|สนาม\s*แบด|คอร์[ทด]\s*แบด|แบด\s*คอร์[ทด]|"
                            rf"{_L}badminton{_R}", re.I),
    "football": re.compile(rf"ฟุตบอล|ฟุตซอล|สนาม\s*หญ้าเทียม|สนาม\s*บอล|"
                           rf"{_L}(?:football|soccer|futsal){_R}", re.I),
    "tennis": re.compile(rf"เทนนิส|{_L}tennis{_R}", re.I),
    "basketball": re.compile(rf"บาสเก[็]?ตบอล|บาสเกตบอล|สนาม\s*บาส|{_L}basketball{_R}", re.I),
    "snooker": re.compile(rf"สนุ[๊]?[กค]เกอร์|สนุ๊ก|บิลเลียด|บิลเลี่ยด|"
                          rf"{_L}(?:snooker|billiards?|pool\s*(?:hall|club|bar|table)s?){_R}", re.I),
    "bowling": re.compile(rf"โบว์?ลิ่ง|{_L}bowling{_R}", re.I),
}
# Read out of the text before the tennis test: table tennis is another game.
_TABLE_TENNIS = re.compile(rf"เทเบิ[้ล]?ล?\s*เทนนิส|{_L}table\s*-?\s*tennis{_R}", re.I)

# A shop selling the gear is not a place to play. Read only when the name says
# nothing about a court, a club or a hall as well.
_GEAR = re.compile(rf"ร้านขาย|อุปกรณ์|จัดสวน|รับปู|ติดตั้ง|รับเหมา|{_L}(?:shop|store|equipment|gear){_R}", re.I)
_VENUE = re.compile(rf"สนาม|คอร์[ทด]|ศูนย์|สโมสร|ชมรม|คลับ|อารีน่า|{_L}(?:court|club|stadium|"
                    rf"hall|arena|center|centre|complex|field|pitch|academy){_R}", re.I)

# Overture's own categories (attrs.overtureCategory).
_DIR = {
    "badminton_court": "badminton",
    "soccer_field": "football", "football_stadium": "football",
    "soccer_stadium": "football", "futsal_field": "football",
    "tennis_court": "tennis", "tennis_stadium": "tennis",
    "basketball_court": "basketball", "basketball_stadium": "basketball",
    "pool_billiards": "snooker", "pool_hall": "snooker",
    "bowling_alley": "bowling",
}
# OpenStreetMap's sport=* values (attrs.sportTag, kept by import_overpass).
# Not bowls or boules: that is pétanque on a lawn, not a bowling alley.
_OSM = {
    "badminton": "badminton",
    "soccer": "football", "futsal": "football",
    "tennis": "tennis",
    "basketball": "basketball",
    "billiards": "snooker", "snooker": "snooker",
    "10pin": "bowling", "9pin": "bowling",
}

_FIELDS = ("name", "nameTh", "nameEn")
_LEAVE = {"muaythai", "golf"}


def osm_kinds(tags: dict) -> list:
    """Games named by an OSM element's own tags: sport=*, or a bowling alley."""
    got = []
    for v in str(tags.get("sport") or "").split(";"):
        k = _OSM.get(v.strip())
        if k and k not in got:
            got.append(k)
    if tags.get("leisure") == "bowling_alley" and "bowling" not in got:
        got.append("bowling")
    return got


def name_kinds(tags: dict) -> list:
    """Games named by an OSM element's own name, for a pitch whose sport tag
    is missing or misspelt ("tennisfee", a สนามแบตมินตัน with no tag)."""
    return list(_name_kinds({"name": tags.get("name"), "nameTh": tags.get("name:th"),
                             "nameEn": tags.get("name:en")}))


def _name_kinds(r) -> dict:
    texts = [(k, str(r.get(k))) for k in _FIELDS if r.get(k)]
    words = " ".join(t for _, t in texts)
    if _GEAR.search(words) and not _VENUE.search(words):
        return {}
    got = {}
    for kind, rx in _NAME.items():
        for k, t in texts:
            if kind == "tennis":
                t = _TABLE_TENNIS.sub(" ", t)
            m = rx.search(t)
            if m:
                got[kind] = f"{k}: {m.group(0).strip()}"
                break
    return got


def classify(r, gym=False) -> dict:
    """{game: reason} for a sport record. Empty when nothing on it names one."""
    got = _name_kinds(r)
    if gym:
        return got
    a = r.get("attrs") or {}
    for v in str(a.get("sportTag") or "").split(";"):
        k = _OSM.get(v.strip())
        if k and k not in got:
            got[k] = f"sportTag: {v.strip()} (OpenStreetMap)"
    cat = a.get("overtureCategory")
    k = _DIR.get(cat or "")
    if k and k not in got:
        got[k] = f"overtureCategory: {cat}"
    return got


def apply(records: list, prov: str, counts: dict | None = None, today: str = "") -> int:
    import provenance
    c = counts if counts is not None else {}
    written = 0

    def bump(k):
        c[k] = c.get(k, 0) + 1

    def receipt(r, field):
        if not any(provenance.source_key(s) == SRC for s in r.get("sources") or []):
            r.setdefault("sources", []).append(
                {"type": "derived", "via": "sport-words", "fetched": today})
        if field in provenance.TRACKED:
            provenance.stamp(r, field, SRC, provenance.DERIVED, today)

    for r in records:
        cats = r.get("cat") or []
        if "sport" not in cats or set(cats) & _LEAVE:
            continue
        subs = list(r.get("sub") or [])
        if set(subs) & _LEAVE:
            continue
        gym = "gym" in subs
        if gym or not subs or "sport" in subs or set(subs) & set(KINDS):
            got = classify(r, gym=gym)
        else:
            continue
        if not got:
            continue
        new_subs = [s for s in subs if s != "sport"]
        for k in KINDS:
            if k in got and k not in new_subs:
                new_subs.append(k)
        if new_subs != subs:
            r["sub"] = new_subs
            receipt(r, "sub")
        attrs = r.setdefault("attrs", {})
        kinds = [k for k in KINDS if k in got]
        if attrs.get("sportKinds") != kinds:
            attrs["sportKinds"] = kinds
            attrs["sportVia"] = {k: got[k] for k in kinds}
            receipt(r, "sportKinds")
            written += 1
        for k in kinds:
            bump(f"sportKind/{k}")
    return written
