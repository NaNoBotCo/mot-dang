#!/usr/bin/env python3
"""Bake the weather widget's data for a fixed set of cities.

Same shape as make_finance.py and make_ticker.py: fetched once here, written to
data/weather.json, read by build.py. Published pages make no external request,
so the reader picks which of these cities to show and the answer is already in
the page — nothing is called at page-load time.

That is why the city list is baked rather than free-text: a search box would
mean a live API call from the browser, which this site does not do. Fifteen
cities cover both provinces, the rest of Thailand people travel to, and the
places readers keep a clock on.

    python3 importers/make_weather.py

Source: Open-Meteo — free, keyless, no attribution requirement, and it takes
every coordinate in one request.
"""
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import ingest      # shared write discipline (WO-41 Phase 2)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "weather.json"
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; daily weather snapshot)"

# (id, Thai name, English name, lat, lng, IANA timezone)
CITIES = [
    ("chiang-mai", "เชียงใหม่", "Chiang Mai", 18.7883, 98.9853, "Asia/Bangkok"),
    ("chiang-rai", "เชียงราย", "Chiang Rai", 19.9105, 99.8406, "Asia/Bangkok"),
    ("pai", "ปาย", "Pai", 19.3583, 98.4392, "Asia/Bangkok"),
    ("mae-hong-son", "แม่ฮ่องสอน", "Mae Hong Son", 19.3020, 97.9654, "Asia/Bangkok"),
    ("lampang", "ลำปาง", "Lampang", 18.2888, 99.4909, "Asia/Bangkok"),
    ("bangkok", "กรุงเทพฯ", "Bangkok", 13.7563, 100.5018, "Asia/Bangkok"),
    ("phuket", "ภูเก็ต", "Phuket", 7.8804, 98.3923, "Asia/Bangkok"),
    ("udon-thani", "อุดรธานี", "Udon Thani", 17.4138, 102.7870, "Asia/Bangkok"),
    ("singapore", "สิงคโปร์", "Singapore", 1.3521, 103.8198, "Asia/Singapore"),
    ("tokyo", "โตเกียว", "Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    ("london", "ลอนดอน", "London", 51.5072, -0.1276, "Europe/London"),
    ("berlin", "เบอร์ลิน", "Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    ("new-york", "นิวยอร์ก", "New York", 40.7128, -74.0060, "America/New_York"),
    ("los-angeles", "ลอสแอนเจลิส", "Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    ("sydney", "ซิดนีย์", "Sydney", -33.8688, 151.2093, "Australia/Sydney"),
]


def main():
    qs = urllib.parse.urlencode({
        "latitude": ",".join(str(c[3]) for c in CITIES),
        "longitude": ",".join(str(c[4]) for c in CITIES),
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "auto",
        "forecast_days": "4",
    })
    url = "https://api.open-meteo.com/v1/forecast?" + qs
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if isinstance(payload, dict):        # a single coordinate comes back unwrapped
        payload = [payload]
    if len(payload) != len(CITIES):
        raise SystemExit(f"expected {len(CITIES)} series, got {len(payload)} — aborting "
                         "rather than pairing cities with the wrong readings")

    cities = []
    for (cid, th, en, lat, lng, tz), s in zip(CITIES, payload):
        cur, daily = s.get("current") or {}, s.get("daily") or {}
        cities.append({
            "id": cid, "th": th, "en": en, "tz": tz,
            "lat": lat, "lng": lng,
            "temp": cur.get("temperature_2m"),
            "humidity": cur.get("relative_humidity_2m"),
            "code": cur.get("weather_code"),
            "observed": cur.get("time"),
            "days": [
                {"date": d, "max": mx, "min": mn, "code": cd}
                for d, mx, mn, cd in zip(daily.get("time", [])[:4],
                                         daily.get("temperature_2m_max", [])[:4],
                                         daily.get("temperature_2m_min", [])[:4],
                                         daily.get("weather_code", [])[:4])
            ],
        })
    # WO-41 Phase 2: one call carries all fifteen cities, so a short list is
    # a broken answer, not a quiet day. Yesterday's forecast beats none.
    ingest.write(OUT, {"generated": date.today().isoformat(),
                       "source": "Open-Meteo (open-meteo.com), CC-BY 4.0",
                       "cities": cities},
                 count=len(cities), min_rows=5, label="weather.json")


if __name__ == "__main__":
    main()
