#!/usr/bin/env python3
"""Commons categories for subjects a geotag misses: festivals, dishes, peoples, crafts.

A lantern photographed at Yi Peng is rarely geotagged, and a bowl of khao soi
is not a place. These categories carry them, each with the tags a picture
drawn from it takes (the same four axes as data/curated/image_picks.json).

    python3 importers/harvest_commons_cats.py

Writes cache/commons_area/cats.json — {title: {meta…, "tags": {...}}}. Nothing
is downloaded here; importers/commons_pool.py chooses and fetches.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harvest_commons_area as H  # noqa: E402

OUT = H.CACHE / "cats.json"
PER_CAT = 120

# category → topic, mood, place, season ("" for none), depth (0 = files only, 1 = also subcats)
CATS = [
    ("Yi Peng", "festival,night", "festive", "cm", "cool", 1),
    ("Loi Krathong in Chiang Mai", "festival,night", "festive", "cm", "cool", 1),
    ("Loy Krathong in Chiang Mai", "festival,night", "festive", "cm", "cool", 1),
    ("Khom loi", "festival,night", "festive", "lanna", "cool", 0),
    ("Sky lanterns", "festival,night", "festive", "elsewhere", "cool", 0),
    ("Songkran in Chiang Mai", "festival", "festive", "cm", "hot", 1),
    ("Chiang Mai Flower Festival", "festival", "festive", "cm", "cool", 1),
    ("Bo Sang", "arts,craft", "streetlife", "cm", "", 1),
    ("Bo Sang Umbrella Festival", "festival,craft", "festive", "cm", "cool", 1),
    ("Paper umbrellas", "arts,craft", "festive", "elsewhere", "", 0),
    ("Khao soi", "food", "appetite", "lanna", "", 0),
    ("Sai ua", "food", "appetite", "lanna", "", 0),
    ("Nam phrik num", "food", "appetite", "lanna", "", 0),
    ("Khan tok", "food", "appetite", "lanna", "", 0),
    ("Cuisine of Northern Thailand", "food", "appetite", "lanna", "", 1),
    ("Sticky rice", "food", "appetite", "elsewhere", "", 0),
    ("Akha people", "hill,people", "calm", "lanna", "", 1),
    ("Hmong people in Thailand", "hill,people", "calm", "lanna", "", 1),
    ("Karen people in Thailand", "hill,people", "calm", "lanna", "", 1),
    ("Lahu people", "hill,people", "calm", "lanna", "", 0),
    ("Lisu people", "hill,people", "calm", "lanna", "", 0),
    ("Mien people", "hill,people", "calm", "lanna", "", 0),
    ("Poy Sang Long", "festival,people", "festive", "lanna", "hot", 1),
    ("Phu Chi Fa", "nature,view", "green,calm", "cr", "", 1),
    ("Doi Mae Salong", "nature,view", "green,calm", "cr", "", 1),
    ("Doi Tung", "nature,view", "green,calm", "cr", "", 1),
    ("Songthaews in Chiang Mai", "transport,city", "streetlife", "cm", "", 0),
    ("Wian tian", "faith,festival,night", "sacred", "elsewhere", "", 0),
    ("Tak bat", "faith,wat", "sacred", "elsewhere", "", 0),
    ("Alms giving in Thailand", "faith,wat", "sacred", "elsewhere", "", 0),
    ("Lanna architecture", "wat,arts,history", "sacred,landmark", "lanna", "", 1),
    ("Kalae", "arts,history", "calm", "lanna", "", 0),
    ("Tung (Lanna flag)", "faith,arts", "festive", "lanna", "", 0),
    ("Rice fields in Chiang Mai Province", "nature", "green", "cm", "", 1),
    ("Rice fields in Chiang Rai Province", "nature", "green", "cr", "", 1),
    ("Thai silk", "textile", "calm", "elsewhere", "", 0),
    ("Teen jok", "textile", "calm", "lanna", "", 0),
    ("Tin chok", "textile", "calm", "lanna", "", 0),
    ("Celadon from Thailand", "arts,craft", "calm", "lanna", "", 0),
    ("Lacquerware of Thailand", "arts,craft", "calm", "elsewhere", "", 0),
    ("Spirit houses in Chiang Mai", "faith,mu", "sacred", "cm", "", 0),
    ("Thai Buddha amulets", "mu,amulets", "sacred", "elsewhere", "", 0),
    ("Elephants in Chiang Mai Province", "animals", "green", "cm", "", 1),
    ("Muay Thai in Chiang Mai", "sport", "festive", "cm", "", 0),
    ("Haze in Thailand", "nature,city", "calm", "elsewhere", "hot", 0),
    ("Fog in Chiang Mai Province", "nature", "calm", "cm", "cool", 0),
    ("Mekong River in Chiang Rai Province", "nature,border", "calm", "cr", "", 1),
    ("Golden Triangle (Southeast Asia)", "border,nature", "landmark", "cr", "", 1),
    ("Wat Rong Khun", "wat,arts", "sacred,landmark", "cr", "", 1),
    ("Baan Dam Museum", "arts", "landmark", "cr", "", 1),
    # names as Commons spells them (category search, 2026-10-02)
    ("Sky lanterns in Thailand", "festival,night", "festive", "lanna", "cool", 1),
    ("Loi Krathong floats", "festival,night", "festive", "elsewhere", "cool", 0),
    ("Flower Festival Chiang Mai", "festival", "festive", "cm", "cool", 1),
    ("Akha people", "hill,people", "calm", "elsewhere", "", 0),
    ("Wat Rong Khun, Chiang Rai", "wat,arts", "sacred,landmark", "cr", "", 1),
    ("Black House Museum, Chiang Rai", "arts", "landmark", "cr", "", 1),
    ("Mekong Golden Triangle", "border,nature", "landmark", "cr", "", 1),
    ("Sop Ruak", "border", "landmark", "cr", "", 1),
    ("Mekong in Chiang Saen", "nature,border", "calm", "cr", "", 1),
    ("Buddhist amulets of Thailand", "mu,amulets", "sacred", "elsewhere", "", 1),
    ("Phra Somdet", "mu,amulets", "sacred", "elsewhere", "", 0),
    ("Mae Salong", "nature,view", "green,calm", "cr", "", 1),
    ("Santikhiri", "nature,view", "green,calm", "cr", "", 1),
    ("Tham bun khantok", "food,festival", "festive", "lanna", "", 0),
    ("Night Bazaar of Chiang Mai", "market,night", "streetlife", "cm", "", 1),
    ("Warorot market", "market", "streetlife", "cm", "", 1),
    ("Nimmanhemin Road", "city", "streetlife", "cm", "", 1),
    ("Views from Doi Inthanon", "nature,view", "green,landmark", "cm", "", 0),
    ("Doi Inthanon National Park", "nature", "green", "cm", "", 1),
    ("Doi Suthep-Pui National Park", "nature", "green", "cm", "", 1),
    ("Stairs to Wat Phra That Doi Suthep", "wat", "sacred,landmark", "cm", "", 0),
    ("Pai (Thailand)", "city,nature", "streetlife", "lanna", "", 1),
    ("Doi Chiang Dao", "nature,view", "green,landmark", "cm", "", 1),
    ("Wat Tham Chiang Dao", "wat,nature", "sacred", "cm", "", 1),
    ("Tung", "faith,arts", "festive", "lanna", "", 0),
    ("Mango sticky rice", "food", "appetite", "elsewhere", "", 0),
    ("Sticky rice in bamboo", "food", "appetite", "elsewhere", "", 0),
    ("Thai celadon", "arts,craft", "calm", "lanna", "", 0),
    ("Clock tower in Chiang Rai", "city", "landmark", "cr", "", 1),
    ("Old clock tower of Chiang Rai", "city,history", "landmark", "cr", "", 0),
    ("Wat Phra That Doi Kham", "wat", "sacred,landmark", "cm", "", 1),
    ("Nam ngiao", "food", "appetite", "lanna", "", 0),
    ("Nam phrik ong", "food", "appetite", "lanna", "", 0),
    ("Songkran in Thailand", "festival", "festive", "elsewhere", "hot", 0),
]


def members(cat, depth):
    titles, cats = [], ["Category:" + cat]
    seen = set()
    while cats and len(titles) < PER_CAT:
        c = cats.pop(0)
        if c in seen:
            continue
        seen.add(c)
        cont = {}
        while len(titles) < PER_CAT:
            d = H.api(dict({"action": "query", "list": "categorymembers", "cmtitle": c,
                            "cmtype": "file|subcat", "cmlimit": 200}, **cont))
            time.sleep(H.PAUSE)
            for m in d.get("query", {}).get("categorymembers", []):
                if m["ns"] == 6:
                    titles.append(m["title"])
                elif m["ns"] == 14 and depth > 0 and len(seen) < 12:
                    cats.append(m["title"])
            cont = d.get("continue") or {}
            if not cont:
                break
    return titles[:PER_CAT]


def main():
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name, topic, mood, place, season, depth in CATS:
        ts = members(name, depth)
        tags = {"topic": topic.split(","), "mood": mood.split(","), "place": place,
                "season": [season] if season else [], "cat": name}
        print(f"{name}: {len(ts)} files", flush=True)
        for t in ts:
            out.setdefault(t, {})["tags"] = out.get(t, {}).get("tags") or tags
    # metadata for all of them, through the area harvester's batch fetch
    todo = {t: {"lat": None, "lng": None} for t, v in out.items() if "licence" not in v}
    if todo:
        mp = H.CACHE / "cats_meta.json"
        H.meta(todo, out_path=mp)
        got = json.loads(mp.read_text())
        for t in todo:
            if t in got:
                out[t] = dict(got[t], tags=out[t]["tags"])
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print("cats.json:", len(out))


if __name__ == "__main__":
    main()
