# ingest_event.py
import json
import math
import os
import sys
import urllib.parse
import urllib.request

# Tha Phae Gate reference coordinates
THA_PHAE_GATE = (18.7877, 98.9932)
LONGDO_API_KEY = os.environ.get("LONGDO_API_KEY", "YOUR_LONGDO_KEY")

def get_coordinates(venue_name):
    """Fetch coordinates using Longdo Map API."""
    query = urllib.parse.urlencode({"keyword": venue_name, "area": "50", "key": LONGDO_API_KEY})
    url = f"https://search.longdo.com/api/search?{query}"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.load(response).get("data")
    except (OSError, ValueError):
        return None, None
    if data:
        # Grab the top confidence result
        top_result = data[0]
        return float(top_result['lat']), float(top_result['lon'])
    return None, None

def calculate_spatial_data(lat, lon):
    """Calculate Haversine distance and compass bearing from Tha Phae Gate."""
    R = 6371  # Earth radius in km
    lat1, lon1 = THA_PHAE_GATE

    # Distance
    dlat = math.radians(lat - lat1)
    dlon = math.radians(lon - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat)) * math.sin(dlon/2)**2
    distance = round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

    # Bearing
    lat1_rad, lon1_rad = map(math.radians, THA_PHAE_GATE)
    lat2_rad, lon2_rad = map(math.radians, (lat, lon))
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    compass = dirs[round(bearing / 45)]

    return distance, compass

def generate_motdang_json(venue_name):
    lat, lon = get_coordinates(venue_name)
    if lat is None or lon is None:
        print(f"Could not resolve venue: {venue_name}")
        sys.exit(1)

    distance, bearing = calculate_spatial_data(lat, lon)

    event_data = {
        "venue": {
            "name": venue_name,
            "coordinates": {"lat": lat, "lon": lon},
            "spatial_badge": f"{distance} km {bearing}"
        },
        "completeness_metrics": {
            "needs_review": True
        }
    }

    with open("new_event.json", "w", encoding="utf-8") as f:
        json.dump(event_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated new_event.json for {venue_name} ({distance} km {bearing})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_event.py 'Venue Name'")
        sys.exit(1)
    generate_motdang_json(sys.argv[1])
