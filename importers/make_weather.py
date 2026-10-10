#!/usr/bin/env python3
"""Bake the weather widget's data for a fixed set of cities.

Same shape as make_finance.py and make_ticker.py: fetched once here, written to
data/weather.json, read by build.py. Published pages make no external request,
so the reader picks which of these cities to show and the answer is already in
the page — nothing is called at page-load time.

That is why the city list is baked rather than free-text: a search box would
mean a live API call from the browser, which this site does not do. Fifteen
cities covered both provinces, the rest of Thailand people travel to, and the
places readers keep a clock on. Cut to three on 2026-09-02: the two provinces
and Réunion.

    python3 importers/make_weather.py
    python3 importers/make_weather.py --publish   # and push docs/data/weather.json live

Hourly (launchd net.motdang.weather-hourly, 2026-10-03). The front page's rain
line said "raining" in San Kamphaeng on a dry evening: the file it read was a
day old, held back while the walk rested. Weather now ships on its own, every
hour, like traffic_now.

SPOTS. The rain line used to read one point, the old city, for everyone in the
province. It now reads the nearest of a grid of points about 11 km apart over
the Chiang Mai and Chiang Rai basins; a reader with no known place still gets
the city.

Source: Open-Meteo — free, keyless, no attribution requirement, and it takes
every coordinate in one request.
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import ingest      # shared write discipline (WO-41 Phase 2)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "weather.json"
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; daily weather snapshot)"

# (id, Thai name, English name, lat, lng, IANA timezone)
CITIES = [
    ("chiang-mai", "เชียงใหม่", "Chiang Mai", 18.7883, 98.9853, "Asia/Bangkok"),
    ("chiang-rai", "เชียงราย", "Chiang Rai", 19.9105, 99.8406, "Asia/Bangkok"),
    # Saint-Denis, Réunion — Saint Expédit's island (Nan, 2026-09-02).
    ("reunion", "เรอูนียง", "Réunion", -20.8789, 55.4481, "Indian/Reunion"),
]

# about 11 km apart: the Chiang Mai basin (San Kamphaeng, Hang Dong, Mae Rim,
# San Sai, Doi Saket…) and the Chiang Rai plain
SPOTS = ([(round(18.6 + 0.1 * i, 1), round(98.8 + 0.1 * j, 1)) for i in range(5) for j in range(5)]
         + [(round(19.8 + 0.1 * i, 1), round(99.7 + 0.1 * j, 1)) for i in range(3) for j in range(3)])


def spots():
    """[{lat, lng, hours: [[local hour, % chance, mm], …]}] for the next 24 hours, or [] —
    the rain line falls back to the city when this is missing."""
    try:
        qs = urllib.parse.urlencode({
            "latitude": ",".join(str(a) for a, _ in SPOTS),
            "longitude": ",".join(str(b) for _, b in SPOTS),
            "hourly": "precipitation_probability,precipitation",
            "forecast_hours": "24", "timezone": "Asia/Bangkok"})
        with urllib.request.urlopen(urllib.request.Request(
                "https://api.open-meteo.com/v1/forecast?" + qs, headers={"User-Agent": UA}), timeout=30) as r:
            got = json.load(r)
    except Exception as e:
        print("  weather: spots unavailable:", e)
        return []
    if isinstance(got, dict):
        got = [got]
    if len(got) != len(SPOTS):
        print(f"  weather: spots came back {len(got)} of {len(SPOTS)}, left out")
        return []
    out = []
    for (lat, lng), s in zip(SPOTS, got):
        h = s.get("hourly") or {}
        out.append({"lat": lat, "lng": lng, "hours": [
            [t, p, mm] for t, p, mm in zip(h.get("time", []), h.get("precipitation_probability", []),
                                           h.get("precipitation", []))]})
    return out


def rain_cal():
    """How often it rained at CNX / CEI when IFS gave each chance (data/curated/rain_calibration.json),
    carried beside the forecast so the front page can say it; {} when the file is missing."""
    try:
        return json.loads((ROOT / "data" / "curated" / "rain_calibration.json").read_text())["bins"]
    except (OSError, ValueError, KeyError):
        return {}


def _col(block, key):
    """One column of an Open-Meteo block, padded with None when the field did not come back."""
    return (block.get(key) or []) + [None] * len(block.get("time") or [])


def main():
    qs = urllib.parse.urlencode({
        "latitude": ",".join(str(c[3]) for c in CITIES),
        "longitude": ",".join(str(c[4]) for c in CITIES),
        "current": ("temperature_2m,relative_humidity_2m,weather_code,apparent_temperature,"
                    "wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index,is_day,precipitation"),
        "daily": ("temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,"
                  "precipitation_probability_max,sunrise,sunset,uv_index_max,wind_speed_10m_max,"
                  "wind_direction_10m_dominant"),
        # the next three days by the hour: the rain line (2026-09-26), and the front
        # page's hour chart, temperature and wind (2026-10-10)
        "hourly": ("precipitation_probability,precipitation,temperature_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,wind_direction_10m,uv_index,relative_humidity_2m"),
        "forecast_hours": "72",
        "timezone": "auto",
        "forecast_days": "7",
    })
    url = "https://api.open-meteo.com/v1/forecast?" + qs
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    # Open-Meteo answers 503 now and then (12 of the hourly runs to 2026-10-04 died on one
    # and the live file went 13 h stale); three more tries over ~3 minutes
    for wait in (20, 60, 120, None):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if wait is None or e.code not in (429, 500, 502, 503, 504):
                raise
            print(f"  open-meteo {e.code}; again in {wait} s", file=sys.stderr)
            time.sleep(wait)
    if isinstance(payload, dict):        # a single coordinate comes back unwrapped
        payload = [payload]
    if len(payload) != len(CITIES):
        raise SystemExit(f"expected {len(CITIES)} series, got {len(payload)} — aborting "
                         "rather than pairing cities with the wrong readings")

    # The rain line reads ECMWF IFS, the model weather-north measured against two
    # years of airport reports (data/curated/rain_calibration.json), not the
    # blended default whose chance of rain nobody here has checked (2026-09-28).
    ifs = []
    try:
        q2 = urllib.parse.urlencode({
            "latitude": ",".join(str(c[3]) for c in CITIES),
            "longitude": ",".join(str(c[4]) for c in CITIES),
            "hourly": "precipitation_probability,precipitation",
            "models": "ecmwf_ifs025", "forecast_hours": "48", "timezone": "auto"})
        with urllib.request.urlopen(urllib.request.Request(
                "https://api.open-meteo.com/v1/forecast?" + q2, headers={"User-Agent": UA}), timeout=30) as r:
            ifs = json.load(r)
        if isinstance(ifs, dict):
            ifs = [ifs]
    except Exception as e:                      # the line goes quiet; the rest stands
        print("  weather: IFS hours unavailable:", e)
        ifs = []

    cities = []
    for i, ((cid, th, en, lat, lng, tz), s) in enumerate(zip(CITIES, payload)):
        ih = (ifs[i].get("hourly") or {}) if i < len(ifs) else {}
        cur, daily = s.get("current") or {}, s.get("daily") or {}
        hourly = s.get("hourly") or {}
        cities.append({
            "id": cid, "th": th, "en": en, "tz": tz,
            "lat": lat, "lng": lng,
            "temp": cur.get("temperature_2m"),
            "humidity": cur.get("relative_humidity_2m"),
            "code": cur.get("weather_code"),
            "observed": cur.get("time"),
            "feels": cur.get("apparent_temperature"),
            "wind": cur.get("wind_speed_10m"),
            "wind_dir": cur.get("wind_direction_10m"),
            "gust": cur.get("wind_gusts_10m"),
            "uv": cur.get("uv_index"),
            "is_day": cur.get("is_day"),
            "rain_now": cur.get("precipitation"),
            "days": [
                {"date": d, "max": mx, "min": mn, "code": cd, "rain": rs, "prob": pp,
                 "sunrise": sr, "sunset": ss, "uv": uv, "wind": wd, "wind_dir": wdd}
                for d, mx, mn, cd, rs, pp, sr, ss, uv, wd, wdd in zip(
                    daily.get("time", []), daily.get("temperature_2m_max", []),
                    daily.get("temperature_2m_min", []), daily.get("weather_code", []),
                    _col(daily, "precipitation_sum"), _col(daily, "precipitation_probability_max"),
                    _col(daily, "sunrise"), _col(daily, "sunset"), _col(daily, "uv_index_max"),
                    _col(daily, "wind_speed_10m_max"), _col(daily, "wind_direction_10m_dominant"))
            ],
            # [local hour, % chance of rain, mm expected in that hour] — the next 48, as before
            "hours": [
                [t, p, mm]
                for t, p, mm in zip(hourly.get("time", [])[:48],
                                    hourly.get("precipitation_probability", []),
                                    hourly.get("precipitation", []))
            ],
            # [local hour, °C, feels-like °C, WMO code, wind km/h, wind from °, UV, % humidity] — 72 hours
            "hx": [
                list(r) for r in zip(hourly.get("time", []), _col(hourly, "temperature_2m"),
                                     _col(hourly, "apparent_temperature"), _col(hourly, "weather_code"),
                                     _col(hourly, "wind_speed_10m"), _col(hourly, "wind_direction_10m"),
                                     _col(hourly, "uv_index"), _col(hourly, "relative_humidity_2m"))
            ],
            "hours_ifs": [
                [t, p, mm]
                for t, p, mm in zip(ih.get("time", []),
                                    ih.get("precipitation_probability", []),
                                    ih.get("precipitation", []))
            ],
        })
    # WO-41 Phase 2: one call carries all fifteen cities, so a short list is
    # a broken answer, not a quiet day. Yesterday's forecast beats none.
    ingest.write(OUT, {"generated": date.today().isoformat(),
                       "fetched": datetime.now(timezone.utc).isoformat(timespec="minutes"),
                       "source": "Open-Meteo (open-meteo.com), CC-BY 4.0",
                       "cities": cities, "spots": spots(), "rain_cal": rain_cal()},
                 count=len(cities), min_rows=3, label="weather.json")
    if "--publish" in sys.argv:
        (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
        (ROOT / "docs" / "data" / "weather.json").write_text(OUT.read_text())
        files = ["data/weather.json"]
        # The air rides the same hour (2026-10-10): the front page's air chart reads the next
        # three days by the hour, and the walk alone refreshed it a few times a day.
        air = ROOT / "data" / "air.json"
        try:
            subprocess.run([sys.executable, str(ROOT / "importers" / "make_air.py")], cwd=ROOT,
                           timeout=180, check=True)
            (ROOT / "docs" / "data" / "air.json").write_text(air.read_text())
            files.append("data/air.json")
        except Exception as e:
            print("  weather: air left as it was:", e)
        os.chdir(ROOT)
        os.execvp(sys.executable, [sys.executable, "publish/deploy.py", "--files", *files, "--yes"])


if __name__ == "__main__":
    main()
