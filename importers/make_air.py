#!/usr/bin/env python3
"""Bake the air-quality data for the northern towns.

Same shape as make_weather.py — fetched once here, written to data/air.json,
read by build.py. The published page makes no external request.

Why this exists at all: for roughly a third of the year the number that governs
what a person in Chiang Mai does with their day is not the temperature, it is
the PM2.5. Every other figure on the front page was already answerable and this
one was not.

    python3 importers/make_air.py

Source: Open-Meteo Air Quality — free, keyless, CC-BY 4.0. Readings are modelled
(CAMS), not a reading from a monitor in your soi, and the page says so: a
model's number and a sensor's number are different claims and should not be
dressed the same.

The seven-day history is kept because a single hour tells you almost nothing in
burning season — what people actually want to know is whether it is getting
better or worse.
"""
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "air.json"
UA = ("mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; "
      "daily air-quality snapshot)")

# The towns people here actually move between in smoke season, plus Bangkok as
# the comparison everyone reaches for. Deliberately not the weather widget's
# fifteen: an air reading for Sydney is trivia, one for Mae Hong Son is a plan.
PLACES = [
    ("chiang-mai", "เชียงใหม่", "Chiang Mai", 18.7883, 98.9853),
    ("chiang-rai", "เชียงราย", "Chiang Rai", 19.9105, 99.8406),
    ("pai", "ปาย", "Pai", 19.3583, 98.4392),
    ("mae-hong-son", "แม่ฮ่องสอน", "Mae Hong Son", 19.3020, 97.9654),
    ("lamphun", "ลำพูน", "Lamphun", 18.5744, 99.0087),
    ("lampang", "ลำปาง", "Lampang", 18.2888, 99.4909),
    ("mae-sai", "แม่สาย", "Mae Sai", 20.4293, 99.8814),
    ("doi-inthanon", "ดอยอินทนนท์", "Doi Inthanon", 18.5885, 98.4867),
    ("bangkok", "กรุงเทพฯ", "Bangkok", 13.7563, 100.5018),
]

# Thailand's own AQI bands, in µg/m³ of PM2.5 (24-hour). These are the colours
# and words people here already read on every other board in town, so the site
# uses them rather than the US EPA scale — the reader is standing in Thailand.
BANDS = [
    (15.0, "excellent", "ดีมาก", "Very good", "#3bb2d0"),
    (25.0, "good", "ดี", "Good", "#4caf50"),
    (37.5, "moderate", "ปานกลาง", "Moderate", "#f6c445"),
    (75.0, "unhealthy", "เริ่มมีผลต่อสุขภาพ", "Starting to affect health", "#f08a3c"),
    (float("inf"), "hazardous", "มีผลต่อสุขภาพ", "Affects health", "#d1495b"),
]


def band(pm25):
    """Thai PCD band for a PM2.5 figure. None in, None out — never a guess."""
    if pm25 is None:
        return None
    for ceiling, key, th, en, colour in BANDS:
        if pm25 <= ceiling:
            return {"key": key, "th": th, "en": en, "colour": colour}
    return None


def main():
    qs = urllib.parse.urlencode({
        "latitude": ",".join(str(p[3]) for p in PLACES),
        "longitude": ",".join(str(p[4]) for p in PLACES),
        "current": "pm2_5,pm10,us_aqi",
        "hourly": "pm2_5",
        "past_days": "7",
        "forecast_days": "3",
        "timezone": "Asia/Bangkok",
    })
    url = "https://air-quality-api.open-meteo.com/v1/air-quality?" + qs
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        payload = json.load(r)
    if isinstance(payload, dict):          # a single coordinate comes back unwrapped
        payload = [payload]
    if len(payload) != len(PLACES):
        raise SystemExit(f"expected {len(PLACES)} series, got {len(payload)} — aborting "
                         "rather than pairing towns with the wrong readings")

    out = []
    for (pid, th, en, lat, lng), s in zip(PLACES, payload):
        cur = s.get("current") or {}
        hourly = s.get("hourly") or {}
        times = hourly.get("time") or []
        vals = hourly.get("pm2_5") or []

        # Daily means from the hourly series. A day with fewer than 12 readings
        # is left out rather than averaged from a stub — a half-day mean and a
        # whole-day mean are not the same number and should not sit in one row.
        buckets = {}
        for t, v in zip(times, vals):
            if v is None:
                continue
            buckets.setdefault(t[:10], []).append(v)
        days = [{"date": d, "pm25": round(sum(xs) / len(xs), 1), "hours": len(xs)}
                for d, xs in sorted(buckets.items()) if len(xs) >= 12]
        for d in days:
            d["band"] = band(d["pm25"])

        pm25 = cur.get("pm2_5")
        out.append({
            "id": pid, "th": th, "en": en, "lat": lat, "lng": lng,
            "pm25": pm25, "pm10": cur.get("pm10"), "usAqi": cur.get("us_aqi"),
            "band": band(pm25), "observed": cur.get("time"), "days": days,
        })

    OUT.write_text(json.dumps(
        {"generated": date.today().isoformat(),
         "source": "Open-Meteo Air Quality (open-meteo.com), CC-BY 4.0",
         "model": "CAMS — modelled, not a monitor at street level",
         "scale": "Thailand PCD PM2.5 bands (µg/m³)",
         "places": out}, ensure_ascii=False, indent=1))
    got = sum(1 for p in out if p["pm25"] is not None)
    print(f"🐜 air quality for {got}/{len(out)} towns -> {OUT}")


if __name__ == "__main__":
    main()
